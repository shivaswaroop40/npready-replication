#!/usr/bin/env bash
# collect.sh <play-id> <dest-dir> [--with-raw] [--machine cp-01] [--user root] [app ...]
#
# Laptop side. Pulls /opt/perfbench/results from the play's cp-01 into <dest-dir>/results
# (via one tarball: labctl ssh + labctl cp), then prints DONE/FAILED counts per app.
# By default it leaves out the raw client streams (hubble.json*, ig_tcp.json*) and old
# attempt dirs (<cond>.attempt-*): the analysis does not need them and they are large.
# --with-raw pulls everything. Then run:
#   python3 analyze/analyze.py <dest-dir>/results
# If root login is refused, pass --user laborant (the tar then runs under sudo).
set -euo pipefail

# Play 6abf7d3feb9990eadd5f4488 (k8s-omni) belongs to another agent's tutorial. Never touch it.
FORBIDDEN_PLAYS="6abf7d3feb9990eadd5f4488"

usage() { sed -n '2,2p' "$0" | sed 's/^# //' >&2; exit 2; }
[ $# -ge 2 ] || usage
PLAY=$1 DEST=$2; shift 2
RAW=0 MACHINE=cp-01 USER_=root APPS=()
while [ $# -gt 0 ]; do
  case $1 in
    --with-raw) RAW=1 ;;
    --machine) MACHINE=$2; shift ;;
    --user) USER_=$2; shift ;;
    -*) usage ;;
    *) APPS+=("$1") ;;
  esac
  shift
done
for f in $FORBIDDEN_PLAYS; do
  [ "$PLAY" != "$f" ] || { echo "collect.sh: refusing to touch play $PLAY (not ours)" >&2; exit 1; }
done
[[ $PLAY =~ ^[0-9a-f]{24}$ ]] || { echo "collect.sh: '$PLAY' does not look like a play id" >&2; exit 2; }
LABCTL=${LABCTL:-labctl}
command -v "$LABCTL" >/dev/null || { echo "collect.sh: labctl not found" >&2; exit 1; }

TS=$(date -u +%Y%m%dT%H%M%SZ)
RTGZ=/tmp/perfbench-results-$TS.tgz
SUDO=""; [ "$USER_" = root ] || SUDO="sudo"
paths="results"
if [ ${#APPS[@]} -gt 0 ]; then paths=""; for a in "${APPS[@]}"; do paths+="results/$a "; done; fi
# patterns are single-quoted so the remote shell passes them to tar unexpanded
excl=""
[ "$RAW" = 1 ] || excl="'--exclude=results/*/rep*/*.attempt-*' '--exclude=results/*/cycle*/*.attempt-*' --exclude=hubble.json --exclude=hubble.json.gz --exclude=ig_tcp.json --exclude=ig_tcp.json.gz"

remote="set -e; cd /opt/perfbench; $SUDO tar -czf $RTGZ $excl $paths; $SUDO chmod 644 $RTGZ; ls -l $RTGZ"
echo "collect: packing on $PLAY/$MACHINE: $paths" >&2
"$LABCTL" ssh -m "$MACHINE" -u "$USER_" "$PLAY" -- "$remote"
mkdir -p "$DEST"
LTGZ=$DEST/perfbench-results-$TS.tgz
"$LABCTL" cp -m "$MACHINE" -u "$USER_" "$PLAY:$RTGZ" "$LTGZ"
"$LABCTL" ssh -m "$MACHINE" -u "$USER_" "$PLAY" -- "$SUDO rm -f $RTGZ" || true
tar -xzf "$LTGZ" -C "$DEST"
echo "collect: $(du -h "$LTGZ" | cut -f1) -> $DEST/results (tarball kept at $LTGZ)" >&2

for appdir in "$DEST"/results/*/; do
  [ -d "$appdir" ] || continue
  a=$(basename "$appdir"); [ "$a" = analysis ] && continue
  d=0 f=0 o=0
  for run in "$appdir"rep*/*/ "$appdir"cycle*/*/; do
    [ -d "$run" ] || continue
    case $(basename "$run") in *.attempt-*) continue ;; esac
    if [ -f "$run/DONE" ]; then d=$((d + 1)); elif [ -f "$run/FAILED" ]; then f=$((f + 1)); else o=$((o + 1)); fi
  done
  printf '%-10s DONE %2d  FAILED %2d  incomplete %2d\n' "$a" "$d" "$f" "$o"
done
