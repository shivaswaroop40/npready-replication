#!/usr/bin/env bash
# smoke_app.sh <app> [--keep]: one-off pre-flight check of an app bundle on the real cluster.
#   1 deploy.sh (timed)            4 steady Job for 60 s, parsed with analyze.py's parser
#   2 pod count and placement      5 throughput Job, TP_N=200 TP_C=8, keepalive and newconn, parsed
#   3 wget TP_URL from a pod on cp-01 (status line must be 200)
#   6 memory: kubectl top (working set) of the app pods per node, and MemAvailable per worker
#   7 undeploy.sh (timed), unless --keep
# Output: results/_smoke/<app>/ (logs, jobs/, summary.json); summary.json is also printed.
# Runs in baseline or any other condition; it does not switch conditions. cp-01, as root.
# TP_C is 8 here (not 16) because hey runs N/C requests per worker: 200/16 would send 192.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PB_ROOT=${PB_ROOT:-$(dirname "$HERE")}
# shellcheck source=lib.sh source-path=SCRIPTDIR
. "$HERE/lib.sh"

APP=${1:?usage: smoke_app.sh <app> [--keep]}
KEEP=0; [ "${2:-}" = --keep ] && KEEP=1
PB_RUN=$PB_RESULTS/_smoke/$APP
rm -rf "$PB_RUN"; mkdir -p "$PB_RUN"/{jobs,tp}
: > "$PB_RUN/kv.tsv"; : > "$PB_RUN/phases.tsv"
pb_load_app "$APP" || pb_die "cannot load $APP"
FAILS=()
fail() { FAILS+=("$*"); pb_log "SMOKE FAIL: $*"; }

# 1 deploy
t0=$EPOCHSECONDS
if bash "$PB_APP_DIR/deploy.sh" > "$PB_RUN/deploy.json" 2> "$PB_RUN/deploy.err"; then :; else fail "deploy.sh rc=$?: $(tail -n 3 "$PB_RUN/deploy.err" | tr '\n' ' ')"; fi
DEPLOY_S=$((EPOCHSECONDS - t0))
pb_log "deploy took ${DEPLOY_S}s"

