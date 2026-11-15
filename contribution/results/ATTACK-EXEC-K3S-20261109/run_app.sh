#!/usr/bin/env bash
# Deploy one held-out application from its stored manifests, execute its attack edges with
# probe_k3s.py (unprotected, then under each stored generated policy), record the cluster state,
# then delete the application's namespace.  Usage: run_app.sh <app>
set -uo pipefail
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
cd /root/ae
APP=$1
case $APP in
  boutique) DIR=BOUTIQUE-20260903; MAN=manifests/online-boutique-v0.10.6.yaml ;;
  bank)     DIR=BANK-20260904;     MAN=manifests/_all.yaml ;;
  dsb)      DIR=DSB-SOCIAL-20260904; MAN=manifests/dsb-social-rendered.yaml ;;
  otel)     DIR=OTEL-20260906;     MAN=manifests/otel-demo-1.12.0.yaml ;;
  teastore) DIR=TEASTORE-20260906; MAN=manifests/teastore-ribbon.yaml ;;
  *) echo "unknown app"; exit 2 ;;
esac
NS=$APP
OUT=/root/ae/out/$APP; mkdir -p "$OUT"
log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }

if [ "$APP" = bank ]; then
  # the probe reads one manifest; concatenate Bank's per-service files (content unchanged)
  : > "$DIR/$MAN"
  for f in "$DIR"/manifests/[a-z]*.yaml; do cat "$f" >> "$DIR/$MAN"; printf '\n---\n' >> "$DIR/$MAN"; done
fi

log "namespace $NS"
kubectl create namespace "$NS" 2>/dev/null || true
log "apply $DIR/$MAN"
kubectl -n "$NS" apply -f "$DIR/$MAN" > "$OUT/apply.log" 2>&1; echo "apply exit $?" >> "$OUT/apply.log"
if [ "$APP" = bank ]; then
  # same fix as the 2026-10-28 run: the GCP tracing exporter needs credentials outside GCP
  kubectl -n "$NS" set env deployment/userservice ENABLE_TRACING=false >> "$OUT/apply.log" 2>&1
  echo "fix: userservice ENABLE_TRACING=false" >> "$OUT/fixes.txt"
fi
log "waiting for pods"
for i in $(seq 90); do
  notready=$(kubectl -n "$NS" get pods --no-headers 2>/dev/null | awk '$3!="Completed" && $3!="Succeeded" {split($2,a,"/"); if (a[1]!=a[2]) n++} END{print n+0}')
  [ "$notready" = 0 ] && [ "$(kubectl -n "$NS" get pods --no-headers 2>/dev/null | wc -l)" -gt 0 ] && break
  sleep 10
done
log "not ready after wait: $notready"
kubectl -n "$NS" get pods -o wide > "$OUT/pods_before.txt" 2>&1
log "probe"
python3 -I probe_k3s.py "$DIR" "$MAN" "$NS" "$OUT/$APP.json" > "$OUT/probe.log" 2>&1
echo "probe exit $?" >> "$OUT/probe.log"
kubectl -n "$NS" get pods -o wide > "$OUT/pods_after.txt" 2>&1
log "delete namespace"
kubectl delete namespace "$NS" --wait=true --timeout=5m > /dev/null 2>&1
log "DONE $APP"
