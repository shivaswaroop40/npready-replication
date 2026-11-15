#!/usr/bin/env bash
# Shared helpers for apps/<app>/*.sh. Source it; do not run it.
#
# Runs on cp-01 as root and needs kubectl, jq, curl (and openssl, python3 for bank).
# KUBECONFIG defaults to the k3s one. Service URLs are checked from the node through the
# Service ClusterIP (k3s runs kube-proxy there, since Cilium has kube-proxy-replacement=false),
# so the checks need no extra pod and add nothing to the app namespace.
#
# Conventions: progress goes to stderr; the one-line JSON from pb_state_json is the only stdout.

: "${KUBECONFIG:=/etc/rancher/k3s/k3s.yaml}"
export KUBECONFIG

# pb_init <app dir> <step>: load app.env, remember the step name and start time.
pb_init() {
  APP_DIR="$(cd "$1" && pwd)"
  PB_STEP="$2"
  set -a
  # shellcheck disable=SC1091
  . "$APP_DIR/app.env"
  set +a
  PB_T0=$(date +%s)
}

pb_log() { printf '[%s %s/%s] %s\n' "$(date -u +%H:%M:%SZ)" "${APP:-?}" "${PB_STEP:-?}" "$*" >&2; }
pb_die() { pb_log "FATAL: $*"; exit 1; }
kc() { kubectl -n "$APP_NS" "$@"; }

pb_deadline() { echo $(( $(date +%s) + $1 )); }
pb_left() { local l=$(( $1 - $(date +%s) )); (( l < 1 )) && l=1; echo "$l"; }

pb_ensure_ns() {
  kubectl create namespace "$APP_NS" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
}

# pb_apply <file>: apply a static file (never envsubst manifest.yaml: it contains Grafana "${...}" text).
pb_apply() {
  local out
  out=$(kc apply -f "$1" 2>&1) || { printf '%s\n' "$out" >&2; pb_die "apply $1 failed"; }
  pb_log "applied $(basename "$1"): $(printf '%s\n' "$out" | grep -cv ' unchanged$') changed, $(printf '%s\n' "$out" | grep -c ' unchanged$') unchanged"
}

# pb_workloads: every Deployment and StatefulSet with replicas > 0, as kind/name, one per line.
pb_workloads() {
  kc get deploy,sts -o json | jq -r '.items[] | select((.spec.replicas // 1) > 0)
    | (if .kind == "Deployment" then "deploy" else "sts" end) + "/" + .metadata.name'
}

# pb_wait_rollouts <timeout s> <kind/name>...: all of them rolled out within one shared deadline.
pb_wait_rollouts() {
  local t=$1 dl w
  shift
  dl=$(pb_deadline "$t")
  for w in "$@"; do
    kc rollout status "$w" --timeout="$(pb_left "$dl")s" >/dev/null 2>&1 \
      || pb_die "$w not rolled out within ${t}s: $(kc get "$w" -o jsonpath='{.status}' 2>/dev/null | head -c 300)"
  done
}

# pb_wait_no_terminating <timeout s>: old pods of a restart have finished terminating.
pb_wait_no_terminating() {
  local dl n
  dl=$(pb_deadline "$1")
  while :; do
    n=$(kc get pods -o json | jq '[.items[] | select(.metadata.deletionTimestamp != null)] | length')
    [ "$n" = 0 ] && return 0
    [ "$(date +%s)" -lt "$dl" ] || pb_die "$n pods still terminating after ${1}s"
    sleep 2
  done
}

pb_wait_all() {
  local ws
  mapfile -t ws < <(pb_workloads)
  [ "${#ws[@]}" -gt 0 ] || pb_die "no workloads in $APP_NS"
  pb_wait_rollouts "$1" "${ws[@]}"
  pb_log "all ${#ws[@]} workloads rolled out"
}

