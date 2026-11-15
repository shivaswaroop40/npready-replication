#!/usr/bin/env bash
# shellcheck shell=bash disable=SC2034,SC2029,SC2016
# (SC2034: variables are used by the scripts that source this file; SC2029/SC2016: remote
#  command strings are built locally on purpose and single-quoted parts expand on the node)
# lib.sh: shared helpers for run_one.sh and run_matrix.sh. Sourced, never executed.
# Runs on cp-01 as root. Needs bash >= 5 (EPOCHREALTIME), kubectl, jq, python3, systemd-run,
# ssh/scp to the workers as root without a password.

export LC_ALL=C                 # EPOCHREALTIME must use '.' as decimal separator
PB_ROOT=${PB_ROOT:-/opt/perfbench}
PB_BIN=${PB_BIN:-$PB_ROOT/bin}
PB_APPS=${PB_APPS:-$PB_ROOT/apps}
PB_RESULTS=${PB_RESULTS:-$PB_ROOT/results}
export KUBECONFIG=${KUBECONFIG:-/etc/rancher/k3s/k3s.yaml}
export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin   # appended: callers (and test mocks) win

PB_CONDS_ALL="baseline hubble otterize ig_tcp ig_snap"
# not part of the default 5-condition matrix: only with run_matrix.sh --conds (agent-only Hubble experiment)
PB_CONDS_EXTRA="hubble_agent"
PB_CONDS_KNOWN="$PB_CONDS_ALL $PB_CONDS_EXTRA"
PB_CP_NODE=${PB_CP_NODE:-cp-01}
PB_NODES=${PB_NODES:-"cp-01 worker-01 worker-02"}
PB_REMOTE_TMP=${PB_REMOTE_TMP:-/var/tmp/perfbench}
PB_SAMPLE_S=${PB_SAMPLE_S:-5}
PB_LOCK=${PB_LOCK:-/run/perfbench.lock}
PB_SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8
             -o ServerAliveInterval=15 -o ServerAliveCountMax=4 -o LogLevel=ERROR)
# metric families kept from the cilium agent :9962 scrape (hubble :9965 keeps every hubble_*)
PB_CILIUM_METRIC_RE='^(cilium_(drop|forward|policy|process_|errors_warnings|bpf_map_pressure|datapath_conntrack|endpoint_regenerations|unreachable)|hubble_)'
PB_RUN=${PB_RUN:-}
declare -A PB_ADDR=()

