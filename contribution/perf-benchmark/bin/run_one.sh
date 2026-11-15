#!/usr/bin/env bash
# shellcheck disable=SC2329  # cleanup/on_exit/write_meta run from the EXIT trap
# run_one.sh <app> <cond> <rep|cycle> [--short | --profile full|short|cycle] [--force]
#
# One benchmark run on cp-01 (as root). Results: /opt/perfbench/results/<app>/rep<rep>/<cond>/,
# or /opt/perfbench/results/<app>/cycle<k>/<cond>/ with --profile cycle (3rd argument = cycle k)
#   1  cond.sh <cond>                       (cluster switched + verified; JSON -> cond_state.json)
#   2  apps/<app>/restart.sh                (fresh app pods); otterize: mapper reset
#   3  host-speed canary (scope pb-canary) and samplers on every node, the metrics scraper
#      (pb-scrape, every condition) and the condition's client (each in scope pb-<name>); BPF
#      program check before and at the end
#   3b idle segment: IDLE_S with the observer on and no load (standing cost, background flows)
#   4  warm-up: Job pb-warmup = steady.yaml with STEADY_SECONDS=WARMUP_S
#   5  steady window: Job pb-steady = steady.yaml with STEADY_SECONDS=STEADY_S
#      (ig_snap: snapshot_socket in the last SNAP_LEAD_S of the window, load still running)
#   6  generator stats -> steady.log
#   8  fixed-count tests: keepalive then newconn, TP_REPS each, TP_PAUSE_S apart -> tp/<mode>-<i>.log
#   9  otterize t1 query; conntrack and cilium/hubble metrics around the window and each test
#   10 stop clients and samplers, meta.json, DONE (or FAILED with the reason)
# Every phase is timestamped in phases.tsv and meta.json ("phases"). A run dir that has no
# DONE is moved aside to <cond>.attempt-<ts> before a new attempt. Exit 0 only with DONE.
# Profiles (timings; everything else is the same protocol):
#   full  (default)  60 s idle, 180 s warm-up, 1200 s window, 3 x 10000 requests per mode
#   short (--short)  30 s idle,  60 s warm-up,  240 s window, 1 x 2000 requests per mode (pipeline check)
#   cycle            60 s idle,  60 s warm-up,  300 s window, 1 x TP_N_CYCLE (app.env) requests per
#                    mode; one run of an interleaved cycle (run_matrix.sh --cycles), dir cycle<k>/
# Env overrides: PB_IDLE_S PB_WARMUP_S PB_STEADY_S PB_TP_REPS PB_TP_N PB_TP_C PB_TP_PAUSE_S
#                PB_SNAP_LEAD_S PB_TP_TIMEOUT_S PB_GADGET_TAG PB_SAMPLE_S PB_PLAY_ID
#                PB_CANARY (0 = no canary) PB_CANARY_S PB_CANARY_ITERS
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PB_ROOT=${PB_ROOT:-$(dirname "$HERE")}
# shellcheck source=lib.sh source-path=SCRIPTDIR
. "$HERE/lib.sh"

usage() { echo "usage: run_one.sh <app> <baseline|hubble|hubble_agent|otterize|ig_tcp|ig_snap> <rep|cycle> [--short | --profile full|short|cycle] [--force]" >&2; exit 2; }
[ $# -ge 3 ] || usage
APP=$1 COND=$2 REP=$3; shift 3
SHORT=0 FORCE=0 PROFILE=""
while [ $# -gt 0 ]; do
  case $1 in
    --short) [ -z "$PROFILE" ] || [ "$PROFILE" = short ] || usage; PROFILE=short ;;
    --profile) [ $# -ge 2 ] || usage; [ -z "$PROFILE" ] || [ "$PROFILE" = "$2" ] || usage; PROFILE=$2; shift ;;
    --profile=*) [ -z "$PROFILE" ] || [ "$PROFILE" = "${1#*=}" ] || usage; PROFILE=${1#*=} ;;
    --force) FORCE=1 ;;
    *) usage ;;
  esac
  shift
done
PROFILE=${PROFILE:-full}
case $PROFILE in full|short|cycle) ;; *) usage ;; esac
[ "$PROFILE" = short ] && SHORT=1
LAYOUT=rep; [ "$PROFILE" = cycle ] && LAYOUT=cycle
case " $PB_CONDS_KNOWN " in *" $COND "*) ;; *) usage ;; esac
[[ $REP =~ ^[0-9]+$ ]] || usage

# d_n for cycle is a placeholder: TP_N_CYCLE comes from app.env, read after pb_load_app
case $PROFILE in
  short) d_i=30 d_w=60  d_s=240  d_r=1 d_n=2000 ;;
  cycle) d_i=60 d_w=60  d_s=300  d_r=1 d_n=2000 ;;
  *)     d_i=60 d_w=180 d_s=1200 d_r=3 d_n=10000 ;;
esac
IDLE_S=${PB_IDLE_S:-$d_i}
WARMUP_S=${PB_WARMUP_S:-$d_w}
STEADY_S=${PB_STEADY_S:-$d_s}
TP_REPS=${PB_TP_REPS:-$d_r}
TP_N=${PB_TP_N:-$d_n}
TP_C=${PB_TP_C:-16}
TP_PAUSE_S=${PB_TP_PAUSE_S:-20}
SNAP_LEAD_S=${PB_SNAP_LEAD_S:-45}
export TP_N TP_C

