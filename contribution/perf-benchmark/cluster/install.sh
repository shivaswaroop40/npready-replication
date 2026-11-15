#!/usr/bin/env bash
# Rebuild the perf-benchmark cluster on an iximiuz flexbox play.
#
# Runs on cp-01 as root from /opt/perfbench/cluster. Every phase is idempotent:
# re-running a phase converges to the same state. Usage:
#   bash install.sh all            # every phase in order
#   bash install.sh <phase> ...    # prereqs k3s clis cilium otterize gadget prepull lock
#                                  # verify smoke baseline
# Needs, next to this file: cilium-values.yaml, otterize-values.yaml, diff_cilium_config.py,
# lock.sh, smoke.sh, and cilium-config-20260910.json (the test-cluster dump; it is kept out of
# the shareable tree and copied to the VM separately, see NOTES.md). ../bin/cond.sh is used
# by the smoke and baseline phases.
#
# Layout (contract): cp-01 172.16.0.2 (2 vCPU / 3 GiB), worker-01 172.16.0.3 and
# worker-02 172.16.0.4 (4 vCPU / 6.5 GiB). Root on cp-01 can ssh to both workers.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(dirname "$HERE")

# ---- pins (mirror test-cluster; see versions.lock for what actually got installed) ----
K3S_VERSION="v1.36.3+k3s1"
CILIUM_CHART_VERSION="1.19.5"
HUBBLE_CLI_VERSION="v1.19.4"     # newest 1.19.x CLI release; laptop used the same
CILIUM_CLI_VERSION="v0.20.1"
HELM_VERSION="v4.3.0"            # laptop helm 4.3.0
OTTERIZE_CHART_VERSION="3.0.47"
IG_VERSION="v0.54.1"

CP_IP=172.16.0.2
WORKERS=(worker-01 worker-02)
declare -A WORKER_IP=([worker-01]=172.16.0.3 [worker-02]=172.16.0.4)

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
export PATH=/usr/local/bin:$PATH
SSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10"

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
die() { log "FATAL: $*"; exit 1; }
on_workers() { local w; for w in "${WORKERS[@]}"; do $SSH "root@$w" "$1"; done; }

# ---------------------------------------------------------------------------
phase_prereqs() {
  log "prereqs: packages on cp-01"
  export DEBIAN_FRONTEND=noninteractive
  if ! command -v conntrack >/dev/null || ! command -v hey >/dev/null || ! command -v envsubst >/dev/null; then
    apt-get update -qq
    apt-get install -y -qq conntrack hey gettext-base python3 >/dev/null
  fi
  command -v jq >/dev/null || apt-get install -y -qq jq >/dev/null
  log "prereqs: packages on workers"
  on_workers 'command -v conntrack >/dev/null || { export DEBIAN_FRONTEND=noninteractive; apt-get update -qq && apt-get install -y -qq conntrack >/dev/null; }'
  # ctnetlink must be loaded for `conntrack -S`; cilium loads the rest itself.
  local mods="nf_conntrack_netlink"
  modprobe $mods
  echo "$mods" > /etc/modules-load.d/perfbench.conf
  on_workers "modprobe $mods && echo $mods > /etc/modules-load.d/perfbench.conf"
}

