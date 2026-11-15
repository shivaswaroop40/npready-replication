#!/usr/bin/env python3
"""The counter-test: run the fusion measurement on Sock Shop.

The platform application declares its dependencies in configuration; Sock Shop
hard-codes them in application source. If the fusion result is real rather than
an artifact of one codebase's style, the two applications should sit at opposite
ends of the same axis. This measures that.

Config edges come from npready's derivation run against the *live* Sock Shop
namespace (the same deployment the observers watched), so neither side of the
comparison has an information advantage.

Usage: python3 fusion_sockshop.py <live-sockshop.yaml> <run-dir> [<run-dir> ...]
"""
from __future__ import annotations
import json, os, sys
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "evaluate"))
sys.path.insert(0, "/Users/shiv/Desktop/code/netpol-readiness/src")

from score_clean30 import (hubble_edges, otterize_edges, ig_tcp_edges,
                           ig_snap_edges, sock_role)
from final_benchmark import L_sock, A_sock
from npready import Inventory, derive_needed

TOOLS = ["our_synth_hubble", "otterize_20day", "otterize_fresh30",
         "ig_trace_tcp", "ig_snapshot_socket"]
# peers that are not Sock Shop workloads; the ground truth is intra-app only
NON_APP = {"kube-dns", "kube-apiserver", "world", "node", "remote-node"}


def declared_edges(manifest):
    """npready's config derivation, mapped into the ground-truth vocabulary."""
    inv = Inventory.from_manifests(manifest)
    out, dropped = set(), []
    for e in derive_needed(inv):
        s = sock_role(str(e.src).split("/")[-1])
        d_raw = str(e.dst).split("/")[-1]
        if d_raw in NON_APP:
            dropped.append(f"{s}->{d_raw}")
            continue
        d = sock_role(d_raw)
        if s and d and s != d:
            out.add((s, d))
    return out, sorted(set(dropped))


def sc(admit, L, A):
    admit = set(admit)
    fd = len([e for e in L if e not in admit]) / len(L)
    return {"false_deny": round(fd, 3), "coverage": round(1 - fd, 3),
            "over_privilege": round(len([e for e in A if e in admit]) / len(A), 3),
            "admit_edges": len(admit)}


def main(manifest, runs):
    L, A = set(L_sock), set(A_sock)
    D, dropped = declared_edges(manifest)

    out = {
        "app": "sock-shop",
        "L": len(L), "A": len(A),
        "declared": {
            "edges": sorted("->".join(e) for e in D),
            "count": len(D),
            "covered_of_L": len(D & L),
            "coverage_of_L": round(len(D & L) / len(L), 3),
            "declared_that_are_attacks": sorted("->".join(e) for e in D & A),
            "dropped_non_app_peers": dropped,
        },
        "per_run": {}, "aggregate": {},
    }

    acc = {t: {"obs": [], "fused": []} for t in TOOLS}
    union_obs_legit = set()

    for run in runs:
        rn = os.path.basename(run)
        obs = {
            "our_synth_hubble":   hubble_edges(run, "sock-shop"),
            "otterize_20day":     otterize_edges(os.path.join(run, "otterize_20day.json"), "sock-shop"),
            "otterize_fresh30":   otterize_edges(os.path.join(run, "otterize_fresh30.json"), "sock-shop"),
            "ig_trace_tcp":       ig_tcp_edges(run, "sock-shop"),
            "ig_snapshot_socket": ig_snap_edges(run, "sock-shop"),
        }
        block = {}
        for t in TOOLS:
            O = obs.get(t)
            if O is None:
                block[t] = None
                continue
            union_obs_legit |= (O & L)
            o_s, f_s = sc(O, L, A), sc(O | D, L, A)
            block[t] = {"observed": o_s, "fused": f_s,
                        "coverage_gain": round(f_s["coverage"] - o_s["coverage"], 3)}
            acc[t]["obs"].append(o_s["false_deny"])
            acc[t]["fused"].append(f_s["false_deny"])
        out["per_run"][rn] = block

    for t in TOOLS:
        if not acc[t]["obs"]:
            out["aggregate"][t] = None
            continue
        o, f = acc[t]["obs"], acc[t]["fused"]
        out["aggregate"][t] = {
            "observed_false_deny_mean": round(mean(o), 3),
            "observed_spread": round(max(o) - min(o), 3),
            "fused_false_deny_mean": round(mean(f), 3),
            "fused_coverage_mean": round(1 - mean(f), 3),
        }

    # the direction-of-dominance test, mirroring the platform analysis
    out["dominance"] = {
        "legit_edges_observation_found": len(union_obs_legit),
        "of": len(L),
        "observation_edges_config_missed":
            sorted("->".join(e) for e in union_obs_legit - D),
        "count_observation_adds_beyond_config": len(union_obs_legit - D),
        "config_edges_observation_missed":
            sorted("->".join(e) for e in (D & L) - union_obs_legit),
    }

    print(json.dumps(out, indent=2))
    dest = os.path.join(HERE, "fusion_sockshop.json")
    json.dump(out, open(dest, "w"), indent=2)
    sys.stderr.write(f"\nwrote {dest}\n")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
