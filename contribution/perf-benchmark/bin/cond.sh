#!/usr/bin/env bash
# cond.sh <baseline|hubble|hubble_agent|otterize|ig_tcp|ig_snap>
#   hubble_agent (agent-only Hubble experiment): enable-hubble=true in the agent, the two hubble-metrics
#   keys absent, Relay at 0 pods; no client. What a default Helm install runs (agent Hubble on since chart 1.9).
#
# Switch the cluster to one benchmark condition, then verify it. Idempotent.
# Every call runs the same sequence, whatever the previous condition was:
#   1. switch off every observer (relay and otterize mapper scaled to 0; otterize sniffer
#      and gadget DaemonSets gated with nodeSelector perfbench.off=true), wait for zero pods
#   2. set enable-hubble (and the two hubble-metrics keys) in kube-system/cilium-config
#   3. rollout-restart ds/cilium (always) and wait until every agent reports OK
#   4. start the observers the condition uses, as new pods
#   5. verify agent hubble state, :9965 reachability, relay/otterize/gadget pod counts
# Prints one JSON line with the verified state on stdout. Progress goes to stderr.
# Exit 0 = verified; exit 1 = mismatch (the JSON line has ok=false and the reasons).
set -Eeuo pipefail
# any unexpected failure (a wait timing out, kubectl erroring) still prints a JSON line
FAIL_LINE=""; JSON_DONE=""
trap 'FAIL_LINE=${FAIL_LINE:-$LINENO}' ERR
trap 'rc=$?; if [ $rc -ne 0 ] && [ -z "$JSON_DONE" ] && [ $rc -ne 2 ]; then
  printf "{\"cond\":\"%s\",\"ok\":false,\"error\":\"aborted at cond.sh line %s (rc %s), see stderr\"}\n" "${COND:-}" "${FAIL_LINE:-?}" "$rc"; fi' EXIT

export KUBECONFIG=${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}
export PATH=/usr/local/bin:$PATH
COND=${1:-}
TIMEOUT=${COND_TIMEOUT:-600}          # seconds per wait
NODE_IPS=(172.16.0.2 172.16.0.3 172.16.0.4)
OFF_SEL='perfbench.off'
IG_TAG=${IG_TAG:-v0.54.1}             # IG server version (DaemonSet, kubectl-gadget)
# gadget image tag for the warm-up: the same one run_one.sh's clients use (cluster/gadget.env)
PB_ROOT=${PB_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}
GADGET_TAG=${PB_GADGET_TAG:-$(sed -n 's/^GADGET_TAG=//p' "$PB_ROOT/cluster/gadget.env" 2>/dev/null | tail -1)}
GADGET_TAG=${GADGET_TAG:-$IG_TAG}
K=kubectl

HA=0   # 1 = agent-only Hubble: enable-hubble true, but no metrics server and no Relay
case "$COND" in
  baseline) H=0 O=0 G=0 ;;
  hubble)   H=1 O=0 G=0 ;;
  hubble_agent) H=0 HA=1 O=0 G=0 ;;
  otterize) H=0 O=1 G=0 ;;
  ig_tcp|ig_snap) H=0 O=0 G=1 ;;
  *) echo "usage: cond.sh baseline|hubble|hubble_agent|otterize|ig_tcp|ig_snap" >&2; exit 2 ;;
esac

exec 9>/run/perfbench-cond.lock
flock -w 900 9 || { echo "cond.sh: another cond.sh holds the lock" >&2; exit 1; }

T0=$(date +%s)
log() { printf '[cond %s %s] %s\n' "$COND" "$(date -u +%H:%M:%SZ)" "$*" >&2; }

