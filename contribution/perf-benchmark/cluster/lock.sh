#!/usr/bin/env bash
# Print every version and digest actually installed on the perf-benchmark cluster.
# Run on cp-01 as root; install.sh `lock` phase writes the output to versions.lock.
set -euo pipefail
export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
export PATH=/usr/local/bin:$PATH
SSH="ssh -o BatchMode=yes -o StrictHostKeyChecking=no -o ConnectTimeout=10"

echo "# versions.lock - generated $(date -u +%FT%TZ) by cluster/lock.sh on $(hostname)"
echo "# format: <component> <version> [digest/notes]"
echo
echo "## nodes"
kubectl get nodes -o json | jq -r '.items[] | "node \(.metadata.name) kubelet=\(.status.nodeInfo.kubeletVersion) runtime=\(.status.nodeInfo.containerRuntimeVersion) kernel=\(.status.nodeInfo.kernelVersion) os=\"\(.status.nodeInfo.osImage)\" cpu=\(.status.capacity.cpu) mem=\(.status.capacity.memory) podCIDR=\(.spec.podCIDR) taints=\([.spec.taints[]?|.key+":"+.effect]|join(","))"'
for h in cp-01 worker-01 worker-02; do
  if [ "$h" = "$(hostname)" ]; then v=$(k3s --version | head -1); else v=$($SSH "root@$h" 'k3s --version | head -1'); fi
  echo "k3s-binary $h $v"
done
echo "k3s-server-config $(tr '\n' ' ' < /etc/rancher/k3s/config.yaml)"
echo
echo "## helm releases"
helm list -A -o json | jq -r '.[] | "helm \(.name) ns=\(.namespace) chart=\(.chart) app=\(.app_version) rev=\(.revision)"'
echo
echo "## controller images (deploy/ds/sts pod templates; digest from the image store on cp-01,"
echo "## filled by install.sh prepull, so observers that are switched off are included)"
kubectl get deploy,ds,sts -A -o json | \
  jq -r '.items[] | select(.metadata.namespace | IN("kube-system","otterize-system","gadget")) | .metadata.namespace as $ns | .kind as $k | .metadata.name as $n | .spec.template.spec | ((.containers // []) + (.initContainers // []))[] | "\($ns) \($k)/\($n) \(.image)"' | sort -u | \
  while read -r ns obj img; do
    d=$(k3s crictl inspecti -o json "$img" 2>/dev/null | jq -r '.status.repoDigests[0] // empty' || true)
    echo "image $ns $obj $img ${d:-digest-unknown}"
  done
echo
echo "## gadget images (OCI artifacts pulled by the gadget pods, not by containerd;"
echo "## digest = Docker-Content-Digest of the tag on ghcr.io at lock time)"
for g in trace_tcp snapshot_socket; do
  ref="ghcr.io/inspektor-gadget/gadget/${g}:v0.54.1"
  tok=$(curl -s "https://ghcr.io/token?scope=repository:inspektor-gadget/gadget/${g}:pull" | jq -r .token)
  d=$(curl -sI -H "Authorization: Bearer $tok" \
      -H 'Accept: application/vnd.oci.image.index.v1+json,application/vnd.oci.image.manifest.v1+json' \
      "https://ghcr.io/v2/inspektor-gadget/gadget/${g}/manifests/v0.54.1" | tr -d '\r' | awk 'tolower($1)=="docker-content-digest:"{print $2}')
  echo "gadget-image $ref ${d:-digest-unknown}"
done
echo
echo "## clients on cp-01"
echo "kubectl $(kubectl version --client -o json | jq -r .clientVersion.gitVersion)"
echo "helm $(helm version --short)"
echo "cilium-cli $(cilium version --client 2>/dev/null | head -1)"
echo "hubble $(hubble version 2>/dev/null | head -1)"
echo "kubectl-gadget $(cat /usr/local/share/perfbench/kubectl-gadget.version 2>/dev/null || echo unknown)"
for b in k3s helm cilium hubble kubectl-gadget; do echo "sha256 $(sha256sum "/usr/local/bin/$b")"; done
echo "hey $(dpkg-query -W -f='${Version}' hey 2>/dev/null)"
echo "conntrack $(conntrack --version 2>&1 | head -1)"
echo "jq $(jq --version)"
echo "python3 $(python3 --version 2>&1)"
for h in worker-01 worker-02; do echo "conntrack@$h $($SSH "root@$h" 'conntrack --version 2>&1 | head -1')"; done
