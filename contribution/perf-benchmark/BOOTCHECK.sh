#!/usr/bin/env bash
# BOOTCHECK.sh: run on cp-01 as root right after a play starts from the perfbench template.
#
# Waits (up to BOOT_TIMEOUT seconds, default 900) until the cluster that was frozen in the
# template is usable again, then prints one line per check on stderr and, as the last line on
# stdout, "OK" (exit 0) or "FAIL: <reasons>" (exit 1). It checks:
#   - k3s (cp-01) and k3s-agent (worker-01, worker-02) are enabled and active
#   - root on cp-01 reaches both workers over ssh without a password. A new play gets new host
#     keys, so stale known_hosts entries from the template are dropped and the new keys accepted.
#   - the API answers and cp-01, worker-01, worker-02 are Ready
#   - ds/cilium and ds/cilium-envoy are ready on all 3 nodes, every agent reports
#     "cilium-dbg status --brief" = OK, and cilium-operator, coredns, metrics-server and
#     local-path-provisioner are available
#   - the pre-pulled images are still in containerd (workers: apps/*/images.txt; cp-01: the
#     images of every steady.yaml and throughput.yaml)
#   - the tools the harness calls exist
# It changes nothing in the cluster. Run cond.sh <cond> afterwards to pick a condition, and
# write the play id first: echo <play-id> > /opt/perfbench/PLAY_ID
set -uo pipefail
export KUBECONFIG=${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}
export PATH=/usr/local/bin:$PATH
PB_ROOT=${PB_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
BOOT_TIMEOUT=${BOOT_TIMEOUT:-900}
NODES=(cp-01 worker-01 worker-02)
declare -A IP=([cp-01]=172.16.0.2 [worker-01]=172.16.0.3 [worker-02]=172.16.0.4)
WORKERS=(worker-01 worker-02)
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 -o LogLevel=ERROR)
DEADLINE=$(( $(date +%s) + BOOT_TIMEOUT ))
T0=$(date +%s)
FAILS=()

log() { printf '[bootcheck %s +%ss] %s\n' "$(date -u +%H:%M:%SZ)" "$(( $(date +%s) - T0 ))" "$*" >&2; }
fail() { FAILS+=("$*"); log "FAIL $*"; }
left() { echo $(( DEADLINE - $(date +%s) )); }
# wait_for <label> <command...>: retry every 5 s until the command succeeds or the deadline
wait_for() {
  local label=$1; shift
  until "$@" >/dev/null 2>&1; do
    [ "$(left)" -gt 0 ] || { fail "$label (timed out after ${BOOT_TIMEOUT}s)"; return 1; }
    sleep 5
  done
  log "ok   $label"
}
on() { ssh -n "${SSH_OPTS[@]}" "root@${IP[$1]}" "$2"; }

[ "$(id -u)" = 0 ] || { echo "FAIL: run as root"; exit 1; }
[ "$(hostname -s)" = cp-01 ] || log "warning: expected to run on cp-01, this is $(hostname -s)"

# ---- 1. local unit ---------------------------------------------------------------------------
[ "$(systemctl is-enabled k3s 2>/dev/null)" = enabled ] || fail "k3s.service not enabled on cp-01"
wait_for "k3s.service active on cp-01" systemctl is-active --quiet k3s

