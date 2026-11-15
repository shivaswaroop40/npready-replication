#!/usr/bin/env python3
"""plan.py <results_root> [--out PLAN.json] [--max-hours 20] [--setup-hours 1.0]

Builds the play plan for the full matrix (5 conditions x 3 reps per app) from measured runs:
every short run (--short) and any run with full-size fixed-count tests under <results_root>.
Laptop side; reads meta.json + tp/*.log of each run dir, like analyze.py.

Per app it measures
  fixed_s   = run wall time minus the hey time of its fixed-count tests (condition switch,
              restart, idle, warm-up, window, snapshots, ct/metric snapshots, job create/delete),
  ovh_s     = per-test time that is not hey's own total (pre-hook, job start/stop, 20 s pause),
  rate      = requests/s of each fixed-count mode at c16 (hey's own N / Total),
  deploy_s  = app deploy (and dsb's one-time graph init) from <app>/deploy.log / PROGRESS.log,
and estimates a full run as
  full_s = (fixed_s - n_tests*ovh_s) + (idle_full - idle) + (warmup_full - warmup)
           + (steady_full - steady) + 6 * ovh_s + sum over modes of 3 * 10000 / rate.
Play hours = setup (play start, install, image pre-pull) + deploy + runs * full_s * 1.05.
The reps of an app are split over as few plays as keep every play <= --max-hours.
"""
import argparse
import glob
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "analyze"))
import analyze as A  # noqa: E402

FULL = {"idle_s": 60.0, "warmup_s": 180.0, "steady_s": 1200.0, "tp_reps": 3, "tp_n": 10000}
CONDS = 5
REPS = 3


def app_env(root, app):
    env = {}
    p = os.path.join(root, "..", "..", "apps", app, "app.env")
    for cand in (p, os.path.join(os.path.dirname(HERE), "apps", app, "app.env")):
        if os.path.exists(cand):
            for line in open(cand):
                m = re.match(r"^\s*([A-Z_][A-Z0-9_]*)=(.*)$", line)
                if m:
                    env[m.group(1)] = m.group(2).strip().strip("'\"")
            break
    return env


def measure(run_dir):
    meta = json.load(open(os.path.join(run_dir, "meta.json")))
    if float((meta.get("kv") or {}).get("app_restarts_during_run", 0) or 0) > 0:
        raise ValueError("app restarted during the run (not representative)")
    ph = meta["phases"]
    pr = meta["params"]
    wall = ph["run_end"] - ph["run_start"]
    hey, rates = 0.0, {"keepalive": [], "newconn": []}
    n_tests = 0
    for t in meta.get("tp_tests", []):
        try:
            r = A.parse_fixed_count(open(os.path.join(run_dir, t["log"])).read())
        except OSError:
            r = None
        if not r or not r.get("total_s"):
            continue
        n_tests += 1
        hey += r["total_s"]
        rates[t["mode"]].append((t.get("n") or pr["tp_n"]) / r["total_s"])
    tp_span = (ph.get("throughput_end", 0) - ph.get("throughput_start", 0)) if "throughput_end" in ph else None
    ovh = (tp_span - hey) / n_tests if tp_span and n_tests else None
    return {"wall": wall, "hey": hey, "n_tests": n_tests, "ovh": ovh, "rates": rates,
            "idle_s": pr.get("idle_s", 0.0), "warmup_s": pr["warmup_s"], "steady_s": pr["steady_s"],
            "restart_s": ph.get("app_restart_end", 0) - ph.get("app_restart_start", 0),
            "cond_s": ph.get("cond_end", 0) - ph.get("cond_start", 0), "short": meta.get("short"),
            "tp_n": pr["tp_n"], "cond": meta["cond"], "status": meta["status"]}


