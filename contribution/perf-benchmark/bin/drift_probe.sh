#!/usr/bin/env bash
# shellcheck disable=SC2329  # finish runs from the EXIT trap
# drift_probe.sh <app> <minutes> <interval_s> [--cond <cond>] [--tp-n N] [--out DIR]
#
# Host-drift probe, on cp-01 as root. With the cluster in one fixed condition and the app
# deployed, it runs the host-speed canary (bin/canary.py, scope pb-canary) on every node and
# repeats one fixed-count test every <interval_s> seconds (start to start) for <minutes> minutes:
# the app's throughput.yaml with TP_N=2000 requests (--tp-n, or PB_TP_N), keep-alive flags
# (TP_FLAGS_KEEPALIVE), TP_C from app.env (PB_TP_C wins; default 16), the app's TP_PRE_HOOK
# before each test. Nothing in the cluster changes between tests, so a change in test time is the
# host. Output in results/_drift/<app>-<UTC time>/ (or --out):
#   timeline.csv   one row per test: start, test time, req/s, canary speed per node during the
#                  test, the workers' speed in the pause before it, their ratio to the probe's
#                  median and the test time normalised by it (bin/drift_join.py)
#   summary.json   CV of the test time raw and normalised, correlation with 1/speed, canary speed
#                  under load vs in the pauses
#   tests.jsonl, tp/<i>.log, canary-<node>.csv (+ .info.json), probe.json, hostinfo.json, run.log,
#   cond_state.json (--cond) or cond_found.txt (the state as found)
# --cond runs cond.sh <cond> first. timeline.csv is rewritten after every test from live copies
# of the canary files, so an interrupted probe keeps its timeline. Takes the benchmark lock.
# Start it detached, e.g.:
#   ( setsid nohup /opt/perfbench/bin/drift_probe.sh boutique 360 120 --cond baseline > /opt/perfbench/results/drift.out 2>&1 < /dev/null & )
# Env: PB_TP_N PB_TP_C PB_TP_TIMEOUT_S PB_CANARY_S PB_CANARY_ITERS PB_PLAY_ID
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PB_ROOT=${PB_ROOT:-$(dirname "$HERE")}
# shellcheck source=lib.sh source-path=SCRIPTDIR
. "$HERE/lib.sh"

usage() { sed -n '3,3p' "$0" | sed 's/^# //' >&2; exit 2; }
[ $# -ge 3 ] || usage
APP=$1 MINUTES=$2 INTERVAL=$3; shift 3
COND="" PROBE_N=${PB_TP_N:-2000} OUT=""
while [ $# -gt 0 ]; do
  case $1 in
    --cond) [ $# -ge 2 ] || usage; COND=$2; shift ;;
    --tp-n) [ $# -ge 2 ] || usage; PROBE_N=$2; shift ;;
    --out) [ $# -ge 2 ] || usage; OUT=$2; shift ;;
    *) usage ;;
  esac
  shift
done
[[ $MINUTES =~ ^[1-9][0-9]*$ ]] && [[ $INTERVAL =~ ^[1-9][0-9]*$ ]] && [[ $PROBE_N =~ ^[1-9][0-9]*$ ]] || usage
if [ -n "$COND" ]; then case " $PB_CONDS_ALL " in *" $COND "*) ;; *) usage ;; esac; fi

exec 8>"$PB_LOCK"
flock -n 8 || { echo "drift_probe: another perfbench run holds $PB_LOCK" >&2; exit 1; }

TS=$(date -u +%Y%m%dT%H%M%SZ)
PB_RUN=${OUT:-$PB_RESULTS/_drift/$APP-$TS}
PB_RUN_ID="drift-$APP-$TS"
[ ! -e "$PB_RUN/tests.jsonl" ] || { echo "drift_probe: $PB_RUN already holds a probe" >&2; exit 1; }
mkdir -p "$PB_RUN"/{jobs,tp,.live} || exit 1
: > "$PB_RUN/phases.tsv"; : > "$PB_RUN/kv.tsv"; : > "$PB_RUN/tests.jsonl"
JOB=pb-drift-tp NTEST=0 CANARY_STARTED=0