PB_RUN=$PB_RESULTS/$APP/$LAYOUT$REP/$COND
PB_RUN_ID="$APP-$LAYOUT$REP-$COND"
if [ "$FORCE" = 0 ] && pb_run_done "$PB_RUN" "$SHORT" "$PROFILE"; then echo "run_one: $PB_RUN already DONE (use --force)" >&2; exit 0; fi

if [ "${PB_LOCK_HELD:-0}" != 1 ]; then
  exec 8>"$PB_LOCK"
  flock -n 8 || { echo "run_one: another perfbench run holds $PB_LOCK" >&2; exit 1; }
fi
if [ -d "$PB_RUN" ]; then mv "$PB_RUN" "$PB_RUN.attempt-$(date -u +%Y%m%dT%H%M%SZ)"; fi
mkdir -p "$PB_RUN"/{jobs,tp,ct,metrics}
: > "$PB_RUN/phases.tsv"; : > "$PB_RUN/kv.tsv"; : > "$PB_RUN/tp.jsonl"

STATUS=RUNNING FAIL_MSG="" CUR_PHASE=init SNAP_DONE=0 SAMPLERS_STARTED=0 CANARY_STARTED=0
pb_fail() { FAIL_MSG="$*"; pb_log "FAILED: $*"; exit 1; }

# shellcheck disable=SC2097,SC2098  # values are passed to python through its environment
write_meta() { # status
  PB_STATUS=$1 PB_FAIL_MSG=$FAIL_MSG APP=$APP COND=$COND REP=$REP SHORT=$SHORT PROFILE=$PROFILE LAYOUT=$LAYOUT \
  CANARY_ON=$PB_CANARY CANARY_S=$PB_CANARY_S CANARY_ITERS=$PB_CANARY_ITERS \
  IDLE_S=$IDLE_S GADGET_TAG_USED="$(pb_gadget_tag)" \
  WARMUP_S=$WARMUP_S STEADY_S=$STEADY_S TP_REPS=$TP_REPS TP_PAUSE_S=$TP_PAUSE_S \
  SNAP_LEAD_S=$SNAP_LEAD_S PB_NODES=$PB_NODES PB_CP_NODE=$PB_CP_NODE PB_SAMPLE_S=$PB_SAMPLE_S \
  PB_APP_VARS=${PB_APP_VARS:-} TP_FLAGS_KEEPALIVE=${TP_FLAGS_KEEPALIVE-} \
  TP_FLAGS_NEWCONN=${TP_FLAGS_NEWCONN--disable-keepalive} \
  ADDRS="$(for n in $PB_NODES; do printf '%s=%s ' "$n" "$(pb_addr "$n")"; done)" \
  python3 - "$PB_RUN" <<'PY'
import json, os, sys
run = sys.argv[1]
E = os.environ
def rd(name, default=None):
    try:
        with open(os.path.join(run, name)) as f:
            return f.read()
    except OSError:
        return default
def rjson(name):
    t = rd(name)
    if not t:
        return None
    try:
        return json.loads(t)
    except ValueError:
        return {"unparsed": t[-2000:]}
phases, order = {}, []
for line in (rd("phases.tsv") or "").splitlines():
    p = line.split("\t")
    if len(p) >= 2:
        phases[p[0]] = float(p[1]); order.append(p[0])
kv = {}
for line in (rd("kv.tsv") or "").splitlines():
    k, _, v = line.partition("\t")
    kv[k] = v
tp = []
for line in (rd("tp.jsonl") or "").splitlines():
    try:
        tp.append(json.loads(line))
    except ValueError:
        pass
nodes = E["PB_NODES"].split()
steady = {}
if "steady_start" in phases:
    steady = {"start": phases["steady_start"],
              "end_nominal": phases["steady_start"] + float(E["STEADY_S"]),
              "job_complete": phases.get("steady_job_complete")}
app_env = {k: E.get(k, "") for k in E.get("PB_APP_VARS", "").split()}
meta = {
    "schema": 1,
    "status": E["PB_STATUS"], "error": E.get("PB_FAIL_MSG") or None,
    "app": E["APP"], "app_ns": app_env.get("APP_NS") or E.get("APP_NS"), "cond": E["COND"],
    "rep": int(E["REP"]), "short": E["SHORT"] == "1",
    "profile": E.get("PROFILE", "full"), "layout": E.get("LAYOUT", "rep"),
    "cycle": int(E["REP"]) if E.get("LAYOUT") == "cycle" else None,
    "params": {
        "idle_s": float(E["IDLE_S"]), "gadget_tag": E.get("GADGET_TAG_USED"),
        "warmup_s": float(E["WARMUP_S"]), "steady_s": float(E["STEADY_S"]),
        "tp_reps": int(E["TP_REPS"]), "tp_n": int(E["TP_N"]), "tp_c": int(E["TP_C"]),
        "tp_pause_s": float(E["TP_PAUSE_S"]), "snap_lead_s": float(E["SNAP_LEAD_S"]),
        "sample_s": float(E["PB_SAMPLE_S"]),
        "tp_flags": {"keepalive": E.get("TP_FLAGS_KEEPALIVE", ""),
                     "newconn": E.get("TP_FLAGS_NEWCONN", "")},
        "order_seed": E.get("PB_ORDER_SEED"), "order_pos": E.get("PB_ORDER_POS"),
        "order_design": E.get("PB_ORDER_DESIGN"), "order_seq": E.get("PB_ORDER_SEQ"),
        "attempt": E.get("PB_ATTEMPT"),
        "canary": E.get("CANARY_ON") == "1", "canary_s": float(E.get("CANARY_S") or 0),
        "canary_iters": int(E["CANARY_ITERS"]) if E.get("CANARY_ITERS") else None,
    },
    "app_env": app_env,
    "phases": phases, "phase_order": order, "steady_window": steady,
    "nodes": {
        "cp": E["PB_CP_NODE"], "list": nodes,
        "addr": dict(x.split("=", 1) for x in E.get("ADDRS", "").split() if "=" in x),
        "clock_offset_s": {n: float(kv["clock_offset_s." + n]) for n in nodes
                           if kv.get("clock_offset_s." + n)},
        "k8s": rjson("nodes.json"),
    },
    "cond_state": rjson("cond_state.json"),
    "host": rjson("hostinfo.json"),
    "bpf": {"pre": rjson("bpf_pre.json"), "final": rjson("bpf_final.json")},
    "versions": rjson("versions.json"),
    "tp_tests": tp,
    "kv": kv,
    "warnings": [w for w in (rd("warnings.txt") or "").splitlines() if w],
}
with open(os.path.join(run, "meta.json"), "w") as f:
    json.dump(meta, f, indent=1, sort_keys=False)
PY
}

