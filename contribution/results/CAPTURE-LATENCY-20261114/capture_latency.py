#!/usr/bin/env python3
"""Per-request latency added by each capture method at the capture load.

Reads the stored per-run table runs.csv of every main-study block
(../PERF-CYCLES-20261003/<block>-final/results/analysis/cycles/runs.csv).
For each block, method and cycle, the paired difference is the method's median (p50) request
latency in the 300 s steady window minus the same cycle's baseline. Reports the mean and the
sample SD of the ten paired differences, and the baseline mean and SD.
Descriptive only: latency was not a pre-registered endpoint and is outside the Holm family.
Run: python3 capture_latency.py > output.txt
"""
import csv, glob, json, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "PERF-CYCLES-20261003")
METHODS = ["hubble", "otterize", "ig_tcp", "ig_snap"]
out = {}
for d in sorted(glob.glob(os.path.join(ROOT, "*-final"))):
    block = os.path.basename(d)[:-len("-final")]
    rows = list(csv.DictReader(open(os.path.join(d, "results", "analysis", "cycles", "runs.csv"))))
    p50 = {}
    for r in rows:
        try:
            p50[(r["rep"], r["cond"])] = float(r["steady.p50_ms"])
        except (KeyError, ValueError):
            pass
    reps = sorted({k[0] for k in p50 if k[1] == "baseline"}, key=int)
    base = [p50[(r, "baseline")] for r in reps]
    rec = {"n_cycles": len(reps), "baseline_mean": st.mean(base), "baseline_sd": st.stdev(base)}
    for m in METHODS:
        diffs = [p50[(r, m)] - p50[(r, "baseline")] for r in reps if (r, m) in p50]
        rec[m] = {"n": len(diffs), "mean": st.mean(diffs), "sd": st.stdev(diffs),
                  "pct_of_baseline": 100 * st.mean(diffs) / rec["baseline_mean"]}
    out[block] = rec
    print(f"{block:12} n={len(reps)} baseline {rec['baseline_mean']:7.1f} ± {rec['baseline_sd']:6.1f} ms | " +
          " | ".join(f"{m} {rec[m]['mean']:+7.1f} ± {rec[m]['sd']:5.1f}" for m in METHODS))
json.dump(out, open(os.path.join(HERE, "output.json"), "w"), indent=1)
