#!/usr/bin/env python3
"""The port-aware three-way comparison, run offline from the retained captures.

The cross-tool comparison in the thesis drops to identity pairs because the two
Otterize configurations are port-blind. That coarsening collapses the legitimate
egress agent->world:443 onto the SSRF attack agent->world:80, and the flow
synthesiser is then scored as admitting an attack it does not admit -- the 0.091
over-privilege in the security table.

Three of the five tools do carry ports: the flow synthesiser, IG trace_tcp and IG
snapshot_socket. Scoring just those three at full (src, dst, port) granularity
settles whether that 0.091 is entirely an artefact of the comparison. No cluster
is needed; the ports are in the captures already.

Usage: python3 portaware_threeway.py <run-dir> [<run-dir> ...]
"""
from __future__ import annotations
import glob, json, os, sys
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "evaluate"))

import over_privilege as OP
from score_clean30 import ankra_role

L = set(OP.L)          # (src, dst, port)
A = set(OP.A)
EPH = 32768


def synth_edges(run):
    cap = os.path.join(run, "ankra_enriched.jsonl")
    if not os.path.exists(cap):
        return None
    OP.CAP = cap
    return set(OP.load_observed())


def _ipmap(run):
    f = os.path.join(run, "ipmap.json")
    return json.load(open(f)) if os.path.exists(f) else None


def tcp_edges(run):
    ipmap = _ipmap(run)
    files = glob.glob(os.path.join(run, "ig_tcp_worker_ankra.json"))
    if ipmap is None or not files:
        return None
    e = set()
    for f in files:
        for line in open(f):
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") != "connect":
                continue
            k8s = o.get("k8s", {}) or {}
            if k8s.get("namespace") != "ankra":
                continue
            s = ankra_role(k8s.get("podName", ""))
            dst = o.get("dst", {}) or {}
            tgt = ipmap.get(dst.get("addr", ""))
            port = dst.get("port")
            if not tgt or not port:
                continue
            d = ankra_role(tgt["name"])
            if s and d and s != d:
                e.add((s, d, int(port)))
    return e


def snap_edges(run):
    ipmap = _ipmap(run)
    files = glob.glob(os.path.join(run, "ig_snap_worker_ankra.json"))
    if ipmap is None or not files:
        return None
    e = set()
    for f in files:
        try:
            arr = json.load(open(f))
        except Exception:
            continue
        if isinstance(arr, dict):
            arr = [arr]
        for r in arr:
            dst = r.get("dst", {}) or {}
            if dst.get("proto") != "TCP" or r.get("state") != 1:
                continue
            k8s = r.get("k8s", {}) or {}
            if k8s.get("namespace") != "ankra":
                continue
            pod = ankra_role(k8s.get("podName", ""))
            tgt = ipmap.get(dst.get("addr", ""))
            port = dst.get("port") or 0
            if not tgt or not pod:
                continue
            other = ankra_role(tgt["name"])
            if not other or pod == other:
                continue
            # low dst port => this pod is the client; high => it is the server
            if port and port < EPH:
                e.add((pod, other, int(port)))
    return e


TOOLS = {"our_synth_hubble": synth_edges,
         "ig_trace_tcp": tcp_edges,
         "ig_snapshot_socket": snap_edges}


def score(admit):
    admit = set(admit)
    return {
        "admit_edges": len(admit),
        "over_privilege": round(len([e for e in A if e in admit]) / len(A), 3),
        "block_rate": round(len([e for e in A if e not in admit]) / len(A), 3),
        "false_deny": round(len([e for e in L if e not in admit]) / len(L), 3),
        "admitted_attacks": sorted(f"{s}->{d}:{p}" for s, d, p in A if (s, d, p) in admit),
    }


def main(runs):
    out = {"granularity": "(src,dst,port)", "L": len(L), "A": len(A),
           "runs": [os.path.basename(r) for r in runs], "per_run": {}, "aggregate": {}}
    acc = {t: {"op": [], "fd": []} for t in TOOLS}

    for run in runs:
        rn = os.path.basename(run)
        out["per_run"][rn] = {}
        for t, fn in TOOLS.items():
            edges = fn(run)
            if edges is None:
                out["per_run"][rn][t] = None
                continue
            s = score(edges)
            out["per_run"][rn][t] = s
            acc[t]["op"].append(s["over_privilege"])
            acc[t]["fd"].append(s["false_deny"])

    for t in TOOLS:
        if not acc[t]["op"]:
            out["aggregate"][t] = None
            continue
        op, fd = acc[t]["op"], acc[t]["fd"]
        out["aggregate"][t] = {
            "over_privilege_mean": round(mean(op), 3),
            "over_privilege_values": op,
            "false_deny_mean": round(mean(fd), 3),
            "false_deny_values": fd,
        }

    # the question this script exists to answer
    syn = out["aggregate"].get("our_synth_hubble")
    out["verdict"] = {
        "synth_over_privilege_port_aware": syn["over_privilege_mean"] if syn else None,
        "synth_over_privilege_pair_granularity": 0.091,
        "note": ("If the port-aware figure is 0.000, the 0.091 reported in the "
                 "five-tool table is entirely an artefact of dropping the port for "
                 "cross-tool comparison, and the flow synthesiser blocks every attack."),
    }

    print(json.dumps(out, indent=2))
    dest = os.path.join(HERE, "portaware_threeway.json")
    json.dump(out, open(dest, "w"), indent=2)
    sys.stderr.write(f"\nwrote {dest}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
