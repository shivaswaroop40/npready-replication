#!/usr/bin/env python3
"""drift_join.py <probe_dir> [--canary-dir DIR]

Joins a drift probe (bin/drift_probe.sh) into <probe_dir>/timeline.csv and summary.json.
Inputs in <probe_dir>: probe.json (nodes, cp node), kv.tsv (clock offsets), tests.jsonl (one
line per fixed-count test: start, end, log), tp/<i>.log (hey output) and canary-<node>.csv
(bin/canary.py; read from --canary-dir when given, e.g. the probe's live copies).

timeline.csv, one row per test:
  i, start_epoch, start_utc, end_epoch, ok, test_s (hey Total), rps, n_expected_status,
  speed_cpu.<node> during the test (iterations per CPU-second, every node),
  speed_cpu_workers (mean of the workers), speed_wall_workers, speed_cpu_workers_pause (the workers
  in the pause before the test, no load), ratio_workers (test speed / median test speed of the
  probe), test_s_norm (test_s x ratio_workers: the time at the probe's median host speed)
summary.json: number of tests; test time mean, min, max and CV raw and normalised; canary speed
min, max and CV; Pearson r of the test time with 1/speed; load_vs_pause = median of the workers'
speed during a test / in the pause before it (1.0 = the guest's own load does not move the canary).
Standard library only; imports the parsers from analyze/analyze.py.
"""
import argparse
import csv
import datetime
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "analyze"))
import analyze as A  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("probe_dir")
    ap.add_argument("--canary-dir", default=None)
    a = ap.parse_args()
    d = a.probe_dir
    cdir = a.canary_dir or d
    probe = json.load(open(os.path.join(d, "probe.json")))
    nodes, cp = probe["nodes"], probe.get("cp", "cp-01")
    workers = [n for n in nodes if n != cp] or nodes
    kv = {}
    try:
        for line in open(os.path.join(d, "kv.tsv")):
            k, _, v = line.rstrip("\n").partition("\t")
            kv[k] = v
    except OSError:
        pass
    canary = {}
    for n in nodes:
        for cand in (f"canary-{n}.csv", f"canary-{n}.csv.gz"):
            path = os.path.join(cdir, cand)
            if os.path.exists(path):
                canary[n] = A.read_canary(path, float(kv.get(f"clock_offset_s.{n}") or 0.0))
                break
    tests = []
    try:
        for line in open(os.path.join(d, "tests.jsonl")):
            try:
                tests.append(json.loads(line))
            except ValueError:
                pass
    except OSError:
        pass
    expect = int(probe.get("tp_expect_status") or 200)
    rows, prev_end = [], None
    for t in tests:
        st, en = t.get("start"), t.get("end")
        r = {"i": t.get("i"), "start_epoch": st, "end_epoch": en, "ok": bool(t.get("ok")),
             "start_utc": datetime.datetime.fromtimestamp(st, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
             if st else None}
        try:
            fc = A.parse_fixed_count(open(os.path.join(d, t.get("log", ""))).read())
        except OSError:
            fc = None
        if fc:
            got = fc.get("codes", {}).get(expect) if "codes" in fc else fc.get("n_2xx")
            r.update({"test_s": fc.get("total_s"), "rps": fc.get("rps"), "n_expected_status": got})
            if not got or got < int(t.get("n") or probe.get("tp_n") or 0):
                r["ok"] = False
        if st and en:
            for n in nodes:
                sc = A.canary_speed(canary.get(n, []), st, en)[0]
                r[f"speed_cpu.{n}"] = sc
            r["speed_cpu_workers"] = A.mean([r.get(f"speed_cpu.{n}") for n in workers])
            r["speed_wall_workers"] = A.mean([A.canary_speed(canary.get(n, []), st, en)[1] for n in workers])
            lo = (prev_end + 2.0) if prev_end else st - 60.0
            if st - 1.0 - lo >= 4.0:
                r["speed_cpu_workers_pause"] = A.mean([A.canary_speed(canary.get(n, []), lo, st - 1.0)[0]
                                                       for n in workers])
        prev_end = en or prev_end
        rows.append(r)
    ok = [r for r in rows if r["ok"] and r.get("test_s") and r.get("speed_cpu_workers")]
    med = statistics.median([r["speed_cpu_workers"] for r in ok]) if ok else None
    for r in rows:
        if med and r.get("speed_cpu_workers") and r.get("test_s"):
            r["ratio_workers"] = r["speed_cpu_workers"] / med
            r["test_s_norm"] = r["test_s"] * r["ratio_workers"]
    cols = (["i", "start_epoch", "start_utc", "end_epoch", "ok", "test_s", "rps", "n_expected_status"]
            + [f"speed_cpu.{n}" for n in nodes]
            + ["speed_cpu_workers", "speed_wall_workers", "speed_cpu_workers_pause", "ratio_workers", "test_s_norm"])
    def fmt(c, v):
        if v is None:
            return ""
        if not isinstance(v, float):
            return v
        if c.endswith("_epoch"):
            return f"{v:.3f}"
        return f"{v:.0f}" if c.startswith("speed_") else f"{v:.6g}"
    tmp = os.path.join(d, ".timeline.csv.tmp")
    with open(tmp, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([fmt(c, r.get(c)) for c in cols])
    os.replace(tmp, os.path.join(d, "timeline.csv"))
    ts = [r["test_s"] for r in ok]
    sp = [r["speed_cpu_workers"] for r in ok]
    lp = [r["speed_cpu_workers"] / r["speed_cpu_workers_pause"] for r in ok if r.get("speed_cpu_workers_pause")]
    summ = {"app": probe.get("app"), "tests": len(rows), "tests_ok": len(ok), "canary_nodes": sorted(canary),
            "test_s_mean": A.mean(ts), "test_s_min": min(ts) if ts else None, "test_s_max": max(ts) if ts else None,
            "test_s_cv_pct": A._cv(ts), "test_s_norm_cv_pct": A._cv([r.get("test_s_norm") for r in ok]),
            "speed_cpu_workers_min": min(sp) if sp else None, "speed_cpu_workers_max": max(sp) if sp else None,
            "speed_cpu_workers_cv_pct": A._cv(sp),
            "r_test_s_vs_inv_speed": A._pearson(ts, [1.0 / x for x in sp]),
            "load_vs_pause_speed_median": statistics.median(lp) if lp else None}
    with open(os.path.join(d, "summary.json"), "w") as fh:
        json.dump(summ, fh, indent=1)
    print(json.dumps(summ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
