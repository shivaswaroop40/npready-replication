#!/usr/bin/env python3
"""Sanity checks for collected benchmark runs (laptop side, standard library only).

Usage: python3 analyze/sanity_check.py <results_root> [--cp-max 75] [--json out.json]

For every run directory (<app>/rep<r>/<cond> and <app>/cycle<k>/<cond>, attempt dirs ignored) it checks:
  state      cond.sh state matches the condition (hubble / otterize / gadget on or off) AND the
             samples agree: hubble-relay, otterize-system and gadget pods appear in the steady
             window only in their own condition, and the pb-* client scopes only where expected
  sampler    every node's samples cover the analysis window with no gap > 2 intervals
  cp01_tp    cp-01 busy CPU (all cores) during each fixed-count test < --cp-max % (load driver
             not saturated); the steady-window value is reported too
  tp_2xx     each fixed-count test returned > 99 % 2xx and the expected request count
  hubble     flows (client lines, hubble_flows_processed_total) > 0 only in hubble
  ig         trace_tcp lines > 0 only in ig_tcp; snapshot entries > 0 only in ig_snap
  otterize   serviceIntents of the app namespace at t1 > 0 only in otterize
Writes a Markdown table to stdout. Exit 1 if any check fails.
"""
import argparse
import csv
import gzip
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A  # noqa: E402

CONDS = ["baseline", "hubble", "hubble_agent", "otterize", "ig_tcp", "ig_snap"]
# hubble_agent: agent Hubble on, no Relay/metrics/client; its own state check is below
EXPECT = {"baseline": (0, 0, 0), "hubble": (1, 0, 0), "hubble_agent": (0, 0, 0), "otterize": (0, 1, 0),
          "ig_tcp": (0, 0, 1), "ig_snap": (0, 0, 1)}


