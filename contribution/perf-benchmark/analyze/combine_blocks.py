#!/usr/bin/env python3
"""combine_blocks.py <out_dir> <block_dir> [<block_dir> ...]

Combines the per-block analyses (analyze.py on each block's pull, layout "cycle") into one report.
Each <block_dir> is a pull such as PERF-CYCLES-20261003/bank-b1-final, holding
results/analysis/cycles/*.csv and results/<app>/cycle*/<cond>/meta.json.

Blocks are never pooled: the host types differ in CPU speed and in how the kernel mitigates Spectre,
which changes absolute costs (see FIXLOG "Host type changes Inspektor Gadget's CPU cost"). Every
table therefore has one row per (app, block) with the block's host type.

Writes <out_dir>/RESULTS-COMBINED.md and one CSV per table.
"""
import ast
import csv
import glob
import json
import os
import re
import sys

TECHS = ["hubble", "otterize", "ig_tcp", "ig_snap"]
LABEL = {"hubble": "Hubble", "otterize": "Otterize", "ig_tcp": "IG trace_tcp", "ig_snap": "IG snapshot_socket"}
APPS = ["boutique", "bank", "dsb", "otel", "teastore"]
APP_LABEL = {"boutique": "Online Boutique", "bank": "Bank of Anthos", "dsb": "DSB social network",
             "otel": "OpenTelemetry demo", "teastore": "TeaStore"}


def rd(path):
    return list(csv.DictReader(open(path))) if os.path.exists(path) else []


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def f(x, d=3, sign=False):
    if x is None:
        return "-"
    s = f"{x:+.{d}f}" if sign else f"{x:.{d}f}"
    return s


