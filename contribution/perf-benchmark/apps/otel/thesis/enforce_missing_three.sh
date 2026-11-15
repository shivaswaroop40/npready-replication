#!/usr/bin/env bash
# Close the three n/r cells on the OpenTelemetry row: live-enforce the Otterize,
# IG snapshot_socket and IG trace_tcp policies that the 6 Sept run scored only on paper.
#
# The otel namespace was torn down after that run, so this redeploys the demo from the
# pinned manifest first. Policies are the ones generated on 6 Sept from journey A; they
# are keyed on labels, so they apply unchanged to the fresh pods.
set -uo pipefail
export KUBECONFIG=/tmp/thesis_direct.kubeconfig
export PATH="/opt/homebrew/bin:$PATH"

W=/Users/shiv/Desktop/code/MasterThesis/contribution/results/OTEL-20260906
NS=otel
OUTROOT="$W/enforce"
LOG="$OUTROOT/LOG-missing-three.txt"
mkdir -p "$OUTROOT"

k() { kubectl --insecure-skip-tls-verify --request-timeout=90s "$@"; }
say() { printf '[otel3 %s] %s\n' "$(date -u +%H:%M:%SZ)" "$*" | tee -a "$LOG"; }

say "=== preflight ==="
k get --raw /readyz >/dev/null 2>&1 || { say "FATAL: apiserver not ready"; exit 1; }
say "apiserver ok"

# ---------------------------------------------------------------- redeploy
if ! k get ns "$NS" >/dev/null 2>&1; then
  say "namespace $NS absent, redeploying the demo"
  k create ns "$NS" >/dev/null 2>&1
  k -n "$NS" apply -f "$W/manifests/otel-demo-1.12.0.yaml" >>"$LOG" 2>&1
  say "manifest applied"
  # the original run scaled the observability stack to zero so the app fits the cluster
  for d in grafana jaeger prometheus-server frontendproxy; do
    k -n "$NS" scale deploy "opentelemetry-demo-$d" --replicas=0 >/dev/null 2>&1
  done
  k -n "$NS" scale sts otel-demo-opensearch --replicas=0 >/dev/null 2>&1
  say "observability stack scaled to zero"
else
  say "namespace $NS already present, reusing it"
fi

k -n "$NS" scale deploy opentelemetry-demo-loadgenerator --replicas=0 >/dev/null 2>&1
k -n "$NS" scale deploy opentelemetry-demo-frontendproxy --replicas=0 >/dev/null 2>&1
say "shipped loadgenerator and frontendproxy scaled to zero"
for i in 1 2 3 4 5 6 7 8 9 10; do
  N=$(k -n "$NS" get pods -l app.kubernetes.io/component=loadgenerator --no-headers 2>/dev/null | wc -l | tr -d ' ')
  [ "$N" = "0" ] && break
  sleep 6
done
say "shipped loadgenerator pods remaining: ${N:-?}"

say "waiting for the application to stabilise"
for i in $(seq 1 60); do
  TOT=$(k -n "$NS" get deploy --no-headers 2>/dev/null | wc -l | tr -d ' ')
  RDY=$(k -n "$NS" get deploy --no-headers 2>/dev/null | awk -F'[ /]+' '$2>0 && $2==$3' | wc -l | tr -d ' ')
  ZERO=$(k -n "$NS" get deploy --no-headers 2>/dev/null | awk '$2 == "0/0"' | wc -l | tr -d ' ')
  say "  ready $RDY, scaled-to-zero $ZERO, of $TOT"
  [ "$((RDY + ZERO))" -ge "$TOT" ] && [ "$TOT" -gt 10 ] && break
  sleep 20
done
k -n "$NS" get deploy --no-headers > "$OUTROOT/deploy_state_before.txt" 2>&1
say "application state written"