cleanup() {
  CUR_PHASE=cleanup
  local n
  pb_stop_all_clients
  K -n "${APP_NS:-default}" delete job -l perfbench=1 --ignore-not-found --wait=false >/dev/null 2>&1
  if [ "$SAMPLERS_STARTED" = 1 ]; then
    for n in $PB_NODES; do pb_sampler_stop_fetch "$n" || true; done
    pb_mark samplers_stopped
  fi
  if [ "$CANARY_STARTED" = 1 ]; then
    for n in $PB_NODES; do pb_canary_stop_fetch "$n" || true; done
    pb_mark canary_stopped
  fi
}

on_exit() {
  local rc=$?
  trap - EXIT INT TERM
  if [ "$STATUS" != DONE ] && [ -z "$FAIL_MSG" ]; then
    FAIL_MSG="exited rc=$rc in phase $CUR_PHASE"
  fi
  cleanup
  pb_mark run_end
  [ "$STATUS" = DONE ] || STATUS=FAILED
  write_meta "$STATUS" || pb_log "meta.json write failed"
  if [ "$STATUS" = DONE ]; then
    jq -cn --arg app "$APP" --arg cond "$COND" --argjson rep "$REP" --arg ts "$(pb_iso)" \
      --arg profile "$PROFILE" --arg layout "$LAYOUT" \
      '{app:$app, cond:$cond, rep:$rep, done:$ts, profile:$profile, layout:$layout}' > "$PB_RUN/DONE"
    pb_log "DONE $PB_RUN_ID"
    exit 0
  fi
  printf '%s\n' "$FAIL_MSG" > "$PB_RUN/FAILED"
  pb_log "run $PB_RUN_ID FAILED: $FAIL_MSG"
  exit 1
}
trap on_exit EXIT
trap 'FAIL_MSG="signal received in phase $CUR_PHASE"; exit 1' INT TERM

# ---------------------------------------------------------------------------------------------
pb_mark run_start
pb_load_app "$APP" || pb_fail "cannot load apps/$APP"
# cycle profile: the fixed-count size is per app (TP_N_CYCLE in app.env, sized for 30-60 s a test);
# PB_TP_N still wins
if [ "$PROFILE" = cycle ] && [ -z "${PB_TP_N:-}" ]; then
  TP_N=${TP_N_CYCLE:-}
  [[ $TP_N =~ ^[1-9][0-9]*$ ]] || { pb_warn "apps/$APP/app.env has no valid TP_N_CYCLE ('$TP_N'); using $d_n"; TP_N=$d_n; }
fi
export TP_N TP_C
# hey sends N/C requests per worker: an N that is not a multiple of C sends fewer than N, and the
# analysis rejects the test (boutique TP_N_CYCLE=3000 at c16 sent 2992, 2026-10-03)
if [[ $TP_N =~ ^[0-9]+$ ]] && [[ $TP_C =~ ^[1-9][0-9]*$ ]] && [ $((TP_N % TP_C)) -ne 0 ]; then
  pb_warn "TP_N=$TP_N is not a multiple of TP_C=$TP_C: hey sends $((TP_N / TP_C * TP_C)) requests and the analysis rejects every fixed-count test"
fi
pb_log "run $PB_RUN_ID (profile=$PROFILE idle=${IDLE_S}s warmup=${WARMUP_S}s steady=${STEADY_S}s tp=${TP_REPS}x${TP_N}/c${TP_C} canary=$PB_CANARY)"
# per-test watchdog: PB_TP_TIMEOUT_S (env) > TP_TIMEOUT_S (app.env; bank needs ~15 min a test) > 900
TP_TIMEOUT_S=${PB_TP_TIMEOUT_S:-${TP_TIMEOUT_S:-900}}
K get ns "$APP_NS" >/dev/null 2>&1 || pb_fail "namespace $APP_NS missing (run apps/$APP/deploy.sh or run_matrix.sh)"

