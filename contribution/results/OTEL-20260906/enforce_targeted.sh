#!/usr/bin/env bash
# Targeted live check of the checkout fan-out for OTel: apply policy, restart the checkout path so it
# reconnects under the policy, run journey B, count drops on application edges. Lighter than the full
# 17-service restart (OTel's dependency chains make that impractical); tests the one edge that matters.
set -uo pipefail
export KUBECONFIG=/tmp/thesis_direct.kubeconfig PATH="/opt/homebrew/bin:$PATH"
W=/Users/shiv/Desktop/code/MasterThesis/contribution/results/OTEL-20260906; NS=otel; K="kubectl --insecure-skip-tls-verify --request-timeout=60s"
say(){ printf '[otel-enf %s] %s\n' "$(date -u +%H:%M:%SZ)" "$*" | tee -a "$W/enforce/LOG.txt"; }
for TOOL in synth synth_plus_config; do
  OUT="$W/enforce/$TOOL"; mkdir -p "$OUT"
  EXP=$(grep -c 'kind: NetworkPolicy' "$W/policies/netpol_$TOOL.yaml")
  for t in 1 2 3 4 5; do $K -n $NS apply -f "$W/policies/netpol_$TOOL.yaml" >/dev/null 2>&1; sleep 3; H=$($K -n $NS get netpol --no-headers 2>/dev/null | wc -l | tr -d ' '); [ "$H" = "$EXP" ] && break; done
  say "=== $TOOL: policies $H/$EXP ==="
  # restart the checkout path so its pooled connections to payment/shipping/email/currency re-establish under the policy
  for d in checkoutservice frontend; do $K -n $NS rollout restart deploy/opentelemetry-demo-$d >/dev/null 2>&1; done
  $K -n $NS rollout status deploy/opentelemetry-demo-checkoutservice --timeout=120s >/dev/null 2>&1 || true
  $K -n $NS rollout status deploy/opentelemetry-demo-frontend --timeout=120s >/dev/null 2>&1 || true
  say "checkout+frontend restarted"
  $K -n kube-system port-forward svc/hubble-relay 4250:80 >/tmp/hre_otel.log 2>&1 & HPF=$!; sleep 6
  ( hubble observe --server localhost:4250 --namespace $NS --verdict DROPPED -o json --follow > "$OUT/hubble_drops.json" 2>/dev/null ) & HO=$!
  $K -n $NS apply -f "$W/workloads/loadgen-b.yaml" >/dev/null 2>&1
  i=0; until [ "$($K -n $NS get pods -l journey=B --no-headers 2>/dev/null | awk '{print $3}')" = "Running" ] || [ $i -ge 24 ]; do sleep 5; i=$((i+1)); done
  say "journey B under $TOOL for 180s"; sleep 180
  $K -n $NS logs -l journey=B --tail=40 > "$OUT/locust_B.txt" 2>/dev/null
  kill $HO $HPF 2>/dev/null; sleep 1; $K -n $NS delete deploy loadgen-b --ignore-not-found --wait=false >/dev/null 2>&1
  python3 - "$OUT" <<'PY' | tee -a "$W/enforce/LOG.txt"
import json,sys,re,os
out=sys.argv[1]; drops={}; n=0
for line in open(os.path.join(out,"hubble_drops.json")):
    try: f=json.loads(line)["flow"]
    except: continue
    s=(f.get("source") or {}).get("pod_name","?"); d=(f.get("destination") or {}).get("pod_name","?")
    p=((f.get("l4") or {}).get("TCP") or {}).get("destination_port")
    s=re.sub(r'^opentelemetry-demo-','',re.sub(r'-[a-z0-9]+-[a-z0-9]+$','',s)); d=re.sub(r'^opentelemetry-demo-','',re.sub(r'-[a-z0-9]+-[a-z0-9]+$','',d))
    if 'reserved:' in str((f.get('source') or {}).get('labels')): continue
    drops[f"{s}->{d}:{p}"]=drops.get(f"{s}->{d}:{p}",0)+1; n+=1
json.dump({"drops_total":n,"drops_by_edge":dict(sorted(drops.items(),key=lambda kv:-kv[1]))},open(os.path.join(out,"result.json"),"w"),indent=1)
print(f"   drops={n} edges={len(drops)}")
for k,v in list(dict(sorted(drops.items(),key=lambda kv:-kv[1])).items())[:6]: print(f"     {v:5} {k}")
PY
  say "remove $TOOL policy"; $K -n $NS delete -f "$W/policies/netpol_$TOOL.yaml" --wait=false >/dev/null 2>&1
  i=0; until [ "$($K -n $NS get netpol --no-headers 2>/dev/null | wc -l | tr -d ' ')" = "0" ] || [ $i -ge 20 ]; do sleep 5; i=$((i+1)); done; sleep 5
done
say "TARGETED ENFORCEMENT DONE"