# ---- time, logging, run records --------------------------------------------------------
pb_now() { printf '%s\n' "$EPOCHREALTIME"; }
pb_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }
pb_log() {
  local m; m="[$(pb_iso)] $*"
  printf '%s\n' "$m" >&2
  if [ -n "$PB_RUN" ] && [ -d "$PB_RUN" ]; then printf '%s\n' "$m" >> "$PB_RUN/run.log"; fi
  return 0
}
pb_die() { pb_log "FATAL: $*"; exit 1; }
# pb_mark <phase>: append "<phase>\t<epoch float>\t<iso>" to phases.tsv (meta.json reads it)
pb_mark() { printf '%s\t%s\t%s\n' "$1" "$(pb_now)" "$(pb_iso)" >> "$PB_RUN/phases.tsv"; pb_log "phase $1"; }
pb_kv()   { local v=${2//$'\n'/ }; v=${v#"${v%%[![:space:]]*}"}; printf '%s\t%s\n' "$1" "${v%"${v##*[![:space:]]}"}" >> "$PB_RUN/kv.tsv"; }
pb_warn() { pb_log "WARN: $*"; printf '%s\n' "$*" >> "$PB_RUN/warnings.txt"; }
# float compare: pb_fge a b  -> success when a >= b
pb_fge() { awk -v a="$1" -v b="$2" 'BEGIN{exit !(a >= b)}'; }
pb_fadd() { awk -v a="$1" -v b="$2" 'BEGIN{printf "%.6f\n", a + b}'; }

K() { kubectl --request-timeout=60s "$@"; }

# ---- app bundle -------------------------------------------------------------------------
# pb_load_app <app>: export every variable in apps/<app>/app.env, set PB_APP_DIR, PB_APP_VARS
pb_load_app() {
  local app=$1 f=$PB_APPS/$1/app.env
  [ -f "$f" ] || { pb_log "missing $f"; return 1; }
  set -a
  # shellcheck disable=SC1090
  . "$f" || { set +a; pb_log "cannot source $f"; return 1; }
  set +a
  [ -n "${APP_NS:-}" ] || { pb_log "$f does not set APP_NS"; return 1; }
  [ -n "${TP_URL:-}" ] || { pb_log "$f does not set TP_URL"; return 1; }
  local x
  for x in deploy.sh undeploy.sh restart.sh steady.yaml throughput.yaml; do
    [ -f "$PB_APPS/$app/$x" ] || { pb_log "missing apps/$app/$x"; return 1; }
  done
  export READY_TIMEOUT=${READY_TIMEOUT:-600} TP_HEADERS=${TP_HEADERS:-}
  PB_APP_DIR=$PB_APPS/$app
  PB_APP_VARS=$(grep -oE '^[[:space:]]*(export[[:space:]]+)?[A-Za-z_][A-Za-z0-9_]*=' "$f" \
                | sed -E 's/^[[:space:]]*(export[[:space:]]+)?//; s/=$//' | sort -u | tr '\n' ' ')
}

# pb_render <file> VAR...: print the file with ${VAR} / $VAR replaced for the named VARs only.
# Every other '$' (shell in container args, lua, ...) is left alone. Unset VARs become ''.
pb_render() {
  python3 - "$@" <<'PY'
import os, re, sys
path, names = sys.argv[1], set(sys.argv[2:])
text = open(path).read()
def sub(m):
    n = m.group(1) or m.group(2)
    return os.environ.get(n, "") if n in names else m.group(0)
sys.stdout.write(re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)\b", sub, text))
PY
}

# ---- nodes --------------------------------------------------------------------------------
pb_resolve_nodes() {
  local n ip
  while read -r n ip; do
    [ -n "$n" ] && PB_ADDR[$n]=${ip:-$n}
  done < <(K get nodes -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.status.addresses[?(@.type=="InternalIP")].address}{"\n"}{end}' 2>/dev/null)
  for n in $PB_NODES; do [ -n "${PB_ADDR[$n]:-}" ] || PB_ADDR[$n]=$n; done
}
pb_addr() { printf '%s' "${PB_ADDR[$1]:-$1}"; }
pb_is_local() { [ "$1" = "$PB_CP_NODE" ]; }
# pb_on <node> <command string>: run on a node (locally on cp-01), stdin from /dev/null
pb_on() {
  local n=$1; shift
  if pb_is_local "$n"; then bash -c "$*" </dev/null
  else ssh -n "${PB_SSH_OPTS[@]}" "root@$(pb_addr "$n")" "$*"; fi
}
# pb_on_in <node> <command string>: same, but passes stdin through
pb_on_in() {
  local n=$1; shift
  if pb_is_local "$n"; then bash -c "$*"
  else ssh "${PB_SSH_OPTS[@]}" "root@$(pb_addr "$n")" "$*"; fi
}
pb_put() { # node local remote
  if pb_is_local "$1"; then [ "$2" -ef "$3" ] || cp "$2" "$3"
  else scp -q "${PB_SSH_OPTS[@]}" "$2" "root@$(pb_addr "$1"):$3"; fi
}
pb_get() { # node remote local
  if pb_is_local "$1"; then [ "$2" -ef "$3" ] || cp "$2" "$3"
  else scp -q "${PB_SSH_OPTS[@]}" "root@$(pb_addr "$1"):$2" "$3"; fi
}
# offset = node clock - cp-01 clock (s), from a bracketed remote `date`; stored in kv.tsv
pb_clock_offsets() {
  local n a b r
  for n in $PB_NODES; do
    if pb_is_local "$n"; then pb_kv "clock_offset_s.$n" 0; continue; fi
    a=$(pb_now); r=$(pb_on "$n" 'date +%s.%N' 2>/dev/null); b=$(pb_now)
    if [ -n "$r" ]; then
      pb_kv "clock_offset_s.$n" "$(awk -v a="$a" -v b="$b" -v r="$r" 'BEGIN{printf "%.4f", r - (a + b) / 2}')"
      pb_kv "clock_rtt_s.$n" "$(awk -v a="$a" -v b="$b" 'BEGIN{printf "%.4f", b - a}')"
    else
      pb_warn "clock offset for $n unavailable"
    fi
  done
}

# ---- samplers (one transient systemd service per node) -------------------------------------
pb_sampler_path() { # node -> where that node's sampler writes
  if pb_is_local "$1"; then printf '%s/samples-%s.csv' "$PB_RUN" "$1"
  else printf '%s/%s/samples-%s.csv' "$PB_REMOTE_TMP" "$PB_RUN_ID" "$1"; fi
}
pb_sampler_kill() { # node: stop any sampler left over from an earlier run
  pb_on "$1" 'systemctl stop perfbench-sampler.service >/dev/null 2>&1; systemctl reset-failed perfbench-sampler.service >/dev/null 2>&1; true'
}
pb_sampler_start() { # node
  local n=$1 out; out=$(pb_sampler_path "$n")
  pb_on "$n" "mkdir -p '$PB_BIN' '$(dirname "$out")' && rm -f '$out' '$out.info.json'" || return 1
  pb_is_local "$n" || pb_put "$n" "$PB_BIN/sampler.py" "$PB_BIN/sampler.py" || return 1
  pb_sampler_kill "$n"
  pb_on "$n" "systemd-run --quiet --collect --unit=perfbench-sampler.service /usr/bin/python3 '$PB_BIN/sampler.py' --node '$n' --interval '$PB_SAMPLE_S' --out '$out'"
}
pb_sampler_ok() { # node: unit active and at least one data row written
  local out; out=$(pb_sampler_path "$1")
  pb_on "$1" "systemctl is-active --quiet perfbench-sampler.service && [ \$(wc -l < '$out') -ge 2 ]"
}
pb_sampler_stop_fetch() { # node: stop, then copy CSV + info.json into the run dir
  local n=$1 out; out=$(pb_sampler_path "$n")
  pb_on "$n" 'systemctl stop perfbench-sampler.service >/dev/null 2>&1; true'
  pb_is_local "$n" && return 0
  [ -s "$PB_RUN/samples-$n.csv" ] && return 0      # already fetched (cleanup after a failure)
  pb_get "$n" "$out" "$PB_RUN/samples-$n.csv" || { pb_warn "could not fetch samples from $n"; return 1; }
  pb_get "$n" "$out.info.json" "$PB_RUN/samples-$n.csv.info.json" || pb_warn "no sampler info from $n"
  pb_on "$n" "rm -f '$out' '$out.info.json'; rmdir '$(dirname "$out")' 2>/dev/null; true"
}

# ---- host-speed canary (one transient scope pb-canary per node) ----------------------------
# canary.py runs a fixed CPU-bound kernel every PB_CANARY_S seconds and logs its wall and thread
# CPU time (canary-<node>.csv). The analysis turns that into a host speed index per segment and
# normalises CPU and fixed-count time by it. The scope name starts with pb-, so the sampler sees
# it, and analyze.py counts it as harness. PB_CANARY=0 switches it off; PB_CANARY_ITERS overrides
# the kernel size (keep it fixed across a matrix). The lock fd 8 is closed for the canary, so a
# canary left running never holds the benchmark lock.
PB_CANARY=${PB_CANARY:-1}
PB_CANARY_S=${PB_CANARY_S:-2}
PB_CANARY_ITERS=${PB_CANARY_ITERS:-}
pb_canary_path() { # node -> where that node's canary writes
  if pb_is_local "$1"; then printf '%s/canary-%s.csv' "$PB_RUN" "$1"
  else printf '%s/%s/canary-%s.csv' "$PB_REMOTE_TMP" "$PB_RUN_ID" "$1"; fi
}
pb_canary_kill() { # node: stop a canary left over from an earlier run
  pb_on "$1" 'systemctl stop pb-canary.scope >/dev/null 2>&1; systemctl reset-failed pb-canary.scope >/dev/null 2>&1; true'
}
pb_canary_start() { # node
  local n=$1 out it=""; out=$(pb_canary_path "$n")
  [ -z "$PB_CANARY_ITERS" ] || it="--iterations '$PB_CANARY_ITERS'"
  pb_on "$n" "mkdir -p '$PB_BIN' '$(dirname "$out")' && rm -f '$out' '$out.info.json' '$out.err'" || return 1
  pb_is_local "$n" || pb_put "$n" "$PB_BIN/canary.py" "$PB_BIN/canary.py" || return 1
  pb_canary_kill "$n"
  pb_on "$n" "setsid nohup systemd-run --scope --quiet --unit=pb-canary -- /usr/bin/python3 '$PB_BIN/canary.py' --node '$n' --interval '$PB_CANARY_S' $it --out '$out' </dev/null >/dev/null 2>>'$out.err' 8>&- & sleep 1; systemctl is-active --quiet pb-canary.scope"
}
pb_canary_ok() { # node: scope active and at least one data row written
  local out; out=$(pb_canary_path "$1")
  pb_on "$1" "systemctl is-active --quiet pb-canary.scope && [ \$(wc -l < '$out') -ge 2 ]"
}
pb_canary_stop_fetch() { # node: stop, then copy CSV + info.json into the run dir
  local n=$1 out; out=$(pb_canary_path "$n")
  pb_on "$n" 'systemctl stop pb-canary.scope >/dev/null 2>&1; systemctl reset-failed pb-canary.scope >/dev/null 2>&1; true'
  if pb_is_local "$n"; then [ -s "$out.err" ] || rm -f "$out.err"; return 0; fi
  [ -s "$PB_RUN/canary-$n.csv" ] && return 0      # already fetched (cleanup after a failure)
  pb_get "$n" "$out" "$PB_RUN/canary-$n.csv" || { pb_warn "could not fetch canary samples from $n"; return 1; }
  pb_get "$n" "$out.info.json" "$PB_RUN/canary-$n.csv.info.json" || pb_warn "no canary info from $n"
  if pb_on "$n" "[ -s '$out.err' ]"; then pb_get "$n" "$out.err" "$PB_RUN/canary-$n.csv.err" || true; fi
  pb_on "$n" "rm -f '$out' '$out.info.json' '$out.err'; rmdir '$(dirname "$out")' 2>/dev/null; true"
}

# ---- client processes (each in its own transient scope pb-<name>, so it can be sampled) ------
pb_client_start() { # name stdout-file stderr-file cmd...
  local name=$1 out=$2 err=$3; shift 3
  systemctl stop "pb-$name.scope" >/dev/null 2>&1
  systemctl reset-failed "pb-$name.scope" >/dev/null 2>&1
  nohup systemd-run --scope --quiet --unit="pb-$name" -- "$@" >>"$out" 2>>"$err" </dev/null 8>&- &
  printf '%s\n' "$!" > "$PB_RUN/.pid-$name"
  pb_kv "client.$name.cmd" "$*"
  sleep 3
  systemctl is-active --quiet "pb-$name.scope"
}
pb_client_alive() { systemctl is-active --quiet "pb-$1.scope"; }
pb_client_stop() {
  local p
  systemctl stop "pb-$1.scope" >/dev/null 2>&1
  p=$(cat "$PB_RUN/.pid-$1" 2>/dev/null) && [ -n "$p" ] && wait "$p" 2>/dev/null
  return 0
}
pb_stop_all_clients() {
  local u
  for u in $(systemctl list-units --all --plain --no-legend 'pb-*.scope' 2>/dev/null | awk '{print $1}'); do
    systemctl stop "$u" >/dev/null 2>&1
    systemctl reset-failed "$u" >/dev/null 2>&1
  done
  return 0
}
# pb_oneshot <name> <stdout-file> <timeout_s> cmd...: run a short client in scope pb-<name>
pb_oneshot() {
  local name=$1 out=$2 t=$3; shift 3
  systemctl reset-failed "pb-$name.scope" >/dev/null 2>&1
  timeout "$t" systemd-run --scope --quiet --unit="pb-$name" -- "$@" >"$out" 2>>"$PB_RUN/oneshot.err" </dev/null 8>&-
}

# ---- gadgets ---------------------------------------------------------------------------------
# pb_gadget_tag: the gadget IMAGE tag (trace_tcp, snapshot_socket). PB_GADGET_TAG wins; else
# GADGET_TAG from cluster/gadget.env (shared with cond.sh's warm-up, so both run the same image);
# else v0.54.1. The IG server (DaemonSet, kubectl-gadget) stays v0.54.1 either way. test-cluster
# ran the :latest gadget images of September 2026, which were built with ig v0.55.1, on its
# v0.54.1 server (warning in every thesis captureA/ig_tcp.err), so gadget.env pins v0.55.1.
pb_gadget_tag() {
  local v=""
  if [ -n "${PB_GADGET_TAG:-}" ]; then printf '%s\n' "$PB_GADGET_TAG"; return; fi
  [ -f "$PB_ROOT/cluster/gadget.env" ] && v=$(sed -n 's/^GADGET_TAG=//p' "$PB_ROOT/cluster/gadget.env" | tail -1)
  printf '%s\n' "${v:-v0.54.1}"
}
# pb_gadget_ref <gadget>: "<gadget>:<tag>"
pb_gadget_ref() { printf '%s:%s\n' "$1" "$(pb_gadget_tag)"; }

# ---- Jobs from app templates --------------------------------------------------------------------
# pb_job_create <ns> <job-name> <template> VAR...: render the template, rename its single Job,
# set backoffLimit 0 (one pod, so timing is clean), drop ttlSecondsAfterFinished (keep logs),
# label it perfbench=1, save the manifest under jobs/ and apply it.
pb_job_create() {
  local ns=$1 name=$2 tpl=$3; shift 3
  local json n
  K -n "$ns" delete job "$name" --ignore-not-found --wait=true --timeout=90s >/dev/null 2>&1
  json=$(pb_render "$tpl" "$@" | K create --dry-run=client -o json -f -) || { pb_log "cannot render $tpl"; return 1; }
  n=$(jq '[if .kind=="List" then .items[] else . end | select(.kind=="Job")] | length' <<<"$json")
  [ "$n" = 1 ] || { pb_log "$tpl renders $n Jobs (need exactly 1)"; return 1; }
  jq --arg n "$name" '
    def fix: if .kind == "Job" then
        .metadata.name = $n | .metadata.labels.perfbench = "1" | .spec.backoffLimit = 0
        | del(.spec.ttlSecondsAfterFinished) | .spec.template.metadata.labels.perfbench = "1"
      else . end;
    if .kind == "List" then .items |= map(fix) else fix end' <<<"$json" > "$PB_RUN/jobs/$name.json" || return 1
  K -n "$ns" apply -f "$PB_RUN/jobs/$name.json" >/dev/null
}
# pb_job_state <ns> <job>: prints "<pod> <phase> <exitCode|-> <startedAt|->" for the newest pod
pb_job_state() {
  K -n "$1" get pods -l "job-name=$2" -o json 2>/dev/null | jq -r '
    [.items[]] | sort_by(.metadata.creationTimestamp) | last
    | if . == null then "none Pending - -" else
      "\(.metadata.name) \(.status.phase) \(([.status.containerStatuses[]?.state.terminated.exitCode] | map(select(. != null)) | max) // "-") \(([.status.containerStatuses[]?.state.running.startedAt, .status.containerStatuses[]?.state.terminated.startedAt] | map(select(. != null)) | min) // "-")"
      end' 2>/dev/null || echo "none Unknown - -"
}
pb_job_wait_started() { # ns job timeout_s -> 0 once the pod runs (or already finished)
  local end=$((EPOCHSECONDS + $3)) phase
  while :; do
    read -r _ phase _ _ <<<"$(pb_job_state "$1" "$2")"
    case $phase in Running|Succeeded|Failed) return 0 ;; esac
    [ "$EPOCHSECONDS" -lt "$end" ] || return 1
    sleep 1
  done
}
pb_job_finished() { # ns job -> 0 when the pod has terminated
  local phase
  read -r _ phase _ _ <<<"$(pb_job_state "$1" "$2")"
  case $phase in Succeeded|Failed) return 0 ;; *) return 1 ;; esac
}
pb_job_wait_finished() { # ns job timeout_s poll_s
  local end=$((EPOCHSECONDS + $3))
  while ! pb_job_finished "$1" "$2"; do
    [ "$EPOCHSECONDS" -lt "$end" ] || return 1
    sleep "$4"
  done
}
pb_job_logs() { K -n "$1" logs "job/$2" --all-containers=true --tail=-1 > "$3" 2>&1; }