CUR_PHASE=preflight
pb_resolve_nodes
pb_stop_all_clients
K -n "$APP_NS" delete job -l perfbench=1 --ignore-not-found --wait=true --timeout=120s >/dev/null 2>&1
for n in $PB_NODES; do pb_sampler_kill "$n"; pb_canary_kill "$n"; done
pb_clock_offsets
pb_hostinfo "$PB_RUN/hostinfo.json" || pb_warn "host info not recorded"
K get nodes -o json | jq '[.items[] | {name: .metadata.name, kernel: .status.nodeInfo.kernelVersion,
    kubelet: .status.nodeInfo.kubeletVersion, os: .status.nodeInfo.osImage,
    runtime: .status.nodeInfo.containerRuntimeVersion, cpu: .status.capacity.cpu,
    memory: .status.capacity.memory, allocatable_cpu: .status.allocatable.cpu,
    taints: (.spec.taints // [])}]' > "$PB_RUN/nodes.json" 2>/dev/null
{
  printf '{'
  printf '"kubectl": %s,' "$(K version -o json 2>/dev/null | jq -c . 2>/dev/null || echo null)"
  printf '"k3s": %s,' "$(k3s --version 2>/dev/null | head -1 | jq -Rs 'rtrimstr("\n")')"
  printf '"hubble_cli": %s,' "$(hubble version 2>/dev/null | head -1 | jq -Rs 'rtrimstr("\n")')"
  printf '"kubectl_gadget": %s,' "$(kubectl-gadget version 2>/dev/null | jq -Rs 'rtrimstr("\n")')"
  printf '"gadgets": %s,' "$(jq -cn --arg a "$(pb_gadget_ref trace_tcp)" --arg b "$(pb_gadget_ref snapshot_socket)" '[$a,$b]')"
  printf '"gadget_server": %s,' "$(kubectl-gadget version 2>/dev/null | awk '/Server version/{print $3}' | jq -Rs 'rtrimstr("\n")')"
  printf '"helm_releases": %s' "$(helm list -A -o json 2>/dev/null | jq -c '[.[] | {name, namespace, chart, app_version}]' 2>/dev/null || echo null)"
  printf '}\n'
} > "$PB_RUN/versions.json"

# 1) condition ----------------------------------------------------------------------------------
CUR_PHASE=cond
pb_mark cond_start
bash "$PB_BIN/cond.sh" "$COND" > "$PB_RUN/cond.out" 2> "$PB_RUN/cond.err"; rc=$?
pb_mark cond_end
grep -E '^\{' "$PB_RUN/cond.out" | tail -1 > "$PB_RUN/cond_state.json"
[ "$rc" = 0 ] || pb_fail "cond.sh $COND exit $rc: $(tail -n 3 "$PB_RUN/cond.err" | tr '\n' ' ')"
jq -e '.ok == true' "$PB_RUN/cond_state.json" >/dev/null 2>&1 || pb_warn "cond.sh state JSON missing or not ok"

# 2) fresh app ---------------------------------------------------------------------------------------
CUR_PHASE=app_restart
pb_mark app_restart_start
bash "$PB_APP_DIR/restart.sh" > "$PB_RUN/restart.log" 2>&1 || pb_fail "restart.sh failed: $(tail -n 3 "$PB_RUN/restart.log" | tr '\n' ' ')"
# restart.sh waits for rollouts, which a crash-looping pod can pass between two restarts.
# Every app pod must be Ready, or the run measures a broken app. Terminated pods (finished init
# Jobs, the OTel chart's grafana-test hook pod, which fails while grafana is at 0) are ignored.
# A crash-looping pod can also be Ready for a moment between two restarts, so the pods must stay
# Ready with unchanged restart counts for STABLE_S (20 s) before the run goes on.
NOT_READY="" STABLE_S=20
app_pod_state() {
  K -n "$APP_NS" get pods -o json 2>/dev/null | jq -r '[.items[] | select(.status.phase != "Succeeded" and .status.phase != "Failed")
    | select(.metadata.labels.perfbench != "1")] as $p
    | ([$p[] | select(((.status.containerStatuses // []) | length == 0) or any(.status.containerStatuses[]; .ready | not))
        | .metadata.name] | join(" ")) + "|" + ([$p[] | "\(.metadata.name)=\([.status.containerStatuses[]?.restartCount] | add // 0)"] | sort | join(","))'
}
deadline=$((EPOCHSECONDS + 180))
while :; do
  st=$(app_pod_state); NOT_READY=${st%%|*}
  if [ -z "$NOT_READY" ]; then
    sleep "$STABLE_S"
    st2=$(app_pod_state)
    [ "${st2%%|*}" = "" ] && [ "${st2#*|}" = "${st#*|}" ] && break
    NOT_READY="unstable: ${st2%%|*} restarts ${st#*|} -> ${st2#*|}"
  fi
  [ "$EPOCHSECONDS" -lt "$deadline" ] || break
  sleep 2
done
[ -z "$NOT_READY" ] || pb_fail "app pods not Ready and stable for ${STABLE_S} s within 180 s after restart.sh: $NOT_READY"
pb_mark app_restart_end
if [ "$COND" = otterize ]; then   # thesis "otterize reset", right before capture
  pb_mark otterize_reset_start
  K -n otterize-system rollout restart deployment/otterize-network-mapper >/dev/null || pb_fail "otterize reset failed"
  K -n otterize-system rollout status deployment/otterize-network-mapper --timeout=300s >/dev/null || pb_fail "otterize mapper not ready after reset"
  pb_mark otterize_reset_end
fi
K get pods -A -o wide > "$PB_RUN/pods_start.txt" 2>&1
K -n "$APP_NS" get pods -o json | jq '[.items[] | {name: .metadata.name, node: .spec.nodeName, phase: .status.phase,
  containers: [.status.containerStatuses[]? | {name, image, imageID, restartCount}]}]' > "$PB_RUN/app_pods_start.json" 2>/dev/null

# BPF programs before anything of the run starts. Without IG only Cilium's own may be loaded;
# with the IG DaemonSet on, also its standing container-collection set. Any other tracing program
# (kprobe, tracepoint, raw_tracepoint, perf_event) would be a gadget left over from an earlier run
# or from cond.sh's warm-up, and the run would measure it.
CUR_PHASE=bpf_check
pb_bpf_state "$PB_RUN/bpf_pre.json" || pb_warn "BPF state not recorded"
BPF_PRE=$(jq -r '.tracing_progs_total // "?"' "$PB_RUN/bpf_pre.json" 2>/dev/null || echo "?")
BPF_PRE_G=$(jq -r '.gadget_progs_total // "?"' "$PB_RUN/bpf_pre.json" 2>/dev/null || echo "?")
pb_kv bpf_pre_tracing_progs "$BPF_PRE"
pb_kv bpf_pre_gadget_progs "$BPF_PRE_G"
case $COND in
  ig_tcp|ig_snap) [ "$BPF_PRE_G" = 0 ] || pb_fail "gadget BPF programs loaded before the run: $BPF_PRE_G ($(jq -c '.nodes | map_values(.gadget_prog_names)' "$PB_RUN/bpf_pre.json" 2>/dev/null))" ;;
  *) [ "$BPF_PRE" = 0 ] || pb_fail "tracing BPF programs loaded before the run: $BPF_PRE ($(jq -c '.nodes | map_values(.progs)' "$PB_RUN/bpf_pre.json" 2>/dev/null))" ;;
