#!/usr/bin/env python3
"""Time the three offline generation steps per application with /usr/bin/time -l.

Usage: bench.py [--reps 20] [--warmup 2] [--out DIR]
Every measurement is a fresh process wrapped in /usr/bin/time -l. Each repetition runs, for
each application in turn, step 1 -> step 2 -> step 3 (step 3 reads the outputs of 1 and 2),
plus two app-independent reference processes (bare interpreter, npready CLI startup).
The first --warmup repetitions are recorded with warmup=1 and excluded from the summary.
Writes DIR/runs.csv (one row per process) and DIR/env.json, and leaves the last run's
outputs in DIR/out/<APP>/ for verify.py.
"""
import argparse
import csv
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import APPS, HERE, manifests_path  # noqa: E402

PY = shutil.which("python3")
NPREADY = shutil.which("npready")
TIME_RE = re.compile(r"([\d.]+) real\s+([\d.]+) user\s+([\d.]+) sys")
FIELDS = {"maximum resident set size": "maxrss_bytes", "peak memory footprint": "peak_footprint_bytes",
          "instructions retired": "instructions", "page reclaims": "page_reclaims",
          "page faults": "page_faults", "involuntary context switches": "invol_csw"}


def sh(*cmd):
    return subprocess.run(cmd, capture_output=True, text=True).stdout.strip()


def timed(cmd):
    t0 = time.perf_counter()
    p = subprocess.run(["/usr/bin/time", "-l"] + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    wall_pc = time.perf_counter() - t0
    if p.returncode != 0:
        raise SystemExit(f"failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr}")
    m = TIME_RE.search(p.stderr)
    row = {"wall_s": float(m.group(1)), "user_s": float(m.group(2)), "sys_s": float(m.group(3)),
           "wall_perfcounter_s": round(wall_pc, 6)}
    for line in p.stderr.splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[1] in FIELDS:
            row[FIELDS[parts[1]]] = int(parts[0])
    return row


def steps(app, out):
    return [
        ("1_synth", [PY, os.path.join(HERE, "gen_synth.py"), app, out]),
        ("2_derive", [NPREADY, "derive", "--manifests", manifests_path(app),
                      "--json", os.path.join(out, "config_derived_edges.json")]),
        ("3_fuse", [PY, os.path.join(HERE, "gen_fuse.py"), app, out]),
    ]


REFERENCES = [("ref_python_startup", [PY, "-c", "pass"]),
              ("ref_npready_startup", [NPREADY, "--version"])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--warmup", type=int, default=2)
    ap.add_argument("--out", default=HERE)
    a = ap.parse_args()
    outroot = os.path.join(a.out, "out")
    env = {"started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "hw.model": sh("sysctl", "-n", "hw.model"),
           "cpu": sh("sysctl", "-n", "machdep.cpu.brand_string"), "ncpu": sh("sysctl", "-n", "hw.ncpu"),
           "perf_cores": sh("sysctl", "-n", "hw.perflevel0.physicalcpu"),
           "eff_cores": sh("sysctl", "-n", "hw.perflevel1.physicalcpu"),
           "memsize_bytes": int(sh("sysctl", "-n", "hw.memsize")),
           "macos": sh("sw_vers", "-productVersion") + " (" + sh("sw_vers", "-buildVersion") + ")",
           "python": sh(PY, "--version"), "python_path": os.path.realpath(PY),
           "npready": sh(NPREADY, "--version"), "npready_path": NPREADY,
           "npready_src_commit": sh("git", "-C", "/Users/shiv/Desktop/code/netpol-readiness", "rev-parse", "--short", "HEAD"),
           "pyyaml": sh(PY, "-c", "import yaml;print(yaml.__version__)"),
           "power": sh("pmset", "-g", "batt").splitlines()[0], "loadavg_start": sh("sysctl", "-n", "vm.loadavg"),
           "reps": a.reps, "warmup": a.warmup}
    with open(os.path.join(a.out, "runs.csv"), "w", newline="") as f:
        cols = ["rep", "warmup", "app", "step", "wall_s", "wall_perfcounter_s", "user_s", "sys_s", "cpu_s",
                "maxrss_bytes", "peak_footprint_bytes", "instructions", "page_reclaims", "page_faults", "invol_csw"]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for rep in range(a.warmup + a.reps):
            wu = int(rep < a.warmup)
            for name, cmd in REFERENCES:
                r = timed(cmd)
                w.writerow(dict(rep=rep, warmup=wu, app="-", step=name, cpu_s=round(r["user_s"] + r["sys_s"], 2), **r))
            for app in APPS:
                out = os.path.join(outroot, app)
                shutil.rmtree(out, ignore_errors=True)
                os.makedirs(out)
                for name, cmd in steps(app, out):
                    r = timed(cmd)
                    w.writerow(dict(rep=rep, warmup=wu, app=app, step=name, cpu_s=round(r["user_s"] + r["sys_s"], 2), **r))
            f.flush()
            print(f"rep {rep} done (warmup={wu})", flush=True)
    env["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    env["loadavg_end"] = sh("sysctl", "-n", "vm.loadavg")
    env["platform"] = platform.platform()
    json.dump(env, open(os.path.join(a.out, "env.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
