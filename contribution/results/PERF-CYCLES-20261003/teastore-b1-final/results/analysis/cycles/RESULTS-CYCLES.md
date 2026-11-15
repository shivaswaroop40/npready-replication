# Capture overhead: interleaved cycles (randomized multiple interleaved trials)

Generated 2026-10-05 18:02 UTC by analyze/analyze.py from `teastore-b1-final/results`. 50 run directories, 50 used, 0 excluded.

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
| Hubble | node-bound | teastore +0.046 | teastore +0.56% | teastore -4.1% n.s. | teastore +15.5% | teastore +0.20% |
| Otterize | node-bound | teastore +0.048 | teastore +0.38% | teastore -18.0% | teastore -17.6% | teastore +0.39% |
| IG trace_tcp | node-bound | teastore +0.073 | teastore +0.98% | teastore -1.3% n.s. | teastore +0.1% n.s. | teastore +0.75% |
| IG snapshot_socket | node-bound | teastore +0.063 | teastore +0.61% | teastore -0.4% n.s. | teastore -1.1% n.s. | teastore +0.70% |

Diagnostic only, do not quote: the same, canary-normalised (each run scaled to the app's median canary speed). The 2026-10-03 validation showed the canary does not track the host drift (r 0.41, normalised CV 16.4% vs 16.6% raw) and inflates deltas 1.7-4.7x. The raw paired deltas above, over interleaved cycles, are the result.

| Technique | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn |
|---|---|---|---|---|
| Hubble | teastore +0.045 | teastore +0.50% | teastore -0.2% n.s. | teastore +22.7% |
| Otterize | teastore +0.047 | teastore +0.33% n.s. | teastore -18.0% | teastore -16.3% n.s. |
| IG trace_tcp | teastore +0.076 | teastore +1.10% | teastore +1.7% n.s. | teastore +4.6% n.s. |
| IG snapshot_socket | teastore +0.075 | teastore +1.29% | teastore +6.1% n.s. | teastore +6.9% n.s. |

## teastore

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.056 [+0.030, +0.082] | <0.001 | 0.003 | +0.050 [+0.012, +0.088] | 0.016 | 0.032 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.038 [+0.006, +0.070] | 0.026 | 0.053 | +0.033 [-0.016, +0.083] (n.s.) | 0.162 | 0.162 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.098 [+0.078, +0.119] | <0.001 | <0.001 | +0.110 [+0.069, +0.150] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.061 [+0.008, +0.115] | 0.029 | 0.053 | +0.129 [+0.069, +0.188] | <0.001 | 0.003 | 10 |
| Δ observer CPU (cores) | Hubble | +0.046 [+0.042, +0.050] | <0.001 | <0.001 | +0.045 [+0.040, +0.050] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.048 [+0.043, +0.053] | <0.001 | <0.001 | +0.047 [+0.043, +0.051] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.073 [+0.070, +0.077] | <0.001 | <0.001 | +0.076 [+0.069, +0.083] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.063 [+0.059, +0.068] | <0.001 | <0.001 | +0.075 [+0.063, +0.087] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | -0.009 [-0.027, +0.008] (n.s.) | 0.256 | 0.578 | -0.014 [-0.040, +0.013] (n.s.) | 0.284 | 1.000 | 10 |
| Δ app CPU (cores) | Otterize | -0.016 [-0.037, +0.005] (n.s.) | 0.116 | 0.462 | -0.016 [-0.053, +0.020] (n.s.) | 0.334 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | -0.008 [-0.025, +0.008] (n.s.) | 0.283 | 0.578 | -0.001 [-0.031, +0.028] (n.s.) | 0.919 | 1.000 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | -0.017 [-0.045, +0.010] (n.s.) | 0.193 | 0.578 | +0.021 [-0.020, +0.062] (n.s.) | 0.278 | 1.000 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.027 [+0.020, +0.034] | <0.001 | <0.001 | +0.026 [+0.018, +0.034] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.008 [-0.002, +0.017] (n.s.) | 0.101 | 0.101 | +0.005 [-0.002, +0.012] (n.s.) | 0.127 | 0.127 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.041 [+0.035, +0.046] | <0.001 | <0.001 | +0.042 [+0.033, +0.051] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.021 [+0.003, +0.038] | 0.024 | 0.048 | +0.034 [+0.023, +0.045] | <0.001 | <0.001 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +86 [+81, +90] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +81 [+79, +83] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +134 [+126, +142] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +110 [+107, +113] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +99 [+81, +116] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +100 [+72, +128] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +175 [+128, +222] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +124 [+112, +136] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | -4.1% [-16.3, +8.0] (n.s.) | 0.463 | 1.000 | -0.2% [-16.4, +16.0] (n.s.) | 0.980 | 1.000 | 10 |
| fixed-count time, keep-alive | Otterize | -18.0% [-34.3, -1.8] | 0.033 | 0.132 | -18.0% [-35.1, -1.0] | 0.040 | 0.162 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | -1.3% [-7.6, +5.0] (n.s.) | 0.649 | 1.000 | +1.7% [-10.2, +13.6] (n.s.) | 0.757 | 1.000 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | -0.4% [-8.1, +7.3] (n.s.) | 0.917 | 1.000 | +6.1% [-6.3, +18.5] (n.s.) | 0.298 | 0.893 | 10 |
| fixed-count time, new conn | Hubble | +15.5% [+2.9, +28.2] | 0.021 | 0.085 | +22.7% [+4.5, +40.9] | 0.020 | 0.080 | 10 |
| fixed-count time, new conn | Otterize | -17.6% [-33.6, -1.6] | 0.034 | 0.103 | -16.3% [-35.0, +2.4] (n.s.) | 0.080 | 0.240 | 10 |
| fixed-count time, new conn | IG trace_tcp | +0.1% [-6.7, +6.9] (n.s.) | 0.973 | 1.000 | +4.6% [-5.0, +14.2] (n.s.) | 0.306 | 0.473 | 10 |
| fixed-count time, new conn | IG snapshot_socket | -1.1% [-8.8, +6.5] (n.s.) | 0.745 | 1.000 | +6.9% [-5.4, +19.3] (n.s.) | 0.237 | 0.473 | 10 |
| canary speed, workers, steady window (check) | Hubble | -2.85% [-8.22, +2.52] (n.s.) | 0.261 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | -1.32% [-11.01, +8.37] (n.s.) | 0.765 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | +1.98% [-6.78, +10.74] (n.s.) | 0.622 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | +6.97% [-7.37, +21.30] (n.s.) | 0.300 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 7.0% raw, 11.8% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.17; new conn: CV of the baseline time across cycles 6.8% raw, 9.9% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.07.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-04 03:57 | otterize hubble ig_tcp baseline ig_snap | 51.6 | 68.3 | 52.1 | 66.1 | 0.439 | 0.476 | 10.11 | 1.21 | 8.97 |
| 2 | 10-04 04:57 | otterize ig_tcp hubble ig_snap baseline | 46.8 | 59.7 | 47.1 | 52.0 | 0.433 | 0.430 | 8.52 | 1.02 | 8.51 |
| 3 | 10-04 05:57 | hubble otterize baseline ig_tcp ig_snap | 50.1 | 57.4 | 49.7 | 58.6 | 0.429 | 0.422 | 8.29 | 0.99 | 8.73 |
| 4 | 10-04 06:58 | ig_tcp otterize ig_snap hubble baseline | 50.0 | 60.0 | 49.9 | 61.8 | 0.423 | 0.396 | 7.90 | 0.94 | 8.81 |
| 5 | 10-04 08:00 | hubble baseline otterize ig_snap ig_tcp | 56.9 | 80.3 | 57.3 | 72.0 | 0.405 | 0.425 | 8.67 | 1.03 | 8.58 |
| 6 | 10-04 09:01 | baseline ig_snap hubble ig_tcp otterize | 45.2 | 58.5 | 45.6 | 62.7 | 0.365 | 0.414 | 9.63 | 1.15 | 8.61 |
| 7 | 10-04 10:00 | ig_snap ig_tcp baseline otterize hubble | 46.4 | 64.3 | 46.9 | 60.9 | 0.420 | 0.455 | 8.91 | 1.06 | 8.79 |
| 8 | 10-04 11:01 | ig_snap baseline ig_tcp hubble otterize | 48.1 | 56.7 | 48.6 | 54.5 | 0.415 | 0.415 | 8.28 | 0.99 | 8.31 |
| 9 | 10-04 12:01 | baseline hubble ig_snap otterize ig_tcp | 46.4 | 59.9 | 46.8 | 55.4 | 0.440 | 0.447 | 8.44 | 1.01 | 8.76 |
| 10 | 10-04 13:02 | ig_tcp ig_snap otterize baseline hubble | 49.6 | 56.4 | 49.3 | 56.9 | 0.417 | 0.388 | 7.91 | 0.94 | 8.92 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Otterize; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.046 [+0.042, +0.050] | <0.001 | +0.048 | 0.002 | +0.046 [+0.042, +0.050] | 10 | robust |
| Δ observer CPU | Otterize | +0.048 [+0.043, +0.053] | <0.001 | +0.049 | 0.002 | +0.048 [+0.042, +0.054] | 9 | robust |
| Δ observer CPU | IG trace_tcp | +0.073 [+0.070, +0.077] | <0.001 | +0.072 | 0.002 | +0.073 [+0.070, +0.077] | 10 | robust |
| Δ observer CPU | IG snapshot_socket | +0.063 [+0.059, +0.068] | <0.001 | +0.064 | 0.002 | +0.063 [+0.059, +0.068] | 10 | robust |
| Δ observer anon memory | Hubble | +86 [+81, +90] | <0.001 | +87 | 0.002 | +86 [+81, +90] | 10 | robust |
| Δ observer anon memory | Otterize | +81 [+79, +83] | <0.001 | +80 | 0.002 | +80 [+79, +82] | 9 | robust |
| Δ observer anon memory | IG trace_tcp | +134 [+126, +142] | <0.001 | +133 | 0.002 | +134 [+126, +142] | 10 | robust |
| Δ observer anon memory | IG snapshot_socket | +110 [+107, +113] | <0.001 | +111 | 0.002 | +110 [+107, +113] | 10 | robust |
| fixed-count time, keep-alive | Hubble | -4.1% [-16.3, +8.0] (n.s.) | 1.000 | -0.5% | 0.695 | -4.1% [-16.3, +8.0] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | Otterize | -18.0% [-34.3, -1.8] | 0.231 | -6.3% | 0.037 | -14.3% [-30.0, +1.5] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | IG trace_tcp | -1.3% [-7.6, +5.0] (n.s.) | 1.000 | -2.4% | 0.432 | -1.3% [-7.6, +5.0] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | IG snapshot_socket | -0.4% [-8.1, +7.3] (n.s.) | 1.000 | -3.5% | 1.000 | -0.4% [-8.1, +7.3] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +15.5% [+2.9, +28.2] | 0.171 | +20.3% | 0.064 | +15.5% [+2.9, +28.2] | 10 | n.s. (primary) |
| fixed-count time, new conn | Otterize | -17.6% [-33.6, -1.6] | 0.231 | -5.9% | 0.027 | -13.9% [-29.4, +1.6] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | +0.1% [-6.7, +6.9] (n.s.) | 1.000 | -0.6% | 0.922 | +0.1% [-6.7, +6.9] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | IG snapshot_socket | -1.1% [-8.8, +6.5] (n.s.) | 1.000 | -5.1% | 0.846 | -1.1% [-8.8, +6.5] (n.s.) | 10 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 9152 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **node-bound** (baseline newconn bottleneck throttled 0.00 s/s), so node CPU limits the test. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 49.09 ± 3.42 (n=10) | 47.00 ± 8.20 (n=10) | -4.12% [-16.26, +8.02] (n.s.) (< 8.0% at 95%) | 0.463 | 1.000 | teastore-auth 0.00 | 0.17 |
| keepalive | Otterize | 49.09 ± 3.42 (n=10) | 40.01 ± 10.52 (n=10) | -18.04% [-34.27, -1.82] | 0.033 | 0.231 | teastore-persistence 0.00 | 0.15 |
| keepalive | IG trace_tcp | 49.09 ± 3.42 (n=10) | 48.22 ± 2.41 (n=10) | -1.32% [-7.64, +5.00] (n.s.) (< 5.0% at 95%) | 0.649 | 1.000 | teastore-recommender 0.00 | 0.18 |
| keepalive | IG snapshot_socket | 49.09 ± 3.42 (n=10) | 48.75 ± 4.65 (n=10) | -0.36% [-8.06, +7.33] (n.s.) (< 7.3% at 95%) | 0.917 | 1.000 | teastore-recommender 0.00 | 0.18 |
| newconn | Hubble | 49.32 ± 3.38 (n=10) | 56.87 ± 8.38 (n=10) | +15.55% [+2.90, +28.19] | 0.021 | 0.171 | teastore-auth 0.00 | 1.16 |
| newconn | Otterize | 49.32 ± 3.38 (n=10) | 40.43 ± 10.46 (n=10) | -17.62% [-33.60, -1.63] | 0.034 | 0.231 | teastore-persistence 0.00 | 1.14 |
| newconn | IG trace_tcp | 49.32 ± 3.38 (n=10) | 49.13 ± 2.65 (n=10) | +0.11% [-6.73, +6.94] (n.s.) (< 6.9% at 95%) | 0.973 | 1.000 | teastore-recommender 0.00 | 1.17 |
| newconn | IG snapshot_socket | 49.32 ± 3.38 (n=10) | 48.61 ± 4.68 (n=10) | -1.13% [-8.80, +6.53] (n.s.) (< 6.5% at 95%) | 0.745 | 1.000 | teastore-recommender 0.00 | 1.17 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 49.09 ± 3.42 | 6.97% | 6.97% | 10 |
| newconn | 49.32 ± 3.38 | 6.85% | 6.85% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.065 ± 0.004 | 0.006 | - | 0.684 ± 0.035 | 0.069 | - | - | - | - |
| Hubble | 0.111 ± 0.004 | 0.014 | +0.046 [+0.042, +0.050] | 0.740 ± 0.021 | 0.069 | +0.056 [+0.030, +0.082] | +0.56% | +0.027 | <0.001 / <0.001 |
| Otterize | 0.113 ± 0.009 | 0.009 | +0.048 [+0.043, +0.053] | 0.721 ± 0.033 | 0.071 | +0.038 [+0.006, +0.070] | +0.38% | +0.008 | <0.001 / <0.001 |
| IG trace_tcp | 0.139 ± 0.006 | 0.008 | +0.073 [+0.070, +0.077] | 0.782 ± 0.023 | 0.062 | +0.098 [+0.078, +0.119] | +0.98% | +0.041 | <0.001 / <0.001 |
| IG snapshot_socket | 0.128 ± 0.005 | 0.010 | +0.063 [+0.059, +0.068] | 0.745 ± 0.059 | 0.074 | +0.061 [+0.008, +0.115] | +0.61% | +0.021 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.006 [-0.004, +0.016] (n.s.) | -0.006 [-0.027, +0.015] (n.s.) | -0.010 [-0.059, +0.039] (n.s.) | 13% |
| Otterize | +0.046 [+0.040, +0.051] | +0.012 [+0.002, +0.023] | +0.043 [+0.024, +0.062] | 95% |
| IG trace_tcp | +0.070 [+0.065, +0.074] | +0.033 [+0.025, +0.042] | +0.096 [+0.076, +0.115] | 95% |
| IG snapshot_socket | +0.066 [+0.060, +0.072] | +0.030 [+0.020, +0.039] | +0.091 [+0.076, +0.107] | 105% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.158 [+0.152, +0.165] | +0.267 [+0.149, +0.385] | +0.088 [+0.083, +0.093] | 0.00 → 0.00 | 15% |
| keepalive | Otterize | +0.051 [+0.047, +0.055] | +0.093 [-0.029, +0.215] (n.s.) | +0.003 [-0.002, +0.009] (n.s.) | 0.00 → 0.00 | 10% |
| keepalive | IG trace_tcp | +0.104 [+0.091, +0.118] | +0.208 [+0.107, +0.309] | +0.082 [+0.064, +0.100] | 0.00 → 0.00 | 13% |
| keepalive | IG snapshot_socket | +0.063 [+0.058, +0.068] | +0.066 [-0.015, +0.147] (n.s.) | +0.019 [+0.010, +0.028] | 0.00 → 0.00 | 11% |
| newconn | Hubble | +0.599 [+0.548, +0.651] | +0.547 [+0.432, +0.661] | +0.212 [+0.188, +0.236] | 0.00 → 0.00 | 29% |
| newconn | Otterize | +0.074 [+0.069, +0.080] | +0.152 [+0.047, +0.257] | +0.000 [-0.004, +0.004] (n.s.) | 0.00 → 0.00 | 15% |
| newconn | IG trace_tcp | +0.195 [+0.173, +0.218] | +0.309 [+0.257, +0.361] | +0.176 [+0.141, +0.211] | 0.00 → 0.00 | 22% |
| newconn | IG snapshot_socket | +0.064 [+0.060, +0.068] | +0.100 [+0.043, +0.157] | +0.016 [+0.006, +0.026] | 0.00 → 0.00 | 15% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 650 ± 11 | 2.5 | 1.28 | 367 | - | - | 5845 ± 162 | - | - |
| Hubble | 749 ± 30 (peak 768) | 13.6 | 9.89 | 453 | +86 [+81, +90] | +99 [+81, +116] | 5988 ± 88 | +0.53% | <0.001 / <0.001 |
| Otterize | 750 ± 48 (peak 754) | 2.8 | 1.56 | 448 | +81 [+79, +83] | +100 [+72, +128] | 5931 ± 166 | +0.51% | <0.001 / <0.001 |
| IG trace_tcp | 826 ± 75 (peak 836) | 5.3 | -1.94 | 502 | +134 [+126, +142] | +175 [+128, +222] | 6097 ± 104 | +0.84% | <0.001 / <0.001 |
| IG snapshot_socket | 774 ± 19 (peak 827) | 17.1 | 7.36 | 477 | +110 [+107, +113] | +124 [+112, +136] | 6020 ± 119 | +0.69% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.055 | 0.076 | 0.057 | 0.057 | 0.054 |
| cilium-envoy | 0.007 | 0.007 | 0.007 | 0.007 | 0.006 |
| cilium-operator | 0.003 | 0.003 | 0.003 | 0.003 | 0.003 |
| hubble-relay | 0.000 | 0.011 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.004 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.042 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.069 | 0.065 |
| client-hubble | 0.000 | 0.014 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.003 | 0.000 |
| app | 0.419 | 0.409 | 0.403 | 0.410 | 0.402 |
| loadgen | 0.031 | 0.030 | 0.030 | 0.030 | 0.029 |
| k3s | 0.135 | 0.162 | 0.142 | 0.176 | 0.156 |
| k8s-addons | 0.006 | 0.006 | 0.007 | 0.007 | 0.006 |
| os | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 |
| harness | 0.033 | 0.034 | 0.034 | 0.033 | 0.031 |
| node | 0.684 | 0.740 | 0.721 | 0.782 | 0.745 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 10.76 ± 0.10 | 20.8 ± 1.1 | - | 50.1 ± 5.3 | - | 74.1 ± 3.7 | - | 6.41 |
| Hubble | 10.77 ± 0.12 | 20.3 ± 0.9 | -2.1% [-8.0, +3.9] (n.s.) | 45.5 ± 2.2 | -8.3% [-15.6, -1.0] | 67.9 ± 3.8 | -8.2% [-13.0, -3.4] | 6.49 |
| Otterize | 10.80 ± 0.14 | 19.5 ± 1.2 | -5.9% [-12.3, +0.5] (n.s.) | 46.3 ± 2.6 | -6.4% [-15.7, +2.8] (n.s.) | 70.3 ± 3.5 | -4.8% [-10.6, +0.9] (n.s.) | 6.51 |
| IG trace_tcp | 10.76 ± 0.13 | 20.8 ± 0.6 | +0.3% [-5.0, +5.7] (n.s.) | 46.8 ± 1.8 | -5.6% [-13.4, +2.1] (n.s.) | 71.7 ± 3.1 | -3.0% [-8.3, +2.4] (n.s.) | 7.00 |
| IG snapshot_socket | 10.77 ± 0.13 | 19.6 ± 2.9 | -5.3% [-17.2, +6.7] (n.s.) | 47.3 ± 5.5 | -4.5% [-16.3, +7.4] (n.s.) | 70.2 ± 7.7 | -5.1% [-13.0, +2.8] (n.s.) | 6.73 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 2.9 | 0.07 | 2.87 | - | - | - | - | - |
| Hubble | 3.1 | 0.26 | 2.85 | +823 [+707, +938] | +3793 [+3508, +4079] | +3261 [+3048, +3473] | +4104 [+3216, +4992] | 37.9 (thesis 44.7) |
| Otterize | 4.1 | 1.02 | 3.09 | +37 [-5, +78] (n.s.) | +138 [+90, +186] | +121 [+78, +163] | -598 [-1327, +131] (n.s.) | - |
| IG trace_tcp | 3.0 | 0.06 | 2.91 | +193 [+118, +267] | +708 [+577, +840] | +605 [+493, +717] | +1051 [+556, +1547] | 10.0 (thesis 15.7) |
| IG snapshot_socket | 3.0 | 0.07 | 2.89 | -16 [-57, +25] (n.s.) | -9 [-51, +33] (n.s.) | -8 [-44, +28] (n.s.) | -35 [-414, +343] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 32%. Lost events: 0 in the window, 83 over the whole run (fixed-count tests included). hubble_* series at the end: 264.

| Class | flows/s | share |
|---|---|---|
| app | 38.2 | 73% |
| probe | 0.3 | 1% |
| client_feedback | 2.7 | 5% |
| other | 11.5 | 22% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.063 [+0.059, +0.068] cores. Standing (window before the snapshot) minus baseline observer: +0.062 cores; one snapshot adds 0.39 ± 0.41 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.241 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.037 [+0.025, +0.048] | +0.051 | +0.032 [-0.025, +0.089] (n.s.) | +0.20% / +0.18% | +54 [+32, +76] | +0.09% |
| Otterize | +0.070 [+0.062, +0.078] | +0.071 | +0.067 [+0.034, +0.099] | +0.39% / +0.37% | +126 [+81, +171] | +0.22% |
| IG trace_tcp | +0.135 [+0.128, +0.142] | +0.136 | +0.189 [+0.163, +0.215] | +0.75% / +1.05% | +359 [+267, +450] | +0.61% |
| IG snapshot_socket | +0.126 [+0.121, +0.130] | +0.122 | +0.153 [+0.105, +0.201] | +0.70% / +0.85% | +267 [+227, +307] | +0.46% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 4 | 0.10% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 52.11 |
| 2 | baseline | 5 | 0.01% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 47.15 |
| 3 | baseline | 3 | 0.06% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 49.68 |
| 4 | baseline | 5 | 0.10% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 49.86 |
| 5 | baseline | 2 | 0.17% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 57.26 |
| 6 | baseline | 1 | 0.67% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 45.61 |
| 7 | baseline | 3 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 46.91 |
| 8 | baseline | 2 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 48.59 |
| 9 | baseline | 1 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 46.76 |
| 10 | baseline | 4 | 0.44% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 49.33 |
| 1 | Hubble | 2 | 0.12% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 57.71 |
| 2 | Hubble | 3 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 63.17 |
| 3 | Hubble | 1 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 57.03 |
| 4 | Hubble | 4 | 0.05% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 66.01 |
| 5 | Hubble | 1 | 0.26% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 56.85 |
| 6 | Hubble | 3 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 56.78 |
| 7 | Hubble | 5 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 34.96 |
| 8 | Hubble | 4 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 60.58 |
| 9 | Hubble | 2 | 0.04% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 55.32 |
| 10 | Hubble | 5 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 60.29 |
| 1 | Otterize | 1 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 25.46 |
| 2 | Otterize | 1 | 0.18% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 47.45 |
| 3 | Otterize | 2 | 0.19% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 25.44 |
| 4 | Otterize | 2 | 0.32% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 46.47 |
| 5 | Otterize | 3 | 0.04% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 45.32 |
| 6 | Otterize | 5 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 44.68 |
| 7 | Otterize | 4 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 47.61 |
| 8 | Otterize | 5 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 46.15 |
| 9 | Otterize | 4 | 0.11% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 25.41 |
| 10 | Otterize | 3 | 0.04% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 50.31 |
| 1 | IG trace_tcp | 3 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 47.87 |
| 2 | IG trace_tcp | 2 | 0.09% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 46.83 |
| 3 | IG trace_tcp | 4 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 52.72 |
| 4 | IG trace_tcp | 1 | 0.07% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 49.62 |
| 5 | IG trace_tcp | 5 | 0.25% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 46.71 |
| 6 | IG trace_tcp | 4 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 49.52 |
| 7 | IG trace_tcp | 2 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 47.44 |
| 8 | IG trace_tcp | 3 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 47.88 |
| 9 | IG trace_tcp | 5 | 0.08% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 54.76 |
| 10 | IG trace_tcp | 1 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 47.98 |
| 1 | IG snapshot_socket | 5 | 0.49% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 45.82 |
| 2 | IG snapshot_socket | 4 | 0.04% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 44.07 |
| 3 | IG snapshot_socket | 5 | 0.23% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 58.20 |
| 4 | IG snapshot_socket | 3 | 0.06% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 45.74 |
| 5 | IG snapshot_socket | 4 | 0.06% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 51.67 |
| 6 | IG snapshot_socket | 2 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 46.02 |
| 7 | IG snapshot_socket | 1 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 52.42 |
| 8 | IG snapshot_socket | 1 | 0.02% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 46.80 |
| 9 | IG snapshot_socket | 3 | 0.03% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 51.77 |
| 10 | IG snapshot_socket | 2 | 0.10% | 6ac1c9b633e2d67d2b6515f5 | 1093e4be,ad371274,2bf5a955 | 43.61 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 12.07/7.82 | 12.34/7.87 | 12.27/9.95 | 12.33/8.93 | 1.21 |
| 1 | Hubble | 7.44/8.15 | 8.33/8.28 | 11.01/9.68 | 11.47/9.47 | 0.99 |
| 1 | Otterize | 8.35/8.55 | 8.11/8.15 | 10.01/10.35 | 9.30/10.76 | 0.97 |
| 1 | IG trace_tcp | 8.19/8.58 | 7.72/8.19 | 9.68/11.86 | 7.71/11.50 | 0.95 |
| 1 | IG snapshot_socket | 9.18/8.40 | 10.18/10.53 | 10.48/11.80 | 9.94/12.07 | 1.23 |
| 2 | baseline | 7.71/7.92 | 8.05/9.00 | 10.65/10.77 | 9.42/9.10 | 1.02 |
| 2 | Hubble | 13.64/13.62 | 8.30/8.82 | 10.82/9.69 | 11.33/9.98 | 1.02 |
| 2 | Otterize | 7.76/7.44 | 8.38/8.32 | 9.91/9.93 | 8.42/12.03 | 1.00 |
| 2 | IG trace_tcp | 7.95/10.31 | 8.17/9.90 | 10.12/11.38 | 12.41/11.66 | 1.08 |
| 2 | IG snapshot_socket | 9.11/7.46 | 8.52/7.67 | 10.27/10.54 | 15.07/8.51 | 0.96 |
| 3 | baseline | 8.59/8.04 | 8.32/8.26 | 10.36/8.87 | 8.11/11.72 | 0.99 |
| 3 | Hubble | 7.12/9.45 | 7.89/9.18 | 10.11/11.67 | 11.38/13.02 | 1.02 |
| 3 | Otterize | 7.37/8.28 | 8.03/8.79 | 11.57/11.66 | 10.48/9.72 | 1.00 |
| 3 | IG trace_tcp | 10.44/8.77 | 10.83/8.97 | 12.04/11.91 | 10.41/10.48 | 1.18 |
| 3 | IG snapshot_socket | 8.86/8.01 | 8.47/8.59 | 11.48/10.75 | 8.82/10.03 | 1.02 |
| 4 | baseline | 8.05/7.50 | 7.95/7.85 | 8.97/11.21 | 8.72/12.11 | 0.94 |
| 4 | Hubble | 9.05/9.18 | 8.19/8.35 | 11.54/11.42 | 11.21/10.67 | 0.99 |
| 4 | Otterize | 8.50/7.49 | 11.74/9.24 | 12.67/9.28 | 10.71/11.29 | 1.25 |
| 4 | IG trace_tcp | 10.52/9.41 | 9.35/8.52 | 11.38/9.49 | 9.27/12.66 | 1.06 |
| 4 | IG snapshot_socket | 8.13/9.72 | 8.26/8.69 | 10.58/13.19 | 10.90/13.99 | 1.01 |
| 5 | baseline | 8.22/7.57 | 8.31/9.02 | 10.94/12.75 | 10.80/10.29 | 1.03 |
| 5 | Hubble | 8.35/8.31 | 8.79/8.35 | 11.32/10.59 | 11.65/11.53 | 1.02 |
| 5 | Otterize | 9.86/9.97 | 7.80/8.69 | 10.62/11.99 | 8.43/9.92 | 0.98 |
| 5 | IG trace_tcp | 9.04/7.76 | 9.87/8.31 | 11.27/10.02 | 13.68/9.43 | 1.08 |
| 5 | IG snapshot_socket | 8.79/7.28 | 8.54/8.13 | 11.61/9.76 | 9.02/10.12 | 0.99 |
| 6 | baseline | 8.50/10.79 | 9.34/9.91 | 11.76/9.96 | 12.09/10.96 | 1.15 |
| 6 | Hubble | 8.32/8.73 | 8.40/8.89 | 8.95/11.44 | 10.16/9.80 | 1.03 |
| 6 | Otterize | 9.02/9.73 | 8.74/8.84 | 11.26/11.67 | 11.70/10.92 | 1.05 |
| 6 | IG trace_tcp | 8.12/7.19 | 8.38/7.98 | 10.50/11.08 | 11.00/9.90 | 0.98 |
| 6 | IG snapshot_socket | 7.39/7.11 | 7.95/7.64 | 9.37/9.74 | 10.01/9.63 | 0.93 |
| 7 | baseline | 8.11/8.56 | 8.44/9.37 | 11.02/12.24 | 10.44/11.37 | 1.06 |
| 7 | Hubble | 8.06/7.21 | 8.28/8.03 | 10.73/11.51 | 10.14/9.08 | 0.97 |
| 7 | Otterize | 8.78/8.29 | 8.82/9.13 | 10.89/10.64 | 10.12/10.24 | 1.07 |
| 7 | IG trace_tcp | 8.34/9.51 | 8.27/9.00 | 9.19/9.80 | 11.77/11.49 | 1.03 |
| 7 | IG snapshot_socket | 7.93/10.59 | 8.07/10.44 | 9.67/12.78 | 8.66/11.46 | 1.10 |
| 8 | baseline | 8.39/8.77 | 8.02/8.55 | 10.31/9.48 | 8.99/9.86 | 0.99 |
| 8 | Hubble | 9.20/7.69 | 9.09/7.93 | 13.14/9.22 | 10.06/10.53 | 1.01 |
| 8 | Otterize | 8.11/7.32 | 7.80/8.06 | 9.25/9.90 | 10.90/12.07 | 0.94 |
| 8 | IG trace_tcp | 8.68/8.08 | 9.05/8.01 | 11.67/12.27 | 8.86/10.08 | 1.02 |
| 8 | IG snapshot_socket | 7.62/9.15 | 7.74/8.82 | 9.35/12.65 | 8.67/12.21 | 0.99 |
| 9 | baseline | 8.95/7.28 | 8.59/8.28 | 10.85/10.82 | 10.21/9.66 | 1.01 |
| 9 | Hubble | 7.72/7.72 | 8.02/7.82 | 10.77/12.31 | 11.24/11.59 | 0.94 |
| 9 | Otterize | 7.82/7.37 | 7.88/7.47 | 9.79/9.21 | 9.29/10.07 | 0.91 |
| 9 | IG trace_tcp | 9.15/8.37 | 9.14/8.92 | 10.07/11.39 | 9.86/10.21 | 1.08 |
| 9 | IG snapshot_socket | 12.32/8.92 | 12.43/9.09 | 13.99/10.66 | 14.20/10.33 | 1.28 |
| 10 | baseline | 6.89/7.21 | 8.08/7.74 | 9.69/9.39 | 9.32/10.04 | 0.94 |
| 10 | Hubble | 11.71/11.07 | 8.56/7.95 | 12.78/9.57 | 10.15/10.22 | 0.98 |
| 10 | Otterize | 7.38/7.89 | 8.27/7.58 | 10.49/10.19 | 9.89/9.23 | 0.94 |
| 10 | IG trace_tcp | 8.35/7.98 | 8.38/8.34 | 11.41/10.08 | 9.66/11.09 | 1.00 |
| 10 | IG snapshot_socket | 7.78/7.73 | 11.94/12.33 | 11.31/14.60 | 13.30/13.86 | 1.45 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 62.14 ± 7.34 (n=10) | 61.10 ± 11.08 (n=10) | -0.18% [-16.37, +16.01] (n.s.) (< 16.0% at 95%) | 0.980 | 1.000 |
| keepalive | Otterize | 62.14 ± 7.34 (n=10) | 50.43 ± 13.81 (n=10) | -18.03% [-35.08, -0.98] | 0.040 | 0.162 |
| keepalive | IG trace_tcp | 62.14 ± 7.34 (n=10) | 62.27 ± 5.72 (n=10) | +1.68% [-10.24, +13.60] (n.s.) (< 13.6% at 95%) | 0.757 | 1.000 |
| keepalive | IG snapshot_socket | 62.14 ± 7.34 (n=10) | 65.20 ± 8.04 (n=10) | +6.06% [-6.35, +18.47] (n.s.) (< 18.5% at 95%) | 0.298 | 0.893 |
| newconn | Hubble | 60.09 ± 5.94 (n=10) | 72.99 ± 12.80 (n=10) | +22.70% [+4.48, +40.93] | 0.020 | 0.080 |
| newconn | Otterize | 60.09 ± 5.94 (n=10) | 49.70 ± 13.97 (n=10) | -16.30% [-34.98, +2.38] (n.s.) (< 2.4% at 95%) | 0.080 | 0.240 |
| newconn | IG trace_tcp | 60.09 ± 5.94 (n=10) | 62.29 ± 4.74 (n=10) | +4.60% [-5.00, +14.20] (n.s.) (< 14.2% at 95%) | 0.306 | 0.473 |
| newconn | IG snapshot_socket | 60.09 ± 5.94 (n=10) | 63.51 ± 6.48 (n=10) | +6.94% [-5.45, +19.33] (n.s.) (< 19.3% at 95%) | 0.237 | 0.473 |

## Excluded runs

None.

## Data warnings in used runs

| App | Rep | Condition | Warning |
|---|---|---|---|
| teastore | 1 | hubble | Hubble lost 84 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 10 | hubble | Hubble lost 85 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 2 | hubble | Hubble lost 86 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 3 | hubble | Hubble lost 84 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 4 | hubble | Hubble lost 89 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 5 | hubble | Hubble lost 82 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 6 | hubble | Hubble lost 83 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 7 | hubble | Hubble lost 70 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 8 | hubble | Hubble lost 86 events during the run (ring buffer), 0 of them in the steady window |
| teastore | 9 | hubble | Hubble lost 82 events during the run (ring buffer), 0 of them in the steady window |

## Method notes

- Observer CPU and memory include cilium-agent, cilium-envoy and cilium-operator in every condition, so the baseline row is not zero. The Δ columns are the cost of the technique.
- Cluster busy CPU comes from /proc/stat on each node (user + nice + system + irq + softirq; steal and iowait left out). It also catches indirect costs: API-server and kubelet work for `kubectl port-forward` and `kubectl gadget` streams, exec probes of the gadget DaemonSet, and BPF work in the app's syscalls or in softirq. The kernel here has CONFIG_IRQ_TIME_ACCOUNTING off, so softirq time is charged to whatever task it interrupts.
- The fixed-count time is the tool's own total (hey `Total`), so pod start-up is not in it.
- The steady-window per-flow cost is not reported: the journey-A load keeps connections open, so almost every new connection in the window is a kubelet probe. Per-request and per-connection costs come from the fixed-count tests.
- Events/s for Hubble and IG count client events whose event time falls inside the analysis window (client_bins.json), so both use the same window and the app namespace only.
- The projection is an estimate with two known gaps: no platform background traffic, and a different CPU model and kernel (6.12 here, 6.8 on test-cluster).
- Host-speed canary (bin/canary.py): every 2 s each node runs a fixed pure-Python integer loop and logs its thread CPU time. Iterations per CPU-second is the host speed index; it falls when the hypervisor gives the guest less work per CPU-second (unreported steal, a busy sibling thread, a lower clock). Normalised CPU = cores x speed / the app's median speed (per node); normalised fixed-count time = time x the workers' speed ratio during the test. The canary costs about 1% of one core per node and is counted as harness.
