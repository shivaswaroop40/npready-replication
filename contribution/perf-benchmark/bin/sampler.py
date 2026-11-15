#!/usr/bin/env python3
"""perfbench cgroup sampler (one per node).

Every --interval seconds it appends one row per cgroup to a CSV:
  - every container cgroup under kubepods (systemd or cgroupfs layout), mapped to
    namespace/pod/container through `crictl` (re-read when an unknown cgroup appears, at most
    every 10 s, and otherwise every 600 s) and /var/log/pods,
  - the harness client scopes (pb-*.scope, wherever systemd put them),
  - every top-level slice and every unit directly under system.slice (k3s, containerd, ...),
  - node totals from /proc/stat and /proc/meminfo (kind=node, id=node; steal as id=steal).

Columns: see HEADER. CPU is the cumulative counter (usage_usec), so readers compute rates
from deltas. Memory is in bytes. Working set = mem_current - mem_inactive_file.
For kind=node: cpu_usec = busy (user+nice+system+irq+softirq), mem_current = MemTotal -
MemAvailable, mem_anon = AnonPages, mem_file = Cached+Buffers, mem_inactive_file = Inactive(file).

Stops cleanly on SIGTERM/SIGINT (systemctl stop) or after --duration seconds, then writes
<out>.info.json with its own CPU use, so its overhead can be checked (<1% of a core).
cgroup v2 only (Ubuntu 24.04 + kernel 6.x); it exits with an error on v1.
"""
import argparse
import csv
import json
import os
import platform
import re
import resource
import shlex
import shutil
import signal
import subprocess
import sys
import time

HEADER = ["ts", "node", "kind", "id", "ns", "pod", "container", "cpu_usec",
          "throttled_usec", "mem_current", "mem_anon", "mem_file", "mem_inactive_file"]
CID_RE = re.compile(r"([0-9a-f]{64})")
UID_RE = re.compile(r"pod([0-9a-fA-F]{8}[-_][0-9a-fA-F]{4}[-_][0-9a-fA-F]{4}"
                    r"[-_][0-9a-fA-F]{4}[-_][0-9a-fA-F]{12})")
QOS_RE = re.compile(r"(besteffort|burstable|guaranteed)", re.I)

STOP = False


def _stop(_sig, _frm):
    global STOP
    STOP = True


