#!/usr/bin/env python3
"""selftest.py [--keep DIR]

Builds a synthetic results tree with known overheads (two apps, 5 conditions, 3 reps, one
FAILED run, one interrupted run, one --short run, a clock offset on worker-01 and a container
restart mid-window), runs analyze.py on it and checks that the tables recover the injected
values. Also checks the parsers on real tool output shapes and the built-in Welch p-value
against scipy when scipy is importable.
Interleaved cycles and the host-speed canary: a third app (synthC) in the cycle layout, 10 cycles
in Williams-design order, with a host whose speed drifts by +-35% (plus a 15% step) over the
matrix; all CPU and fixed-count times scale with 1/speed and the canary sees the speed. The
canary-normalised estimates must recover the injected overheads, the drift diagnostic must see
the drift, and the pb-canary scope must count as harness. synthB (rep layout) gets canary data
at a constant speed: its normalised numbers must equal the raw ones. bin/lib.sh pb_williams is
checked for position and carry-over balance when bash >= 4 is on PATH. Exit 0 = all checks passed.
"""
import argparse
import csv
import gzip
import json
import math
import os
import random
import shutil
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import analyze  # noqa: E402
MAIN_CONDS = ["baseline", "hubble", "otterize", "ig_tcp", "ig_snap"]   # the main 5-condition design; hubble_agent is tested in selftest_agentonly

NODES = {"cp-01": (2, 3 * 1024), "worker-01": (4, 6656), "worker-02": (4, 6656)}
OFFSET = {"cp-01": 0.0, "worker-01": 60.0, "worker-02": -0.7}   # node clock - cp clock
T0 = 1_790_000_000.0
WARM, STEADY = 180.0, 1200.0
S0 = T0 + 400.0                          # steady_start (cp clock)
INTERVAL = 5.0
TP_N = 10000

# per node: (kind, id, ns, pod, container) -> (cores, MiB); the app only loads its pods in the window
BASE = {
    "cp-01": {("container", "c" * 63 + "1", "kube-system", "cilium-x1", "cilium-agent"): (0.05, 150),
              ("container", "c" * 63 + "2", "kube-system", "cilium-envoy-e1", "cilium-envoy"): (0.01, 30),
              ("unit", "k3s.service", "", "", ""): (0.30, 900),
              ("unit", "perfbench-sampler.service", "", "", ""): (0.002, 20),
              ("unit", "ssh.service", "", "", ""): (0.01, 10),
              ("container", "c" * 63 + "3", "APP", "pb-steady-abcde", "locust"): (0.15, 120)},
    "worker-01": {("container", "d" * 63 + "1", "kube-system", "cilium-x2", "cilium-agent"): (0.05, 150),
                  ("container", "d" * 63 + "2", "kube-system", "cilium-envoy-e2", "cilium-envoy"): (0.01, 30),
                  ("container", "d" * 63 + "3", "kube-system", "cilium-operator-6f-x", "cilium-operator"): (0.005, 40),
                  ("unit", "k3s-agent.service", "", "", ""): (0.08, 200),
                  ("container", "d" * 63 + "4", "APP", "frontend-1", "server"): (0.20, 100),
                  ("container", "d" * 63 + "5", "APP", "cart-1", "server"): (0.20, 100),
                  ("container", "d" * 63 + "6", "APP", "db-1", "db"): (0.20, 300)},
    "worker-02": {("container", "e" * 63 + "1", "kube-system", "cilium-x3", "cilium-agent"): (0.05, 150),
                  ("container", "e" * 63 + "2", "kube-system", "cilium-envoy-e3", "cilium-envoy"): (0.01, 30),
                  ("container", "e" * 63 + "3", "kube-system", "coredns-7b-x", "coredns"): (0.01, 25),
                  ("unit", "k3s-agent.service", "", "", ""): (0.08, 200),
                  ("container", "e" * 63 + "4", "APP", "checkout-1", "server"): (0.20, 100),
                  ("container", "e" * 63 + "5", "APP", "payment-1", "server"): (0.20, 100),
                  ("container", "e" * 63 + "6", "APP", "redis-1", "redis"): (0.20, 50)},
}
ADD = {   # condition -> node -> key -> (cores, MiB) added on top of BASE (or new cgroups)
    "baseline": {},
    "hubble": {"cp-01": {("container", "c" * 63 + "1", "kube-system", "cilium-x1", "cilium-agent"): (0.10, 40),
                         ("client", "pb-hubble.scope", "", "", ""): (0.08, 50)},
               "worker-01": {("container", "d" * 63 + "1", "kube-system", "cilium-x2", "cilium-agent"): (0.10, 40)},
               "worker-02": {("container", "e" * 63 + "1", "kube-system", "cilium-x3", "cilium-agent"): (0.10, 40),
                             ("container", "e" * 63 + "9", "kube-system", "hubble-relay-5d-x", "hubble-relay"): (0.05, 60)}},
    "otterize": {"worker-01": {("container", "d" * 63 + "8", "otterize-system", "otterize-network-mapper-7c-x", "mapper"): (0.06, 80),
                               ("container", "d" * 63 + "9", "otterize-system", "otterize-network-sniffer-a", "sniffer"): (0.04, 40)},
                 "worker-02": {("container", "e" * 63 + "8", "otterize-system", "otterize-network-sniffer-b", "sniffer"): (0.04, 40)}},
    "ig_tcp": {"cp-01": {("container", "c" * 63 + "8", "gadget", "gadget-a", "gadget"): (0.07, 100),
                         ("client", "pb-igtcp.scope", "", "", ""): (0.05, 60)},
               "worker-01": {("container", "d" * 63 + "7", "gadget", "gadget-b", "gadget"): (0.07, 100)},
               "worker-02": {("container", "e" * 63 + "7", "gadget", "gadget-c", "gadget"): (0.07, 100)}},
    "ig_snap": {"cp-01": {("container", "c" * 63 + "8", "gadget", "gadget-a", "gadget"): (0.01, 90)},
                "worker-01": {("container", "d" * 63 + "7", "gadget", "gadget-b", "gadget"): (0.01, 90)},
                "worker-02": {("container", "e" * 63 + "7", "gadget", "gadget-c", "gadget"): (0.01, 90)}},
}
TRUTH = {  # expected deltas vs baseline
    "obs_cpu": {"hubble": 0.43, "otterize": 0.14, "ig_tcp": 0.26, "ig_snap": 0.03},
    "obs_mem": {"hubble": 230, "otterize": 160, "ig_tcp": 360, "ig_snap": 270},
    "proj_cpu": {"hubble": 0.65, "otterize": 0.18, "ig_tcp": 0.42, "ig_snap": 0.06},
    "tp_base": {"keepalive": 4.0, "newconn": 6.0},          # seconds without capture
    "tp": {"keepalive": {"baseline": 1.0, "hubble": 1.02, "otterize": 1.01, "ig_tcp": 1.03, "ig_snap": 1.0},
           "newconn": {"baseline": 1.0, "hubble": 1.05, "otterize": 1.03, "ig_tcp": 1.08, "ig_snap": 1.0}},
    "p95_base": 100.0,                                       # ms without capture
    "p95": {"baseline": 1.0, "hubble": 1.05, "otterize": 1.02, "ig_tcp": 1.04, "ig_snap": 1.0},
    "rps": 20.0, "flows_per_worker": 400.0,
}
BG_PER_WORKER = 3.0     # background accepts per second per worker in the idle segment