# ---- helpers -------------------------------------------------------------
ds_gate() {   # ns ds on|off  (off = a nodeSelector no node matches, so zero pods)
  local v; [ "$3" = off ] && v='"true"' || v=null
  $K -n "$1" patch ds "$2" --type merge -p "{\"spec\":{\"template\":{\"spec\":{\"nodeSelector\":{\"$OFF_SEL\":$v}}}}}" >/dev/null
}
deploy_scale() { $K -n "$1" scale deploy "$2" --replicas="$3" >/dev/null; }  # ns deploy replicas
count_pods() {  # ns [selector]  -> number of pods that exist (any phase, incl. terminating)
  local sel=${2:+-l $2}
  # shellcheck disable=SC2086
  $K -n "$1" get pods $sel --no-headers 2>/dev/null | wc -l
}
wait_zero() {   # ns [selector]
  local end=$(( $(date +%s) + TIMEOUT ))
  while [ "$(count_pods "$@")" -ne 0 ]; do
    [ "$(date +%s)" -lt "$end" ] || { log "timeout waiting for zero pods in $*"; return 1; }
    sleep 2
  done
}
wait_ds_ready() { # ns ds
  $K -n "$1" rollout status ds "$2" --timeout="${TIMEOUT}s" >/dev/null
  local end=$(( $(date +%s) + TIMEOUT ))
  while :; do  # rollout status can return before the last old pod has finished terminating
    local st; st=$($K -n "$1" get ds "$2" -o json | jq -r '[.status.desiredNumberScheduled,.status.numberReady,.status.updatedNumberScheduled] | @tsv')
    read -r des rdy upd <<<"$st"
    local n; n=$(count_pods "$1" "$(ds_selector "$1" "$2")")
    [ "$des" -gt 0 ] && [ "$rdy" = "$des" ] && [ "$upd" = "$des" ] && [ "$n" = "$des" ] && return 0
    [ "$(date +%s)" -lt "$end" ] || { log "timeout: ds $1/$2 des=$des ready=$rdy upd=$upd pods=$n"; return 1; }
    sleep 2
  done
}
ds_selector() { $K -n "$1" get ds "$2" -o json | jq -r '.spec.selector.matchLabels | to_entries | map(.key+"="+.value) | join(",")'; }
deploy_selector() { $K -n "$1" get deploy "$2" -o json | jq -r '.spec.selector.matchLabels | to_entries | map(.key+"="+.value) | join(",")'; }
wait_deploy() { # ns deploy replicas
  local ns=$1 d=$2 n=$3 sel; sel=$(deploy_selector "$ns" "$d")
  if [ "$n" -eq 0 ]; then wait_zero "$ns" "$sel"; return; fi
  $K -n "$ns" rollout status deploy "$d" --timeout="${TIMEOUT}s" >/dev/null
  local end=$(( $(date +%s) + TIMEOUT ))
  while [ "$(count_pods "$ns" "$sel")" -ne "$n" ]; do  # old pod still terminating
    [ "$(date +%s)" -lt "$end" ] || { log "timeout: $ns/$d pods != $n"; return 1; }
    sleep 2
  done
}
port_open() { timeout 3 bash -c "exec 3<>/dev/tcp/$1/$2" 2>/dev/null; }

# ---- 1. every observer goes off first, whatever the previous condition was ----------
# (so the pre-run sequence is identical for all conditions and the target's observers
# always start as new pods after the fresh cilium agents)
OTT_DEPLOYS=$($K -n otterize-system get deploy -o name 2>/dev/null | cut -d/ -f2)
OTT_DS=$($K -n otterize-system get ds -o name 2>/dev/null | cut -d/ -f2)
[ -n "$OTT_DEPLOYS" ] || { JSON_DONE=1; echo '{"ok":false,"error":"otterize-system has no deployments"}'; exit 1; }

log "all observers off (relay, otterize, gadget)"
deploy_scale kube-system hubble-relay 0
for d in $OTT_DEPLOYS; do deploy_scale otterize-system "$d" 0; done
for ds in $OTT_DS; do ds_gate otterize-system "$ds" off; done
ds_gate gadget gadget off
wait_zero kube-system k8s-app=hubble-relay
wait_zero otterize-system
wait_zero gadget

# ---- 2+3. hubble flag, then always a fresh cilium agent set ------------------------
# In 1.19 the Hubble metrics server is its own cell: enable-hubble=false alone leaves :9965
# up. Off therefore also removes the two metrics keys (the agent default "" = no metrics
# server, which is how test-cluster looked before the 2026-07-27 patch); on restores the exact
# test-cluster values.
HUBBLE_METRICS='drop:sourceContext=identity;destinationContext=identity flow:sourceContext=identity;destinationContext=identity tcp dns'
HUBBLE_METRICS_SERVER=':9965'
WANT_HUBBLE=$({ [ "$H" -eq 1 ] || [ "$HA" -eq 1 ]; } && echo true || echo false)
log "enable-hubble=$WANT_HUBBLE (+ hubble metrics keys); rollout-restart ds/cilium"
if [ "$H" -eq 1 ]; then
  PATCH=$(jq -cn --arg m "$HUBBLE_METRICS" --arg s "$HUBBLE_METRICS_SERVER" \
    '{data:{"enable-hubble":"true","hubble-metrics":$m,"hubble-metrics-server":$s}}')
elif [ "$HA" -eq 1 ]; then
  PATCH='{"data":{"enable-hubble":"true","hubble-metrics":null,"hubble-metrics-server":null}}'