# 2 pods
K -n "$APP_NS" get pods -o wide > "$PB_RUN/pods.txt" 2>&1
PODS=$(K -n "$APP_NS" get pods -o json | jq -c '[.items[] | select(.status.phase=="Running")] |
  {running: length, per_node: (group_by(.spec.nodeName) | map({(.[0].spec.nodeName): length}) | add // {}),
   restarts: ([.[].status.containerStatuses[]?.restartCount] | add // 0)}')

# 3 wget from a pod on cp-01 (hey image: Alpine with busybox wget; already on cp-01)
HDR=""; ENVJ="[]"
if [ "$APP" = bank ]; then
  HDR='--header "Cookie: token=$(PB_SESSION_TOKEN)"'
  ENVJ='[{"name":"PB_SESSION_TOKEN","valueFrom":{"secretKeyRef":{"name":"perfbench-session","key":"token"}}}]'
fi
K -n "$APP_NS" delete pod pb-wget --ignore-not-found --wait=true >/dev/null 2>&1
OVR=$(jq -cn --arg url "$TP_URL" --arg hdr "$HDR" --argjson env "$ENVJ" '{spec:{restartPolicy:"Never",
  nodeSelector:{"kubernetes.io/hostname":"cp-01"},
  tolerations:[{key:"node-role.kubernetes.io/control-plane",operator:"Exists",effect:"NoSchedule"}],
  containers:[{name:"wget", image:"williamyeh/hey@sha256:6e63ae9c5801204cf7abe22c9ddf82d1bcbc7140ffd206a9bd83a8a643dcd6f2",
    imagePullPolicy:"IfNotPresent", env:$env, command:["/bin/sh","-c"],
    args:["wget -S -T 20 -O /dev/null " + $hdr + " " + ($url|@sh) + " 2>&1 | grep -E \"HTTP/|wget:\"; true"]}]}}')
K -n "$APP_NS" run pb-wget --image=busybox --restart=Never --labels=perfbench=1 --overrides="$OVR" >/dev/null 2>&1
for _ in $(seq 60); do
  ph=$(K -n "$APP_NS" get pod pb-wget -o jsonpath='{.status.phase}' 2>/dev/null)
  case $ph in Succeeded|Failed) break ;; esac; sleep 1
done
K -n "$APP_NS" logs pb-wget > "$PB_RUN/wget.log" 2>&1
K -n "$APP_NS" delete pod pb-wget --wait=false >/dev/null 2>&1
WGET=$(grep -m1 -oE 'HTTP/[0-9.]+ [0-9]{3}' "$PB_RUN/wget.log" | awk '{print $2}')
[ "$WGET" = "${TP_EXPECT_STATUS:-200}" ] || fail "wget from cp-01 pod got '${WGET:-none}': $(tr '\n' ' ' < "$PB_RUN/wget.log" | head -c 200)"

# 4 steady 60 s
TPL_VARS="$PB_APP_VARS STEADY_SECONDS APP_NS TP_URL TP_HEADERS"
export STEADY_SECONDS=60
# shellcheck disable=SC2086
if pb_job_create "$APP_NS" pb-steady "$PB_APP_DIR/steady.yaml" $TPL_VARS; then
  pb_job_wait_started "$APP_NS" pb-steady 300 || fail "steady pod did not start: $(pb_job_state "$APP_NS" pb-steady)"
  pb_job_wait_finished "$APP_NS" pb-steady 400 3 || fail "steady Job did not finish"
  pb_job_logs "$APP_NS" pb-steady "$PB_RUN/steady.log"
  STEADY_STATE=$(pb_job_state "$APP_NS" pb-steady)
  K top pods -n "$APP_NS" --no-headers > "$PB_RUN/top_pods_under_load.txt" 2>&1
  K top nodes --no-headers > "$PB_RUN/top_nodes_under_load.txt" 2>&1
  K -n "$APP_NS" delete job pb-steady --wait=false >/dev/null 2>&1
else
  fail "steady Job create failed"; STEADY_STATE=none
fi
STEADY=$(python3 -c 'import json,sys; sys.path.insert(0,sys.argv[2]); import analyze as a; print(json.dumps(a.parse_steady(open(sys.argv[1]).read())))' "$PB_RUN/steady.log" "$PB_ROOT/analyze" 2>"$PB_RUN/parse.err" || echo null)
[ "$STEADY" != null ] || fail "steady log did not parse"

# 5 throughput
export TP_N=200 TP_C=8
TPJ="{}"
for mode in keepalive newconn; do
  if [ "$mode" = keepalive ]; then TP_FLAGS=${TP_FLAGS_KEEPALIVE-}; else TP_FLAGS=${TP_FLAGS_NEWCONN--disable-keepalive}; fi
  export TP_FLAGS
  if [ -n "${TP_PRE_HOOK:-}" ]; then (cd "$PB_APP_DIR" && bash "./$TP_PRE_HOOK") >> "$PB_RUN/tp_pre_hook.log" 2>&1 || fail "TP_PRE_HOOK failed"; fi
  # shellcheck disable=SC2086
  if pb_job_create "$APP_NS" "pb-tp-$mode-1" "$PB_APP_DIR/throughput.yaml" $PB_APP_VARS TP_N TP_C TP_FLAGS TP_URL TP_HEADERS APP_NS; then
    pb_job_wait_started "$APP_NS" "pb-tp-$mode-1" 300 && pb_job_wait_finished "$APP_NS" "pb-tp-$mode-1" 300 2 || fail "tp $mode did not finish"
    pb_job_logs "$APP_NS" "pb-tp-$mode-1" "$PB_RUN/tp/$mode-1.log"
    K -n "$APP_NS" delete job "pb-tp-$mode-1" --wait=false >/dev/null 2>&1
  else
    fail "tp $mode create failed"
  fi
  r=$(python3 -c 'import json,sys; sys.path.insert(0,sys.argv[2]); import analyze as a; print(json.dumps(a.parse_fixed_count(open(sys.argv[1]).read())))' "$PB_RUN/tp/$mode-1.log" "$PB_ROOT/analyze" 2>>"$PB_RUN/parse.err" || echo null)
  [ "$(jq -r '.n_2xx // 0' <<<"$r")" = 200 ] || fail "tp $mode: 2xx=$(jq -r '.n_2xx' <<<"$r") codes=$(jq -c '.codes' <<<"$r")"
  TPJ=$(jq -c --arg m "$mode" --argjson r "$r" '. + {($m): $r}' <<<"$TPJ")
done

# 6 memory (metrics-server working set, after load)
sleep 5
K top pods -n "$APP_NS" --no-headers > "$PB_RUN/top_pods.txt" 2>&1
MEM=$(K -n "$APP_NS" get pods -o json | jq -r '.items[] | "\(.metadata.name) \(.spec.nodeName)"' | \
  awk 'NR==FNR {node[$1]=$2; next} {m=$3; sub(/Mi$/,"",m); if ($3 ~ /Gi$/) {sub(/Gi$/,"",m); m*=1024}; c=$2; sub(/m$/,"",c); n=node[$1]; mem[n]+=m; cpu[n]+=c; tm+=m}
       END {printf "{"; s=""; for (k in mem) {printf "%s\"%s\":{\"mem_mib\":%d,\"cpu_m\":%d}", s, k, mem[k], cpu[k]; s=","}; printf ",\"total_mem_mib\":%d}\n", tm}' - "$PB_RUN/top_pods.txt")
AVAIL="{}"
for n in worker-01 worker-02; do
  a=$(pb_on "$n" "awk '/MemAvailable/ {print int(\$2/1024)}' /proc/meminfo")
  AVAIL=$(jq -c --arg n "$n" --argjson a "${a:-0}" '. + {($n): $a}' <<<"$AVAIL")
done
CPAVAIL=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)

# 7 undeploy
UNDEPLOY_S=null
if [ "$KEEP" = 0 ]; then
  t0=$EPOCHSECONDS
  bash "$PB_APP_DIR/undeploy.sh" > "$PB_RUN/undeploy.json" 2> "$PB_RUN/undeploy.err" || fail "undeploy.sh rc=$?"
  UNDEPLOY_S=$((EPOCHSECONDS - t0))
fi

jq -n --arg app "$APP" --argjson deploy_s "$DEPLOY_S" --argjson undeploy_s "$UNDEPLOY_S" \
  --argjson pods "${PODS:-null}" --arg wget "${WGET:-}" --arg steady_state "$STEADY_STATE" \
  --argjson steady "${STEADY:-null}" --argjson tp "$TPJ" --argjson mem "${MEM:-null}" \
  --argjson avail "$AVAIL" --argjson cp_avail "${CPAVAIL:-0}" \
  --arg fails "$(printf '%s\n' "${FAILS[@]}")" \
  '($fails|split("\n")|map(select(length>0))) as $f | {app:$app, ok:($f|length==0), deploy_s:$deploy_s, undeploy_s:$undeploy_s, pods:$pods,
    wget_status:$wget, steady_state:$steady_state, steady:$steady, tp:$tp,
    app_mem_working_set:$mem, mem_available_mib:($avail + {"cp-01":$cp_avail}),
    failures:$f}' | tee "$PB_RUN/summary.json"
[ ${#FAILS[@]} -eq 0 ]