def read_text(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except OSError:
        return None


def _read_raw(path):
    """bytes of a small pseudo-file, or None. os.open/os.read: no buffered text wrapper."""
    try:
        fd = os.open(path, os.O_RDONLY)
    except OSError:
        return None
    try:
        return os.read(fd, 65536)
    except OSError:
        return None
    finally:
        os.close(fd)


def cgroup_stats(path):
    """Return (cpu_usec, throttled_usec, mem_current, anon, file, inactive_file) as strings
    ('' when missing), or None if the cgroup vanished."""
    cpu = _read_raw(path + "/cpu.stat")
    if cpu is None:
        return None
    usage = thr = ""
    for line in cpu.split(b"\n"):
        if line.startswith(b"usage_usec "):
            usage = line[11:].decode()
        elif line.startswith(b"throttled_usec "):
            thr = line[15:].decode()
    cur = (_read_raw(path + "/memory.current") or b"").strip().decode()
    anon = fil = inact = ""
    for line in (_read_raw(path + "/memory.stat") or b"").split(b"\n"):
        if line.startswith(b"anon "):
            anon = line[5:].decode()
        elif line.startswith(b"file "):
            fil = line[5:].decode()
        elif line.startswith(b"inactive_file "):
            inact = line[14:].decode()
            break                      # inactive_file comes after anon and file
    return (usage, thr, cur, anon, fil, inact)


class Mapper:
    """container id / sandbox id / pod uid -> (ns, pod, container)."""

    def __init__(self, crictl_cmd, pods_log_dir, refresh_s=600.0):
        self.crictl = crictl_cmd
        self.pods_log_dir = pods_log_dir
        self.refresh_s = refresh_s
        self.containers = {}   # cid -> (ns, pod, container)
        self.sandboxes = {}    # sid -> (ns, pod)
        self.uids = {}         # uid -> (ns, pod)
        self.last = -1e9
        self.last_forced = -1e9
        self.errors = 0
        self.refreshes = 0

    def _crictl(self, args):
        if not self.crictl:
            return None
        try:
            out = subprocess.run(self.crictl + args, capture_output=True, timeout=15,
                                 check=True).stdout
            return json.loads(out or b"{}")
        except (OSError, subprocess.SubprocessError, ValueError):
            self.errors += 1
            return None

    def refresh(self, force=False):
        now = time.monotonic()
        if force:
            if now - self.last_forced < 10:
                return
            self.last_forced = now
        elif now - self.last < self.refresh_s:
            return
        self.last = now
        self.refreshes += 1
        cs = self._crictl(["ps", "-a", "-o", "json"])
        if cs:
            for c in cs.get("containers", []):
                lb = c.get("labels") or {}
                ns = lb.get("io.kubernetes.pod.namespace", "")
                pod = lb.get("io.kubernetes.pod.name", "")
                name = lb.get("io.kubernetes.container.name") or \
                    (c.get("metadata") or {}).get("name", "")
                self.containers[c.get("id", "")] = (ns, pod, name)
                uid = lb.get("io.kubernetes.pod.uid")
                if uid:
                    self.uids[uid] = (ns, pod)
        ps = self._crictl(["pods", "-o", "json"])
        if ps:
            for p in ps.get("items", []):
                md = p.get("metadata") or {}
                self.sandboxes[p.get("id", "")] = (md.get("namespace", ""), md.get("name", ""))
                if md.get("uid"):
                    self.uids[md["uid"]] = (md.get("namespace", ""), md.get("name", ""))
        # crictl-free fallback for ns/pod: /var/log/pods/<ns>_<pod>_<uid>
        try:
            for e in os.scandir(self.pods_log_dir):
                parts = e.name.split("_")
                if len(parts) == 3 and parts[2] not in self.uids:
                    self.uids[parts[2]] = (parts[0], parts[1])
        except OSError:
            pass

    def lookup(self, cid, uid):
        if cid in self.containers:
            ns, pod, name = self.containers[cid]
            return "container", ns, pod, name
        if cid in self.sandboxes:
            ns, pod = self.sandboxes[cid]
            return "sandbox", ns, pod, "POD"
        ns, pod = self.uids.get(uid, ("", ""))
        return "container", ns, pod, ""


def find_kubepods(root):
    for name, layout in (("kubepods.slice", "systemd"), ("kubepods", "cgroupfs")):
        p = os.path.join(root, name)
        if os.path.isdir(p):
            return p, layout
    # nested (e.g. k3s started inside another cgroup): search two levels down
    try:
        for e in os.scandir(root):
            if e.is_dir(follow_symlinks=False):
                for name, layout in (("kubepods.slice", "systemd"), ("kubepods", "cgroupfs")):
                    p = os.path.join(e.path, name)
                    if os.path.isdir(p):
                        return p, layout
    except OSError:
        pass
    return None, "none"


def iter_pod_dirs(kp_root):
    """Yield (pod_dir, uid). Pods sit directly under kubepods (guaranteed QoS) or one
    level down in a QoS slice."""
    stack = [(kp_root, 0)]
    while stack:
        d, depth = stack.pop()
        try:
            entries = list(os.scandir(d))
        except OSError:
            continue
        for e in entries:
            if not e.is_dir(follow_symlinks=False):
                continue
            m = UID_RE.search(e.name)
            if m:
                yield e.path, m.group(1).replace("_", "-").lower()
            elif depth == 0 and QOS_RE.search(e.name):
                stack.append((e.path, 1))


def iter_other(root, kp_root):
    """Yield (path, kind, id) for top-level slices, units under system.slice and pb-* scopes."""
    stack = [(root, 0)]
    while stack:
        d, depth = stack.pop()
        try:
            entries = list(os.scandir(d))
        except OSError:
            continue
        for e in entries:
            if not e.is_dir(follow_symlinks=False) or e.path == kp_root:
                continue
            name = e.name
            if name.startswith("pb-"):
                yield e.path, "client", name
                continue
            if depth == 0:
                yield e.path, "slice", name
            elif depth == 1 and os.path.basename(d) == "system.slice":
                yield e.path, "unit", name
            if depth < 3:
                stack.append((e.path, depth + 1))


def node_rows(proc_root, clk):
    rows = []
    stat = read_text(os.path.join(proc_root, "stat")) or ""
    busy = steal = ""
    for line in stat.splitlines():
        if line.startswith("cpu "):
            f = [int(x) for x in line.split()[1:]]
            f += [0] * (10 - len(f))
            user, nice, system, _idle, _iowait, irq, softirq, st = f[:8]
            busy = str(int((user + nice + system + irq + softirq) * 1_000_000 // clk))
            steal = str(int(st * 1_000_000 // clk))
            break
    mi = {}
    for line in (read_text(os.path.join(proc_root, "meminfo")) or "").splitlines():
        k, _, v = line.partition(":")
        parts = v.split()
        if parts:
            mi[k] = int(parts[0]) * 1024
    used = cached = anon = inact = ""
    if "MemTotal" in mi and "MemAvailable" in mi:
        used = str(mi["MemTotal"] - mi["MemAvailable"])
        cached = str(mi.get("Cached", 0) + mi.get("Buffers", 0))
        anon = str(mi.get("AnonPages", 0))
        inact = str(mi.get("Inactive(file)", 0))
    rows.append(("node", "node", "", "", "", busy, "", used, anon, cached, inact))
    rows.append(("node", "steal", "", "", "", steal, "", "", "", "", ""))
    return rows, mi.get("MemTotal")


def detect_crictl(arg):
    if arg is not None:
        return shlex.split(arg) if arg else []
    sock = "/run/k3s/containerd/containerd.sock"
    if os.path.exists(sock) and "CONTAINER_RUNTIME_ENDPOINT" not in os.environ:
        os.environ["CONTAINER_RUNTIME_ENDPOINT"] = "unix://" + sock
    if shutil.which("crictl"):
        return ["crictl"]
    if shutil.which("k3s"):
        return ["k3s", "crictl"]
    return []


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, help="CSV path (appended; header written if new)")
    ap.add_argument("--node", default=platform.node())
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--duration", type=float, default=0, help="stop after N s (0 = until SIGTERM)")
    ap.add_argument("--cgroup-root", default="/sys/fs/cgroup")
    ap.add_argument("--proc-root", default="/proc")
    ap.add_argument("--pods-log-dir", default="/var/log/pods")
    ap.add_argument("--crictl", default=None, help="crictl command (default: autodetect; '' disables)")
    # 600 s, not 30 s: one refresh (crictl ps + crictl pods) costs ~0.47 s CPU on the workers
    # (measured 2026-10-02), so a 30 s period alone was 1.6% of a core. New containers still
    # trigger a forced refresh (unknown cgroup -> refresh(force=True)).
    ap.add_argument("--refresh", type=float, default=600.0, help="periodic crictl refresh, s")
    a = ap.parse_args()

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    root = a.cgroup_root
    if not os.path.exists(os.path.join(root, "cgroup.controllers")):
        print(f"sampler: {root} is not a cgroup v2 mount", file=sys.stderr)
        return 2
    kp_root, layout = find_kubepods(root)
    clk = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else 100
    mapper = Mapper(detect_crictl(a.crictl), a.pods_log_dir, a.refresh)
    mapper.refresh()
    _, memtotal = node_rows(a.proc_root, clk)

    info_path = a.out + ".info.json"
    info = {
        "node": a.node, "interval_s": a.interval, "cgroup_root": root,
        "kubepods_root": kp_root, "layout": layout, "ncpu": os.cpu_count(),
        "mem_total_bytes": memtotal, "kernel": platform.release(),
        "python": platform.python_version(), "clk_tck": clk,
        "crictl": mapper.crictl, "start_ts": time.time(), "pid": os.getpid(),
    }
    with open(info_path, "w") as f:
        json.dump(info, f, indent=1)

    new = not os.path.exists(a.out) or os.path.getsize(a.out) == 0
    out = open(a.out, "a", newline="", buffering=1 << 16)
    w = csv.writer(out)
    if new:
        w.writerow(HEADER)
        out.flush()

    ticks = 0
    tick_cost = []
    t_end = time.monotonic() + a.duration if a.duration > 0 else None
    next_t = time.monotonic()
    node = a.node
    while not STOP:
        t0 = time.monotonic()
        mapper.refresh()        # before the timestamp: a crictl refresh can take 0.3-0.4 s
        ts = f"{time.time():.3f}"
        rows = []
        unknown = False
        if kp_root:
            for pod_dir, uid in iter_pod_dirs(kp_root):
                try:
                    entries = list(os.scandir(pod_dir))
                except OSError:
                    continue
                for e in entries:
                    if not e.is_dir(follow_symlinks=False):
                        continue
                    m = CID_RE.search(e.name)
                    if not m:
                        continue
                    st = cgroup_stats(e.path)
                    if st is None:
                        continue
                    cid = m.group(1)
                    kind, ns, pod, cname = mapper.lookup(cid, uid)
                    if not cname:
                        unknown = True
                    rows.append((ts, node, kind, cid, ns, pod, cname) + st)
        for path, kind, ident in iter_other(root, kp_root):
            st = cgroup_stats(path)
            if st is not None:
                rows.append((ts, node, kind, ident, "", "", "") + st)
        nrows, _ = node_rows(a.proc_root, clk)
        rows.extend((ts, node) + r for r in nrows)
        w.writerows(rows)
        out.flush()
        ticks += 1
        if unknown:
            mapper.refresh(force=True)
        tick_cost.append(time.monotonic() - t0)
        if t_end is not None and time.monotonic() >= t_end:
            break
        next_t += a.interval
        if next_t < time.monotonic():           # fell behind (suspend, slow I/O): resync
            next_t = time.monotonic() + a.interval
        while not STOP and time.monotonic() < next_t:
            time.sleep(min(1.0, max(0.0, next_t - time.monotonic())))

    out.close()
    ru_s = resource.getrusage(resource.RUSAGE_SELF)
    ru_c = resource.getrusage(resource.RUSAGE_CHILDREN)
    elapsed = time.time() - info["start_ts"]
    cpu_s = ru_s.ru_utime + ru_s.ru_stime + ru_c.ru_utime + ru_c.ru_stime
    info.update({
        "end_ts": time.time(), "ticks": ticks, "elapsed_s": round(elapsed, 3),
        "own_cpu_s": round(cpu_s, 3),
        "own_cpu_pct_of_core": round(100 * cpu_s / elapsed, 3) if elapsed > 0 else None,
        "tick_s_mean": round(sum(tick_cost) / len(tick_cost), 4) if tick_cost else None,
        "tick_s_max": round(max(tick_cost), 4) if tick_cost else None,
        "crictl_refreshes": mapper.refreshes, "crictl_errors": mapper.errors,
        "max_rss_kib": ru_s.ru_maxrss,
    })
    with open(info_path, "w") as f:
        json.dump(info, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
