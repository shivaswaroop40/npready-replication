#!/usr/bin/env python3
"""analyze.py <results_root> [--out DIR] [--short] [--trim-head S] [--trim-tail S]

Reads the run dirs <results_root>/<app>/rep<r>/<cond>/ pulled by bin/collect.sh and writes
Markdown + CSV tables and RESULTS-PERF.md to <results_root>/analysis/ (or --out).
Interleaved cycles (<app>/cycle<k>/<cond>/, run_matrix.sh --cycles) are analysed separately, with
the same tables (a cycle is the block a rep is) plus per-cycle paired deltas with Holm across
techniques and a drift diagnostic, into <out>/cycles/ (RESULTS-CYCLES.md).
Host-speed canary (canary-<node>.csv, bin/canary.py), where present: mean speed per node and
segment, and every CPU and fixed-count number also canary-normalised (x the segment's speed / the
app's median speed), side by side with the raw one. Runs without canary data give the old outputs.

Per run, from the cgroup samples, cut by the phases in meta.json:
  - steady window: mean, within-window SD (5-s bins), peak and slope of CPU (cores) and memory
    (MiB working set = memory.current - inactive_file; anon too) per component, group and node
    scope (cluster, workers, cp); generator req/s and latency; steal; flows/s (pod-netns TCP
    accepts) minus the background rate measured in the idle segment;
  - idle segment (observer on, app up, no load): the standing cost of each condition;
  - each fixed-count test: CPU per group, app CFS throttling and the bottleneck container,
    connections per request; observer and node CPU per request and per new connection;
  - ig_snap: standing cost and CPU per snapshot, separately; Hubble flow mix and lost events;
    client events/s inside the analysis window (client_bins.json).
Per (app, condition): mean +- SD over repetitions; the main estimate of every overhead is the
paired per-rep difference (technique minus the same rep's baseline) with a t-based 95% CI
(df = n-1) and a paired t-test; Welch's test on the run values is kept as a second check.
"n.s." = the 95% CI of the paired difference includes 0. Four primary endpoints per technique
get Holm-adjusted p-values; everything else is exploratory. Fixed-count time in GoLeash
Table-5 format (mean +- SD over all executions, plus the SD of run means). Projection to
test-cluster (an estimate, with an upper bound and an observer+indirect variant).

Standard library only. scipy.stats is used for Welch's t-test when importable; otherwise a
built-in Student-t CDF gives the same p-values.
"""
import argparse
import bisect
import csv
import datetime
import gzip
import json
import math
import os
import re
import statistics
import sys
from collections import defaultdict

CONDS = ["baseline", "hubble", "hubble_agent", "otterize", "ig_tcp", "ig_snap"]
TECHS = CONDS[1:]
LABEL = {"baseline": "baseline", "hubble": "Hubble", "hubble_agent": "Hubble (agent only)", "otterize": "Otterize",
         "ig_tcp": "IG trace_tcp", "ig_snap": "IG snapshot_socket"}
MODES = ["keepalive", "newconn"]
MIB = 1024.0 * 1024.0

# test-cluster (OVH, deleted 2026-10-02): 3 x c3-4 control planes, 3 x b3-16-flex workers.
# Memory: worker capacity 15989976Ki each (REBUILD-SPEC section 2); a 4 GB c3-4 shows about
# 3.75 GiB capacity (estimate), so about 57 GiB in all rather than the nominal 60.
THESIS = {"cp_nodes": 3, "worker_nodes": 3, "vcpu": 3 * 2 + 3 * 4,
          "mem_gib": round(3 * 15989976 / 1048576 + 3 * 3.75, 1)}
# thesis journey-A event rates (captureA, first to last event, all observers on together):
# Hubble client lines/s and IG trace_tcp lines/s for the app namespace
THESIS_RATES = {"boutique": (33.2, 5.7), "bank": (101.3, 28.8), "dsb": (354.0, 76.1),
                "otel": (72.3, 3.8), "teastore": (44.7, 15.7)}
# primary endpoints (Holm-adjusted per app over 4 techniques x 4 endpoints); the rest is exploratory
# Decided 2026-10-03 ~09:30Z, with 2-3 of 10 cycles in (FIXLOG "Primary endpoints"): observer CPU (drifts
# least; cluster busy stays as a secondary column) and observer anonymous memory (working set swings with
# reclaimable page cache: IG +349 vs +122 MiB WS in two cycles, anon +139 both times).
PRIMARY = [("cpu.cluster.observer", "Δ observer CPU"), ("anon.cluster.observer", "Δ observer anon memory"),
           ("tp.keepalive.time_s", "fixed-count time, keep-alive"), ("tp.newconn.time_s", "fixed-count time, new conn")]

OBS_INCLUSTER = ["cilium-agent", "cilium-envoy", "cilium-operator", "hubble-relay", "hubble-ui",
                 "otterize-mapper", "otterize-sniffer", "otterize-other", "gadget"]
CLIENTS = ["client-hubble", "client-ig", "client-otterize", "client-other"]
GROUPS = {
    "observer": OBS_INCLUSTER + CLIENTS,
    "observer_incluster": OBS_INCLUSTER,
    "clients": CLIENTS,
    "app": ["app"],
    "loadgen": ["loadgen"],
    "k8s_system": ["k3s", "k8s-addons"],
    "os": ["os"],
    "harness": ["harness"],
    "unmapped": ["unmapped"],
    "node": ["node"],
}
# projection: DaemonSets on every test-cluster node, sniffer on the workers only, rest singletons
DS_ALL_NODES = {"cilium-agent", "cilium-envoy", "gadget"}
DS_WORKERS = {"otterize-sniffer"}
BREAKDOWN = OBS_INCLUSTER + CLIENTS + ["app", "loadgen", "k3s", "k8s-addons", "os", "harness",
                                       "unmapped", "node"]

# --------------------------------------------------------------------------------------------
# statistics


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def sd(xs):
    xs = [x for x in xs if x is not None]
    return statistics.stdev(xs) if len(xs) >= 2 else None