# ---------------------------------------------------------------- the three tools
for TOOL in otterize ig_snapshot_socket ig_trace_tcp; do
  OUT="$OUTROOT/$TOOL"; mkdir -p "$OUT"
  POL="$W/policies/netpol_$TOOL.yaml"
  EXP=$(grep -c 'kind: NetworkPolicy' "$POL")

  say "=== $TOOL ==="
  for t in 1 2 3 4 5; do
    k -n "$NS" apply -f "$POL" >/dev/null 2>&1
    sleep 4
    HAVE=$(k -n "$NS" get netpol --no-headers 2>/dev/null | wc -l | tr -d ' ')
    [ "$HAVE" = "$EXP" ] && break
  done
  say "$TOOL: policies applied $HAVE/$EXP"
  [ "$HAVE" != "$EXP" ] && say "WARNING: partial apply, results for $TOOL are suspect"

  # restart the checkout path so its pooled connections re-establish under the policy,
  # exactly as the 6 Sept targeted run did for synth and synth+config
  for d in checkoutservice frontend; do
    k -n "$NS" rollout restart "deploy/opentelemetry-demo-$d" >/dev/null 2>&1
  done
  k -n "$NS" rollout status deploy/opentelemetry-demo-checkoutservice --timeout=180s >/dev/null 2>&1
  k -n "$NS" rollout status deploy/opentelemetry-demo-frontend --timeout=180s >/dev/null 2>&1
  say "$TOOL: checkout path restarted"

  k -n kube-system port-forward svc/hubble-relay 4250:80 >/tmp/hre_otel3.log 2>&1 &
  HPF=$!
  sleep 6
  ( hubble observe --server localhost:4250 --namespace "$NS" --verdict DROPPED -o json --follow \
      > "$OUT/hubble_drops.json" 2>/dev/null ) &
  HO=$!

  k -n "$NS" apply -f "$W/workloads/loadgen-b.yaml" >/dev/null 2>&1
  i=0
  until [ "$(k -n "$NS" get pods -l journey=B --no-headers 2>/dev/null | awk '{print $3}')" = "Running" ] || [ $i -ge 24 ]; do
    sleep 5; i=$((i+1))
  done
  say "$TOOL: journey B running for 180s"
  sleep 180

  k -n "$NS" logs -l journey=B --tail=40 > "$OUT/locust_B.txt" 2>/dev/null
  kill $HO $HPF 2>/dev/null; sleep 2
  k -n "$NS" delete deploy loadgen-b --ignore-not-found --wait=false >/dev/null 2>&1
  k -n "$NS" get pods --no-headers > "$OUT/pods_after.txt" 2>&1

  python3 - "$OUT" <<'PY'
import json, sys, os, collections
out = sys.argv[1]
edges = collections.Counter()
path = os.path.join(out, "hubble_drops.json")
for line in open(path, errors="ignore") if os.path.exists(path) else []:
    line = line.strip()
    if not line:
        continue
    try:
        o = json.loads(line)
    except Exception:
        continue
    f = o.get("flow", o)
    s = (f.get("source") or {}); d = (f.get("destination") or {})
    def role(x):
        import re
        ns, pod = x.get("namespace"), x.get("pod_name") or ""
        if not ns or not pod:
            return "?"
        if ns == "kube-system":
            return "kube-dns"
        pod = pod.replace("opentelemetry-demo-", "")
        return re.sub(r"-[a-z0-9]{6,10}(-[a-z0-9]{4,5})?$", "", pod)
    l4 = f.get("l4") or {}
    dp = ((l4.get("TCP") or {}).get("destination_port")) or ((l4.get("UDP") or {}).get("destination_port"))
    edges[f"{role(s)}->{role(d)}:{dp}"] += 1
app = {e: v for e, v in edges.items() if not e.startswith("?->") and "->?" not in e}
res = {"drops_by_edge": dict(edges),
       "app_edge_drops": sum(app.values()),
       "total_drops": sum(edges.values()),
       "top": sorted(app.items(), key=lambda x: -x[1])[:8]}
json.dump(res, open(os.path.join(out, "result.json"), "w"), indent=2)
print(f"    app-edge drops = {res['app_edge_drops']}  (total {res['total_drops']})")
print(f"    top: {res['top'][:3]}")
PY

  k -n "$NS" delete netpol --all --wait=false >/dev/null 2>&1
  sleep 8
  say "$TOOL: done, policies removed"
done

say "=== all three complete ==="
for TOOL in otterize ig_snapshot_socket ig_trace_tcp; do
  if [ -f "$OUTROOT/$TOOL/result.json" ]; then
    D=$(python3 -c "import json;print(json.load(open('$OUTROOT/$TOOL/result.json'))['app_edge_drops'])")
    say "  $TOOL: $D app-edge drops"
  fi
done
k get --raw /readyz >/dev/null 2>&1 && say "post-run apiserver health: ok" || say "post-run health: FAILED"
say "namespace $NS left deployed with no policies"
