# Capture overhead: interleaved cycles (randomized multiple interleaved trials)

Generated 2026-10-05 18:02 UTC by analyze/analyze.py from `teastore-b2-final/results`. 50 run directories, 50 used, 0 excluded.

## Setup

- Cluster: iximiuz play, k3s, Cilium 1.19.5 configured like test-cluster. cp-01 has 2 vCPU and runs the load generator and the capture clients. worker-01 and worker-02 have 4 vCPU each and run the app.
- Conditions: baseline (Cilium, Hubble off, no other observer), Hubble (agent Hubble on, Relay, `hubble observe` through `kubectl port-forward` as in the thesis), Otterize (mapper and sniffers), IG trace_tcp (gadget DaemonSet and a streaming client), IG snapshot_socket (gadget DaemonSet and one snapshot near the end of the window). A metrics scraper fetches :9962, :9963 and :9965 every 15 s in every condition, like test-cluster' Prometheus.
- Each run: fresh Cilium agents and app pods, a 60 s idle segment (observer on, no load), 60 s warm-up, a 300 s steady window with the thesis journey-A load, then the fixed-count tests (9152 requests, concurrency 16, 1 repeats per mode, keep-alive and new connection per request).
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
| Hubble | node-bound | teastore +0.031 | teastore +0.50% | teastore +5.4% n.s. | teastore +25.7% | teastore +0.14% |
| Otterize | node-bound | teastore +0.055 | teastore +0.58% | teastore -0.3% n.s. | teastore -0.1% n.s. | teastore +0.44% |
| IG trace_tcp | node-bound | teastore +0.081 | teastore +1.17% | teastore +2.4% n.s. | teastore +4.7% n.s. | teastore +0.83% |
| IG snapshot_socket | node-bound | teastore +0.074 | teastore +1.04% | teastore -7.1% n.s. | teastore -7.1% n.s. | teastore +0.78% |