def block_info(bdir):
    """app, block name, cycles, host type and retry count of one block pull."""
    name = os.path.basename(bdir.rstrip("/")).replace("-final", "")
    res = os.path.join(bdir, "results")
    app = next(a for a in APPS if os.path.isdir(os.path.join(res, a)))
    cycles = sorted(int(m.group(1)) for d in glob.glob(os.path.join(res, app, "cycle*"))
                    if (m := re.search(r"cycle(\d+)$", d)))
    meta = sorted(glob.glob(os.path.join(res, app, "cycle*", "baseline", "meta.json")))
    host = {}
    if meta:
        n = json.load(open(meta[0])).get("host", {}).get("nodes", {}).get("worker-01", {})
        v = n.get("vulnerabilities") or {}
        v = v if isinstance(v, dict) else ast.literal_eval(v)
        s2 = v.get("spectre_v2", "")
        host = {"cpu": n.get("cpu_model", "?").replace("(R)", "").replace("  ", " "),
                "mhz": (n.get("cpu_mhz") or [None])[0],
                "mitigation": "software (retpolines)" if "Retpolines" in s2 else
                              "hardware (IBRS)" if "IBRS" in s2 else s2[:30]}
    prog = os.path.join(res, app, "PROGRESS.log")
    retries = sum(1 for line in open(prog) if "FAILED rc" in line) if os.path.exists(prog) else None
    done = len(glob.glob(os.path.join(res, app, "cycle*", "*", "DONE")))
    host_s = f"{host.get('cpu', '?')} {host.get('mhz') or 0:.0f} MHz, {host.get('mitigation', '?')}"
    return {"name": name, "app": app, "cycles": cycles, "host": host, "host_s": host_s,
            "retries": retries, "done": done, "csv": os.path.join(res, "analysis", "cycles")}


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    blocks = [block_info(b) for b in sys.argv[2:]]
    blocks.sort(key=lambda b: (APPS.index(b["app"]), b["cycles"][0] if b["cycles"] else 0))
    L = ["# Capture overhead: combined results over all blocks\n",
         "One row per (app, block). Blocks are not pooled because the host types differ (CPU speed and "
         "Spectre mitigation). Every Δ is the mean of the per-cycle paired differences (technique minus "
         "the same cycle's baseline) with its 95% CI over the block's 10 cycles. Verdict: 'robust' = "
         "significant after Holm and in both pre-declared checks (median/Wilcoxon, and without the "
         "block's first run); 'fragile' = significant after Holm only; 'n.s.' = not significant after Holm, "
         "with the upper 95% bound as the most the effect can be.\n"]

    # ---- blocks
    rows = [[b["name"], APP_LABEL[b["app"]], f"{b['cycles'][0]}-{b['cycles'][-1]}" if b["cycles"] else "-",
             b["host_s"], b["done"], b["retries"]] for b in blocks]
    L.append("## Blocks\n\n" + md_table(["Block", "App", "Cycles", "Host type", "Runs done", "Retried attempts"],
                                       rows) + "\n")

    sens = {}
    for b in blocks:
        for r in rd(os.path.join(b["csv"], "sensitivity.csv")):
            sens[(b["name"], r["endpoint"], r["technique"])] = r

    def cell(bname, ep, tech, d, unit=""):
        r = sens.get((bname, ep, tech))
        if not r:
            return "-", "-"
        p, lo, hi = num(r["primary"]), num(r["primary_lo"]), num(r["primary_hi"])
        v = r["verdict"]
        txt = f"{f(p, d, True)}{unit} [{f(lo, d, True)}, {f(hi, d, True)}]"
        if v.startswith("n.s."):
            v = f"n.s. (< {f(hi, d, True)}{unit})" if hi is not None else "n.s."
        return txt, v

    # ---- Table 5 (GoLeash): fixed-count time
    L.append("## Fixed-count time (GoLeash Table 5 format)\n\n"
             "Time to finish TP_N requests at concurrency 16 (per app: boutique 3008, bank 608, dsb 1504, "
             "otel 7040, teastore 9152), one test per mode per cycle. w/o and with: mean ± SD over the "
             "block's 10 executions. Overhead: paired per-cycle % difference [95% CI].\n")
    t5rows, t5csv = [], []
    for b in blocks:
        t5 = {(r["mode"], r["cond"]): r for r in rd(os.path.join(b["csv"], "table5_fixed_count.csv"))}
        for mode in ("keepalive", "newconn"):
            for t in TECHS:
                r = t5.get((mode, t))
                if not r:
                    continue
                ep = f"tp.{mode}.time_s"
                txt, v = cell(b["name"], ep, t, 1, "%")
                t5rows.append([APP_LABEL[b["app"]], b["name"], "keep-alive" if mode == "keepalive" else "new conn",
                               LABEL[t], f"{f(num(r['wo_exec_s']), 2)} ± {f(num(r['wo_exec_sd']), 2)}",
                               f"{f(num(r['with_exec_s']), 2)} ± {f(num(r['with_exec_sd']), 2)}", txt, v])
                t5csv.append([b["app"], b["name"], b["host_s"], mode, t, r["wo_exec_s"], r["wo_exec_sd"],
                              r["with_exec_s"], r["with_exec_sd"], r["overhead_pct"], r["overhead_ci_lo"],
                              r["overhead_ci_hi"], r["holm_p"], (sens.get((b["name"], ep, t)) or {}).get("verdict")])
    L.append(md_table(["App", "Block", "Mode", "Technique", "w/o (s)", "with (s)", "Overhead [95% CI]", "Verdict"],
                      t5rows) + "\n")

    # ---- observer CPU and memory (steady window, thesis journey-A load)
    rows, cpucsv = [], []
    for b in blocks:
        for t in TECHS:
            c_txt, c_v = cell(b["name"], "cpu.cluster.observer", t, 3)
            m_txt, m_v = cell(b["name"], "anon.cluster.observer", t, 0)
            rows.append([APP_LABEL[b["app"]], b["name"], LABEL[t], c_txt, c_v, m_txt, m_v])
            rc, rm = sens.get((b["name"], "cpu.cluster.observer", t), {}), sens.get((b["name"], "anon.cluster.observer", t), {})
            cpucsv.append([b["app"], b["name"], b["host_s"], t, rc.get("primary"), rc.get("primary_lo"),
                           rc.get("primary_hi"), rc.get("verdict"), rm.get("primary"), rm.get("primary_lo"),
                           rm.get("primary_hi"), rm.get("verdict")])
    L.append("## Resource cost at the thesis load (steady window)\n\n"
             "Δ observer CPU (cores) and Δ observer anonymous memory (MiB): the capture components and their "
             "clients, technique minus baseline, at each app's thesis journey-A load.\n\n"
             + md_table(["App", "Block", "Technique", "Δ observer CPU (cores)", "Verdict", "Δ anon memory (MiB)",
                         "Verdict"], rows) + "\n")

    # ---- cost under load: observer CPU during the new-connection fixed-count tests
    rows = []
    for b in blocks:
        fc = {(r["mode"], r["cond"]): r for r in rd(os.path.join(b["csv"], "fixed_count_cpu.csv"))}
        for t in TECHS:
            r = fc.get(("newconn", t))
            if r:
                rows.append([APP_LABEL[b["app"]], b["name"], LABEL[t],
                             f"{f(num(r['obs_delta']), 3, True)} [{f(num(r['obs_ci_lo']), 3, True)}, "
                             f"{f(num(r['obs_ci_hi']), 3, True)}]",
                             f"{f(num(r['node_delta']), 3, True)} [{f(num(r['node_ci_lo']), 3, True)}, "
                             f"{f(num(r['node_ci_hi']), 3, True)}]"])
    L.append("## Cost under load (new-connection fixed-count tests)\n\n"
             "Δ observer CPU and Δ node busy CPU (all nodes, cores) while the app serves one new TCP "
             "connection per request as fast as it can.\n\n"
             + md_table(["App", "Block", "Technique", "Δ observer CPU", "Δ node busy CPU"], rows) + "\n")

    # ---- host type and Inspektor Gadget
    rows = []
    for b in blocks:
        comp = {(r["cond"], r["component"]): num(r["cpu_cores_mean"])
                for r in rd(os.path.join(b["csv"], "components_cpu_mem.csv"))}
        rows.append([b["name"], b["host_s"], f(comp.get(("ig_tcp", "gadget"))), f(comp.get(("ig_snap", "gadget"))),
                     f(comp.get(("baseline", "cilium-agent")))])
    L.append("## Host type and Inspektor Gadget's own CPU\n\n"
             "Steady-window CPU (cores) of the gadget DaemonSet pods and of cilium-agent at baseline. "
             "Hypothesis (FIXLOG, untested directly): hosts whose kernel mitigates Spectre v2 / retbleed in "
             "software (retpolines, return thunk) make the syscall-heavy gadget agent about 3x dearer.\n\n"
             + md_table(["Block", "Host type", "gadget (ig_tcp)", "gadget (ig_snap)", "cilium-agent (baseline)"],
                        rows) + "\n")

    # ---- robust findings
    rob = []
    for (bname, ep, t), r in sorted(sens.items()):
        if r["verdict"] == "robust" and ep.startswith("tp."):
            rob.append(f"- {bname}: {LABEL[t]} slows the fixed-count test "
                       f"({'keep-alive' if 'keepalive' in ep else 'new conn'}) by {f(num(r['primary']), 1, True)}% "
                       f"[{f(num(r['primary_lo']), 1, True)}, {f(num(r['primary_hi']), 1, True)}]")
    frag = [f"- {bname}: {LABEL[t]} {ep} {f(num(r['primary']), 3, True)} (significant after Holm, not in both checks)"
            for (bname, ep, t), r in sorted(sens.items()) if r["verdict"] == "fragile"]
    L.append("## Throughput effects that survive every check\n\n" + ("\n".join(rob) or "- none") + "\n\n"
             "Fragile results (significant after Holm only):\n\n" + ("\n".join(frag) or "- none") + "\n")

    open(os.path.join(out, "RESULTS-COMBINED.md"), "w").write("\n".join(L))
    with open(os.path.join(out, "table5_combined.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["app", "block", "host", "mode", "technique", "wo_s", "wo_sd", "with_s", "with_sd",
                    "overhead_pct", "ci_lo", "ci_hi", "holm_p", "verdict"])
        w.writerows(t5csv)
    with open(os.path.join(out, "resources_combined.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["app", "block", "host", "technique", "cpu_delta", "cpu_lo", "cpu_hi", "cpu_verdict",
                    "anon_delta_mib", "anon_lo", "anon_hi", "anon_verdict"])
        w.writerows(cpucsv)
    print(f"combined {len(blocks)} blocks -> {out}/RESULTS-COMBINED.md")


if __name__ == "__main__":
    main()