else
  PATCH='{"data":{"enable-hubble":"false","hubble-metrics":null,"hubble-metrics-server":null}}'
fi
$K -n kube-system patch cm cilium-config --type merge -p "$PATCH" >/dev/null
$K -n kube-system rollout restart ds/cilium >/dev/null
wait_ds_ready kube-system cilium
end=$(( $(date +%s) + TIMEOUT ))
for p in $($K -n kube-system get pods -l k8s-app=cilium -o name); do
  until [ "$($K -n kube-system exec "$p" -c cilium-agent -- cilium-dbg status --brief 2>/dev/null)" = OK ]; do
    [ "$(date +%s)" -lt "$end" ] || { log "timeout: $p not OK"; break; }
    sleep 3
  done
done
CILIUM_RESTARTED_AT=$(date -u +%FT%TZ)

# ---- 4. observers the condition uses come up fresh ------------------------------------
if [ "$H" -eq 1 ]; then
  log "relay on"; deploy_scale kube-system hubble-relay 1; wait_deploy kube-system hubble-relay 1
fi
if [ "$O" -eq 1 ]; then
  log "otterize on (fresh mapper + sniffers)"
  for d in $OTT_DEPLOYS; do deploy_scale otterize-system "$d" 1; done
  for ds in $OTT_DS; do ds_gate otterize-system "$ds" on; done
  for d in $OTT_DEPLOYS; do wait_deploy otterize-system "$d" 1; done
  for ds in $OTT_DS; do wait_ds_ready otterize-system "$ds"; done
fi
SNAP_N=0; TCP_RC=-1
if [ "$G" -eq 1 ]; then
  log "gadget on (fresh pods)"; ds_gate gadget gadget on; wait_ds_ready gadget gadget
  # The gadget pods keep pulled gadget images in an emptyDir, so fresh pods start with an
  # empty store and the first run pays the pull (measured: snapshot 4.5 s cold vs 0.6 s warm,
  # trace_tcp start 5.3 s vs 1.5 s). test-cluster' gadget pods were long-lived with warm
  # stores, so both gadgets run once here, against ns gadget, before the run starts. The same
  # warm-up runs for ig_tcp and ig_snap. snapshot_socket never exits by itself (that is why
  # the thesis killed it after 12 s): wait for a complete JSON array, then kill it.
  log "gadget warm-up: snapshot_socket:$GADGET_TAG and trace_tcp:$GADGET_TAG on every node"
  WD=$(mktemp -d)
  kubectl gadget run "snapshot_socket:$GADGET_TAG" -n gadget -o json > "$WD/snap.json" 2> "$WD/snap.err" &
  SP=$!
  for _ in $(seq 300); do
    SNAP_N=$(python3 -c "import json;print(len(json.load(open('$WD/snap.json'))))" 2>/dev/null || echo 0)
    [ "$SNAP_N" -gt 0 ] && break
    sleep 0.1
  done
  kill "$SP" 2>/dev/null || true; wait "$SP" 2>/dev/null || true
  # trace_tcp right after fresh gadget pods sometimes exits rc=1 (a start-up race, seen in 9 of
  # about 250 IG switches up to 2026-10-04, more often on AMD hosts), so try up to 3 times, 5 s
  # apart, and keep each failure's stderr for diagnosis. Nothing measured runs during this.
  for t in 1 2 3; do
    TCP_RC=0
    timeout 60 kubectl gadget run "trace_tcp:$GADGET_TAG" -n gadget -t 2 -o json > "$WD/tcp.json" 2> "$WD/tcp.err" || TCP_RC=$?
    [ "$TCP_RC" -eq 0 ] && break
    cp "$WD/tcp.err" "/var/tmp/perfbench-gadget-warmup-tcp.err.$t" 2>/dev/null || true
    log "gadget warm-up trace_tcp rc=$TCP_RC (try $t of 3): $(tail -n 2 "$WD/tcp.err" | tr '\n' ' ')"
    [ "$t" -lt 3 ] && sleep 5
  done
  rm -rf "$WD"
fi

# ---- 5. verify -------------------------------------------------------------------------
ERR=()
CM=$($K -n kube-system get cm cilium-config -o json)
CM_HUBBLE=$(jq -r '.data["enable-hubble"]' <<<"$CM")
CM_MSRV=$(jq -r '.data["hubble-metrics-server"] // "absent"' <<<"$CM")
CM_MET=$(jq -r '.data["hubble-metrics"] // "absent"' <<<"$CM")
[ "$CM_HUBBLE" = "$WANT_HUBBLE" ] || ERR+=("cilium-config enable-hubble=$CM_HUBBLE")
if [ "$H" -eq 1 ]; then
  [ "$CM_MSRV" = "$HUBBLE_METRICS_SERVER" ] && [ "$CM_MET" = "$HUBBLE_METRICS" ] || ERR+=("cilium-config hubble metrics keys wrong")