def deploy_seconds(root, app):
    prog = os.path.join(root, app, "PROGRESS.log")
    if os.path.exists(prog):
        for line in open(prog):
            m = re.search(r"deploy ok in (\d+)s", line)
            if m:
                return float(m.group(1))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_root", nargs="+")
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-hours", type=float, default=20.0)
    ap.add_argument("--setup-hours", type=float, default=1.0,
                    help="play start + cluster install + image pre-pull (install measured ~15-40 min, pre-pull ~10 min)")
    ap.add_argument("--slack", type=float, default=1.05, help="factor on run time for retries and drift")
    ap.add_argument("--extra-s", type=float, default=20.0,
                    help="seconds per run the measured runs did not have yet (the 20 s pod-stability wait)")
    ap.add_argument("--override", action="append", default=[],
                    help="app:key=value, e.g. dsb:deploy_s=1500 (measured outside the results root)")
    ap.add_argument("--assume", default=None,
                    help="JSON file {app: {full_s, deploy_s, basis}} for apps with no measured run here")
    a = ap.parse_args()
    per_app = {}
    for root in a.results_root:
        for meta in sorted(glob.glob(os.path.join(root, "*", "rep*", "*", "meta.json"))):
            d = os.path.dirname(meta)
            app = d.split(os.sep)[-3]
            if not os.path.exists(os.path.join(d, "DONE")):
                continue
            try:
                m = measure(d)
            except (OSError, KeyError, ValueError) as e:
                print(f"skip {d}: {e}", file=sys.stderr)
                continue
            per_app.setdefault(app, {"runs": [], "deploy_s": None, "roots": set()})
            per_app[app]["runs"].append(m)
            per_app[app]["roots"].add(root)
            dep = deploy_seconds(root, app)
            if dep is not None:
                per_app[app]["deploy_s"] = dep
    over = {}
    for o in a.override:
        app, _, kv = o.partition(":")
        k, _, v = kv.partition("=")
        over.setdefault(app, {})[k] = float(v)

    plan, notes = [], {}
    assumed = {k: v for k, v in (json.load(open(a.assume)) if a.assume else {}).items() if not k.startswith("_")}
    for app, d in sorted(list(per_app.items()) + [(k, None) for k in assumed if k not in per_app]):
        if d is None:
            v = assumed[app]
            full_s, deploy_s = float(v["full_s"]), float(v.get("deploy_s", 300))
            env = app_env(a.results_root[0], app)
            rt = int(float(env.get("RUN_TIMEOUT", 5400)))
            notes[app] = {"full_run_min": round(full_s / 60, 1), "deploy_s": deploy_s, "assumed": True}
            hrs = a.setup_hours + deploy_s / 3600.0 + CONDS * REPS * full_s * a.slack / 3600.0
            plan.append({"name": app, "app": app, "rep_list": list(range(1, REPS + 1)), "runs": CONDS * REPS,
                         "est_hours": round(hrs, 2), "est_run_min": round(full_s / 60, 1), "run_timeout_s": rt,
                         "command": f"run_matrix.sh {app} --rep-list '1 2 3'",
                         "basis": v.get("basis", "assumed") + f"; full run {full_s / 60:.1f} min; deploy "
                                  f"{deploy_s / 60:.1f} min; setup {a.setup_hours} h; x{a.slack} slack on run time",
                         "basis_detail": notes[app]})
            continue
        runs = d["runs"]
        rates = {mode: [x for r in runs for x in r["rates"][mode]] for mode in ("keepalive", "newconn")}
        rate = {mode: (statistics.fmean(v) if v else None) for mode, v in rates.items()}
        ovh = statistics.fmean([r["ovh"] for r in runs if r["ovh"] is not None])
        base = []
        for r in runs:
            fixed = r["wall"] - r["hey"] - r["n_tests"] * ovh
            base.append(fixed + (FULL["idle_s"] - r["idle_s"]) + (FULL["warmup_s"] - r["warmup_s"])
                        + (FULL["steady_s"] - r["steady_s"]))
        fixed_full = statistics.fmean(base) + a.extra_s
        tp_full = sum(FULL["tp_reps"] * FULL["tp_n"] / rate[m] for m in rate if rate[m])
        full_s = over.get(app, {}).get("full_s") or (fixed_full + 2 * FULL["tp_reps"] * ovh + tp_full)
        deploy_s = over.get(app, {}).get("deploy_s") or d["deploy_s"] or 300.0
        env = app_env(list(d["roots"])[0], app)
        rt = int(float(env.get("RUN_TIMEOUT", 5400)))
        runs_total = CONDS * REPS

        def hours(nruns):
            return a.setup_hours + deploy_s / 3600.0 + nruns * full_s * a.slack / 3600.0

        nplays = 1
        while True:
            per = math.ceil(REPS / nplays)
            if hours(per * CONDS) <= a.max_hours or per == 1:
                break
            nplays += 1
        reps = list(range(1, REPS + 1))
        chunks, i = [], 0
        sizes = [REPS // nplays + (1 if k < REPS % nplays else 0) for k in range(nplays)]
        for s in sizes:
            chunks.append(reps[i:i + s])
            i += s
        basis = (f"{len(runs)} measured runs (conds {sorted({r['cond'] for r in runs})}); fixed part of a full run "
                 f"{fixed_full / 60:.1f} min (condition switch {statistics.fmean([r['cond_s'] for r in runs]):.0f} s, "
                 f"app restart {statistics.fmean([r['restart_s'] for r in runs]):.0f} s, idle 60 s, warm-up 180 s, window "
                 f"1200 s, snapshots); fixed-count at c16: keep-alive {rate['keepalive'] or 0:.1f} req/s, new conn "
                 f"{rate['newconn'] or 0:.1f} req/s -> 6 x 10000 requests = {tp_full / 60:.1f} min, plus "
                 f"{ovh:.0f} s per test (pause, job start, pre-hook); full run {full_s / 60:.1f} min; deploy "
                 f"{deploy_s / 60:.1f} min; setup {a.setup_hours} h; x{a.slack} slack on run time")
        if over.get(app):
            basis += f"; overrides {over[app]}"
        notes[app] = {"full_run_min": round(full_s / 60, 1), "rate": rate, "ovh_s": ovh, "deploy_s": deploy_s,
                      "fixed_full_min": round(fixed_full / 60, 1)}
        for k, ch in enumerate(chunks):
            name = app if nplays == 1 else f"{app}-{'abcdefgh'[k]}"
            plan.append({"name": name, "app": app, "rep_list": ch, "runs": len(ch) * CONDS,
                         "est_hours": round(hours(len(ch) * CONDS), 2), "est_run_min": round(full_s / 60, 1),
                         "run_timeout_s": rt,
                         "command": f"run_matrix.sh {app} --rep-list '{' '.join(map(str, ch))}'",
                         "basis": basis, "basis_detail": notes[app]})
    txt = json.dumps(plan, indent=1)
    if a.out:
        open(a.out, "w").write(txt + "\n")
    print(txt)
    bad = [p for p in plan if p["est_hours"] > a.max_hours]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