pb_load_app "$APP" || { pb_log "cannot load apps/$APP"; exit 1; }
TP_N=$PROBE_N
TP_C=${PB_TP_C:-${TP_C:-16}}
TP_FLAGS=${TP_FLAGS_KEEPALIVE-}
export TP_N TP_C TP_FLAGS
if [[ $TP_C =~ ^[1-9][0-9]*$ ]] && [ $((TP_N % TP_C)) -ne 0 ]; then   # hey sends N/C requests per worker
  pb_warn "--tp-n $TP_N is not a multiple of TP_C=$TP_C: hey sends $((TP_N / TP_C * TP_C)) requests and every test counts as failed"
fi
TP_TIMEOUT_S=${PB_TP_TIMEOUT_S:-${TP_TIMEOUT_S:-900}}
PB_PLAY_ID=${PB_PLAY_ID:-$(cat "$PB_ROOT/PLAY_ID" 2>/dev/null || true)}
export PB_PLAY_ID
K get ns "$APP_NS" >/dev/null 2>&1 || { pb_log "namespace $APP_NS missing (deploy the app first)"; exit 1; }
pb_resolve_nodes

live_join() { # copy the canary files as they are now and rewrite timeline.csv
  local n
  for n in $PB_NODES; do
    if pb_is_local "$n"; then cp -f "$(pb_canary_path "$n")" "$PB_RUN/.live/canary-$n.csv" 2>/dev/null
    else pb_get "$n" "$(pb_canary_path "$n")" "$PB_RUN/.live/canary-$n.csv" 2>/dev/null; fi
  done
  python3 "$PB_BIN/drift_join.py" "$PB_RUN" --canary-dir "$PB_RUN/.live" >/dev/null 2>>"$PB_RUN/run.log"
}
finish() {
  local rc=$? n
  trap - EXIT INT TERM
  K -n "$APP_NS" delete job "$JOB" --ignore-not-found --wait=false >/dev/null 2>&1
  if [ "$CANARY_STARTED" = 1 ]; then
    for n in $PB_NODES; do pb_canary_stop_fetch "$n" || true; done
    pb_mark canary_stopped
  fi
  if [ -s "$PB_RUN/probe.json" ]; then
    if python3 "$PB_BIN/drift_join.py" "$PB_RUN" > "$PB_RUN/summary.line" 2>>"$PB_RUN/run.log"; then
      rm -rf "$PB_RUN/.live"
    else
      pb_warn "drift_join.py failed; live copies kept in .live/"
    fi
  fi
  pb_mark probe_end
  pb_log "drift probe end (rc=$rc): $NTEST tests -> $PB_RUN/timeline.csv $(cat "$PB_RUN/summary.line" 2>/dev/null)"
  exit "$rc"
}
trap finish EXIT
trap 'exit 1' INT TERM

pb_mark probe_start
pb_log "drift probe $APP: ${MINUTES} min, a test every ${INTERVAL}s, ${TP_N} requests c${TP_C} keep-alive, cond=${COND:-as found}"
if [ -n "$COND" ]; then
  bash "$PB_BIN/cond.sh" "$COND" > "$PB_RUN/cond.out" 2> "$PB_RUN/cond.err"; rc=$?
  grep -E '^\{' "$PB_RUN/cond.out" | tail -1 > "$PB_RUN/cond_state.json"
  [ "$rc" = 0 ] || { pb_log "cond.sh $COND exit $rc: $(tail -n 3 "$PB_RUN/cond.err" | tr '\n' ' ')"; exit 1; }
else
  {
    echo "enable-hubble=$(K -n kube-system get cm cilium-config -o jsonpath='{.data.enable-hubble}' 2>/dev/null)"
    echo "hubble_relay_pods=$(K -n kube-system get pods -l k8s-app=hubble-relay --no-headers 2>/dev/null | wc -l)"
    echo "otterize_pods=$(K -n otterize-system get pods --no-headers 2>/dev/null | wc -l)"
    echo "gadget_pods=$(K -n gadget get pods --no-headers 2>/dev/null | wc -l)"
  } > "$PB_RUN/cond_found.txt"