# ---- 2. ssh to the workers (fix stale host keys once) ----------------------------------------
ssh_ok() { on "$1" true; }
for w in "${WORKERS[@]}"; do
  wait_for "tcp/22 open on $w" timeout 3 bash -c "exec 3<>/dev/tcp/${IP[$w]}/22" || continue
  if ! ssh_ok "$w" 2>/dev/null; then
    err=$(on "$w" true 2>&1 >/dev/null || true)
    if grep -qiE 'host key|IDENTIFICATION HAS CHANGED' <<<"$err"; then
      log "host key of $w changed (new play): replacing its known_hosts entries"
      for h in "${IP[$w]}" "$w"; do ssh-keygen -R "$h" >/dev/null 2>&1 || true; done
    fi
  fi
  wait_for "passwordless root ssh cp-01 -> $w" ssh_ok "$w" || continue
  # the name form too (cluster/install.sh and some notes use it)
  ssh -n "${SSH_OPTS[@]}" "root@$w" true >/dev/null 2>&1 || {
    ssh-keygen -R "$w" >/dev/null 2>&1 || true
    ssh -n "${SSH_OPTS[@]}" "root@$w" true >/dev/null 2>&1 || log "warning: ssh root@$w by name fails (by IP works)"; }
  st=$(on "$w" 'echo "$(systemctl is-enabled k3s-agent 2>&1) $(systemctl is-active k3s-agent 2>&1)"' 2>/dev/null)
  [ "${st%% *}" = enabled ] || fail "k3s-agent not enabled on $w ($st)"
  wait_for "k3s-agent active on $w" on "$w" 'systemctl is-active --quiet k3s-agent'
done

# ---- 3. API and nodes ------------------------------------------------------------------------
wait_for "API server answers" kubectl get --raw /readyz
node_ready() { [ "$(kubectl get node "$1" -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)" = True ]; }
for n in "${NODES[@]}"; do wait_for "node $n Ready" node_ready "$n"; done