Diagnostic only, do not quote: the same, canary-normalised (each run scaled to the app's median canary speed). The 2026-10-03 validation showed the canary does not track the host drift (r 0.41, normalised CV 16.4% vs 16.6% raw) and inflates deltas 1.7-4.7x. The raw paired deltas above, over interleaved cycles, are the result.

| Technique | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn |
|---|---|---|---|---|
| Hubble | teastore +0.029 | teastore +0.39% | teastore +3.0% n.s. | teastore +20.2% |
| Otterize | teastore +0.053 | teastore +0.53% | teastore -1.0% n.s. | teastore -1.4% n.s. |
| IG trace_tcp | teastore +0.078 | teastore +1.09% | teastore +1.0% n.s. | teastore +1.7% n.s. |
| IG snapshot_socket | teastore +0.071 | teastore +0.99% | teastore -8.5% n.s. | teastore -10.3% n.s. |

## teastore

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.050 [+0.037, +0.064] | <0.001 | <0.001 | +0.039 [+0.020, +0.058] | 0.001 | 0.001 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.058 [+0.023, +0.093] | 0.005 | 0.005 | +0.053 [+0.037, +0.069] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.117 [+0.077, +0.158] | <0.001 | <0.001 | +0.109 [+0.091, +0.127] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.104 [+0.067, +0.142] | <0.001 | <0.001 | +0.099 [+0.069, +0.128] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Hubble | +0.031 [+0.026, +0.035] | <0.001 | <0.001 | +0.029 [+0.025, +0.033] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.055 [+0.047, +0.062] | <0.001 | <0.001 | +0.053 [+0.048, +0.057] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.081 [+0.072, +0.090] | <0.001 | <0.001 | +0.078 [+0.073, +0.084] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.074 [+0.067, +0.081] | <0.001 | <0.001 | +0.071 [+0.067, +0.076] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | +0.006 [+0.002, +0.010] | 0.012 | 0.048 | -0.001 [-0.012, +0.009] (n.s.) | 0.812 | 1.000 | 10 |
| Δ app CPU (cores) | Otterize | +0.002 [-0.019, +0.023] (n.s.) | 0.811 | 1.000 | -0.000 [-0.010, +0.010] (n.s.) | 0.999 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | +0.008 [-0.014, +0.030] (n.s.) | 0.442 | 1.000 | +0.004 [-0.006, +0.015] (n.s.) | 0.406 | 1.000 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | +0.009 [-0.018, +0.036] (n.s.) | 0.480 | 1.000 | +0.006 [-0.019, +0.030] (n.s.) | 0.600 | 1.000 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.018 [+0.015, +0.021] | <0.001 | <0.001 | +0.016 [+0.013, +0.019] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.006 [-0.002, +0.014] (n.s.) | 0.123 | 0.123 | +0.005 [+0.001, +0.009] | 0.014 | 0.014 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.036 [+0.027, +0.044] | <0.001 | <0.001 | +0.034 [+0.030, +0.038] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.025 [+0.019, +0.031] | <0.001 | <0.001 | +0.024 [+0.021, +0.028] | <0.001 | <0.001 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +87 [+85, +90] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +81 [+77, +85] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +137 [+133, +142] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +111 [+108, +114] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +89 [+80, +97] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +80 [+70, +91] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +143 [+120, +167] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +132 [+109, +154] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | +5.4% [-3.5, +14.4] (n.s.) | 0.203 | 0.704 | +3.0% [-6.5, +12.5] (n.s.) | 0.499 | 1.000 | 10 |
| fixed-count time, keep-alive | Otterize | -0.3% [-6.2, +5.6] (n.s.) | 0.915 | 0.915 | -1.0% [-9.3, +7.3] (n.s.) | 0.785 | 1.000 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | +2.4% [-3.7, +8.5] (n.s.) | 0.400 | 0.800 | +1.0% [-6.6, +8.5] (n.s.) | 0.782 | 1.000 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | -7.1% [-18.1, +3.9] (n.s.) | 0.176 | 0.704 | -8.5% [-20.1, +3.0] (n.s.) | 0.129 | 0.518 | 10 |
| fixed-count time, new conn | Hubble | +25.7% [+15.9, +35.5] | <0.001 | <0.001 | +20.2% [+8.9, +31.4] | 0.003 | 0.011 | 10 |
| fixed-count time, new conn | Otterize | -0.1% [-5.8, +5.5] (n.s.) | 0.960 | 0.960 | -1.4% [-8.8, +6.1] (n.s.) | 0.686 | 1.000 | 10 |
| fixed-count time, new conn | IG trace_tcp | +4.7% [-1.6, +10.9] (n.s.) | 0.125 | 0.374 | +1.7% [-6.8, +10.2] (n.s.) | 0.655 | 1.000 | 10 |
| fixed-count time, new conn | IG snapshot_socket | -7.1% [-17.7, +3.5] (n.s.) | 0.166 | 0.374 | -10.3% [-22.0, +1.5] (n.s.) | 0.079 | 0.238 | 10 |
| canary speed, workers, steady window (check) | Hubble | -2.38% [-4.99, +0.23] (n.s.) | 0.069 | 0.276 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | -0.79% [-5.03, +3.45] (n.s.) | 0.683 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | -1.37% [-5.94, +3.20] (n.s.) | 0.515 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | -1.71% [-6.00, +2.58] (n.s.) | 0.391 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 8.3% raw, 10.9% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.22; new conn: CV of the baseline time across cycles 8.0% raw, 11.5% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.35.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 10-05 03:53 | baseline hubble ig_snap otterize ig_tcp | 51.1 | 52.5 | 51.0 | 53.5 | 0.248 | 0.266 | 16.59 | 1.06 | 14.98 |
| 12 | 10-05 04:54 | ig_snap baseline ig_tcp hubble otterize | 43.0 | 38.0 | 43.3 | 38.0 | 0.309 | 0.282 | 14.20 | 0.91 | 13.97 |
| 13 | 10-05 05:55 | ig_snap ig_tcp baseline otterize hubble | 46.5 | 41.2 | 46.2 | 40.3 | 0.320 | 0.289 | 14.16 | 0.91 | 14.06 |
| 14 | 10-05 06:56 | hubble baseline otterize ig_snap ig_tcp | 52.2 | 46.2 | 52.4 | 47.6 | 0.316 | 0.291 | 14.38 | 0.92 | 15.10 |
| 15 | 10-05 07:58 | baseline ig_snap hubble ig_tcp otterize | 49.3 | 48.0 | 49.0 | 46.5 | 0.264 | 0.264 | 15.53 | 1.00 | 15.59 |
| 16 | 10-05 08:58 | ig_tcp ig_snap otterize baseline hubble | 54.3 | 53.2 | 54.2 | 53.4 | 0.262 | 0.266 | 15.76 | 1.01 | 15.26 |
| 17 | 10-05 10:01 | otterize hubble ig_tcp baseline ig_snap | 44.8 | 44.5 | 45.2 | 45.0 | 0.268 | 0.273 | 15.88 | 1.02 | 15.56 |
| 18 | 10-05 11:02 | otterize ig_tcp hubble ig_snap baseline | 45.6 | 46.0 | 45.5 | 45.5 | 0.260 | 0.271 | 16.25 | 1.04 | 16.02 |
| 19 | 10-05 12:02 | ig_tcp otterize ig_snap hubble baseline | 50.3 | 51.0 | 50.6 | 51.6 | 0.256 | 0.266 | 16.16 | 1.04 | 15.91 |
| 20 | 10-05 13:03 | hubble otterize baseline ig_tcp ig_snap | 54.7 | 52.7 | 54.4 | 52.5 | 0.266 | 0.262 | 15.37 | 0.99 | 15.71 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 11 baseline; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.031 [+0.026, +0.035] | <0.001 | +0.028 | 0.002 | +0.031 [+0.026, +0.036] | 9 | robust |
| Δ observer CPU | Otterize | +0.055 [+0.047, +0.062] | <0.001 | +0.053 | 0.002 | +0.052 [+0.047, +0.057] | 9 | robust |
| Δ observer CPU | IG trace_tcp | +0.081 [+0.072, +0.090] | <0.001 | +0.079 | 0.002 | +0.078 [+0.071, +0.085] | 9 | robust |
| Δ observer CPU | IG snapshot_socket | +0.074 [+0.067, +0.081] | <0.001 | +0.071 | 0.002 | +0.074 [+0.066, +0.082] | 9 | robust |
| Δ observer anon memory | Hubble | +87 [+85, +90] | <0.001 | +86 | 0.002 | +87 [+85, +90] | 9 | robust |
| Δ observer anon memory | Otterize | +81 [+77, +85] | <0.001 | +82 | 0.002 | +81 [+76, +85] | 9 | robust |
| Δ observer anon memory | IG trace_tcp | +137 [+133, +142] | <0.001 | +136 | 0.002 | +136 [+132, +139] | 9 | robust |
| Δ observer anon memory | IG snapshot_socket | +111 [+108, +114] | <0.001 | +109 | 0.002 | +110 [+107, +113] | 9 | robust |
| fixed-count time, keep-alive | Hubble | +5.4% [-3.5, +14.4] (n.s.) | 0.997 | +2.9% | 0.322 | +6.3% [-3.6, +16.3] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | Otterize | -0.3% [-6.2, +5.6] (n.s.) | 1.000 | -1.0% | 1.000 | +0.5% [-5.9, +6.9] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | IG trace_tcp | +2.4% [-3.7, +8.5] (n.s.) | 1.000 | +5.6% | 0.375 | +3.4% [-3.2, +9.9] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | IG snapshot_socket | -7.1% [-18.1, +3.9] (n.s.) | 0.997 | -6.5% | 0.160 | -6.5% [-18.9, +5.9] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +25.7% [+15.9, +35.5] | 0.002 | +22.8% | 0.002 | +26.6% [+15.7, +37.5] | 9 | robust |
| fixed-count time, new conn | Otterize | -0.1% [-5.8, +5.5] (n.s.) | 1.000 | -0.5% | 1.000 | +0.7% [-5.4, +6.8] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | +4.7% [-1.6, +10.9] (n.s.) | 0.873 | +7.9% | 0.160 | +5.7% [-1.0, +12.3] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG snapshot_socket | -7.1% [-17.7, +3.5] (n.s.) | 0.997 | -5.6% | 0.160 | -6.5% [-18.5, +5.5] (n.s.) | 9 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 9152 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **node-bound** (baseline newconn bottleneck throttled 0.00 s/s), so node CPU limits the test. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 49.19 ± 4.07 (n=10) | 51.49 ± 3.48 (n=10) | +5.43% [-3.51, +14.38] (n.s.) (< 14.4% at 95%) | 0.203 | 0.997 | teastore-image 0.00 | 0.18 |
| keepalive | Otterize | 49.19 ± 4.07 (n=10) | 48.83 ± 3.07 (n=10) | -0.29% [-6.19, +5.61] (n.s.) (< 5.6% at 95%) | 0.915 | 1.000 | teastore-persistence 0.00 | 0.18 |
| keepalive | IG trace_tcp | 49.19 ± 4.07 (n=10) | 50.11 ± 2.74 (n=10) | +2.39% [-3.73, +8.50] (n.s.) (< 8.5% at 95%) | 0.400 | 1.000 | teastore-persistence 0.00 | 0.18 |
| keepalive | IG snapshot_socket | 49.19 ± 4.07 (n=10) | 45.63 ± 7.68 (n=10) | -7.12% [-18.10, +3.85] (n.s.) (< 3.9% at 95%) | 0.176 | 0.997 | teastore-auth 0.00 | 0.22 |
| newconn | Hubble | 49.18 ± 3.95 (n=10) | 61.40 ± 3.59 (n=10) | +25.68% [+15.89, +35.46] | <0.001 | 0.002 | teastore-image 0.00 | 1.17 |
| newconn | Otterize | 49.18 ± 3.95 (n=10) | 48.92 ± 3.09 (n=10) | -0.13% [-5.78, +5.52] (n.s.) (< 5.5% at 95%) | 0.960 | 1.000 | teastore-persistence 0.00 | 1.17 |
| newconn | IG trace_tcp | 49.18 ± 3.95 (n=10) | 51.23 ± 2.84 (n=10) | +4.68% [-1.57, +10.93] (n.s.) (< 10.9% at 95%) | 0.125 | 0.873 | teastore-persistence 0.00 | 1.17 |
| newconn | IG snapshot_socket | 49.18 ± 3.95 (n=10) | 45.67 ± 7.50 (n=10) | -7.07% [-17.68, +3.55] (n.s.) (< 3.5% at 95%) | 0.166 | 0.997 | teastore-auth 0.00 | 1.21 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 49.19 ± 4.07 | 8.27% | 8.27% | 10 |
| newconn | 49.18 ± 3.95 | 8.03% | 8.03% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.047 ± 0.009 | 0.004 | - | 0.447 ± 0.044 | 0.061 | - | - | - | - |
| Hubble | 0.077 ± 0.014 | 0.007 | +0.031 [+0.026, +0.035] | 0.498 ± 0.057 | 0.058 | +0.050 [+0.037, +0.064] | +0.50% | +0.018 | <0.001 / <0.001 |
| Otterize | 0.101 ± 0.011 | 0.005 | +0.055 [+0.047, +0.062] | 0.506 ± 0.048 | 0.062 | +0.058 [+0.023, +0.093] | +0.58% | +0.006 | <0.001 / <0.001 |
| IG trace_tcp | 0.128 ± 0.014 | 0.008 | +0.081 [+0.072, +0.090] | 0.565 ± 0.056 | 0.065 | +0.117 [+0.077, +0.158] | +1.17% | +0.036 | <0.001 / <0.001 |
| IG snapshot_socket | 0.120 ± 0.014 | 0.009 | +0.074 [+0.067, +0.081] | 0.552 ± 0.055 | 0.067 | +0.104 [+0.067, +0.142] | +1.04% | +0.025 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.006 [+0.004, +0.009] | +0.000 [-0.002, +0.002] (n.s.) | -0.008 [-0.019, +0.004] (n.s.) | 20% |
| Otterize | +0.052 [+0.043, +0.060] | +0.009 [-0.000, +0.018] (n.s.) | +0.043 [+0.017, +0.068] | 94% |
| IG trace_tcp | +0.074 [+0.064, +0.084] | +0.024 [+0.014, +0.033] | +0.085 [+0.057, +0.113] | 91% |
| IG snapshot_socket | +0.069 [+0.063, +0.075] | +0.020 [+0.015, +0.025] | +0.073 [+0.053, +0.093] | 94% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.167 [+0.139, +0.195] | +0.270 [+0.128, +0.412] | +0.108 [+0.096, +0.121] | 0.00 → 0.00 | 14% |
| keepalive | Otterize | +0.072 [+0.059, +0.085] | +0.128 [-0.090, +0.345] (n.s.) | +0.008 [-0.004, +0.020] (n.s.) | 0.00 → 0.00 | 10% |
| keepalive | IG trace_tcp | +0.127 [+0.114, +0.140] | +0.231 [+0.062, +0.400] | +0.115 [+0.101, +0.129] | 0.00 → 0.00 | 14% |
| keepalive | IG snapshot_socket | +0.078 [+0.071, +0.085] | +0.390 [-0.214, +0.995] (n.s.) | +0.038 [+0.006, +0.071] | 0.00 → 0.00 | 11% |
| newconn | Hubble | +0.633 [+0.558, +0.708] | +0.706 [+0.552, +0.861] | +0.282 [+0.255, +0.309] | 0.00 → 0.00 | 31% |
| newconn | Otterize | +0.104 [+0.093, +0.115] | +0.176 [+0.035, +0.317] | +0.009 [+0.003, +0.016] | 0.00 → 0.00 | 14% |
| newconn | IG trace_tcp | +0.245 [+0.221, +0.270] | +0.561 [+0.423, +0.700] | +0.283 [+0.254, +0.311] | 0.00 → 0.00 | 26% |
| newconn | IG snapshot_socket | +0.080 [+0.073, +0.087] | +0.486 [-0.133, +1.105] (n.s.) | +0.045 [+0.013, +0.077] | 0.00 → 0.00 | 16% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 667 ± 48 | 3.1 | 2.20 | 368 | - | - | 5663 ± 136 | - | - |
| Hubble | 756 ± 39 (peak 775) | 13.9 | 10.15 | 455 | +87 [+85, +90] | +89 [+80, +97] | 5757 ± 94 | +0.55% | <0.001 / <0.001 |
| Otterize | 747 ± 47 (peak 751) | 2.8 | 1.82 | 449 | +81 [+77, +85] | +80 [+70, +91] | 5792 ± 143 | +0.51% | <0.001 / <0.001 |
| IG trace_tcp | 810 ± 19 (peak 822) | 5.1 | -1.74 | 505 | +137 [+133, +142] | +143 [+120, +167] | 5870 ± 160 | +0.86% | <0.001 / <0.001 |
| IG snapshot_socket | 799 ± 73 (peak 851) | 16.6 | 7.19 | 478 | +111 [+108, +114] | +132 [+109, +154] | 5908 ± 142 | +0.69% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.038 | 0.053 | 0.039 | 0.040 | 0.039 |
| cilium-envoy | 0.006 | 0.006 | 0.006 | 0.006 | 0.006 |
| cilium-operator | 0.002 | 0.002 | 0.002 | 0.002 | 0.002 |
| hubble-relay | 0.000 | 0.007 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.004 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.050 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.077 | 0.072 |
| client-hubble | 0.000 | 0.009 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.002 | 0.000 |
| app | 0.277 | 0.283 | 0.279 | 0.285 | 0.286 |
| loadgen | 0.018 | 0.019 | 0.019 | 0.019 | 0.018 |
| k3s | 0.083 | 0.101 | 0.089 | 0.119 | 0.108 |
| k8s-addons | 0.003 | 0.003 | 0.004 | 0.003 | 0.003 |
| os | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 |
| harness | 0.020 | 0.021 | 0.021 | 0.021 | 0.021 |
| node | 0.447 | 0.498 | 0.506 | 0.565 | 0.552 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 10.85 ± 0.09 | 9.9 ± 1.1 | - | 27.3 ± 3.3 | - | 32.4 ± 4.6 | - | 6.72 |
| Hubble | 10.93 ± 0.14 | 10.3 ± 1.5 | +3.8% [+0.3, +7.3] | 29.1 ± 5.3 | +6.2% [-0.3, +12.7] (n.s.) | 34.5 ± 7.2 | +6.1% [-2.2, +14.5] (n.s.) | 6.74 |
| Otterize | 10.90 ± 0.11 | 9.9 ± 1.1 | +0.5% [-7.2, +8.2] (n.s.) | 27.8 ± 3.2 | +2.5% [-6.2, +11.2] (n.s.) | 33.2 ± 4.6 | +3.7% [-8.2, +15.5] (n.s.) | 7.44 |
| IG trace_tcp | 10.85 ± 0.12 | 10.4 ± 1.2 | +5.7% [-3.3, +14.7] (n.s.) | 29.0 ± 3.3 | +7.1% [-2.7, +16.8] (n.s.) | 35.6 ± 4.9 | +11.3% [-1.8, +24.3] (n.s.) | 7.06 |
| IG snapshot_socket | 10.95 ± 0.11 | 10.9 ± 3.4 | +11.4% [-17.3, +40.2] (n.s.) | 29.0 ± 4.8 | +7.0% [-6.5, +20.5] (n.s.) | 37.0 ± 8.2 | +15.5% [-4.4, +35.4] (n.s.) | 6.87 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 3.0 | 0.07 | 2.91 | - | - | - | - | - |
| Hubble | 3.2 | 0.26 | 2.96 | +934 [+771, +1097] | +4345 [+3838, +4852] | +3708 [+3275, +4141] | +5850 [+4954, +6745] | 39.6 (thesis 44.7) |
| Otterize | 4.4 | 1.07 | 3.31 | +114 [+84, +145] | +292 [+268, +316] | +249 [+229, +269] | +585 [+146, +1024] | - |
| IG trace_tcp | 3.0 | 0.06 | 2.93 | +305 [+286, +324] | +996 [+871, +1121] | +850 [+743, +956] | +2621 [+2175, +3067] | 12.0 (thesis 15.7) |
| IG snapshot_socket | 2.9 | 0.06 | 2.88 | +46 [+25, +68] | +55 [+27, +82] | +44 [+23, +65] | +994 [-1094, +3083] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 32%. Lost events: 0 in the window, 89 over the whole run (fixed-count tests included). hubble_* series at the end: 262.

| Class | flows/s | share |
|---|---|---|
| app | 39.9 | 73% |
| probe | 0.3 | 1% |
| client_feedback | 2.7 | 5% |
| other | 11.6 | 21% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.074 [+0.067, +0.081] cores. Standing (window before the snapshot) minus baseline observer: +0.073 cores; one snapshot adds 0.35 ± 0.12 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.254 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.025 [+0.020, +0.030] | +0.033 | +0.032 [+0.015, +0.050] | +0.14% / +0.18% | +25 [-16, +66] (n.s.) | +0.04% |
| Otterize | +0.079 [+0.064, +0.093] | +0.080 | +0.079 [+0.028, +0.131] | +0.44% / +0.44% | +79 [+31, +128] | +0.14% |
| IG trace_tcp | +0.150 [+0.132, +0.168] | +0.154 | +0.202 [+0.137, +0.266] | +0.83% / +1.12% | +276 [+201, +352] | +0.47% |
| IG snapshot_socket | +0.140 [+0.128, +0.152] | +0.144 | +0.180 [+0.139, +0.221] | +0.78% / +1.00% | +278 [+234, +323] | +0.48% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 11 | baseline | 1 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 51.02 |
| 12 | baseline | 2 | 0.20% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 43.30 |
| 13 | baseline | 3 | 0.15% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 46.21 |
| 14 | baseline | 2 | 0.17% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 52.42 |
| 15 | baseline | 1 | 0.04% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 49.03 |
| 16 | baseline | 4 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 54.17 |
| 17 | baseline | 4 | 0.07% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 45.20 |
| 18 | baseline | 5 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 45.51 |
| 19 | baseline | 5 | 0.12% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 50.57 |
| 20 | baseline | 3 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 54.37 |
| 11 | Hubble | 2 | 0.01% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 59.97 |
| 12 | Hubble | 4 | 0.17% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 64.19 |
| 13 | Hubble | 5 | 0.18% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 64.01 |
| 14 | Hubble | 1 | 0.16% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 55.78 |
| 15 | Hubble | 3 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 63.20 |
| 16 | Hubble | 5 | 0.08% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 62.71 |
| 17 | Hubble | 2 | 0.01% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 56.87 |
| 18 | Hubble | 3 | 0.11% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 64.79 |
| 19 | Hubble | 4 | 0.04% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 57.33 |
| 20 | Hubble | 1 | 0.01% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 65.15 |
| 11 | Otterize | 4 | 0.12% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 47.33 |
| 12 | Otterize | 5 | 0.14% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 47.76 |
| 13 | Otterize | 4 | 0.14% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 48.07 |
| 14 | Otterize | 3 | 0.01% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 48.24 |
| 15 | Otterize | 5 | 0.04% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 48.05 |
| 16 | Otterize | 3 | 0.02% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 54.59 |
| 17 | Otterize | 1 | 0.19% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 49.95 |
| 18 | Otterize | 1 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 47.93 |
| 19 | Otterize | 2 | 0.01% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 43.84 |
| 20 | Otterize | 2 | 0.01% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 53.43 |
| 11 | IG trace_tcp | 5 | 0.15% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 48.88 |
| 12 | IG trace_tcp | 3 | 0.17% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 50.49 |
| 13 | IG trace_tcp | 2 | 0.21% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 50.04 |
| 14 | IG trace_tcp | 5 | 0.15% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 52.85 |
| 15 | IG trace_tcp | 4 | 0.28% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 55.89 |
| 16 | IG trace_tcp | 1 | 0.04% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 47.87 |
| 17 | IG trace_tcp | 3 | 0.66% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 48.64 |
| 18 | IG trace_tcp | 2 | 0.18% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 49.31 |
| 19 | IG trace_tcp | 1 | 0.25% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 55.11 |
| 20 | IG trace_tcp | 4 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 53.28 |
| 11 | IG snapshot_socket | 3 | 0.02% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 44.93 |
| 12 | IG snapshot_socket | 1 | 0.39% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 47.39 |
| 13 | IG snapshot_socket | 1 | 0.33% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 47.34 |
| 14 | IG snapshot_socket | 4 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 45.95 |
| 15 | IG snapshot_socket | 2 | 0.06% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 46.24 |
| 16 | IG snapshot_socket | 2 | 0.61% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 51.22 |
| 17 | IG snapshot_socket | 5 | 0.09% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 46.48 |
| 18 | IG snapshot_socket | 4 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 25.34 |
| 19 | IG snapshot_socket | 3 | 0.03% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 51.42 |
| 20 | IG snapshot_socket | 5 | 0.12% | 6ac31e5d94d679d21b1d95be | 0c18850a,3f7bbfbd,9df48518 | 50.37 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 11 | baseline | 16.72/16.73 | 16.52/16.66 | 15.83/16.16 | 16.20/16.45 | 1.06 |
| 11 | Hubble | 15.85/16.44 | 15.90/15.72 | 15.09/15.46 | 15.37/14.99 | 1.01 |
| 11 | Otterize | 14.42/13.87 | 14.53/14.08 | 12.88/12.96 | 13.62/13.44 | 0.92 |
| 11 | IG trace_tcp | 13.56/14.77 | 13.74/14.31 | 13.46/14.26 | 13.18/13.93 | 0.90 |
| 11 | IG snapshot_socket | 12.16/15.97 | 11.96/16.35 | 11.28/15.87 | 11.20/15.03 | 0.91 |
| 12 | baseline | 14.72/14.26 | 14.26/14.14 | 13.80/13.69 | 13.50/13.82 | 0.91 |
| 12 | Hubble | 14.16/14.03 | 14.01/13.83 | 13.77/13.21 | 13.25/13.14 | 0.89 |
| 12 | Otterize | 14.21/14.86 | 13.72/14.43 | 13.34/14.36 | 12.93/14.26 | 0.90 |
| 12 | IG trace_tcp | 13.83/14.12 | 13.87/13.90 | 13.64/12.78 | 13.61/13.38 | 0.89 |
| 12 | IG snapshot_socket | 13.89/13.62 | 14.04/13.47 | 13.79/13.61 | 13.87/12.80 | 0.88 |
| 13 | baseline | 14.21/14.43 | 14.10/14.23 | 13.54/14.11 | 13.74/13.46 | 0.91 |
| 13 | Hubble | 14.40/14.42 | 14.64/13.96 | 13.86/13.14 | 13.54/12.08 | 0.92 |
| 13 | Otterize | 13.16/14.00 | 13.07/14.24 | 12.93/13.99 | 13.01/13.83 | 0.88 |
| 13 | IG trace_tcp | 14.43/14.07 | 14.46/14.05 | 14.07/13.80 | 13.94/13.37 | 0.92 |
| 13 | IG snapshot_socket | 14.21/14.23 | 13.99/13.89 | 13.30/13.55 | 13.51/13.44 | 0.89 |
| 14 | baseline | 14.79/14.19 | 14.58/14.18 | 13.96/13.59 | 14.00/14.27 | 0.92 |
| 14 | Hubble | 14.21/14.13 | 13.94/13.54 | 14.00/13.62 | 13.23/13.51 | 0.88 |
| 14 | Otterize | 16.43/15.84 | 16.04/15.48 | 15.65/14.52 | 16.13/15.01 | 1.01 |
| 14 | IG trace_tcp | 16.36/16.29 | 15.84/15.92 | 15.66/15.47 | 13.69/13.79 | 1.02 |
| 14 | IG snapshot_socket | 15.99/15.71 | 15.64/15.79 | 15.10/15.25 | 15.24/15.62 | 1.01 |
| 15 | baseline | 15.75/15.50 | 15.59/15.47 | 15.02/15.31 | 14.65/14.89 | 1.00 |
| 15 | Hubble | 16.06/15.79 | 16.09/15.30 | 15.84/14.96 | 15.82/14.88 | 1.01 |
| 15 | Otterize | 16.02/15.69 | 15.67/15.87 | 14.79/15.94 | 15.12/15.54 | 1.01 |
| 15 | IG trace_tcp | 16.29/15.52 | 15.94/15.03 | 15.12/14.58 | 15.32/14.94 | 0.99 |
| 15 | IG snapshot_socket | 15.63/15.69 | 15.48/15.47 | 15.60/14.81 | 15.03/14.89 | 0.99 |
| 16 | baseline | 16.11/15.92 | 15.79/15.72 | 15.03/15.46 | 15.59/15.15 | 1.01 |
| 16 | Hubble | 13.59/15.62 | 13.54/15.31 | 12.76/15.17 | 12.72/14.41 | 0.93 |
| 16 | Otterize | 15.33/15.56 | 15.76/15.80 | 15.58/15.45 | 15.34/15.58 | 1.01 |
| 16 | IG trace_tcp | 15.91/14.96 | 15.80/15.05 | 15.31/14.28 | 15.16/14.56 | 0.99 |
| 16 | IG snapshot_socket | 16.13/15.71 | 15.23/14.61 | 15.63/14.52 | 14.53/13.85 | 0.96 |
| 17 | baseline | 16.21/15.80 | 16.05/15.71 | 15.28/15.70 | 15.29/15.71 | 1.02 |
| 17 | Hubble | 15.24/14.96 | 14.91/14.68 | 14.80/13.87 | 14.63/13.81 | 0.95 |
| 17 | Otterize | 16.37/16.03 | 16.26/15.59 | 16.32/15.00 | 15.86/14.72 | 1.02 |
| 17 | IG trace_tcp | 16.06/15.67 | 15.55/15.15 | 15.00/14.89 | 15.30/14.52 | 0.99 |
| 17 | IG snapshot_socket | 16.11/15.83 | 15.83/15.91 | 14.91/15.82 | 15.02/15.95 | 1.02 |
| 18 | baseline | 16.26/15.95 | 16.36/16.13 | 16.07/15.33 | 15.65/15.52 | 1.04 |
| 18 | Hubble | 16.47/15.77 | 16.17/16.05 | 15.70/15.63 | 14.91/15.79 | 1.03 |
| 18 | Otterize | 16.57/15.98 | 15.92/15.54 | 15.62/15.49 | 14.91/15.02 | 1.01 |
| 18 | IG trace_tcp | 16.33/16.38 | 15.92/15.97 | 15.51/14.83 | 15.62/14.93 | 1.02 |
| 18 | IG snapshot_socket | 15.74/16.41 | 15.80/16.31 | 15.49/15.36 | 14.57/14.87 | 1.03 |
| 19 | baseline | 16.27/16.40 | 16.07/16.24 | 15.56/16.05 | 15.84/15.94 | 1.04 |
| 19 | Hubble | 16.09/15.87 | 16.09/15.78 | 15.66/15.26 | 15.82/14.38 | 1.02 |
| 19 | Otterize | 16.26/15.51 | 16.33/15.51 | 16.14/14.62 | 16.16/14.60 | 1.02 |
| 19 | IG trace_tcp | 16.55/15.93 | 16.05/15.49 | 16.07/14.92 | 15.85/14.86 | 1.01 |
| 19 | IG snapshot_socket | 16.55/15.78 | 15.80/15.77 | 14.91/15.37 | 14.37/14.95 | 1.01 |
| 20 | baseline | 16.15/15.14 | 15.46/15.28 | 15.26/14.76 | 15.04/15.08 | 0.99 |
| 20 | Hubble | 16.25/16.10 | 16.06/15.53 | 15.43/14.97 | 15.36/14.50 | 1.01 |
| 20 | Otterize | 16.22/16.08 | 16.05/15.73 | 15.74/15.05 | 15.61/14.57 | 1.02 |
| 20 | IG trace_tcp | 15.69/16.12 | 15.68/15.92 | 15.14/15.86 | 15.02/15.34 | 1.01 |
| 20 | IG snapshot_socket | 16.00/16.31 | 15.65/15.75 | 15.01/15.15 | 14.06/15.35 | 1.01 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 47.33 ± 5.16 (n=10) | 48.29 ± 4.48 (n=10) | +2.96% [-6.53, +12.45] (n.s.) (< 12.5% at 95%) | 0.499 | 1.000 |
| keepalive | Otterize | 47.33 ± 5.16 (n=10) | 46.50 ± 4.94 (n=10) | -1.03% [-9.32, +7.26] (n.s.) (< 7.3% at 95%) | 0.785 | 1.000 |
| keepalive | IG trace_tcp | 47.33 ± 5.16 (n=10) | 47.45 ± 4.46 (n=10) | +0.95% [-6.59, +8.49] (n.s.) (< 8.5% at 95%) | 0.782 | 1.000 |
| keepalive | IG snapshot_socket | 47.33 ± 5.16 (n=10) | 43.05 ± 7.50 (n=10) | -8.52% [-20.06, +3.03] (n.s.) (< 3.0% at 95%) | 0.129 | 0.518 |
| newconn | Hubble | 47.39 ± 5.44 (n=10) | 56.39 ± 5.22 (n=10) | +20.19% [+8.93, +31.45] | 0.003 | 0.011 |
| newconn | Otterize | 47.39 ± 5.44 (n=10) | 46.40 ± 4.53 (n=10) | -1.37% [-8.80, +6.06] (n.s.) (< 6.1% at 95%) | 0.686 | 1.000 |
| newconn | IG trace_tcp | 47.39 ± 5.44 (n=10) | 47.78 ± 4.33 (n=10) | +1.74% [-6.77, +10.25] (n.s.) (< 10.2% at 95%) | 0.655 | 1.000 |
| newconn | IG snapshot_socket | 47.39 ± 5.44 (n=10) | 42.20 ± 7.27 (n=10) | -10.27% [-22.03, +1.48] (n.s.) (< 1.5% at 95%) | 0.079 | 0.238 |

## Excluded runs

None.

## Data warnings in used runs

| App | Rep | Condition | Warning |
|---|---|---|---|
| teastore | 11 | hubble | Hubble lost 86 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 12 | hubble | Hubble lost 89 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 13 | hubble | Hubble lost 117 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 14 | hubble | Hubble lost 83 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 15 | hubble | Hubble lost 87 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 16 | hubble | Hubble lost 88 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 17 | hubble | Hubble lost 84 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 18 | hubble | Hubble lost 87 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 19 | hubble | Hubble lost 84 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 20 | hubble | Hubble lost 89 events during the run (ring buffer), 0 of them in the steady window |

## Method notes

- Observer CPU and memory include cilium-agent, cilium-envoy and cilium-operator in every condition, so the baseline row is not zero. The Δ columns are the cost of the technique.
- Cluster busy CPU comes from /proc/stat on each node (user + nice + system + irq + softirq; steal and iowait left out). It also catches indirect costs: API-server and kubelet work for `kubectl port-forward` and `kubectl gadget` streams, exec probes of the gadget DaemonSet, and BPF work in the app's syscalls or in softirq. The kernel here has CONFIG_IRQ_TIME_ACCOUNTING off, so softirq time is charged to whatever task it interrupts.
- The fixed-count time is the tool's own total (hey `Total`), so pod start-up is not in it.
- The steady-window per-flow cost is not reported: the journey-A load keeps connections open, so almost every new connection in the window is a kubelet probe. Per-request and per-connection costs come from the fixed-count tests.
- Events/s for Hubble and IG count client events whose event time falls inside the analysis window (client_bins.json), so both use the same window and the app namespace only.
- The projection is an estimate with two known gaps: no platform background traffic, and a different CPU model and kernel (6.12 here, 6.8 on test-cluster).
- Host-speed canary (bin/canary.py): every 2 s each node runs a fixed pure-Python integer loop and logs its thread CPU time. Iterations per CPU-second is the host speed index; it falls when the hypervisor gives the guest less work per CPU-second (unreported steal, a busy sibling thread, a lower clock). Normalised CPU = cores x speed / the app's median speed (per node); normalised fixed-count time = time x the workers' speed ratio during the test. The canary costs about 1% of one core per node and is counted as harness.
