# Capture overhead: interleaved cycles (randomized multiple interleaved trials)

Generated 2026-10-05 18:02 UTC by analyze/analyze.py from `boutique-b2-final/results`. 50 run directories, 50 used, 0 excluded.

## Setup

- Cluster: iximiuz play, k3s, Cilium 1.19.5 configured like test-cluster. cp-01 has 2 vCPU and runs the load generator and the capture clients. worker-01 and worker-02 have 4 vCPU each and run the app.
- Conditions: baseline (Cilium, Hubble off, no other observer), Hubble (agent Hubble on, Relay, `hubble observe` through `kubectl port-forward` as in the thesis), Otterize (mapper and sniffers), IG trace_tcp (gadget DaemonSet and a streaming client), IG snapshot_socket (gadget DaemonSet and one snapshot near the end of the window). A metrics scraper fetches :9962, :9963 and :9965 every 15 s in every condition, like test-cluster' Prometheus.
- Each run: fresh Cilium agents and app pods, a 60 s idle segment (observer on, no load), 60 s warm-up, a 300 s steady window with the thesis journey-A load, then the fixed-count tests (3008 requests, concurrency 16, 1 repeats per mode, keep-alive and new connection per request).
- Order: K short cycles, each running every condition once; the order of cycle k is sequence k of a Williams design for 5 conditions (10 sequences: every condition twice in every position, every ordered pair of conditions adjacent twice), cycles 11-20 the same set in a fresh seeded order. Pairing within a cycle cancels host drift slower than a cycle (about an hour); the design spreads faster drift evenly over the conditions (Abedi and Brecht, ICPE 2017). A host-speed canary on every node gives the canary-normalised columns. CPU and memory come from cgroup counters sampled every 5 s on every node.
- The analysis uses the steady window minus its first 15 s and last 10 s.

## How to read the tables

