#!/usr/bin/env python3
"""Step 3, fusion: union of the synth edge set (step 1) and the config-derived edge set (step 2),
then render the fused policy.

Usage: gen_fuse.py <APP> <OUTDIR>
Reads OUTDIR/synth_edges.json and OUTDIR/config_derived_edges.json (written by
`npready derive --json`), writes OUTDIR/fused_edges.json and OUTDIR/netpol_synth_plus_config.yaml.
The union is the one score_<app>.py scores: pairs(hubble_edges(A)) | pairs(config_edges()).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import config_triples, load_score_module, render  # noqa: E402


def main():
    app, out = sys.argv[1], sys.argv[2]
    mod = load_score_module(app)
    with open(os.path.join(out, "synth_edges.json")) as f:
        synth = {tuple(x) for x in json.load(f)}
    with open(os.path.join(out, "config_derived_edges.json")) as f:
        cfg = config_triples(mod, json.load(f))
    fused = synth | cfg
    with open(os.path.join(out, "fused_edges.json"), "w") as f:
        json.dump(sorted(list(t) for t in fused), f)
    with open(os.path.join(out, "netpol_synth_plus_config.yaml"), "w") as f:
        f.write(render(app, mod, fused, "synth_plus_config"))


if __name__ == "__main__":
    main()
