#!/usr/bin/env bash
# tests/mockcluster/run.sh [work_dir]
#
# End-to-end test of the shell harness on the laptop (needs Docker; about 30 minutes). Builds an
# Ubuntu 24.04 image (bash 5, Python 3.12, jq, flock, timeout: as on the bench nodes), mounts the
# harness read-only and runs drive.sh: the real run_matrix.sh, run_one.sh, drift_probe.sh,
# sampler.py and canary.py against mock kubectl/systemd-run/systemctl/ssh/scp, then check.py.
# The results stay in work_dir (default: a new temp dir). Exit 0 = all checks passed.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ROOT=$(cd "$HERE/../.." && pwd)
WORK=${1:-$(mktemp -d "${TMPDIR:-/tmp}/pb-mockcluster.XXXXXX")}
mkdir -p "$WORK"
[ -z "$(ls -A "$WORK")" ] || { echo "run.sh: $WORK is not empty" >&2; exit 2; }
WORK=$(cd "$WORK" && pwd)
docker build -q -t pbtest:24.04 "$HERE" >/dev/null
echo "mockcluster: results in $WORK" >&2
docker run --rm --init -v "$ROOT":/opt/perfbench-src:ro -v "$WORK":/work pbtest:24.04 \
  bash /opt/perfbench-src/tests/mockcluster/drive.sh