def _betacf(a, b, x):
    tiny, eps = 1e-300, 3e-16
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def betainc(a, b, x):
    """Regularised incomplete beta I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x)
    bt = math.exp(lbt)
    if x < (a + 1.0) / (a + b + 2.0):
        return bt * _betacf(a, b, x) / a
    return 1.0 - bt * _betacf(b, a, 1.0 - x) / b


try:
    from scipy import stats as _scipy_stats  # type: ignore
except Exception:  # noqa: BLE001
    _scipy_stats = None


def t_cdf(t, df):
    """Student-t CDF."""
    if df <= 0:
        return None
    x = df / (df + t * t)
    tail = 0.5 * betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t > 0 else tail


def t_ppf(q, df):
    """Student-t quantile by bisection (q in (0, 1))."""
    if _scipy_stats is not None:
        return float(_scipy_stats.t.ppf(q, df))
    lo, hi = -1e3, 1e3
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < q:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def paired_stats(ds):
    """mean, SD, 95% CI (t, df = n-1) and two-sided p of a list of paired differences."""
    ds = [d for d in ds if d is not None]
    n = len(ds)
    out = {"n": n, "mean": mean(ds), "sd": sd(ds), "lo": None, "hi": None, "p": None}
    if n >= 2:
        s = statistics.stdev(ds)
        se = s / math.sqrt(n)
        q = t_ppf(0.975, n - 1)
        out["lo"], out["hi"] = out["mean"] - q * se, out["mean"] + q * se
        if se > 0:
            t = out["mean"] / se
            out["p"] = 2.0 * (1.0 - t_cdf(abs(t), n - 1))
    return out


def wilcoxon_p(ds):
    """Two-sided Wilcoxon signed-rank p for paired differences (zeros dropped). Exact distribution of
    W+ when there are no ties among |d|, normal approximation with tie correction otherwise."""
    ds = [d for d in ds if d is not None and d != 0]
    n = len(ds)
    if n < 2:
        return None
    order = sorted(range(n), key=lambda i: abs(ds[i]))
    ranks = [0.0] * n
    i = 0
    ties = []
    while i < n:
        j = i
        while j + 1 < n and abs(ds[order[j + 1]]) == abs(ds[order[i]]):
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = r
        if j > i:
            ties.append(j - i + 1)
        i = j + 1
    wplus = sum(r for r, d in zip(ranks, ds) if d > 0)
    total = n * (n + 1) / 2.0
    if not ties:
        counts = [1] + [0] * int(total)          # number of sign patterns giving each W+
        for k in range(1, n + 1):
            for w in range(int(total), k - 1, -1):
                counts[w] += counts[w - k]
        allp = 2 ** n
        w = int(round(wplus))
        lo = sum(counts[:w + 1]) / allp
        hi = sum(counts[w:]) / allp
        return min(1.0, 2.0 * min(lo, hi))
    mu = total / 2.0
    var = n * (n + 1) * (2 * n + 1) / 24.0 - sum(t ** 3 - t for t in ties) / 48.0
    if var <= 0:
        return None
    z = (abs(wplus - mu) - 0.5) / math.sqrt(var)
    return min(1.0, math.erfc(max(z, 0.0) / math.sqrt(2.0)))


def holm(ps):
    """Holm step-down adjusted p-values for a list (None entries are kept as None)."""
    idx = sorted((p, i) for i, p in enumerate(ps) if p is not None)
    m = len(idx)
    adj = [None] * len(ps)
    run = 0.0
    for k, (p, i) in enumerate(idx):
        run = max(run, min(1.0, (m - k) * p))
        adj[i] = run
    return adj


def welch_p(a, b):
    """Two-sided Welch t-test p-value, or None if it cannot be computed."""
    a = [x for x in a if x is not None]
    b = [x for x in b if x is not None]
    if len(a) < 2 or len(b) < 2:
        return None
    va, vb = statistics.variance(a), statistics.variance(b)
    se2 = va / len(a) + vb / len(b)
    if se2 == 0:
        return None
    if _scipy_stats is not None:
        return float(_scipy_stats.ttest_ind(a, b, equal_var=False).pvalue)
    t = (statistics.fmean(a) - statistics.fmean(b)) / math.sqrt(se2)
    df = se2 ** 2 / ((va / len(a)) ** 2 / (len(a) - 1) + (vb / len(b)) ** 2 / (len(b) - 1))
    return betainc(df / 2.0, 0.5, df / (df + t * t))


# --------------------------------------------------------------------------------------------
# parsers for generator / fixed-count output

def _num(s):
    try:
        v = float(s)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def _to_ms(v, unit):
    return float(v) * {"us": 0.001, "ms": 1.0, "s": 1000.0, "m": 60000.0, "h": 3600000.0}[unit]


def _to_s(v, unit):
    return float(v) * {"us": 1e-6, "ms": 1e-3, "s": 1.0, "m": 60.0, "h": 3600.0}[unit]


def parse_locust_csv(text):
    lines = text.splitlines()
    found = None
    for i, line in enumerate(lines):
        if line.startswith("Type,Name,Request Count"):
            header = next(csv.reader([line]))
            rows = []
            for l2 in lines[i + 1:]:
                try:
                    r = next(csv.reader([l2]))
                except (StopIteration, csv.Error):
                    break
                if len(r) != len(header):
                    break
                rows.append(dict(zip(header, r)))
            agg = [r for r in rows if r.get("Name") == "Aggregated"]
            if agg:
                found = agg[-1]
    if not found:
        return None
    req = _num(found.get("Request Count"))
    fail = _num(found.get("Failure Count"))
    return {"kind": "locust", "requests": req, "failures": fail,
            "fail_pct": 100.0 * fail / req if req else None,
            "rps": _num(found.get("Requests/s")), "avg_ms": _num(found.get("Average Response Time")),
            "p50_ms": _num(found.get("50%")), "p95_ms": _num(found.get("95%")),
            "p99_ms": _num(found.get("99%"))}


def parse_locust_history(text):
    """locust --csv ..._stats_history.csv -> [(unix_ts, total_requests, total_failures)] (Aggregated)."""
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        if line.startswith("Timestamp,User Count,Type,Name"):
            header = next(csv.reader([line]))
            try:
                it, ir, iff = header.index("Timestamp"), header.index("Total Request Count"), header.index("Total Failure Count")
                iname = header.index("Name")
            except ValueError:
                return []
            for l2 in lines[i + 1:]:
                try:
                    r = next(csv.reader([l2]))
                except (StopIteration, csv.Error):
                    break
                if len(r) != len(header):
                    break
                if r[iname] == "Aggregated":
                    t, n, f_ = _num(r[it]), _num(r[ir]), _num(r[iff])
                    if t is not None and n is not None:
                        out.append((t, n, f_ or 0.0))
    return out


def window_rate(hist, lo, hi):
    """requests/s and failure % between the history rows closest inside [lo, hi]."""
    rows = [h for h in hist if lo <= h[0] <= hi]
    if len(rows) < 2 or rows[-1][0] <= rows[0][0]:
        return None, None
    dn = rows[-1][1] - rows[0][1]
    df = rows[-1][2] - rows[0][2]
    return dn / (rows[-1][0] - rows[0][0]), (100.0 * df / dn if dn > 0 else None)


def parse_locust_table(text):
    """Fallback: the summary tables locust prints in --headless mode."""
    out = None
    agg_re = re.compile(r"^\s*Aggregated\s+(\d+)\s+(\d+)\(([\d.]+)%\)\s*\|\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)"
                        r"\s*\|\s*([\d.]+)\s+([\d.]+)", re.M)
    for m in agg_re.finditer(text):
        out = {"kind": "locust-table", "requests": float(m.group(1)), "failures": float(m.group(2)),
               "fail_pct": float(m.group(3)), "avg_ms": float(m.group(4)), "p50_ms": float(m.group(7)),
               "rps": float(m.group(8)), "p95_ms": None, "p99_ms": None}
    if out is None:
        return None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if "50%" in line and "99%" in line and "Name" in line:
            cols = line.split()
            pcols = [c for c in cols if c.endswith("%")]
            for l2 in lines[i + 1:i + 60]:
                if l2.strip().startswith("Aggregated"):
                    vals = l2.split()[1:]
                    for c, v in zip(pcols, vals):
                        if c == "50%":
                            out["p50_ms"] = _num(v)
                        elif c == "95%":
                            out["p95_ms"] = _num(v)
                        elif c == "99%":
                            out["p99_ms"] = _num(v)
                    break
    return out


def _wrk2_segment(seg):
    pct = {}
    for m in re.finditer(r"^\s*([\d.]+)%\s+([\d.]+)(us|ms|s|m)\s*$", seg, re.M):
        pct.setdefault(float(m.group(1)), _to_ms(m.group(2), m.group(3)))
    # wrk2 prints no 95% line, and a log tail may hold only the detailed spectrum
    # (Value(ms) Percentile TotalCount 1/(1-P)): fill missing quantiles from the spectrum
    spec = [(float(m.group(2)), float(m.group(1))) for m in re.finditer(
        r"^\s+([\d.]+)\s+(0\.\d+|1\.0+)\s+(\d+)\s+([\d.]+|inf)\s*$", seg, re.M)]
    for q in (50.0, 95.0, 99.0):
        if q in pct:
            continue
        hit = [v for p_, v in spec if p_ >= q / 100.0]
        if hit and spec[0][0] <= q / 100.0:
            pct[q] = hit[0]
    m = re.search(r"(\d+)\s+requests in\s+([\d.]+)(us|ms|s|m|h)", seg)
    req = float(m.group(1)) if m else None
    dur = _to_s(m.group(2), m.group(3)) if m else None
    m = re.search(r"Requests/sec:\s+([\d.]+)", seg)
    rps = float(m.group(1)) if m else None
    errs = 0.0
    m = re.search(r"Socket errors: connect (\d+), read (\d+), write (\d+), timeout (\d+)", seg)
    if m:
        errs += sum(float(x) for x in m.groups())
    m = re.search(r"Non-2xx or 3xx responses:\s+(\d+)", seg)
    if m:
        errs += float(m.group(1))
    return {"pct": pct, "req": req, "dur": dur, "rps": rps, "errs": errs}


def parse_wrk2(text):
    marker = "Latency Distribution (HdrHistogram - Recorded Latency)"
    if marker in text:
        parts = [_wrk2_segment(seg) for seg in text.split(marker)[1:]]
    elif re.search(r"\d+\s+requests in\s+[\d.]+(us|ms|s|m|h)", text) and "Requests/sec:" in text:
        parts = [_wrk2_segment(text)]
    else:
        return None
    req = sum(p["req"] or 0 for p in parts)
    dur = sum(p["dur"] or 0 for p in parts)
    errs = sum(p["errs"] for p in parts)

    def wavg(q):
        num = den = 0.0
        for p in parts:
            if q in p["pct"] and p["req"]:
                num += p["pct"][q] * p["req"]
                den += p["req"]
        return num / den if den else None

    rps = req / dur if dur else (parts[-1]["rps"] if parts else None)
    return {"kind": "wrk2", "segments": len(parts), "requests": req or None, "failures": errs,
            "fail_pct": 100.0 * errs / req if req else None, "rps": rps, "avg_ms": None,
            "p50_ms": wavg(50.0), "p95_ms": wavg(95.0), "p99_ms": wavg(99.0)}


def parse_steady(text):
    for f in (parse_locust_csv, parse_wrk2, parse_locust_table):
        r = f(text)
        if r and r.get("rps") is not None:
            return r
    return None


def parse_fixed_count(text):
    """hey / oha / ab summary -> dict, or None."""
    r = {"tool": None, "total_s": None, "rps": None, "p50_ms": None, "p95_ms": None,
         "p99_ms": None, "n_2xx": None, "n_other": 0, "n_err": 0}
    m = re.search(r"^\s*Total:\s+([\d.]+)\s*secs", text, re.M)
    if m:
        r["tool"] = "hey"
        r["total_s"] = float(m.group(1))
        m = re.search(r"Requests/sec:\s+([\d.]+)", text)
        r["rps"] = float(m.group(1)) if m else None
        for m in re.finditer(r"^\s*([\d.]+)%+ in ([\d.]+) secs", text, re.M):
            q = float(m.group(1))
            for key, want in (("p50_ms", 50.0), ("p95_ms", 95.0), ("p99_ms", 99.0)):
                if abs(q - want) < 1e-6:
                    r[key] = float(m.group(2)) * 1000.0
        codes = {int(c): int(n) for c, n in re.findall(r"\[(\d{3})\]\s+(\d+)\s+responses", text)}
        r["codes"] = codes
        r["n_2xx"] = sum(n for c, n in codes.items() if 200 <= c < 300)
        r["n_other"] = sum(n for c, n in codes.items() if not 200 <= c < 300)
        if "Error distribution:" in text:
            tail = text.split("Error distribution:", 1)[1]
            r["n_err"] = sum(int(n) for n in re.findall(r"^\s*\[(\d+)\]\s", tail, re.M))
        return r
    m = re.search(r"Time taken for tests:\s+([\d.]+)\s*seconds", text)
    if m:
        r["tool"] = "ab"
        r["total_s"] = float(m.group(1))
        m = re.search(r"Requests per second:\s+([\d.]+)", text)
        r["rps"] = float(m.group(1)) if m else None
        comp = re.search(r"Complete requests:\s+(\d+)", text)
        failed = re.search(r"Failed requests:\s+(\d+)", text)
        non2 = re.search(r"Non-2xx responses:\s+(\d+)", text)
        c = int(comp.group(1)) if comp else 0
        f = int(failed.group(1)) if failed else 0
        n2 = int(non2.group(1)) if non2 else 0
        r["n_2xx"] = max(0, c - f - n2)
        r["n_other"] = n2
        r["n_err"] = f
        for m in re.finditer(r"^\s*(\d+)%\s+(\d+)", text, re.M):
            q = int(m.group(1))
            if q in (50, 95, 99):
                r[f"p{q}_ms"] = float(m.group(2))
        return r
    return None


def parse_ct(path):
    """/proc/net/stat/nf_conntrack (summed over CPUs) or conntrack -S -> (ts, {counter: value})."""
    try:
        txt = open(path).read()
    except OSError:
        return None, {}
    m = re.search(r"# ts=([\d.]+)", txt)
    ts = float(m.group(1)) if m else None
    lines = txt.splitlines()
    vals = {}
    for i, line in enumerate(lines):
        if line.split()[:1] == ["entries"]:
            names = line.split()
            for l2 in lines[i + 1:]:
                if l2.startswith("#") or not l2.strip():
                    break
                hexes = l2.split()
                if len(hexes) != len(names):
                    break
                for n, h in zip(names, hexes):
                    v = int(h, 16)
                    if n == "entries":
                        vals[n] = v
                    else:
                        vals[n] = vals.get(n, 0) + v
            break
    if "insert" not in vals:
        for line in lines:
            if line.startswith("cpu="):
                for k, v in re.findall(r"(\w+)=(\d+)", line):
                    if k != "cpu":
                        vals[k] = vals.get(k, 0) + int(v)
    # pod network namespaces' TCP counters (lib.sh pb_ct_snap), the flow count on kernel 6.12
    m = re.search(r"# podnet_tcp active_opens=(\d+) passive_opens=(\d+) netns=(\d+)", txt)
    if m:
        vals["podnet_active_opens"] = int(m.group(1))
        vals["podnet_passive_opens"] = int(m.group(2))
        vals["podnet_netns"] = int(m.group(3))
    per_ns = {ns: int(pv) for ns, _a, pv in re.findall(r"^# podnet_ns (\S+) (\d+) (\d+)$", txt, re.M)}
    if per_ns:
        vals["_podnet_ns"] = per_ns
    return ts, vals


def prom_series(path, name):
    """-> [(labels dict, value)] for every series of one metric family."""
    try:
        txt = open(path).read()
    except OSError:
        return None
    out = []
    lab_re = re.compile(r'(\w+)="((?:[^"\\]|\\.)*)"')
    for line in txt.splitlines():
        if not line.startswith(name):
            continue
        rest = line[len(name):]
        if rest[:1] not in ("{", " "):
            continue
        labels = {}
        if rest.startswith("{"):
            body, _, rest = rest[1:].partition("} ")
            labels = dict(lab_re.findall(body))
        v = _num(rest.split()[-1]) if rest.split() else None
        if v is not None:
            out.append((labels, v))
    return out


def prom_sum(path, name):
    try:
        txt = open(path).read()
    except OSError:
        return None
    tot, seen = 0.0, False
    for line in txt.splitlines():
        if line.startswith(name) and (line[len(name):len(name) + 1] in ("{", " ")):
            v = _num(line.rsplit(None, 1)[-1])
            if v is not None:
                tot += v
                seen = True
    return tot if seen else None



# --------------------------------------------------------------------------------------------
# samples -> per-component series

def classify(kind, ident, ns, pod, container, app_ns, node, cp_node):
    if kind == "node":
        return "node" if ident == "node" else "steal"
    if kind == "slice":
        return None
    if kind == "client" or ident.startswith("pb-"):
        if ident.startswith(("pb-scrape", "pb-canary")):
            return "harness"          # the 15-s metrics scraper and the host-speed canary run in every condition
        if ident.startswith("pb-hubble"):
            return "client-hubble"    # hubble observe and its kubectl port-forward
        if ident.startswith(("pb-igtcp", "pb-igsnap")):
            return "client-ig"
        if ident.startswith("pb-otterize"):
            return "client-otterize"
        return "client-other"
    if kind == "unit":
        if ident.startswith(("k3s", "containerd")):
            return "k3s"
        if ident.startswith("perfbench"):
            return "harness"
        return "os"
    if not ns and not pod:
        return "unmapped"
    if ns == "kube-system":
        if pod.startswith("cilium-envoy"):
            return "cilium-envoy"
        if pod.startswith("cilium-operator"):
            return "cilium-operator"
        if pod.startswith("hubble-relay"):
            return "hubble-relay"
        if pod.startswith("hubble-ui"):
            return "hubble-ui"
        if pod.startswith("cilium-") or container == "cilium-agent":
            return "cilium-agent"
        return "k8s-addons"
    if ns == "otterize-system":
        if "mapper" in pod:
            return "otterize-mapper"
        if "sniffer" in pod:
            return "otterize-sniffer"
        return "otterize-other"
    if ns == "gadget":
        return "gadget"
    if app_ns and ns == app_ns:
        return "loadgen" if (pod.startswith("pb-") or node == cp_node) else "app"
    return "k8s-addons"


def _open(path):
    return gzip.open(path, "rt", newline="") if path.endswith(".gz") else open(path, newline="")


def read_ticks(path, offset, lo, hi, app_ns, node, cp_node):
    """-> sorted [(t, {key: (comp, cpu_usec, ws_bytes, throttled_usec, anon_bytes, label)})]
    for lo <= t <= hi (t on cp-01's clock)."""
    ticks = {}
    cache = {}
    with _open(path) as f:
        for row in csv.DictReader(f):
            try:
                t = float(row["ts"]) - offset
            except (KeyError, ValueError):
                continue
            if t < lo or t > hi:
                continue
            ck = (row["kind"], row["id"], row["ns"], row["pod"], row["container"])
            comp = cache.get(ck, "?")
            if comp == "?":
                comp = classify(*ck, app_ns, node, cp_node)
                cache[ck] = comp
            if comp is None:
                continue
            cpu = _num(row.get("cpu_usec"))
            cur = _num(row.get("mem_current"))
            inact = _num(row.get("mem_inactive_file"))
            if comp in ("node", "steal"):
                wsb = cur
            else:
                wsb = max(0.0, cur - (inact or 0.0)) if cur is not None else None
            thr = _num(row.get("throttled_usec"))
            anon = _num(row.get("mem_anon"))
            label = f"{row['pod']}/{row['container']}" if row.get("pod") else row["id"]
            ticks.setdefault(t, {})[(row["kind"], row["id"])] = (comp, cpu, wsb, thr, anon, label)
    return sorted(ticks.items())


# --------------------------------------------------------------------------------------------
# host-speed canary (bin/canary.py)

CANARY_MAX_PCT = 1.5        # canary cost above this % of one core is flagged
CANARY_MIN_SAMPLES = 2      # fewer kernel runs inside a segment: no speed for that segment


def read_canary(path, offset):
    """canary-<node>.csv(.gz) -> sorted [(t_mid, iterations, wall_ns, cpu_ns, cpu)], t_mid = middle
    of the kernel run on cp-01's clock. Broken or partial rows (a live copy) are skipped."""
    out = []
    try:
        with _open(path) as f:
            for row in csv.DictReader(f):
                try:
                    t = float(row["ts"]) - offset
                    it, w, c = int(row["iterations"]), int(row["wall_ns"]), int(row["cpu_ns"])
                except (KeyError, TypeError, ValueError):
                    continue
                if it > 0 and w > 0 and c > 0:
                    out.append((t - w / 2e9, it, w, c, row.get("cpu")))
    except (OSError, EOFError, ValueError):
        pass
    out.sort()
    return out


def canary_speed(samples, lo, hi):
    """-> (iterations per CPU-second, iterations per wall-second, kernel runs) over the kernel runs
    whose middle lies in [lo, hi] (ratio of sums), or (None, None, n) with too few runs."""
    ts = [x[0] for x in samples]
    sel = samples[bisect.bisect_left(ts, lo):bisect.bisect_right(ts, hi)]
    if len(sel) < CANARY_MIN_SAMPLES:
        return None, None, len(sel)
    it = float(sum(x[1] for x in sel))
    return it / (sum(x[3] for x in sel) / 1e9), it / (sum(x[2] for x in sel) / 1e9), len(sel)


def slice_ticks(ticks, lo, hi):
    ts = [t for t, _ in ticks]
    return ticks[bisect.bisect_left(ts, lo):bisect.bisect_right(ts, hi)]


NEW_CGROUP_MAX_CORES = 64.0


def node_series(ticks):
    """-> cpu intervals [(t_mid, dt, {comp: cores}, {comp: throttled s/s}, {label: throttled s/s})],
    mem ticks [(t, {comp: ws bytes}, {comp: anon bytes})].
    A cgroup that first appears after the first tick (a client scope or container created inside
    the segment) is counted from 0, so the CPU it used before its first sample is not lost."""
    cpu_iv, mem_t = [], []
    prev = None
    seen = set()
    for t, d in ticks:
        agg = defaultdict(float)
        anon = defaultdict(float)
        for comp, _cpu, wsb, _thr, an, _l in d.values():
            if wsb is not None:
                agg[comp] += wsb
            if an is not None and comp not in ("node", "steal"):
                anon[comp] += an
        mem_t.append((t, dict(agg), dict(anon)))
        if prev is not None:
            t0, d0 = prev
            dt = t - t0
            if dt > 0:
                rate = defaultdict(float)
                thr = defaultdict(float)
                thr_l = defaultdict(float)
                for key, (comp, cpu, _w, th, _a, label) in d.items():
                    p = d0.get(key)
                    if p is None:
                        if key in seen or cpu is None or comp in ("node", "steal"):
                            continue
                        p = (comp, 0.0, None, 0.0, None, label)     # new cgroup: counter started at 0
                        if cpu / dt / 1e6 > NEW_CGROUP_MAX_CORES:
                            continue
                    if cpu is None or p[1] is None:
                        continue
                    delta = cpu - p[1]
                    if delta >= 0:
                        rate[comp] += delta / dt / 1e6
                    if th is not None and p[3] is not None and th >= p[3]:
                        v = (th - p[3]) / dt / 1e6
                        thr[comp] += v
                        if comp == "app":
                            thr_l[label] += v
                cpu_iv.append(((t0 + t) / 2.0, dt, dict(rate), dict(thr), dict(thr_l)))
        seen.update(d.keys())
        prev = (t, d)
    return cpu_iv, mem_t


def wmean(pairs):
    """time-weighted mean of [(value, dt)]"""
    tot = sum(dt for _, dt in pairs)
    return sum(v * dt for v, dt in pairs) / tot if tot else None


def seg_means(series):
    """{"cpu": {comp: cores}, "mem": {comp: MiB}, "anon": {comp: MiB}, "thr": {comp: s/s},
    "thr_l": {label: s/s}, "dur": s} for one node's series over a segment."""
    cpu_iv, mem_t = series
    comps = set()
    for _, _, rate, _, _ in cpu_iv:
        comps.update(rate)
    out = {"cpu": {}, "mem": {}, "anon": {}, "thr": {}, "thr_l": {}, "dur": sum(dt for _, dt, _, _, _ in cpu_iv)}
    for c in comps:
        out["cpu"][c] = wmean([(rate.get(c, 0.0), dt) for _, dt, rate, _, _ in cpu_iv]) or 0.0
        out["thr"][c] = wmean([(th.get(c, 0.0), dt) for _, dt, _, th, _ in cpu_iv]) or 0.0
    labels = set()
    for _, _, _, _, tl in cpu_iv:
        labels.update(tl)
    for lb in labels:
        out["thr_l"][lb] = wmean([(tl.get(lb, 0.0), dt) for _, dt, _, _, tl in cpu_iv]) or 0.0
    mcomps = set()
    for _, agg, _ in mem_t:
        mcomps.update(agg)
    for c in mcomps:
        out["mem"][c] = mean([agg.get(c, 0.0) / MIB for _, agg, _ in mem_t]) or 0.0
        out["anon"][c] = mean([an.get(c, 0.0) / MIB for _, _, an in mem_t]) or 0.0
    return out


def grp(seg, nodes, comps, what="cpu"):
    return sum(sum(seg[n][what].get(c, 0.0) for c in comps) for n in nodes if n in seg)


def lin_slope(xs, ys):
    """least-squares slope dy/dx, or None"""
    if len(xs) < 3:
        return None
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else None


# --------------------------------------------------------------------------------------------
# one run

class Run:
    def __init__(self, app, rep, cond, path, layout="rep"):
        self.app, self.rep, self.cond, self.path = app, rep, cond, path
        self.layout = layout   # "rep" (rep<r>/) or "cycle" (cycle<k>/); rep holds k for a cycle
        self.status, self.reason = "INCOMPLETE", ""
        self.meta = {}
        self.m = {}            # flat numeric metrics
        self.info = {}         # non-numeric per-run facts (bottleneck names, host signature)
        self.comp_rows = []    # per node x component (steady window)
        self.tp_rows = []      # per fixed-count test
        self.flags = []        # data-quality notes
        self.excluded = False
        self.short = None
        self.host_sig = None
        self.nodes, self.workers = [], []
        self.canary_seg = {}   # segment -> {node: (speed_cpu, speed_wall, kernel runs, lo, hi)}
        self.canary_ref = {}   # node -> the app's median steady-window speed (set by normalise_by_canary)
        self.node_grp = {}     # node -> {group: steady-window cores}, for the per-node normalisation


HUB_CLASSES = ("app", "probe", "client_feedback", "other")


def hubble_class(lb, app_ns):
    src, dst = lb.get("source", ""), lb.get("destination", "")
    if "k8s-app=hubble-relay" in src or "k8s-app=hubble-relay" in dst:
        return "client_feedback"
    nsl = f"k8s:io.kubernetes.pod.namespace={app_ns}"
    if src == "reserved:host" or dst == "reserved:host":
        return "probe"
    if app_ns and (nsl in src or nsl in dst):
        return "app"
    return "other"


def analyze_run(run, trim_head, trim_tail, tp_tolerance=0.0):
    p = run.path
    if os.path.exists(os.path.join(p, "DONE")):
        run.status = "DONE"
    elif os.path.exists(os.path.join(p, "FAILED")):
        run.status = "FAILED"
        run.reason = open(os.path.join(p, "FAILED")).read().strip()[:300]
    try:
        run.meta = json.load(open(os.path.join(p, "meta.json")))
    except (OSError, ValueError):
        run.meta = {}
    run.short = bool(run.meta.get("short")) if run.meta else None
    if run.status != "DONE":
        run.excluded = True
        if not run.reason:
            run.reason = "no DONE or FAILED file (run interrupted)"
        return
    if not run.meta:
        run.excluded, run.reason = True, "DONE but meta.json missing or unreadable"
        return
    meta = run.meta
    params = meta.get("params", {})
    ph = meta.get("phases", {})
    steady_s = float(params.get("steady_s", 0))
    rs = _num((meta.get("kv") or {}).get("app_restarts_during_run"))
    if rs and rs > 0:   # the harness fails such runs since 2026-10-02; older ones are excluded here
        run.excluded, run.reason = True, f"app containers restarted {rs:.0f} times during the run"
        return
    if "steady_start" not in ph:
        run.excluded, run.reason = True, "no steady_start phase"
        return
    s0 = ph["steady_start"]
    end_nom = s0 + steady_s
    end_obs = ph.get("steady_job_complete") or end_nom
    ws, we = s0 + trim_head, min(end_nom, end_obs) - trim_tail
    run.m["window_s"] = we - ws
    if we - ws < 0.8 * (steady_s - trim_head - trim_tail):
        run.excluded, run.reason = True, f"steady window only {we - ws:.0f}s of {steady_s:.0f}s"
        return
    nodes_meta = meta.get("nodes", {})
    nodes = nodes_meta.get("list") or []
    cp = nodes_meta.get("cp") or "cp-01"
    offsets = nodes_meta.get("clock_offset_s", {})
    app_ns = meta.get("app_ns")
    interval = float(params.get("sample_s", 5))
    run_lo = min(v for v in ph.values() if isinstance(v, (int, float))) - 60
    run_hi = max(v for v in ph.values() if isinstance(v, (int, float))) + 60

    # host identity: one play and one set of machines per rep, or the paired deltas are confounded
    host = meta.get("host") or {}
    hn = host.get("nodes") or {}
    if hn:
        run.host_sig = (host.get("play_id"), tuple(sorted((n, (hn.get(n) or {}).get("machine_id")) for n in hn)))
        run.info["play_id"] = host.get("play_id")
        run.info["boot_ids"] = ",".join(str((hn.get(n) or {}).get("boot_id", ""))[:8] for n in sorted(hn))
        run.info["cpu_model"] = ";".join(sorted({str((hn.get(n) or {}).get("cpu_model")) for n in hn}))
        run.info["irq_time_accounting"] = ";".join(sorted({str(((hn.get(n) or {}).get("kconfig") or {}).get(
            "CONFIG_IRQ_TIME_ACCOUNTING")) for n in hn}))

    all_ticks, info_n = {}, {}
    for n in nodes:
        path = None
        for cand in (f"samples-{n}.csv.gz", f"samples-{n}.csv"):
            if os.path.exists(os.path.join(p, cand)):
                path = os.path.join(p, cand)
                break
        if path is None:
            run.excluded, run.reason = True, f"no samples from {n}"
            return
        info = {}
        try:
            info = json.load(open(os.path.join(p, f"samples-{n}.csv.info.json")))
        except (OSError, ValueError):
            pass
        info_n[n] = info
        all_ticks[n] = read_ticks(path, float(offsets.get(n, 0.0)), run_lo, run_hi, app_ns, n, cp)
        own = info.get("own_cpu_pct_of_core")
        if own is not None and own > 1.0:
            run.flags.append(f"sampler on {n} used {own:.2f}% of a core")
    canary = {}
    for n in nodes:
        for cand in (f"canary-{n}.csv.gz", f"canary-{n}.csv"):
            if os.path.exists(os.path.join(p, cand)):
                canary[n] = read_canary(os.path.join(p, cand), float(offsets.get(n, 0.0)))
                break
        try:
            cinfo = json.load(open(os.path.join(p, f"canary-{n}.csv.info.json")))
        except (OSError, ValueError):
            cinfo = {}
        own = cinfo.get("own_cpu_pct_of_core")
        if own is not None and own > CANARY_MAX_PCT:
            run.flags.append(f"host-speed canary on {n} used {own:.2f}% of a core (limit {CANARY_MAX_PCT}%)")
    if canary and len(canary) < len(nodes):
        run.flags.append(f"host-speed canary data missing from {', '.join(n for n in nodes if n not in canary)}")

    def series(lo, hi):
        return {n: node_series(slice_ticks(all_ticks[n], lo, hi)) for n in nodes}

    def segment(lo, hi):
        return {n: seg_means(s) for n, s in series(lo, hi).items()}

    per_node = {}
    for n in nodes:
        ticks = slice_ticks(all_ticks[n], ws, we)
        if len(ticks) < 0.8 * (we - ws) / interval:
            run.excluded, run.reason = True, f"samples from {n} cover only {len(ticks)} ticks"
            return
        cpu_iv, mem_t = node_series(ticks)
        per_node[n] = {"cpu": cpu_iv, "mem": mem_t, "info": info_n[n]}
    workers = [n for n in nodes if n != cp]
    run.nodes, run.workers = list(nodes), workers
    ncpu = {n: (per_node[n]["info"].get("ncpu") or _k8s_cpu(meta, n)) for n in nodes}
    memtot = {n: per_node[n]["info"].get("mem_total_bytes") for n in nodes}
    run.m["capacity.cpu.cluster"] = sum(v or 0 for v in ncpu.values())
    run.m["capacity.cpu.workers"] = sum(ncpu[n] or 0 for n in workers)
    run.m["capacity.mem.cluster"] = sum(v or 0 for v in memtot.values()) / MIB
    run.m["capacity.mem.workers"] = sum(memtot[n] or 0 for n in workers) / MIB

    # ---- steady window: per node x component
    node_comp_cpu, node_comp_mem, node_comp_anon = {}, {}, {}
    steals = []
    for n in nodes:
        sm = seg_means((per_node[n]["cpu"], per_node[n]["mem"]))
        node_comp_cpu[n], node_comp_mem[n], node_comp_anon[n] = sm["cpu"], sm["mem"], sm["anon"]
        for c in sorted(set(sm["cpu"]) | set(sm["mem"])):
            vals = [rate.get(c, 0.0) for _, _, rate, _, _ in per_node[n]["cpu"]]
            mvals = [agg.get(c, 0.0) / MIB for _, agg, _ in per_node[n]["mem"]]
            run.comp_rows.append({"node": n, "component": c, "cpu_cores_mean": sm["cpu"].get(c, 0.0),
                                  "cpu_cores_sd": sd(vals), "mem_mib_mean": sm["mem"].get(c, 0.0),
                                  "mem_mib_max": max(mvals) if mvals else None,
                                  "anon_mib_mean": sm["anon"].get(c)})
        if n in ncpu and ncpu[n]:
            stl = node_comp_cpu[n].get("steal", 0.0) / ncpu[n]
            run.m[f"steal_frac.{n}"] = stl
            steals.append(stl)
            if stl > 0.05:
                run.flags.append(f"{n}: CPU steal {100 * stl:.1f}% (noisy host)")
        run.m[f"app_throttled.{n}"] = sm["thr"].get("app", 0.0)
    run.m["steal.frac_mean"] = mean(steals)

    # scopes: mean = sum of node means; SD / peak / slope from 5-s bins summed over the scope's nodes
    scopes = {"cluster": nodes, "workers": workers, "cp": [cp] if cp in nodes else []}
    for scope, sn in scopes.items():
        if not sn:
            continue
        for g, comps in GROUPS.items():
            run.m[f"cpu.{scope}.{g}"] = sum(sum(node_comp_cpu[n].get(c, 0.0) for c in comps) for n in sn)
            run.m[f"mem.{scope}.{g}"] = sum(sum(node_comp_mem[n].get(c, 0.0) for c in comps) for n in sn)
            cbins = defaultdict(lambda: defaultdict(list))
            mbins = defaultdict(lambda: defaultdict(list))
            for n in sn:
                for tm, _, rate, _, _ in per_node[n]["cpu"]:
                    cbins[int((tm - ws) // interval)][n].append(sum(rate.get(c, 0.0) for c in comps))
                for t, agg, _ in per_node[n]["mem"]:
                    mbins[int((t - ws) // interval)][n].append(sum(agg.get(c, 0.0) for c in comps) / MIB)
            cser = [sum(mean(v) for v in b.values()) for b in cbins.values() if len(b) == len(sn)]
            mkeys = sorted(k for k, b in mbins.items() if len(b) == len(sn))
            mser = [sum(mean(v) for v in mbins[k].values()) for k in mkeys]
            run.m[f"cpu_sd.{scope}.{g}"] = sd(cser)
            run.m[f"mem_peak.{scope}.{g}"] = max(mser) if mser else None
            run.m[f"mem_sd.{scope}.{g}"] = sd(mser)
            if mser:
                run.m[f"mem_end.{scope}.{g}"] = mser[-1]
                sl = lin_slope([k * interval / 60.0 for k in mkeys], mser)
                run.m[f"mem_slope.{scope}.{g}"] = sl          # MiB per minute
            if g in ("observer", "observer_incluster"):
                run.m[f"anon.{scope}.{g}"] = sum(sum(node_comp_anon[n].get(c, 0.0) for c in comps) for n in sn)
    for c in BREAKDOWN:
        run.m[f"comp_cpu.{c}"] = sum(node_comp_cpu[n].get(c, 0.0) for n in nodes)
        run.m[f"comp_mem.{c}"] = sum(node_comp_mem[n].get(c, 0.0) for n in nodes)
    run.node_grp = {n: {g: sum(node_comp_cpu[n].get(c, 0.0) for c in comps) for g, comps in GROUPS.items()}
                    for n in nodes}

    # ---- idle segment (observer on, app up, no load): standing cost per node
    idle = None
    if "idle_start" in ph and "idle_end" in ph and ph["idle_end"] - ph["idle_start"] >= 2 * interval:
        idle = segment(ph["idle_start"] + 2.0, ph["idle_end"])
        if any(idle[n]["dur"] < interval for n in nodes):
            idle = None
            run.flags.append("idle segment has too few samples")
    if idle:
        for scope, sn in scopes.items():
            for g in ("observer", "observer_incluster", "clients", "app", "k8s_system", "node", "harness"):
                run.m[f"idle.cpu.{scope}.{g}"] = grp(idle, sn, GROUPS[g])
                run.m[f"idle.mem.{scope}.{g}"] = grp(idle, sn, GROUPS[g], "mem")
        for c in ("cilium-agent", "gadget", "otterize-sniffer", "k3s"):
            run.m[f"idle.comp_cpu.{c}"] = sum(idle[n]["cpu"].get(c, 0.0) for n in nodes)

    # ---- projection to test-cluster (estimate)
    # Main: the measured cost on the 3 bench nodes (it carries the whole app load, which
    # test-cluster split over its nodes too) plus, for each node test-cluster has in addition
    # (2 control planes, 1 worker), that node role's standing cost from the idle segment.
    # Upper: the earlier method, every test-cluster node costs what the bench node of its role
    # costs in the steady window (triples cp-01, which also carries the generator and clients).
    # Without an idle segment the steady values stand in for the idle ones (= upper).
    src = idle if idle else {n: {"cpu": node_comp_cpu[n], "mem": node_comp_mem[n]} for n in nodes}
    if not idle:
        run.flags.append("no idle segment: projection uses the steady window for the extra nodes (= upper bound)")
    extra_cp, extra_w = THESIS["cp_nodes"] - 1, THESIS["worker_nodes"] - len(workers)

    def proj(comps_ds_all, comps_ds_w, comps_single, what):
        cur = node_comp_cpu if what == "cpu" else node_comp_mem
        main = upper = 0.0
        for c in comps_ds_all:
            s_all = sum(cur[n].get(c, 0.0) for n in nodes)
            i_cp = src.get(cp, {}).get(what, {}).get(c, 0.0)
            i_w = mean([src[n][what].get(c, 0.0) for n in workers]) or 0.0
            main += s_all + extra_cp * i_cp + extra_w * i_w
            upper += THESIS["worker_nodes"] * (mean([cur[n].get(c, 0.0) for n in workers]) or 0.0) \
                + THESIS["cp_nodes"] * cur.get(cp, {}).get(c, 0.0)
        for c in comps_ds_w:
            s_w = sum(cur[n].get(c, 0.0) for n in workers)
            i_w = mean([src[n][what].get(c, 0.0) for n in workers]) or 0.0
            main += s_w + extra_w * i_w
            upper += THESIS["worker_nodes"] * (mean([cur[n].get(c, 0.0) for n in workers]) or 0.0)
        for c in comps_single:
            v = sum(cur[n].get(c, 0.0) for n in nodes)
            main += v
            upper += v
        return main, upper

    ds_all = [c for c in OBS_INCLUSTER if c in DS_ALL_NODES]
    ds_w = [c for c in OBS_INCLUSTER if c in DS_WORKERS]
    single = [c for c in OBS_INCLUSTER if c not in DS_ALL_NODES and c not in DS_WORKERS]
    run.m["proj.cpu"], run.m["proj.cpu_upper"] = proj(ds_all, ds_w, single, "cpu")
    run.m["proj.mem"], run.m["proj.mem_upper"] = proj(ds_all, ds_w, single, "mem")
    # observer + indirect: everything in the cluster except the bench's clients, generator and
    # harness (k3s/containerd/API server, kernel time, BPF work charged to the app's cgroups).
    # Node busy - those, per node; the extra test-cluster nodes get the idle-segment value.
    excl_c = set(CLIENTS) | {"loadgen", "harness"}

    def incl_node(n, d):
        return d[n]["cpu"].get("node", 0.0) - sum(d[n]["cpu"].get(c, 0.0) for c in excl_c)

    steady_d = {n: {"cpu": node_comp_cpu[n]} for n in nodes}
    i_src = idle if idle else steady_d
    run.m["proj.cpu_all"] = (sum(incl_node(n, steady_d) for n in nodes) + extra_cp * incl_node(cp, i_src)
                             + extra_w * (mean([incl_node(n, i_src) for n in workers]) or 0.0))

    # ---- steady generator
    steady_dur = (end_obs - s0) if ph.get("steady_job_complete") else steady_s
    st, stext = None, ""
    try:
        stext = open(os.path.join(p, "steady.log"), errors="replace").read()
        st = parse_steady(stext)
    except OSError:
        pass
    if st:
        for k in ("rps", "p50_ms", "p95_ms", "p99_ms", "fail_pct", "requests"):
            run.m[f"steady.{k}"] = st.get(k)
        run.m["steady.kind"] = st.get("kind")
        run.m["steady.rps_job"] = st.get("rps")
        wr, wf = window_rate(parse_locust_history(stext), ws, we)
        if wr is not None:
            run.m["steady.rps"] = wr
            run.m["steady.fail_pct"] = wf
            run.m["steady.rps_source"] = "history-window"
    else:
        run.flags.append("steady generator output not parsed (latency/throughput missing)")

    # ---- background connection rate (kubelet probes etc.), from the idle segment or the TP pauses
    bg = None
    fk_all = flow_key(p, "steady_pre", workers)
    dt_i, d_i = ct_delta(p, "idle_pre", "idle_post", workers)
    if d_i is not None and dt_i and dt_i > 10:
        bg = d_i / dt_i
        run.m["flows.bg_source"] = "idle"
        if bg < 0:
            run.flags.append(f"background accepts fell during the idle segment ({bg:.2f}/s); set to 0")
            bg = 0.0
    tests = meta.get("tp_tests") or []
    if bg is None and len(tests) >= 2:
        rates = []
        ordered = sorted([t for t in tests if t.get("ct_prefix")], key=lambda t: t.get("created") or 0)
        for t1, t2 in zip(ordered, ordered[1:]):
            dt_p, d_p = ct_delta(p, t1["ct_prefix"].removeprefix("ct/") + ".post",
                                 t2["ct_prefix"].removeprefix("ct/") + ".pre", workers)
            if d_p is not None and dt_p and dt_p > 5:
                rates.append(max(0.0, d_p / dt_p))
        if rates:
            bg = statistics.median(rates)
            run.m["flows.bg_source"] = "tp-pauses"
    if bg is not None:
        run.m["flows.bg_per_s"] = bg

    # ---- fixed-count tests
    tp_n = int(params.get("tp_n", 0))
    if not tests:   # fall back to whatever logs exist
        for fn in sorted(os.listdir(os.path.join(p, "tp"))) if os.path.isdir(os.path.join(p, "tp")) else []:
            mm = re.match(r"(keepalive|newconn)-(\d+)\.log$", fn)
            if mm:
                tests.append({"mode": mm.group(1), "i": int(mm.group(2)), "log": f"tp/{fn}", "ok": True})
    idle_obs = grp(idle, nodes, GROUPS["observer"]) if idle else None
    idle_node = grp(idle, nodes, ["node"]) if idle else None
    by_mode = defaultdict(list)
    for t in tests:
        row = {"mode": t.get("mode"), "i": t.get("i"), "ok_harness": t.get("ok"), "valid": False,
               "why": ""}
        try:
            r = parse_fixed_count(open(os.path.join(p, t.get("log", "")), errors="replace").read())
        except OSError:
            r = None
        n_req = t.get("n") or tp_n
        if r is None:
            row["why"] = "output not parsed"
        else:
            row.update({k: v for k, v in r.items() if k != "codes"})
            expect = int(_num(meta.get("app_env", {}).get("TP_EXPECT_STATUS")) or 200)
            got = r.get("codes", {}).get(expect) if "codes" in r else r["n_2xx"]
            row["n_expected_status"] = got
            row["non2xx_pct"] = 100.0 * (n_req - (got or 0)) / n_req if n_req else None
            if r["total_s"] is None:
                row["why"] = "no total time"
            elif n_req and (got or 0) < n_req * (1.0 - tp_tolerance):
                row["why"] = f"{got or 0} x [{expect}] of {n_req} (codes {r.get('codes') or {}}, errors {r['n_err']})"
            else:
                row["valid"] = True
        if t.get("start") and t.get("end"):
            row["job_wall_s"] = t["end"] - t["start"]
        ctp = (t.get("ct_prefix") or f"tp_{t.get('mode')}_{t.get('i')}").removeprefix("ct/")
        dt_t, d_t = ct_delta(p, f"{ctp}.pre", f"{ctp}.post", workers)
        if d_t is not None:
            row["ct_inserts_workers"] = d_t
            if bg is not None and dt_t:
                row["conn_corrected"] = d_t - bg * dt_t
        # CPU and throttling during the test (the samples keep running through the tests)
        if t.get("start") and t.get("end") and t["end"] - t["start"] >= 2 * interval:
            sg = segment(t["start"], t["end"])
            if all(sg[n]["dur"] > 0 for n in nodes):
                dur = t["end"] - t["start"]
                row["cpu_obs"] = grp(sg, nodes, GROUPS["observer"])
                row["cpu_node"] = grp(sg, nodes, ["node"])
                row["cpu_k3s"] = grp(sg, nodes, ["k3s"])
                row["cpu_app"] = grp(sg, nodes, ["app"])
                row["cpu_cp_node"] = grp(sg, [cp], ["node"])
                row["thr_app"] = sum(sg[n]["thr"].get("app", 0.0) for n in nodes)
                lab = {}
                for n in nodes:
                    for lb, v in sg[n]["thr_l"].items():
                        lab[lb] = lab.get(lb, 0.0) + v
                if lab:
                    b = max(lab, key=lab.get)
                    # pod name without the ReplicaSet and pod hashes -> workload name
                    row["bottleneck"] = re.sub(r"-[a-z0-9]{6,10}-[a-z0-9]{5}$|-[0-9]+$", "", b.split("/")[0])
                    row["bottleneck_thr"] = lab[b]
                if idle_obs is not None:
                    row["obs_excess_cpu_s"] = (row["cpu_obs"] - idle_obs) * dur
                    row["node_excess_cpu_s"] = (row["cpu_node"] - idle_node) * dur
        run.tp_rows.append(row)
        if row["valid"]:
            by_mode[row["mode"]].append(row)
        else:
            run.flags.append(f"fixed-count {row['mode']} #{row['i']} invalid: {row['why']}")
    for mode in MODES:
        rows = by_mode.get(mode, [])
        run.m[f"tp.{mode}.n_valid"] = len(rows)
        run.m[f"tp.{mode}.time_s"] = mean([r["total_s"] for r in rows])
        run.m[f"tp.{mode}.time_sd_within"] = sd([r["total_s"] for r in rows])
        run.m[f"tp.{mode}.rps"] = mean([r.get("rps") for r in rows])
        run.m[f"tp.{mode}.p99_ms"] = mean([r.get("p99_ms") for r in rows])
        run.m[f"tp.{mode}.non2xx_pct"] = mean([r.get("non2xx_pct") for r in rows])
        ins = [r.get("ct_inserts_workers") for r in rows if r.get("ct_inserts_workers") is not None]
        run.m[f"tp.{mode}.inserts_per_req"] = (mean(ins) / tp_n) if ins and tp_n else None
        cc = [r.get("conn_corrected") for r in rows if r.get("conn_corrected") is not None]
        run.m[f"tp.{mode}.conn_per_req"] = (mean(cc) / tp_n) if cc and tp_n else None
        for k in ("cpu_obs", "cpu_node", "cpu_k3s", "cpu_app", "cpu_cp_node", "thr_app", "bottleneck_thr"):
            run.m[f"tp.{mode}.{k}"] = mean([r.get(k) for r in rows])
        bn = [r.get("bottleneck") for r in rows if r.get("bottleneck")]
        if bn:
            run.info[f"tp.{mode}.bottleneck"] = max(set(bn), key=bn.count)
        # cost per request (exact count) and per new connection (background-corrected)
        per_req_o = [1e6 * r["obs_excess_cpu_s"] / tp_n for r in rows if r.get("obs_excess_cpu_s") is not None and tp_n]
        per_req_n = [1e6 * r["node_excess_cpu_s"] / tp_n for r in rows if r.get("node_excess_cpu_s") is not None and tp_n]
        run.m[f"norm.{mode}.obs_us_per_req"] = mean(per_req_o)
        run.m[f"norm.{mode}.node_us_per_req"] = mean(per_req_n)
        if mode == "newconn":
            pc_o = [1e6 * r["obs_excess_cpu_s"] / r["conn_corrected"] for r in rows
                    if r.get("obs_excess_cpu_s") is not None and (r.get("conn_corrected") or 0) > 0.2 * tp_n]
            pc_n = [1e6 * r["node_excess_cpu_s"] / r["conn_corrected"] for r in rows
                    if r.get("node_excess_cpu_s") is not None and (r.get("conn_corrected") or 0) > 0.2 * tp_n]
            run.m["norm.newconn.obs_us_per_conn"] = mean(pc_o)
            run.m["norm.newconn.node_us_per_conn"] = mean(pc_n)

    # ---- flows in the steady window: pod accepts on the workers, minus the background rate
    span, dlt = ct_delta(p, "steady_pre", "steady_post", workers)
    run.m["flows.source"] = fk_all
    if dlt is not None and steady_dur > 0 and dlt > 0:
        # raw: all accepts between the snapshots per second of load; app: minus the background
        # rate over the whole snapshot span, per second of load
        span = span if span and span > 0 else steady_dur
        run.m["flows.workers_per_s"] = dlt / steady_dur
        if bg is not None:
            run.m["flows.app_per_s"] = (dlt - bg * span) / steady_dur
    else:
        run.flags.append("no flow counts: conntrack insert stays 0 and no pod TCP counters (flows/s unknown)")

    # ---- Hubble: flows processed (all namespaces), its mix, lost events
    def hsum(label, name):
        v = [prom_sum(os.path.join(p, "metrics", f"{label}.{n}.hubble.prom"), name) for n in nodes]
        return v if all(x is not None for x in v) else None
    hp, hq = hsum("steady_pre", "hubble_flows_processed_total"), hsum("steady_post", "hubble_flows_processed_total")
    if hp and hq and steady_dur > 0:
        run.m["hubble.flows_per_s"] = (sum(hq) - sum(hp)) / steady_dur
        cpn = nodes.index(cp) if cp in nodes else None
        tot = sum(hq) - sum(hp)
        if cpn is not None and tot > 0:
            run.m["hubble.cp_share"] = (hq[cpn] - hp[cpn]) / tot
        mix = defaultdict(float)
        for n in nodes:
            a = prom_series(os.path.join(p, "metrics", f"steady_pre.{n}.hubble.prom"), "hubble_flows_processed_total") or []
            b = prom_series(os.path.join(p, "metrics", f"steady_post.{n}.hubble.prom"), "hubble_flows_processed_total") or []
            before = defaultdict(float)
            for lb, v in a:
                before[tuple(sorted(lb.items()))] += v
            for lb, v in b:
                mix[hubble_class(lb, app_ns)] += v - before.get(tuple(sorted(lb.items())), 0.0)
        for c in HUB_CLASSES:
            run.m[f"hubble.mix.{c}_per_s"] = mix.get(c, 0.0) / steady_dur
    lp, lq = hsum("steady_pre", "hubble_lost_events_total"), hsum("steady_post", "hubble_lost_events_total")
    if lp and lq:
        run.m["hubble.lost_events"] = sum(lq) - sum(lp)
    lf = hsum("final", "hubble_lost_events_total")
    if lf:
        run.m["hubble.lost_events_run"] = sum(lf)       # counters start at the agent restart in cond.sh
        if run.cond == "hubble" and sum(lf) > 0:
            run.flags.append(f"Hubble lost {sum(lf):.0f} events during the run (ring buffer), "
                             f"{run.m.get('hubble.lost_events', 0):.0f} of them in the steady window")
    hs = hsum("final", "hubble_flows_processed_total")
    if hs is not None:
        nser = 0
        for n in nodes:
            try:
                nser += sum(1 for ln in open(os.path.join(p, "metrics", f"final.{n}.hubble.prom"))
                            if ln.startswith("hubble_"))
            except OSError:
                pass
        run.m["hubble.series_final"] = nser

    # ---- client events/s inside the analysis window (same window for every tool)
    kv = meta.get("kv", {})
    cb = None
    try:
        cb = json.load(open(os.path.join(p, "client_bins.json")))
    except (OSError, ValueError):
        pass
    for tool, key in (("hubble", "client.hubble_lines_per_s"), ("ig_tcp", "client.igtcp_lines_per_s")):
        if cb and tool in cb:
            bs = float(cb.get("bin_s", 5))
            inside = [float(b) for b in cb[tool]["counts"] if float(b) >= ws and float(b) + bs <= we]
            cnt = sum(v for b, v in cb[tool]["counts"].items() if float(b) >= ws and float(b) + bs <= we)
            nb = len(range(int(math.ceil(ws / bs) * bs), int(we - bs) + 1, int(bs))) or len(inside)
            if nb > 0:
                run.m[key] = cnt / (nb * bs)
                run.info[f"{key}.source"] = "window"
            if tool == "ig_tcp":
                run.info["ig_tcp.types"] = json.dumps(cb[tool].get("types", {}), sort_keys=True)
        else:
            f_ = "hubble.json" if tool == "hubble" else "ig_tcp.json"
            lines = _num(kv.get(f"client_out.{f_}.lines"))
            cs, ce = ph.get("client_started"), ph.get("clients_stopped")
            if lines is not None and cs and ce and ce > cs:
                run.m[key] = lines / (ce - cs)
                run.info[f"{key}.source"] = "client lifetime (no client_bins.json)"
    if kv.get("snap_ok") == "0":
        run.flags.append("snapshot_socket returned nothing after 3 tries")

    # ---- ig_snap: standing cost vs the one snapshot
    if run.cond == "ig_snap" and "snap_start" in ph:
        run.m["snap.seconds"] = ph.get("snap_end", ph["snap_start"]) - ph["snap_start"]
        sa, sb = ph["snap_start"], ph.get("snap_end", ph["snap_start"])
        if sa - 2 * interval > ws:
            stand = segment(ws, sa - 2.0)
            snap = segment(sa - 1.0 * interval, sb + 1.5 * interval)
            cmps = GROUPS["observer"] + ["k3s"]
            r0, r1 = grp(stand, nodes, cmps), grp(snap, nodes, cmps)
            d1 = mean([snap[n]["dur"] for n in nodes]) or 0.0
            run.m["snap.standing.cpu.cluster.observer"] = grp(stand, nodes, GROUPS["observer"])
            run.m["snap.standing.cpu.cluster.obs_k3s"] = r0
            run.m["snap.cpu_s"] = (r1 - r0) * d1
    for w in meta.get("warnings", []):
        run.flags.append(w)
    obs = run.m.get("cpu.cluster.observer")
    fl = run.m.get("flows.workers_per_s")
    if obs is not None and fl:
        run.m["norm.obs_mcores_per_kflow"] = 1000.0 * obs / (fl / 1000.0)

    # ---- host-speed canary: mean speed per node over each segment (only runs that have it, so
    # runs without a canary keep exactly their old metrics)
    if canary:
        segs = [("steady", ws, we)]
        if "idle_start" in ph and "idle_end" in ph:
            segs.insert(0, ("idle", ph["idle_start"] + 2.0, ph["idle_end"]))
        for t in tests:
            if t.get("start") and t.get("end"):
                segs.append((f"tp_{t.get('mode')}_{t.get('i')}", t["start"], t["end"]))
        for seg, lo, hi in segs:
            d = {}
            for n, smp in canary.items():
                sc, sw, k = canary_speed(smp, lo, hi)
                d[n] = (sc, sw, k, lo, hi)
            run.canary_seg[seg] = d
        st_ = run.canary_seg["steady"]
        for n in nodes:
            if st_.get(n) and st_[n][0]:
                run.m[f"canary.steady.speed_cpu.{n}"] = st_[n][0]
                run.m[f"canary.steady.speed_wall.{n}"] = st_[n][1]
        for seg in ("steady", "idle"):
            if seg in run.canary_seg:
                run.m[f"canary.{seg}.speed_cpu.workers"] = mean(
                    [run.canary_seg[seg][n][0] for n in workers if run.canary_seg[seg].get(n)])
        for mode in MODES:
            run.m[f"canary.tp.{mode}.speed_cpu.workers"] = mean(
                [mean([run.canary_seg[f"tp_{mode}_{r['i']}"][n][0] for n in workers
                       if run.canary_seg.get(f"tp_{mode}_{r['i']}", {}).get(n)])
                 for r in by_mode.get(mode, [])])
        if run.m.get("canary.steady.speed_cpu.workers") is None:
            run.flags.append("host-speed canary: no samples from the workers in the steady window")


def _k8s_cpu(meta, n):
    for x in (meta.get("nodes", {}).get("k8s") or []):
        if isinstance(x, dict) and x.get("name") == n:
            return _num(x.get("cpu"))
    return None


FLOW_KEYS = ("podnet_passive_opens", "insert")


def ct_delta(p, pre_label, post_label, nodes):
    """-> (seconds between the snapshots, accepted connections between them) or (None, None).
    With per-netns counters in both snapshots, only network namespaces present in both count, so
    a pod that went away (or appeared) in between does not move the sum. Else the node sums."""
    pre = [parse_ct(os.path.join(p, "ct", f"{pre_label}.{n}.txt")) for n in nodes]
    post = [parse_ct(os.path.join(p, "ct", f"{post_label}.{n}.txt")) for n in nodes]
    t0 = [x[0] for x in pre if x[0] is not None]
    t1 = [x[0] for x in post if x[0] is not None]
    dt = (mean(t1) - mean(t0)) if t0 and t1 else None
    if pre and all("_podnet_ns" in a[1] and "_podnet_ns" in b[1] for a, b in zip(pre, post)):
        d = 0
        for a, b in zip(pre, post):
            pa, pb = a[1]["_podnet_ns"], b[1]["_podnet_ns"]
            d += sum(pb[k] - pa[k] for k in pa.keys() & pb.keys())
        return dt, d
    key = flow_key(p, pre_label, nodes)
    if key and all(key in a[1] for a in pre) and all(key in b[1] for b in post):
        return dt, sum(b[1][key] for b in post) - sum(a[1][key] for a in pre)
    return dt, None


def parse_ct_nodes(p, label, nodes, key=None):
    """Flow counter summed over nodes: pod-netns TCP PassiveOpens (accepted connections) when every
    node's snapshot has it, else the conntrack insert counter (always 0 on kernel 6.12)."""
    return ct_point(p, label, nodes, key)[1]


def ct_point(p, label, nodes, key=None):
    """-> (mean snapshot time, counter summed over nodes) or (None, None)"""
    got = [parse_ct(os.path.join(p, "ct", f"{label}.{n}.txt")) for n in nodes]
    vals = [g[1] for g in got]
    tss = [g[0] for g in got if g[0] is not None]
    for k in ((key,) if key else FLOW_KEYS):
        if vals and all(k in v for v in vals):
            return (mean(tss) if tss else None), sum(v[k] for v in vals)
    return None, None


def flow_key(p, label, nodes):
    vals = [parse_ct(os.path.join(p, "ct", f"{label}.{n}.txt"))[1] for n in nodes]
    for k in FLOW_KEYS:
        if vals and all(k in v for v in vals):
            return k
    return None


# --------------------------------------------------------------------------------------------
# canary normalisation (after every run is analysed: the reference is a median over runs)

NORM_GROUPS = ("node", "observer", "observer_incluster", "clients", "app", "loadgen", "k8s_system", "harness")


def normalise_by_canary(runs):
    """Per app and layout, reference speed of a node = median of its steady-window canary speeds
    over the used runs. Ratio = a segment's speed / the reference (> 1: the host was faster than
    usual, so the same work took fewer cores and less time). Writes, for runs with canary data:
    cn.cpu.<scope>.<group> = sum over nodes of the node's steady-window cores x its ratio (a node
    without canary data gets the mean ratio of the others), cn.tp.<mode>.time_s = mean over the
    valid tests of time x the workers' mean ratio during that test, and the ratios themselves."""
    groups = defaultdict(list)
    for r in runs:
        if not r.excluded and r.canary_seg.get("steady"):
            groups[(r.app, r.layout)].append(r)
    for rs in groups.values():
        ref = {}
        for n in sorted({n for r in rs for n in r.canary_seg["steady"]}):
            v = [r.canary_seg["steady"][n][0] for r in rs
                 if r.canary_seg["steady"].get(n) and r.canary_seg["steady"][n][0]]
            if v:
                ref[n] = statistics.median(v)
        for r in rs:
            r.canary_ref = ref

            def ratios(seg, r=r):
                d = r.canary_seg.get(seg) or {}
                return {n: d[n][0] / ref[n] for n in d if d[n][0] and ref.get(n)}
            rst = ratios("steady")
            if not rst:
                continue
            fill = mean(list(rst.values()))
            r.m["canary.ratio.cluster"] = fill
            r.m["canary.ratio.workers"] = mean([rst[n] for n in r.workers if n in rst])
            for scope, sn in (("cluster", r.nodes), ("workers", r.workers)):
                for g in NORM_GROUPS:
                    r.m[f"cn.cpu.{scope}.{g}"] = sum(r.node_grp.get(n, {}).get(g, 0.0) * rst.get(n, fill) for n in sn)
            for row in r.tp_rows:
                tr = ratios(f"tp_{row.get('mode')}_{row.get('i')}")
                wk = [tr[n] for n in r.workers if n in tr]
                if wk and row.get("total_s") is not None:
                    row["canary_ratio"] = mean(wk)
                    row["total_s_norm"] = row["total_s"] * row["canary_ratio"]
            for mode in MODES:
                ok = [row for row in r.tp_rows if row.get("mode") == mode and row.get("valid")
                      and row.get("total_s_norm") is not None]
                r.m[f"cn.tp.{mode}.time_s"] = mean([row["total_s_norm"] for row in ok])
                r.m[f"canary.tp.{mode}.ratio.workers"] = mean([row["canary_ratio"] for row in ok])


# --------------------------------------------------------------------------------------------
# discovery and aggregation

def discover(root):
    if not any(re.match(r"(rep|cycle)\d+$", d) for a in _dirs(root) for d in _dirs(os.path.join(root, a))):
        if os.path.isdir(os.path.join(root, "results")):
            root = os.path.join(root, "results")
    runs = []
    for app in sorted(_dirs(root)):
        if app == "analysis":
            continue
        for rep in sorted(_dirs(os.path.join(root, app))):
            mm = re.match(r"(rep|cycle)(\d+)$", rep)
            if not mm:
                continue
            for cond in CONDS:
                d = os.path.join(root, app, rep, cond)
                if os.path.isdir(d):
                    runs.append(Run(app, int(mm.group(2)), cond, d, layout=mm.group(1)))
    return root, runs


def _dirs(p):
    try:
        return [e.name for e in os.scandir(p) if e.is_dir()]
    except OSError:
        return []


class Agg:
    def __init__(self, runs):
        self.cells = defaultdict(list)   # (app, cond) -> [Run]
        for r in runs:
            if not r.excluded:
                self.cells[(r.app, r.cond)].append(r)

    def vals(self, app, cond, key):
        return [r.m.get(key) for r in self.cells.get((app, cond), []) if r.m.get(key) is not None]

    def stat(self, app, cond, key):
        v = self.vals(app, cond, key)
        return mean(v), sd(v), len(v)

    def by_rep(self, app, cond):
        return {r.rep: r for r in self.cells.get((app, cond), [])}

    def cmp(self, app, cond, key):
        """Technique vs baseline for one metric.
        delta/pct: the paired per-rep difference (technique minus the same rep's baseline, only
        reps run on the same play and machines) when at least one pair exists, else the
        difference of the means. lo/hi: its t-based 95% CI (df = pairs - 1). nd ("n.s."): that CI
        includes 0. p: paired t-test. p_welch: Welch on the run values (second check)."""
        b, bsd, nb = self.stat(app, "baseline", key)
        c, csd, nc = self.stat(app, cond, key)
        out = {"b": b, "b_sd": bsd, "n_b": nb, "c": c, "c_sd": csd, "n_c": nc,
               "delta": None, "pct": None, "lo": None, "hi": None, "pct_lo": None, "pct_hi": None,
               "nd": None, "p": None, "p_welch": None, "n_pair": 0, "deltas": [], "pcts": [],
               "host_skipped": [], "within_2sd": None}
        B, C = self.by_rep(app, "baseline"), self.by_rep(app, cond)
        ds, pcts = [], []
        for rep in sorted(set(B) & set(C)):
            vb, vc = B[rep].m.get(key), C[rep].m.get(key)
            if vb is None or vc is None:
                continue
            if B[rep].host_sig and C[rep].host_sig and B[rep].host_sig != C[rep].host_sig:
                out["host_skipped"].append(rep)
                continue
            ds.append(vc - vb)
            if vb:
                pcts.append(100.0 * (vc - vb) / vb)
        ps, pp = paired_stats(ds), paired_stats(pcts)
        out.update({"deltas": ds, "pcts": pcts, "n_pair": ps["n"]})
        if ps["n"]:
            out.update({"delta": ps["mean"], "lo": ps["lo"], "hi": ps["hi"], "p": ps["p"]})
            out.update({"pct": pp["mean"], "pct_lo": pp["lo"], "pct_hi": pp["hi"]})
        elif b is not None and c is not None:
            out["delta"] = c - b
            out["pct"] = 100.0 * (c - b) / b if b else None
        if out["lo"] is not None:
            out["nd"] = out["lo"] <= 0.0 <= out["hi"]
        # % endpoints (fixed-count time, canary checks) are reported as per-pair % differences, so their
        # p, n.s. flag and Holm input come from those same % differences, not from absolute seconds
        if (key.endswith(".time_s") or key.startswith("canary.")) and pp["n"] and out.get("pct_lo") is not None:
            out["p"] = pp["p"]
            out["nd"] = out["pct_lo"] <= 0.0 <= out["pct_hi"]
        # sensitivity (pre-declared 2026-10-04): median of the paired differences and Wilcoxon p
        is_pct = key.endswith(".time_s") or key.startswith("canary.")
        src = pcts if is_pct else ds
        out["median"] = statistics.median(src) if src else None
        out["wilcox_p"] = wilcoxon_p(src)
        if b is not None and c is not None and bsd is not None:
            out["within_2sd"] = abs(c - b) < 2 * bsd
        if b is not None and c is not None:
            out["p_welch"] = welch_p(self.vals(app, cond, key), self.vals(app, "baseline", key))
        return out

    def tp_exec(self, app, cond, mode, key="total_s"):
        """all valid fixed-count executions of a cell -> (mean, SD, n) of total_s (or total_s_norm)"""
        xs = [t[key] for r in self.cells.get((app, cond), []) for t in r.tp_rows
              if t.get("mode") == mode and t.get("valid") and t.get(key) is not None]
        return mean(xs), sd(xs), len(xs)


# --------------------------------------------------------------------------------------------
# formatting

def f(x, d=2):
    return "-" if x is None else f"{x:.{d}f}"


def pm(m, s, d=2):
    if m is None:
        return "-"
    return f"{m:.{d}f} ± {s:.{d}f}" if s is not None else f"{m:.{d}f}"


def sign(x, d=1, suffix=""):
    return "-" if x is None else f"{x:+.{d}f}{suffix}"


def nd_mark(c):
    return " (n.s.)" if c.get("nd") else ""


def ci(c, d=1, suffix="", pct=False):
    """'+1.2 [-0.3, +2.7]' for the paired delta (or pct), with an n.s. mark"""
    v, lo, hi = (c.get("pct"), c.get("pct_lo"), c.get("pct_hi")) if pct else (c.get("delta"), c.get("lo"), c.get("hi"))
    if v is None:
        return "-"
    s = f"{v:+.{d}f}{suffix}"
    if lo is not None:
        s += f" [{lo:+.{d}f}, {hi:+.{d}f}]"
    return s + nd_mark(c)


def pval(c, key="p"):
    v = c.get(key)
    return "-" if v is None else (f"{v:.3f}" if v >= 0.001 else "<0.001")


def pfmt(v):
    return "-" if v is None else (f"{v:.3f}" if v >= 0.001 else "<0.001")


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)


def write_csv(path, headers, rows):
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(headers)
        for r in rows:
            w.writerow(["" if x is None else x for x in r])


def _mode_info(agg, app, cond, key):
    vs = [r.info.get(key) for r in agg.cells.get((app, cond), []) if r.info.get(key)]
    return max(sorted(set(vs)), key=vs.count) if vs else None  # sorted: deterministic tie-break


# --------------------------------------------------------------------------------------------
# interleaved cycles and canary normalisation: extra sections (only for cycle data or when a run
# has canary data, so rep-layout outputs without canary data stay exactly as they were)

# (label, raw key, canary-normalised key or None, "abs" | "pct", decimals)
PAIRED_ENDPOINTS = [
    ("Δ cluster busy CPU (cores)", "cpu.cluster.node", "cn.cpu.cluster.node", "abs", 3),
    ("Δ observer CPU (cores)", "cpu.cluster.observer", "cn.cpu.cluster.observer", "abs", 3),
    ("Δ app CPU (cores)", "cpu.cluster.app", "cn.cpu.cluster.app", "abs", 3),
    ("Δ k3s/containerd CPU (cores)", "cpu.cluster.k8s_system", "cn.cpu.cluster.k8s_system", "abs", 3),
    ("Δ observer anon memory (MiB, primary)", "anon.cluster.observer", None, "abs", 0),
    ("Δ observer memory, working set (MiB)", "mem.cluster.observer", None, "abs", 0),
    ("fixed-count time, keep-alive", "tp.keepalive.time_s", "cn.tp.keepalive.time_s", "pct", 1),
    ("fixed-count time, new conn", "tp.newconn.time_s", "cn.tp.newconn.time_s", "pct", 1),
    # check, not an outcome: with interleaved blocks host drift averages out over the conditions, so
    # a canary speed that differs by condition means the observer's own load slows the canary, and
    # normalising would then remove part of the real overhead
    ("canary speed, workers, steady window (check)", "canary.steady.speed_cpu.workers", None, "pct", 2),
]


def _utc(t):
    return "-" if t is None else datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%m-%d %H:%M")


def _cv(xs):
    xs = [x for x in xs if x is not None]
    return 100.0 * statistics.stdev(xs) / statistics.fmean(xs) if len(xs) >= 2 and statistics.fmean(xs) else None


def _pearson(xs, ys):
    pr = [(x, y) for x, y in zip(xs, ys) if x is not None and y is not None]
    if len(pr) < 3:
        return None
    mx, my = statistics.fmean(p_[0] for p_ in pr), statistics.fmean(p_[1] for p_ in pr)
    sxy = sum((x - mx) * (y - my) for x, y in pr)
    sxx, syy = sum((x - mx) ** 2 for x, _ in pr), sum((y - my) ** 2 for _, y in pr)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else None


def first_run_ids(runs):
    """(app, cycle, cond) of the first run of every block: the run at order position 1 of the lowest
    cycle run on each play (cycle layout only)."""
    first_cycle = {}
    for r in runs:
        if r.excluded or r.layout != "cycle":
            continue
        play = (r.meta.get("host") or {}).get("play_id") or (r.host_sig[0] if r.host_sig else None)
        k = (r.app, play)
        first_cycle[k] = min(first_cycle.get(k, r.rep), r.rep)
    ids = set()
    for r in runs:
        if r.excluded or r.layout != "cycle":
            continue
        play = (r.meta.get("host") or {}).get("play_id") or (r.host_sig[0] if r.host_sig else None)
        if r.rep == first_cycle.get((r.app, play)) and str(r.meta.get("params", {}).get("order_pos")) == "1":
            ids.add((r.app, r.rep, r.cond))
    return ids


def sensitivity_part(agg, agg_nf, app, techs, holm_p, first_ids, csv_rows):
    """Pre-declared 2026-10-04 (FIXLOG): primary paired Δ next to (1) the median of the paired
    differences with a Wilcoxon signed-rank p and (2) the same paired analysis without the first run
    of each block. A primary result that is significant after Holm but not in both checks is fragile."""
    rows = []
    for key, label in PRIMARY:
        pct = key.endswith(".time_s")
        d = 1 if pct else (3 if key.startswith("cpu.") else 0)
        unit = "%" if pct else ""
        for c in techs:
            cm, cn = agg.cmp(app, c, key), agg_nf.cmp(app, c, key)
            hp = holm_p.get((app, c, key))
            med = cm.get("median")
            sig = hp is not None and hp < 0.05
            ok_w = cm.get("wilcox_p") is not None and cm["wilcox_p"] < 0.05
            ok_nf = cn.get("nd") is False
            verdict = ("robust" if ok_w and ok_nf else "fragile") if sig else "n.s. (primary)"
            rows.append([label, LABEL[c], ci(cm, d, unit, pct=pct), pfmt(hp),
                         sign(med, d, unit) if med is not None else "-", pfmt(cm.get("wilcox_p")),
                         ci(cn, d, unit, pct=pct), str(cn.get("n_pair") or 0), verdict])
            csv_rows["sensitivity"].append([app, key, c, cm.get("pct" if pct else "delta"),
                                            cm.get("pct_lo" if pct else "lo"), cm.get("pct_hi" if pct else "hi"), hp,
                                            med, cm.get("wilcox_p"), cn.get("pct" if pct else "delta"),
                                            cn.get("pct_lo" if pct else "lo"), cn.get("pct_hi" if pct else "hi"),
                                            cn.get("n_pair"), verdict])
    dropped = sorted(f"cycle {k} {LABEL[c]}" for a, k, c in first_ids if a == app)
    return ("### Sensitivity: median and without each block's first run (pre-declared)\n\n"
            "Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the "
            "per-cycle paired differences with its 95% CI and Holm p. Median = median of the same "
            "differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the "
            "primary analysis with the first run of each block left out (" + (", ".join(dropped) or "none")
            + "; that cycle loses only that condition's pair). 'robust' = significant after Holm and in "
            "both checks; 'fragile' = significant after Holm but not in both checks.\n\n"
            + md_table(["Endpoint", "Technique", "Primary Δ [95% CI]", "Holm p", "Median Δ", "Wilcoxon p",
                        "Without first run Δ [95% CI]", "pairs", "Verdict"], rows))


def extra_parts(agg, app, conds_here, techs, layout, csv_rows):
    """-> (parts before the standard tables, parts after them) for one app"""
    unit = "cycle" if layout == "cycle" else "rep"
    has_canary = any(r.canary_seg for c in conds_here for r in agg.cells.get((app, c), []))
    top, bottom = [], []

    # ---- paired deltas, raw and canary-normalised, Holm across techniques per endpoint
    rows = []
    for label, kr, kn, kind, d in PAIRED_ENDPOINTS:
        res = {}
        for variant, key in (("raw", kr), ("norm", kn)):
            if key and (variant == "raw" or has_canary):
                cm = {c: agg.cmp(app, c, key) for c in techs}
                res[variant] = (cm, dict(zip(techs, holm([cm[c]["p"] for c in techs]))))
        pct = kind == "pct"
        for c in techs:
            cr, hr = res["raw"][0][c], res["raw"][1][c]
            cn, hn = (res["norm"][0][c], res["norm"][1][c]) if "norm" in res else (None, None)
            rows.append([label, LABEL[c], ci(cr, d, "%" if pct else "", pct=pct), pval(cr), pfmt(hr),
                         ci(cn, d, "%" if pct else "", pct=pct) if cn else "-", pval(cn) if cn else "-",
                         pfmt(hn) if cn else "-", cr["n_pair"]])
            csv_rows["paired"].append([app, kr, c, cr["n_pair"], cr["b"], cr["c"], cr["delta"], cr["lo"], cr["hi"],
                                       cr["pct"], cr["pct_lo"], cr["pct_hi"], cr["p"], hr]
                                      + ([cn["b"], cn["c"], cn["delta"], cn["lo"], cn["hi"], cn["pct"], cn["pct_lo"],
                                          cn["pct_hi"], cn["p"], hn] if cn else [None] * 10))
    t_q = None
    n_blocks = max((r[-1] for r in rows), default=0)
    if n_blocks >= 2:
        t_q = t_ppf(0.975, n_blocks - 1)
    head = ("### Interleaved cycles: paired deltas, raw and canary-normalised\n\n"
            "Every cycle ran each condition once (Williams-design order), so each technique is paired "
            "with the baseline of the same cycle, about an hour apart at most, and slow host drift "
            "cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, "
            "ICPE 2017). " if layout == "cycle" else
            "### Host speed (canary): paired deltas, raw and canary-normalised\n\n")
    top_or_bottom = top if layout == "cycle" else bottom
    top_or_bottom.append(
        head + f"Δ = mean of the per-{unit} differences (technique minus the same {unit}'s baseline) with "
        f"its 95% CI (t, df = {unit}s - 1" + (f"; t = {t_q:.2f} at {n_blocks} {unit}s" if t_q else "") + "); "
        "fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the "
        "techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU "
        "x (its canary speed in that window / its median speed over this app's runs), fixed-count "
        "time x the workers' speed ratio during that test, so a run on a fast host is scaled up to "
        "the median host speed. Memory is not normalised. The last row is a check: the canary's own "
        "speed should not differ by condition (CI including 0); if it does, the observer's load slows "
        "the canary and the normalised Δ understates the overhead."
        + ("" if has_canary else " No run of this app has canary data, so the normalised columns are empty.")
        + "\n\n" + md_table(["Endpoint", "Technique", "raw Δ [95% CI]", "p", "Holm p", "normalised Δ [95% CI]",
                              "p", "Holm p", f"{unit}s"], rows))

    # ---- drift diagnostic: per block, the baseline's fixed-count time and the canary speed
    B = agg.by_rep(app, "baseline")
    blocks = sorted({r.rep for c in conds_here for r in agg.cells.get((app, c), [])})
    drows, recs = [], []
    for k in blocks:
        rs = [r for c in conds_here for r in agg.cells.get((app, c), []) if r.rep == k]
        t0 = min((r.meta.get("phases", {}).get("run_start") for r in rs
                  if r.meta.get("phases", {}).get("run_start")), default=None)
        order = " ".join(r.cond for r in sorted(rs, key=lambda r: int(r.meta.get("params", {}).get("order_pos") or 0)))
        b = B.get(k)

        def g(key, b=b):
            return b.m.get(key) if b else None
        rec = {"block": k, "start": t0, "order": order,
               "ka": g("tp.keepalive.time_s"), "nc": g("tp.newconn.time_s"),
               "ka_n": g("cn.tp.keepalive.time_s"), "nc_n": g("cn.tp.newconn.time_s"),
               "app": g("cpu.cluster.app"), "app_n": g("cn.cpu.cluster.app"),
               "node": g("cpu.cluster.node"), "node_n": g("cn.cpu.cluster.node"),
               "sp": g("canary.steady.speed_cpu.workers"), "sp_ka": g("canary.tp.keepalive.speed_cpu.workers"),
               "sp_nc": g("canary.tp.newconn.speed_cpu.workers"), "sp_idle": g("canary.idle.speed_cpu.workers"),
               "ratio": g("canary.ratio.workers"),
               "sp_all": mean([r.m.get("canary.steady.speed_cpu.workers") for r in rs])}
        recs.append(rec)
        M = 1e6
        drows.append([k, _utc(t0), order, f(rec["ka"], 1), f(rec["ka_n"], 1), f(rec["nc"], 1), f(rec["nc_n"], 1),
                      f(rec["app"], 3), f(rec["app_n"], 3),
                      f(rec["sp"] / M if rec["sp"] else None, 2), f(rec["ratio"], 2),
                      f(rec["sp_all"] / M if rec["sp_all"] else None, 2)])
        csv_rows["drift"].append([app, layout, k, t0, order, rec["ka"], rec["ka_n"], rec["nc"], rec["nc_n"],
                                  rec["app"], rec["app_n"], rec["node"], rec["node_n"], rec["sp_idle"], rec["sp"],
                                  rec["sp_ka"], rec["sp_nc"], rec["ratio"], rec["sp_all"]])
    if layout == "cycle" or has_canary:
        notes = []
        for mode, kr_, kn_, ks in (("keep-alive", "ka", "ka_n", "sp_ka"), ("new conn", "nc", "nc_n", "sp_nc")):
            cr_, cn_ = _cv([x[kr_] for x in recs]), _cv([x[kn_] for x in recs])
            rr = _pearson([x[kr_] for x in recs], [1.0 / x[ks] if x[ks] else None for x in recs])
            notes.append(f"{mode}: CV of the baseline time across {unit}s {f(cr_, 1)}% raw, "
                         f"{f(cn_, 1)}% normalised; correlation of the raw time with 1/canary speed "
                         f"during the tests r = {f(rr, 2)}")
            csv_rows["drift_summary"].append([app, layout, mode, len(recs), cr_, cn_, rr])
        (top if layout == "cycle" else bottom).append(
            f"### Drift diagnostic (per {unit})\n\n"
            "The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in "
            "the steady window (cores) raw and normalised, the workers' canary speed in that window "
            "(million iterations per CPU-second) and its ratio to the app's median, and the mean "
            f"canary speed over all runs of the {unit}. If the host drifts, the raw baseline times "
            "move with 1/speed and the normalised ones stay flat. " + "; ".join(notes) + ".\n\n"
            + md_table([unit.capitalize(), "start (UTC)", "order", "keep-alive s", "norm.", "new conn s", "norm.",
                        "app CPU", "norm.", "canary speed", "ratio", f"{unit} mean speed"], drows))

    if not has_canary:
        return top, bottom
    # ---- canary speed per segment and worker
    rows = []
    for c in conds_here:
        for r in sorted(agg.cells.get((app, c), []), key=lambda r: r.rep):
            ws_ = r.workers
            for seg, d in r.canary_seg.items():
                for n, (sc, sw, kk, lo, hi) in d.items():
                    ref = r.canary_ref.get(n)
                    csv_rows["canary_seg"].append([app, layout, r.rep, c, seg, n, lo, hi, kk, sc, sw, ref,
                                                   sc / ref if sc and ref else None])

            def segv(prefix, r=r, ws_=ws_):
                keys = [s_ for s_ in r.canary_seg if s_ == prefix or s_.startswith(prefix + "_")]
                return "/".join(f(mean([r.canary_seg[s_][n][0] for s_ in keys if r.canary_seg[s_].get(n)
                                        and r.canary_seg[s_][n][0]]) / 1e6
                                  if any(r.canary_seg[s_].get(n) and r.canary_seg[s_][n][0] for s_ in keys) else None, 2)
                                for n in ws_)
            if r.canary_seg:
                rows.append([r.rep, LABEL[c], segv("idle"), segv("steady"), segv("tp_keepalive"), segv("tp_newconn"),
                             f(r.m.get("canary.ratio.workers"), 2)])
    rows.sort(key=lambda x: (x[0], CONDS.index([k for k, v in LABEL.items() if v == x[1]][0])))
    bottom.append("### Host-speed canary per segment\n\n"
                  "Million canary iterations per CPU-second, one value per worker (" + ", ".join(
                      next((r.workers for c in conds_here for r in agg.cells.get((app, c), []) if r.workers), []))
                  + "), over the idle segment, the steady window and the fixed-count tests of each mode. "
                  "Ratio: the workers' steady-window speed over the app's median. Every value per node "
                  "and segment is in canary_segments.csv.\n\n"
                  + md_table([unit.capitalize(), "Technique", "idle", "steady", "keep-alive tests", "new conn tests",
                              "ratio"], rows))
    # ---- Table 5 with canary-normalised times
    rows = []
    for mode in MODES:
        key = f"cn.tp.{mode}.time_s"
        wo = agg.tp_exec(app, "baseline", mode, "total_s_norm")
        cms = {c: agg.cmp(app, c, key) for c in techs}
        adj = dict(zip(techs, holm([cms[c]["p"] for c in techs])))
        for c in techs:
            cm = cms[c]
            wi = agg.tp_exec(app, c, mode, "total_s_norm")
            bound = "" if cm.get("pct_hi") is None or not cm.get("nd") else f" (< {cm['pct_hi']:.1f}% at 95%)"
            rows.append([mode, LABEL[c], f"{pm(wo[0], wo[1])} (n={wo[2]})", f"{pm(wi[0], wi[1])} (n={wi[2]})",
                         ci(cm, 2, "%", pct=True) + bound, pval(cm), pfmt(adj[c])])
            csv_rows["table5n"].append([app, mode, c, wo[0], wo[1], wo[2], wi[0], wi[1], wi[2], cm["pct"],
                                        cm["pct_lo"], cm["pct_hi"], cm["nd"], cm["p"], adj[c], cm["n_pair"]])
    bottom.append("### Fixed-count time, canary-normalised (Table 5 format)\n\n"
                  "As the Table 5 above, with every execution's time multiplied by the workers' canary "
                  "speed ratio during that execution. Holm: across the techniques, per mode.\n\n"
                  + md_table(["Mode", "Technique", "w/o (s)", "with (s)", "Overhead [95% CI]", "p", "Holm p"], rows))
    return top, bottom


# --------------------------------------------------------------------------------------------
# report

def build(root, runs, out, args, layout="rep"):
    agg = Agg(runs)
    first_ids = first_run_ids(runs) if layout == "cycle" else set()
    agg_nf = Agg([r for r in runs if (r.app, r.rep, r.cond) not in first_ids]) if first_ids else None
    apps = sorted({r.app for r in runs})
    md_parts = {}
    csv_rows = defaultdict(list)
    regime = {}

    # Holm over the primary endpoints, per app
    holm_p = {}
    for app in apps:
        keys = [(c, k) for c in TECHS for k, _ in PRIMARY if agg.cells.get((app, c))]
        adj = holm([agg.cmp(app, c, k)["p"] for c, k in keys])
        for (c, k), a in zip(keys, adj):
            holm_p[(app, c, k)] = a

    for app in apps:
        parts = []
        conds_here = [c for c in CONDS if agg.cells.get((app, c))]
        if "baseline" not in conds_here:
            md_parts[app] = f"No usable baseline run for {app}, so no overhead can be computed.\n"
            continue
        techs = [c for c in TECHS if c in conds_here]
        thr_b = agg.stat(app, "baseline", "tp.newconn.bottleneck_thr")[0]
        regime[app] = "quota-bound" if (thr_b or 0.0) > 0.1 else "node-bound"

        # ---- Table 5 (GoLeash): fixed-count time
        rows = []
        for mode in MODES:
            key = f"tp.{mode}.time_s"
            wo = agg.tp_exec(app, "baseline", mode)
            bcv = agg.stat(app, "baseline", key)
            aa = 100 * bcv[1] / bcv[0] if bcv[0] and bcv[1] is not None else None
            bn_b = _mode_info(agg, app, "baseline", f"tp.{mode}.bottleneck")
            thr_bm = agg.stat(app, "baseline", f"tp.{mode}.bottleneck_thr")[0]
            for c in techs:
                cm = agg.cmp(app, c, key)
                wi = agg.tp_exec(app, c, mode)
                hp = holm_p.get((app, c, key))
                bn_c = _mode_info(agg, app, c, f"tp.{mode}.bottleneck")
                thr_cm = agg.stat(app, c, f"tp.{mode}.bottleneck_thr")[0]
                cpb = agg.stat(app, c, f"tp.{mode}.cpu_cp_node")[0]
                cpr = agg.stat(app, c, f"tp.{mode}.conn_per_req")[0]
                bound = "" if cm.get("pct_hi") is None or not cm.get("nd") else f" (< {cm['pct_hi']:.1f}% at 95%)"
                rows.append([mode, LABEL[c], f"{pm(wo[0], wo[1])} (n={wo[2]})", f"{pm(wi[0], wi[1])} (n={wi[2]})",
                             ci(cm, 2, "%", pct=True) + bound, pval(cm), pfmt(hp),
                             f"{bn_c or '-'} {f(thr_cm, 2)}", f(cpr, 2)])
                csv_rows["table5"].append([app, mode, c, cm["b"], cm["b_sd"], cm["n_b"], cm["c"], cm["c_sd"], cm["n_c"],
                                           cm["pct"], cm["nd"], cm["p_welch"], wo[0], wo[1], wo[2], wi[0], wi[1], wi[2],
                                           cm["pct_lo"], cm["pct_hi"], cm["p"], hp, cm["n_pair"], aa, bn_b, thr_bm,
                                           bn_c, thr_cm, agg.stat(app, "baseline", f"tp.{mode}.conn_per_req")[0], cpr,
                                           (100 * cpb / 2.0) if cpb is not None else None])
        n_tp = _param(agg, app, "tp_n")
        parts.append("### Fixed-count time (GoLeash Table 5 format)\n\n"
                     f"Time to finish {n_tp} requests at concurrency {_param(agg, app, 'tp_c')}. "
                     "w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports "
                     "its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI "
                     "(t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most "
                     "the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. "
                     f"Bottleneck: the app container with the most CFS throttling during the tests (s/s); this "
                     f"app is **{regime[app]}** (baseline newconn bottleneck throttled {f(thr_b, 2)} s/s), so "
                     + ("the test measures how fast throttled app cgroups drain their quota; it sees observer "
                        "cost only where it is charged to those cgroups. "
                        if regime[app] == "quota-bound" else "node CPU limits the test. ")
                     + "conn/req: background-corrected new connections accepted per request.\n\n"
                     + md_table(["Mode", "Technique", "w/o (s)", "with (s)", "Overhead [95% CI]", "p", "Holm p",
                                 "bottleneck (thr s/s)", "conn/req"], rows))
        rows = []
        for mode in MODES:
            b = agg.stat(app, "baseline", f"tp.{mode}.time_s")
            cv = 100 * b[1] / b[0] if b[0] and b[1] is not None else None
            wo = agg.tp_exec(app, "baseline", mode)
            rows.append([mode, pm(b[0], b[1]), f(cv, 2) + "%", f(100 * wo[1] / wo[0] if wo[0] and wo[1] else None, 2) + "%",
                         str(b[2])])
        parts.append("A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run "
                     "noise any overhead has to beat; the SD over executions includes the within-run "
                     "repeats.\n\n" + md_table(["Mode", "baseline run means (s)", "CV of run means",
                                                 "CV over executions", "runs"], rows))

        # ---- CPU
        rows = []
        bl = agg.stat(app, "baseline", "cpu.cluster.observer")
        bn = agg.stat(app, "baseline", "cpu.cluster.node")
        cap = agg.stat(app, "baseline", "capacity.cpu.cluster")[0]
        rows.append(["baseline", pm(bl[0], bl[1], 3), f(agg.stat(app, "baseline", "cpu_sd.cluster.observer")[0], 3), "-",
                     pm(bn[0], bn[1], 3), f(agg.stat(app, "baseline", "cpu_sd.cluster.node")[0], 3), "-", "-", "-", "-"])
        for c in techs:
            o = agg.cmp(app, c, "cpu.cluster.observer")
            n = agg.cmp(app, c, "cpu.cluster.node")
            w = agg.cmp(app, c, "cpu.workers.node")
            k = agg.cmp(app, c, "cpu.cluster.k8s_system")
            hp = holm_p.get((app, c, "cpu.cluster.observer"))
            rows.append([LABEL[c], pm(o["c"], o["c_sd"], 3), f(agg.stat(app, c, "cpu_sd.cluster.observer")[0], 3),
                         ci(o, 3), pm(n["c"], n["c_sd"], 3), f(agg.stat(app, c, "cpu_sd.cluster.node")[0], 3), ci(n, 3),
                         sign(100 * n["delta"] / cap if n["delta"] is not None and cap else None, 2, "%"),
                         sign(k["delta"], 3), f"{pval(o)} / {pfmt(hp)}"])
            csv_rows["cpu"].append([app, c, o["b"], o["b_sd"], o["c"], o["c_sd"], o["delta"], o["nd"], o["p"],
                                    n["b"], n["b_sd"], n["c"], n["c_sd"], n["delta"], n["pct"],
                                    100 * n["delta"] / cap if n["delta"] is not None and cap else None,
                                    w["delta"], 100 * w["delta"] / agg.stat(app, "baseline", "capacity.cpu.workers")[0]
                                    if w["delta"] is not None and agg.stat(app, "baseline", "capacity.cpu.workers")[0] else None,
                                    n["nd"], n["p"], o["lo"], o["hi"], n["lo"], n["hi"], hp, n["p_welch"], k["delta"],
                                    agg.stat(app, c, "cpu_sd.cluster.observer")[0], agg.stat(app, c, "cpu_sd.cluster.node")[0]])
        parts.append("### CPU (cores, steady window)\n\n"
                     f"Observer = capture components plus their clients. Cluster busy = busy CPU of all "
                     f"{_fmt_int(cap)} vCPUs. Two SDs: '±' is the SD of the window means over reps "
                     "(reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values "
                     "inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the "
                     "kubelet/containerd/API-server change, which observer cgroups do not show. "
                     "The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in "
                     "overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load "
                     "and that ratio would overstate the overhead several times.\n\n"
                     + md_table(["Technique", "Observer", "SD in window", "Δ observer", "Cluster busy", "SD in window",
                                 "Δ cluster", "Δ % of capacity", "Δ k3s", "p / Holm p (Δ observer, primary)"], rows))

        # ---- idle segment (standing cost)
        if any(agg.stat(app, c, "idle.cpu.cluster.node")[0] is not None for c in conds_here):
            rows = []
            for c in techs:
                o = agg.cmp(app, c, "idle.cpu.cluster.observer")
                k = agg.cmp(app, c, "idle.cpu.cluster.k8s_system")
                n = agg.cmp(app, c, "idle.cpu.cluster.node")
                so = agg.cmp(app, c, "cpu.cluster.observer")
                share = 100 * o["delta"] / so["delta"] if o["delta"] is not None and so["delta"] else None
                rows.append([LABEL[c], ci(o, 3), ci(k, 3), ci(n, 3), f(share, 0) + "%"])
                csv_rows["idle"].append([app, c, o["delta"], o["lo"], o["hi"], k["delta"], n["delta"], n["lo"], n["hi"], share])
            parts.append("### Standing cost (idle segment: observer on, app up, no load)\n\n"
                         "Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ "
                         "observer / steady Δ observer: the part of the steady cost that does not depend on "
                         "traffic.\n\n" + md_table(["Technique", "Δ observer", "Δ k3s", "Δ node busy", "Share"], rows))

        # ---- CPU during the fixed-count tests
        rows = []
        for mode in MODES:
            for c in techs:
                o = agg.cmp(app, c, f"tp.{mode}.cpu_obs")
                n = agg.cmp(app, c, f"tp.{mode}.cpu_node")
                k = agg.cmp(app, c, f"tp.{mode}.cpu_k3s")
                tb = agg.stat(app, "baseline", f"tp.{mode}.thr_app")[0]
                tc = agg.stat(app, c, f"tp.{mode}.thr_app")[0]
                cpb = agg.stat(app, c, f"tp.{mode}.cpu_cp_node")[0]
                rows.append([mode, LABEL[c], ci(o, 3), ci(n, 3), ci(k, 3), f"{f(tb, 2)} → {f(tc, 2)}",
                             f(100 * cpb / 2.0 if cpb is not None else None, 0) + "%"])
                csv_rows["tpcpu"].append([app, mode, c, o["delta"], o["lo"], o["hi"], n["delta"], n["lo"], n["hi"],
                                          k["delta"], tb, tc, cpb])
        parts.append("### CPU during the fixed-count tests (cores)\n\n"
                     "Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App "
                     "throttled = CFS throttled time of all app containers, s/s (baseline → technique). "
                     "cp-01 busy = generator node, % of its 2 vCPUs.\n\n"
                     + md_table(["Mode", "Technique", "Δ observer", "Δ node busy", "Δ k3s", "App throttled s/s",
                                 "cp-01 busy"], rows))

        # ---- memory
        rows = []
        bl = agg.stat(app, "baseline", "mem.cluster.observer")
        bn = agg.stat(app, "baseline", "mem.cluster.node")
        mcap = agg.stat(app, "baseline", "capacity.mem.cluster")[0]
        rows.append(["baseline", pm(bl[0], bl[1], 0), f(agg.stat(app, "baseline", "mem_sd.cluster.observer")[0], 1),
                     f(agg.stat(app, "baseline", "mem_slope.cluster.observer")[0], 2),
                     f(agg.stat(app, "baseline", "anon.cluster.observer")[0], 0), "-", "-", pm(bn[0], bn[1], 0), "-", "-"])
        for c in techs:
            o = agg.cmp(app, c, "mem.cluster.observer")
            pk = agg.stat(app, c, "mem_peak.cluster.observer")
            n = agg.cmp(app, c, "mem.cluster.node")
            a_ = agg.cmp(app, c, "anon.cluster.observer")
            hp = holm_p.get((app, c, "anon.cluster.observer"))
            rows.append([LABEL[c], pm(o["c"], o["c_sd"], 0) + f" (peak {f(pk[0], 0)})",
                         f(agg.stat(app, c, "mem_sd.cluster.observer")[0], 1),
                         f(agg.stat(app, c, "mem_slope.cluster.observer")[0], 2),
                         f(agg.stat(app, c, "anon.cluster.observer")[0], 0), ci(a_, 0), ci(o, 0),
                         pm(n["c"], n["c_sd"], 0),
                         sign(100 * a_["delta"] / mcap if a_["delta"] is not None and mcap else None, 2, "%"),
                         f"{pval(a_)} / {pfmt(hp)}"])
            csv_rows["mem"].append([app, c, o["b"], o["b_sd"], o["c"], o["c_sd"], pk[0], o["delta"], o["nd"], o["p"],
                                    n["b"], n["b_sd"], n["c"], n["c_sd"], n["delta"], n["pct"],
                                    100 * o["delta"] / mcap if o["delta"] is not None and mcap else None,
                                    o["lo"], o["hi"], hp, agg.stat(app, c, "mem_sd.cluster.observer")[0],
                                    agg.stat(app, c, "mem_slope.cluster.observer")[0],
                                    agg.stat(app, c, "anon.cluster.observer")[0], agg.stat(app, c, "mem_end.cluster.observer")[0]])
        parts.append("### Memory (MiB, steady window)\n\n"
                     "Observer working set = memory.current minus inactive_file (as the kubelet counts it); "
                     "anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope "
                     "= MiB per minute over the window (a stationarity check: a rising observer is not at "
                     "steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from "
                     "component working sets, so do not compare the two columns.\n\n"
                     + md_table(["Technique", "Observer WS", "SD in window", "slope MiB/min", "anon",
                                 "Δ observer anon (primary)", "Δ observer WS", "Cluster used",
                                 "Δ obs anon % of memory", "p / Holm p (Δ anon)"], rows))

        # ---- breakdown
        comps = [c for c in BREAKDOWN if any(agg.stat(app, k, f"comp_cpu.{c}")[0] for k in conds_here)]
        rows = []
        for comp in comps:
            row = [comp]
            for k in conds_here:
                m_, s_, _ = agg.stat(app, k, f"comp_cpu.{comp}")
                row.append(f(m_, 3))
                csv_rows["components"].append([app, k, comp, m_, s_, agg.stat(app, k, f"comp_mem.{comp}")[0]])
            rows.append(row)
        parts.append("### Where the CPU goes (cores, steady window, mean over runs)\n\n"
                     + md_table(["Component"] + [LABEL[k] for k in conds_here], rows))

        # ---- steady latency / throughput (controlled load)
        rows = []
        b = {k: agg.stat(app, "baseline", f"steady.{k}") for k in ("rps", "p50_ms", "p95_ms", "p99_ms", "fail_pct")}
        rows.append(["baseline", pm(b["rps"][0], b["rps"][1], 2), pm(b["p50_ms"][0], b["p50_ms"][1], 1), "-",
                     pm(b["p95_ms"][0], b["p95_ms"][1], 1), "-", pm(b["p99_ms"][0], b["p99_ms"][1], 1), "-",
                     f(b["fail_pct"][0], 2)])
        for c in techs:
            cc = {k: agg.cmp(app, c, f"steady.{k}") for k in ("rps", "p50_ms", "p95_ms", "p99_ms", "fail_pct")}
            rows.append([LABEL[c], pm(cc["rps"]["c"], cc["rps"]["c_sd"], 2),
                         pm(cc["p50_ms"]["c"], cc["p50_ms"]["c_sd"], 1), ci(cc["p50_ms"], 1, "%", pct=True),
                         pm(cc["p95_ms"]["c"], cc["p95_ms"]["c_sd"], 1), ci(cc["p95_ms"], 1, "%", pct=True),
                         pm(cc["p99_ms"]["c"], cc["p99_ms"]["c_sd"], 1), ci(cc["p99_ms"], 1, "%", pct=True),
                         f(cc["fail_pct"]["c"], 2)])
            csv_rows["latency"].append([app, c] + [cc[k][x] for k in ("rps", "p50_ms", "p95_ms", "p99_ms")
                                                    for x in ("b", "c", "c_sd", "pct", "nd", "p")] + [cc["fail_pct"]["c"]])
        for mode in MODES:
            for c in techs:
                cm = agg.cmp(app, c, f"tp.{mode}.rps")
                cp99 = agg.cmp(app, c, f"tp.{mode}.p99_ms")
                csv_rows["fixed_rps"].append([app, mode, c, cm["b"], cm["c"], cm["pct"], cm["nd"],
                                              cp99["b"], cp99["c"], cp99["pct"], cp99["pct_lo"], cp99["pct_hi"]])
        lowrate = (b["rps"][0] or 0) < 5
        parts.append("### Steady window: generator throughput and latency (exploratory)\n\n"
                     "req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it "
                     "is a controlled input, not an outcome; throughput claims come from the fixed-count "
                     "table. Latency percentiles come from the generator's whole-Job summary; locust rounds "
                     "times above 100 ms to two significant digits, so one bucket step is 5-10%."
                     + (" At under 5 req/s the window holds few requests; do not read the p95/p99 deltas."
                        if lowrate else "") + "\n\n"
                     + md_table(["Technique", "req/s", "p50 (ms)", "Δ p50", "p95 (ms)", "Δ p95", "p99 (ms)", "Δ p99",
                                 "fail %"], rows))

        # ---- normalised cost and event rates
        rows = []
        th = THESIS_RATES.get(app)
        bgb = agg.stat(app, "baseline", "flows.bg_per_s")
        for c in conds_here:
            fr = agg.stat(app, c, "flows.workers_per_s")
            bgc = agg.stat(app, c, "flows.bg_per_s")
            af = agg.stat(app, c, "flows.app_per_s")
            ev = agg.stat(app, c, "client.hubble_lines_per_s")[0] if c == "hubble" else \
                agg.stat(app, c, "client.igtcp_lines_per_s")[0] if c == "ig_tcp" else None
            thr_ = (th[0] if c == "hubble" else th[1] if c == "ig_tcp" else None) if th else None
            if c == "baseline":
                rows.append([LABEL[c], f(fr[0], 1), f(bgc[0], 2), f(af[0], 2), "-", "-", "-", "-", "-"])
                continue
            ok = agg.cmp(app, c, "norm.keepalive.obs_us_per_req")
            on = agg.cmp(app, c, "norm.newconn.obs_us_per_req")
            oc = agg.cmp(app, c, "norm.newconn.obs_us_per_conn")
            nc = agg.cmp(app, c, "norm.newconn.node_us_per_conn")
            rows.append([LABEL[c], f(fr[0], 1), f(bgc[0], 2), f(af[0], 2), ci(ok, 0), ci(on, 0), ci(oc, 0), ci(nc, 0),
                         (f"{f(ev, 1)} (thesis {f(thr_, 1)})" if ev is not None else "-")])
            csv_rows["normalised"].append([app, c, fr[0], fr[1], agg.stat(app, c, "cpu.cluster.observer")[0],
                                           agg.stat(app, c, "norm.obs_mcores_per_kflow")[0], None, None, ev,
                                           agg.stat(app, c, "hubble.lost_events")[0], bgc[0], af[0],
                                           ok["delta"], ok["lo"], ok["hi"], on["delta"], oc["delta"], oc["lo"], oc["hi"],
                                           nc["delta"], nc["lo"], nc["hi"], agg.stat(app, c, "hubble.flows_per_s")[0],
                                           thr_, (ev / thr_) if ev is not None and thr_ else None])
            if ev is not None and thr_ and not (0.5 <= ev / thr_ <= 2.0):
                csv_rows["rate_flags"].append([app, c, ev, thr_])
        parts.append("### Cost per request and per new connection\n\n"
                     "flows/s: new TCP connections accepted by pods on the workers in the steady window "
                     "(PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle "
                     "segment, with no load: kubelet probes and other background. app/s = flows - bg. "
                     "Keep-alive load opens almost no connections, so a per-flow cost from the steady window "
                     "would divide idle cost by the probe rate; the costs below come from the fixed-count "
                     "tests instead: the observer CPU above its idle level during a test, per request "
                     "(exact count) and per new connection (newconn tests, background-corrected), as the "
                     "paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per "
                     "1000 connections/s. node/conn uses all busy CPU (indirect costs included). "
                     "events/s: the capture client's events with event time inside the analysis window, "
                     "next to the thesis journey-A capture rate of the same app.\n\n"
                     + md_table(["Technique", "flows/s", "bg/s", "app/s", "Δ obs µs/req keep-alive",
                                 "Δ obs µs/req newconn", "Δ obs µs/conn", "Δ node µs/conn", "events/s"], rows))

        # ---- Hubble mix and losses
        if "hubble" in conds_here:
            hm = {k: agg.stat(app, "hubble", f"hubble.mix.{k}_per_s")[0] for k in HUB_CLASSES}
            tot = sum(v for v in hm.values() if v) or None
            rows = [[k, f(hm[k], 1), f(100 * hm[k] / tot if tot and hm[k] is not None else None, 0) + "%"] for k in HUB_CLASSES]
            parts.append("### Hubble: what the agents processed (steady window, all namespaces)\n\n"
                         f"Flows processed/s by class, from hubble_flows_processed_total with identity "
                         f"context. client_feedback = traffic to and from hubble-relay (the capture client's "
                         f"own stream); probe = to or from reserved:host. cp-01 share of all flows: "
                         f"{f(100 * (agg.stat(app, 'hubble', 'hubble.cp_share')[0] or 0), 0)}%. Lost events: "
                         f"{f(agg.stat(app, 'hubble', 'hubble.lost_events')[0], 0)} in the window, "
                         f"{f(agg.stat(app, 'hubble', 'hubble.lost_events_run')[0], 0)} over the whole run "
                         f"(fixed-count tests included). hubble_* series at the end: "
                         f"{f(agg.stat(app, 'hubble', 'hubble.series_final')[0], 0)}.\n\n"
                         + md_table(["Class", "flows/s", "share"], rows))
            for k in HUB_CLASSES:
                csv_rows["hubble_mix"].append([app, k, hm[k], (hm[k] / tot) if tot and hm[k] is not None else None])

        # ---- ig_snap: standing vs snapshot
        if "ig_snap" in conds_here:
            st_ = agg.cmp(app, "ig_snap", "cpu.cluster.observer")
            sstand = agg.stat(app, "ig_snap", "snap.standing.cpu.cluster.observer")[0]
            bobs = agg.stat(app, "baseline", "cpu.cluster.observer")[0]
            scpu = agg.stat(app, "ig_snap", "snap.cpu_s")
            parts.append("### IG snapshot_socket: standing cost vs one snapshot\n\n"
                         f"Δ observer over the whole window {ci(st_, 3)} cores. Standing (window before the "
                         f"snapshot) minus baseline observer: "
                         f"{sign(sstand - bobs if sstand is not None and bobs is not None else None, 3)} cores; "
                         f"one snapshot adds {pm(scpu[0], scpu[1], 2)} CPU-seconds (observer + k3s, above the "
                         f"standing rate). The window mean therefore depends on the window length; the two "
                         "numbers above do not.\n")

        # ---- projection
        rows = []
        for c in techs:
            pc = agg.cmp(app, c, "proj.cpu")
            pu = agg.cmp(app, c, "proj.cpu_upper")
            pa = agg.cmp(app, c, "proj.cpu_all")
            pmm = agg.cmp(app, c, "proj.mem")
            rows.append([LABEL[c], ci(pc, 3), sign(pu["delta"], 3), ci(pa, 3),
                         sign(100 * pc["delta"] / THESIS["vcpu"] if pc["delta"] is not None else None, 2, "%")
                         + " / " + sign(100 * pa["delta"] / THESIS["vcpu"] if pa["delta"] is not None else None, 2, "%"),
                         ci(pmm, 0), sign(100 * pmm["delta"] / (THESIS["mem_gib"] * 1024) if pmm["delta"] is not None else None, 2, "%")])
            csv_rows["projection"].append([app, c, pc["b"], pc["c"], pc["delta"],
                                           100 * pc["delta"] / THESIS["vcpu"] if pc["delta"] is not None else None,
                                           pmm["b"], pmm["c"], pmm["delta"],
                                           100 * pmm["delta"] / (THESIS["mem_gib"] * 1024) if pmm["delta"] is not None else None,
                                           pc["lo"], pc["hi"], pu["delta"], pa["delta"], pa["lo"], pa["hi"],
                                           100 * pa["delta"] / THESIS["vcpu"] if pa["delta"] is not None else None])
        sums = [agg.cmp(app, c, "proj.cpu")["delta"] for c in ("hubble", "otterize", "ig_tcp")]
        tot_s = sum(sums) if all(v is not None for v in sums) else None
        parts.append("### test-cluster projection (estimate)\n\n"
                     "Observer only: the capture components' cost measured on the 3 bench nodes (they carry "
                     "the whole app load, which test-cluster split over its nodes too), plus for each node "
                     "test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from "
                     "the idle segment. Upper: the earlier method, every test-cluster node costs what the bench "
                     "node of its role costs under load; it triples cp-01, which here also carries the "
                     "generator and the capture clients. Observer + indirect: all busy CPU except the bench's "
                     "clients, generator and harness (adds k3s/containerd/API-server work, kernel time and "
                     "BPF work charged to the app), scaled the same way. Clients are left out: in the thesis "
                     "they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) "
                     "is not in the bench, so these are app-attributable costs. Isolated per technique; "
                     "test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add "
                     f"up, that configuration costs about {sign(tot_s, 3)} cores (observer only). "
                     f"Memory % uses about {THESIS['mem_gib']} GiB.\n\n"
                     + md_table(["Technique", "Δ CPU observer", "upper", "Δ CPU obs + indirect",
                                 f"% of {THESIS['vcpu']} vCPU (obs / all)", "Δ memory (MiB)",
                                 f"% of {THESIS['mem_gib']} GiB"], rows))

        # ---- per-run facts: order position, steal, host
        rows = []
        stl = [r.m.get("steal.frac_mean") for c in conds_here for r in agg.cells[(app, c)] if r.m.get("steal.frac_mean") is not None]
        med = statistics.median(stl) if stl else None
        for c in conds_here:
            for r in sorted(agg.cells[(app, c)], key=lambda r: r.rep):
                s_ = r.m.get("steal.frac_mean")
                hi_ = s_ is not None and med is not None and s_ > max(2 * med, 0.01)
                rows.append([r.rep, LABEL[c], r.meta.get("params", {}).get("order_pos") or "-",
                             f(100 * s_ if s_ is not None else None, 2) + "%" + (" (high)" if hi_ else ""),
                             r.info.get("play_id") or "-", r.info.get("boot_ids") or "-",
                             f(r.m.get("tp.newconn.time_s"), 2)])
                if hi_:
                    r.flags.append(f"steal {100 * s_:.2f}% is more than twice the app median ({100 * med:.2f}%)")
        parts.append("### Runs: order position, steal, host\n\n"
                     + md_table(["Rep", "Technique", "Position", "Steal (mean of nodes)", "Play", "Boot ids",
                                 "newconn time (s)"], rows))

        if layout == "cycle" or any(r.canary_seg for c in conds_here for r in agg.cells[(app, c)]):
            top, bottom = extra_parts(agg, app, conds_here, techs, layout, csv_rows)
            if agg_nf is not None:
                top.append(sensitivity_part(agg, agg_nf, app, techs, holm_p, first_ids, csv_rows))
            parts = top + parts + bottom
        n_used = {c: len(agg.cells.get((app, c), [])) for c in conds_here}
        md_parts[app] = (f"Runs used: " + ", ".join(f"{LABEL[c]} {n_used[c]}" for c in conds_here) + ".\n\n"
                         + ("In the standard tables below (from the Table 5 on), 'rep' means one interleaved "
                            "cycle: the cycle is the block of the paired comparison.\n\n" if layout == "cycle" else "")
                         + "\n\n".join(parts) + "\n")

    # ---- host identity across the whole results tree
    host_notes = []
    for app in apps:
        sigs = {r.host_sig for c in CONDS for r in agg.cells.get((app, c), []) if r.host_sig}
        if len(sigs) > 1:
            plays = sorted({str(s[0]) for s in sigs})
            host_notes.append(f"{app}: runs come from {len(sigs)} host sets (plays {', '.join(plays)}); deltas are "
                              "paired only within a rep on one host set")
        for rep in sorted({r.rep for c in CONDS for r in agg.cells.get((app, c), [])}):
            rs = {r.host_sig for c in CONDS for r in agg.cells.get((app, c), []) if r.rep == rep and r.host_sig}
            if len(rs) > 1:
                host_notes.append(f"{app} rep{rep}: the runs of this rep span {len(rs)} host sets; pairs across "
                                  "them are dropped from the paired estimates")

    # ---- summary across apps (by regime; n.s. and CI carried)
    summ = []
    for c in TECHS:
        def cell(app, key, pct=False, d=3, suffix=""):
            cm = agg.cmp(app, c, key)
            v = cm["pct"] if pct else cm["delta"]
            if v is None:
                return None
            return f"{app} {v:+.{d}f}{suffix}" + (" n.s." if cm.get("nd") else "")
        for reg in ("quota-bound", "node-bound"):
            apps_r = [a for a in apps if regime.get(a) == reg and agg.cells.get((a, c))]
            if not apps_r:
                continue
            cap_vals = []
            for app in apps_r:
                cm = agg.cmp(app, c, "cpu.cluster.node")
                cap = agg.stat(app, "baseline", "capacity.cpu.cluster")[0]
                if cm["delta"] is not None and cap:
                    cap_vals.append(f"{app} {100 * cm['delta'] / cap:+.2f}%" + (" n.s." if cm.get("nd") else ""))
            proj = [f"{a} {100 * agg.cmp(a, c, 'proj.cpu')['delta'] / THESIS['vcpu']:+.2f}%" for a in apps_r
                    if agg.cmp(a, c, "proj.cpu")["delta"] is not None]
            summ.append([LABEL[c], reg,
                         "; ".join(x for x in (cell(a, "cpu.cluster.observer") for a in apps_r) if x) or "-",
                         "; ".join(cap_vals) or "-",
                         "; ".join(x for x in (cell(a, "tp.keepalive.time_s", True, 1, "%") for a in apps_r) if x) or "-",
                         "; ".join(x for x in (cell(a, "tp.newconn.time_s", True, 1, "%") for a in apps_r) if x) or "-",
                         "; ".join(proj) or "-"])
            csv_rows["summary"].append([c, reg] + [";".join(str(agg.cmp(a, c, k)["pct" if pct else "delta"]) for a in apps_r)
                                                   for k, pct in (("cpu.cluster.observer", False), ("cpu.cluster.node", False),
                                                                  ("tp.keepalive.time_s", True), ("tp.newconn.time_s", True),
                                                                  ("proj.cpu", False))])

    # ---- the same summary from the canary-normalised metrics (only apps with canary data)
    summ_n = []
    for c in TECHS:
        def celln(app, key, pct=False, d=3, suffix=""):
            cm = agg.cmp(app, c, key)
            v = cm["pct"] if pct else cm["delta"]
            return None if v is None else f"{app} {v:+.{d}f}{suffix}" + (" n.s." if cm.get("nd") else "")
        apps_c = [a for a in apps if agg.cells.get((a, c)) and agg.cmp(a, c, "cn.cpu.cluster.node")["delta"] is not None]
        if not apps_c:
            continue
        capn = []
        for app in apps_c:
            cm = agg.cmp(app, c, "cn.cpu.cluster.node")
            cap = agg.stat(app, "baseline", "capacity.cpu.cluster")[0]
            if cap:
                capn.append(f"{app} {100 * cm['delta'] / cap:+.2f}%" + (" n.s." if cm.get("nd") else ""))
        summ_n.append([LABEL[c], "; ".join(x for x in (celln(a, "cn.cpu.cluster.observer") for a in apps_c) if x) or "-",
                       "; ".join(capn) or "-",
                       "; ".join(x for x in (celln(a, "cn.tp.keepalive.time_s", True, 1, "%") for a in apps_c) if x) or "-",
                       "; ".join(x for x in (celln(a, "cn.tp.newconn.time_s", True, 1, "%") for a in apps_c) if x) or "-"])

    # ---- exploratory: does Δ CPU scale with the app's connection rate?
    scale_rows = []
    for c in TECHS:
        xs, ys, names = [], [], []
        for app in apps:
            x = agg.stat(app, "baseline", "flows.app_per_s")[0]
            y = agg.cmp(app, c, "cpu.cluster.node")["delta"]
            if x is not None and y is not None:
                xs.append(x)
                ys.append(y)
                names.append(app)
        if len(xs) >= 3:
            b_ = lin_slope(xs, ys)
            a_ = statistics.fmean(ys) - b_ * statistics.fmean(xs) if b_ is not None else None
            scale_rows.append([LABEL[c], len(xs), f(a_, 3), f(1000 * b_ if b_ is not None else None, 2)])

    # exclusions and flags
    excl = [[r.app, r.rep, r.cond, r.status, r.reason] for r in runs if r.excluded]
    flags = [[r.app, r.rep, r.cond, fl] for r in runs if not r.excluded for fl in r.flags]
    for app, c, ev, thr_ in csv_rows["rate_flags"]:
        flags.append([app, "-", c, f"capture events/s {ev:.1f} is outside 0.5-2x the thesis journey-A rate {thr_:.1f}"])
    for note in host_notes:
        flags.append(["-", "-", "-", note])

    # ---- CSV
    write_csv(os.path.join(out, "runs.csv"), *_runs_table(runs))
    write_csv(os.path.join(out, "components_per_node.csv"),
              ["app", "rep", "cond", "node", "component", "cpu_cores_mean", "cpu_cores_sd", "mem_mib_mean", "mem_mib_max",
               "anon_mib_mean"],
              [[r.app, r.rep, r.cond, c["node"], c["component"], c["cpu_cores_mean"], c["cpu_cores_sd"],
                c["mem_mib_mean"], c["mem_mib_max"], c.get("anon_mib_mean")] for r in runs for c in r.comp_rows])
    tp_cols = ("mode", "i", "valid", "why", "tool", "total_s", "rps", "p50_ms", "p95_ms", "p99_ms", "n_2xx",
               "n_expected_status", "n_other", "n_err", "non2xx_pct", "job_wall_s", "ct_inserts_workers",
               "conn_corrected", "cpu_obs", "cpu_node", "cpu_k3s", "cpu_app", "cpu_cp_node", "thr_app", "bottleneck",
               "bottleneck_thr", "obs_excess_cpu_s", "node_excess_cpu_s")
    write_csv(os.path.join(out, "fixed_count_tests.csv"), ["app", "rep", "cond"] + list(tp_cols),
              [[r.app, r.rep, r.cond] + [t.get(k) for k in tp_cols] for r in runs for t in r.tp_rows])
    write_csv(os.path.join(out, "table5_fixed_count.csv"),
              ["app", "mode", "cond", "wo_s", "wo_sd", "wo_n", "with_s", "with_sd", "with_n", "overhead_pct",
               "not_distinguishable", "welch_p", "wo_exec_s", "wo_exec_sd", "wo_exec_n", "with_exec_s", "with_exec_sd",
               "with_exec_n", "overhead_ci_lo", "overhead_ci_hi", "paired_p", "holm_p", "n_pairs", "aa_cv_pct",
               "bottleneck_wo", "bottleneck_thr_wo", "bottleneck_with", "bottleneck_thr_with", "conn_per_req_wo",
               "conn_per_req_with", "cp01_busy_pct_with"], csv_rows["table5"])
    write_csv(os.path.join(out, "overhead_cpu.csv"),
              ["app", "cond", "obs_base", "obs_base_sd", "obs", "obs_sd", "obs_delta", "obs_nd", "obs_p",
               "cluster_base", "cluster_base_sd", "cluster", "cluster_sd", "cluster_delta",
               "cluster_delta_pct_of_bench_base", "cluster_delta_pct_of_capacity", "workers_delta",
               "workers_delta_pct_of_capacity", "cluster_nd", "cluster_p", "obs_ci_lo", "obs_ci_hi", "cluster_ci_lo",
               "cluster_ci_hi", "cluster_holm_p", "cluster_welch_p", "k3s_delta", "obs_sd_in_window",
               "cluster_sd_in_window"], csv_rows["cpu"])
    write_csv(os.path.join(out, "overhead_memory.csv"),
              ["app", "cond", "obs_base_mib", "obs_base_sd", "obs_mib", "obs_sd", "obs_peak_mib", "obs_delta_mib",
               "obs_nd", "obs_p", "cluster_base_mib", "cluster_base_sd", "cluster_mib", "cluster_sd",
               "cluster_delta_mib", "cluster_delta_pct_of_bench_base", "obs_delta_pct_of_cluster_memory", "obs_ci_lo",
               "obs_ci_hi", "obs_holm_p", "obs_sd_in_window", "obs_slope_mib_per_min", "obs_anon_mib", "obs_end_mib"],
              csv_rows["mem"])
    write_csv(os.path.join(out, "idle_standing_cost.csv"),
              ["app", "cond", "obs_delta", "obs_ci_lo", "obs_ci_hi", "k3s_delta", "node_delta", "node_ci_lo",
               "node_ci_hi", "idle_share_of_steady_obs_pct"], csv_rows["idle"])
    write_csv(os.path.join(out, "fixed_count_cpu.csv"),
              ["app", "mode", "cond", "obs_delta", "obs_ci_lo", "obs_ci_hi", "node_delta", "node_ci_lo", "node_ci_hi",
               "k3s_delta", "app_throttled_base", "app_throttled_with", "cp01_busy_cores_with"], csv_rows["tpcpu"])
    write_csv(os.path.join(out, "components_cpu_mem.csv"),
              ["app", "cond", "component", "cpu_cores_mean", "cpu_cores_sd", "mem_mib_mean"], csv_rows["components"])
    write_csv(os.path.join(out, "latency_throughput.csv"),
              ["app", "cond"] + [f"{k}_{x}" for k in ("rps", "p50_ms", "p95_ms", "p99_ms")
                                 for x in ("base", "with", "with_sd", "delta_pct", "nd", "p")] + ["fail_pct"],
              csv_rows["latency"])
    write_csv(os.path.join(out, "fixed_count_rps.csv"),
              ["app", "mode", "cond", "rps_base", "rps_with", "rps_delta_pct", "rps_nd", "p99_base_ms",
               "p99_with_ms", "p99_delta_pct", "p99_ci_lo", "p99_ci_hi"], csv_rows["fixed_rps"])
    write_csv(os.path.join(out, "normalised_cost.csv"),
              ["app", "cond", "flows_per_s", "flows_sd", "observer_cores", "mcores_per_kflow_steady_raw", "unused1",
               "unused2", "events_per_s", "hubble_lost_events", "bg_flows_per_s", "app_flows_per_s",
               "d_obs_us_per_req_keepalive", "lo", "hi", "d_obs_us_per_req_newconn", "d_obs_us_per_conn", "conn_lo",
               "conn_hi", "d_node_us_per_conn", "node_lo", "node_hi", "hubble_flows_processed_per_s",
               "thesis_events_per_s", "ratio_to_thesis"], csv_rows["normalised"])
    write_csv(os.path.join(out, "hubble_flow_mix.csv"), ["app", "class", "flows_per_s", "share"], csv_rows["hubble_mix"])
    write_csv(os.path.join(out, "projection_shiv_thesis.csv"),
              ["app", "cond", "proj_cpu_base", "proj_cpu", "delta_cores", "delta_pct_of_18vcpu", "proj_mem_base_mib",
               "proj_mem_mib", "delta_mib", "delta_pct_of_mem", "ci_lo", "ci_hi", "delta_cores_upper",
               "delta_cores_obs_plus_indirect", "all_ci_lo", "all_ci_hi", "all_pct_of_18vcpu"], csv_rows["projection"])
    write_csv(os.path.join(out, "summary_across_apps.csv"),
              ["cond", "regime", "delta_observer_cores", "delta_cluster_cores", "keepalive_overhead_pct",
               "newconn_overhead_pct", "proj_cores"], csv_rows["summary"])
    write_csv(os.path.join(out, "excluded_runs.csv"), ["app", "rep", "cond", "status", "reason"], excl)
    write_csv(os.path.join(out, "data_flags.csv"), ["app", "rep", "cond", "flag"], flags)

    # ---- cycle / canary CSVs (only when there is something to put in them)
    if csv_rows["sensitivity"]:
        write_csv(os.path.join(out, "sensitivity.csv"),
                  ["app", "endpoint", "technique", "primary", "primary_lo", "primary_hi", "holm_p", "median",
                   "wilcoxon_p", "no_first_run", "no_first_run_lo", "no_first_run_hi", "no_first_run_pairs",
                   "verdict"], csv_rows["sensitivity"])
    if csv_rows["paired"]:
        write_csv(os.path.join(out, "paired_deltas.csv"),
                  ["app", "endpoint", "cond", "n_pairs", "raw_base", "raw_with", "raw_delta", "raw_ci_lo", "raw_ci_hi",
                   "raw_pct", "raw_pct_lo", "raw_pct_hi", "raw_p", "raw_holm_p", "norm_base", "norm_with", "norm_delta",
                   "norm_ci_lo", "norm_ci_hi", "norm_pct", "norm_pct_lo", "norm_pct_hi", "norm_p", "norm_holm_p"],
                  csv_rows["paired"])
    if csv_rows["drift"]:
        write_csv(os.path.join(out, "drift_per_block.csv"),
                  ["app", "layout", "block", "start_epoch", "order", "base_keepalive_s", "base_keepalive_s_norm",
                   "base_newconn_s", "base_newconn_s_norm", "base_app_cores", "base_app_cores_norm",
                   "base_node_cores", "base_node_cores_norm", "base_canary_idle", "base_canary_steady",
                   "base_canary_tp_keepalive", "base_canary_tp_newconn", "base_canary_ratio_workers",
                   "block_mean_canary_steady"], csv_rows["drift"])
        write_csv(os.path.join(out, "drift_summary.csv"),
                  ["app", "layout", "mode", "blocks", "cv_raw_pct", "cv_norm_pct", "r_time_vs_inv_speed"],
                  csv_rows["drift_summary"])
    if csv_rows["canary_seg"]:
        write_csv(os.path.join(out, "canary_segments.csv"),
                  ["app", "layout", "block", "cond", "segment", "node", "lo", "hi", "kernel_runs", "speed_cpu",
                   "speed_wall", "ref_speed_cpu", "ratio"], csv_rows["canary_seg"])
    if csv_rows["table5n"]:
        write_csv(os.path.join(out, "table5_fixed_count_normalised.csv"),
                  ["app", "mode", "cond", "wo_exec_s", "wo_exec_sd", "wo_exec_n", "with_exec_s", "with_exec_sd",
                   "with_exec_n", "overhead_pct", "overhead_ci_lo", "overhead_ci_hi", "not_distinguishable",
                   "paired_p", "holm_p_across_techniques", "n_pairs"], csv_rows["table5n"])

    # ---- Markdown
    for app in apps:
        with open(os.path.join(out, f"tables-{app}.md"), "w") as fh:
            fh.write(f"# {app}\n\n{md_parts[app]}")
    write_results_md(out, root, runs, apps, md_parts, summ, excl, flags, args, scale_rows, layout, summ_n)


def _param(agg, app, key):
    for r in agg.cells.get((app, "baseline"), []):
        v = r.meta.get("params", {}).get(key)
        if v is not None:
            return v
    return "?"


def _fmt_int(x):
    return "?" if x is None else f"{x:.0f}"


def _runs_table(runs):
    keys = sorted({k for r in runs for k in r.m})
    ikeys = sorted({k for r in runs for k in r.info})
    headers = ["app", "rep", "cond", "status", "excluded", "reason", "short", "flags"] + keys + ikeys
    rows = []
    for r in sorted(runs, key=lambda r: (r.app, r.rep, CONDS.index(r.cond))):
        rows.append([r.app, r.rep, r.cond, r.status, r.excluded, r.reason, r.short, "; ".join(r.flags)]
                    + [r.m.get(k) for k in keys] + [r.info.get(k) for k in ikeys])
    return headers, rows


def write_results_md(out, root, runs, apps, md_parts, summ, excl, flags, args, scale_rows, layout="rep", summ_n=None):
    used = [r for r in runs if not r.excluded]
    p0 = used[0].meta.get("params", {}) if used else {}
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    cyc = layout == "cycle"
    L = []
    L.append("# Capture overhead: interleaved cycles (randomized multiple interleaved trials)\n" if cyc else
             "# Capture overhead: performance benchmark results\n")
    L.append(f"Generated {now} by analyze/analyze.py from `{root}`. "
             f"{len(runs)} run directories, {len(used)} used, {len(runs) - len(used)} excluded.\n")
    L.append("## Setup\n")
    L.append("- Cluster: iximiuz play, k3s, Cilium 1.19.5 configured like test-cluster. cp-01 has 2 vCPU "
             "and runs the load generator and the capture clients. worker-01 and worker-02 have 4 vCPU "
             "each and run the app.")
    L.append("- Conditions: baseline (Cilium, Hubble off, no other observer), Hubble (agent Hubble on, "
             "Relay, `hubble observe` through `kubectl port-forward` as in the thesis), Otterize (mapper and "
             "sniffers), IG trace_tcp (gadget DaemonSet and a streaming client), IG snapshot_socket (gadget "
             "DaemonSet and one snapshot near the end of the window). A metrics scraper fetches :9962, :9963 "
             "and :9965 every 15 s in every condition, like test-cluster' Prometheus.")
    L.append(f"- Each run: fresh Cilium agents and app pods, a {f(p0.get('idle_s'), 0)} s idle segment "
             f"(observer on, no load), {f(p0.get('warmup_s'), 0)} s warm-up, a {f(p0.get('steady_s'), 0)} s "
             f"steady window with the thesis journey-A load, then the fixed-count tests "
             f"({p0.get('tp_n', '?')} requests, concurrency {p0.get('tp_c', '?')}, {p0.get('tp_reps', '?')} "
             "repeats per mode, keep-alive and new connection per request).")
    if cyc:
        L.append("- Order: K short cycles, each running every condition once; the order of cycle k is "
                 "sequence k of a Williams design for 5 conditions (10 sequences: every condition twice in "
                 "every position, every ordered pair of conditions adjacent twice), cycles 11-20 the same set "
                 "in a fresh seeded order. Pairing within a cycle cancels host drift slower than a cycle "
                 "(about an hour); the design spreads faster drift evenly over the conditions (Abedi and "
                 "Brecht, ICPE 2017). A host-speed canary on every node gives the canary-normalised "
                 f"columns. CPU and memory come from cgroup counters sampled every {f(p0.get('sample_s'), 0)} s "
                 "on every node.")
    else:
        L.append("- Order: a balanced position design per app (every condition at three different positions, "
                 "mean position 3 ± 1/3), so drift within a rep hits every condition about equally. CPU and "
                 f"memory come from cgroup counters sampled every {f(p0.get('sample_s'), 0)} s on every node.")
    L.append(f"- The analysis uses the steady window minus its first {args.trim_head:.0f} s and last "
             f"{args.trim_tail:.0f} s.\n")
    L.append("## How to read the tables\n")
    if cyc:
        nb = max((len({r.rep for r in used if r.app == a}) for a in apps), default=0)
        L.append("- Each cycle is a block: every Δ is the mean of the per-cycle differences (technique minus "
                 "the same cycle's baseline), with a t-based 95% CI (df = cycles - 1) in brackets"
                 + (f"; with {nb} cycles the t quantile is {t_ppf(0.975, nb - 1):.2f}" if nb >= 2 else "")
                 + ". In the standard tables 'rep' means cycle. The first table of each app gives every "
                 "endpoint raw and canary-normalised, with Holm across the techniques; the drift diagnostic "
                 "shows whether the host moved during the matrix.")
    else:
        L.append("- Each rep is a block: every Δ is the mean of the per-rep differences (technique minus the "
                 "same rep's baseline), with a t-based 95% CI (df = reps - 1) in brackets. With 3 reps the "
                 "t quantile is 4.30, so CIs are wide.")
    L.append("- \"n.s.\" means the 95% CI includes 0. For a fixed-count overhead the upper CI bound is "
             "then given as the most the overhead can be.")
    L.append("- Primary endpoints (Holm-adjusted per app over 4 techniques x 4 endpoints): Δ cluster busy "
             "CPU, Δ observer memory, fixed-count time keep-alive and new connection. All other p-values "
             "are exploratory and unadjusted. Welch's test on the run values is in the CSVs as a second "
             "check.")
    L.append("- Δ is the technique minus the baseline. A negative Δ is noise or a side effect, not a saving.")
    L.append("- Transferable numbers: Δ cores, Δ MiB, Δ % of capacity, the fixed-count overhead and the "
             "projection. A percentage of this bench's baseline is not transferable to test-cluster, whose "
             "baseline carried the whole platform.\n")
    L.append("## Summary across apps\n")
    L.append("Per-app values, grouped by what limits the fixed-count test (quota-bound: throttled app "
             "containers; node-bound: node CPU). Steady-window latency is left out of the summary: it is "
             "bucket-limited and the steady load is a controlled input.\n")
    L.append(md_table(["Technique", "Regime", "Δ observer CPU (cores)", "Δ cluster CPU, % of capacity",
                       "Fixed-count overhead, keep-alive", "Fixed-count overhead, new conn",
                       "test-cluster CPU, % of 18 vCPU (est.)"], summ))
    L.append("")
    if summ_n:
        L.append("Diagnostic only, do not quote: the same, canary-normalised (each run scaled to the app's "
                 "median canary speed). The 2026-10-03 validation showed the canary does not track the host "
                 "drift (r 0.41, normalised CV 16.4% vs 16.6% raw) and inflates deltas 1.7-4.7x. The raw "
                 "paired deltas above, over interleaved cycles, are the result.\n")
        L.append(md_table(["Technique", "Δ observer CPU (cores)", "Δ cluster CPU, % of capacity",
                           "Fixed-count overhead, keep-alive", "Fixed-count overhead, new conn"], summ_n))
        L.append("")
    if scale_rows:
        L.append("Exploratory: Δ cluster CPU = a + b x app connection rate, fitted across apps "
                 "(b in millicores per 1 connection/s). With at most 5 apps this is a trend, not a model.\n")
        L.append(md_table(["Technique", "apps", "a (cores)", "b (mcores per conn/s)"], scale_rows))
        L.append("")
    for app in apps:
        L.append(f"## {app}\n")
        L.append(md_parts[app])
    L.append("## Excluded runs\n")
    if excl:
        L.append(md_table(["App", "Rep", "Condition", "Status", "Reason"], excl))
    else:
        L.append("None.")
    L.append("")
    L.append("## Data warnings in used runs\n")
    if flags:
        L.append(md_table(["App", "Rep", "Condition", "Warning"], flags))
    else:
        L.append("None.")
    L.append("")
    L.append("## Method notes\n")
    L.append("- Observer CPU and memory include cilium-agent, cilium-envoy and cilium-operator in every "
             "condition, so the baseline row is not zero. The Δ columns are the cost of the technique.")
    L.append("- Cluster busy CPU comes from /proc/stat on each node (user + nice + system + irq + softirq; "
             "steal and iowait left out). It also catches indirect costs: API-server and kubelet work for "
             "`kubectl port-forward` and `kubectl gadget` streams, exec probes of the gadget DaemonSet, "
             "and BPF work in the app's syscalls or in softirq. The kernel here has "
             "CONFIG_IRQ_TIME_ACCOUNTING off, so softirq time is charged to whatever task it interrupts.")
    L.append("- The fixed-count time is the tool's own total (hey `Total`), so pod start-up is not in it.")
    L.append("- The steady-window per-flow cost is not reported: the journey-A load keeps connections "
             "open, so almost every new connection in the window is a kubelet probe. Per-request and "
             "per-connection costs come from the fixed-count tests.")
    L.append("- Events/s for Hubble and IG count client events whose event time falls inside the analysis "
             "window (client_bins.json), so both use the same window and the app namespace only.")
    L.append("- The projection is an estimate with two known gaps: no platform background traffic, and "
             "a different CPU model and kernel (6.12 here, 6.8 on test-cluster).")
    if cyc or any(r.canary_seg for r in used):
        L.append("- Host-speed canary (bin/canary.py): every 2 s each node runs a fixed pure-Python integer "
                 "loop and logs its thread CPU time. Iterations per CPU-second is the host speed index; it "
                 "falls when the hypervisor gives the guest less work per CPU-second (unreported steal, a "
                 "busy sibling thread, a lower clock). Normalised CPU = cores x speed / the app's median "
                 "speed (per node); normalised fixed-count time = time x the workers' speed ratio during "
                 "the test. The canary costs about 1% of one core per node and is counted as harness.")
    with open(os.path.join(out, "RESULTS-CYCLES.md" if cyc else "RESULTS-PERF.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")


# --------------------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="perf-benchmark analysis")
    ap.add_argument("results_root")
    ap.add_argument("--out", default=None, help="output dir (default <results_root>/analysis)")
    ap.add_argument("--short", action="store_true", help="analyse --short runs (default: full runs only)")
    ap.add_argument("--trim-head", type=float, default=15.0, help="seconds cut from the window start")
    ap.add_argument("--trim-tail", type=float, default=10.0, help="seconds cut from the window end")
    ap.add_argument("--tp-tolerance", type=float, default=0.0,
                    help="fraction of fixed-count requests allowed to miss TP_EXPECT_STATUS (default 0: all must match)")
    ap.add_argument("--apps", nargs="*", default=None)
    args = ap.parse_args()

    root, runs = discover(args.results_root)
    if args.apps:
        runs = [r for r in runs if r.app in args.apps]
    if not runs:
        print(f"no run directories under {root}", file=sys.stderr)
        return 1
    out = args.out or os.path.join(root, "analysis")
    os.makedirs(out, exist_ok=True)
    for r in runs:
        try:
            analyze_run(r, args.trim_head, args.trim_tail, args.tp_tolerance)
        except Exception as e:  # noqa: BLE001  one broken run must not stop the analysis
            r.excluded, r.reason = True, f"analysis error: {type(e).__name__}: {e}"
        # --short selects the rep-layout runs; cycle runs have their own profile and are always used
        if r.layout == "rep" and not r.excluded and r.short is not None and r.short != args.short:
            r.excluded, r.reason = True, ("short run (use --short)" if r.short else "full run (analysing --short)")
        if r.layout == "cycle" and not r.excluded and (r.meta.get("profile") or "cycle") != "cycle":
            r.excluded, r.reason = True, f"profile {r.meta.get('profile')} in a cycle directory"
    normalise_by_canary(runs)
    rep_runs = [r for r in runs if r.layout == "rep"]
    cyc_runs = [r for r in runs if r.layout == "cycle"]
    if rep_runs:
        build(root, rep_runs, out, args)
        n_ok = sum(1 for r in rep_runs if not r.excluded)
        print(f"analysed {len(rep_runs)} runs ({n_ok} used) -> {out}/RESULTS-PERF.md", file=sys.stderr)
    if cyc_runs:
        cout = os.path.join(out, "cycles")
        os.makedirs(cout, exist_ok=True)
        build(root, cyc_runs, cout, args, layout="cycle")
        n_ok = sum(1 for r in cyc_runs if not r.excluded)
        print(f"analysed {len(cyc_runs)} cycle runs ({n_ok} used) -> {cout}/RESULTS-CYCLES.md", file=sys.stderr)
    print(f"Welch p-values via {'scipy' if _scipy_stats else 'built-in t distribution'}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