# ---------------------------------------------------------------------------
phase_k3s() {
  log "k3s: server on cp-01 ($K3S_VERSION)"
  mkdir -p /etc/rancher/k3s
  # Contract flags: embedded etcd, no flannel, no k3s netpol controller, no traefik/servicelb.
  # local-storage and metrics-server stay (test-cluster used Cinder, not available here).
  # cgroup-driver systemd as on test-cluster' kubelets.
  cat > /etc/rancher/k3s/config.yaml <<EOF
cluster-init: true
flannel-backend: none
disable-network-policy: true
disable:
  - traefik
  - servicelb
node-ip: $CP_IP
advertise-address: $CP_IP
tls-san:
  - $CP_IP
  - cp-01
node-taint:
  - node-role.kubernetes.io/control-plane:NoSchedule
write-kubeconfig-mode: "0600"
kubelet-arg:
  - cgroup-driver=systemd
EOF
  if ! (k3s --version 2>/dev/null | grep -qF "$K3S_VERSION"); then
    curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="$K3S_VERSION" INSTALL_K3S_EXEC="server" sh -
  else
    systemctl is-active --quiet k3s || systemctl start k3s
  fi
  for _ in $(seq 60); do kubectl get --raw /readyz >/dev/null 2>&1 && break; sleep 5; done
  kubectl get --raw /readyz >/dev/null || die "k3s API not ready"

  local token; token=$(cat /var/lib/rancher/k3s/server/node-token)
  local w
  for w in "${WORKERS[@]}"; do
    log "k3s: agent on $w"
    # token goes over ssh stdin into a 0600 file; it is never written on the laptop
    printf 'server: https://%s:6443\ntoken: %s\nnode-ip: %s\nkubelet-arg:\n  - cgroup-driver=systemd\n' \
      "$CP_IP" "$token" "${WORKER_IP[$w]}" | \
      $SSH "root@$w" 'mkdir -p /etc/rancher/k3s && umask 077 && cat > /etc/rancher/k3s/config.yaml'
    $SSH "root@$w" "if ! (k3s --version 2>/dev/null | grep -qF '$K3S_VERSION'); then curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION='$K3S_VERSION' INSTALL_K3S_EXEC=agent sh - ; else systemctl is-active --quiet k3s-agent || systemctl start k3s-agent; fi"
  done
  for _ in $(seq 60); do [ "$(kubectl get nodes --no-headers 2>/dev/null | wc -l)" -ge 3 ] && break; sleep 5; done
  kubectl get nodes -o wide
}

# ---------------------------------------------------------------------------
fetch_tgz() { # url binary-name
  local tmp; tmp=$(mktemp -d)
  curl -sfL "$1" -o "$tmp/a.tgz"
  tar -xzf "$tmp/a.tgz" -C "$tmp"
  install -m 0755 "$(find "$tmp" -type f -name "$2" | head -1)" "/usr/local/bin/$2"
  rm -rf "$tmp"
}
phase_clis() {
  log "clis: helm $HELM_VERSION, cilium-cli $CILIUM_CLI_VERSION, hubble $HUBBLE_CLI_VERSION, kubectl-gadget $IG_VERSION"
  (helm version --short 2>/dev/null | grep -qF "$HELM_VERSION") || \
    fetch_tgz "https://get.helm.sh/helm-${HELM_VERSION}-linux-amd64.tar.gz" helm
  (cilium version --client 2>/dev/null | grep -qF "${CILIUM_CLI_VERSION}") || \
    fetch_tgz "https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz" cilium
  (hubble version 2>/dev/null | grep -qF "${HUBBLE_CLI_VERSION#v}") || \
    fetch_tgz "https://github.com/cilium/hubble/releases/download/${HUBBLE_CLI_VERSION}/hubble-linux-amd64.tar.gz" hubble
  # `kubectl-gadget version` fails while no gadget pod runs, so a marker file records the version
  mkdir -p /usr/local/share/perfbench
  if ! { [ -x /usr/local/bin/kubectl-gadget ] && grep -qxF "$IG_VERSION" /usr/local/share/perfbench/kubectl-gadget.version 2>/dev/null; }; then
    fetch_tgz "https://github.com/inspektor-gadget/inspektor-gadget/releases/download/${IG_VERSION}/kubectl-gadget-linux-amd64-${IG_VERSION}.tar.gz" kubectl-gadget
    echo "$IG_VERSION" > /usr/local/share/perfbench/kubectl-gadget.version
  fi
  grep -q 'KUBECONFIG=/etc/rancher/k3s/k3s.yaml' /root/.bashrc 2>/dev/null || \
    echo 'export KUBECONFIG=/etc/rancher/k3s/k3s.yaml' >> /root/.bashrc
}

