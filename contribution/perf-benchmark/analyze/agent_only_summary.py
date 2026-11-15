#!/usr/bin/env python3
"""agent_only_summary.py <out_dir> <block_dir> [<block_dir> ...]

Summary of the agent-only Hubble experiment (FIXLOG, 2026-10-05). Each <block_dir> is a pull such as
PERF-AGENTONLY-20261005/ao-boutique-final with results/analysis/cycles/*.csv already built by analyze.py.

Per app (one block each, never pooled): Hubble agent-only against baseline (the headline contrast, from
the pre-declared analysis in sensitivity.csv), and the secondary contrast agent-only against the full Hubble
stack in the same cycles (paired per cycle, 95% CI over cycles, computed here from runs.csv).
Also the agent's share of the full stack's extra observer CPU and memory.

Writes <out_dir>/AGENT-ONLY-SUMMARY.md and agent_only_summary.csv.
"""
import csv
import glob
import json
import math
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A  # noqa: E402

APPS = ["boutique", "bank", "dsb", "otel", "teastore"]
NAME = {"boutique": "Online Boutique", "bank": "Bank of Anthos", "dsb": "DSB social network",
        "otel": "OpenTelemetry demo", "teastore": "TeaStore"}


def rd(path):
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def host_of(bdir, app):
    f = sorted(glob.glob(os.path.join(bdir, "results", app, "cycle*", "baseline", "meta.json")))
    if not f:
        return "?"
    n = json.load(open(f[0])).get("host", {}).get("nodes", {}).get("worker-01", {})
    return f"{n.get('cpu_model', '?').split('(')[0].strip()} {(n.get('cpu_mhz') or [0])[0]:.0f} MHz"


def paired(rows, key, a, b, pct=False):
    """paired per-cycle difference a minus b of metric `key` (or % of b); returns A.paired_stats dict"""
    by = {}
    for r in rows:
        if r["status"] == "DONE":
            by.setdefault(r["rep"], {})[r["cond"]] = num(r.get(key))
    ds = []
    for cyc, d in by.items():
        if d.get(a) is not None and d.get(b) is not None:
            ds.append(100.0 * (d[a] - d[b]) / d[b] if pct and d[b] else d[a] - d[b])
    st = A.paired_stats(ds)
    st["wilcox"] = A.wilcoxon_p(ds)
    return st


