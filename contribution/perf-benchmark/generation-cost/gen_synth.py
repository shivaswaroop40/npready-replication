#!/usr/bin/env python3
"""Step 1, observation-only generation: stored journey-A Hubble capture -> synth edge set + policy.

Usage: gen_synth.py <APP> <OUTDIR>
Writes OUTDIR/synth_edges.json ([src, dst, port] triples, the set score_<app>.py builds as
hubble_edges(captureA)) and OUTDIR/netpol_synth.yaml.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import APPS, app_dir, load_score_module, render  # noqa: E402


def main():
    app, out = sys.argv[1], sys.argv[2]
    mod = load_score_module(app)
    triples = mod.hubble_edges(os.path.join(app_dir(app), "captureA", APPS[app]["hubble"]))
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "synth_edges.json"), "w") as f:
        json.dump(sorted(list(t) for t in triples), f)
    with open(os.path.join(out, "netpol_synth.yaml"), "w") as f:
        f.write(render(app, mod, triples, "synth"))


if __name__ == "__main__":
    main()
