#!/usr/bin/env python3
"""client_bins.py <run_dir>: count the capture clients' events per 5-s bin of event time.

hubble.json: one JSON object per line; flows carry "flow":{"time":"<RFC3339>"} (node clock),
other lines (lost_events, node status) are counted separately. ig_tcp.json: one event per line
with "timestamp_raw" (ns since the epoch) and "type" (connect/accept/close).
Writes <run_dir>/client_bins.json, so analyze.py can count events inside its analysis window
for every capture tool the same way. Uses regexes, not a JSON parse per line (cheap on cp-01).
"""
import datetime
import gzip
import json
import os
import re
import sys

BIN = 5
T_RE = re.compile(r'"time":"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d+)?)Z"')
R_RE = re.compile(r'"timestamp_raw":(\d+)')
TY_RE = re.compile(r'"type":"(\w+)"')


def iso_epoch(s):
    head, _, frac = s.partition(".")
    t = datetime.datetime.strptime(head, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc).timestamp()
    return t + (float("0." + frac) if frac else 0.0)


def opener(run, name):
    """the stream, plain or gzipped (a finished run dir has only the .gz)"""
    for p, op in ((os.path.join(run, name), open), (os.path.join(run, name + ".gz"), gzip.open)):
        if os.path.exists(p):
            return op(p, "rt", errors="replace")
    return None


def main():
    run = sys.argv[1]
    out = {"bin_s": BIN}
    fh = opener(run, "hubble.json")
    if fh:
        bins, other = {}, 0
        with fh:
            for line in fh:
                m = T_RE.search(line[:200]) if line.startswith('{"flow"') else None
                if not m:
                    other += 1
                    continue
                b = int(iso_epoch(m.group(1)) // BIN * BIN)
                bins[b] = bins.get(b, 0) + 1
        out["hubble"] = {"counts": bins, "non_flow_lines": other}
    fh = opener(run, "ig_tcp.json")
    if fh:
        bins, types, other = {}, {}, 0
        with fh:
            for line in fh:
                m = R_RE.search(line)
                if not m:
                    other += 1
                    continue
                b = int(int(m.group(1)) / 1e9 // BIN * BIN)
                bins[b] = bins.get(b, 0) + 1
                t = TY_RE.findall(line)
                ty = t[-1] if t else "?"
                types[ty] = types.get(ty, 0) + 1
        out["ig_tcp"] = {"counts": bins, "types": types, "non_event_lines": other}
    with open(os.path.join(run, "client_bins.json"), "w") as fh:
        json.dump(out, fh)


if __name__ == "__main__":
    sys.exit(main())