# pb_restart_tiers <timeout s> "<tier>" ["<tier>" ...]
# A tier is a space-separated list of kind/name; the word REST stands for every workload with
# replicas > 0 that no tier names. Tiers run in order: rollout restart all of a tier, wait for
# it, then the next. Dies if a named workload does not exist, or if any workload is missed.
# PB_RESTART_KEEP (optional, space-separated kind/name) lists workloads that are deliberately
# left running (dsb datastores); they are not part of REST and not counted as missed.
pb_restart_tiers() {
  local t=$1 tier w x
  shift
  local all named=" ${PB_RESTART_KEEP:-} " restarted=" ${PB_RESTART_KEEP:-} " items
  mapfile -t all < <(pb_workloads)
  for tier in "$@"; do
    for w in $tier; do
      [ "$w" = REST ] && continue
      printf '%s\n' "${all[@]}" | grep -qxF "$w" || pb_die "restart tier names $w, which is not a running workload"
      named+="$w "
    done
  done
  for tier in "$@"; do
    items=()
    for w in $tier; do
      if [ "$w" = REST ]; then
        for x in "${all[@]}"; do [[ "$named" == *" $x "* ]] || items+=("$x"); done
      else
        items+=("$w")
      fi
    done
    [ "${#items[@]}" -gt 0 ] || continue
    for w in "${items[@]}"; do kc rollout restart "$w" >/dev/null; done
    pb_wait_rollouts "$t" "${items[@]}"
    for w in "${items[@]}"; do restarted+="$w "; done
    pb_log "restarted and ready: ${items[*]}"
  done
  for x in "${all[@]}"; do [[ "$restarted" == *" $x "* ]] || pb_die "$x was not restarted"; done
  pb_wait_no_terminating "$t"
}

# pb_cluster_url <in-cluster URL>: http://svc[.ns.svc.cluster.local][:port]/path ->
# http://<ClusterIP>:<port>/path, reachable from any node. The Service must be in APP_NS.
pb_cluster_url() {
  local rest hostport path host port ip
  rest=${1#http://}
  hostport=${rest%%/*}
  if [ "$rest" = "$hostport" ]; then path=/; else path=/${rest#*/}; fi
  host=${hostport%%:*}
  port=${hostport##*:}
  [ "$port" = "$hostport" ] && port=80
  host=${host%%.*}
  ip=$(kc get svc "$host" -o jsonpath='{.spec.clusterIP}' 2>/dev/null) || true
  [ -n "$ip" ] || { pb_log "no Service $host in $APP_NS"; return 1; }
  echo "http://$ip:$port$path"
}

# pb_wait_http_ok <in-cluster URL> <timeout s> [curl args...]: three answers in a row with
# TP_EXPECT_STATUS (redirects are not followed).
pb_wait_http_ok() {
  local url=$1 t=$2 cu code="" ok=0 dl
  shift 2
  dl=$(pb_deadline "$t")
  while :; do
    if cu=$(pb_cluster_url "$url"); then
      code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$@" "$cu" || true)
    fi
    if [ "$code" = "${TP_EXPECT_STATUS:-200}" ]; then
      ok=$((ok + 1))
      [ "$ok" -ge 3 ] && break
      sleep 1
      continue
    fi
    ok=0
    [ "$(date +%s)" -lt "$dl" ] || pb_die "$url answered '${code}', expected ${TP_EXPECT_STATUS:-200}, for ${t}s"
    sleep 3
  done
  pb_log "$url -> $code, 3 in a row"
}

# pb_state_json [key=string | key:=json ...]: one-line JSON summary of the app's pods on stdout.
pb_state_json() {
  local extra="{}" kv
  for kv in "$@"; do
    if [[ "$kv" == *:=* ]]; then
      extra=$(jq -c --arg k "${kv%%:=*}" --argjson v "${kv#*:=}" '. + {($k): $v}' <<<"$extra")
    else
      extra=$(jq -c --arg k "${kv%%=*}" --arg v "${kv#*=}" '. + {($k): $v}' <<<"$extra")
    fi
  done
  kc get pods -o json | jq -c --arg app "$APP" --arg ns "$APP_NS" --arg step "$PB_STEP" \
    --argjson secs $(( $(date +%s) - PB_T0 )) --argjson extra "$extra" '
    [.items[] | select(.metadata.labels["app.kubernetes.io/part-of"] != "perfbench")
              | select(.status.phase == "Running" or .status.phase == "Pending")] as $p
    | {app: $app, ns: $ns, step: $step, ok: true, seconds: $secs,
       pods: ($p | length),
       ready: ([$p[] | select((.status.containerStatuses // []) | length > 0 and all(.[]; .ready))] | length),
       restarts: ([$p[] | .status.containerStatuses[]?.restartCount] | add // 0),
       not_ready: [$p[] | select((.status.containerStatuses // []) | length == 0 or any(.[]; .ready | not))
                        | .metadata.name],
       nodes: ([$p[] | .spec.nodeName] | group_by(.) | map({(.[0] // "none"): length}) | add // {})}
    + $extra'
}
