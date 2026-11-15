#!/usr/bin/env python3
"""Ground-truth sensitivity analysis + the fusion measurement, recomputed from
retained artifacts across all three reproduction runs.

Two things were missing from the thesis and both are recoverable offline:

  1. SENSITIVITY. Every Chapter 6 number is scored against a hand-authored L
     (39 edges, evaluate/over_privilege.py). A second, mechanically derived L
     exists (derive-L/L_derived.py, 55 edges) and disagrees at Jaccard ~0.49.
     If the qualitative findings survive both reference sets, the result is
     robust to how ground truth was built. If they do not, that is a limitation
     that has to be stated. Nobody had checked.

  2. FUSION. The claimed 82-89 % combined coverage had no retained output. It
     is recomputable: fusion admits (observed edges) UNION (config-derived
     edges), and is scored against the same L as everything else.

     Circularity note, load-bearing: the declared set D *is* L_derived. Scoring
     fusion against L_derived would therefore be scoring a set against itself
     and would trivially return 100 %. That number is reported below only to
     make the circularity visible; the defensible fusion figure is the one
     against the hand-authored L, which was written independently of the
     derivation (the Jaccard 0.49 disagreement is the evidence of that
     independence).

Usage:  python3 sensitivity_and_fusion.py <run-dir> [<run-dir> ...]
"""
from __future__ import annotations
import json, os, sys
from statistics import mean

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "evaluate"))
sys.path.insert(0, os.path.join(ROOT, "derive-L"))

from score_clean30 import (hubble_edges, otterize_edges, ig_tcp_edges,
                           ig_snap_edges)
import over_privilege as OP
from L_derived import L_DERIVED

# ---------------------------------------------------------------- edge sets
def pairs(triples):
    return {(s, d) for (s, d, _p) in triples}

L_HAND_T = set(OP.L)                 # hand-authored, port granularity
L_DERV_T = set(L_DERIVED)            # mechanically derived, port granularity
A_T      = set(OP.A)

L_HAND = pairs(L_HAND_T)
L_DERV = pairs(L_DERV_T)
A      = pairs(A_T)
D      = pairs(L_DERV_T)             # the declared set the fusion adds

GROUND_TRUTHS = {"L_hand": L_HAND, "L_derived": L_DERV}

TOOLS = ["our_synth_hubble", "otterize_20day", "otterize_fresh30",
         "ig_trace_tcp", "ig_snapshot_socket"]


def observed_sets(run):
    return {
        "our_synth_hubble":   hubble_edges(run, "ankra"),
        "otterize_20day":     otterize_edges(os.path.join(run, "otterize_20day.json"), "ankra"),
        "otterize_fresh30":   otterize_edges(os.path.join(run, "otterize_fresh30.json"), "ankra"),
        "ig_trace_tcp":       ig_tcp_edges(run, "ankra"),
        "ig_snapshot_socket": ig_snap_edges(run, "ankra"),
    }


def sc(admit, L):
    """false-deny, coverage and over-privilege of an admitted edge set."""
    admit = set(admit)
    fd = len([e for e in L if e not in admit]) / len(L)
    op = len([e for e in A if e in admit]) / len(A)
    return {"false_deny": round(fd, 3),
            "coverage": round(1 - fd, 3),
            "over_privilege": round(op, 3),
            "admit_edges": len(admit)}