def locust_csv(rps, p95):
    hdr = ("Type,Name,Request Count,Failure Count,Median Response Time,Average Response Time,Min Response Time,"
           "Max Response Time,Average Content Size,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%")
    n = int(rps * STEADY)
    agg = (f",Aggregated,{n},{n // 100},40,55.2,3,900,1200,{rps:.4f},0.2,40,50,60,65,80,{p95:.1f},"
           f"{p95 * 1.3:.1f},{p95 * 1.6:.1f},400,800,900")
    return ("[2026-10-02 12:00:00,000] cp-01/INFO/locust.main: Starting Locust 2.31.5\n"
            "some printed table lines | that are not csv\n" + hdr + "\nGET,/,10,0,40,50,3,90,1200,1.0,0,40,50,60,65,80,90,95,98,99,99,99\n"
            + agg + "\n")


def wrk2_out(rps, p95):
    n = int(rps * STEADY)
    return (f"Running 20m test @ http://nginx-thrift:8080/wrk2-api/home-timeline/read\n"
            f"  2 threads and 8 connections\n  Thread calibration: mean lat.: 4.2ms\n"
            f"  Latency Distribution (HdrHistogram - Recorded Latency)\n"
            f" 50.000%   40.00ms\n 75.000%   55.00ms\n 90.000%   70.00ms\n 95.000%   {p95:.2f}ms\n"
            f" 99.000%  {p95 * 1.6:.2f}ms\n 99.900%  261.25ms\n100.000%    1.20s\n\n"
            f"  Detailed Percentile spectrum:\n       Value   Percentile   TotalCount 1/(1-Percentile)\n"
            f"       4.743     0.989062         5713        91.43\n"
            f"----------------------------------------------------------\n"
            f"  {n} requests in 20.00m, 64.31MB read\n  Socket errors: connect 0, read 0, write 0, timeout 8\n"
            f"Requests/sec:     {rps:.2f}\nTransfer/sec:    219.49KB\n")


def hey_out(total, n):
    return (f"\nSummary:\n  Total:\t{total:.4f} secs\n  Slowest:\t0.2000 secs\n  Fastest:\t0.0010 secs\n"
            f"  Average:\t0.0100 secs\n  Requests/sec:\t{n / total:.4f}\n\n  Total data:\t123 bytes\n\n"
            f"Response time histogram:\n  0.001 [1]\t|\n\nLatency distribution:\n  10% in 0.0050 secs\n"
            f"  25% in 0.0070 secs\n  50% in 0.0100 secs\n  75% in 0.0150 secs\n  90% in 0.0200 secs\n"
            f"  95% in 0.0250 secs\n  99% in 0.0400 secs\n\nDetails (average, fastest, slowest):\n"
            f"  DNS+dialup:\t0.0001 secs, 0.0000 secs, 0.0100 secs\n\nStatus code distribution:\n"
            f"  [200]\t{n} responses\n\n")


def ct_text(ts, insert):
    hdr = ("entries  clashres found new invalid ignore delete chainlength insert insert_failed drop early_drop "
           "icmp_error  expect_new expect_create expect_delete search_restart")
    half = insert // 2
    row = lambda v: " ".join(["0000002a"] + ["00000000"] * 7 + [f"{v:08x}"] + ["00000000"] * 8)
    return f"# ts={ts:.3f}\n{hdr}\n{row(half)}\n{row(insert - half)}\n# count=42\n# conntrack -S\n"


def canary_csv(path, node, t_lo, t_hi, offset, speed_fn, rng, iters=150000):
    """canary-<node>.csv as bin/canary.py writes it: one kernel run every 2 s, node clock"""
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["ts", "node", "seq", "cpu", "iterations", "wall_ns", "cpu_ns", "invol_cs"])
        t, k = t_lo, 0
        while t <= t_hi:
            cpu_ns = int(iters / (speed_fn(t) * (1 + rng.gauss(0, 0.003))) * 1e9)
            w.writerow([f"{t + offset:.3f}", node, k, k % 4, iters, int(cpu_ns * 1.02), cpu_ns, 1])
            t += 2.0
            k += 1
    with open(path + ".info.json", "w") as fh:
        json.dump({"node": node, "iterations": iters, "interval_s": 2.0, "own_cpu_pct_of_core": 0.9}, fh)