# ---------------------------------------------------------------------------
phase_cilium() {
  log "cilium: chart $CILIUM_CHART_VERSION"
  helm repo add cilium https://helm.cilium.io >/dev/null 2>&1 || true
  helm repo update cilium >/dev/null
  helm upgrade --install cilium cilium/cilium --version "$CILIUM_CHART_VERSION" \
    -n kube-system -f "$HERE/cilium-values.yaml" --wait --timeout 15m
  kubectl -n kube-system rollout status ds/cilium --timeout=10m
  kubectl -n kube-system rollout status ds/cilium-envoy --timeout=10m
  kubectl -n kube-system rollout status deploy/cilium-operator --timeout=10m
  kubectl -n kube-system rollout status deploy/hubble-relay --timeout=10m
  # pods that started before the CNI existed (coredns, metrics-server, local-path) get
  # restarted so cilium manages their endpoints
  local ns_pod
  for ns_pod in $(kubectl get pods -A -o json | jq -r '.items[] | select(.spec.hostNetwork!=true) | select(.metadata.namespace=="kube-system") | .metadata.namespace+"/"+.metadata.name'); do
    local ns=${ns_pod%%/*} pod=${ns_pod##*/}
    kubectl -n "$ns" get ciliumendpoint "$pod" >/dev/null 2>&1 || kubectl -n "$ns" delete pod "$pod" --wait=false
  done
  cilium status --wait --wait-duration 10m
}

# ---------------------------------------------------------------------------
phase_otterize() {
  log "otterize: network-mapper chart $OTTERIZE_CHART_VERSION (release network-mapper, ns otterize-system)"
  helm repo add otterize https://helm.otterize.com >/dev/null 2>&1 || true
  helm repo update otterize >/dev/null
  helm upgrade --install network-mapper otterize/network-mapper --version "$OTTERIZE_CHART_VERSION" \
    -n otterize-system --create-namespace -f "$HERE/otterize-values.yaml" --wait --timeout 10m
}

# ---------------------------------------------------------------------------
phase_gadget() {
  log "gadget: kubectl gadget deploy $IG_VERSION"
  if ! kubectl -n gadget get ds gadget >/dev/null 2>&1; then
    kubectl gadget deploy --image "ghcr.io/inspektor-gadget/inspektor-gadget:${IG_VERSION}"
  fi
  kubectl -n gadget rollout status ds/gadget --timeout=10m
}

# ---------------------------------------------------------------------------
# Pull every observer image on every node so no condition pays a first-pull cost.
phase_prepull() {
  local imgs
  # from the controllers' pod templates, so observers that are switched off are included
  imgs=$(kubectl get deploy,ds,sts -A -o json | \
    jq -r '.items[].spec.template.spec | ((.containers // []) + (.initContainers // []))[].image' | sort -u)
  # The gadget images (trace_tcp, snapshot_socket) are OCI artifacts that the gadget pods pull
  # into their own emptyDir store, not containerd images; cond.sh warms them per fresh gadget pod.
  log "prepull: $(echo "$imgs" | wc -l) images on cp-01 and workers"
  echo "$imgs" | while read -r i; do [ -n "$i" ] && k3s crictl pull "$i" >/dev/null 2>&1 || true; done
  local w
  for w in "${WORKERS[@]}"; do
    echo "$imgs" | $SSH "root@$w" 'while read -r i; do [ -n "$i" ] && k3s crictl pull "$i" >/dev/null 2>&1 || true; done'
  done
}

# ---------------------------------------------------------------------------
phase_verify() {
  log "verify: nodes, cilium config diff, observers"
  kubectl get nodes -o wide
  cilium status --wait --wait-duration 5m
  python3 "$HERE/diff_cilium_config.py" "$HERE/cilium-config-20260910.json" || true
}

# ---------------------------------------------------------------------------
phase_lock() {
  bash "$HERE/lock.sh" > "$HERE/versions.lock"
  log "lock: wrote $HERE/versions.lock"
}

# Exercise every observer once via bin/cond.sh (ends in baseline).
phase_smoke() { bash "$HERE/smoke.sh"; }

# Leave the cluster in the baseline condition.
phase_baseline() { bash "$ROOT/bin/cond.sh" baseline; }

# ---------------------------------------------------------------------------
main() {
  [ "$(id -u)" = 0 ] || die "run as root"
  local phases=("$@")
  [ ${#phases[@]} -eq 0 ] && phases=(all)
  [ "${phases[0]}" = all ] && phases=(prereqs k3s clis cilium otterize gadget prepull lock verify smoke baseline)
  local p
  for p in "${phases[@]}"; do
    declare -F "phase_$p" >/dev/null || die "unknown phase $p"
    "phase_$p"
  done
  log "install.sh done: ${phases[*]}"
}
main "$@"