esac

# 3) samplers + client -------------------------------------------------------------------------
# the canary starts first, so the sampler sees its scope from the first tick
CUR_PHASE=canary
if [ "$PB_CANARY" = 1 ]; then
  CANARY_STARTED=1
  for n in $PB_NODES; do pb_canary_start "$n" || pb_warn "host-speed canary did not start on $n"; done
fi
CUR_PHASE=samplers
SAMPLERS_STARTED=1
for n in $PB_NODES; do pb_sampler_start "$n" || pb_fail "sampler did not start on $n"; done
sleep 3
for n in $PB_NODES; do pb_sampler_ok "$n" || pb_fail "sampler on $n is not writing"; done
if [ "$CANARY_STARTED" = 1 ]; then
  for n in $PB_NODES; do pb_canary_ok "$n" || pb_warn "host-speed canary on $n is not writing"; done
fi
pb_mark samplers_started
# test-cluster' Prometheus scraped :9962/:9965 every 15 s; pb-scrape does the same in every condition
pb_client_start scrape "$PB_RUN/scrape.log" "$PB_RUN/scrape.err" bash -c "$(pb_scrape_loop_cmd)" \
  || pb_fail "metrics scraper did not start"

CUR_PHASE=client
CLIENT=""
case $COND in
  hubble)
    pb_kv relay_ip "$(K -n kube-system get svc hubble-relay -o jsonpath='{.spec.clusterIP}')"
    # As the thesis did (BANK-20260904/bank_capture.sh): kubectl port-forward svc/hubble-relay
    # through the API server and kubelet, and hubble observe against localhost; both restart on exit.
    HPORT=4247
    pb_client_start hubblepf "$PB_RUN/hubble-pf.log" "$PB_RUN/hubble-pf.err" bash -c \
      "while :; do kubectl -n kube-system port-forward svc/hubble-relay $HPORT:80; echo \"# port-forward exited rc=\$? at \$(date +%s)\" >&2; sleep 1; done" \
      || pb_fail "hubble-relay port-forward did not start: $(tail -n 3 "$PB_RUN/hubble-pf.err" | tr '\n' ' ')"
    for _ in $(seq 30); do ss -ltnH 2>/dev/null | grep -q "127.0.0.1:$HPORT " && break; sleep 1; done
    pb_client_start hubble "$PB_RUN/hubble.json" "$PB_RUN/hubble.err" bash -c \
      "while :; do hubble observe --server 'localhost:$HPORT' --namespace '$APP_NS' -o json --follow; echo \"# hubble observe exited rc=\$? at \$(date +%s)\" >&2; sleep 2; done" \
      || pb_fail "hubble observe client did not start: $(tail -n 3 "$PB_RUN/hubble.err" | tr '\n' ' ')"
    CLIENT=hubble ;;
  ig_tcp)
    pb_client_start igtcp "$PB_RUN/ig_tcp.json" "$PB_RUN/ig_tcp.err" \
      kubectl gadget run "$(pb_gadget_ref trace_tcp)" -n "$APP_NS" -o json \
      || pb_fail "trace_tcp client did not start: $(tail -n 3 "$PB_RUN/ig_tcp.err" | tr '\n' ' ')"
    CLIENT=igtcp ;;
  otterize)
    pb_mark otterize_t0
    pb_otterize_query "$PB_RUN/otterize_t0.json" otterize-t0 || pb_warn "otterize t0 query failed"
    pb_kv otterize_t0_bytes "$(wc -c < "$PB_RUN/otterize_t0.json" 2>/dev/null || echo 0)" ;;
esac
pb_mark client_started