def rd_json(p):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def sample_rows(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", newline="") as f:
        yield from csv.DictReader(f)


def node_samples(run, node):
    for ext in (".csv.gz", ".csv"):
        p = os.path.join(run, f"samples-{node}{ext}")
        if os.path.exists(p):
            return p
    return None


def check_run(run, cp_max, root):
    meta = rd_json(os.path.join(run, "meta.json")) or {}
    cond, ns = meta.get("cond"), meta.get("app_ns")
    ph = meta.get("phases", {})
    res = {"run": os.path.relpath(run, root), "status": meta.get("status"), "cond": cond, "fail": [], "info": {}}
    if meta.get("status") != "DONE":
        res["fail"].append(f"status {meta.get('status')}")
        return res
    want_h, want_o, want_g = EXPECT[cond]

    # ---- state from cond.sh
    cs = meta.get("cond_state") or {}
    h_on = cs.get("enable_hubble") == "true" and (cs.get("relay") or {}).get("pods", 0) >= 1
    h_off = cs.get("enable_hubble") == "false" and (cs.get("relay") or {}).get("pods", 0) == 0 \
        and not any((cs.get("cilium") or {}).get("hubble_metrics_9965", []))
    o_on = (cs.get("otterize") or {}).get("mapper_pods", 0) >= 1 and (cs.get("otterize") or {}).get("sniffer_desired", 0) >= 1
    o_off = (cs.get("otterize") or {}).get("pods", 1) == 0
    g_on = (cs.get("gadget") or {}).get("pods", 0) >= 1
    g_off = (cs.get("gadget") or {}).get("pods", 1) == 0
    if cond == "hubble_agent":
        csc = cs.get("cilium") or {}
        if not (cs.get("enable_hubble") == "true" and (cs.get("relay") or {}).get("pods", 1) == 0
                and not any(csc.get("hubble_metrics_9965", []))
                and csc.get("agent_hubble") and all("hubble=Ok" in x for x in csc.get("agent_hubble", []))):
            res["fail"].append("cond_state hubble_agent: agent Hubble not on, or Relay/metrics not off")
    for name, want, on, off in (("hubble", want_h, h_on, h_off), ("otterize", want_o, o_on, o_off),
                                ("gadget", want_g, g_on, g_off)):
        if name == "hubble" and cond == "hubble_agent":
            continue
        if (want and not on) or (not want and not off):
            res["fail"].append(f"cond_state {name} {'not on' if want else 'not off'}")

    # ---- BPF programs (bpf_pre before the run, bpf_final with the clients still running),
    # host identity and the idle segment (added 2026-10-02; older runs lack them -> info only)
    bpf = meta.get("bpf") or {}
    pre_t = (bpf.get("pre") or {}).get("tracing_progs_total")
    fin_t = (bpf.get("final") or {}).get("tracing_progs_total")
    pre_g = (bpf.get("pre") or {}).get("gadget_progs_total")
    fin_g = (bpf.get("final") or {}).get("gadget_progs_total")
    res["info"]["bpf_tracing_pre_final"] = [pre_t, fin_t]
    res["info"]["bpf_gadget_pre_final"] = [pre_g, fin_g]
    if bpf:
        ig = cond in ("ig_tcp", "ig_snap")
        if (pre_g if ig else pre_t) != 0:
            res["fail"].append(f"bpf: tracing programs loaded before the run (all {pre_t}, gadget {pre_g})")
        if not ig and fin_t != 0:
            res["fail"].append(f"bpf: {fin_t} tracing programs at the end of a {cond} run")
        if ig and (cond == "ig_tcp") != bool(fin_g):
            res["fail"].append(f"bpf: {fin_g} gadget programs at the end of a {cond} run")
        if ig and not pre_t:
            res["fail"].append("bpf: IG DaemonSet on but its standing programs are missing")
    rs = int(float((meta.get("kv") or {}).get("app_restarts_during_run", 0) or 0))
    if rs > 0:
        res["fail"].append(f"app containers restarted {rs} times during the run")
    host = meta.get("host") or {}
    res["info"]["play_id"] = host.get("play_id")
    if meta.get("params", {}).get("idle_s") and not ("idle_start" in ph and "idle_end" in ph):
        res["fail"].append("idle segment missing")

    # ---- samples: coverage, observer presence, cp-01 CPU
    lo, hi = ph.get("steady_start", 0) + 15, ph.get("steady_start", 0) + meta["params"]["steady_s"] - 10
    interval = meta["params"].get("sample_s", 5)
    offsets = (meta.get("nodes") or {}).get("clock_offset_s", {})
    seen = {"hubble-relay": 0, "otterize": 0, "gadget": 0, "pb-hubble": 0, "pb-igtcp": 0}
    cov = {}
    cp_ticks = []
    ncpu_cp = None
    for node in meta["nodes"]["list"]:
        p = node_samples(run, node)
        if not p:
            res["fail"].append(f"no samples from {node}")
            continue
        info = rd_json(p.replace(".gz", "") + ".info.json") or rd_json(os.path.join(run, f"samples-{node}.csv.info.json")) or {}
        off = offsets.get(node, 0.0)
        ts_all = set()
        for r in sample_rows(p):
            t = float(r["ts"]) - off
            if r["kind"] == "node" and r["id"] == "node":
                ts_all.add(t)
                if node == meta["nodes"]["cp"]:
                    cp_ticks.append((t, int(r["cpu_usec"] or 0)))
                continue
            if not lo <= t <= hi:
                continue
            pod, rns, ident = r["pod"], r["ns"], r["id"]
            if rns == "kube-system" and pod.startswith("hubble-relay"):
                seen["hubble-relay"] += 1
            elif rns == "otterize-system":
                seen["otterize"] += 1
            elif rns == "gadget":
                seen["gadget"] += 1
            elif ident.startswith("pb-hubble"):
                seen["pb-hubble"] += 1
            elif ident.startswith("pb-igtcp"):
                seen["pb-igtcp"] += 1
        ts = sorted(x for x in ts_all if lo - interval <= x <= hi + interval)
        gaps = [b - a for a, b in zip(ts, ts[1:])]
        first = (ts[0] - lo) if ts else None
        last = (hi - ts[-1]) if ts else None
        cov[node] = {"ticks": len(ts), "max_gap_s": round(max(gaps), 1) if gaps else None,
                     "start_lag_s": round(first, 1) if first is not None else None,
                     "end_lag_s": round(last, 1) if last is not None else None,
                     "sampler_cpu_pct_core": info.get("own_cpu_pct_of_core")}
        if not ts or (gaps and max(gaps) > 2 * interval + 1) or first > interval + 1 or last > interval + 1:
            res["fail"].append(f"sampler coverage {node}: {cov[node]}")
        if node == meta["nodes"]["cp"]:
            ncpu_cp = info.get("ncpu") or 2
    res["info"]["coverage"] = cov
    res["info"]["observer_rows_in_window"] = seen
    for key, want in (("hubble-relay", want_h), ("pb-hubble", want_h), ("otterize", want_o),
                      ("gadget", want_g), ("pb-igtcp", cond == "ig_tcp")):
        if bool(seen[key]) != bool(want):
            res["fail"].append(f"samples: {key} rows={seen[key]} in {cond}")

    def cp_util(a, b):
        pts = sorted(x for x in cp_ticks if a <= x[0] <= b)
        if len(pts) < 2:
            return None, None
        per = [(q[1] - p[1]) / ((q[0] - p[0]) * 1e6 * ncpu_cp) * 100 for p, q in zip(pts, pts[1:]) if q[0] > p[0]]
        tot = (pts[-1][1] - pts[0][1]) / ((pts[-1][0] - pts[0][0]) * 1e6 * ncpu_cp) * 100
        return round(tot, 1), round(max(per), 1)
    cp_ticks.sort()
    res["info"]["cp01_cpu_steady_pct"] = cp_util(lo, hi)[0]
    tps = []
    for t in meta.get("tp_tests", []):
        mean_u, max_u = cp_util(t.get("start") or 0, t.get("end") or 0)
        try:
            pf = A.parse_fixed_count(open(os.path.join(run, t["log"])).read()) or {}
        except OSError:
            pf = {}
        n_all = (pf.get("n_2xx") or 0) + (pf.get("n_other") or 0) + (pf.get("n_err") or 0)
        frac = 100.0 * (pf.get("n_2xx") or 0) / n_all if n_all else 0.0
        tps.append({"test": f"{t['mode']}-{t['i']}", "total_s": pf.get("total_s"), "rps": pf.get("rps"),
                    "pct_2xx": round(frac, 2), "n_2xx": pf.get("n_2xx"), "n": t.get("n"),
                    "cp01_cpu_mean_pct": mean_u, "cp01_cpu_max_tick_pct": max_u})
        if frac <= 99.0 or (pf.get("n_2xx") or 0) < 0.99 * (t.get("n") or 0):
            res["fail"].append(f"tp {t['mode']}-{t['i']}: {frac:.1f}% 2xx, n_2xx={pf.get('n_2xx')}")
        if mean_u is None or mean_u >= cp_max:
            res["fail"].append(f"tp {t['mode']}-{t['i']}: cp-01 CPU {mean_u}% (limit {cp_max}%)")
    res["info"]["tp"] = tps

    # ---- capture outputs
    kv = meta.get("kv", {})
    hub_lines = int(kv.get("client_out.hubble.json.lines", 0) or 0)
    flows = 0.0
    for node in meta["nodes"]["list"]:
        a = A.prom_sum(os.path.join(run, "metrics", f"steady_pre.{node}.hubble.prom"), "hubble_flows_processed_total")
        b = A.prom_sum(os.path.join(run, "metrics", f"steady_post.{node}.hubble.prom"), "hubble_flows_processed_total")
        if a is not None and b is not None:
            flows += b - a
    ig_lines = int(kv.get("client_out.ig_tcp.json.lines", 0) or 0)
    snap = rd_json(os.path.join(run, "ig_snap.json"))
    snap_n = len(snap) if isinstance(snap, list) else 0
    t1 = rd_json(os.path.join(run, "otterize_t1.json")) or {}
    intents = [x for x in ((t1.get("data") or {}).get("serviceIntents") or [])
               if (x.get("client") or {}).get("namespace") == ns]
    n_int = sum(len(x.get("intents") or []) for x in intents)
    res["info"].update({"hubble_client_lines": hub_lines, "hubble_flows_processed_window": flows,
                        "ig_tcp_lines": ig_lines, "ig_snap_entries": snap_n,
                        "otterize_t1_clients": len(intents), "otterize_t1_intents": n_int})
    for name, val, want in (("hubble client lines", hub_lines, want_h), ("hubble flows metric", flows, want_h),
                            ("ig_tcp lines", ig_lines, cond == "ig_tcp"), ("ig_snap entries", snap_n, cond == "ig_snap"),
                            ("otterize intents", n_int, want_o)):
        if bool(val > 0) != bool(want):
            res["fail"].append(f"{name}={val} in {cond}")

    st = None
    try:
        st = A.parse_steady(open(os.path.join(run, "steady.log")).read())
    except OSError:
        pass
    res["info"]["steady"] = {k: (st or {}).get(k) for k in ("rps", "fail_pct", "p50_ms", "p95_ms", "p99_ms", "requests")}
    res["info"]["warnings"] = meta.get("warnings", [])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--cp-max", type=float, default=75.0)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    root = a.root
    if os.path.isdir(os.path.join(root, "results")):
        root = os.path.join(root, "results")
    runs = []
    for app in sorted(os.listdir(root)):
        for rep in sorted(os.listdir(os.path.join(root, app)) if os.path.isdir(os.path.join(root, app)) else []):
            if re.match(r"(rep|cycle)\d+$", rep):
                for c in CONDS:
                    d = os.path.join(root, app, rep, c)
                    if os.path.isdir(d):
                        runs.append(d)
    out = [check_run(r, a.cp_max, root) for r in runs]
    print("| Run | Status | Checks | cp-01 CPU steady / TP mean (max tick) | TP 2xx % | hubble lines / flows | IG tcp / snap | Otterize intents | Steady req/s, fail % |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in out:
        i = r["info"]
        tp = "; ".join(f"{t['test']} {t['cp01_cpu_mean_pct']} ({t['cp01_cpu_max_tick_pct']})" for t in i.get("tp", []))
        tp2 = "; ".join(f"{t['test']} {t['pct_2xx']}" for t in i.get("tp", []))
        st = i.get("steady") or {}
        print(f"| {r['run']} | {r['status']} | {'OK' if not r['fail'] else 'FAIL: ' + '; '.join(r['fail'])} | "
              f"{i.get('cp01_cpu_steady_pct')} / {tp} | {tp2} | {i.get('hubble_client_lines')} / {i.get('hubble_flows_processed_window')} | "
              f"{i.get('ig_tcp_lines')} / {i.get('ig_snap_entries')} | {i.get('otterize_t1_intents')} | "
              f"{A.f(st.get('rps'), 2)}, {A.f(st.get('fail_pct'), 1)} |")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=1)
    return 1 if any(r["fail"] for r in out) else 0


if __name__ == "__main__":
    sys.exit(main())
