#!/usr/bin/env python3
"""check.py <work_dir>: checks what tests/mockcluster/drive.sh left in <work_dir>/results.

- cycle matrix (--cycles 2): 10 runs DONE in cycle<k>/<cond>/, profile cycle, TP_N = TP_N_CYCLE,
  one fixed-count test per mode, a Williams order per cycle in ORDER.json that matches
  bin/lib.sh pb_williams, canary-<node>.csv.gz (+ info.json) from every node, the remote ones
  fetched; STATUS.json with layout, cycle_list, cycles_total, cycles_done
- the second --cycles 2 call skipped all 10 runs (resume)
- rep matrix (old interface): rep1/<cond>/ DONE, profile full, STATUS without cycle fields
- run_one --short with PB_CANARY=0: DONE, no canary files
- bad argument combinations exit 2
- drift probe: tests.jsonl, timeline.csv with a canary speed per test, summary.json
- nothing left behind: lock free, no canary or sampler processes
- analyze.py on the tree: rep report + cycles report with the canary sections
Exit 0 = all checks passed.
"""
import csv
import glob
import gzip
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CONDS = ["baseline", "hubble", "otterize", "ig_tcp", "ig_snap"]
NODES = ["cp-01", "worker-01", "worker-02"]


def main():
    work = sys.argv[1]
    res = os.path.join(work, "results")
    app = os.path.join(res, "mockapp")
    errs = []

    def need(cond, msg):
        if not cond:
            errs.append(msg)
    drive = open(os.path.join(res, "DRIVE.log")).read()
    need("ALLDONE" in drive, "drive.sh did not finish")
    rcs = [ln.split("rc=")[-1].strip() for ln in drive.splitlines() if "rc=" in ln]
    need(rcs[:4] == ["0", "0", "0", "0"], f"matrix/run_one exit codes {rcs[:4]} (want 0 0 0 0)")
    need(rcs[4:7] == ["2", "2", "2"], f"bad-argument exit codes {rcs[4:7]} (want 2 2 2)")
    need(rcs[7:8] == ["0"], f"drift probe exit code {rcs[7:8]}")
    need("lock free? yes; canary procs: 0; sampler procs: 0" in drive, "leftovers: " + drive.splitlines()[-2])

    # ---- cycle matrix
    lib = os.path.join(ROOT, "bin", "lib.sh")
    for k in (1, 2):
        o = json.load(open(os.path.join(app, f"cycle{k}", "ORDER.json")))
        want = subprocess.run(["bash", "-c", f". '{lib}'; pb_williams mockapp {k} {' '.join(CONDS)}"],
                              capture_output=True, text=True).stdout.split()
        need(o.get("design") == "williams" and o.get("order") == want[3:] and str(o.get("sequence")) == want[2],
             f"cycle{k} ORDER.json {o} != pb_williams {want}")
        for pos, c in enumerate(o["order"], 1):
            d = os.path.join(app, f"cycle{k}", c)
            need(os.path.exists(os.path.join(d, "DONE")), f"cycle{k}/{c} not DONE")
            m = json.load(open(os.path.join(d, "meta.json")))
            p = m["params"]
            need(m.get("profile") == "cycle" and m.get("layout") == "cycle" and m.get("cycle") == k,
                 f"cycle{k}/{c} meta profile/layout/cycle {m.get('profile')} {m.get('layout')} {m.get('cycle')}")
            need(p["tp_n"] == 1504 and p["tp_reps"] == 1 and p["warmup_s"] == 5 and p["steady_s"] == 60,
                 f"cycle{k}/{c} params {p}")
            need(str(p.get("order_pos")) == str(pos) and p.get("order_design") == "williams" and p.get("canary"),
                 f"cycle{k}/{c} order params {p}")
            need(len(m["tp_tests"]) == 2 and all(t["ok"] for t in m["tp_tests"]), f"cycle{k}/{c} tests {m['tp_tests']}")
            # the mock loads no BPF programs (ig_tcp's end-of-run gadget check warns) and has no
            # Otterize mapper to query
            mock_ok = ("ig_tcp: no gadget BPF programs", "otterize t0 query failed", "otterize t1 query failed")
            wn = [w for w in m.get("warnings") or [] if not w.startswith(mock_ok)]
            need(not wn, f"cycle{k}/{c} warnings {wn}")
            for n in NODES:
                f = os.path.join(d, f"canary-{n}.csv.gz")
                need(os.path.exists(f) and os.path.exists(os.path.join(d, f"canary-{n}.csv.info.json")),
                     f"cycle{k}/{c}: canary files of {n} missing")
                if os.path.exists(f):
                    rows = list(csv.DictReader(gzip.open(f, "rt")))
                    need(len(rows) >= 30 and rows[0]["node"] == n, f"cycle{k}/{c}: {len(rows)} canary rows from {n}")
                info = json.load(open(os.path.join(d, f"canary-{n}.csv.info.json")))
                need(info.get("end_ts") and info.get("own_cpu_pct_of_core") is not None,
                     f"cycle{k}/{c}: canary on {n} did not stop cleanly: {info}")
            need(not glob.glob(os.path.join(d, "canary-*.err")), f"cycle{k}/{c}: canary stderr left")
            dn = json.load(open(os.path.join(d, "DONE")))
            need(dn.get("layout") == "cycle" and dn.get("profile") == "cycle", f"cycle{k}/{c} DONE {dn}")
    need(not glob.glob("/var/tmp/perfbench/*") if os.path.isdir("/var/tmp/perfbench") else True,
         "remote temp files left")
    st = json.load(open(os.path.join(res, "STATUS.cycles.json")))
    need(st.get("layout") == "cycle" and st.get("cycle_list") == [1, 2] and st.get("cycles_total") == 2
         and st.get("cycles_done") == 2 and st.get("done_runs") == 10 and st.get("total_runs") == 10
         and st.get("rep_list") == [] and st.get("stage") == "finished" and st.get("current_cycle") is None,
         f"STATUS.cycles.json {st}")
    prog = open(os.path.join(app, "PROGRESS.log")).read()
    need(prog.count("SKIP (DONE)") == 10, f"resume: {prog.count('SKIP (DONE)')} SKIP lines, want 10")

    # ---- rep matrix and the --short run (old interfaces)
    for c in ("baseline", "hubble"):
        d = os.path.join(app, "rep1", c)
        m = json.load(open(os.path.join(d, "meta.json")))
        need(os.path.exists(os.path.join(d, "DONE")) and m.get("profile") == "full" and m.get("layout") == "rep"
             and m["params"]["steady_s"] == 60 and m["params"]["tp_n"] == 800, f"rep1/{c}: {m.get('profile')} {m['params']}")
    st = json.load(open(os.path.join(res, "STATUS.rep.json")))
    need(st.get("rep_list") == [1] and st.get("layout") == "rep" and "cycle_list" not in st and st.get("done_runs") == 2,
         f"STATUS.rep.json {st}")
    d = os.path.join(app, "rep2", "ig_snap")
    m = json.load(open(os.path.join(d, "meta.json")))
    need(os.path.exists(os.path.join(d, "DONE")) and m.get("short") is True and m.get("profile") == "short"
         and not glob.glob(os.path.join(d, "canary-*")) and m["params"].get("canary") is False,
         f"--short run without canary: {m.get('profile')} {glob.glob(os.path.join(d, 'canary-*'))}")

    # ---- drift probe
    pd = os.path.join(res, "_drift", "probe1")
    tests = [json.loads(x) for x in open(os.path.join(pd, "tests.jsonl"))]
    need(len(tests) >= 5 and all(t["ok"] for t in tests), f"drift probe tests {len(tests)}")
    tl = list(csv.DictReader(open(os.path.join(pd, "timeline.csv"))))
    need(len(tl) == len(tests) and all(r["speed_cpu_workers"] and r["test_s"] for r in tl),
         f"timeline.csv rows {tl[:2]}")
    need(all(abs(float(r["start_epoch"]) - t["start"]) < 0.01 for r, t in zip(tl, tests)),
         f"timeline.csv start_epoch lost precision: {[r['start_epoch'] for r in tl[:2]]}")
    sm = json.load(open(os.path.join(pd, "summary.json")))
    need(sm.get("tests_ok") == len(tests) and sm.get("canary_nodes") == NODES and sm.get("load_vs_pause_speed_median"),
         f"summary.json {sm}")
    need(not os.path.exists(os.path.join(pd, ".live")), "drift probe left .live/")
    need(all(os.path.exists(os.path.join(pd, f"canary-{n}.csv")) for n in NODES), "drift probe canary files missing")
    need(json.load(open(os.path.join(pd, "probe.json"))).get("tp_n") == 2000, "drift probe tp_n != 2000")

    # ---- analysis
    out = os.path.join(work, "analysis")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "analyze", "analyze.py"), res, "--out", out],
                       capture_output=True, text=True)
    need(r.returncode == 0, f"analyze.py rc {r.returncode}: {r.stderr[-500:]}")
    for fn in ("RESULTS-PERF.md", "canary_segments.csv", "paired_deltas.csv", "cycles/RESULTS-CYCLES.md",
               "cycles/paired_deltas.csv", "cycles/drift_per_block.csv", "cycles/canary_segments.csv",
               "cycles/table5_fixed_count_normalised.csv"):
        need(os.path.exists(os.path.join(out, fn)), f"analysis/{fn} missing")
    if os.path.exists(os.path.join(out, "cycles", "runs.csv")):
        rows = list(csv.DictReader(open(os.path.join(out, "cycles", "runs.csv"))))
        need(len(rows) == 10 and not any(x["excluded"] == "True" for x in rows),
             f"cycles/runs.csv: {[(x['rep'], x['cond'], x['reason']) for x in rows if x['excluded'] == 'True']}")
        need(all(x.get("canary.steady.speed_cpu.workers") for x in rows), "cycle runs without a canary speed")
    if errs:
        print("FAILED checks:")
        for e in errs:
            print("  -", e)
        return 1
    print(f"mockcluster check OK ({work})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
