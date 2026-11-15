#!/usr/bin/env bash
# For each tool: enforce its journey-A policy, restart the app so every connection reconnects under it,
# run journey B, measure drops + Locust failures + readiness. Evaluation is journey B only.
set -uo pipefail
export KUBECONFIG=/tmp/thesis_direct.kubeconfig PATH="/opt/homebrew/bin:$PATH"
ART=/Users/shiv/Desktop/code/MasterThesis/contribution/results/OTEL-20260906
NS=otel; WINDOW="${1:-180}"; K="kubectl --insecure-skip-tls-verify --request-timeout=60s"
say(){ printf '[enforce %s] %s\n' "$(date -u +%H:%M:%SZ)" "$*" | tee -a "$ART/enforce/LOG.txt"; }
mkdir -p "$ART/enforce"
DEPLOYS="adservice cartservice checkoutservice currencyservice emailservice flagd frauddetectionservice frontend imageprovider kafka paymentservice productcatalogservice quoteservice recommendationservice shippingservice valkey accountingservice"
for TOOL in synth synth_plus_config ig_snapshot_socket otterize ig_trace_tcp; do
  OUT="$ART/enforce/$TOOL"; mkdir -p "$OUT"
  say "=== $TOOL: apply policy ==="
  EXPECT=$(grep -c 'kind: NetworkPolicy' "$ART/policies/netpol_$TOOL.yaml")
  for try in 1 2 3 4 5 6; do
    $K -n $NS apply -f "$ART/policies/netpol_$TOOL.yaml" >/dev/null 2>&1; sleep 4
    HAVE=$($K -n $NS get netpol --no-headers 2>/dev/null | wc -l | tr -d ' ')
    [ "$HAVE" = "$EXPECT" ] && break; say "apply incomplete ($HAVE/$EXPECT), retry $try"; sleep 5
  done
  say "policies active: $HAVE / expected $EXPECT"
  [ "$HAVE" = "$EXPECT" ] || { say "!! could not apply full policy for $TOOL, skipping"; continue; }
  say "restart every deployment one at a time (scale 0->1) so connections re-establish under the policy"
  for d in $DEPLOYS; do
    $K -n $NS scale deploy/$d --replicas=0 >/dev/null 2>&1; sleep 3; $K -n $NS scale deploy/$d --replicas=1 >/dev/null 2>&1
    i=0; until [ "$($K -n $NS get pods -l app=$d --no-headers 2>/dev/null | awk '{print $2}' | grep -c '^1/1$')" = "1" ] || [ $i -ge 24 ]; do sleep 5; i=$((i+1)); done
    printf '   %s ready=%s after ~%ss\n' "$d" "$([ $i -lt 24 ] && echo yes || echo NO)" "$((i*5))" | tee -a "$ART/enforce/LOG.txt"
  done
  $K -n $NS get pods --no-headers 2>/dev/null | grep -v 'loadgenerator' > "$OUT/pods_after_restart.txt"
  NOTREADY=$(awk '{split($2,a,"/"); if(a[1]!=a[2]) c++} END{print c+0}' "$OUT/pods_after_restart.txt"); say "pods not ready after restart: $NOTREADY"
  # hubble drops during journey B
  $K -n kube-system port-forward svc/hubble-relay 4248:80 >/tmp/hre.log 2>&1 & HPF=$!; sleep 6
  ( hubble observe --server localhost:4248 --namespace $NS --verdict DROPPED -o json --follow > "$OUT/hubble_drops.json" 2>/dev/null ) & HO=$!
  $K -n $NS apply -f "$ART/workloads/loadgenerator-b.yaml" >/dev/null 2>&1
  i=0; until [ "$($K -n $NS get pods -l journey=B --no-headers 2>/dev/null | awk '{print $3}')" = "Running" ] || [ $i -ge 24 ]; do sleep 5; i=$((i+1)); done
  say "loadgenerator-b: $($K -n $NS get pods -l journey=B --no-headers 2>/dev/null | awk '{print $3}')"
  say "journey B running ${WINDOW}s under $TOOL policy"; sleep "$WINDOW"
  $K -n $NS logs -l journey=B --tail=60 > "$OUT/locust_B.txt" 2>/dev/null
  kill $HO $HPF 2>/dev/null; sleep 1
  $K -n $NS delete deploy loadgenerator-b --ignore-not-found >/dev/null 2>&1
  python3 - "$OUT" <<'PY' | tee -a "$ART/enforce/LOG.txt"
import json,sys,re,os
out=sys.argv[1]; drops={}; n=0
for line in open(os.path.join(out,"hubble_drops.json")):
    try: f=json.loads(line).get("flow",{})
    except: continue
    n+=1; s=(f.get("source") or {}).get("pod_name","?"); d=(f.get("destination") or {}).get("pod_name","?")
    p=((f.get("l4") or {}).get("TCP") or {}).get("destination_port")
    s=re.sub(r'-[a-z0-9]+-[a-z0-9]+$','',s); d=re.sub(r'-[a-z0-9]+-[a-z0-9]+$','',d)
    drops[f"{s}->{d}:{p}"]=drops.get(f"{s}->{d}:{p}",0)+1
loc=open(os.path.join(out,"locust_B.txt")).read() if os.path.exists(os.path.join(out,"locust_B.txt")) else ""
agg=[l for l in loc.splitlines() if 'Aggregated' in l]
fails=agg[-1].split()[2] if agg else "n/a"
res={"drops_total":n,"drops_by_edge":dict(sorted(drops.items(),key=lambda kv:-kv[1])),"locust_aggregated_last":agg[-1].strip() if agg else None,"locust_fails":fails}
json.dump(res,open(os.path.join(out,"result.json"),"w"),indent=1)
print(f"   drops={n} distinct_edges={len(drops)} locust_fails={fails}")
for k,v in list(res['drops_by_edge'].items())[:8]: print(f"     {v:6}  {k}")
PY
  say "remove $TOOL policy"; $K -n $NS delete -f "$ART/policies/netpol_$TOOL.yaml" --wait=false >/dev/null 2>&1
  i=0; until [ "$($K -n $NS get netpol --no-headers 2>/dev/null | wc -l | tr -d ' ')" = "0" ] || [ $i -ge 24 ]; do sleep 5; i=$((i+1)); done; say "policies left after removal: $($K -n $NS get netpol --no-headers 2>/dev/null | wc -l | tr -d ' ')"
done
$K -n $NS get netpol --no-headers 2>/dev/null | wc -l | xargs say "policies left:"
say "ENFORCEMENT EVAL DONE"
