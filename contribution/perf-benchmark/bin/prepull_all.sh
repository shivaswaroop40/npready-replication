#!/usr/bin/env bash
# prepull_all.sh [app ...]: pull every image the apps need before any run, so no run pays a pull.
#   workers: every line of apps/<app>/images.txt (app pods, init jobs, generators)
#   cp-01:   the images of steady.yaml and throughput.yaml (the Jobs are pinned to cp-01)
# Idempotent: images already present are skipped. Three tries per image, 20 s apart.
# Per-node logs and a summary (image count, total size, containerd disk use, free disk) go to
# results/_prepull/. Writes results/_prepull/DONE at the end. Runs on cp-01 as root.
# Start it detached:
#   setsid nohup bash /opt/perfbench/bin/prepull_all.sh > /opt/perfbench/results/_prepull.out 2>&1 < /dev/null &
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
export PB_ROOT=${PB_ROOT:-$(dirname "$HERE")}
# shellcheck source=lib.sh source-path=SCRIPTDIR
. "$HERE/lib.sh"

APPS=${*:-boutique bank dsb otel teastore}
OUT=$PB_RESULTS/_prepull
mkdir -p "$OUT"
rm -f "$OUT/DONE"
pb_resolve_nodes

WORKER_IMGS=$(for a in $APPS; do grep -vE '^[[:space:]]*(#|$)' "$PB_APPS/$a/images.txt" | awk '{print $1}'; done | sort -u)
CP_IMGS=$(for a in $APPS; do grep -hE '^[[:space:]]*image:' "$PB_APPS/$a/steady.yaml" "$PB_APPS/$a/throughput.yaml" | awk '{print $2}'; done | sort -u)

# shellcheck disable=SC2016  # runs on the node
PULL='n=0; while read -r i; do
  [ -n "$i" ] || continue
  if k3s crictl inspecti "$i" >/dev/null 2>&1; then echo "have $i"; continue; fi
  t0=$(date +%s); ok=0
  for try in 1 2 3; do
    if k3s crictl pull "$i" >/dev/null 2>/tmp/pb-pull.err; then ok=1; break; fi
    echo "try $try failed $i: $(tr "\n" " " < /tmp/pb-pull.err | tail -c 300)"; sleep 20
  done
  if [ $ok = 1 ]; then echo "pulled $i in $(( $(date +%s) - t0 ))s"; else echo "PULL FAILED $i"; fi
done
echo "# summary"
k3s crictl images -o json | python3 -c "import json,sys; im=json.load(sys.stdin)[\"images\"]; print(\"images\", len(im), \"total_size_GiB\", round(sum(int(x[\"size\"]) for x in im)/2**30, 2))"
echo "containerd_disk $(du -sh /var/lib/rancher/k3s/agent/containerd 2>/dev/null | cut -f1)"
echo "rootfs $(df -h / | tail -1)"'

pids=()
for n in $PB_NODES; do
  if pb_is_local "$n"; then list=$CP_IMGS; else list=$WORKER_IMGS; fi
  printf '%s\n' "$list" | pb_on_in "$n" "$PULL" > "$OUT/$n.log" 2>&1 &
  pids+=("$!")
done
wait "${pids[@]}"
{
  for n in $PB_NODES; do
    echo "== $n: $(grep -c '^pulled ' "$OUT/$n.log") pulled, $(grep -c '^have ' "$OUT/$n.log") present, $(grep -c '^PULL FAILED' "$OUT/$n.log") failed"
    sed -n '/^# summary/,$p' "$OUT/$n.log" | tail -n +2
    grep '^PULL FAILED' "$OUT/$n.log"
  done
} > "$OUT/summary.txt"
cat "$OUT/summary.txt"
date -u +%FT%TZ > "$OUT/DONE"