# 3b) idle segment: observer on, app up, no load. Gives each condition's standing cost per node
# and the background connection rate (kubelet probes) to subtract from the flow counts.
CUR_PHASE=idle
pb_ct_snap idle_pre
pb_mark idle_start
sleep "$IDLE_S"
pb_mark idle_end
pb_ct_snap idle_post

# 4) warm-up ------------------------------------------------------------------------------------
CUR_PHASE=warmup
TPL_VARS="$PB_APP_VARS STEADY_SECONDS APP_NS TP_URL TP_HEADERS"
export STEADY_SECONDS=$WARMUP_S
# shellcheck disable=SC2086
pb_job_create "$APP_NS" pb-warmup "$PB_APP_DIR/steady.yaml" $TPL_VARS || pb_fail "cannot create warm-up Job"
pb_mark warmup_created
pb_job_wait_started "$APP_NS" pb-warmup 300 || pb_fail "warm-up pod did not start: $(pb_job_state "$APP_NS" pb-warmup)"
pb_mark warmup_start
pb_job_wait_finished "$APP_NS" pb-warmup $((WARMUP_S + 300)) 5 || pb_fail "warm-up Job did not finish"
pb_mark warmup_end
pb_job_logs "$APP_NS" pb-warmup "$PB_RUN/warmup.log"
pb_kv warmup_state "$(pb_job_state "$APP_NS" pb-warmup)"
K -n "$APP_NS" delete job pb-warmup --wait=false >/dev/null 2>&1

# 5) steady window ----------------------------------------------------------------------------------
CUR_PHASE=steady
pb_ct_snap steady_pre
pb_metrics_scrape steady_pre
export STEADY_SECONDS=$STEADY_S
# shellcheck disable=SC2086
pb_job_create "$APP_NS" pb-steady "$PB_APP_DIR/steady.yaml" $TPL_VARS || pb_fail "cannot create steady Job"
pb_mark steady_created
pb_job_wait_started "$APP_NS" pb-steady 300 || pb_fail "steady pod did not start: $(pb_job_state "$APP_NS" pb-steady)"
pb_mark steady_start
T_START=${EPOCHSECONDS}
END_NOM=$((T_START + STEADY_S))
SNAP_AT=$((END_NOM - SNAP_LEAD_S))
pb_kv steady_state_at_start "$(pb_job_state "$APP_NS" pb-steady)"

ig_snapshot() { # thesis: up to 3 tries x 12 s, stop at the first non-empty JSON
  local t ok=0 ref sp i
  ref=$(pb_gadget_ref snapshot_socket)
  pb_mark snap_start
  for t in 1 2 3; do
    systemctl reset-failed "pb-igsnap-$t.scope" >/dev/null 2>&1
    systemd-run --scope --quiet --unit="pb-igsnap-$t" -- kubectl gadget run "$ref" -n "$APP_NS" -o json \
      > "$PB_RUN/ig_snap.json" 2>> "$PB_RUN/ig_snap.err" </dev/null 8>&- &
    sp=$!
    for i in $(seq 1 12); do kill -0 "$sp" 2>/dev/null || break; sleep 1; done
    kill "$sp" 2>/dev/null; systemctl stop "pb-igsnap-$t.scope" >/dev/null 2>&1; wait "$sp" 2>/dev/null
    sleep 1
    if python3 -c 'import json,sys; a=json.load(open(sys.argv[1])); sys.exit(0 if a else 1)' "$PB_RUN/ig_snap.json" 2>/dev/null; then
      ok=1; break
    fi
    pb_log "snapshot_socket retry $t (i=$i)"
  done
  pb_mark snap_end
  pb_kv snap_attempts "$t"; pb_kv snap_ok "$ok"
  pb_kv snap_bytes "$(wc -c < "$PB_RUN/ig_snap.json" 2>/dev/null || echo 0)"
  SNAP_DONE=1
  [ "$ok" = 1 ] || pb_warn "snapshot_socket returned no sockets after 3 tries"
}

LAST_CHECK=$EPOCHSECONDS EARLY=0
while [ "$EPOCHSECONDS" -lt $((END_NOM - 3)) ]; do
  if [ "$COND" = ig_snap ] && [ "$SNAP_DONE" = 0 ] && [ "$EPOCHSECONDS" -ge "$SNAP_AT" ]; then ig_snapshot; fi
  if [ $((EPOCHSECONDS - LAST_CHECK)) -ge 120 ]; then
    LAST_CHECK=$EPOCHSECONDS
    if pb_job_finished "$APP_NS" pb-steady; then EARLY=1; break; fi
    msg="steady $((END_NOM - EPOCHSECONDS))s left"
    case $CLIENT in
      hubble) msg+=" hubble_lines=$(wc -l < "$PB_RUN/hubble.json")" ;;
      igtcp)  msg+=" igtcp_lines=$(wc -l < "$PB_RUN/ig_tcp.json")" ;;
    esac
    if [ -n "$CLIENT" ] && ! pb_client_alive "$CLIENT"; then pb_warn "client $CLIENT died during the steady window"; fi
    pb_log "$msg"
  fi
  sleep 1
