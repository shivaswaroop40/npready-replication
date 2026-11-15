#!/usr/bin/env bash
# Two-node k3s + Cilium 1.16.5 cluster for the attack-execution rerun (same spec as the 2026-10-28 run:
# two nodes, Cilium v1.16.5, kubeProxyReplacement=true, Hubble enabled).
set -euo pipefail
K3S_VERSION="v1.36.3+k3s1"
CILIUM_VERSION="1.16.5"
CILIUM_CLI_VERSION="v0.16.22"
CP_IP=172.16.0.2; W_IP=172.16.0.3
SSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=no"
log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

log "k3s server"
mkdir -p /etc/rancher/k3s
cat > /etc/rancher/k3s/config.yaml <<EOF
flannel-backend: none
disable-network-policy: true
disable-kube-proxy: true
disable:
  - traefik
  - servicelb
node-ip: $CP_IP
advertise-address: $CP_IP
write-kubeconfig-mode: "0600"
EOF
curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="$K3S_VERSION" INSTALL_K3S_EXEC=server sh -
for _ in $(seq 60); do kubectl get --raw /readyz >/dev/null 2>&1 && break; sleep 5; done
TOKEN=$(cat /var/lib/rancher/k3s/server/node-token)

log "k3s agent on worker-01"
printf 'server: https://%s:6443\ntoken: %s\nnode-ip: %s\n' "$CP_IP" "$TOKEN" "$W_IP" | \
  $SSH root@worker-01 'mkdir -p /etc/rancher/k3s && umask 077 && cat > /etc/rancher/k3s/config.yaml'
$SSH root@worker-01 "curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION='$K3S_VERSION' INSTALL_K3S_EXEC=agent sh -"
for _ in $(seq 60); do [ "$(kubectl get nodes --no-headers 2>/dev/null | wc -l)" -ge 2 ] && break; sleep 5; done

log "cilium-cli $CILIUM_CLI_VERSION"
curl -sfL "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz" | tar xz -C /usr/local/bin cilium

log "cilium $CILIUM_VERSION"
cilium install --version "$CILIUM_VERSION" \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost=$CP_IP --set k8sServicePort=6443 \
  --set ipam.mode=kubernetes \
  --set hubble.enabled=true
cilium status --wait --wait-duration 10m
kubectl get nodes -o wide
log "packages"
apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-yaml jq >/dev/null
log "DONE"
