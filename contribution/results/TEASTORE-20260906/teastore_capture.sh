#!/usr/bin/env bash
# Online Boutique two-journey capture. Usage: boutique_capture.sh A|B <seconds>
#  A: shipped Locust generator (Google's UserBehavior) drives traffic; all observers on; policies learn from this.
#  B: purchase-path journey (Google's task functions, different weights); evaluation traffic.
set -uo pipefail
export KUBECONFIG=/tmp/thesis_direct.kubeconfig
export PATH="/opt/homebrew/bin:$PATH"
PHASE="${1:?A|B}"; WINDOW="${2:-1200}"; NS=teastore
ART=/Users/shiv/Desktop/code/MasterThesis/contribution/results/TEASTORE-20260906
RUN="$ART/capture$PHASE"; mkdir -p "$RUN"
K="kubectl --insecure-skip-tls-verify"
say(){ printf '[%s %s] %s\n' "$PHASE" "$(date -u +%H:%M:%SZ)" "$*" | tee -a "$RUN/LOG.txt"; }
RUNNING=1; PIDS=()
cleanup(){ RUNNING=0; for p in "${PIDS[@]:-}"; do kill "$p" 2>/dev/null || true; done
  pkill -f "port-forward.*hubble-relay" 2>/dev/null || true; pkill -f "hubble observe" 2>/dev/null || true
  pkill -f "gadget run trace_tcp" 2>/dev/null || true; }
trap cleanup EXIT INT TERM
say "start window=${WINDOW}s"
otter(){ $K -n otterize-system port-forward svc/otterize-network-mapper 9093:9090 >/tmp/ottb.log 2>&1 & P=$!; sleep 7
  curl -sS -m20 -X POST http://localhost:9093/query -H 'Content-Type: application/json' \
   -d '{"query":"{ serviceIntents { client { name namespace } intents { name namespace } } }"}' > "$1" 2>/dev/null; kill $P 2>/dev/null; sleep 1; }
if [ "$PHASE" = A ]; then
  $K -n otterize-system rollout restart deployment/otterize-network-mapper >/dev/null 2>&1
  $K -n otterize-system rollout status deployment/otterize-network-mapper --timeout=120s >/dev/null 2>&1 || true
  say "otterize reset"
fi
otter "$RUN/otterize_t0.json"; say "otterize t0: $(wc -c < "$RUN/otterize_t0.json")b"
# observers
( while [ "$RUNNING" = 1 ]; do
    $K -n kube-system port-forward svc/hubble-relay 4247:80 >/tmp/hrb.log 2>&1 & HPF=$!; sleep 6
    hubble observe --server localhost:4247 --namespace $NS -o json --follow >> "$RUN/hubble_teastore.json" 2>/dev/null
    kill $HPF 2>/dev/null || true; sleep 2; done ) & PIDS+=($!)
( kubectl gadget run trace_tcp:latest -n $NS -o json > "$RUN/ig_tcp.json" 2>"$RUN/ig_tcp.err" ) & PIDS+=($!)
sleep 12; say "observers up (hubble, IG trace_tcp)"
# workload
$K -n $NS delete deploy loadgen-a loadgen-b --ignore-not-found --wait=false >/dev/null 2>&1; sleep 5
$K -n $NS apply -f "$ART/workloads/loadgen-$(echo $PHASE | tr A-Z a-z).yaml" >/dev/null 2>&1
say "workload $PHASE started"
END=$(( $(date +%s) + WINDOW ))
while [ "$(date +%s)" -lt "$END" ]; do sleep 60; rem=$(( END - $(date +%s) )); [ $rem -lt 0 ] && rem=0
  say "  ${rem}s left | hubble=$(wc -l < "$RUN/hubble_teastore.json" 2>/dev/null) igtcp=$(wc -l < "$RUN/ig_tcp.json" 2>/dev/null) loadgen=$($K -n $NS get pods -l run=load-test --no-headers 2>/dev/null | awk '{print $3}' | tr '\n' ',')"; done
# end snapshots
otter "$RUN/otterize_t1.json"; say "otterize t1: $(wc -c < "$RUN/otterize_t1.json")b"
for t in 1 2 3; do kubectl gadget run snapshot_socket:latest -n $NS -o json > "$RUN/ig_snap.json" 2>/dev/null & SP=$!; sleep 12; kill $SP 2>/dev/null; sleep 1
  python3 -c "import json;a=json.load(open('$RUN/ig_snap.json'));exit(0 if a else 1)" 2>/dev/null && { say "snapshot_socket OK ($(wc -c < "$RUN/ig_snap.json")b)"; break; }; say "snapshot retry $t"; done
python3 /Users/shiv/Desktop/code/thesis-harness/runs/build_ipmap.py "$RUN/ipmap.json" 2>/dev/null | tail -1 | tee -a "$RUN/LOG.txt"
$K -n $NS get pods -o wide --no-headers > "$RUN/pods.txt" 2>/dev/null
# stop workload
$K -n $NS logs -l run=load-test --tail=40 > "$RUN/locust_output.txt" 2>/dev/null; $K -n $NS delete deploy loadgen-a loadgen-b --ignore-not-found --wait=false >/dev/null 2>&1
cleanup; trap - EXIT; sleep 2
say "DONE hubble=$(wc -l < "$RUN/hubble_teastore.json") igtcp=$(wc -l < "$RUN/ig_tcp.json")"