done
pb_job_wait_finished "$APP_NS" pb-steady $((END_NOM + 300 - EPOCHSECONDS)) 2 || pb_fail "steady Job overran its window by 300 s"
pb_mark steady_job_complete
pb_ct_snap steady_post
pb_metrics_scrape steady_post
if [ "$EARLY" = 1 ] || [ "$EPOCHSECONDS" -lt $((END_NOM - 60)) ]; then
  pb_job_logs "$APP_NS" pb-steady "$PB_RUN/steady.log"
  pb_fail "steady generator ended $((END_NOM - EPOCHSECONDS))s early: $(pb_job_state "$APP_NS" pb-steady)"
fi

# 6) generator stats ------------------------------------------------------------------------------
CUR_PHASE=steady_stats
pb_job_logs "$APP_NS" pb-steady "$PB_RUN/steady.log"
pb_kv steady_state "$(pb_job_state "$APP_NS" pb-steady)"
[ -s "$PB_RUN/steady.log" ] || pb_fail "steady generator printed nothing"
K -n "$APP_NS" delete job pb-steady --wait=false >/dev/null 2>&1

# 7) ig_snap: normally done inside the window; only a short window can skip it
if [ "$COND" = ig_snap ] && [ "$SNAP_DONE" = 0 ]; then ig_snapshot; fi

# 8) fixed-count tests ------------------------------------------------------------------------------
CUR_PHASE=throughput
pb_mark throughput_start
for mode in keepalive newconn; do
  if [ "$mode" = keepalive ]; then TP_FLAGS=${TP_FLAGS_KEEPALIVE-}; else TP_FLAGS=${TP_FLAGS_NEWCONN--disable-keepalive}; fi
  export TP_FLAGS
  for i in $(seq 1 "$TP_REPS"); do
    name="pb-tp-$mode-$i" tag="tp_${mode}_$i"
    if [ -n "${TP_PRE_HOOK:-}" ]; then   # e.g. bank: refresh the session cookie (expires after 1 h)
      { echo "# $(pb_iso) before $mode #$i"; (cd "$PB_APP_DIR" && bash "./$TP_PRE_HOOK"); } \
        >> "$PB_RUN/tp_pre_hook.log" 2>&1 || pb_warn "TP_PRE_HOOK $TP_PRE_HOOK failed before $mode #$i"
    fi
    pb_ct_snap "$tag.pre"
    t_created=$(pb_now) t_start="" t_end="" ok=true err=""
    # shellcheck disable=SC2086
    if ! pb_job_create "$APP_NS" "$name" "$PB_APP_DIR/throughput.yaml" $PB_APP_VARS TP_N TP_C TP_FLAGS TP_URL TP_HEADERS APP_NS; then
      ok=false err="create failed"
    elif ! pb_job_wait_started "$APP_NS" "$name" 300; then
      ok=false err="pod did not start"
    else
      t_start=$(pb_now); pb_mark "${tag}_start"
      # poll every 2 s: the test pod shares cp-01 with this loop (hey's own Total is the metric)
      pb_job_wait_finished "$APP_NS" "$name" "$TP_TIMEOUT_S" 2 || { ok=false; err="timeout ${TP_TIMEOUT_S}s"; }
      t_end=$(pb_now); pb_mark "${tag}_end"
    fi
    pb_ct_snap "$tag.post"
    pb_job_logs "$APP_NS" "$name" "$PB_RUN/tp/$mode-$i.log"
    read -r pod phase exitc started <<<"$(pb_job_state "$APP_NS" "$name")"
    [ "$phase" = Succeeded ] || { ok=false; err="${err:+$err; }pod phase $phase exit $exitc"; }
    jq -cn --arg mode "$mode" --argjson i "$i" --arg job "$name" --arg pod "$pod" --arg phase "$phase" \
      --arg exit "$exitc" --arg started_at "$started" --arg created "$t_created" --arg start "$t_start" \
      --arg end "$t_end" --argjson ok "$ok" --arg err "$err" --arg flags "$TP_FLAGS" \
      --argjson n "$TP_N" --argjson c "$TP_C" --arg log "tp/$mode-$i.log" --arg ct "ct/$tag" \
      '{mode:$mode, i:$i, job:$job, pod:$pod, phase:$phase, exit:$exit, container_started_at:$started_at,
        created:($created|tonumber), start:(if $start=="" then null else ($start|tonumber) end),
        end:(if $end=="" then null else ($end|tonumber) end), ok:$ok, error:$err, flags:$flags,
        n:$n, c:$c, log:$log, ct_prefix:$ct}' >> "$PB_RUN/tp.jsonl"
    [ "$ok" = true ] || pb_warn "fixed-count $mode #$i: $err"
    K -n "$APP_NS" delete job "$name" --wait=false >/dev/null 2>&1
    pb_log "fixed-count $mode #$i ok=$ok $(grep -m1 -E 'Total:' "$PB_RUN/tp/$mode-$i.log" | tr -s ' \t' ' ')"
    sleep "$TP_PAUSE_S"
  done
done
pb_mark throughput_end

# 9) end-of-run queries ------------------------------------------------------------------------------
CUR_PHASE=final
if [ "$COND" = otterize ]; then
  pb_mark otterize_t1
  pb_otterize_query "$PB_RUN/otterize_t1.json" otterize-t1 || pb_warn "otterize t1 query failed"
  pb_kv otterize_t1_bytes "$(wc -c < "$PB_RUN/otterize_t1.json" 2>/dev/null || echo 0)"
  pb_kv otterize_t1_intents_app "$(jq --arg ns "$APP_NS" '[.data.serviceIntents[]? | select(.client.namespace == $ns)] | length' "$PB_RUN/otterize_t1.json" 2>/dev/null || echo -1)"