def fmt(st, d, unit="", sign=True):
    if not st or st.get("mean") is None or st["n"] < 2:
        return "-"
    s = lambda x: (f"{x:+.{d}f}" if sign else f"{x:.{d}f}")
    ns = " (n.s.)" if st["lo"] <= 0 <= st["hi"] else ""
    return f"{s(st['mean'])}{unit} [{s(st['lo'])}, {s(st['hi'])}]{ns}"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    blocks = {}
    for b in sys.argv[2:]:
        res = os.path.join(b, "results")
        app = next((a for a in APPS if os.path.isdir(os.path.join(res, a))), None)
        if app:
            blocks[app] = b
    L = ["# Agent-only Hubble experiment: summary\n",
         "Conditions per cycle: baseline (Hubble off), full Hubble (agent + metrics + Relay + streaming client) and "
         "**agent-only Hubble** (Hubble on in the Cilium agent, no metrics server, no Relay, no client: the Helm "
         "default). 12 cycles per app on one fresh play, all 6 orders twice. Each cell is the mean of the paired "
         "per-cycle differences with its 95% CI over cycles; n.s. = the interval includes zero. One block per app, "
         "never pooled across host types.\n"]
    csv_rows = []
    tab_rows, share_rows, hdr_rows = [], [], []
    for app in APPS:
        if app not in blocks:
            continue
        b = blocks[app]
        cyc = os.path.join(b, "results", "analysis", "cycles")
        runs = rd(os.path.join(cyc, "runs.csv"))
        done = [r for r in runs if r["status"] == "DONE"]
        n_cycles = len({r["rep"] for r in done if r["cond"] == "hubble_agent"})
        hdr_rows.append([NAME[app], host_of(b, app), len(done), n_cycles])
        sens = {(r["endpoint"], r["technique"]): r for r in rd(os.path.join(cyc, "sensitivity.csv"))}

        def head(ep, d, unit=""):
            r = sens.get((ep, "hubble_agent"))
            if not r:
                return "-", "-"
            lo, hi = num(r["primary_lo"]), num(r["primary_hi"])
            p = num(r["primary"])
            return f"{p:+.{d}f}{unit} [{lo:+.{d}f}, {hi:+.{d}f}]", r["verdict"]

        cpu, cpu_v = head("cpu.cluster.observer", 3)
        mem, mem_v = head("anon.cluster.observer", 0)
        ka, ka_v = head("tp.keepalive.time_s", 1, "%")
        nc, nc_v = head("tp.newconn.time_s", 1, "%")
        tab_rows.append([NAME[app], f"{cpu} {cpu_v}", f"{mem} {mem_v}", f"{ka} {ka_v}", f"{nc} {nc_v}"])
        # secondary contrast: agent-only against the full stack, same cycles
        s_cpu = paired(runs, "cpu.cluster.observer", "hubble_agent", "hubble")
        s_mem = paired(runs, "anon.cluster.observer", "hubble_agent", "hubble")
        s_ka = paired(runs, "tp.keepalive.time_s", "hubble_agent", "hubble", pct=True)
        s_nc = paired(runs, "tp.newconn.time_s", "hubble_agent", "hubble", pct=True)
        share_rows.append([NAME[app], fmt(s_cpu, 3), fmt(s_mem, 0), fmt(s_ka, 1, "%"), fmt(s_nc, 1, "%")])
        # agent's share of the full stack's extra observer CPU (means over cycles)
        def mean_of(key, cond):
            v = [num(r.get(key)) for r in done if r["cond"] == cond and num(r.get(key)) is not None]
            return statistics.fmean(v) if v else None
        base, ha, hf = (mean_of("cpu.cluster.observer", c) for c in ("baseline", "hubble_agent", "hubble"))
        mb, mha, mhf = (mean_of("anon.cluster.observer", c) for c in ("baseline", "hubble_agent", "hubble"))
        if None not in (base, ha, hf) and hf > base:
            csv_rows.append([app, host_of(b, app), len(done), n_cycles, ha - base, hf - base,
                             100 * (ha - base) / (hf - base), (mha - mb) if mb is not None else None,
                             (mhf - mb) if mb is not None else None])
            share_rows[-1].append(f"{100 * (ha - base) / (hf - base):.0f}%")
        else:
            share_rows[-1].append("-")

    L.append("## Runs\n\n" + A.md_table(["App", "Host", "Runs done", "Cycles with agent-only"], hdr_rows) + "\n")
    L.append("## Agent-only Hubble against baseline (headline)\n\n"
             "Pre-declared primary endpoints: observer CPU (cores), observer anonymous memory (MiB), fixed-count "
             "time (%, keep-alive and new connection). Verdict: robust / fragile / n.s. as in the main study "
             "(Holm over the two techniques, median/Wilcoxon, without the first run).\n\n"
             + A.md_table(["App", "Δ observer CPU (cores)", "Δ anon memory (MiB)", "Fixed-count, keep-alive",
                           "Fixed-count, new connection"], tab_rows) + "\n")
    L.append("## Agent-only against the full Hubble stack (same cycles; secondary)\n\n"
             "Agent-only minus full stack. A negative number means the agent-only setup uses less. The last column "
             "is the agent-only share of the full stack's extra observer CPU over baseline.\n\n"
             + A.md_table(["App", "Δ observer CPU (cores)", "Δ anon memory (MiB)", "Fixed-count, keep-alive",
                           "Fixed-count, new connection", "Agent-only share of extra CPU"], share_rows) + "\n")
    open(os.path.join(out, "AGENT-ONLY-SUMMARY.md"), "w").write("\n".join(L))
    with open(os.path.join(out, "agent_only_summary.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["app", "host", "runs_done", "cycles", "agent_extra_cpu", "full_extra_cpu", "agent_share_pct",
                    "agent_extra_anon_mib", "full_extra_anon_mib"])
        w.writerows(csv_rows)
    print(f"wrote {out}/AGENT-ONLY-SUMMARY.md ({len(blocks)} apps)")


if __name__ == "__main__":
    main()