# ---- conntrack and metrics snapshots ------------------------------------------------------------
# Kernel 6.12 never increments the nf_conntrack "insert" counter (it stays 0; seen in the pilot on
# 2026-10-02), so flows are also counted from the pods' own TCP counters: the sum of ActiveOpens
# and PassiveOpens in /proc/<pid>/net/snmp over every pod network namespace on the node (one
# pause process per pod; host-network pods and duplicates skipped). PassiveOpens = connections
# the node's pods accepted, so a pod-to-pod connection counts once, at its server. One
# "# podnet_ns <netns> <active> <passive>" line per pod netns lets the analysis count only the
# namespaces present in both snapshots (a pod that goes away would otherwise drop its counters).
# shellcheck disable=SC2016  # runs on the node
PB_PODNET_SH='h=$(readlink /proc/1/ns/net); seen=" "; a=0; p=0; n=0
for pid in $(pgrep -x pause); do
  ns=$(readlink /proc/$pid/ns/net 2>/dev/null) || continue
  [ "$ns" = "$h" ] && continue
  case $seen in *" $ns "*) continue ;; esac
  seen="$seen$ns "
  set -- $(awk "/^Tcp: [0-9]/ {print \$6, \$7; exit}" /proc/$pid/net/snmp 2>/dev/null)
  [ $# -eq 2 ] || continue
  a=$((a + $1)); p=$((p + $2)); n=$((n + 1))
  echo "# podnet_ns ${ns#net:} $1 $2"
done
echo "# podnet_tcp active_opens=$a passive_opens=$p netns=$n"'
# pb_ct_snap <label>: /proc/net/stat/nf_conntrack (+ conntrack -S) and the pod-netns TCP open
# counters of every node -> ct/<label>.<node>.txt
pb_ct_snap() {
  local n pids=()
  for n in $PB_NODES; do
    pb_on "$n" 'echo "# ts=$(date +%s.%N)"; cat /proc/net/stat/nf_conntrack 2>/dev/null; echo "# count=$(cat /proc/sys/net/netfilter/nf_conntrack_count 2>/dev/null)"; echo "# conntrack -S"; conntrack -S 2>/dev/null; '"$PB_PODNET_SH"'; true' \
      > "$PB_RUN/ct/$1.$n.txt" 2>&1 &
    pids+=("$!")
  done
  wait "${pids[@]}"
  return 0
}
# pb_metrics_scrape <label>: cilium agent :9962 (filtered) and hubble :9965 of every node
pb_metrics_scrape() {
  local n ip pids=()
  for n in $PB_NODES; do
    ip=$(pb_addr "$n")
    { echo "# ts=$(pb_now)"; curl -s -m 8 "http://$ip:9962/metrics" | grep -E "$PB_CILIUM_METRIC_RE"; } \
      > "$PB_RUN/metrics/$1.$n.cilium.prom" 2>/dev/null &
    pids+=("$!")
    { echo "# ts=$(pb_now)"; curl -s -m 8 "http://$ip:9965/metrics" | grep -E '^hubble_'; } \
      > "$PB_RUN/metrics/$1.$n.hubble.prom" 2>/dev/null &
    pids+=("$!")
  done
  wait "${pids[@]}"
  return 0
}

# pb_scrape_loop_cmd: the command of the pb-scrape client. Every 15 s it fetches the cilium agent
# (:9962), operator (:9963) and hubble (:9965, only while Hubble is on) metrics of every node and
# throws the body away, like the kube-prometheus-stack scrapes on test-cluster (15 s interval,
# ServiceMonitors for 9962/9965 from the 2026-07-27 patch). It runs in every condition and is
# counted as harness; what it adds to the observers is their exposition cost.
pb_scrape_loop_cmd() {
  local ips="" n
  for n in $PB_NODES; do ips+="$(pb_addr "$n") "; done
  printf '%s' "while :; do t=\$(date +%s); for ip in $ips; do for p in 9962 9963 9965; do b=\$(curl -s -m 5 -o /dev/null -w '%{size_download}' http://\$ip:\$p/metrics 2>/dev/null || echo 0); echo \"\$t \$ip \$p \$b\"; done; done; s=\$((15 - (\$(date +%s) - t))); [ \$s -gt 0 ] && sleep \$s; done"
}

# ---- otterize -----------------------------------------------------------------------------------
pb_otterize_query() { # out-file scope-name
  local ip
  ip=$(K -n otterize-system get svc otterize-network-mapper -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
  [ -n "$ip" ] || { pb_warn "otterize mapper service not found"; return 1; }
  pb_oneshot "$2" "$1" 30 curl -sS -m 20 -X POST "http://$ip:9090/query" \
    -H 'Content-Type: application/json' \
    -d '{"query":"{ serviceIntents { client { name namespace } intents { name namespace } } }"}'
}

# ---- host identity and kernel facts --------------------------------------------------------------
# pb_hostinfo <out.json>: per node boot_id, machine-id, CPU model/MHz, CPU vulnerabilities, kernel
# command line (random seed removed), kernel config switches that decide where BPF and IRQ time is
# accounted, and the play id (PB_PLAY_ID, or /opt/perfbench/PLAY_ID written at upload time).
# analyze.py uses it to refuse pooling runs of one rep from different hosts.
# shellcheck disable=SC2016  # runs on the node
PB_HOSTINFO_SH='python3 - <<"PY"
import glob, gzip, json, os, re
def rd(p, d=""):
    try:
        return open(p).read().strip()
    except OSError:
        return d
cpu = rd("/proc/cpuinfo")
model = re.search(r"^model name\s*:\s*(.*)$", cpu, re.M)
mhz = re.findall(r"^cpu MHz\s*:\s*([\d.]+)$", cpu, re.M)
kc = {}
cfg = ""
try:
    cfg = gzip.open("/proc/config.gz", "rt").read()
except OSError:
    cfg = rd("/boot/config-" + os.uname().release)
for k in ("CONFIG_IRQ_TIME_ACCOUNTING", "CONFIG_VIRT_CPU_ACCOUNTING_GEN", "CONFIG_TICK_CPU_ACCOUNTING",
          "CONFIG_PREEMPT", "CONFIG_PREEMPT_VOLUNTARY", "CONFIG_PREEMPT_NONE", "CONFIG_PREEMPT_DYNAMIC",
          "CONFIG_HZ", "CONFIG_NO_HZ_FULL", "CONFIG_BPF_JIT_ALWAYS_ON", "CONFIG_DEBUG_INFO_BTF"):
    m = re.search(r"^" + k + r"=(.*)$", cfg, re.M)
    kc[k] = m.group(1) if m else None
vul = {os.path.basename(f): rd(f) for f in sorted(glob.glob("/sys/devices/system/cpu/vulnerabilities/*"))}
print(json.dumps({"hostname": os.uname().nodename, "kernel": os.uname().release,
    "boot_id": rd("/proc/sys/kernel/random/boot_id"), "machine_id": rd("/etc/machine-id"),
    "cpu_model": model.group(1) if model else None,
    "cpu_mhz": [float(x) for x in mhz], "ncpu": os.cpu_count(),
    "cmdline": re.sub(r"systemd\.random_seed=\S+\s*", "", rd("/proc/cmdline")),
    "kconfig": kc, "vulnerabilities": vul,
    "steal_jiffies": int(rd("/proc/stat").splitlines()[0].split()[8])}))
PY'
pb_hostinfo() {
  local n play=${PB_PLAY_ID:-} out=$1 tmp
  [ -n "$play" ] || play=$(cat "$PB_ROOT/PLAY_ID" 2>/dev/null || true)
  tmp=$(mktemp)
  for n in $PB_NODES; do
    printf '%s\t%s\n' "$n" "$(pb_on "$n" "$PB_HOSTINFO_SH" 2>/dev/null | tail -1)" >> "$tmp"
  done
  python3 - "$tmp" "$play" > "$out" <<'PY'
import json, sys
nodes = {}
for line in open(sys.argv[1]):
    n, _, j = line.rstrip("\n").partition("\t")
    try:
        nodes[n] = json.loads(j)
    except ValueError:
        nodes[n] = {"error": "no host info"}
print(json.dumps({"play_id": sys.argv[2] or None, "nodes": nodes}))
PY
  rm -f "$tmp"
}

# ---- BPF programs and observer ports --------------------------------------------------------------
# pb_bpf_state <out.json>: BPF programs on every node (bpftool in the node's cilium-agent container,
# which sees the host's programs) and which observer ports listen.
# Tracing types are kprobe, tracepoint, raw_tracepoint and perf_event ("tracing" also holds the
# kernel's own bpf iterators, so it is reported but not judged). The IG gadget pods load a standing
# set while the DaemonSet runs, with no gadget active (container collection: ig_execve_e/_x,
# ig_sched_exec, ig_fa_pick_e/_x); "gadget_progs" counts every other tracing program, i.e. a
# running (or leftover) gadget such as trace_tcp.
pb_bpf_state() {
  local out=$1 n pod tmp
  tmp=$(mktemp)
  for n in $PB_NODES; do
    pod=$(K -n kube-system get pods -l k8s-app=cilium --field-selector "spec.nodeName=$n" -o name 2>/dev/null | head -1)
    {
      printf '%s\t' "$n"
      if [ -n "$pod" ]; then
        K -n kube-system exec "$pod" -c cilium-agent -- bpftool prog list -j 2>/dev/null \
          | jq -cj '[.[] | {type, name: (.name // "")}]' 2>/dev/null || printf '[]'
      else printf '[]'; fi
      printf '\t%s\n' "$(pb_on "$n" "ss -ltnH 2>/dev/null | awk '{print \$4}' | grep -oE ':(4244|4245|9962|9963|9965|9090|8080)\$' | sort -u | tr -d ':' | tr '\n' ' '" 2>/dev/null)"
    } >> "$tmp"
  done
  python3 - "$tmp" > "$out" <<'PY'
import json, sys
TR = ("kprobe", "tracepoint", "raw_tracepoint", "perf_event")
STANDING = ("ig_execve_e", "ig_execve_x", "ig_sched_exec", "ig_fa_pick_e", "ig_fa_pick_x")
nodes, tracing, gadget = {}, 0, 0
for line in open(sys.argv[1]):
    n, progs, ports = (line.rstrip("\n").split("\t") + ["", ""])[:3]
    try:
        p = json.loads(progs or "[]")
    except ValueError:
        p = []
    if not isinstance(p, list):
        p = []
    by_type = {}
    for x in p:
        by_type[x.get("type")] = by_type.get(x.get("type"), 0) + 1
    tr = [x for x in p if x.get("type") in TR]
    gd = sorted({x.get("name", "") for x in tr if not str(x.get("name", "")).startswith(STANDING)})
    t = len(tr)
    g = sum(1 for x in tr if not str(x.get("name", "")).startswith(STANDING))
    tracing += t
    gadget += g
    nodes[n] = {"progs": by_type, "tracing_progs": t, "gadget_progs": g, "gadget_prog_names": gd,
                "standing_ig_progs": t - g, "ports": [int(x) for x in ports.split()]}
print(json.dumps({"tracing_progs_total": tracing, "gadget_progs_total": gadget, "nodes": nodes}))
PY
  rm -f "$tmp"
}

# ---- matrix helpers ---------------------------------------------------------------------------------
# pb_run_done <run-dir> <short 0|1> [profile]: DONE exists and was made in the same mode (a
# --short run does not count as done for a full matrix, and the other way round). With a profile
# (full, short, cycle) meta.json's profile must match too; runs made before profiles existed
# count as "short" or "full" by their short flag.
pb_run_done() {
  [ -f "$1/DONE" ] || return 1
  local want=false; [ "$2" = 1 ] && want=true
  [ "$(jq -r '.short' "$1/meta.json" 2>/dev/null)" = "$want" ] || return 1
  [ -z "${3:-}" ] || [ "$(jq -r '.profile // (if .short then "short" else "full" end)' "$1/meta.json" 2>/dev/null)" = "$3" ]
}
# pb_williams <app> <cycle> <cond>...: prints "<seed> <design> <sequence> <cond> <cond> ..."
# All 5 conditions: a Williams design (Williams 1949) for 5 treatments, 10 sequences. Over the
# 10 sequences every condition takes every position exactly twice and every ordered pair of
# different conditions is adjacent exactly twice (first-order carry-over balance); no condition
# follows itself. Treatment t is condition t of the canonical order baseline hubble otterize
# ig_tcp ig_snap. Cycles 1-10 use the 10 sequences in the order of a shuffle seeded with
# sha256("<app>:williams:1"); cycles 11-20 use the same set in a fresh order seeded with
# sha256("<app>:williams:2"), and so on. So a cycle's order depends only on app and cycle, and a
# matrix split over plays runs the same orders. Only complete sets of 10 cycles are fully balanced.
# Other condition sets: a shuffle seeded with sha256("<app>:cycle<k>"), sequence "-".
pb_williams() {
  python3 - "$@" <<'PY'
import hashlib, random, sys
app, k, conds = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ALL = ["baseline", "hubble", "otterize", "ig_tcp", "ig_snap"]
def williams(n):
    first, lo, hi = [0], 1, n - 1
    while len(first) < n:
        if len(first) % 2:
            first.append(lo); lo += 1
        else:
            first.append(hi); hi -= 1
    rows = [[(x + i) % n for x in first] for i in range(n)]
    return rows + [r[::-1] for r in rows] if n % 2 else rows
if sorted(conds) == sorted(ALL) and k >= 1:
    rows = williams(len(ALL))
    block = (k - 1) // len(rows) + 1
    seed = int(hashlib.sha256(f"{app}:williams:{block}".encode()).hexdigest()[:8], 16)
    perm = list(range(len(rows)))
    random.Random(seed).shuffle(perm)
    seq = perm[(k - 1) % len(rows)]
    print(seed, "williams", seq, *[ALL[t] for t in rows[seq]])
elif 2 <= len(conds) <= 3 and k >= 1:
    # few conditions: all n! orders form one complete block (6 cycles for 3 conditions, 2 for 2), each
    # block in a seeded shuffled order; a cycle's order depends only on app and cycle
    import itertools
    perms = list(itertools.permutations(sorted(conds)))
    block = (k - 1) // len(perms) + 1
    seed = int(hashlib.sha256(f"{app}:perm:{block}".encode()).hexdigest()[:8], 16)
    perm = list(range(len(perms)))
    random.Random(seed).shuffle(perm)
    seq = perm[(k - 1) % len(perms)]
    print(seed, "permutations", seq, *perms[seq])
else:
    seed = int(hashlib.sha256(f"{app}:cycle{k}".encode()).hexdigest()[:8], 16)
    order = list(conds)
    random.Random(seed).shuffle(order)
    print(seed, "shuffle", "-", *order)
PY
}
# pb_shuffle <app> <rep> <cond>...: prints "<seed> <design> <cond> <cond> ..."
# All 5 conditions, reps 1-3: a balanced design. Three fixed rows of a 5x5 position design in
# which every condition takes three different positions, the mean position of every condition
# is 3 +- 1/3 (1-based), and no condition directly follows the same condition twice. Baseline
# sits in the column with positions 2, 4, 3. The other four conditions are assigned to the other
# columns by a shuffle seeded with sha256("<app>"), so each app gets its own assignment and a
# rep's order depends only on app and rep (a matrix split over two plays runs the same orders).
# Other condition sets or reps > 3: the old seeded shuffle, seed sha256("<app>:rep<r>").
pb_shuffle() {
  python3 - "$@" <<'PY'
import hashlib, random, sys
app, rep, conds = sys.argv[1], int(sys.argv[2]), sys.argv[3:]
ALL = ["baseline", "hubble", "otterize", "ig_tcp", "ig_snap"]
# ROWS[r][col] = 0-based position of column col in rep r+1
ROWS = [(0, 1, 2, 3, 4), (1, 3, 4, 2, 0), (4, 2, 1, 0, 3)]
if sorted(conds) == sorted(ALL) and 1 <= rep <= len(ROWS):
    seed = int(hashlib.sha256(app.encode()).hexdigest()[:8], 16)
    others = [c for c in ALL if c != "baseline"]
    random.Random(seed).shuffle(others)
    cols = [others[0], "baseline"] + others[1:]
    order = [None] * 5
    for col, pos in enumerate(ROWS[rep - 1]):
        order[pos] = cols[col]
    print(seed, "balanced", *order)
else:
    seed = int(hashlib.sha256(f"{app}:rep{rep}".encode()).hexdigest()[:8], 16)
    order = list(conds)
    random.Random(seed).shuffle(order)
    print(seed, "shuffle", *order)
PY
}