def main(runs):
    out = {
        "runs": [os.path.basename(r) for r in runs],
        "ground_truth_comparison": {},
        "per_run": {},
        "aggregate": {},
    }

    # ---- how far apart are the two ground truths, at both granularities ----
    for name, (a, b) in {"port_granularity": (L_HAND_T, L_DERV_T),
                         "pair_granularity": (L_HAND, L_DERV)}.items():
        inter, union = len(a & b), len(a | b)
        out["ground_truth_comparison"][name] = {
            "L_hand": len(a), "L_derived": len(b),
            "intersection": inter, "union": union,
            "jaccard": round(inter / union, 3),
            "in_hand_not_derived": sorted("->".join(map(str, e)) for e in a - b),
            "in_derived_not_hand": sorted("->".join(map(str, e)) for e in b - a),
        }

    # D is the fusion's declared input; its reach over the *independent* L
    out["ground_truth_comparison"]["declared_reach_over_L_hand"] = {
        "covered": len(L_HAND & D), "of": len(L_HAND),
        "fraction": round(len(L_HAND & D) / len(L_HAND), 3),
        "note": "ceiling of config-only coverage against the independent hand-authored L",
    }
    out["ground_truth_comparison"]["declared_vs_attacks"] = {
        "declared_edges_that_are_attacks": sorted("->".join(e) for e in (D & A)),
        "count": len(D & A),
        "note": "must be 0 for the 'fusion cannot cost security' argument to hold",
    }

    # ------------------------------------------------ per-run, per-tool ----
    acc = {gt: {t: {"obs": [], "fused": []} for t in TOOLS} for gt in GROUND_TRUTHS}
    acc_cfg = {gt: [] for gt in GROUND_TRUTHS}

    for run in runs:
        rn = os.path.basename(run)
        obs = observed_sets(run)
        out["per_run"][rn] = {}
        for gt, L in GROUND_TRUTHS.items():
            block = {"config_only": sc(D, L)}
            acc_cfg[gt].append(block["config_only"]["false_deny"])
            for t in TOOLS:
                O = obs.get(t)
                if O is None:
                    block[t] = None
                    continue
                o_s = sc(O, L)
                f_s = sc(O | D, L)
                block[t] = {
                    "observed": o_s,
                    "fused": f_s,
                    "coverage_gain": round(f_s["coverage"] - o_s["coverage"], 3),
                    "over_privilege_delta": round(
                        f_s["over_privilege"] - o_s["over_privilege"], 3),
                }
                acc[gt][t]["obs"].append(o_s["false_deny"])
                acc[gt][t]["fused"].append(f_s["false_deny"])
            out["per_run"][rn][gt] = block

    # --------------------------------------------------------- aggregate ---
    for gt in GROUND_TRUTHS:
        agg = {"config_only_false_deny": {
            "values": acc_cfg[gt],
            "mean": round(mean(acc_cfg[gt]), 3),
            "spread": round(max(acc_cfg[gt]) - min(acc_cfg[gt]), 3)}}
        for t in TOOLS:
            o, f = acc[gt][t]["obs"], acc[gt][t]["fused"]
            if not o:
                agg[t] = None
                continue
            agg[t] = {
                "observed_false_deny": {"values": o, "mean": round(mean(o), 3),
                                        "spread": round(max(o) - min(o), 3)},
                "fused_false_deny": {"values": f, "mean": round(mean(f), 3),
                                     "spread": round(max(f) - min(f), 3)},
                "fused_coverage_mean": round(1 - mean(f), 3),
            }
        # does the ordering of tools by false-deny survive under this L?
        orders = []
        for i in range(len(runs)):
            ranked = sorted((t for t in TOOLS if acc[gt][t]["obs"]),
                            key=lambda t: acc[gt][t]["obs"][i])
            orders.append(tuple(ranked))
        agg["ordering_stable"] = len(set(orders)) == 1
        agg["orderings"] = [list(o) for o in orders]
        out["aggregate"][gt] = agg

    # ordering agreement *between* the two ground truths (the robustness test)
    ord_hand = out["aggregate"]["L_hand"]["orderings"][0]
    ord_derv = out["aggregate"]["L_derived"]["orderings"][0]
    out["aggregate"]["ordering_agrees_across_ground_truths"] = ord_hand == ord_derv

    print(json.dumps(out, indent=2))
    dest = os.path.join(HERE, "sensitivity_and_fusion.json")
    json.dump(out, open(dest, "w"), indent=2)
    sys.stderr.write(f"\nwrote {dest}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