def write_run(root, app, steady_kind, rep, cond, rng, status="DONE", short=False, restart=False, canary=False):
    d = os.path.join(root, app, f"rep{rep}", cond)
    os.makedirs(os.path.join(d, "tp"), exist_ok=True)
    os.makedirs(os.path.join(d, "ct"), exist_ok=True)
    os.makedirs(os.path.join(d, "metrics"), exist_ok=True)
    end = S0 + STEADY + 3.0
    phases = {"run_start": T0, "cond_start": T0 + 5, "cond_end": T0 + 90, "samplers_started": T0 + 140,
              "client_started": T0 + 150, "idle_start": T0 + 152, "idle_end": T0 + 212,
              "warmup_start": S0 - WARM - 5, "warmup_end": S0 - 5,
              "steady_start": S0, "steady_job_complete": end, "clients_stopped": end + 400}
    tp_tests = []
    t = end + 10
    for mode in ("keepalive", "newconn"):
        for i in (1, 2, 3):
            total = TRUTH["tp_base"][mode] * TRUTH["tp"][mode][cond] + rng.gauss(0, 0.01)
            with open(os.path.join(d, "tp", f"{mode}-{i}.log"), "w") as fh:
                txt = hey_out(total, TP_N)
                if app == "synthA" and rep == 1 and cond == "ig_snap" and mode == "newconn" and i == 3:
                    txt = txt.replace(f"[200]\t{TP_N} responses", f"[200]\t{TP_N - 10} responses\n  [302]\t10 responses")
                fh.write(txt)
            tag = f"tp_{mode}_{i}"
            for n in ("worker-01", "worker-02"):
                with open(os.path.join(d, "ct", f"{tag}.pre.{n}.txt"), "w") as fh:
                    fh.write(ct_text(t, 5_000_000))
                with open(os.path.join(d, "ct", f"{tag}.post.{n}.txt"), "w") as fh:
                    fh.write(ct_text(t + total, 5_000_000 + (3 * TP_N if mode == "newconn" else 200)))
            tp_tests.append({"mode": mode, "i": i, "job": f"pb-tp-{mode}-{i}", "ok": True, "n": TP_N, "c": 16,
                             "created": t - 3, "start": t, "end": t + total + 1, "log": f"tp/{mode}-{i}.log",
                             "ct_prefix": f"ct/{tag}"})
            phases[f"tp_{mode}_{i}_start"] = t
            t += total + 25
    if cond == "ig_snap":
        phases["snap_start"], phases["snap_end"] = S0 + STEADY - 45, S0 + STEADY - 30
    meta = {"schema": 1, "status": status, "app": app, "app_ns": app, "cond": cond, "rep": rep, "short": short,
            "params": {"warmup_s": WARM, "steady_s": STEADY, "tp_reps": 3, "tp_n": TP_N, "tp_c": 16,
                       "tp_pause_s": 20, "snap_lead_s": 45, "sample_s": INTERVAL},
            "phases": phases, "nodes": {"cp": "cp-01", "list": list(NODES), "clock_offset_s": OFFSET},
            "tp_tests": tp_tests, "kv": {"client_out.hubble.json.lines": "360000"} if cond == "hubble" else {},
            "warnings": []}
    with open(os.path.join(d, "meta.json"), "w") as fh:
        json.dump(meta, fh)
    p95 = TRUTH["p95_base"] * TRUTH["p95"][cond] * (1 + rng.gauss(0, 0.003))
    with open(os.path.join(d, "steady.log"), "w") as fh:
        fh.write(locust_csv(TRUTH["rps"], p95) if steady_kind == "locust" else wrk2_out(TRUTH["rps"], p95))
    for n in ("worker-01", "worker-02"):   # idle segment: background accepts only (BG_PER_WORKER/s)
        with open(os.path.join(d, "ct", f"idle_pre.{n}.txt"), "w") as fh:
            fh.write(ct_text(T0 + 151, 900_000))
        with open(os.path.join(d, "ct", f"idle_post.{n}.txt"), "w") as fh:
            fh.write(ct_text(T0 + 213, 900_000 + int(BG_PER_WORKER * 62)))
    if cond in ("hubble", "ig_tcp"):        # client events per 5-s bin of event time
        per_bin = 150 if cond == "hubble" else 25
        bins = {str(int(b)): per_bin for b in range(int(S0 - 300) // 5 * 5, int(end + 400), 5)}
        with open(os.path.join(d, "client_bins.json"), "w") as fh:
            json.dump({"bin_s": 5, ("hubble" if cond == "hubble" else "ig_tcp"): {"counts": bins}}, fh)
    for n in ("worker-01", "worker-02"):
        with open(os.path.join(d, "ct", f"steady_pre.{n}.txt"), "w") as fh:
            fh.write(ct_text(S0 - 8, 1_000_000))
        with open(os.path.join(d, "ct", f"steady_post.{n}.txt"), "w") as fh:
            fh.write(ct_text(end + 1, 1_000_000 + int(TRUTH["flows_per_worker"] * (end - S0))))
    for n in NODES:
        for lab, v in (("steady_pre", 1000), ("steady_post", 1000 + 300 * (end - S0))):
            with open(os.path.join(d, "metrics", f"{lab}.{n}.hubble.prom"), "w") as fh:
                if cond == "hubble":
                    fh.write(f"# ts={S0}\nhubble_flows_processed_total{{type=\"L3_L4\"}} {v}\nhubble_lost_events_total{{source=\"x\"}} 0\n")
                else:
                    fh.write(f"# ts={S0}\n")
    # samples
    for node, (ncpu, memmib) in NODES.items():
        comps = dict(BASE[node])
        for k, (c, m) in ADD[cond].get(node, {}).items():
            c0, m0 = comps.get(k, (0.0, 0.0))
            comps[k] = (c0 + c, m0 + m)
        comps = {(k[0], k[1], k[2].replace("APP", app), k[3], k[4]): v for k, v in comps.items()}
        rep_off = {k: rng.gauss(0, 0.002) for k in comps}
        cum = {k: rng.randint(10**9, 10**10) for k in comps}
        node_cum = 5 * 10**10
        steal_cum = 10**8
        rows = []
        tt = S0 - 300.0
        restarted = False
        while tt <= S0 + STEADY + 200:
            ts = tt + OFFSET[node]
            busy = 0.0
            wsum = 0.0
            for k in list(comps):
                c, m = comps[k]
                in_win = S0 <= tt <= S0 + STEADY
                if k[2] == app and not k[3].startswith("pb-") and not in_win:
                    c = 0.02
                r = max(0.0, c + rep_off[k] + rng.gauss(0, 0.01))
                cum[k] += int(r * INTERVAL * 1e6)
                busy += r
                ws = m * analyze.MIB
                wsum += ws
                rows.append([f"{ts:.3f}", node, k[0], k[1], k[2], k[3], k[4], cum[k], 0, int(ws + 4096 * 1000),
                             int(ws * 0.8), 4096 * 1000 + 777, 4096 * 1000, ""])
            # restart: worker-01 db container gets a new id (counter from 0) mid-window
            if restart and node == "worker-01" and not restarted and tt >= S0 + 500:
                old = [k for k in comps if k[3] == "db-1"][0]
                new = (old[0], "f" * 64, old[2], "db-1", "db")
                comps[new] = comps.pop(old)
                rep_off[new] = rep_off.pop(old)
                cum.pop(old)
                cum[new] = 0
                restarted = True
            busy += 0.03
            node_cum += int(busy * INTERVAL * 1e6)
            steal_cum += int(0.004 * INTERVAL * 1e6)
            used = wsum + 500 * analyze.MIB
            rows.append([f"{ts:.3f}", node, "node", "node", "", "", "", node_cum, "", int(used), "", "", "", ""])
            rows.append([f"{ts:.3f}", node, "node", "steal", "", "", "", steal_cum, "", "", "", "", "", ""])
            rows.append([f"{ts:.3f}", node, "slice", "system.slice", "", "", "", node_cum, "", int(used), "", "", "", ""])
            tt += INTERVAL
        gz = node != "cp-01"
        path = os.path.join(d, f"samples-{node}.csv" + (".gz" if gz else ""))
        fh = gzip.open(path, "wt", newline="") if gz else open(path, "w", newline="")
        w = csv.writer(fh)
        w.writerow(["ts", "node", "kind", "id", "ns", "pod", "container", "cpu_usec", "throttled_usec",
                    "mem_current", "mem_anon", "mem_file", "mem_inactive_file", "mem_peak"])
        w.writerows(rows)
        fh.close()
        with open(os.path.join(d, f"samples-{node}.csv.info.json"), "w") as fh:
            json.dump({"node": node, "ncpu": ncpu, "mem_total_bytes": memmib * 1024 * 1024,
                       "own_cpu_pct_of_core": 0.3}, fh)
    if canary:   # constant host speed: the normalised numbers must equal the raw ones
        for node in NODES:
            canary_csv(os.path.join(d, f"canary-{node}.csv"), node, T0 + 140, end + 400, OFFSET[node],
                       lambda _t: CANARY_S0, rng)
    if status == "DONE":
        open(os.path.join(d, "DONE"), "w").write("{}\n")
    elif status == "FAILED":
        open(os.path.join(d, "FAILED"), "w").write("cond.sh otterize exit 1: relay pods=1\n")


# ---- interleaved cycles with host drift (synthC) -------------------------------------------------
CANARY_S0 = 7.5e6                 # canary iterations per CPU-second at host speed 1
CYC_T0 = T0 + 200_000.0           # start of the synthC matrix
CYC_RUN_S = 800.0                 # one run every 800 s, so a cycle of 5 runs takes about 67 min
CYC = {"idle": 60.0, "warm": 60.0, "steady": 300.0, "tp_n": 3000,
       "tp_base": {"keepalive": 40.0, "newconn": 45.0}, "cycles": 10}
CYC_OFFSET = {"cp-01": 0.0, "worker-01": 30.0, "worker-02": -0.4}
CANARY_SCOPE = ("client", "pb-canary.scope", "", "", "")


def host_speed(t):
    """+-35% over a 2.5 h period plus a 15% step between hours 4.2 and 6 of the matrix"""
    x = (t - CYC_T0) / 3600.0
    return 1.0 + 0.35 * math.sin(2 * math.pi * x / 2.5) + (0.15 if 4.2 < x < 6.0 else 0.0)


def williams_orders():
    """the same construction as bin/lib.sh pb_williams (cycles 1-10, block 1)"""
    import hashlib
    first, lo, hi = [0], 1, 4
    while len(first) < 5:
        if len(first) % 2:
            first.append(lo); lo += 1
        else:
            first.append(hi); hi -= 1
    rows = [[(x + i) % 5 for x in first] for i in range(5)]
    rows += [r[::-1] for r in rows]
    seed = int(hashlib.sha256(b"synthC:williams:1").hexdigest()[:8], 16)
    perm = list(range(10))
    random.Random(seed).shuffle(perm)
    return [[MAIN_CONDS[t] for t in rows[perm[k]]] for k in range(10)], seed


def write_cycle_run(root, app, k, cond, pos, t0, seed, rng, status="DONE"):
    d = os.path.join(root, app, f"cycle{k}", cond)
    for sub in ("tp", "ct", "metrics"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    s0 = t0 + 250.0
    end = s0 + CYC["steady"] + 3.0
    phases = {"run_start": t0, "cond_start": t0 + 5, "cond_end": t0 + 50, "samplers_started": t0 + 115,
              "client_started": t0 + 120, "idle_start": t0 + 122, "idle_end": t0 + 122 + CYC["idle"],
              "warmup_start": s0 - CYC["warm"] - 5, "warmup_end": s0 - 5, "steady_start": s0,
              "steady_job_complete": end}
    tests, t, loads = [], end + 8, [(s0, end)]
    for mode in ("keepalive", "newconn"):
        base = CYC["tp_base"][mode] * TRUTH["tp"][mode][cond]
        tot = base / host_speed(t + base / 2)          # the test runs at the host's speed
        tot = base / host_speed(t + tot / 2)
        with open(os.path.join(d, "tp", f"{mode}-1.log"), "w") as fh:
            fh.write(hey_out(tot, CYC["tp_n"]))
        tests.append({"mode": mode, "i": 1, "job": f"pb-tp-{mode}-1", "ok": True, "n": CYC["tp_n"], "c": 16,
                      "created": t - 3, "start": t, "end": t + tot + 1, "log": f"tp/{mode}-1.log",
                      "ct_prefix": f"ct/tp_{mode}_1"})
        loads.append((t, t + tot + 1))
        phases[f"tp_{mode}_1_start"], phases[f"tp_{mode}_1_end"] = t, t + tot + 1
        t += tot + 25
    phases["clients_stopped"] = phases["run_end"] = t + 5
    if cond == "ig_snap":
        phases["snap_start"], phases["snap_end"] = end - 48, end - 33
    meta = {"schema": 1, "status": status, "app": app, "app_ns": app, "cond": cond, "rep": k, "short": False,
            "profile": "cycle", "layout": "cycle", "cycle": k,
            "params": {"idle_s": CYC["idle"], "warmup_s": CYC["warm"], "steady_s": CYC["steady"], "tp_reps": 1,
                       "tp_n": CYC["tp_n"], "tp_c": 16, "tp_pause_s": 20, "snap_lead_s": 45, "sample_s": INTERVAL,
                       "order_seed": str(seed), "order_pos": str(pos), "order_design": "williams", "canary": True,
                       "canary_s": 2.0},
            "phases": phases, "nodes": {"cp": "cp-01", "list": list(NODES), "clock_offset_s": CYC_OFFSET},
            "tp_tests": tests, "kv": {}, "warnings": []}
    with open(os.path.join(d, "meta.json"), "w") as fh:
        json.dump(meta, fh)
    with open(os.path.join(d, "steady.log"), "w") as fh:
        fh.write(locust_csv(TRUTH["rps"], TRUTH["p95_base"] * TRUTH["p95"][cond]))
    for node, (ncpu, memmib) in NODES.items():
        comps = dict(BASE[node])
        comps[CANARY_SCOPE] = (0.01, 12)
        for kk, (c, m) in ADD[cond].get(node, {}).items():
            c0, m0 = comps.get(kk, (0.0, 0.0))
            comps[kk] = (c0 + c, m0 + m)
        comps = {(kk[0], kk[1], kk[2].replace("APP", app), kk[3], kk[4]): v for kk, v in comps.items()}
        cum = {kk: rng.randint(10**9, 10**10) for kk in comps}
        node_cum, rows, tt = 5 * 10**10, [], t0 + 100
        while tt <= phases["run_end"] + 10:
            h = host_speed(tt)
            busy = 0.0
            for kk, (c, m) in comps.items():
                if kk[2] == app and not kk[3].startswith("pb-") and not any(a <= tt <= b for a, b in loads):
                    c = 0.02
                r = max(0.0, (c + rng.gauss(0, 0.002)) / h)       # the same work costs 1/h cores
                cum[kk] += int(r * INTERVAL * 1e6)
                busy += r
                ws = m * analyze.MIB
                rows.append([f"{tt + CYC_OFFSET[node]:.3f}", node, kk[0], kk[1], kk[2], kk[3], kk[4], cum[kk], 0,
                             int(ws + 4096 * 1000), int(ws * 0.8), 4096 * 1000 + 777, 4096 * 1000, ""])
            node_cum += int((busy + 0.03 / h) * INTERVAL * 1e6)
            rows.append([f"{tt + CYC_OFFSET[node]:.3f}", node, "node", "node", "", "", "", node_cum, "", 10**9, "", "", "", ""])
            rows.append([f"{tt + CYC_OFFSET[node]:.3f}", node, "node", "steal", "", "", "", 10**8, "", "", "", "", "", ""])
            tt += INTERVAL
        with gzip.open(os.path.join(d, f"samples-{node}.csv.gz"), "wt", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ts", "node", "kind", "id", "ns", "pod", "container", "cpu_usec", "throttled_usec",
                        "mem_current", "mem_anon", "mem_file", "mem_inactive_file", "mem_peak"])
            w.writerows(rows)
        with open(os.path.join(d, f"samples-{node}.csv.info.json"), "w") as fh:
            json.dump({"node": node, "ncpu": ncpu, "mem_total_bytes": memmib * 1024 * 1024,
                       "own_cpu_pct_of_core": 0.3}, fh)
        canary_csv(os.path.join(d, f"canary-{node}.csv"), node, t0 + 110, phases["run_end"], CYC_OFFSET[node],
                   lambda tq: CANARY_S0 * host_speed(tq), rng)
        with open(os.path.join(d, f"canary-{node}.csv"), "rb") as src, \
                gzip.open(os.path.join(d, f"canary-{node}.csv.gz"), "wb") as dst:
            dst.write(src.read())
        os.remove(os.path.join(d, f"canary-{node}.csv"))
    if status == "DONE":
        open(os.path.join(d, "DONE"), "w").write("{}\n")
    else:
        open(os.path.join(d, "FAILED"), "w").write("cond.sh ig_tcp exit 1: gadget pods=0\n")
    return s0


def build_cycle_tree(root):
    """synthC: 10 cycles in Williams order; cycle 4's ig_tcp run FAILED. -> {(k, cond): steady mean speed}"""
    rng = random.Random(11)
    orders, seed = williams_orders()
    steady_h = {}
    for k in range(1, CYC["cycles"] + 1):
        for pos, cond in enumerate(orders[k - 1], 1):
            t0 = CYC_T0 + ((k - 1) * 5 + pos - 1) * CYC_RUN_S
            failed = (k == 4 and cond == "ig_tcp")
            s0 = write_cycle_run(root, "synthC", k, cond, pos, t0, seed, rng, status="FAILED" if failed else "DONE")
            if not failed:
                steady_h[(k, cond)] = statistics.fmean(host_speed(s0 + 15 + x) for x in range(0, 276, 2))
    return orders, steady_h


def build_tree(root):
    rng = random.Random(7)
    for app, kind in (("synthA", "locust"), ("synthB", "wrk2")):
        for rep in (1, 2, 3):
            for cond in MAIN_CONDS:
                status = "DONE"
                if app == "synthA" and rep == 3 and cond == "otterize":
                    status = "FAILED"
                if app == "synthB" and rep == 2 and cond == "ig_snap":
                    status = "INCOMPLETE"
                write_run(root, app, kind, rep, cond, rng, status=status,
                          restart=(app == "synthA" and rep == 2 and cond == "hubble"), canary=(app == "synthB"))
    write_run(root, "synthA", "locust", 4, "baseline", rng, short=True)
    return build_cycle_tree(root)


def read_csv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def check_parsers():
    errs = []
    s = analyze.parse_steady(locust_csv(20.0, 105.0))
    if not s or abs(s["p95_ms"] - 105.0) > 1e-6 or s["kind"] != "locust":
        errs.append(f"locust csv parse: {s}")
    spec = ("       1.000     0.000000            1         1.00\n      40.000     0.500000         2000         2.00\n"
            "      66.500     0.950000         5700        20.00\n      90.000     0.990000         5900       100.00\n")
    s = analyze.parse_wrk2(wrk2_out(19.98, 77.0).replace(" 95.000%", " 96.000%")
                           .replace("       4.743     0.989062         5713        91.43\n", spec))
    if not s or abs(s["p95_ms"] - 66.5) > 1e-6 or abs(s["p50_ms"] - 40.0) > 1e-6:
        errs.append(f"wrk2 p95 from spectrum: {s}")
    s = analyze.parse_steady(wrk2_out(19.98, 77.0))
    if not s or abs(s["p95_ms"] - 77.0) > 1e-6 or abs(s["p99_ms"] - 77.0 * 1.6) > 1e-3:
        errs.append(f"wrk2 parse: {s}")
    real_wrk2 = os.path.join(HERE, "..", "..", "results", "DSB-SOCIAL-20260904", "captureA", "wrk2_output.txt")
    if os.path.exists(real_wrk2):
        s = analyze.parse_wrk2(open(real_wrk2).read())
        if not s or not s["rps"] or s["segments"] < 1:
            errs.append(f"real thesis wrk2 output not parsed: {s}")
    real_locust = os.path.join(HERE, "..", "..", "results", "BANK-20260904", "captureA", "locust_output.txt")
    if os.path.exists(real_locust):
        s = analyze.parse_locust_table(open(real_locust).read())
        if not s or s["requests"] != 2119 or abs(s["rps"] - 1.9) > 1e-9:
            errs.append(f"real thesis locust table not parsed: {s}")
    hist = ("Timestamp,User Count,Type,Name,Requests/s,Failures/s,50%,66%,75%,80%,90%,95%,98%,99%,99.9%,99.99%,100%,"
            "Total Request Count,Total Failure Count,Total Median Response Time,Total Average Response Time,"
            "Total Min Response Time,Total Max Response Time,Total Average Content Size\n"
            + "".join(f"{1000 + t},8,,Aggregated,20,0,1,1,1,1,1,1,1,1,1,1,1,{20 * t},{t},1,1,1,1,1\n" for t in range(100))
            + "=== PB_FILE other ===\n")
    rate, fail = analyze.window_rate(analyze.parse_locust_history(hist), 1010, 1090)
    if rate is None or abs(rate - 20.0) > 1e-9 or abs(fail - 5.0) > 1e-9:
        errs.append(f"locust history window rate: {rate} {fail}")
    h = analyze.parse_fixed_count(hey_out(4.2, 10000))
    if not h or abs(h["total_s"] - 4.2) > 1e-9 or h["n_2xx"] != 10000 or abs(h["p99_ms"] - 40.0) > 1e-9:
        errs.append(f"hey parse: {h}")
    ab = ("Complete requests:      2000\nFailed requests:        3\nNon-2xx responses:      5\n"
          "Time taken for tests:   2.345 seconds\nRequests per second:    852.88 [#/sec] (mean)\n"
          "Percentage of the requests served within a certain time (ms)\n  50%     10\n  95%     30\n  99%     45\n")
    a = analyze.parse_fixed_count(ab)
    if not a or a["n_2xx"] != 1992 or a["p95_ms"] != 30.0 or a["total_s"] != 2.345:
        errs.append(f"ab parse: {a}")
    return errs


def check_welch():
    errs = []
    rng = random.Random(3)
    saved = analyze._scipy_stats
    try:
        for _ in range(200):
            a = [rng.gauss(10, rng.uniform(0.1, 3)) for _ in range(rng.choice([2, 3, 5]))]
            b = [rng.gauss(10 + rng.uniform(-3, 3), rng.uniform(0.1, 3)) for _ in range(rng.choice([2, 3, 4]))]
            analyze._scipy_stats = None
            p_builtin = analyze.welch_p(a, b)
            if saved is not None:
                p_scipy = float(saved.ttest_ind(a, b, equal_var=False).pvalue)
                if abs(p_builtin - p_scipy) > 1e-6:
                    errs.append(f"welch mismatch {p_builtin} vs scipy {p_scipy}")
                    break
            elif not (0.0 <= p_builtin <= 1.0):
                errs.append(f"welch out of range {p_builtin}")
    finally:
        analyze._scipy_stats = saved
    return errs, saved is not None


def check_canary_and_cycles(out, orders, steady_h, near):
    errs = []
    nerr0 = len(errs)

    def near_e(label, got, want, tol):
        if got in ("", None) or abs(float(got) - want) > tol:
            errs.append(f"{label}: got {got}, want {want} +- {tol}")
    # ---- the rep report must not contain cycle runs, and synthA (no canary) no canary section
    runs = read_csv(os.path.join(out, "runs.csv"))
    if any(r["app"] == "synthC" for r in runs):
        errs.append("cycle runs leaked into the rep-layout runs.csv")
    ta, tb = (open(os.path.join(out, f"tables-{a}.md")).read() for a in ("synthA", "synthB"))
    if "canary" in ta.lower():
        errs.append("tables-synthA.md (no canary data) mentions the canary")
    for needle in ("Host speed (canary)", "Host-speed canary per segment", "canary-normalised (Table 5 format)"):
        if needle not in tb:
            errs.append(f"tables-synthB.md lacks '{needle}'")
    # synthB: constant canary speed -> normalised == raw
    pdB = {(r["endpoint"], r["cond"]): r for r in read_csv(os.path.join(out, "paired_deltas.csv")) if r["app"] == "synthB"}
    for c in MAIN_CONDS[1:]:
        r = pdB.get(("cpu.cluster.node", c))
        if not r or abs(float(r["norm_delta"]) - float(r["raw_delta"])) > 0.003:
            errs.append(f"synthB {c}: constant host speed but normalised Δ != raw Δ: {r and (r['raw_delta'], r['norm_delta'])}")
        r = pdB.get(("tp.newconn.time_s", c))
        if not r or abs(float(r["norm_pct"]) - float(r["raw_pct"])) > 0.1:
            errs.append(f"synthB {c}: newconn normalised % != raw %: {r and (r['raw_pct'], r['norm_pct'])}")
    # ---- cycle report
    cdir = os.path.join(out, "cycles")
    for fn in ("RESULTS-CYCLES.md", "tables-synthC.md", "paired_deltas.csv", "drift_per_block.csv", "drift_summary.csv",
               "canary_segments.csv", "table5_fixed_count_normalised.csv", "table5_fixed_count.csv", "runs.csv"):
        if not os.path.exists(os.path.join(cdir, fn)):
            errs.append(f"cycles/{fn} missing")
    if errs[nerr0:]:
        return errs
    h_med = statistics.median(steady_h.values())
    pd = {(r["endpoint"], r["cond"]): r for r in read_csv(os.path.join(cdir, "paired_deltas.csv"))}
    for c in MAIN_CONDS[1:]:
        npair = 9 if c == "ig_tcp" else 10
        if pd[("cpu.cluster.observer", c)]["n_pairs"] != str(npair):
            errs.append(f"synthC {c}: {pd[('cpu.cluster.observer', c)]['n_pairs']} pairs, want {npair}")
        # normalised: the overhead at the median host speed; raw: biased and noisy by the drift
        near_e(f"synthC {c} normalised Δ observer x median speed", float(pd[("cpu.cluster.observer", c)]["norm_delta"]) * h_med,
               TRUTH["obs_cpu"][c], 0.006)
        near_e(f"synthC {c} normalised Δ cluster x median speed", float(pd[("cpu.cluster.node", c)]["norm_delta"]) * h_med,
               TRUTH["obs_cpu"][c], 0.012)
        for mode in ("keepalive", "newconn"):
            r = pd[(f"tp.{mode}.time_s", c)]
            near_e(f"synthC {c} {mode} normalised overhead %", r["norm_pct"], 100 * (TRUTH["tp"][mode][c] - 1), 0.3)
            if c != "ig_snap":
                wr, wn = float(r["raw_pct_hi"]) - float(r["raw_pct_lo"]), float(r["norm_pct_hi"]) - float(r["norm_pct_lo"])
                if not wr > 3 * wn:
                    errs.append(f"synthC {c} {mode}: raw CI width {wr:.2f} not > 3 x normalised {wn:.2f} under drift")
    # Holm across the 4 techniques, per endpoint and variant
    for ep in ("cpu.cluster.node", "tp.newconn.time_s"):
        for v in ("raw", "norm"):
            ps = [float(pd[(ep, c)][f"{v}_p"]) for c in MAIN_CONDS[1:]]
            want = analyze.holm(ps)
            got = [float(pd[(ep, c)][f"{v}_holm_p"]) for c in MAIN_CONDS[1:]]
            if any(abs(a - b) > 1e-9 for a, b in zip(want, got)):
                errs.append(f"synthC Holm {ep} {v}: {got} != {want}")
    # drift diagnostic: the raw baseline time follows 1/speed, the normalised one is flat
    ds = {(r["mode"]): r for r in read_csv(os.path.join(cdir, "drift_summary.csv")) if r["app"] == "synthC"}
    for mode in ("keep-alive", "new conn"):
        r = ds.get(mode)
        if not r or float(r["cv_raw_pct"]) < 10 or float(r["cv_norm_pct"]) > 1.0 or float(r["r_time_vs_inv_speed"]) < 0.99:
            errs.append(f"synthC drift summary {mode}: {r}")
    db = read_csv(os.path.join(cdir, "drift_per_block.csv"))
    got_orders = [r["order"].split() for r in sorted(db, key=lambda r: int(r["block"]))]
    want_orders = [[c for c in o if not (k == 4 and c == "ig_tcp")] for k, o in enumerate(orders, 1)]
    if got_orders != want_orders:
        errs.append(f"synthC drift table orders {got_orders} != Williams orders {want_orders}")
    for r in db:   # the baseline's steady speed ratio = its steady mean speed / the median
        k = int(r["block"])
        near_e(f"synthC cycle {k} baseline canary ratio", r["base_canary_ratio_workers"],
               steady_h[(k, "baseline")] / h_med, 0.01)
    # canary segments: speed = S0 x host speed (clock offsets applied; worker-01 is 30 s ahead)
    seg = read_csv(os.path.join(cdir, "canary_segments.csv"))
    st = [r for r in seg if r["segment"] == "steady" and r["node"] == "worker-01"]
    if len(st) != 49:
        errs.append(f"synthC: {len(st)} steady canary segments on worker-01, want 49")
    for r in st:
        want = CANARY_S0 * steady_h[(int(r["block"]), r["cond"])]
        near_e(f"synthC canary speed cycle{r['block']}/{r['cond']}", float(r["speed_cpu"]) / want, 1.0, 0.004)
    if not any(r["segment"] == "tp_newconn_1" for r in seg) or not any(r["segment"] == "idle" for r in seg):
        errs.append("synthC: canary_segments.csv lacks the idle or fixed-count segments")
    # the pb-canary scope is harness, never observer or client
    cr = {(r["rep"], r["cond"]): r for r in read_csv(os.path.join(cdir, "runs.csv"))}
    b1 = cr[("1", "baseline")]
    if float(b1.get("cpu.cluster.clients") or 0) > 1e-6 or float(b1.get("comp_cpu.client-other") or 0) > 1e-6:
        errs.append(f"synthC: pb-canary counted as a client ({b1.get('cpu.cluster.clients')})")
    if not float(b1.get("cpu.cluster.harness") or 0) > 0.02:
        errs.append(f"synthC: pb-canary not in harness ({b1.get('cpu.cluster.harness')})")
    md = open(os.path.join(cdir, "RESULTS-CYCLES.md")).read()
    for needle in ("Interleaved cycles: paired deltas", "Drift diagnostic (per cycle)", "GoLeash Table 5",
                   "Williams design", "cond.sh ig_tcp exit 1"):
        if needle not in md:
            errs.append(f"RESULTS-CYCLES.md lacks '{needle}'")
    return errs


def check_williams_shell():
    """bin/lib.sh pb_williams: 10 sequences per block, positions and carry-over balanced"""
    bash = shutil.which("bash")
    lib = os.path.join(HERE, "..", "bin", "lib.sh")
    if not bash:
        return []
    v = subprocess.run([bash, "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True, text=True).stdout.strip()
    if not v.isdigit() or int(v) < 4:
        print("pb_williams check skipped (bash >= 4 not on PATH)")
        return []
    script = f". '{lib}'; for k in $(seq 1 20); do pb_williams synthC $k baseline hubble otterize ig_tcp ig_snap; done"
    out = subprocess.run([bash, "-c", script], capture_output=True, text=True)
    lines = [ln.split() for ln in out.stdout.splitlines() if ln.strip()]
    errs = []
    if len(lines) != 20 or any(ln[1] != "williams" for ln in lines):
        return [f"pb_williams output: {out.stdout[:300]} {out.stderr[:300]}"]
    if [ln[3:] for ln in lines[:10]] != williams_orders()[0]:
        errs.append("pb_williams (lib.sh) and the selftest copy disagree on cycles 1-10")
    for b in (0, 1):
        orders = [ln[3:] for ln in lines[10 * b:10 * b + 10]]
        pos = {(c, i): 0 for c in MAIN_CONDS for i in range(5)}
        pairs = {}
        for o in orders:
            for i, c in enumerate(o):
                pos[(c, i)] += 1
            for a, c in zip(o, o[1:]):
                pairs[(a, c)] = pairs.get((a, c), 0) + 1
        if set(pos.values()) != {2} or len(pairs) != 20 or set(pairs.values()) != {2}:
            errs.append(f"pb_williams block {b + 1} not balanced: positions {set(pos.values())}, pairs {pairs}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", default=None, help="build the tree here and keep it")
    a = ap.parse_args()
    root = a.keep or tempfile.mkdtemp(prefix="pb-selftest-")
    if a.keep and os.path.exists(root):
        shutil.rmtree(root)
    os.makedirs(root, exist_ok=True)
    errs = check_parsers()
    werrs, had_scipy = check_welch()
    errs += werrs
    orders, steady_h = build_tree(root)
    res = subprocess.run([sys.executable, os.path.join(HERE, "analyze.py"), root], capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout, res.stderr)
        return 1
    out = os.path.join(root, "analysis")
    cpu = {(r["app"], r["cond"]): r for r in read_csv(os.path.join(out, "overhead_cpu.csv"))}
    mem = {(r["app"], r["cond"]): r for r in read_csv(os.path.join(out, "overhead_memory.csv"))}
    proj = {(r["app"], r["cond"]): r for r in read_csv(os.path.join(out, "projection_shiv_thesis.csv"))}
    t5 = {(r["app"], r["mode"], r["cond"]): r for r in read_csv(os.path.join(out, "table5_fixed_count.csv"))}
    lat = {(r["app"], r["cond"]): r for r in read_csv(os.path.join(out, "latency_throughput.csv"))}
    norm = {(r["app"], r["cond"]): r for r in read_csv(os.path.join(out, "normalised_cost.csv"))}
    idle = {(r["app"], r["cond"]): r for r in read_csv(os.path.join(out, "idle_standing_cost.csv"))}
    runs = read_csv(os.path.join(out, "runs.csv"))
    excl = read_csv(os.path.join(out, "excluded_runs.csv"))

    def near(label, got, want, tol):
        if got in ("", None) or abs(float(got) - want) > tol:
            errs.append(f"{label}: got {got}, want {want} +- {tol}")

    for app in ("synthA", "synthB"):
        for c in MAIN_CONDS[1:]:
            near(f"{app}/{c} Δ observer cores", cpu[(app, c)]["obs_delta"], TRUTH["obs_cpu"][c], 0.012)
            near(f"{app}/{c} Δ cluster cores", cpu[(app, c)]["cluster_delta"], TRUTH["obs_cpu"][c], 0.03)
            near(f"{app}/{c} Δ observer MiB", mem[(app, c)]["obs_delta_mib"], TRUTH["obs_mem"][c], 1.0)
            near(f"{app}/{c} Δ projected cores", proj[(app, c)]["delta_cores"], TRUTH["proj_cpu"][c], 0.03)
            near(f"{app}/{c} projected % of 18 vCPU", proj[(app, c)]["delta_pct_of_18vcpu"],
                 100 * TRUTH["proj_cpu"][c] / 18, 0.2)
            for mode in ("keepalive", "newconn"):
                near(f"{app}/{mode}/{c} Table5 overhead %", t5[(app, mode, c)]["overhead_pct"],
                     100 * (TRUTH["tp"][mode][c] - 1), 0.6)
                near(f"{app}/{mode}/{c} Table5 w/o", t5[(app, mode, c)]["wo_s"], TRUTH["tp_base"][mode], 0.02)
            near(f"{app}/{c} p95 Δ%", lat[(app, c)]["p95_ms_delta_pct"], 100 * (TRUTH["p95"][c] - 1), 0.8)
            near(f"{app}/{c} flows/s", norm[(app, c)]["flows_per_s"], 2 * TRUTH["flows_per_worker"], 1.0)
        near(f"{app} hubble events/s (client, window)", norm[(app, "hubble")]["events_per_s"], 30.0, 0.01)
        near(f"{app} IG events/s (client, window)", norm[(app, "ig_tcp")]["events_per_s"], 5.0, 0.01)
        near(f"{app} hubble flows processed/s (metric)", norm[(app, "hubble")]["hubble_flows_processed_per_s"], 900.0, 1.0)
        near(f"{app} background flows/s", norm[(app, "hubble")]["bg_flows_per_s"], 2 * BG_PER_WORKER, 0.05)
        near(f"{app} app flows/s", norm[(app, "hubble")]["app_flows_per_s"],
             2 * TRUTH["flows_per_worker"] - 2 * BG_PER_WORKER * (STEADY + 3 + 9) / (STEADY + 3), 0.1)
        for c in MAIN_CONDS[1:]:   # observers are constant in time here, so idle Δ = steady Δ
            # (12 noisy 5-s ticks in the idle segment, so a wider tolerance than the steady window's)
            near(f"{app}/{c} idle Δ observer", idle[(app, c)]["obs_delta"], TRUTH["obs_cpu"][c], 0.03)
            near(f"{app}/{c} projection upper = main", proj[(app, c)]["delta_cores_upper"],
                 float(proj[(app, c)]["delta_cores"]), 0.03)
    bad = [r for r in read_csv(os.path.join(out, "fixed_count_tests.csv"))
           if r["app"] == "synthA" and r["rep"] == "1" and r["cond"] == "ig_snap" and r["mode"] == "newconn" and r["i"] == "3"]
    if not bad or bad[0]["valid"] != "False" or "302" not in bad[0]["why"]:
        errs.append(f"fixed-count test with 302s should be invalid: {bad}")
    # per-test conntrack inserts: newconn adds 3 x TP_N per worker pair, keepalive 200
    tpt = read_csv(os.path.join(out, "fixed_count_tests.csv"))
    nc = [float(r["ct_inserts_workers"]) for r in tpt if r["mode"] == "newconn" and r["ct_inserts_workers"]]
    ka = [float(r["ct_inserts_workers"]) for r in tpt if r["mode"] == "keepalive" and r["ct_inserts_workers"]]
    if not nc or not ka or min(nc) != 2 * 3 * TP_N or max(ka) != 2 * 200:
        errs.append(f"per-test conntrack inserts wrong: newconn {set(nc)} keepalive {set(ka)}")
    # the otterize cell of synthA has 2 runs (rep3 FAILED)
    if t5[("synthA", "keepalive", "otterize")]["with_n"] != "2":
        errs.append("synthA otterize should have n=2")
    want_excl = {("synthA", "3", "otterize", "FAILED"), ("synthB", "2", "ig_snap", "INCOMPLETE"),
                 ("synthA", "4", "baseline", "DONE")}
    got_excl = {(r["app"], r["rep"], r["cond"], r["status"]) for r in excl}
    if got_excl != want_excl:
        errs.append(f"excluded runs {got_excl} != {want_excl}")
    # the restart must not create a spike: app CPU in the restarted run ~ the other hubble runs
    app_cpu = {(r["app"], r["rep"], r["cond"]): float(r["cpu.cluster.app"]) for r in runs if r.get("cpu.cluster.app")}
    near("app CPU in run with mid-window restart", app_cpu[("synthA", "2", "hubble")],
         app_cpu[("synthA", "1", "hubble")], 0.03)
    # clock offset: worker-01 app pods load only inside the window; without the +60 s correction
    # the mean would drop by ~5%
    w01 = [float(r["cpu.workers.app"]) for r in runs if r["app"] == "synthB" and r.get("cpu.workers.app")]
    near("workers app CPU (clock offset handled)", sum(w01) / len(w01), 1.2, 0.02)
    md = open(os.path.join(out, "RESULTS-PERF.md")).read()
    for needle in ("## synthA", "## synthB", "GoLeash Table 5", "## Excluded runs", "cond.sh otterize exit 1",
                   "test-cluster projection"):
        if needle not in md:
            errs.append(f"RESULTS-PERF.md lacks '{needle}'")
    errs += check_canary_and_cycles(out, orders, steady_h, near)
    errs += check_williams_shell()
    print(res.stderr.strip())
    print(f"Welch check against scipy: {'yes' if had_scipy else 'no (scipy not importable)'}")
    if errs:
        print("FAILED checks:")
        for e in errs:
            print("  -", e)
        return 1
    print(f"selftest OK ({root})")
    if not a.keep:
        shutil.rmtree(root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