else
  [ "$CM_MSRV" = absent ] && [ "$CM_MET" = absent ] || ERR+=("cilium-config hubble metrics keys still set")
fi

AGENT_HUBBLE=()
for p in $($K -n kube-system get pods -l k8s-app=cilium -o name); do
  # Right after the restart the agent can report hubble=Warning for a few seconds (seen on 2 of the first 4
  # hubble_agent switches, 2026-10-05); the full hubble condition is spared by its Relay wait. When Hubble is
  # meant to be on, give it up to 60 s to reach Ok before verifying. Nothing measured runs during this.
  for _try in $(seq 20); do
    sj=$($K -n kube-system exec "$p" -c cilium-agent -- cilium-dbg status -o json 2>/dev/null || echo '{}')
    st=$(jq -r '.hubble.state // "absent"' <<<"$sj")
    mst=$(jq -r '.["hubble-metrics"].state // "absent"' <<<"$sj")
    if [ "$H" -eq 1 ] || [ "$HA" -eq 1 ]; then [ "$st" = Ok ] && break; else break; fi
    sleep 3
  done
  AGENT_HUBBLE+=("${p#pod/}:hubble=$st,metrics=$mst")
  if [ "$H" -eq 1 ]; then
    [ "$st" = Ok ] && [ "$mst" = Ok ] || ERR+=("$p hubble=$st metrics=$mst")
  elif [ "$HA" -eq 1 ]; then
    [ "$st" = Ok ] && [ "$mst" != Ok ] || ERR+=("$p hubble=$st metrics=$mst")
  else
    [ "$st" = Disabled ] && [ "$mst" != Ok ] || ERR+=("$p hubble=$st metrics=$mst")
  fi
