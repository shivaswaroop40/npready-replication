#!/bin/bash
# tests/mockcluster/drive.sh: runs inside the pbtest:24.04 container (see run.sh). It wires the
# real harness (mounted read-only at /opt/perfbench-src) to the mocks in this directory and runs:
# a 2-cycle interleaved matrix, the same again (resume: all runs SKIP), a rep matrix (old
# interface), run_one --short with the canary off, three bad argument combinations, a 2-minute
# drift probe; then check.py checks the results and analyses them. The mock kubectl serves Jobs
# (steady: locust stats; fixed-count: hey output at 400 req/s), ssh/scp run "remote" nodes
# worker-01/02 in this container on their own temp paths, systemd-run/systemctl track scopes and
# services per node. cond.sh is a stub. Samplers and canaries are the real ones.
set -u
SRC=/opt/perfbench-src
MOCK=$SRC/tests/mockcluster
mkdir -p /work/bin /work/results /run/mock
for f in "$SRC"/bin/*; do [ "$(basename "$f")" = cond.sh ] || ln -sf "$f" /work/bin/; done
cp "$MOCK/cond.sh" /work/bin/cond.sh
ln -sfn "$SRC/analyze" /work/analyze
mkdir -p /work/apps && cp -r "$MOCK/apps/mockapp" /work/apps/
export PATH=$MOCK/bin:$PATH PB_RESULTS=/work/results PB_APPS=/work/apps PB_LOCK=/run/perfbench.lock
export PB_IDLE_S=6 PB_WARMUP_S=5 PB_STEADY_S=60 PB_TP_PAUSE_S=2 PB_SNAP_LEAD_S=20 PB_PLAY_ID=000000000000000000000000
export PYTHONDONTWRITEBYTECODE=1
step() { echo "[$(date -u +%T)] $*" | tee -a /work/results/DRIVE.log; }
step "cycle matrix --cycles 2"
bash /work/bin/run_matrix.sh mockapp --cycles 2 --keep > /work/results/cyc.out 2>&1; step "rc=$?"
cp /work/results/STATUS.json /work/results/STATUS.cycles.json
step "cycle matrix again (resume: all SKIP)"
bash /work/bin/run_matrix.sh mockapp --cycles 2 --keep > /work/results/cyc2.out 2>&1; step "rc=$?"
step "rep matrix --rep-list 1, 2 conds (old interface)"
PB_TP_REPS=1 PB_TP_N=800 bash /work/bin/run_matrix.sh mockapp --rep-list 1 --conds "baseline hubble" --keep > /work/results/rep.out 2>&1; step "rc=$?"
cp /work/results/STATUS.json /work/results/STATUS.rep.json
step "run_one --short (old interface), canary off"
PB_CANARY=0 bash /work/bin/run_one.sh mockapp ig_snap 2 --short > /work/results/short.out 2>&1; step "rc=$?"
step "bad args"
bash /work/bin/run_matrix.sh mockapp --cycles 2 --short > /work/results/bad1.out 2>&1; step "cycles+short rc=$?"
bash /work/bin/run_matrix.sh mockapp --cycles 2 --rep-list 1 > /work/results/bad2.out 2>&1; step "cycles+rep-list rc=$?"
bash /work/bin/run_one.sh mockapp baseline 1 --short --profile cycle > /work/results/bad3.out 2>&1; step "short+profile cycle rc=$?"
step "drift probe 2 min, a test every 20 s"
bash /work/bin/drift_probe.sh mockapp 2 20 --cond baseline --out /work/results/_drift/probe1 > /work/results/drift.out 2>&1; step "rc=$?"
step "leftovers: lock free? $(flock -n /run/perfbench.lock true && echo yes || echo NO); canary procs: $(pgrep -fc canary.py); sampler procs: $(pgrep -fc sampler.py)"
echo ALLDONE >> /work/results/DRIVE.log
python3 "$MOCK/check.py" /work
