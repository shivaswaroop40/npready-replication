#!/usr/bin/env python3
"""Summarise runs.csv (non-warm-up rows) into Markdown tables on stdout.

Usage: summarize.py [runs.csv]
Wall = /usr/bin/time -l "real" (10 ms resolution) and the driver's perf_counter around the
same process (sub-millisecond, includes the /usr/bin/time fork). CPU = user + sys from
/usr/bin/time -l (10 ms resolution). Peak RSS = "maximum resident set size" in MiB.
"""
import csv
import os
import statistics as st
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
STEP_NAMES = {"1_synth": "Step 1: observation-only generation (Hubble capture -> synth edges + policy)",
              "2_derive": "Step 2: configuration derivation (npready derive --manifests)",
              "3_fuse": "Step 3: fusion (union + fused policy render)"}


def fmt(xs, f):
    return f"{f(st.median(xs))} [{f(min(xs))}-{f(max(xs))}]"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "runs.csv")
    rows = [r for r in csv.DictReader(open(path)) if r["warmup"] == "0"]
    g = defaultdict(list)
    for r in rows:
        g[(r["app"], r["step"])].append(r)
    apps = sorted({r["app"] for r in rows if r["app"] != "-"}, key=lambda a: ["BOUTIQUE", "DSB", "BANK", "OTEL", "TEASTORE"].index(a.split("-")[0]))
    ms = lambda x: f"{x * 1000:.0f}"
    s2 = lambda x: f"{x:.2f}"
    mib = lambda x: f"{x / 2**20:.1f}"
    gi = lambda x: f"{x / 1e9:.2f}"
    head = "| app | n | wall ms (perf_counter) | wall s (time -l) | CPU s user+sys | peak RSS MiB | instructions 10^9 |\n|---|---|---|---|---|---|---|"
    for step, title in STEP_NAMES.items():
        print(f"\n#### {title}\n\n{head}")
        for app in apps:
            rs = g[(app, step)]
            col = lambda k: [float(r[k]) for r in rs]
            print(f"| {app.split('-')[0].title()} | {len(rs)} | {fmt(col('wall_perfcounter_s'), ms)} | {fmt(col('wall_s'), s2)} | "
                  f"{fmt(col('cpu_s'), s2)} | {fmt(col('maxrss_bytes'), mib)} | {fmt(col('instructions'), gi)} |")
    print(f"\n#### Reference processes (no work)\n\n{head}")
    for step in ("ref_python_startup", "ref_npready_startup"):
        rs = g[("-", step)]
        col = lambda k: [float(r[k]) for r in rs]
        print(f"| {step} | {len(rs)} | {fmt(col('wall_perfcounter_s'), ms)} | {fmt(col('wall_s'), s2)} | "
              f"{fmt(col('cpu_s'), s2)} | {fmt(col('maxrss_bytes'), mib)} | {fmt(col('instructions'), gi)} |")
    print("\n#### What fusion adds (step 2 + step 3, per repetition) over step 1\n")
    print("| app | step 1 wall ms | step 2+3 wall ms | added / step 1 | step 1 CPU s | step 2+3 CPU s | step 1 peak RSS MiB | max(step 2, step 3) peak RSS MiB |\n|---|---|---|---|---|---|---|---|")
    for app in apps:
        by = defaultdict(dict)
        for step in STEP_NAMES:
            for r in g[(app, step)]:
                by[r["rep"]][step] = r
        s1w = [float(v["1_synth"]["wall_perfcounter_s"]) for v in by.values()]
        addw = [float(v["2_derive"]["wall_perfcounter_s"]) + float(v["3_fuse"]["wall_perfcounter_s"]) for v in by.values()]
        s1c = [float(v["1_synth"]["cpu_s"]) for v in by.values()]
        addc = [float(v["2_derive"]["cpu_s"]) + float(v["3_fuse"]["cpu_s"]) for v in by.values()]
        rss1 = [float(v["1_synth"]["maxrss_bytes"]) for v in by.values()]
        rss23 = [max(float(v["2_derive"]["maxrss_bytes"]), float(v["3_fuse"]["maxrss_bytes"])) for v in by.values()]
        ratio = st.median(addw) / st.median(s1w)
        print(f"| {app.split('-')[0].title()} | {ms(st.median(s1w))} | {ms(st.median(addw))} | {ratio * 100:.0f} % | "
              f"{s2(st.median(s1c))} | {s2(st.median(addc))} | {mib(st.median(rss1))} | {mib(st.median(rss23))} |")


if __name__ == "__main__":
    main()
