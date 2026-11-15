#!/usr/bin/env python3
"""Correctness check and input/output sizes for the generation-cost benchmark.

Usage: verify.py <OUTROOT>   (OUTROOT/<APP>/ holds the outputs of the last timed run)
Compares each step's output with what the thesis stored:
  step 1  synth pair count            == scores.json analytical["synth (ours, traffic A)"].admit
          netpol_synth.yaml           == policies/netpol_synth.yaml            (enforcement semantics)
  step 2  config_derived_edges.json   == policies/config_derived_edges.json    (same set of records)
  step 3  fused pair count            == scores.json analytical["synth_plus_config ..."].admit
          netpol_synth_plus_config    == policies/netpol_synth_plus_config.yaml (enforcement semantics)
Enforcement semantics: the same set of selected workloads, each admitting the same set of
(source selector, port). Policy names, document order and deny-vs-empty-allow spelling are ignored.
Writes OUTROOT/verify.json and prints a summary.
"""
import json
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import APPS, app_dir, manifests_path  # noqa: E402

SYNTH_KEY = "synth (ours, traffic A)"
FUSED_KEY = "synth_plus_config (ours, traffic A + config)"


def semantics(path):
    out = {}
    with open(path) as f:
        for d in yaml.safe_load_all(f):
            if not d:
                continue
            tgt = tuple(sorted(d["spec"]["podSelector"]["matchLabels"].items()))
            adm = out.setdefault(tgt, set())
            for ing in d["spec"].get("ingress") or []:
                ports = [p["port"] for p in ing.get("ports") or []] or ["*"]
                for fr in ing.get("from") or []:
                    src = tuple(sorted(fr["podSelector"]["matchLabels"].items()))
                    adm.update((src, p) for p in ports)
    return out


def recset(d):
    return sorted(json.dumps(x, sort_keys=True) for x in d["needed"])


def count_flows(path):
    n = 0
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
                n += 1
            except ValueError:
                pass
    return n


def count_manifest_objects(mpath):
    n = 0
    files = [mpath] if os.path.isfile(mpath) else sorted(
        os.path.join(mpath, x) for x in os.listdir(mpath) if x.endswith((".yaml", ".yml")))
    for p in files:
        with open(p) as f:
            for d in yaml.safe_load_all(f):
                if isinstance(d, dict) and d.get("kind"):
                    n += len(d.get("items") or []) if d["kind"].endswith("List") else 1
    return n, len(files)


def main():
    root = sys.argv[1]
    report = {}
    for app in APPS:
        a, o = app_dir(app), os.path.join(root, app)
        scores = json.load(open(os.path.join(a, "scores", "scores.json")))["analytical"]
        synth = {tuple(x) for x in json.load(open(os.path.join(o, "synth_edges.json")))}
        fused = {tuple(x) for x in json.load(open(os.path.join(o, "fused_edges.json")))}
        derived = json.load(open(os.path.join(o, "config_derived_edges.json")))
        stored_derived = json.load(open(os.path.join(a, "policies", "config_derived_edges.json")))
        sp, fp = {(s, d) for s, d, _ in synth}, {(s, d) for s, d, _ in fused}
        sem = {}
        for name in ("netpol_synth", "netpol_synth_plus_config"):
            mine, stored = semantics(os.path.join(o, name + ".yaml")), semantics(os.path.join(a, "policies", name + ".yaml"))
            sem[name] = dict(equal=mine == stored, policies_mine=len(mine), policies_stored=len(stored),
                             rules=sum(len(v) for v in mine.values()),
                             only_mine=sorted(str((k, sorted(v - stored.get(k, set())))) for k, v in mine.items() if v - stored.get(k, set())),
                             only_stored=sorted(str((k, sorted(v - mine.get(k, set())))) for k, v in stored.items() if v - mine.get(k, set())),
                             targets_differ=sorted(str(k) for k in set(mine) ^ set(stored)),
                             byte_identical=open(os.path.join(o, name + ".yaml")).read() == open(os.path.join(a, "policies", name + ".yaml")).read())
        n_obj, n_files = count_manifest_objects(manifests_path(app))
        r = {
            "input": {"hubble_flow_records": count_flows(os.path.join(a, "captureA", APPS[app]["hubble"])),
                      "hubble_bytes": os.path.getsize(os.path.join(a, "captureA", APPS[app]["hubble"])),
                      "manifest_objects": n_obj, "manifest_files": n_files,
                      "manifest_input": os.path.relpath(manifests_path(app), a),
                      "manifest_bytes": (os.path.getsize(manifests_path(app)) if os.path.isfile(manifests_path(app)) else
                                         sum(os.path.getsize(os.path.join(manifests_path(app), x)) for x in os.listdir(manifests_path(app))))},
            "step1": {"synth_triples": len(synth), "synth_pairs": len(sp), "stored_admit": scores[SYNTH_KEY]["admit"],
                      "pairs_match": len(sp) == scores[SYNTH_KEY]["admit"], "yaml": sem["netpol_synth"]},
            "step2": {"declared_edges": len(derived["needed"]), "stored_edges": len(stored_derived["needed"]),
                      "same_records": recset(derived) == recset(stored_derived),
                      "same_order": derived == stored_derived},
            "step3": {"fused_triples": len(fused), "fused_pairs": len(fp), "stored_admit": scores[FUSED_KEY]["admit"],
                      "pairs_match": len(fp) == scores[FUSED_KEY]["admit"],
                      "config_only_pairs_added": len(fp - sp), "yaml": sem["netpol_synth_plus_config"]},
        }
        report[app] = r
        print(f"{app:20} flows={r['input']['hubble_flow_records']:>7} objs={n_obj:>4} | "
              f"s1 pairs {len(sp)}/{r['step1']['stored_admit']} yaml={sem['netpol_synth']['equal']} | "
              f"s2 edges {r['step2']['declared_edges']}/{r['step2']['stored_edges']} same={r['step2']['same_records']} order={r['step2']['same_order']} | "
              f"s3 pairs {len(fp)}/{r['step3']['stored_admit']} yaml={sem['netpol_synth_plus_config']['equal']}")
        for name, s in sem.items():
            if not s["equal"]:
                print("   ", name, "only_mine", s["only_mine"], "only_stored", s["only_stored"], "targets_differ", s["targets_differ"])
    json.dump(report, open(os.path.join(root, "verify.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