fi
pb_clock_offsets
pb_hostinfo "$PB_RUN/hostinfo.json" || pb_warn "host info not recorded"
jq -n --arg app "$APP" --arg ns "$APP_NS" --arg nodes "$PB_NODES" --arg cp "$PB_CP_NODE" --arg cond "$COND" \
  --argjson minutes "$MINUTES" --argjson interval "$INTERVAL" --argjson n "$TP_N" --argjson c "$TP_C" \
  --arg flags "$TP_FLAGS" --arg url "$TP_URL" --arg expect "${TP_EXPECT_STATUS:-200}" --arg play "${PB_PLAY_ID:-}" \
  --arg canary_s "$PB_CANARY_S" --arg iters "$PB_CANARY_ITERS" --arg t0 "$(pb_now)" \
  '{app:$app, app_ns:$ns, nodes:($nodes|split(" ")|map(select(length>0))), cp:$cp,
    cond:(if $cond=="" then null else $cond end), minutes:$minutes, interval_s:$interval, tp_n:$n, tp_c:$c,
    tp_flags:$flags, tp_url:$url, tp_expect_status:($expect|tonumber), play_id:(if $play=="" then null else $play end),
    canary_s:($canary_s|tonumber), canary_iters:(if $iters=="" then null else ($iters|tonumber) end),
    started:($t0|tonumber)}' > "$PB_RUN/probe.json"

CANARY_STARTED=1
for n in $PB_NODES; do pb_canary_start "$n" || { pb_log "canary did not start on $n"; exit 1; }; done
sleep 3
for n in $PB_NODES; do pb_canary_ok "$n" || { pb_log "canary on $n is not writing"; exit 1; }; done
sleep "$PB_CANARY_S"; sleep "$PB_CANARY_S"   # a few canary samples before the first test

T_END=$((EPOCHSECONDS + MINUTES * 60))
while [ "$EPOCHSECONDS" -lt "$T_END" ]; do
  NTEST=$((NTEST + 1)); next=$((EPOCHSECONDS + INTERVAL))
  if [ -n "${TP_PRE_HOOK:-}" ]; then   # e.g. bank: refresh the session cookie
    { echo "# $(pb_iso) before test $NTEST"; (cd "$PB_APP_DIR" && bash "./$TP_PRE_HOOK"); } \
      >> "$PB_RUN/tp_pre_hook.log" 2>&1 || pb_warn "TP_PRE_HOOK $TP_PRE_HOOK failed before test $NTEST"
  fi
  t_created=$(pb_now) t_start="" t_end="" ok=true err=""
  # shellcheck disable=SC2086
  if ! pb_job_create "$APP_NS" "$JOB" "$PB_APP_DIR/throughput.yaml" $PB_APP_VARS TP_N TP_C TP_FLAGS TP_URL TP_HEADERS APP_NS; then
    ok=false err="create failed"
  elif ! pb_job_wait_started "$APP_NS" "$JOB" 300; then
    ok=false err="pod did not start"
  else
    t_start=$(pb_now)
    pb_job_wait_finished "$APP_NS" "$JOB" "$TP_TIMEOUT_S" 2 || { ok=false; err="timeout ${TP_TIMEOUT_S}s"; }
    t_end=$(pb_now)
  fi
  pb_job_logs "$APP_NS" "$JOB" "$PB_RUN/tp/$NTEST.log"
  read -r pod phase exitc _ <<<"$(pb_job_state "$APP_NS" "$JOB")"
  [ "$phase" = Succeeded ] || { ok=false; err="${err:+$err; }pod phase $phase exit $exitc"; }
  jq -cn --argjson i "$NTEST" --arg pod "$pod" --arg phase "$phase" --arg created "$t_created" \
    --arg start "$t_start" --arg end "$t_end" --argjson ok "$ok" --arg err "$err" --argjson n "$TP_N" \
    --argjson c "$TP_C" --arg log "tp/$NTEST.log" \
    '{i:$i, pod:$pod, phase:$phase, created:($created|tonumber),
      start:(if $start=="" then null else ($start|tonumber) end),
      end:(if $end=="" then null else ($end|tonumber) end), ok:$ok, error:$err, n:$n, c:$c, log:$log}' \
    >> "$PB_RUN/tests.jsonl"
  K -n "$APP_NS" delete job "$JOB" --wait=false >/dev/null 2>&1
  pb_log "test $NTEST ok=$ok $(grep -m1 -E 'Total:' "$PB_RUN/tp/$NTEST.log" | tr -s ' \t' ' ')"
  [ "$ok" = true ] || pb_warn "test $NTEST: $err"
  live_join
  while [ "$EPOCHSECONDS" -lt "$next" ] && [ "$EPOCHSECONDS" -lt "$T_END" ]; do sleep 1; done
done
exit 0