- Each cycle is a block: every Δ is the mean of the per-cycle differences (technique minus the same cycle's baseline), with a t-based 95% CI (df = cycles - 1) in brackets; with 10 cycles the t quantile is 2.26. In the standard tables 'rep' means cycle. The first table of each app gives every endpoint raw and canary-normalised, with Holm across the techniques; the drift diagnostic shows whether the host moved during the matrix.
- "n.s." means the 95% CI includes 0. For a fixed-count overhead the upper CI bound is then given as the most the overhead can be.
- Primary endpoints (Holm-adjusted per app over 4 techniques x 4 endpoints): Δ cluster busy CPU, Δ observer memory, fixed-count time keep-alive and new connection. All other p-values are exploratory and unadjusted. Welch's test on the run values is in the CSVs as a second check.
- Δ is the technique minus the baseline. A negative Δ is noise or a side effect, not a saving.
- Transferable numbers: Δ cores, Δ MiB, Δ % of capacity, the fixed-count overhead and the projection. A percentage of this bench's baseline is not transferable to test-cluster, whose baseline carried the whole platform.

## Summary across apps

Per-app values, grouped by what limits the fixed-count test (quota-bound: throttled app containers; node-bound: node CPU). Steady-window latency is left out of the summary: it is bucket-limited and the steady load is a controlled input.

| Technique | Regime | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn | test-cluster CPU, % of 18 vCPU (est.) |
|---|---|---|---|---|---|---|
| Hubble | quota-bound | boutique +0.062 | boutique +0.84% | boutique +1.1% n.s. | boutique +7.1% | boutique +0.30% |
| Otterize | quota-bound | boutique +0.087 | boutique +0.96% | boutique -1.3% n.s. | boutique +2.5% n.s. | boutique +0.70% |
| IG trace_tcp | quota-bound | boutique +0.216 | boutique +2.69% | boutique +1.0% n.s. | boutique +2.3% n.s. | boutique +2.27% |
| IG snapshot_socket | quota-bound | boutique +0.211 | boutique +2.55% | boutique -0.3% n.s. | boutique +2.4% n.s. | boutique +2.24% |

Diagnostic only, do not quote: the same, canary-normalised (each run scaled to the app's median canary speed). The 2026-10-03 validation showed the canary does not track the host drift (r 0.41, normalised CV 16.4% vs 16.6% raw) and inflates deltas 1.7-4.7x. The raw paired deltas above, over interleaved cycles, are the result.

| Technique | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn |
|---|---|---|---|---|
| Hubble | boutique +0.062 | boutique +0.86% | boutique +0.0% n.s. | boutique +8.4% |
| Otterize | boutique +0.087 | boutique +0.98% | boutique -1.3% n.s. | boutique +1.2% n.s. |
| IG trace_tcp | boutique +0.218 | boutique +2.74% | boutique +0.8% n.s. | boutique +2.4% n.s. |
| IG snapshot_socket | boutique +0.212 | boutique +2.59% | boutique +0.6% n.s. | boutique +3.2% n.s. |

## boutique

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.084 [+0.072, +0.097] | <0.001 | <0.001 | +0.086 [+0.072, +0.100] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.096 [+0.086, +0.107] | <0.001 | <0.001 | +0.098 [+0.087, +0.110] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.269 [+0.259, +0.279] | <0.001 | <0.001 | +0.274 [+0.265, +0.283] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.255 [+0.241, +0.270] | <0.001 | <0.001 | +0.259 [+0.243, +0.276] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Hubble | +0.062 [+0.060, +0.063] | <0.001 | <0.001 | +0.062 [+0.059, +0.065] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.087 [+0.085, +0.088] | <0.001 | <0.001 | +0.087 [+0.085, +0.090] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.216 [+0.213, +0.219] | <0.001 | <0.001 | +0.218 [+0.215, +0.221] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.211 [+0.207, +0.214] | <0.001 | <0.001 | +0.212 [+0.208, +0.216] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | +0.001 [-0.002, +0.004] (n.s.) | 0.369 | 1.000 | +0.001 [-0.002, +0.004] (n.s.) | 0.327 | 0.654 | 10 |
| Δ app CPU (cores) | Otterize | +0.001 [-0.002, +0.004] (n.s.) | 0.372 | 1.000 | +0.001 [-0.001, +0.003] (n.s.) | 0.126 | 0.407 | 10 |
| Δ app CPU (cores) | IG trace_tcp | -0.001 [-0.004, +0.003] (n.s.) | 0.675 | 1.000 | -0.000 [-0.004, +0.003] (n.s.) | 0.915 | 0.915 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | +0.002 [-0.001, +0.005] (n.s.) | 0.114 | 0.457 | +0.002 [-0.001, +0.005] (n.s.) | 0.102 | 0.407 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.039 [+0.037, +0.041] | <0.001 | <0.001 | +0.040 [+0.038, +0.042] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.012 [+0.010, +0.013] | <0.001 | <0.001 | +0.012 [+0.009, +0.016] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.069 [+0.067, +0.071] | <0.001 | <0.001 | +0.071 [+0.069, +0.073] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.057 [+0.054, +0.060] | <0.001 | <0.001 | +0.059 [+0.055, +0.062] | <0.001 | <0.001 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +98 [+95, +101] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +80 [+78, +82] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +135 [+132, +138] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +114 [+110, +119] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +111 [+95, +127] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +90 [+75, +105] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +153 [+150, +156] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +144 [+99, +188] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | +1.1% [-2.7, +4.8] (n.s.) | 0.535 | 1.000 | +0.0% [-4.2, +4.2] (n.s.) | 0.987 | 1.000 | 10 |
| fixed-count time, keep-alive | Otterize | -1.3% [-4.1, +1.5] (n.s.) | 0.337 | 1.000 | -1.3% [-5.5, +3.0] (n.s.) | 0.510 | 1.000 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | +1.0% [-2.6, +4.6] (n.s.) | 0.542 | 1.000 | +0.8% [-3.7, +5.3] (n.s.) | 0.685 | 1.000 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | -0.3% [-3.3, +2.6] (n.s.) | 0.807 | 1.000 | +0.6% [-3.7, +4.9] (n.s.) | 0.748 | 1.000 | 10 |
| fixed-count time, new conn | Hubble | +7.1% [+3.0, +11.2] | 0.004 | 0.015 | +8.4% [+3.4, +13.3] | 0.004 | 0.016 | 10 |
| fixed-count time, new conn | Otterize | +2.5% [-0.6, +5.5] (n.s.) | 0.099 | 0.297 | +1.2% [-3.4, +5.8] (n.s.) | 0.569 | 0.587 | 10 |
| fixed-count time, new conn | IG trace_tcp | +2.3% [-1.0, +5.7] (n.s.) | 0.154 | 0.302 | +2.4% [-2.4, +7.1] (n.s.) | 0.293 | 0.587 | 10 |
| fixed-count time, new conn | IG snapshot_socket | +2.4% [-1.0, +5.8] (n.s.) | 0.151 | 0.302 | +3.2% [-0.5, +6.9] (n.s.) | 0.080 | 0.240 | 10 |
| canary speed, workers, steady window (check) | Hubble | +0.28% [-0.98, +1.55] (n.s.) | 0.625 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | +0.55% [-0.89, +1.99] (n.s.) | 0.407 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | +0.71% [-0.35, +1.77] (n.s.) | 0.165 | 0.660 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | +0.22% [-1.04, +1.49] (n.s.) | 0.699 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 3.5% raw, 5.2% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.30; new conn: CV of the baseline time across cycles 3.1% raw, 5.2% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.09.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 10-04 04:55 | ig_snap ig_tcp baseline otterize hubble | 64.6 | 64.2 | 65.0 | 64.3 | 0.082 | 0.082 | 3.29 | 0.99 | 3.32 |
| 12 | 10-04 06:01 | hubble otterize baseline ig_tcp ig_snap | 63.2 | 66.4 | 63.5 | 63.7 | 0.085 | 0.086 | 3.37 | 1.02 | 3.31 |
| 13 | 10-04 07:07 | otterize ig_tcp hubble ig_snap baseline | 68.1 | 69.2 | 67.2 | 68.2 | 0.085 | 0.085 | 3.34 | 1.01 | 3.36 |
| 14 | 10-04 08:12 | baseline ig_snap hubble ig_tcp otterize | 68.8 | 70.1 | 65.4 | 72.4 | 0.084 | 0.083 | 3.27 | 0.99 | 3.31 |
| 15 | 10-04 09:17 | ig_tcp otterize ig_snap hubble baseline | 65.3 | 67.4 | 62.9 | 62.9 | 0.083 | 0.083 | 3.35 | 1.01 | 3.31 |
| 16 | 10-04 10:24 | otterize hubble ig_tcp baseline ig_snap | 63.1 | 62.4 | 67.2 | 66.5 | 0.087 | 0.087 | 3.31 | 1.00 | 3.32 |
| 17 | 10-04 11:30 | hubble baseline otterize ig_snap ig_tcp | 68.9 | 70.2 | 68.6 | 70.4 | 0.091 | 0.091 | 3.30 | 1.00 | 3.32 |
| 18 | 10-04 12:36 | ig_tcp ig_snap otterize baseline hubble | 65.3 | 63.5 | 62.4 | 62.5 | 0.089 | 0.088 | 3.28 | 0.99 | 3.35 |
| 19 | 10-04 13:41 | baseline hubble ig_snap otterize ig_tcp | 67.9 | 73.1 | 65.0 | 66.7 | 0.083 | 0.082 | 3.28 | 0.99 | 3.31 |
| 20 | 10-04 14:48 | ig_snap baseline ig_tcp hubble otterize | 68.5 | 70.8 | 64.8 | 70.5 | 0.082 | 0.083 | 3.33 | 1.00 | 3.31 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 11 IG snapshot_socket; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.062 [+0.060, +0.063] | <0.001 | +0.061 | 0.002 | +0.062 [+0.060, +0.063] | 10 | robust |
| Δ observer CPU | Otterize | +0.087 [+0.085, +0.088] | <0.001 | +0.087 | 0.002 | +0.087 [+0.085, +0.088] | 10 | robust |
| Δ observer CPU | IG trace_tcp | +0.216 [+0.213, +0.219] | <0.001 | +0.217 | 0.002 | +0.216 [+0.213, +0.219] | 10 | robust |
| Δ observer CPU | IG snapshot_socket | +0.211 [+0.207, +0.214] | <0.001 | +0.212 | 0.002 | +0.211 [+0.208, +0.214] | 9 | robust |
| Δ observer anon memory | Hubble | +98 [+95, +101] | <0.001 | +98 | 0.002 | +98 [+95, +101] | 10 | robust |
| Δ observer anon memory | Otterize | +80 [+78, +82] | <0.001 | +81 | 0.002 | +80 [+78, +82] | 10 | robust |
| Δ observer anon memory | IG trace_tcp | +135 [+132, +138] | <0.001 | +133 | 0.002 | +135 [+132, +138] | 10 | robust |
| Δ observer anon memory | IG snapshot_socket | +114 [+110, +119] | <0.001 | +113 | 0.002 | +115 [+110, +120] | 9 | robust |
| fixed-count time, keep-alive | Hubble | +1.1% [-2.7, +4.8] (n.s.) | 1.000 | +0.2% | 0.625 | +1.1% [-2.7, +4.8] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | Otterize | -1.3% [-4.1, +1.5] (n.s.) | 1.000 | -1.9% | 0.375 | -1.3% [-4.1, +1.5] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | IG trace_tcp | +1.0% [-2.6, +4.6] (n.s.) | 1.000 | +1.7% | 0.557 | +1.0% [-2.6, +4.6] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | IG snapshot_socket | -0.3% [-3.3, +2.6] (n.s.) | 1.000 | -0.9% | 0.375 | -0.3% [-3.7, +3.1] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +7.1% [+3.0, +11.2] | 0.029 | +8.6% | 0.010 | +7.1% [+3.0, +11.2] | 10 | robust |
| fixed-count time, new conn | Otterize | +2.5% [-0.6, +5.5] (n.s.) | 0.694 | +2.0% | 0.064 | +2.5% [-0.6, +5.5] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | +2.3% [-1.0, +5.7] (n.s.) | 0.905 | +2.8% | 0.160 | +2.3% [-1.0, +5.7] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | IG snapshot_socket | +2.4% [-1.0, +5.8] (n.s.) | 0.905 | +4.2% | 0.232 | +2.6% [-1.3, +6.4] (n.s.) | 9 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 3008 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 1.14 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 66.36 ± 2.33 (n=10) | 66.99 ± 2.44 (n=10) | +1.07% [-2.69, +4.84] (n.s.) (< 4.8% at 95%) | 0.535 | 1.000 | recommendationservice 1.04 | 0.01 |
| keepalive | Otterize | 66.36 ± 2.33 (n=10) | 65.48 ± 2.44 (n=10) | -1.26% [-4.06, +1.54] (n.s.) (< 1.5% at 95%) | 0.337 | 1.000 | frontend 1.02 | 0.00 |
| keepalive | IG trace_tcp | 66.36 ± 2.33 (n=10) | 66.94 ± 1.80 (n=10) | +1.01% [-2.60, +4.63] (n.s.) (< 4.6% at 95%) | 0.542 | 1.000 | recommendationservice 0.98 | 0.00 |
| keepalive | IG snapshot_socket | 66.36 ± 2.33 (n=10) | 66.11 ± 2.78 (n=10) | -0.33% [-3.29, +2.64] (n.s.) (< 2.6% at 95%) | 0.807 | 1.000 | recommendationservice 1.06 | 0.01 |
| newconn | Hubble | 65.19 ± 2.01 (n=10) | 69.73 ± 2.82 (n=10) | +7.07% [+2.96, +11.19] | 0.004 | 0.029 | frontend 1.11 | 1.00 |
| newconn | Otterize | 65.19 ± 2.01 (n=10) | 66.77 ± 2.56 (n=10) | +2.48% [-0.57, +5.53] (n.s.) (< 5.5% at 95%) | 0.099 | 0.694 | recommendationservice 1.08 | 1.01 |
| newconn | IG trace_tcp | 65.19 ± 2.01 (n=10) | 66.62 ± 1.82 (n=10) | +2.30% [-1.05, +5.66] (n.s.) (< 5.7% at 95%) | 0.154 | 0.905 | recommendationservice 0.99 | 1.00 |
| newconn | IG snapshot_socket | 65.19 ± 2.01 (n=10) | 66.68 ± 2.37 (n=10) | +2.37% [-1.04, +5.79] (n.s.) (< 5.8% at 95%) | 0.151 | 0.905 | recommendationservice 0.99 | 1.00 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 66.36 ± 2.33 | 3.52% | 3.52% | 10 |
| newconn | 65.19 ± 2.01 | 3.08% | 3.08% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.097 ± 0.002 | 0.009 | - | 0.485 ± 0.008 | 0.047 | - | - | - | - |
| Hubble | 0.158 ± 0.002 | 0.017 | +0.062 [+0.060, +0.063] | 0.570 ± 0.017 | 0.051 | +0.084 [+0.072, +0.097] | +0.84% | +0.039 | <0.001 / <0.001 |
| Otterize | 0.183 ± 0.002 | 0.012 | +0.087 [+0.085, +0.088] | 0.582 ± 0.018 | 0.045 | +0.096 [+0.086, +0.107] | +0.96% | +0.012 | <0.001 / <0.001 |
| IG trace_tcp | 0.313 ± 0.004 | 0.014 | +0.216 [+0.213, +0.219] | 0.754 ± 0.013 | 0.046 | +0.269 [+0.259, +0.279] | +2.69% | +0.069 | <0.001 / <0.001 |
| IG snapshot_socket | 0.307 ± 0.004 | 0.018 | +0.211 [+0.207, +0.214] | 0.741 ± 0.015 | 0.050 | +0.255 [+0.241, +0.270] | +2.55% | +0.057 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.032 [+0.029, +0.035] | +0.015 [+0.008, +0.023] | +0.031 [+0.010, +0.053] | 53% |
| Otterize | +0.086 [+0.084, +0.089] | +0.022 [+0.016, +0.028] | +0.104 [+0.087, +0.120] | 100% |
| IG trace_tcp | +0.218 [+0.214, +0.221] | +0.070 [+0.063, +0.077] | +0.274 [+0.256, +0.291] | 101% |
| IG snapshot_socket | +0.207 [+0.203, +0.211] | +0.055 [+0.047, +0.064] | +0.250 [+0.233, +0.266] | 98% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.063 [+0.058, +0.068] | +0.071 [+0.018, +0.124] | +0.038 [+0.032, +0.044] | 2.09 → 2.10 | 16% |
| keepalive | Otterize | +0.087 [+0.085, +0.090] | +0.092 [+0.040, +0.145] | +0.009 [+0.003, +0.015] | 2.09 → 1.99 | 14% |
| keepalive | IG trace_tcp | +0.210 [+0.206, +0.214] | +0.251 [+0.198, +0.304] | +0.069 [+0.062, +0.075] | 2.09 → 1.95 | 18% |
| keepalive | IG snapshot_socket | +0.204 [+0.200, +0.207] | +0.238 [+0.178, +0.298] | +0.054 [+0.047, +0.061] | 2.09 → 2.05 | 18% |
| newconn | Hubble | +0.592 [+0.576, +0.608] | +0.750 [+0.677, +0.823] | +0.255 [+0.241, +0.268] | 2.14 → 2.08 | 35% |
| newconn | Otterize | +0.118 [+0.114, +0.121] | +0.108 [+0.052, +0.164] | +0.009 [+0.003, +0.015] | 2.14 → 2.05 | 17% |
| newconn | IG trace_tcp | +0.317 [+0.313, +0.322] | +0.473 [+0.399, +0.548] | +0.211 [+0.201, +0.221] | 2.14 → 1.91 | 27% |
| newconn | IG snapshot_socket | +0.202 [+0.196, +0.208] | +0.195 [+0.138, +0.253] | +0.052 [+0.043, +0.060] | 2.14 → 1.89 | 20% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 689 ± 13 | 1.9 | 1.19 | 370 | - | - | 3250 ± 43 | - | - |
| Hubble | 800 ± 26 (peak 812) | 11.2 | 7.67 | 468 | +98 [+95, +101] | +111 [+95, +127] | 3362 ± 37 | +0.61% | <0.001 / <0.001 |
| Otterize | 779 ± 25 (peak 784) | 2.5 | 1.18 | 451 | +80 [+78, +82] | +90 [+75, +105] | 3366 ± 43 | +0.50% | <0.001 / <0.001 |
| IG trace_tcp | 842 ± 14 (peak 851) | 5.1 | -1.97 | 505 | +135 [+132, +138] | +153 [+150, +156] | 3477 ± 44 | +0.84% | <0.001 / <0.001 |
| IG snapshot_socket | 832 ± 65 (peak 882) | 16.2 | 6.64 | 485 | +114 [+110, +119] | +144 [+99, +188] | 3437 ± 46 | +0.72% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.084 | 0.112 | 0.085 | 0.086 | 0.087 |
| cilium-envoy | 0.007 | 0.007 | 0.007 | 0.007 | 0.008 |
| cilium-operator | 0.005 | 0.005 | 0.005 | 0.005 | 0.005 |
| hubble-relay | 0.000 | 0.015 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.010 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.076 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.211 | 0.207 |
| client-hubble | 0.000 | 0.019 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.003 | 0.001 |
| app | 0.085 | 0.086 | 0.086 | 0.084 | 0.087 |
| loadgen | 0.006 | 0.007 | 0.007 | 0.006 | 0.006 |
| k3s | 0.208 | 0.246 | 0.218 | 0.277 | 0.265 |
| k8s-addons | 0.008 | 0.008 | 0.009 | 0.008 | 0.008 |
| os | 0.003 | 0.003 | 0.003 | 0.003 | 0.003 |
| harness | 0.080 | 0.080 | 0.080 | 0.080 | 0.080 |
| node | 0.485 | 0.570 | 0.582 | 0.754 | 0.741 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%. At under 5 req/s the window holds few requests; do not read the p95/p99 deltas.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 2.20 ± 0.07 | 21.2 ± 0.9 | - | 58.4 ± 6.9 | - | 97.5 ± 9.1 | - | 0.07 |
| Hubble | 2.20 ± 0.05 | 21.3 ± 0.5 | +0.7% [-3.1, +4.4] (n.s.) | 60.7 ± 7.8 | +6.2% [-10.5, +22.9] (n.s.) | 105.3 ± 35.8 | +9.0% [-19.3, +37.3] (n.s.) | 0.05 |
| Otterize | 2.20 ± 0.04 | 21.2 ± 0.9 | +0.2% [-4.3, +4.7] (n.s.) | 63.9 ± 7.1 | +10.8% [-1.3, +22.9] (n.s.) | 104.6 ± 10.0 | +8.2% [-2.2, +18.5] (n.s.) | 0.02 |
| IG trace_tcp | 2.16 ± 0.08 | 21.3 ± 0.5 | +0.7% [-3.1, +4.4] (n.s.) | 58.2 ± 5.8 | +1.7% [-12.9, +16.3] (n.s.) | 96.9 ± 5.4 | +0.2% [-7.6, +7.9] (n.s.) | 0.00 |
| IG snapshot_socket | 2.22 ± 0.05 | 21.6 ± 0.5 | +2.1% [-2.3, +6.5] (n.s.) | 62.7 ± 6.2 | +9.6% [-6.7, +25.8] (n.s.) | 100.1 ± 13.4 | +3.7% [-9.3, +16.7] (n.s.) | 0.05 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 2.9 | 2.86 | 0.00 | - | - | - | - | - |
| Hubble | 3.1 | 3.02 | 0.05 | +707 [+602, +812] | +13415 [+12940, +13890] | +13402 [+12924, +13881] | +18684 [+16283, +21086] | 32.4 (thesis 33.2) |
| Otterize | 3.7 | 3.72 | -0.07 | +21 [-33, +74] (n.s.) | +716 [+664, +767] | +710 [+659, +761] | +346 [-1027, +1719] (n.s.) | - |
| IG trace_tcp | 2.9 | 2.87 | -0.02 | -172 [-247, -98] | +2287 [+2165, +2410] | +2289 [+2166, +2412] | +5046 [+3703, +6389] | 5.7 (thesis 5.7) |
| IG snapshot_socket | 2.9 | 2.85 | 0.02 | -72 [-117, -27] | -97 [-243, +48] (n.s.) | -98 [-243, +48] (n.s.) | -732 [-2204, +740] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 30%. Lost events: 0 in the window, 73 over the whole run (fixed-count tests included). hubble_* series at the end: 302.

| Class | flows/s | share |
|---|---|---|
| app | 12.7 | 27% |
| probe | 20.8 | 44% |
| client_feedback | 2.6 | 6% |
| other | 11.6 | 24% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.211 [+0.207, +0.214] cores. Standing (window before the snapshot) minus baseline observer: +0.208 cores; one snapshot adds 1.04 ± 0.39 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.591 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.055 [+0.050, +0.060] | +0.066 | +0.084 [+0.052, +0.116] | +0.30% / +0.47% | +72 [+54, +90] | +0.12% |
| Otterize | +0.126 [+0.123, +0.130] | +0.126 | +0.155 [+0.131, +0.179] | +0.70% / +0.86% | +115 [+94, +135] | +0.20% |
| IG trace_tcp | +0.409 [+0.402, +0.416] | +0.406 | +0.515 [+0.493, +0.536] | +2.27% / +2.86% | +310 [+294, +325] | +0.53% |
| IG snapshot_socket | +0.403 [+0.394, +0.411] | +0.403 | +0.490 [+0.465, +0.515] | +2.24% / +2.72% | +320 [+233, +408] | +0.55% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 11 | baseline | 3 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 64.98 |
| 12 | baseline | 3 | 0.28% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 63.46 |
| 13 | baseline | 5 | 0.90% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 67.23 |
| 14 | baseline | 1 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.36 |
| 15 | baseline | 5 | 0.16% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 62.87 |
| 16 | baseline | 4 | 0.01% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 67.17 |
| 17 | baseline | 2 | 0.04% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 68.65 |
| 18 | baseline | 4 | 0.24% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 62.43 |
| 19 | baseline | 1 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 64.98 |
| 20 | baseline | 2 | 0.04% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 64.76 |
| 11 | Hubble | 5 | 0.53% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 72.87 |
| 12 | Hubble | 1 | 0.06% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 70.18 |
| 13 | Hubble | 3 | 0.46% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 71.67 |
| 14 | Hubble | 3 | 0.04% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 72.02 |
| 15 | Hubble | 4 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 70.17 |
| 16 | Hubble | 2 | 0.04% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 69.81 |
| 17 | Hubble | 1 | 0.30% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 64.18 |
| 18 | Hubble | 5 | 0.04% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 66.83 |
| 19 | Hubble | 2 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 67.22 |
| 20 | Hubble | 4 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 72.34 |
| 11 | Otterize | 4 | 0.03% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 68.52 |
| 12 | Otterize | 2 | 0.35% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 63.74 |
| 13 | Otterize | 1 | 0.10% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 66.98 |
| 14 | Otterize | 5 | 0.94% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.99 |
| 15 | Otterize | 2 | 0.05% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.15 |
| 16 | Otterize | 1 | 0.04% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 63.72 |
| 17 | Otterize | 3 | 0.04% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 71.88 |
| 18 | Otterize | 3 | 1.91% (high) | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 69.33 |
| 19 | Otterize | 4 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.61 |
| 20 | Otterize | 5 | 0.01% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 66.78 |
| 11 | IG trace_tcp | 2 | 0.40% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 64.66 |
| 12 | IG trace_tcp | 4 | 0.22% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 67.57 |
| 13 | IG trace_tcp | 2 | 0.63% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.52 |
| 14 | IG trace_tcp | 4 | 0.03% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.95 |
| 15 | IG trace_tcp | 1 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.89 |
| 16 | IG trace_tcp | 3 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 70.17 |
| 17 | IG trace_tcp | 5 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 64.33 |
| 18 | IG trace_tcp | 1 | 0.41% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 68.75 |
| 19 | IG trace_tcp | 5 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 67.14 |
| 20 | IG trace_tcp | 3 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 66.23 |
| 11 | IG snapshot_socket | 1 | 0.68% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.44 |
| 12 | IG snapshot_socket | 5 | 0.07% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 67.05 |
| 13 | IG snapshot_socket | 4 | 0.14% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 61.79 |
| 14 | IG snapshot_socket | 2 | 0.19% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 69.18 |
| 15 | IG snapshot_socket | 3 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 65.81 |
| 16 | IG snapshot_socket | 5 | 0.01% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 66.60 |
| 17 | IG snapshot_socket | 4 | 0.03% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 67.69 |
| 18 | IG snapshot_socket | 2 | 0.02% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 64.74 |
| 19 | IG snapshot_socket | 3 | 0.56% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 69.64 |
| 20 | IG snapshot_socket | 1 | 0.09% | 6ac1db3f33e2d67d2b66cdba | 2d6d0b2a,d4e1e3ad,a401fb78 | 68.82 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 11 | baseline | 3.30/3.29 | 3.31/3.28 | 3.34/3.26 | 3.28/3.28 | 0.99 |
| 11 | Hubble | 3.36/3.50 | 3.36/3.44 | 3.39/3.32 | 3.25/3.21 | 1.02 |
| 11 | Otterize | 3.40/3.38 | 3.36/3.28 | 3.27/3.35 | 3.37/3.37 | 1.00 |
| 11 | IG trace_tcp | 3.27/3.34 | 3.30/3.26 | 3.34/3.29 | 3.46/3.32 | 0.99 |
| 11 | IG snapshot_socket | 3.24/3.30 | 3.32/3.33 | 3.28/3.42 | 3.26/3.39 | 1.00 |
| 12 | baseline | 3.27/3.29 | 3.35/3.39 | 3.45/3.53 | 3.37/3.29 | 1.02 |
| 12 | Hubble | 3.28/3.26 | 3.33/3.27 | 3.35/3.23 | 3.36/3.43 | 1.00 |
| 12 | Otterize | 3.28/3.30 | 3.33/3.29 | 3.47/3.52 | 3.37/3.32 | 1.00 |
| 12 | IG trace_tcp | 3.36/3.47 | 3.27/3.36 | 3.32/3.57 | 3.24/3.75 | 1.00 |
| 12 | IG snapshot_socket | 3.22/3.22 | 3.26/3.28 | 3.32/3.30 | 3.35/3.32 | 0.99 |
| 13 | baseline | 3.29/3.30 | 3.35/3.32 | 3.36/3.37 | 3.33/3.39 | 1.01 |
| 13 | Hubble | 3.22/3.28 | 3.43/3.44 | 3.46/3.38 | 3.57/3.51 | 1.04 |
| 13 | Otterize | 3.31/3.36 | 3.33/3.33 | 3.39/3.42 | 3.35/3.34 | 1.00 |
| 13 | IG trace_tcp | 3.28/3.27 | 3.36/3.30 | 3.31/3.33 | 3.28/3.32 | 1.00 |
| 13 | IG snapshot_socket | 3.31/3.28 | 3.40/3.29 | 3.32/3.39 | 3.69/3.56 | 1.01 |
| 14 | baseline | 3.26/3.26 | 3.24/3.29 | 3.29/3.46 | 3.70/3.65 | 0.99 |
| 14 | Hubble | 3.28/3.25 | 3.27/3.31 | 3.43/3.29 | 3.59/3.29 | 0.99 |
| 14 | Otterize | 3.28/3.24 | 3.40/3.30 | 3.28/3.29 | 3.25/3.27 | 1.01 |
| 14 | IG trace_tcp | 3.39/3.21 | 3.41/3.30 | 3.42/3.20 | 3.47/3.29 | 1.01 |
| 14 | IG snapshot_socket | 3.30/3.29 | 3.30/3.32 | 3.37/3.40 | 3.36/3.50 | 1.00 |
| 15 | baseline | 3.29/3.32 | 3.36/3.34 | 3.54/3.30 | 3.40/3.24 | 1.01 |
| 15 | Hubble | 3.35/3.30 | 3.30/3.32 | 3.35/3.58 | 3.60/3.48 | 1.00 |
| 15 | Otterize | 3.27/3.45 | 3.28/3.32 | 3.35/3.28 | 3.35/3.28 | 1.00 |
| 15 | IG trace_tcp | 3.24/3.37 | 3.29/3.35 | 3.28/3.34 | 3.33/3.37 | 1.00 |
| 15 | IG snapshot_socket | 3.36/3.25 | 3.36/3.24 | 3.45/3.41 | 3.48/3.46 | 0.99 |
| 16 | baseline | 3.36/3.38 | 3.31/3.30 | 3.27/3.29 | 3.23/3.33 | 1.00 |
| 16 | Hubble | 3.55/3.32 | 3.27/3.28 | 3.21/3.38 | 3.27/3.61 | 0.99 |
| 16 | Otterize | 3.28/3.29 | 3.32/3.31 | 3.37/3.36 | 3.43/3.26 | 1.00 |
| 16 | IG trace_tcp | 3.31/3.40 | 3.36/3.40 | 3.36/3.45 | 3.41/3.37 | 1.02 |
| 16 | IG snapshot_socket | 3.43/3.30 | 3.41/3.26 | 3.45/3.34 | 3.38/3.31 | 1.01 |
| 17 | baseline | 3.26/3.38 | 3.24/3.37 | 3.29/3.47 | 3.28/3.52 | 1.00 |
| 17 | Hubble | 3.24/3.41 | 3.27/3.30 | 3.35/3.22 | 3.33/3.57 | 0.99 |
| 17 | Otterize | 3.30/3.32 | 3.36/3.32 | 3.62/3.40 | 3.56/3.35 | 1.01 |
| 17 | IG trace_tcp | 3.34/3.40 | 3.33/3.41 | 3.42/3.54 | 3.48/3.46 | 1.02 |
| 17 | IG snapshot_socket | 3.27/3.29 | 3.26/3.36 | 3.45/3.30 | 3.35/3.35 | 1.00 |
| 18 | baseline | 3.29/3.22 | 3.30/3.27 | 3.20/3.25 | 3.35/3.29 | 0.99 |
| 18 | Hubble | 3.27/3.30 | 3.28/3.34 | 3.35/3.32 | 3.52/3.54 | 1.00 |
| 18 | Otterize | 3.40/3.59 | 3.45/3.43 | 3.23/3.49 | 3.18/3.46 | 1.04 |
| 18 | IG trace_tcp | 3.33/3.48 | 3.34/3.35 | 3.18/3.50 | 3.16/3.53 | 1.01 |
| 18 | IG snapshot_socket | 3.36/3.30 | 3.42/3.30 | 3.51/3.58 | 3.55/3.57 | 1.01 |
| 19 | baseline | 3.28/3.29 | 3.29/3.27 | 3.66/3.47 | 3.45/3.35 | 0.99 |
| 19 | Hubble | 3.27/3.32 | 3.28/3.31 | 3.34/3.38 | 3.49/3.38 | 0.99 |
| 19 | Otterize | 3.44/3.37 | 3.28/3.31 | 3.38/3.53 | 3.37/3.46 | 0.99 |
| 19 | IG trace_tcp | 3.39/3.32 | 3.33/3.31 | 3.34/3.31 | 3.37/3.32 | 1.00 |
| 19 | IG snapshot_socket | 3.39/3.32 | 3.43/3.28 | 3.53/3.62 | 3.45/3.46 | 1.01 |
| 20 | baseline | 3.28/3.28 | 3.32/3.34 | 3.44/3.41 | 3.54/3.68 | 1.00 |
| 20 | Hubble | 3.36/3.27 | 3.26/3.33 | 3.35/3.25 | 3.45/3.28 | 0.99 |
| 20 | Otterize | 3.34/3.26 | 3.30/3.28 | 3.38/3.17 | 3.39/3.26 | 0.99 |
| 20 | IG trace_tcp | 3.39/3.29 | 3.40/3.26 | 3.76/3.21 | 3.70/3.25 | 1.01 |
| 20 | IG snapshot_socket | 3.34/3.28 | 3.30/3.27 | 3.50/3.33 | 3.37/3.33 | 0.99 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 67.73 ± 3.51 (n=10) | 67.59 ± 2.15 (n=10) | +0.03% [-4.17, +4.24] (n.s.) (< 4.2% at 95%) | 0.987 | 1.000 |
| keepalive | Otterize | 67.73 ± 3.51 (n=10) | 66.72 ± 2.68 (n=10) | -1.29% [-5.54, +2.96] (n.s.) (< 3.0% at 95%) | 0.510 | 1.000 |
| keepalive | IG trace_tcp | 67.73 ± 3.51 (n=10) | 68.11 ± 1.63 (n=10) | +0.83% [-3.65, +5.32] (n.s.) (< 5.3% at 95%) | 0.685 | 1.000 |
| keepalive | IG snapshot_socket | 67.73 ± 3.51 (n=10) | 68.07 ± 4.01 (n=10) | +0.63% [-3.67, +4.93] (n.s.) (< 4.9% at 95%) | 0.748 | 1.000 |
| newconn | Hubble | 66.81 ± 3.49 (n=10) | 72.23 ± 2.86 (n=10) | +8.37% [+3.43, +13.30] | 0.004 | 0.016 |
| newconn | Otterize | 66.81 ± 3.49 (n=10) | 67.48 ± 3.25 (n=10) | +1.20% [-3.41, +5.82] (n.s.) (< 5.8% at 95%) | 0.569 | 0.587 |
| newconn | IG trace_tcp | 66.81 ± 3.49 (n=10) | 68.21 ± 2.16 (n=10) | +2.36% [-2.42, +7.14] (n.s.) (< 7.1% at 95%) | 0.293 | 0.587 |
| newconn | IG snapshot_socket | 66.81 ± 3.49 (n=10) | 68.84 ± 2.07 (n=10) | +3.23% [-0.47, +6.93] (n.s.) (< 6.9% at 95%) | 0.080 | 0.240 |

## Excluded runs

None.

## Data warnings in used runs

| App | Rep | Condition | Warning |
|---|---|---|---|
| boutique | 11 | baseline | host-speed canary on cp-01 used 2.15% of a core (limit 1.5%) |
| boutique | 11 | baseline | host-speed canary on worker-01 used 2.30% of a core (limit 1.5%) |
| boutique | 11 | baseline | host-speed canary on worker-02 used 2.32% of a core (limit 1.5%) |
| boutique | 11 | hubble | host-speed canary on cp-01 used 2.17% of a core (limit 1.5%) |
| boutique | 11 | hubble | host-speed canary on worker-01 used 2.23% of a core (limit 1.5%) |
| boutique | 11 | hubble | host-speed canary on worker-02 used 2.19% of a core (limit 1.5%) |
| boutique | 11 | hubble | Hubble lost 74 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 11 | otterize | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 11 | otterize | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 11 | otterize | host-speed canary on worker-02 used 2.29% of a core (limit 1.5%) |
| boutique | 11 | ig_tcp | host-speed canary on cp-01 used 2.12% of a core (limit 1.5%) |
| boutique | 11 | ig_tcp | host-speed canary on worker-01 used 2.30% of a core (limit 1.5%) |
| boutique | 11 | ig_tcp | host-speed canary on worker-02 used 2.31% of a core (limit 1.5%) |
| boutique | 11 | ig_snap | host-speed canary on cp-01 used 2.12% of a core (limit 1.5%) |
| boutique | 11 | ig_snap | host-speed canary on worker-01 used 2.31% of a core (limit 1.5%) |
| boutique | 11 | ig_snap | host-speed canary on worker-02 used 2.27% of a core (limit 1.5%) |
| boutique | 12 | baseline | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 12 | baseline | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 12 | baseline | host-speed canary on worker-02 used 2.25% of a core (limit 1.5%) |
| boutique | 12 | hubble | host-speed canary on cp-01 used 2.18% of a core (limit 1.5%) |
| boutique | 12 | hubble | host-speed canary on worker-01 used 2.28% of a core (limit 1.5%) |
| boutique | 12 | hubble | host-speed canary on worker-02 used 2.30% of a core (limit 1.5%) |
| boutique | 12 | hubble | Hubble lost 73 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 12 | otterize | host-speed canary on cp-01 used 2.23% of a core (limit 1.5%) |
| boutique | 12 | otterize | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 12 | otterize | host-speed canary on worker-02 used 2.29% of a core (limit 1.5%) |
| boutique | 12 | ig_tcp | host-speed canary on cp-01 used 2.16% of a core (limit 1.5%) |
| boutique | 12 | ig_tcp | host-speed canary on worker-01 used 2.31% of a core (limit 1.5%) |
| boutique | 12 | ig_tcp | host-speed canary on worker-02 used 2.22% of a core (limit 1.5%) |
| boutique | 12 | ig_snap | host-speed canary on cp-01 used 2.24% of a core (limit 1.5%) |
| boutique | 12 | ig_snap | host-speed canary on worker-01 used 2.32% of a core (limit 1.5%) |
| boutique | 12 | ig_snap | host-speed canary on worker-02 used 2.32% of a core (limit 1.5%) |
| boutique | 13 | baseline | host-speed canary on cp-01 used 2.23% of a core (limit 1.5%) |
| boutique | 13 | baseline | host-speed canary on worker-01 used 2.28% of a core (limit 1.5%) |
| boutique | 13 | baseline | host-speed canary on worker-02 used 2.30% of a core (limit 1.5%) |
| boutique | 13 | hubble | host-speed canary on cp-01 used 2.18% of a core (limit 1.5%) |
| boutique | 13 | hubble | host-speed canary on worker-01 used 2.23% of a core (limit 1.5%) |
| boutique | 13 | hubble | host-speed canary on worker-02 used 2.22% of a core (limit 1.5%) |
| boutique | 13 | hubble | Hubble lost 75 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 13 | otterize | host-speed canary on cp-01 used 2.24% of a core (limit 1.5%) |
| boutique | 13 | otterize | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 13 | otterize | host-speed canary on worker-02 used 2.27% of a core (limit 1.5%) |
| boutique | 13 | ig_tcp | host-speed canary on cp-01 used 2.25% of a core (limit 1.5%) |
| boutique | 13 | ig_tcp | host-speed canary on worker-01 used 2.29% of a core (limit 1.5%) |
| boutique | 13 | ig_tcp | host-speed canary on worker-02 used 2.31% of a core (limit 1.5%) |
| boutique | 13 | ig_snap | host-speed canary on cp-01 used 2.13% of a core (limit 1.5%) |
| boutique | 13 | ig_snap | host-speed canary on worker-01 used 2.24% of a core (limit 1.5%) |
| boutique | 13 | ig_snap | host-speed canary on worker-02 used 2.27% of a core (limit 1.5%) |
| boutique | 14 | baseline | host-speed canary on cp-01 used 2.23% of a core (limit 1.5%) |
| boutique | 14 | baseline | host-speed canary on worker-01 used 2.31% of a core (limit 1.5%) |
| boutique | 14 | baseline | host-speed canary on worker-02 used 2.27% of a core (limit 1.5%) |
| boutique | 14 | hubble | host-speed canary on cp-01 used 2.18% of a core (limit 1.5%) |
| boutique | 14 | hubble | host-speed canary on worker-01 used 2.29% of a core (limit 1.5%) |
| boutique | 14 | hubble | host-speed canary on worker-02 used 2.30% of a core (limit 1.5%) |
| boutique | 14 | hubble | Hubble lost 73 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 14 | otterize | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 14 | otterize | host-speed canary on worker-01 used 2.28% of a core (limit 1.5%) |
| boutique | 14 | otterize | host-speed canary on worker-02 used 2.32% of a core (limit 1.5%) |
| boutique | 14 | ig_tcp | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 14 | ig_tcp | host-speed canary on worker-01 used 2.24% of a core (limit 1.5%) |
| boutique | 14 | ig_tcp | host-speed canary on worker-02 used 2.33% of a core (limit 1.5%) |
| boutique | 14 | ig_snap | host-speed canary on cp-01 used 2.16% of a core (limit 1.5%) |
| boutique | 14 | ig_snap | host-speed canary on worker-01 used 2.29% of a core (limit 1.5%) |
| boutique | 14 | ig_snap | host-speed canary on worker-02 used 2.27% of a core (limit 1.5%) |
| boutique | 15 | baseline | host-speed canary on cp-01 used 2.26% of a core (limit 1.5%) |
| boutique | 15 | baseline | host-speed canary on worker-01 used 2.26% of a core (limit 1.5%) |
| boutique | 15 | baseline | host-speed canary on worker-02 used 2.29% of a core (limit 1.5%) |
| boutique | 15 | hubble | host-speed canary on cp-01 used 2.23% of a core (limit 1.5%) |
| boutique | 15 | hubble | host-speed canary on worker-01 used 2.26% of a core (limit 1.5%) |
| boutique | 15 | hubble | host-speed canary on worker-02 used 2.27% of a core (limit 1.5%) |
| boutique | 15 | hubble | Hubble lost 74 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 15 | otterize | host-speed canary on cp-01 used 2.25% of a core (limit 1.5%) |
| boutique | 15 | otterize | host-speed canary on worker-01 used 2.31% of a core (limit 1.5%) |
| boutique | 15 | otterize | host-speed canary on worker-02 used 2.29% of a core (limit 1.5%) |
| boutique | 15 | ig_tcp | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 15 | ig_tcp | host-speed canary on worker-01 used 2.31% of a core (limit 1.5%) |
| boutique | 15 | ig_tcp | host-speed canary on worker-02 used 2.26% of a core (limit 1.5%) |
| boutique | 15 | ig_snap | host-speed canary on cp-01 used 2.14% of a core (limit 1.5%) |
| boutique | 15 | ig_snap | host-speed canary on worker-01 used 2.25% of a core (limit 1.5%) |
| boutique | 15 | ig_snap | host-speed canary on worker-02 used 2.32% of a core (limit 1.5%) |
| boutique | 16 | baseline | host-speed canary on cp-01 used 2.23% of a core (limit 1.5%) |
| boutique | 16 | baseline | host-speed canary on worker-01 used 2.30% of a core (limit 1.5%) |
| boutique | 16 | baseline | host-speed canary on worker-02 used 2.29% of a core (limit 1.5%) |
| boutique | 16 | hubble | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 16 | hubble | host-speed canary on worker-01 used 2.30% of a core (limit 1.5%) |
| boutique | 16 | hubble | host-speed canary on worker-02 used 2.28% of a core (limit 1.5%) |
| boutique | 16 | hubble | Hubble lost 73 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 16 | otterize | host-speed canary on cp-01 used 2.25% of a core (limit 1.5%) |
| boutique | 16 | otterize | host-speed canary on worker-01 used 2.28% of a core (limit 1.5%) |
| boutique | 16 | otterize | host-speed canary on worker-02 used 2.30% of a core (limit 1.5%) |
| boutique | 16 | ig_tcp | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 16 | ig_tcp | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 16 | ig_tcp | host-speed canary on worker-02 used 2.25% of a core (limit 1.5%) |
| boutique | 16 | ig_snap | host-speed canary on cp-01 used 2.16% of a core (limit 1.5%) |
| boutique | 16 | ig_snap | host-speed canary on worker-01 used 2.22% of a core (limit 1.5%) |
| boutique | 16 | ig_snap | host-speed canary on worker-02 used 2.31% of a core (limit 1.5%) |
| boutique | 17 | baseline | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 17 | baseline | host-speed canary on worker-01 used 2.34% of a core (limit 1.5%) |
| boutique | 17 | baseline | host-speed canary on worker-02 used 2.24% of a core (limit 1.5%) |
| boutique | 17 | hubble | host-speed canary on cp-01 used 2.17% of a core (limit 1.5%) |
| boutique | 17 | hubble | host-speed canary on worker-01 used 2.32% of a core (limit 1.5%) |
| boutique | 17 | hubble | host-speed canary on worker-02 used 2.30% of a core (limit 1.5%) |
| boutique | 17 | hubble | Hubble lost 71 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 17 | otterize | host-speed canary on cp-01 used 2.26% of a core (limit 1.5%) |
| boutique | 17 | otterize | host-speed canary on worker-01 used 2.23% of a core (limit 1.5%) |
| boutique | 17 | otterize | host-speed canary on worker-02 used 2.28% of a core (limit 1.5%) |
| boutique | 17 | ig_tcp | host-speed canary on cp-01 used 2.23% of a core (limit 1.5%) |
| boutique | 17 | ig_tcp | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 17 | ig_tcp | host-speed canary on worker-02 used 2.21% of a core (limit 1.5%) |
| boutique | 17 | ig_snap | host-speed canary on cp-01 used 2.19% of a core (limit 1.5%) |
| boutique | 17 | ig_snap | host-speed canary on worker-01 used 2.30% of a core (limit 1.5%) |
| boutique | 17 | ig_snap | host-speed canary on worker-02 used 2.28% of a core (limit 1.5%) |
| boutique | 18 | baseline | host-speed canary on cp-01 used 2.25% of a core (limit 1.5%) |
| boutique | 18 | baseline | host-speed canary on worker-01 used 2.31% of a core (limit 1.5%) |
| boutique | 18 | baseline | host-speed canary on worker-02 used 2.33% of a core (limit 1.5%) |
| boutique | 18 | hubble | host-speed canary on cp-01 used 2.14% of a core (limit 1.5%) |
| boutique | 18 | hubble | host-speed canary on worker-01 used 2.29% of a core (limit 1.5%) |
| boutique | 18 | hubble | host-speed canary on worker-02 used 2.26% of a core (limit 1.5%) |
| boutique | 18 | hubble | Hubble lost 72 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 18 | otterize | host-speed canary on cp-01 used 2.19% of a core (limit 1.5%) |
| boutique | 18 | otterize | host-speed canary on worker-01 used 2.26% of a core (limit 1.5%) |
| boutique | 18 | otterize | host-speed canary on worker-02 used 2.21% of a core (limit 1.5%) |
| boutique | 18 | otterize | steal 1.91% is more than twice the app median (0.04%) |
| boutique | 18 | ig_tcp | host-speed canary on cp-01 used 2.08% of a core (limit 1.5%) |
| boutique | 18 | ig_tcp | host-speed canary on worker-01 used 2.31% of a core (limit 1.5%) |
| boutique | 18 | ig_tcp | host-speed canary on worker-02 used 2.22% of a core (limit 1.5%) |
| boutique | 18 | ig_snap | host-speed canary on cp-01 used 2.25% of a core (limit 1.5%) |
| boutique | 18 | ig_snap | host-speed canary on worker-01 used 2.21% of a core (limit 1.5%) |
| boutique | 18 | ig_snap | host-speed canary on worker-02 used 2.27% of a core (limit 1.5%) |
| boutique | 19 | baseline | host-speed canary on cp-01 used 2.24% of a core (limit 1.5%) |
| boutique | 19 | baseline | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 19 | baseline | host-speed canary on worker-02 used 2.31% of a core (limit 1.5%) |
| boutique | 19 | hubble | host-speed canary on cp-01 used 2.19% of a core (limit 1.5%) |
| boutique | 19 | hubble | host-speed canary on worker-01 used 2.29% of a core (limit 1.5%) |
| boutique | 19 | hubble | host-speed canary on worker-02 used 2.28% of a core (limit 1.5%) |
| boutique | 19 | hubble | Hubble lost 72 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 19 | otterize | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 19 | otterize | host-speed canary on worker-01 used 2.28% of a core (limit 1.5%) |
| boutique | 19 | otterize | host-speed canary on worker-02 used 2.26% of a core (limit 1.5%) |
| boutique | 19 | ig_tcp | host-speed canary on cp-01 used 2.23% of a core (limit 1.5%) |
| boutique | 19 | ig_tcp | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 19 | ig_tcp | host-speed canary on worker-02 used 2.29% of a core (limit 1.5%) |
| boutique | 19 | ig_snap | host-speed canary on cp-01 used 2.21% of a core (limit 1.5%) |
| boutique | 19 | ig_snap | host-speed canary on worker-01 used 2.22% of a core (limit 1.5%) |
| boutique | 19 | ig_snap | host-speed canary on worker-02 used 2.26% of a core (limit 1.5%) |
| boutique | 20 | baseline | host-speed canary on cp-01 used 2.22% of a core (limit 1.5%) |
| boutique | 20 | baseline | host-speed canary on worker-01 used 2.27% of a core (limit 1.5%) |
| boutique | 20 | baseline | host-speed canary on worker-02 used 2.26% of a core (limit 1.5%) |
| boutique | 20 | hubble | host-speed canary on cp-01 used 2.19% of a core (limit 1.5%) |
| boutique | 20 | hubble | host-speed canary on worker-01 used 2.31% of a core (limit 1.5%) |
| boutique | 20 | hubble | host-speed canary on worker-02 used 2.30% of a core (limit 1.5%) |
| boutique | 20 | hubble | Hubble lost 74 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 20 | otterize | host-speed canary on cp-01 used 2.29% of a core (limit 1.5%) |
| boutique | 20 | otterize | host-speed canary on worker-01 used 2.29% of a core (limit 1.5%) |
| boutique | 20 | otterize | host-speed canary on worker-02 used 2.33% of a core (limit 1.5%) |
| boutique | 20 | ig_tcp | host-speed canary on cp-01 used 2.18% of a core (limit 1.5%) |
| boutique | 20 | ig_tcp | host-speed canary on worker-01 used 2.20% of a core (limit 1.5%) |
| boutique | 20 | ig_tcp | host-speed canary on worker-02 used 2.33% of a core (limit 1.5%) |
| boutique | 20 | ig_snap | host-speed canary on cp-01 used 2.21% of a core (limit 1.5%) |
| boutique | 20 | ig_snap | host-speed canary on worker-01 used 2.29% of a core (limit 1.5%) |
| boutique | 20 | ig_snap | host-speed canary on worker-02 used 2.30% of a core (limit 1.5%) |

## Method notes

- Observer CPU and memory include cilium-agent, cilium-envoy and cilium-operator in every condition, so the baseline row is not zero. The Δ columns are the cost of the technique.
- Cluster busy CPU comes from /proc/stat on each node (user + nice + system + irq + softirq; steal and iowait left out). It also catches indirect costs: API-server and kubelet work for `kubectl port-forward` and `kubectl gadget` streams, exec probes of the gadget DaemonSet, and BPF work in the app's syscalls or in softirq. The kernel here has CONFIG_IRQ_TIME_ACCOUNTING off, so softirq time is charged to whatever task it interrupts.
- The fixed-count time is the tool's own total (hey `Total`), so pod start-up is not in it.
- The steady-window per-flow cost is not reported: the journey-A load keeps connections open, so almost every new connection in the window is a kubelet probe. Per-request and per-connection costs come from the fixed-count tests.
- Events/s for Hubble and IG count client events whose event time falls inside the analysis window (client_bins.json), so both use the same window and the app namespace only.
- The projection is an estimate with two known gaps: no platform background traffic, and a different CPU model and kernel (6.12 here, 6.8 on test-cluster).
- Host-speed canary (bin/canary.py): every 2 s each node runs a fixed pure-Python integer loop and logs its thread CPU time. Iterations per CPU-second is the host speed index; it falls when the hypervisor gives the guest less work per CPU-second (unreported steal, a busy sibling thread, a lower clock). Normalised CPU = cores x speed / the app's median speed (per node); normalised fixed-count time = time x the workers' speed ratio during the test. The canary costs about 1% of one core per node and is counted as harness.
