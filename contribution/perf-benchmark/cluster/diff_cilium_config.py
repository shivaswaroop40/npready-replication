#!/usr/bin/env python3
"""Diff the live kube-system/cilium-config ConfigMap against the saved test-cluster dump.

Usage: diff_cilium_config.py <saved.json> [--live live.json] [--json]
The saved file is the 155-key `data` map dumped from test-cluster on 2026-09-10.
Without --live the live map is read with kubectl. Exit code 0 always; the report is the output.
"""
import json
import subprocess
import sys


def load_live(path=None):
    if path:
        with open(path) as f:
            d = json.load(f)
    else:
        out = subprocess.check_output(
            ["kubectl", "-n", "kube-system", "get", "cm", "cilium-config", "-o", "json"])
        d = json.loads(out)
    return d.get("data", d)


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    saved_path = args[0]
    live_path = args[args.index("--live") + 1] if "--live" in args else None
    with open(saved_path) as f:
        saved = json.load(f)
    saved = saved.get("data", saved)
    live = load_live(live_path)

    changed = {k: (saved[k], live[k]) for k in sorted(saved) if k in live and saved[k] != live[k]}
    only_saved = {k: saved[k] for k in sorted(saved) if k not in live}
    only_live = {k: live[k] for k in sorted(live) if k not in saved}
    same = sum(1 for k in saved if k in live and saved[k] == live[k])

    if "--json" in args:
        print(json.dumps({"saved_keys": len(saved), "live_keys": len(live), "identical": same,
                          "changed": changed, "only_in_saved": only_saved,
                          "only_in_live": only_live}, indent=1))
        return
    print(f"saved keys {len(saved)}, live keys {len(live)}, identical {same}, "
          f"changed {len(changed)}, only-in-saved {len(only_saved)}, only-in-live {len(only_live)}")
    for k, (a, b) in changed.items():
        print(f"CHANGED   {k}: saved={a!r} live={b!r}")
    for k, v in only_saved.items():
        print(f"MISSING   {k}: saved={v!r}")
    for k, v in only_live.items():
        print(f"EXTRA     {k}: live={v!r}")


if __name__ == "__main__":
    main()