fi
pb_metrics_scrape final
K get pods -A -o wide > "$PB_RUN/pods_end.txt" 2>&1
K -n "$APP_NS" get pods -o json | jq '[.items[] | {name: .metadata.name, node: .spec.nodeName, phase: .status.phase,
  containers: [.status.containerStatuses[]? | {name, image, imageID, restartCount}]}]' > "$PB_RUN/app_pods_end.json" 2>/dev/null
R0=$(jq '[.[] | select(.name | startswith("pb-") | not) | .containers[].restartCount] | add // 0' "$PB_RUN/app_pods_start.json" 2>/dev/null || echo 0)
R1=$(jq '[.[] | select(.name | startswith("pb-") | not) | .containers[].restartCount] | add // 0' "$PB_RUN/app_pods_end.json" 2>/dev/null || echo 0)
pb_kv app_restarts_during_run "$((R1 - R0))"
# a restart inside the run means the app was partly down while it was measured: fail, so
# run_matrix.sh retries the run
[ "$((R1 - R0))" -le 0 ] || pb_fail "app containers restarted $((R1 - R0)) times during the run: $(jq -r '[.[] | select([.containers[].restartCount] | add > 0) | .name] | join(" ")' "$PB_RUN/app_pods_end.json" 2>/dev/null)"

# BPF programs at the end, clients still running: trace_tcp's kprobes must be there in ig_tcp
# and nowhere else (snapshot_socket uses iterators, Hubble and Otterize load none).
pb_bpf_state "$PB_RUN/bpf_final.json" || pb_warn "final BPF state not recorded"
BPF_FIN=$(jq -r '.tracing_progs_total // "?"' "$PB_RUN/bpf_final.json" 2>/dev/null || echo "?")
BPF_FIN_G=$(jq -r '.gadget_progs_total // "?"' "$PB_RUN/bpf_final.json" 2>/dev/null || echo "?")
pb_kv bpf_final_tracing_progs "$BPF_FIN"
pb_kv bpf_final_gadget_progs "$BPF_FIN_G"
case $COND in
  ig_tcp) [ "$BPF_FIN_G" != 0 ] || pb_warn "ig_tcp: no gadget BPF programs loaded at the end (client not tracing?)" ;;
  ig_snap) [ "$BPF_FIN_G" = 0 ] || pb_warn "ig_snap: $BPF_FIN_G gadget BPF programs loaded at the end" ;;
  *) [ "$BPF_FIN" = 0 ] || pb_warn "$COND: $BPF_FIN tracing BPF programs loaded at the end" ;;
esac

# 10) stop clients and samplers, compress, finish ------------------------------------------------------
CUR_PHASE=stop
if [ -n "$CLIENT" ]; then
  pb_client_alive "$CLIENT" || pb_warn "client $CLIENT was not running at the end"
  pb_client_stop "$CLIENT"
  [ "$CLIENT" = hubble ] && pb_client_stop hubblepf
  pb_mark clients_stopped
fi
pb_client_alive scrape || pb_warn "metrics scraper was not running at the end"
pb_client_stop scrape
pb_kv scrape_cycles "$(awk '{print $1}' "$PB_RUN/scrape.log" 2>/dev/null | sort -u | wc -l)"
for n in $PB_NODES; do pb_sampler_stop_fetch "$n" || pb_fail "no samples from $n"; done
SAMPLERS_STARTED=0
pb_mark samplers_stopped
if [ "$CANARY_STARTED" = 1 ]; then   # a missing canary costs the normalised numbers, not the run
  for n in $PB_NODES; do pb_canary_stop_fetch "$n" || pb_warn "no canary samples from $n"; done
  CANARY_STARTED=0
  pb_mark canary_stopped
fi
for f in hubble.json ig_tcp.json; do
  [ -f "$PB_RUN/$f" ] || continue
  pb_kv "client_out.$f.lines" "$(wc -l < "$PB_RUN/$f")"
  pb_kv "client_out.$f.bytes" "$(wc -c < "$PB_RUN/$f")"
done
[ -f "$PB_RUN/hubble.json" ] && pb_kv client_out.hubble.lost_event_lines "$(grep -c '"lost_events"' "$PB_RUN/hubble.json")"
[ -f "$PB_RUN/hubble.err" ] && pb_kv client_out.hubble.restarts "$(grep -c 'hubble observe exited' "$PB_RUN/hubble.err")"
[ -f "$PB_RUN/hubble-pf.err" ] && pb_kv client_out.hubble.portforward_restarts "$(grep -c 'port-forward exited' "$PB_RUN/hubble-pf.err")"
for f in ig_tcp.err ig_snap.err; do   # the gadget pods report the image they ran (and version warnings)
  [ -f "$PB_RUN/$f" ] && pb_kv "client_err.$f.version_warning" "$(grep -m1 -oE 'built with ig v[0-9.]+ and it.s being run with v[0-9.]+' "$PB_RUN/$f")"
done
# event counts per 5-s bin of event time, so the analysis can use the same window for every tool
python3 "$PB_BIN/client_bins.py" "$PB_RUN" 2>> "$PB_RUN/run.log" || pb_warn "client_bins.py failed"
gzip -f "$PB_RUN"/samples-*.csv "$PB_RUN"/canary-*.csv "$PB_RUN"/hubble.json "$PB_RUN"/ig_tcp.json 2>/dev/null
STATUS=DONE
exit 0
