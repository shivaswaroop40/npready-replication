#!/usr/bin/env bash
# Build a local staging copy of the public replication package (nothing is pushed).
# Keeps the contribution/... layout that Appendix A's paths assume.
# Leaves out: raw captures (Ankra node names and labels), the platform study (withheld under
# the anonymisation agreement), backups, caches, and the private folder.
# Usage: bash make_replication_staging.sh [DEST]   (default ~/Desktop/code/thesis-replication)
set -euo pipefail
SRC=$(cd "$(dirname "$0")/../.." && pwd)            # MasterThesis/
DEST=${1:-$HOME/Desktop/code/thesis-replication}
mkdir -p "$DEST"
R="rsync -a --delete --exclude=__pycache__ --exclude=*.pyc --exclude=*.bak* --exclude=.DS_Store"

# Held-out applications: derived files only (no captureA/, captureB/, raw drop logs, IP maps).
for app in BOUTIQUE-20260903 BANK-20260904 DSB-SOCIAL-20260904 OTEL-20260906 TEASTORE-20260906; do
  $R --exclude=captureA/ --exclude=captureA2/ --exclude=captureB/ --exclude='enforce-INVALID*/' \
     --exclude=hubble_drops.json --exclude=ipmap.json --exclude='pods*.txt' --exclude=DeathStarBench/ \
     "$SRC/contribution/results/$app/" "$DEST/contribution/results/$app/"
done

# Derived results and analysis the thesis cites.
for d in ATTACK-EXEC-K3S-20261109 HELDOUT-UNIFORM-20261105 TWO-JOURNEY-figures CAPTURE-LATENCY-20261114; do
  $R "$SRC/contribution/results/$d/" "$DEST/contribution/results/$d/"
done
for f in REPRO-FROM-POLICIES-20261028.txt REPRODUCE.md RESULTS-TWO-JOURNEY.md RESULTS-GENERATION.md \
         RESULTS-PERFORMANCE.md; do
  cp "$SRC/contribution/results/$f" "$DEST/contribution/results/$f"
done

# Cost study: combined report and per-block analysis tables (not the raw per-run directories).
mkdir -p "$DEST/contribution/results/PERF-CYCLES-20261003"
$R "$SRC/contribution/results/PERF-CYCLES-20261003/COMBINED/" "$DEST/contribution/results/PERF-CYCLES-20261003/COMBINED/"
cp "$SRC/contribution/results/PERF-CYCLES-20261003/SUMMARY.md" "$DEST/contribution/results/PERF-CYCLES-20261003/" 2>/dev/null || true
for b in "$SRC"/contribution/results/PERF-CYCLES-20261003/*-final; do
  n=$(basename "$b")
  $R "$b/results/analysis/cycles/" "$DEST/contribution/results/PERF-CYCLES-20261003/$n/results/analysis/cycles/"
done
$R --include='*/' --include='*.md' --include='*.csv' --exclude='*' \
   "$SRC/contribution/results/PERF-AGENTONLY-20261005/" "$DEST/contribution/results/PERF-AGENTONLY-20261005/"

# Code: scripts, figure scripts and figures, cost-study harness.
$R --exclude=revalidate_attacks.sh "$SRC/contribution/scripts/" "$DEST/contribution/scripts/"
$R --exclude=thesis_diagrams_platform.py --exclude='*DRAFT*' "$SRC/contribution/figures/" "$DEST/contribution/figures/"
$R --exclude='HANDOVER.md*' --exclude=ops/ "$SRC/contribution/perf-benchmark/" "$DEST/contribution/perf-benchmark/"

# The old test cluster's name is an Ankra-internal identifier; the thesis calls it the test cluster.
grep -rIl "test-cluster" "$DEST" | while read -r f; do sed -i '' 's/test-cluster/test-cluster/g' "$f"; done
cp "$SRC/contribution/scripts/REPLICATION-README.md" "$DEST/README.md"

echo "staged in $DEST: $(find "$DEST" -type f | wc -l | tr -d ' ') files, $(du -sh "$DEST" | cut -f1)"
