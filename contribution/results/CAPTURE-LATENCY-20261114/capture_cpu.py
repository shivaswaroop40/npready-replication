#!/usr/bin/env python3
"""Observer CPU added by each capture method at the capture load: mean and SD of the ten paired
differences per block (method minus the same cycle's baseline, column cpu.cluster.observer of
each block's stored runs.csv). The means equal Table 6.13 of the thesis; this adds the SDs.
Run: python3 capture_cpu.py > output_cpu.txt
"""
import csv, glob, json, os, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "PERF-CYCLES-20261003")
out = {}
for d in sorted(glob.glob(os.path.join(ROOT, "*-final"))):
    block = os.path.basename(d)[:-len("-final")]
    rows = list(csv.DictReader(open(os.path.join(d, "results", "analysis", "cycles", "runs.csv"))))
    by = {(r["rep"], r["cond"]): float(r["cpu.cluster.observer"]) for r in rows}
    reps = sorted({k[0] for k in by if k[1] == "baseline"}, key=int)
    out[block] = {}
    for m in ["hubble", "otterize", "ig_tcp", "ig_snap"]:
        dd = [by[(r, m)] - by[(r, "baseline")] for r in reps if (r, m) in by]
        out[block][m] = {"n": len(dd), "mean": st.mean(dd), "sd": st.stdev(dd)}
    print(f"{block:12} " + " | ".join(f"{m} {v['mean']:.3f} ± {v['sd']:.3f} (n={v['n']})" for m, v in out[block].items()))
json.dump(out, open(os.path.join(HERE, "output_cpu.json"), "w"), indent=1)
