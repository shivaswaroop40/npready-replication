# Capture overhead: interleaved cycles (randomized multiple interleaved trials)

Generated 2026-10-05 18:02 UTC by analyze/analyze.py from `boutique-b1-final/results`. 50 run directories, 50 used, 0 excluded.

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
| Hubble | quota-bound | boutique +0.050 | boutique +0.48% | boutique -0.8% n.s. | boutique +5.2% n.s. | boutique +0.23% |
| Otterize | quota-bound | boutique +0.052 | boutique +0.49% | boutique +3.6% n.s. | boutique +3.2% n.s. | boutique +0.43% |
| IG trace_tcp | quota-bound | boutique +0.078 | boutique +1.00% | boutique -5.0% n.s. | boutique +1.7% n.s. | boutique +0.79% |
| IG snapshot_socket | quota-bound | boutique +0.071 | boutique +0.90% | boutique -6.6% n.s. | boutique -0.1% n.s. | boutique +0.74% |

Diagnostic only, do not quote: the same, canary-normalised (each run scaled to the app's median canary speed). The 2026-10-03 validation showed the canary does not track the host drift (r 0.41, normalised CV 16.4% vs 16.6% raw) and inflates deltas 1.7-4.7x. The raw paired deltas above, over interleaved cycles, are the result.

| Technique | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn |
|---|---|---|---|---|
| Hubble | boutique +0.054 | boutique +0.55% | boutique +1.7% n.s. | boutique -1.2% n.s. |
| Otterize | boutique +0.054 | boutique +0.45% | boutique -3.9% n.s. | boutique +3.4% n.s. |
| IG trace_tcp | boutique +0.096 | boutique +1.46% | boutique -3.0% n.s. | boutique +3.5% n.s. |
| IG snapshot_socket | boutique +0.077 | boutique +1.01% | boutique -5.7% n.s. | boutique -2.9% n.s. |

## boutique

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.048 [+0.015, +0.081] | 0.009 | 0.009 | +0.055 [+0.024, +0.086] | 0.003 | 0.006 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.049 [+0.028, +0.070] | <0.001 | <0.001 | +0.045 [+0.020, +0.071] | 0.003 | 0.006 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.100 [+0.083, +0.118] | <0.001 | <0.001 | +0.146 [+0.102, +0.189] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.090 [+0.075, +0.105] | <0.001 | <0.001 | +0.101 [+0.051, +0.151] | 0.001 | 0.004 | 10 |
| Δ observer CPU (cores) | Hubble | +0.050 [+0.041, +0.058] | <0.001 | <0.001 | +0.054 [+0.044, +0.063] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.052 [+0.047, +0.057] | <0.001 | <0.001 | +0.054 [+0.046, +0.062] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.078 [+0.073, +0.082] | <0.001 | <0.001 | +0.096 [+0.083, +0.109] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.071 [+0.064, +0.077] | <0.001 | <0.001 | +0.077 [+0.060, +0.094] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | -0.007 [-0.012, -0.003] | 0.005 | 0.021 | -0.006 [-0.015, +0.003] (n.s.) | 0.165 | 0.659 | 10 |
| Δ app CPU (cores) | Otterize | -0.003 [-0.007, +0.002] (n.s.) | 0.210 | 0.210 | -0.003 [-0.009, +0.004] (n.s.) | 0.401 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | -0.004 [-0.007, -0.001] | 0.021 | 0.063 | -0.001 [-0.009, +0.008] (n.s.) | 0.898 | 1.000 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | -0.004 [-0.007, -0.001] | 0.021 | 0.063 | +0.001 [-0.013, +0.015] (n.s.) | 0.928 | 1.000 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.019 [+0.004, +0.034] | 0.018 | 0.035 | +0.022 [+0.007, +0.038] | 0.011 | 0.028 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.007 [-0.004, +0.018] (n.s.) | 0.205 | 0.205 | +0.003 [-0.013, +0.020] (n.s.) | 0.653 | 0.653 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.039 [+0.029, +0.048] | <0.001 | <0.001 | +0.063 [+0.039, +0.088] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.033 [+0.024, +0.043] | <0.001 | <0.001 | +0.035 [+0.011, +0.059] | 0.009 | 0.028 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +91 [+88, +94] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +79 [+76, +82] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +133 [+128, +137] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +111 [+109, +113] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +104 [+88, +121] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +95 [+75, +114] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +166 [+119, +212] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +119 [+116, +121] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | -0.8% [-14.6, +13.0] (n.s.) | 0.899 | 1.000 | +1.7% [-18.0, +21.3] (n.s.) | 0.853 | 1.000 | 10 |
| fixed-count time, keep-alive | Otterize | +3.6% [-18.3, +25.4] (n.s.) | 0.719 | 1.000 | -3.9% [-17.8, +10.0] (n.s.) | 0.545 | 1.000 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | -5.0% [-22.9, +13.0] (n.s.) | 0.548 | 1.000 | -3.0% [-17.1, +11.2] (n.s.) | 0.645 | 1.000 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | -6.6% [-20.7, +7.5] (n.s.) | 0.315 | 1.000 | -5.7% [-17.4, +6.1] (n.s.) | 0.303 | 1.000 | 10 |
| fixed-count time, new conn | Hubble | +5.2% [-6.7, +17.1] (n.s.) | 0.347 | 1.000 | -1.2% [-12.8, +10.4] (n.s.) | 0.815 | 1.000 | 10 |
| fixed-count time, new conn | Otterize | +3.2% [-19.8, +26.2] (n.s.) | 0.761 | 1.000 | +3.4% [-9.1, +15.9] (n.s.) | 0.556 | 1.000 | 10 |
| fixed-count time, new conn | IG trace_tcp | +1.7% [-12.9, +16.4] (n.s.) | 0.794 | 1.000 | +3.5% [-11.9, +18.8] (n.s.) | 0.623 | 1.000 | 10 |
| fixed-count time, new conn | IG snapshot_socket | -0.1% [-13.5, +13.3] (n.s.) | 0.992 | 1.000 | -2.9% [-14.7, +8.9] (n.s.) | 0.595 | 1.000 | 10 |
| canary speed, workers, steady window (check) | Hubble | +3.50% [-7.33, +14.33] (n.s.) | 0.483 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | +1.00% [-6.13, +8.13] (n.s.) | 0.758 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | +6.61% [-3.80, +17.01] (n.s.) | 0.185 | 0.739 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | +6.24% [-9.37, +21.85] (n.s.) | 0.389 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 21.7% raw, 15.4% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.69; new conn: CV of the baseline time across cycles 17.5% raw, 10.4% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.83.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-03 06:18 | otterize hubble ig_tcp baseline ig_snap | 34.8 | 50.6 | 38.2 | 54.3 | 0.082 | 0.079 | 6.94 | 0.96 | 7.34 |
| 2 | 10-03 07:16 | hubble baseline otterize ig_snap ig_tcp | 45.9 | 59.8 | 45.3 | 51.3 | 0.082 | 0.093 | 7.66 | 1.07 | 8.09 |
| 3 | 10-03 08:16 | ig_snap baseline ig_tcp hubble otterize | 52.3 | 56.7 | 31.2 | 50.1 | 0.080 | 0.074 | 6.65 | 0.92 | 7.42 |
| 4 | 10-03 09:14 | baseline hubble ig_snap otterize ig_tcp | 52.6 | 65.8 | 40.1 | 58.1 | 0.076 | 0.085 | 8.82 | 1.22 | 8.32 |
| 5 | 10-03 10:14 | otterize ig_tcp hubble ig_snap baseline | 32.4 | 43.6 | 34.0 | 44.1 | 0.086 | 0.086 | 7.14 | 0.99 | 7.49 |
| 6 | 10-03 11:13 | ig_snap ig_tcp baseline otterize hubble | 50.2 | 57.7 | 36.6 | 41.7 | 0.085 | 0.080 | 6.78 | 0.94 | 8.36 |
| 7 | 10-03 12:11 | baseline ig_snap hubble ig_tcp otterize | 46.2 | 51.9 | 46.4 | 48.2 | 0.086 | 0.085 | 7.08 | 0.98 | 7.04 |
| 8 | 10-03 13:11 | ig_tcp otterize ig_snap hubble baseline | 42.0 | 44.1 | 37.1 | 53.5 | 0.072 | 0.083 | 8.19 | 1.14 | 7.70 |
| 9 | 10-03 14:09 | hubble otterize baseline ig_tcp ig_snap | 25.8 | 48.7 | 24.1 | 46.5 | 0.077 | 0.074 | 6.91 | 0.96 | 7.17 |
| 10 | 10-03 15:07 | ig_tcp ig_snap otterize baseline hubble | 37.2 | 41.0 | 40.6 | 44.9 | 0.078 | 0.103 | 9.02 | 1.24 | 8.30 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Otterize; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.050 [+0.041, +0.058] | <0.001 | +0.052 | 0.002 | +0.050 [+0.041, +0.058] | 10 | robust |
| Δ observer CPU | Otterize | +0.052 [+0.047, +0.057] | <0.001 | +0.051 | 0.002 | +0.053 [+0.048, +0.058] | 9 | robust |
| Δ observer CPU | IG trace_tcp | +0.078 [+0.073, +0.082] | <0.001 | +0.078 | 0.002 | +0.078 [+0.073, +0.082] | 10 | robust |
| Δ observer CPU | IG snapshot_socket | +0.071 [+0.064, +0.077] | <0.001 | +0.068 | 0.002 | +0.071 [+0.064, +0.077] | 10 | robust |
| Δ observer anon memory | Hubble | +91 [+88, +94] | <0.001 | +93 | 0.002 | +91 [+88, +94] | 10 | robust |
| Δ observer anon memory | Otterize | +79 [+76, +82] | <0.001 | +79 | 0.002 | +80 [+77, +83] | 9 | robust |
| Δ observer anon memory | IG trace_tcp | +133 [+128, +137] | <0.001 | +135 | 0.002 | +133 [+128, +137] | 10 | robust |
| Δ observer anon memory | IG snapshot_socket | +111 [+109, +113] | <0.001 | +110 | 0.002 | +111 [+109, +113] | 10 | robust |
| fixed-count time, keep-alive | Hubble | -0.8% [-14.6, +13.0] (n.s.) | 1.000 | +0.9% | 1.000 | -0.8% [-14.6, +13.0] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | Otterize | +3.6% [-18.3, +25.4] (n.s.) | 1.000 | -4.0% | 0.625 | +4.7% [-20.1, +29.4] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | IG trace_tcp | -5.0% [-22.9, +13.0] (n.s.) | 1.000 | -5.5% | 0.375 | -5.0% [-22.9, +13.0] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | IG snapshot_socket | -6.6% [-20.7, +7.5] (n.s.) | 1.000 | -2.9% | 0.432 | -6.6% [-20.7, +7.5] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +5.2% [-6.7, +17.1] (n.s.) | 1.000 | -1.1% | 0.625 | +5.2% [-6.7, +17.1] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | Otterize | +3.2% [-19.8, +26.2] (n.s.) | 1.000 | -4.2% | 0.492 | +6.2% [-18.8, +31.3] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | +1.7% [-12.9, +16.4] (n.s.) | 1.000 | +0.4% | 1.000 | +1.7% [-12.9, +16.4] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | IG snapshot_socket | -0.1% [-13.5, +13.3] (n.s.) | 1.000 | -1.2% | 0.492 | -0.1% [-13.5, +13.3] (n.s.) | 10 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 3008 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 0.77 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 41.94 ± 9.12 (n=10) | 40.62 ± 7.78 (n=10) | -0.79% [-14.60, +13.01] (n.s.) (< 13.0% at 95%) | 0.899 | 1.000 | recommendationservice 0.85 | 0.00 |
| keepalive | Otterize | 41.94 ± 9.12 (n=10) | 41.33 ± 5.44 (n=10) | +3.58% [-18.28, +25.44] (n.s.) (< 25.4% at 95%) | 0.719 | 1.000 | recommendationservice 0.80 | 0.00 |
| keepalive | IG trace_tcp | 41.94 ± 9.12 (n=10) | 38.45 ± 7.41 (n=10) | -4.96% [-22.92, +13.01] (n.s.) (< 13.0% at 95%) | 0.548 | 1.000 | recommendationservice 0.84 | 0.01 |
| keepalive | IG snapshot_socket | 41.94 ± 9.12 (n=10) | 37.88 ± 6.14 (n=10) | -6.62% [-20.71, +7.46] (n.s.) (< 7.5% at 95%) | 0.315 | 1.000 | recommendationservice 0.79 | 0.01 |
| newconn | Hubble | 37.37 ± 6.56 (n=10) | 38.72 ± 6.17 (n=10) | +5.23% [-6.68, +17.13] (n.s.) (< 17.1% at 95%) | 0.347 | 1.000 | recommendationservice 0.77 | 1.00 |
| newconn | Otterize | 37.37 ± 6.56 (n=10) | 37.22 ± 7.43 (n=10) | +3.20% [-19.84, +26.23] (n.s.) (< 26.2% at 95%) | 0.761 | 1.000 | frontend 0.82 | 1.01 |
| newconn | IG trace_tcp | 37.37 ± 6.56 (n=10) | 37.17 ± 5.51 (n=10) | +1.74% [-12.88, +16.35] (n.s.) (< 16.4% at 95%) | 0.794 | 1.000 | recommendationservice 0.95 | 1.00 |
| newconn | IG snapshot_socket | 37.37 ± 6.56 (n=10) | 36.68 ± 5.96 (n=10) | -0.06% [-13.47, +13.35] (n.s.) (< 13.3% at 95%) | 0.992 | 1.000 | recommendationservice 0.85 | 1.00 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 41.94 ± 9.12 | 21.74% | 21.74% | 10 |
| newconn | 37.37 ± 6.56 | 17.55% | 17.55% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.096 ± 0.005 | 0.008 | - | 0.410 ± 0.021 | 0.041 | - | - | - | - |
| Hubble | 0.146 ± 0.013 | 0.020 | +0.050 [+0.041, +0.058] | 0.458 ± 0.043 | 0.066 | +0.048 [+0.015, +0.081] | +0.48% | +0.019 | <0.001 / <0.001 |
| Otterize | 0.148 ± 0.006 | 0.013 | +0.052 [+0.047, +0.057] | 0.459 ± 0.017 | 0.048 | +0.049 [+0.028, +0.070] | +0.49% | +0.007 | <0.001 / <0.001 |
| IG trace_tcp | 0.174 ± 0.007 | 0.012 | +0.078 [+0.073, +0.082] | 0.510 ± 0.023 | 0.049 | +0.100 [+0.083, +0.118] | +1.00% | +0.039 | <0.001 / <0.001 |
| IG snapshot_socket | 0.167 ± 0.008 | 0.012 | +0.071 [+0.064, +0.077] | 0.500 ± 0.018 | 0.045 | +0.090 [+0.075, +0.105] | +0.90% | +0.033 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.026 [+0.018, +0.034] | +0.007 [-0.014, +0.028] (n.s.) | +0.020 [-0.011, +0.051] (n.s.) | 52% |
| Otterize | +0.053 [+0.047, +0.059] | +0.021 [+0.000, +0.041] | +0.067 [+0.036, +0.098] | 103% |
| IG trace_tcp | +0.076 [+0.068, +0.084] | +0.026 [+0.001, +0.051] | +0.088 [+0.061, +0.116] | 98% |
| IG snapshot_socket | +0.066 [+0.061, +0.072] | +0.019 [-0.009, +0.047] (n.s.) | +0.073 [+0.039, +0.106] | 94% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.044 [+0.032, +0.056] | +0.068 [-0.006, +0.142] (n.s.) | +0.024 [-0.000, +0.049] (n.s.) | 1.32 → 1.31 | 10% |
| keepalive | Otterize | +0.050 [+0.040, +0.060] | +0.053 [+0.014, +0.093] | +0.017 [-0.005, +0.039] (n.s.) | 1.32 → 1.31 | 9% |
| keepalive | IG trace_tcp | +0.078 [+0.064, +0.092] | +0.115 [+0.033, +0.197] | +0.037 [+0.004, +0.071] | 1.32 → 1.34 | 11% |
| keepalive | IG snapshot_socket | +0.072 [+0.057, +0.087] | +0.097 [+0.025, +0.170] | +0.036 [+0.008, +0.064] | 1.32 → 1.14 | 10% |
| newconn | Hubble | +0.458 [+0.419, +0.498] | +0.588 [+0.500, +0.676] | +0.155 [+0.124, +0.186] | 1.23 → 1.23 | 25% |
| newconn | Otterize | +0.064 [+0.050, +0.078] | +0.052 [+0.020, +0.083] | +0.002 [-0.027, +0.030] (n.s.) | 1.23 → 1.39 | 11% |
| newconn | IG trace_tcp | +0.176 [+0.156, +0.197] | +0.301 [+0.200, +0.401] | +0.149 [+0.116, +0.182] | 1.23 → 1.48 | 18% |
| newconn | IG snapshot_socket | +0.082 [+0.066, +0.098] | +0.116 [+0.059, +0.173] | +0.034 [+0.009, +0.059] | 1.23 → 1.19 | 12% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 658 ± 14 | 2.3 | 1.50 | 371 | - | - | 3302 ± 61 | - | - |
| Hubble | 763 ± 31 (peak 778) | 8.5 | 6.10 | 462 | +91 [+88, +94] | +104 [+88, +121] | 3404 ± 65 | +0.57% | <0.001 / <0.001 |
| Otterize | 753 ± 41 (peak 758) | 3.0 | 1.64 | 450 | +79 [+76, +82] | +95 [+75, +114] | 3407 ± 67 | +0.50% | <0.001 / <0.001 |
| IG trace_tcp | 824 ± 73 (peak 835) | 5.4 | -2.54 | 504 | +133 [+128, +137] | +166 [+119, +212] | 3523 ± 58 | +0.83% | <0.001 / <0.001 |
| IG snapshot_socket | 777 ± 16 (peak 821) | 14.4 | 5.16 | 482 | +111 [+109, +113] | +119 [+116, +121] | 3483 ± 54 | +0.69% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.082 | 0.103 | 0.082 | 0.082 | 0.082 |
| cilium-envoy | 0.009 | 0.009 | 0.009 | 0.009 | 0.009 |
| cilium-operator | 0.005 | 0.004 | 0.005 | 0.005 | 0.005 |
| hubble-relay | 0.000 | 0.013 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.004 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.048 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.074 | 0.071 |
| client-hubble | 0.000 | 0.016 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.003 | 0.000 |
| app | 0.080 | 0.073 | 0.078 | 0.077 | 0.076 |
| loadgen | 0.007 | 0.006 | 0.007 | 0.007 | 0.007 |
| k3s | 0.201 | 0.221 | 0.207 | 0.240 | 0.234 |
| k8s-addons | 0.009 | 0.008 | 0.010 | 0.009 | 0.009 |
| os | 0.002 | 0.001 | 0.002 | 0.002 | 0.002 |
| harness | 0.038 | 0.037 | 0.038 | 0.036 | 0.038 |
| node | 0.410 | 0.458 | 0.459 | 0.510 | 0.500 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%. At under 5 req/s the window holds few requests; do not read the p95/p99 deltas.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 2.18 ± 0.06 | 22.7 ± 2.5 | - | 56.6 ± 12.0 | - | 108.4 ± 14.3 | - | 0.05 |
| Hubble | 2.20 ± 0.03 | 18.8 ± 3.3 | -16.3% [-28.7, -3.8] | 38.8 ± 7.4 | -29.9% [-39.0, -20.8] | 90.8 ± 14.8 | -16.0% [-23.5, -8.6] | 0.02 |
| Otterize | 2.18 ± 0.04 | 21.0 ± 2.1 | -6.2% [-17.8, +5.5] (n.s.) | 44.9 ± 8.4 | -15.3% [-39.2, +8.6] (n.s.) | 101.8 ± 11.0 | -4.6% [-16.4, +7.3] (n.s.) | 0.03 |
| IG trace_tcp | 2.18 ± 0.06 | 20.8 ± 2.7 | -8.3% [-13.4, -3.2] | 46.0 ± 11.3 | -17.4% [-30.1, -4.7] | 100.7 ± 13.2 | -6.5% [-14.7, +1.6] (n.s.) | 0.03 |
| IG snapshot_socket | 2.18 ± 0.07 | 21.7 ± 1.5 | -3.4% [-11.7, +4.8] (n.s.) | 47.0 ± 9.8 | -13.1% [-32.7, +6.5] (n.s.) | 99.0 ± 13.5 | -7.0% [-20.7, +6.7] (n.s.) | 0.02 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 4.5 | 4.43 | 0.04 | - | - | - | - | - |
| Hubble | 4.7 | 4.63 | 0.05 | +265 [+47, +483] | +5838 [+5225, +6452] | +5832 [+5219, +6446] | +8110 [+6455, +9766] | 31.9 (thesis 33.2) |
| Otterize | 5.6 | 5.65 | -0.11 | -63 [-202, +75] (n.s.) | +156 [-39, +350] (n.s.) | +155 [-38, +349] (n.s.) | -274 [-2385, +1838] (n.s.) | - |
| IG trace_tcp | 4.5 | 4.43 | 0.01 | +40 [-110, +190] (n.s.) | +1307 [+999, +1616] | +1307 [+998, +1615] | +2827 [+323, +5331] | 5.4 (thesis 5.7) |
| IG snapshot_socket | 4.5 | 4.44 | 0.05 | +56 [-113, +226] (n.s.) | +177 [-8, +362] (n.s.) | +177 [-8, +362] (n.s.) | +430 [-1198, +2057] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 18%. Lost events: 0 in the window, 64 over the whole run (fixed-count tests included). hubble_* series at the end: 320.

| Class | flows/s | share |
|---|---|---|
| app | 12.2 | 26% |
| probe | 25.4 | 54% |
| client_feedback | 2.7 | 6% |
| other | 7.2 | 15% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.071 [+0.064, +0.077] cores. Standing (window before the snapshot) minus baseline observer: +0.070 cores; one snapshot adds 0.04 ± 0.86 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.261 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.041 [+0.030, +0.053] | +0.050 | +0.039 [-0.013, +0.091] (n.s.) | +0.23% / +0.22% | +67 [+44, +90] | +0.11% |
| Otterize | +0.078 [+0.070, +0.085] | +0.076 | +0.088 [+0.051, +0.126] | +0.43% / +0.49% | +115 [+84, +147] | +0.20% |
| IG trace_tcp | +0.142 [+0.131, +0.153] | +0.143 | +0.182 [+0.154, +0.211] | +0.79% / +1.01% | +345 [+249, +441] | +0.59% |
| IG snapshot_socket | +0.133 [+0.125, +0.141] | +0.136 | +0.158 [+0.124, +0.192] | +0.74% / +0.88% | +257 [+244, +269] | +0.44% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 4 | 0.03% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 38.16 |
| 2 | baseline | 2 | 0.03% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 45.29 |
| 3 | baseline | 2 | 0.10% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 31.24 |
| 4 | baseline | 1 | 0.17% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 40.06 |
| 5 | baseline | 5 | 0.08% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 34.02 |
| 6 | baseline | 3 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 36.64 |
| 7 | baseline | 1 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 46.42 |
| 8 | baseline | 5 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 37.13 |
| 9 | baseline | 3 | 0.11% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 24.15 |
| 10 | baseline | 4 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 40.56 |
| 1 | Hubble | 2 | 0.14% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 35.68 |
| 2 | Hubble | 1 | 0.70% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 44.56 |
| 3 | Hubble | 4 | 0.24% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 39.62 |
| 4 | Hubble | 2 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 32.24 |
| 5 | Hubble | 3 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 33.85 |
| 6 | Hubble | 5 | 0.09% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 46.00 |
| 7 | Hubble | 3 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 49.46 |
| 8 | Hubble | 4 | 1.32% (high) | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 35.65 |
| 9 | Hubble | 1 | 0.09% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 31.35 |
| 10 | Hubble | 5 | 0.16% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 38.79 |
| 1 | Otterize | 1 | 0.21% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 28.94 |
| 2 | Otterize | 3 | 0.03% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 43.74 |
| 3 | Otterize | 5 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 31.19 |
| 4 | Otterize | 4 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 52.19 |
| 5 | Otterize | 1 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 31.28 |
| 6 | Otterize | 4 | 0.23% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 34.82 |
| 7 | Otterize | 5 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 30.84 |
| 8 | Otterize | 2 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 37.93 |
| 9 | Otterize | 2 | 0.25% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 43.83 |
| 10 | Otterize | 3 | 0.07% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 37.46 |
| 1 | IG trace_tcp | 3 | 0.24% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 34.22 |
| 2 | IG trace_tcp | 5 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 37.86 |
| 3 | IG trace_tcp | 3 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 39.39 |
| 4 | IG trace_tcp | 5 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 39.81 |
| 5 | IG trace_tcp | 2 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 34.54 |
| 6 | IG trace_tcp | 2 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 38.51 |
| 7 | IG trace_tcp | 4 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 47.72 |
| 8 | IG trace_tcp | 1 | 0.27% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 26.15 |
| 9 | IG trace_tcp | 4 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 34.40 |
| 10 | IG trace_tcp | 1 | 0.06% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 39.07 |
| 1 | IG snapshot_socket | 5 | 0.08% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 28.74 |
| 2 | IG snapshot_socket | 4 | 0.04% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 44.44 |
| 3 | IG snapshot_socket | 1 | 0.14% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 31.08 |
| 4 | IG snapshot_socket | 3 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 35.06 |
| 5 | IG snapshot_socket | 4 | 0.03% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 35.09 |
| 6 | IG snapshot_socket | 1 | 0.03% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 34.84 |
| 7 | IG snapshot_socket | 2 | 0.05% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 46.26 |
| 8 | IG snapshot_socket | 3 | 0.10% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 32.53 |
| 9 | IG snapshot_socket | 5 | 0.09% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 35.36 |
| 10 | IG snapshot_socket | 2 | 0.30% | 6ac09d9faf86f3063ae25c87 | 09f3ce84,610652e3,c2dc7fcd | 43.41 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 7.70/6.37 | 7.29/6.59 | 9.54/11.32 | 9.10/11.30 | 0.96 |
| 1 | Hubble | 8.07/5.51 | 7.68/7.50 | 8.49/10.11 | 10.18/8.66 | 1.05 |
| 1 | Otterize | 7.06/7.43 | 7.45/7.50 | 10.67/9.94 | 10.52/7.33 | 1.04 |
| 1 | IG trace_tcp | 7.56/8.42 | 7.68/7.43 | 10.53/9.81 | 9.90/10.28 | 1.05 |
| 1 | IG snapshot_socket | 9.08/7.65 | 7.40/6.85 | 10.43/9.49 | 10.80/10.56 | 0.99 |
| 2 | baseline | 8.17/7.06 | 6.93/8.39 | 10.45/8.40 | 8.58/7.77 | 1.07 |
| 2 | Hubble | 8.28/7.06 | 9.09/7.87 | 8.07/7.13 | 10.09/8.23 | 1.17 |
| 2 | Otterize | 10.01/8.91 | 6.99/6.91 | 7.78/8.95 | 9.80/9.78 | 0.96 |
| 2 | IG trace_tcp | 11.35/9.97 | 11.25/9.59 | 14.70/12.85 | 13.45/13.18 | 1.44 |
| 2 | IG snapshot_socket | 7.94/8.61 | 7.41/6.50 | 6.50/9.87 | 6.24/10.19 | 0.96 |
| 3 | baseline | 9.02/7.15 | 6.56/6.74 | 8.01/7.61 | 11.49/11.60 | 0.92 |
| 3 | Hubble | 7.15/6.47 | 6.87/7.13 | 8.75/9.09 | 7.96/8.18 | 0.97 |
| 3 | Otterize | 7.87/7.39 | 6.95/6.88 | 7.93/7.92 | 9.48/10.82 | 0.96 |
| 3 | IG trace_tcp | 8.11/7.88 | 7.64/6.62 | 8.06/6.52 | 9.91/7.77 | 0.99 |
| 3 | IG snapshot_socket | 6.75/7.11 | 12.19/6.64 | 13.66/6.91 | 11.81/11.22 | 1.29 |
| 4 | baseline | 10.40/6.73 | 10.81/6.83 | 9.71/8.34 | 10.35/10.52 | 1.22 |
| 4 | Hubble | 8.02/7.72 | 7.09/8.21 | 7.38/9.81 | 10.73/10.80 | 1.07 |
| 4 | Otterize | 7.19/11.74 | 6.29/10.49 | 9.18/10.40 | 8.24/9.36 | 1.18 |
| 4 | IG trace_tcp | 11.21/8.40 | 10.86/6.85 | 9.83/7.50 | 11.23/8.73 | 1.22 |
| 4 | IG snapshot_socket | 9.71/9.94 | 7.36/8.43 | 8.60/8.27 | 9.59/10.09 | 1.10 |
| 5 | baseline | 7.43/6.18 | 7.89/6.38 | 9.77/9.58 | 9.81/8.90 | 0.99 |
| 5 | Hubble | 10.99/8.11 | 10.72/7.80 | 9.29/12.92 | 10.79/11.22 | 1.28 |
| 5 | Otterize | 7.96/7.13 | 7.06/6.33 | 7.87/8.64 | 11.03/10.91 | 0.93 |
| 5 | IG trace_tcp | 7.74/7.30 | 7.59/6.44 | 7.39/6.40 | 8.81/8.56 | 0.97 |
| 5 | IG snapshot_socket | 8.20/6.92 | 8.03/6.69 | 11.46/8.77 | 9.82/8.33 | 1.02 |
| 6 | baseline | 7.05/6.42 | 6.82/6.74 | 6.83/9.65 | 7.52/8.85 | 0.94 |
| 6 | Hubble | 7.66/9.75 | 7.08/9.02 | 7.61/9.08 | 8.13/7.14 | 1.12 |
| 6 | Otterize | 9.22/6.55 | 9.55/7.33 | 8.92/7.25 | 10.27/11.32 | 1.17 |
| 6 | IG trace_tcp | 10.54/6.40 | 9.95/6.67 | 13.51/9.36 | 12.74/10.07 | 1.15 |
| 6 | IG snapshot_socket | 9.17/11.32 | 9.04/11.37 | 9.32/14.50 | 10.64/12.77 | 1.42 |
| 7 | baseline | 6.69/7.33 | 7.48/6.69 | 7.52/8.64 | 6.96/7.95 | 0.98 |
| 7 | Hubble | 8.19/7.67 | 6.41/6.71 | 6.68/6.98 | 7.04/6.61 | 0.91 |
| 7 | Otterize | 7.41/6.17 | 6.86/6.51 | 8.03/7.33 | 10.91/11.30 | 0.93 |
| 7 | IG trace_tcp | 8.28/11.02 | 8.10/7.16 | 7.95/8.96 | 7.91/8.55 | 1.06 |
| 7 | IG snapshot_socket | 9.35/7.92 | 7.92/6.57 | 10.60/7.45 | 8.82/6.60 | 1.00 |
| 8 | baseline | 9.52/9.84 | 8.21/8.18 | 7.62/7.49 | 10.98/9.81 | 1.14 |
| 8 | Hubble | 7.33/7.41 | 6.62/6.82 | 10.54/10.55 | 7.95/7.56 | 0.93 |
| 8 | Otterize | 7.26/7.78 | 6.73/9.13 | 6.51/9.51 | 8.77/11.00 | 1.11 |
| 8 | IG trace_tcp | 6.45/7.23 | 7.30/7.87 | 13.65/11.25 | 12.19/12.15 | 1.05 |
| 8 | IG snapshot_socket | 7.84/8.52 | 7.85/8.27 | 8.07/8.39 | 9.77/10.00 | 1.12 |
| 9 | baseline | 8.64/8.78 | 7.15/6.67 | 13.76/13.49 | 12.96/14.72 | 0.96 |
| 9 | Hubble | 10.56/10.53 | 7.41/7.65 | 10.60/10.51 | 12.44/9.16 | 1.05 |
| 9 | Otterize | 7.38/7.53 | 7.20/7.38 | 7.85/7.71 | 7.80/7.88 | 1.01 |
| 9 | IG trace_tcp | 8.61/9.74 | 7.27/7.60 | 8.92/10.28 | 7.51/9.28 | 1.03 |
| 9 | IG snapshot_socket | 11.08/11.56 | 6.90/6.49 | 7.84/10.61 | 7.15/9.11 | 0.93 |
| 10 | baseline | 10.80/8.50 | 11.09/6.95 | 9.74/6.24 | 9.80/6.27 | 1.24 |
| 10 | Hubble | 9.86/10.36 | 7.88/8.52 | 10.06/11.59 | 8.85/10.55 | 1.14 |
| 10 | Otterize | 10.17/8.52 | 10.72/6.86 | 11.73/7.45 | 13.17/8.05 | 1.21 |
| 10 | IG trace_tcp | 10.73/8.52 | 8.35/6.96 | 8.44/6.85 | 9.20/6.88 | 1.06 |
| 10 | IG snapshot_socket | 9.23/9.07 | 7.71/7.95 | 7.54/7.44 | 7.86/7.56 | 1.09 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 51.99 ± 7.99 (n=10) | 51.44 ± 8.47 (n=10) | +1.65% [-18.03, +21.34] (n.s.) (< 21.3% at 95%) | 0.853 | 1.000 |
| keepalive | Otterize | 51.99 ± 7.99 (n=10) | 48.97 ± 6.63 (n=10) | -3.87% [-17.79, +10.04] (n.s.) (< 10.0% at 95%) | 0.545 | 1.000 |
| keepalive | IG trace_tcp | 51.99 ± 7.99 (n=10) | 50.71 ± 15.00 (n=10) | -2.98% [-17.12, +11.16] (n.s.) (< 11.2% at 95%) | 0.645 | 1.000 |
| keepalive | IG snapshot_socket | 51.99 ± 7.99 (n=10) | 48.14 ± 5.75 (n=10) | -5.67% [-17.40, +6.06] (n.s.) (< 6.1% at 95%) | 0.303 | 1.000 |
| newconn | Hubble | 49.27 ± 5.12 (n=10) | 48.05 ± 4.91 (n=10) | -1.24% [-12.84, +10.37] (n.s.) (< 10.4% at 95%) | 0.815 | 1.000 |
| newconn | Otterize | 49.27 ± 5.12 (n=10) | 50.53 ± 7.97 (n=10) | +3.38% [-9.14, +15.90] (n.s.) (< 15.9% at 95%) | 0.556 | 1.000 |
| newconn | IG trace_tcp | 49.27 ± 5.12 (n=10) | 50.59 ± 9.47 (n=10) | +3.46% [-11.91, +18.82] (n.s.) (< 18.8% at 95%) | 0.623 | 1.000 |
| newconn | IG snapshot_socket | 49.27 ± 5.12 (n=10) | 47.27 ± 4.79 (n=10) | -2.88% [-14.71, +8.95] (n.s.) (< 8.9% at 95%) | 0.595 | 1.000 |

## Excluded runs

None.

## Data warnings in used runs

| App | Rep | Condition | Warning |
|---|---|---|---|
| boutique | 1 | hubble | Hubble lost 61 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 10 | hubble | Hubble lost 72 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 2 | hubble | Hubble lost 65 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 3 | hubble | Hubble lost 61 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 4 | hubble | Hubble lost 59 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 5 | hubble | Hubble lost 68 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 6 | hubble | Hubble lost 63 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 7 | hubble | Hubble lost 66 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 8 | hubble | Hubble lost 61 events during the run (ring buffer), 0 of them in the steady window |
| boutique | 8 | hubble | steal 1.32% is more than twice the app median (0.05%) |
| boutique | 9 | hubble | Hubble lost 59 events during the run (ring buffer), 0 of them in the steady window |

## Method notes

- Observer CPU and memory include cilium-agent, cilium-envoy and cilium-operator in every condition, so the baseline row is not zero. The Δ columns are the cost of the technique.
- Cluster busy CPU comes from /proc/stat on each node (user + nice + system + irq + softirq; steal and iowait left out). It also catches indirect costs: API-server and kubelet work for `kubectl port-forward` and `kubectl gadget` streams, exec probes of the gadget DaemonSet, and BPF work in the app's syscalls or in softirq. The kernel here has CONFIG_IRQ_TIME_ACCOUNTING off, so softirq time is charged to whatever task it interrupts.
- The fixed-count time is the tool's own total (hey `Total`), so pod start-up is not in it.
- The steady-window per-flow cost is not reported: the journey-A load keeps connections open, so almost every new connection in the window is a kubelet probe. Per-request and per-connection costs come from the fixed-count tests.
- Events/s for Hubble and IG count client events whose event time falls inside the analysis window (client_bins.json), so both use the same window and the app namespace only.
- The projection is an estimate with two known gaps: no platform background traffic, and a different CPU model and kernel (6.12 here, 6.8 on test-cluster).
- Host-speed canary (bin/canary.py): every 2 s each node runs a fixed pure-Python integer loop and logs its thread CPU time. Iterations per CPU-second is the host speed index; it falls when the hypervisor gives the guest less work per CPU-second (unreported steal, a busy sibling thread, a lower clock). Normalised CPU = cores x speed / the app's median speed (per node); normalised fixed-count time = time x the workers' speed ratio during the test. The canary costs about 1% of one core per node and is counted as harness.
