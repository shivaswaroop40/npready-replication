#!/usr/bin/env python3
"""perfbench host-speed canary (one per node, in its own systemd scope pb-canary).

Every --interval seconds it runs a fixed CPU-bound kernel for a fixed number of iterations
and appends one CSV row: when it ended, how long it took in wall time and in this thread's
CPU time, and how many iterations it ran. The kernel is a pure-Python integer loop (a 31-bit
linear congruential generator): single-threaded, no syscalls, no I/O, no allocation beyond
CPython's own small-object pool, and a working set that fits in L1. So it measures how much
work one guest CPU-second buys right now, and it is not sensitive to the guest's own cache or
memory traffic (which would move with the condition under test).

Speed index = iterations / CPU-second (main) and iterations / wall-second. On a hypervisor that
does not report steal, stolen time is charged to the running thread, so a slower host shows up
as fewer iterations per CPU-second. The wall index also includes waiting for a vCPU inside the
guest, which depends on the guest's own load; the analysis uses the CPU index.

The canary opens no socket and makes no connect(), so Hubble, IG trace_tcp and Otterize have
nothing to see. Its cost is one kernel run per interval: about 20 ms per 2 s = 1% of one core
(--iterations is sized for 15-25 ms on the bench's 2.5 GHz EPYC vCPUs; see --calibrate).
By default it rotates its CPU affinity over the allowed CPUs, one CPU per sample, so every vCPU
is measured equally often (column cpu; -1 when affinity is not available).

Columns: ts (node clock, end of the kernel, s), node, seq, cpu, iterations, wall_ns, cpu_ns,
invol_cs (involuntary context switches of this thread during the kernel).
Stops cleanly on SIGTERM/SIGINT or after --duration seconds and writes <out>.info.json with
its own CPU use. Standard library only; Linux for affinity and per-thread rusage.
"""
import argparse
import csv
import gc
import json
import os
import platform
import resource
import signal
import sys
import time

HEADER = ["ts", "node", "seq", "cpu", "iterations", "wall_ns", "cpu_ns", "invol_cs"]
KERNEL = "lcg31-py"
# Sizing (2026-10-03, --calibrate): 72 ns per iteration on Python 3.12.3 (Linux aarch64, Apple M-series
# host) and 79 ns on Python 3.14 (macOS arm64). A 2.5 GHz EPYC vCPU runs CPython about 1.3-2x
# slower per thread, so 100-160 ns per iteration and 150000 iterations = 15-24 ms there (0.75-1.2%
# of one core at a 2 s interval). Every row records the real wall_ns and cpu_ns, and the analysis
# flags a canary that used more than 1.5% of a core. Keep the value fixed across runs.
DEFAULT_ITERS = 150000

STOP = False


def _stop(_sig, _frm):
    global STOP
    STOP = True


def kernel(n):
    x = 1
    for _ in range(n):
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF
    return x


_RUSAGE = getattr(resource, "RUSAGE_THREAD", resource.RUSAGE_SELF)


def invol():
    return resource.getrusage(_RUSAGE).ru_nivcsw


def one(n):
    """-> (wall_ns, cpu_ns, involuntary context switches) of one kernel run"""
    v0 = invol()
    c0 = time.thread_time_ns()
    w0 = time.perf_counter_ns()
    kernel(n)
    w1 = time.perf_counter_ns()
    c1 = time.thread_time_ns()
    return w1 - w0, c1 - c0, invol() - v0


def calibrate(target_ms):
    """iterations for target_ms of CPU time on this machine (median of 5 runs)"""
    n = 20000
    while True:
        _, c, _ = one(n)
        if c >= 5e6 or n >= 1 << 30:
            break
        n *= 2
    per = sorted(one(n)[1] / n for _ in range(5))[2]
    return {"kernel": KERNEL, "ns_per_iteration": round(per, 3),
            "iterations_for_target": int(target_ms * 1e6 / per), "target_ms": target_ms,
            "default_iterations": DEFAULT_ITERS, "default_ms": round(DEFAULT_ITERS * per / 1e6, 2),
            "python": platform.python_version(), "machine": platform.machine()}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", help="CSV path (appended; header written if new)")
    ap.add_argument("--node", default=platform.node())
    ap.add_argument("--interval", type=float, default=2.0)
    ap.add_argument("--iterations", type=int, default=DEFAULT_ITERS)
    ap.add_argument("--duration", type=float, default=0, help="stop after N s (0 = until SIGTERM)")
    ap.add_argument("--no-rotate", action="store_true", help="do not rotate CPU affinity")
    ap.add_argument("--calibrate", type=float, metavar="MS", default=None,
                    help="print the iterations for MS ms of CPU time on this machine and exit")
    a = ap.parse_args()
    gc.disable()          # the kernel makes no reference cycles; no collector pauses inside it
    if a.calibrate is not None:
        print(json.dumps(calibrate(a.calibrate)))
        return 0
    if not a.out:
        ap.error("--out is required")
    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    cpus = []
    if not a.no_rotate and hasattr(os, "sched_setaffinity"):
        try:
            cpus = sorted(os.sched_getaffinity(0))
        except OSError:
            cpus = []
    info_path = a.out + ".info.json"
    info = {"node": a.node, "kernel": KERNEL, "iterations": a.iterations, "interval_s": a.interval,
            "rotate_cpus": cpus, "python": platform.python_version(), "machine": platform.machine(),
            "kernel_release": platform.release(), "ncpu": os.cpu_count(), "start_ts": time.time(),
            "pid": os.getpid()}
    with open(info_path, "w") as f:
        json.dump(info, f, indent=1)

    new = not os.path.exists(a.out) or os.path.getsize(a.out) == 0
    out = open(a.out, "a", newline="", buffering=1)      # line-buffered: every row is on disk
    w = csv.writer(out, lineterminator="\n")
    if new:
        w.writerow(HEADER)
    kernel(a.iterations // 10)                           # warm the interpreter's caches
    seq = 0
    speeds = []
    t_end = time.monotonic() + a.duration if a.duration > 0 else None
    next_t = time.monotonic()
    while not STOP:
        cpu = -1
        if cpus:
            cpu = cpus[seq % len(cpus)]
            try:
                os.sched_setaffinity(0, {cpu})
            except OSError:
                cpu = -1
        wall, cput, ic = one(a.iterations)
        w.writerow([f"{time.time():.3f}", a.node, seq, cpu, a.iterations, wall, cput, ic])
        if cput > 0:
            speeds.append(a.iterations / (cput / 1e9))
        seq += 1
        if t_end is not None and time.monotonic() >= t_end:
            break
        next_t += a.interval
        if next_t < time.monotonic():                    # fell behind (suspend): resync
            next_t = time.monotonic() + a.interval
        while not STOP and time.monotonic() < next_t:
            time.sleep(min(0.5, max(0.0, next_t - time.monotonic())))
    out.close()
    ru = resource.getrusage(resource.RUSAGE_SELF)
    elapsed = time.time() - info["start_ts"]
    cpu_s = ru.ru_utime + ru.ru_stime
    speeds.sort()
    info.update({"end_ts": time.time(), "samples": seq, "elapsed_s": round(elapsed, 3),
                 "own_cpu_s": round(cpu_s, 3),
                 "own_cpu_pct_of_core": round(100 * cpu_s / elapsed, 3) if elapsed > 0 else None,
                 "speed_cpu_median": round(speeds[len(speeds) // 2]) if speeds else None,
                 "max_rss_kib": ru.ru_maxrss})
    with open(info_path, "w") as f:
        json.dump(info, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
