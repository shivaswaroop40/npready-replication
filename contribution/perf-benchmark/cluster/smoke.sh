#!/usr/bin/env bash
# Smoke-test every observer once against a tiny test namespace (pb-smoke: busybox httpd
# server + a wget loop client on the other worker). Uses bin/cond.sh to switch conditions,
# so it also exercises cond.sh. Ends in baseline and deletes pb-smoke.
#   bash smoke.sh [outdir]      (default /opt/perfbench/results/_infra-smoke)
# Prints one JSON summary line; exit 1 if any observer returned nothing.
set -euo pipefail
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
export PATH=/usr/local/bin:$PATH
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
COND="$(dirname "$HERE")/bin/cond.sh"
OUT=${1:-/opt/perfbench/results/_infra-smoke}
IG_TAG=v0.54.1
NS=pb-smoke
mkdir -p "$OUT"; cd "$OUT"
log() { printf '[smoke %s] %s\n' "$(date -u +%H:%M:%SZ)" "$*" >&2; }

kubectl create ns $NS --dry-run=client -o yaml | kubectl apply -f - >/dev/null
kubectl apply -f - >/dev/null <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata: {name: srv, namespace: pb-smoke}
spec:
  replicas: 1
  selector: {matchLabels: {app: srv}}
  template:
    metadata: {labels: {app: srv}}
    spec:
      containers:
      - name: srv
        image: busybox:1.36
        command: ["sh","-c","mkdir -p /w && echo ok > /w/index.html && httpd -f -p 8080 -h /w"]
---
apiVersion: v1
kind: Service
metadata: {name: srv, namespace: pb-smoke}
spec:
  selector: {app: srv}
  ports: [{port: 80, targetPort: 8080}]
---
apiVersion: apps/v1
kind: Deployment
metadata: {name: cli, namespace: pb-smoke}
spec:
  replicas: 1
  selector: {matchLabels: {app: cli}}
  template:
    metadata: {labels: {app: cli}}
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector: {matchLabels: {app: srv}}
            topologyKey: kubernetes.io/hostname
      containers:
      - name: cli
        image: busybox:1.36
        command: ["sh","-c","while true; do wget -q -O- http://srv.pb-smoke.svc.cluster.local/ >/dev/null; sleep 1; done"]
EOF
kubectl -n $NS rollout status deploy/srv --timeout=180s >/dev/null
kubectl -n $NS rollout status deploy/cli --timeout=180s >/dev/null

log "hubble"; bash "$COND" hubble > cond_hubble.json
# the hubble condition is the state test-cluster ran in: diff its ConfigMap against the dump
[ -f "$HERE/cilium-config-20260910.json" ] && \
  python3 "$HERE/diff_cilium_config.py" "$HERE/cilium-config-20260910.json" > cilium_config_diff_hubble.txt
RIP=$(kubectl -n kube-system get svc hubble-relay -o jsonpath='{.spec.clusterIP}')
sleep 10
hubble observe --server "$RIP:80" --namespace $NS --last 50 -o json > hubble_observe.json || true
HUB=$(wc -l < hubble_observe.json)

log "otterize"; bash "$COND" otterize > cond_otterize.json
MIP=$(kubectl -n otterize-system get svc otterize-network-mapper -o jsonpath='{.spec.clusterIP}')
OTT=0
for _ in $(seq 30); do
  curl -sS -m 20 -X POST "http://$MIP:9090/query" -H 'Content-Type: application/json' \
    -d '{"query":"{ serviceIntents { client { name namespace } intents { name namespace } } }"}' > otterize_query.json || true
  OTT=$(jq '[.data.serviceIntents[]? | select(.client.namespace=="pb-smoke" and .client.name=="cli") | .intents[] | select(.name=="srv")] | length' otterize_query.json 2>/dev/null || echo 0)
  [ "$OTT" -gt 0 ] && break
  sleep 5
done

log "ig_tcp"; bash "$COND" ig_tcp > cond_ig_tcp.json
timeout 25 kubectl gadget run "trace_tcp:$IG_TAG" -n $NS -o json > ig_tcp.json 2> ig_tcp.err || true
TCP=$(wc -l < ig_tcp.json)
SNAP=0
for t in 1 2 3; do  # exactly the thesis loop: background run, kill after 12 s
  kubectl gadget run "snapshot_socket:$IG_TAG" -n $NS -o json > ig_snap.json 2> ig_snap.err & SP=$!
  sleep 12; kill $SP 2>/dev/null || true; sleep 1
  SNAP=$(python3 -c "import json;print(len(json.load(open('ig_snap.json'))))" 2>/dev/null || echo 0)
  [ "$SNAP" -gt 0 ] && { log "snapshot_socket ok on try $t"; break; }
done

log "baseline"; bash "$COND" baseline > cond_baseline.json
[ -f "$HERE/cilium-config-20260910.json" ] && \
  python3 "$HERE/diff_cilium_config.py" "$HERE/cilium-config-20260910.json" > cilium_config_diff_baseline.txt
kubectl delete ns $NS --wait=true >/dev/null

OK=$([ "$HUB" -gt 0 ] && [ "$OTT" -gt 0 ] && [ "$TCP" -gt 0 ] && [ "$SNAP" -gt 0 ] && echo true || echo false)
jq -cn --argjson ok "$OK" --argjson hubble_flows "$HUB" --argjson otterize_cli_to_srv "$OTT" \
  --argjson ig_trace_tcp_events "$TCP" --argjson ig_snapshot_entries "$SNAP" \
  '{smoke_ok:$ok, hubble_flows:$hubble_flows, otterize_cli_to_srv:$otterize_cli_to_srv,
    ig_trace_tcp_events_25s:$ig_trace_tcp_events, ig_snapshot_socket_entries:$ig_snapshot_entries}' | tee smoke.json
[ "$OK" = true ]