# ---- 4. cilium and the system deployments ----------------------------------------------------
ds_ready() {  # ns ds want
  local s; s=$(kubectl -n "$1" get ds "$2" -o jsonpath='{.status.desiredNumberScheduled} {.status.numberReady} {.status.updatedNumberScheduled} {.status.numberAvailable}' 2>/dev/null) || return 1
  read -r des rdy upd av <<<"$s"
  [ "$des" = "$3" ] && [ "$rdy" = "$3" ] && [ "$upd" = "$3" ] && [ "${av:-0}" = "$3" ]
}
deploy_avail() {  # ns deploy
  local s; s=$(kubectl -n "$1" get deploy "$2" -o jsonpath='{.spec.replicas} {.status.availableReplicas} {.status.updatedReplicas}' 2>/dev/null) || return 1
  read -r want av upd <<<"$s"
  [ "${want:-0}" -gt 0 ] && [ "${av:-0}" = "$want" ] && [ "${upd:-0}" = "$want" ]
}
agents_ok() {
  local p n=0
  for p in $(kubectl -n kube-system get pods -l k8s-app=cilium -o name 2>/dev/null); do
    [ "$(kubectl -n kube-system exec "$p" -c cilium-agent -- cilium-dbg status --brief 2>/dev/null)" = OK ] || return 1
    n=$((n + 1))
  done
  [ "$n" -eq ${#NODES[@]} ]
}
wait_for "ds/cilium ready on ${#NODES[@]} nodes" ds_ready kube-system cilium ${#NODES[@]}
wait_for "ds/cilium-envoy ready on ${#NODES[@]} nodes" ds_ready kube-system cilium-envoy ${#NODES[@]}
wait_for "every cilium agent: cilium-dbg status --brief = OK" agents_ok
for d in cilium-operator coredns metrics-server local-path-provisioner; do
  wait_for "deploy/$d available" deploy_avail kube-system "$d"
done
kube_system_settled() {  # every kube-system pod Running and Ready, or Succeeded
  [ -z "$(kubectl -n kube-system get pods -o json 2>/dev/null | jq -r '.items[]
     | select(.status.phase != "Succeeded")
     | select(.status.phase != "Running" or ([.status.containerStatuses[]? | .ready] | all | not))
     | .metadata.name')" ]
}
wait_for "all kube-system pods Running and Ready" kube_system_settled
# DNS from a pod's point of view is exercised by every app deploy; here only the service exists
kubectl -n kube-system get svc kube-dns >/dev/null 2>&1 || fail "svc kube-dns missing"

# ---- 5. pre-pulled images ----------------------------------------------------------------------
APPS=(boutique bank dsb otel teastore)
WORKER_IMGS=$(for a in "${APPS[@]}"; do grep -vE '^[[:space:]]*(#|$)' "$PB_ROOT/apps/$a/images.txt" | awk '{print $1}'; done | sort -u)
CP_IMGS=$(for a in "${APPS[@]}"; do grep -hE '^[[:space:]]*image:' "$PB_ROOT/apps/$a/steady.yaml" "$PB_ROOT/apps/$a/throughput.yaml" | awk '{print $2}'; done | tr -d '"'"'" | sort -u)
# shellcheck disable=SC2016  # runs on the node
MISSING_SH='m=0; while read -r i; do [ -n "$i" ] || continue; k3s crictl inspecti "$i" >/dev/null 2>&1 || { echo "missing $i"; m=$((m+1)); }; done; echo "missing_total $m"'
for n in "${NODES[@]}"; do
  if [ "$n" = cp-01 ]; then imgs=$CP_IMGS; out=$(bash -c "$MISSING_SH" <<<"$imgs" 2>&1)
  else imgs=$WORKER_IMGS; out=$(ssh "${SSH_OPTS[@]}" "root@${IP[$n]}" "$MISSING_SH" <<<"$imgs" 2>&1); fi
  want=$(grep -c . <<<"$imgs"); miss=$(awk '/^missing_total/{print $2}' <<<"$out")
  if [ "${miss:-x}" = 0 ]; then log "ok   $n has all $want pre-pulled images"
  else fail "$n: ${miss:-?} of $want pre-pulled images missing ($(grep '^missing ' <<<"$out" | head -3 | cut -d' ' -f2 | tr '\n' ' '))"; fi
done

# ---- 6. tools ----------------------------------------------------------------------------------
for t in kubectl helm jq python3 conntrack hubble cilium kubectl-gadget crictl systemd-run curl envsubst hey; do
  command -v "$t" >/dev/null 2>&1 || fail "tool $t missing on cp-01"
done
for w in "${WORKERS[@]}"; do
  m=$(on "$w" 'for t in python3 conntrack crictl jq; do command -v $t >/dev/null || printf "%s " $t; done' 2>/dev/null)
  [ -z "$m" ] || fail "tools missing on $w: $m"
done
[ -x "$PB_ROOT/bin/cond.sh" ] || [ -f "$PB_ROOT/bin/cond.sh" ] || fail "$PB_ROOT/bin/cond.sh missing"

# ---- info (never fails) -------------------------------------------------------------------------
EH=$(kubectl -n kube-system get cm cilium-config -o jsonpath='{.data.enable-hubble}' 2>/dev/null)
OBS=$(for ns in otterize-system gadget; do printf '%s=%s ' "$ns" "$(kubectl -n "$ns" get pods --no-headers 2>/dev/null | wc -l)"; done)
RELAY=$(kubectl -n kube-system get pods -l k8s-app=hubble-relay --no-headers 2>/dev/null | wc -l)
log "info cilium-config enable-hubble=$EH; observer pods: hubble-relay=$RELAY $OBS(baseline = false and all 0)"
log "info k3s $(k3s --version 2>/dev/null | head -1 | awk '{print $3}'), kernel $(uname -r), results dirs: $(find "$PB_ROOT/results" -mindepth 1 -maxdepth 1 2>/dev/null | wc -l)"
[ -s "$PB_ROOT/PLAY_ID" ] && log "info PLAY_ID=$(cat "$PB_ROOT/PLAY_ID")" \
  || log "info PLAY_ID not set yet: echo <play-id> > $PB_ROOT/PLAY_ID before run_matrix.sh"

if [ ${#FAILS[@]} -eq 0 ]; then
  log "all checks passed in $(( $(date +%s) - T0 ))s"
  echo OK; exit 0
fi
echo "FAIL: $(IFS=';'; echo "${FAILS[*]}")"; exit 1