done
CILIUM_READY=$($K -n kube-system get ds cilium -o jsonpath='{.status.numberReady}')
CILIUM_DES=$($K -n kube-system get ds cilium -o jsonpath='{.status.desiredNumberScheduled}')
[ "$CILIUM_READY" = "$CILIUM_DES" ] && [ "$CILIUM_DES" -eq ${#NODE_IPS[@]} ] || ERR+=("cilium ready $CILIUM_READY/$CILIUM_DES")

M9965=(); M9962=()
for ip in "${NODE_IPS[@]}"; do
  if port_open "$ip" 9965; then M9965+=(true); [ "$H" -eq 1 ] || ERR+=("$ip :9965 open"); else M9965+=(false); [ "$H" -eq 0 ] || ERR+=("$ip :9965 closed"); fi
  if port_open "$ip" 9962; then M9962+=(true); else M9962+=(false); ERR+=("$ip :9962 closed"); fi
done

RELAY=$(count_pods kube-system k8s-app=hubble-relay)
OTT=$(count_pods otterize-system)
GAD=$(count_pods gadget)
OTT_MAPPER=$(count_pods otterize-system "$(deploy_selector otterize-system otterize-network-mapper)")
OTT_SNIFF_DES=0; for ds in $OTT_DS; do OTT_SNIFF_DES=$(( OTT_SNIFF_DES + $($K -n otterize-system get ds "$ds" -o jsonpath='{.status.desiredNumberScheduled}') )); done
GAD_DES=$($K -n gadget get ds gadget -o jsonpath='{.status.desiredNumberScheduled}')

RELAY_NODES=""; OTT_QUERY=""; GAD_SERVER=""
if [ "$H" -eq 1 ]; then
  [ "$RELAY" -eq 1 ] || ERR+=("relay pods=$RELAY")
  RIP=$($K -n kube-system get svc hubble-relay -o jsonpath='{.spec.clusterIP}')
  end=$(( $(date +%s) + 120 ))
  until RELAY_NODES=$(hubble status --server "$RIP:80" 2>/dev/null | awk -F': ' '/Connected Nodes/{print $2}') && [ "$RELAY_NODES" = "${#NODE_IPS[@]}/${#NODE_IPS[@]}" ]; do
    [ "$(date +%s)" -lt "$end" ] || { ERR+=("relay connected nodes=$RELAY_NODES"); break; }
    sleep 3
  done
else
  [ "$RELAY" -eq 0 ] || ERR+=("relay pods=$RELAY")
fi
if [ "$O" -eq 1 ]; then
  [ "$OTT_MAPPER" -eq 1 ] || ERR+=("otterize mapper pods=$OTT_MAPPER")
  [ "$OTT_SNIFF_DES" -gt 0 ] || ERR+=("otterize sniffer desired=0")
  MIP=$($K -n otterize-system get svc otterize-network-mapper -o jsonpath='{.spec.clusterIP}')
  end=$(( $(date +%s) + 120 ))
  until OTT_QUERY=$(curl -sS -m 10 -X POST "http://$MIP:9090/query" -H 'Content-Type: application/json' \
        -d '{"query":"{ serviceIntents { client { name namespace } } }"}' 2>/dev/null | jq -c 'if .data.serviceIntents then "ok:\(.data.serviceIntents|length)" else error end' 2>/dev/null); do
    [ "$(date +%s)" -lt "$end" ] || { ERR+=("otterize graphql not answering"); OTT_QUERY=fail; break; }
    sleep 3
  done
else
  [ "$OTT" -eq 0 ] || ERR+=("otterize pods=$OTT")
fi
if [ "$G" -eq 1 ]; then
  [ "$GAD" -eq "$GAD_DES" ] && [ "$GAD" -gt 0 ] || ERR+=("gadget pods=$GAD desired=$GAD_DES")
  GAD_SERVER=$(kubectl gadget version 2>/dev/null | awk '/Server version/{print $3}')
  [ "$GAD_SERVER" = "$IG_TAG" ] || ERR+=("gadget server version '$GAD_SERVER' != $IG_TAG")
  [ "$SNAP_N" -gt 0 ] || ERR+=("gadget warm-up snapshot_socket returned nothing")
  [ "$TCP_RC" -eq 0 ] || ERR+=("gadget warm-up trace_tcp rc=$TCP_RC")
else
  [ "$GAD" -eq 0 ] || ERR+=("gadget pods=$GAD")
fi

OK=$([ ${#ERR[@]} -eq 0 ] && echo true || echo false)
JSON_DONE=1
jq -cn --arg cond "$COND" --arg ts "$(date -u +%FT%TZ)" --argjson ok "$OK" \
  --arg enable_hubble "$CM_HUBBLE" --arg cilium_restarted_at "$CILIUM_RESTARTED_AT" \
  --argjson cilium_ready "${CILIUM_READY:-0}" --argjson cilium_desired "${CILIUM_DES:-0}" \
  --arg agent_hubble "${AGENT_HUBBLE[*]}" --arg m9965 "${M9965[*]}" --arg m9962 "${M9962[*]}" \
  --argjson relay_pods "$RELAY" --arg relay_nodes "$RELAY_NODES" \
  --argjson otterize_pods "$OTT" --argjson otterize_mapper_pods "$OTT_MAPPER" \
  --argjson otterize_sniffer_desired "$OTT_SNIFF_DES" --arg otterize_query "${OTT_QUERY//\"/}" \
  --argjson gadget_pods "$GAD" --argjson gadget_desired "${GAD_DES:-0}" --arg gadget_server "$GAD_SERVER" \
  --argjson warm_snap "$SNAP_N" --argjson warm_tcp_rc "$TCP_RC" --arg gadget_tag "$GADGET_TAG" \
  --argjson secs "$(( $(date +%s) - T0 ))" --arg errors "$(IFS=';'; echo "${ERR[*]:-}")" \
  --arg msrv "$CM_MSRV" \
  '{cond:$cond, ok:$ok, ts:$ts, secs:$secs, enable_hubble:$enable_hubble, hubble_metrics_server:$msrv,
    cilium:{ready:$cilium_ready, desired:$cilium_desired, restarted_at:$cilium_restarted_at,
            agent_hubble:($agent_hubble|split(" ")), metrics_9962:($m9962|split(" ")|map(.=="true")),
            hubble_metrics_9965:($m9965|split(" ")|map(.=="true"))},
    relay:{pods:$relay_pods, connected_nodes:$relay_nodes},
    otterize:{pods:$otterize_pods, mapper_pods:$otterize_mapper_pods, sniffer_desired:$otterize_sniffer_desired, query:$otterize_query},
    gadget:{pods:$gadget_pods, desired:$gadget_desired, server:$gadget_server,
            image_tag:$gadget_tag, warmup_snapshot_entries:$warm_snap, warmup_trace_tcp_rc:$warm_tcp_rc},
    errors:($errors|split(";")|map(select(length>0)))}'
[ "$OK" = true ] || { log "VERIFY FAILED: ${ERR[*]}"; exit 1; }
log "verified in $(( $(date +%s) - T0 ))s"
