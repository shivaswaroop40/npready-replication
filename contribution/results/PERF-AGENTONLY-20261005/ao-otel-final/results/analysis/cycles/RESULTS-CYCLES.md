# Capture overhead: interleaved cycles (randomized multiple interleaved trials)

Generated 2026-10-06 03:12 UTC by analyze/analyze.py from `/Users/shiv/Desktop/code/MasterThesis/contribution/perf-benchmark/../results/PERF-AGENTONLY-20261005/ao-otel-final/results`. 36 run directories, 36 used, 0 excluded.

## Setup

- Cluster: iximiuz play, k3s, Cilium 1.19.5 configured like test-cluster. cp-01 has 2 vCPU and runs the load generator and the capture clients. worker-01 and worker-02 have 4 vCPU each and run the app.
- Conditions: baseline (Cilium, Hubble off, no other observer), Hubble (agent Hubble on, Relay, `hubble observe` through `kubectl port-forward` as in the thesis), Otterize (mapper and sniffers), IG trace_tcp (gadget DaemonSet and a streaming client), IG snapshot_socket (gadget DaemonSet and one snapshot near the end of the window). A metrics scraper fetches :9962, :9963 and :9965 every 15 s in every condition, like test-cluster' Prometheus.
- Each run: fresh Cilium agents and app pods, a 60 s idle segment (observer on, no load), 60 s warm-up, a 300 s steady window with the thesis journey-A load, then the fixed-count tests (7040 requests, concurrency 16, 1 repeats per mode, keep-alive and new connection per request).
- Order: K short cycles, each running every condition once; the order of cycle k is sequence k of a Williams design for 5 conditions (10 sequences: every condition twice in every position, every ordered pair of conditions adjacent twice), cycles 11-20 the same set in a fresh seeded order. Pairing within a cycle cancels host drift slower than a cycle (about an hour); the design spreads faster drift evenly over the conditions (Abedi and Brecht, ICPE 2017). A host-speed canary on every node gives the canary-normalised columns. CPU and memory come from cgroup counters sampled every 5 s on every node.
- The analysis uses the steady window minus its first 15 s and last 10 s.

## How to read the tables

- Each cycle is a block: every Δ is the mean of the per-cycle differences (technique minus the same cycle's baseline), with a t-based 95% CI (df = cycles - 1) in brackets; with 12 cycles the t quantile is 2.20. In the standard tables 'rep' means cycle. The first table of each app gives every endpoint raw and canary-normalised, with Holm across the techniques; the drift diagnostic shows whether the host moved during the matrix.
- "n.s." means the 95% CI includes 0. For a fixed-count overhead the upper CI bound is then given as the most the overhead can be.
- Primary endpoints (Holm-adjusted per app over 4 techniques x 4 endpoints): Δ cluster busy CPU, Δ observer memory, fixed-count time keep-alive and new connection. All other p-values are exploratory and unadjusted. Welch's test on the run values is in the CSVs as a second check.
- Δ is the technique minus the baseline. A negative Δ is noise or a side effect, not a saving.
- Transferable numbers: Δ cores, Δ MiB, Δ % of capacity, the fixed-count overhead and the projection. A percentage of this bench's baseline is not transferable to test-cluster, whose baseline carried the whole platform.

## Summary across apps

Per-app values, grouped by what limits the fixed-count test (quota-bound: throttled app containers; node-bound: node CPU). Steady-window latency is left out of the summary: it is bucket-limited and the steady load is a controlled input.

| Technique | Regime | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn | test-cluster CPU, % of 18 vCPU (est.) |
|---|---|---|---|---|---|---|
| Hubble | node-bound | otel +0.067 | otel +0.83% | otel +11.9% n.s. | otel +20.1% | otel +0.37% |
| Hubble (agent only) | node-bound | otel +0.017 | otel +0.10% n.s. | otel +6.1% n.s. | otel +7.8% n.s. | otel +0.16% |

Diagnostic only, do not quote: the same, canary-normalised (each run scaled to the app's median canary speed). The 2026-10-03 validation showed the canary does not track the host drift (r 0.41, normalised CV 16.4% vs 16.6% raw) and inflates deltas 1.7-4.7x. The raw paired deltas above, over interleaved cycles, are the result.

| Technique | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn |
|---|---|---|---|---|
| Hubble | otel +0.066 | otel +0.74% | otel +12.0% n.s. | otel +20.0% |
| Hubble (agent only) | otel +0.015 | otel -0.02% n.s. | otel +7.4% n.s. | otel +10.2% n.s. |

## otel

Runs used: baseline 12, Hubble 12, Hubble (agent only) 12.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.20 at 12 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.083 [+0.070, +0.097] | <0.001 | <0.001 | +0.074 [+0.038, +0.110] | <0.001 | 0.002 | 12 |
| Δ cluster busy CPU (cores) | Hubble (agent only) | +0.010 [-0.010, +0.030] (n.s.) | 0.291 | 0.291 | -0.002 [-0.037, +0.034] (n.s.) | 0.920 | 0.920 | 12 |
| Δ observer CPU (cores) | Hubble | +0.067 [+0.063, +0.071] | <0.001 | <0.001 | +0.066 [+0.060, +0.072] | <0.001 | <0.001 | 12 |
| Δ observer CPU (cores) | Hubble (agent only) | +0.017 [+0.014, +0.020] | <0.001 | <0.001 | +0.015 [+0.010, +0.019] | <0.001 | <0.001 | 12 |
| Δ app CPU (cores) | Hubble | -0.004 [-0.009, +0.001] (n.s.) | 0.126 | 0.251 | -0.013 [-0.033, +0.008] (n.s.) | 0.195 | 0.390 | 12 |
| Δ app CPU (cores) | Hubble (agent only) | -0.000 [-0.007, +0.007] (n.s.) | 0.977 | 0.977 | -0.005 [-0.027, +0.017] (n.s.) | 0.620 | 0.620 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.035 [+0.029, +0.040] | <0.001 | <0.001 | +0.034 [+0.023, +0.044] | <0.001 | <0.001 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble (agent only) | +0.001 [-0.005, +0.007] (n.s.) | 0.744 | 0.744 | -0.003 [-0.013, +0.008] (n.s.) | 0.561 | 0.561 | 12 |
| Δ observer anon memory (MiB, primary) | Hubble | +113 [+109, +117] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer anon memory (MiB, primary) | Hubble (agent only) | +46 [+44, +49] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble | +121 [+111, +131] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble (agent only) | +58 [+42, +73] | <0.001 | <0.001 | - | - | - | 12 |
| fixed-count time, keep-alive | Hubble | +11.9% [-3.1, +26.9] (n.s.) | 0.108 | 0.216 | +12.0% [-2.8, +26.8] (n.s.) | 0.102 | 0.205 | 12 |
| fixed-count time, keep-alive | Hubble (agent only) | +6.1% [-13.6, +25.9] (n.s.) | 0.508 | 0.508 | +7.4% [-9.5, +24.3] (n.s.) | 0.357 | 0.357 | 12 |
| fixed-count time, new conn | Hubble | +20.1% [+6.7, +33.4] | 0.007 | 0.014 | +20.0% [+4.1, +35.9] | 0.018 | 0.037 | 12 |
| fixed-count time, new conn | Hubble (agent only) | +7.8% [-12.0, +27.6] (n.s.) | 0.406 | 0.406 | +10.2% [-9.1, +29.5] (n.s.) | 0.270 | 0.270 | 12 |
| canary speed, workers, steady window (check) | Hubble | -3.95% [-8.97, +1.06] (n.s.) | 0.111 | 0.222 | - | - | - | 12 |
| canary speed, workers, steady window (check) | Hubble (agent only) | -3.43% [-9.45, +2.58] (n.s.) | 0.235 | 0.235 | - | - | - | 12 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 16.6% raw, 15.6% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.38; new conn: CV of the baseline time across cycles 12.8% raw, 15.8% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.35.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-05 19:12 | hubble_agent hubble baseline | 40.7 | 59.1 | 49.8 | 65.8 | 0.252 | 0.278 | 8.84 | 1.06 | 8.47 |
| 2 | 10-05 19:47 | baseline hubble_agent hubble | 36.9 | 56.8 | 52.9 | 78.5 | 0.255 | 0.248 | 8.08 | 0.97 | 8.31 |
| 3 | 10-05 20:33 | hubble_agent baseline hubble | 31.6 | 45.8 | 34.1 | 48.0 | 0.251 | 0.268 | 9.35 | 1.12 | 8.57 |
| 4 | 10-05 21:07 | baseline hubble hubble_agent | 42.2 | 63.8 | 43.8 | 61.8 | 0.249 | 0.251 | 9.28 | 1.11 | 8.99 |
| 5 | 10-05 21:42 | hubble hubble_agent baseline | 41.6 | 61.4 | 48.5 | 71.7 | 0.250 | 0.265 | 8.92 | 1.07 | 9.06 |
| 6 | 10-05 22:17 | hubble baseline hubble_agent | 48.6 | 71.7 | 53.9 | 80.7 | 0.237 | 0.253 | 8.91 | 1.07 | 8.54 |
| 7 | 10-05 23:03 | hubble_agent baseline hubble | 32.5 | 48.3 | 46.4 | 62.9 | 0.251 | 0.241 | 7.96 | 0.95 | 8.17 |
| 8 | 10-05 23:50 | hubble hubble_agent baseline | 28.7 | 44.5 | 40.6 | 52.6 | 0.257 | 0.259 | 8.14 | 0.97 | 8.35 |
| 9 | 10-06 00:24 | hubble baseline hubble_agent | 30.9 | 47.5 | 37.6 | 51.8 | 0.261 | 0.334 | 10.10 | 1.21 | 8.65 |
| 10 | 10-06 00:59 | baseline hubble_agent hubble | 43.0 | 51.9 | 47.5 | 64.1 | 0.255 | 0.271 | 8.67 | 1.04 | 8.71 |
| 11 | 10-06 01:45 | baseline hubble hubble_agent | 31.7 | 50.2 | 46.9 | 70.1 | 0.273 | 0.255 | 8.27 | 0.99 | 8.20 |
| 12 | 10-06 02:31 | hubble_agent hubble baseline | 39.9 | 63.5 | 45.5 | 70.5 | 0.262 | 0.249 | 8.13 | 0.97 | 7.75 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Hubble (agent only); that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.067 [+0.063, +0.071] | <0.001 | +0.066 | <0.001 | +0.067 [+0.063, +0.071] | 12 | robust |
| Δ observer CPU | Hubble (agent only) | +0.017 [+0.014, +0.020] | <0.001 | +0.017 | <0.001 | +0.017 [+0.013, +0.020] | 11 | robust |
| Δ observer anon memory | Hubble | +113 [+109, +117] | <0.001 | +113 | <0.001 | +113 [+109, +117] | 12 | robust |
| Δ observer anon memory | Hubble (agent only) | +46 [+44, +49] | <0.001 | +46 | <0.001 | +46 [+44, +49] | 11 | robust |
| fixed-count time, keep-alive | Hubble | +11.9% [-3.1, +26.9] (n.s.) | 0.323 | +7.1% | 0.151 | +11.9% [-3.1, +26.9] (n.s.) | 12 | n.s. (primary) |
| fixed-count time, keep-alive | Hubble (agent only) | +6.1% [-13.6, +25.9] (n.s.) | 0.813 | +5.5% | 0.622 | +5.9% [-15.9, +27.8] (n.s.) | 11 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +20.1% [+6.7, +33.4] | 0.028 | +13.7% | 0.007 | +20.1% [+6.7, +33.4] | 12 | robust |
| fixed-count time, new conn | Hubble (agent only) | +7.8% [-12.0, +27.6] (n.s.) | 0.813 | +6.9% | 0.519 | +7.9% [-14.0, +29.9] (n.s.) | 11 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 7040 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **node-bound** (baseline newconn bottleneck throttled 0.00 s/s), so node CPU limits the test. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 37.34 ± 6.20 (n=12) | 41.05 ± 7.11 (n=12) | +11.94% [-3.07, +26.94] (n.s.) (< 26.9% at 95%) | 0.108 | 0.323 | opentelemetry-demo-currencyservice 0.00 | 0.00 |
| keepalive | Hubble (agent only) | 37.34 ± 6.20 (n=12) | 38.16 ± 6.95 (n=12) | +6.13% [-13.60, +25.85] (n.s.) (< 25.9% at 95%) | 0.508 | 0.813 | opentelemetry-demo-frontend 0.00 | 0.00 |
| newconn | Hubble | 45.62 ± 5.86 (n=12) | 53.85 ± 5.24 (n=12) | +20.09% [+6.74, +33.43] | 0.007 | 0.028 | opentelemetry-demo-currencyservice 0.00 | 1.00 |
| newconn | Hubble (agent only) | 45.62 ± 5.86 (n=12) | 47.81 ± 9.69 (n=12) | +7.78% [-12.05, +27.61] (n.s.) (< 27.6% at 95%) | 0.406 | 0.813 | opentelemetry-demo-frontend 0.00 | 1.00 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 37.34 ± 6.20 | 16.60% | 16.60% | 12 |
| newconn | 45.62 ± 5.86 | 12.84% | 12.84% | 12 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.079 ± 0.005 | 0.008 | - | 0.562 ± 0.025 | 0.052 | - | - | - | - |
| Hubble | 0.146 ± 0.008 | 0.016 | +0.067 [+0.063, +0.071] | 0.646 ± 0.029 | 0.064 | +0.083 [+0.070, +0.097] | +0.83% | +0.035 | <0.001 / <0.001 |
| Hubble (agent only) | 0.096 ± 0.006 | 0.009 | +0.017 [+0.014, +0.020] | 0.572 ± 0.033 | 0.052 | +0.010 [-0.010, +0.030] (n.s.) | +0.10% | +0.001 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.053 [+0.048, +0.057] | +0.030 [+0.024, +0.037] | +0.075 [+0.063, +0.086] | 79% |
| Hubble (agent only) | +0.011 [+0.008, +0.014] | -0.002 [-0.008, +0.004] (n.s.) | +0.003 [-0.014, +0.019] (n.s.) | 67% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.038 [+0.035, +0.041] | +0.403 [-0.150, +0.957] (n.s.) | +0.023 [+0.006, +0.041] | 0.00 → 0.00 | 11% |
| keepalive | Hubble (agent only) | +0.007 [+0.004, +0.010] | +0.173 [-0.451, +0.796] (n.s.) | +0.004 [-0.014, +0.022] (n.s.) | 0.00 → 0.00 | 10% |
| newconn | Hubble | +0.772 [+0.726, +0.817] | +0.944 [+0.036, +1.852] | +0.329 [+0.300, +0.357] | 0.00 → 0.00 | 43% |
| newconn | Hubble (agent only) | +0.150 [+0.139, +0.162] | -0.112 [-0.852, +0.628] (n.s.) | -0.007 [-0.023, +0.009] (n.s.) | 0.00 → 0.00 | 18% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 663 ± 16 | 2.7 | 1.41 | 375 | - | - | 4776 ± 46 | - | - |
| Hubble | 785 ± 28 (peak 795) | 6.8 | 4.75 | 488 | +113 [+109, +117] | +121 [+111, +131] | 4921 ± 41 | +0.71% | <0.001 / <0.001 |
| Hubble (agent only) | 721 ± 35 (peak 730) | 5.4 | 3.54 | 421 | +46 [+44, +49] | +58 [+42, +73] | 4827 ± 54 | +0.29% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Hubble (agent only) |
|---|---|---|---|
| cilium-agent | 0.068 | 0.096 | 0.085 |
| cilium-envoy | 0.008 | 0.007 | 0.008 |
| cilium-operator | 0.004 | 0.003 | 0.004 |
| hubble-relay | 0.000 | 0.018 | 0.000 |
| client-hubble | 0.000 | 0.021 | 0.000 |
| app | 0.254 | 0.250 | 0.254 |
| loadgen | 0.028 | 0.028 | 0.028 |
| k3s | 0.169 | 0.204 | 0.170 |
| k8s-addons | 0.009 | 0.009 | 0.009 |
| os | 0.001 | 0.001 | 0.001 |
| harness | 0.033 | 0.034 | 0.034 |
| node | 0.562 | 0.646 | 0.572 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 17.00 ± 0.17 | 6.2 ± 0.4 | - | 19.2 ± 0.5 | - | 24.4 ± 0.5 | - | 0.00 |
| Hubble | 16.89 ± 0.24 | 6.2 ± 0.4 | +0.0% [+0.0, +0.0] (n.s.) | 19.2 ± 0.5 | +0.0% [-1.4, +1.4] (n.s.) | 24.3 ± 0.8 | -0.3% [-2.9, +2.3] (n.s.) | 0.00 |
| Hubble (agent only) | 16.92 ± 0.15 | 6.1 ± 0.5 | -1.2% [-6.4, +4.0] (n.s.) | 19.4 ± 0.7 | +0.9% [-1.1, +2.8] (n.s.) | 24.8 ± 0.6 | +1.4% [-0.6, +3.4] (n.s.) | 0.00 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 0.2 | 0.22 | 0.02 | - | - | - | - | - |
| Hubble | 0.4 | 0.42 | 0.02 | -104 [-145, -64] | +5656 [+5489, +5824] | +5655 [+5488, +5823] | +12359 [+4152, +20565] | 60.7 (thesis 72.3) |
| Hubble (agent only) | 0.2 | 0.22 | 0.02 | -23 [-47, +1] (n.s.) | +966 [+901, +1031] | +966 [+901, +1031] | +784 [-7967, +9534] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 45%. Lost events: 0 in the window, 69 over the whole run (fixed-count tests included). hubble_* series at the end: 446.

| Class | flows/s | share |
|---|---|---|
| app | 60.0 | 79% |
| probe | 1.8 | 2% |
| client_feedback | 2.7 | 3% |
| other | 11.6 | 15% |

### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about - cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.067 [+0.062, +0.072] | +0.072 | +0.116 [+0.094, +0.138] | +0.37% / +0.64% | +85 [+74, +96] | +0.15% |
| Hubble (agent only) | +0.028 [+0.023, +0.034] | +0.034 | +0.016 [-0.016, +0.048] (n.s.) | +0.16% / +0.09% | +83 [+35, +131] | +0.14% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 3 | 0.04% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 49.84 |
| 2 | baseline | 1 | 0.04% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 52.85 |
| 3 | baseline | 2 | 0.05% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 34.12 |
| 4 | baseline | 1 | 0.06% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 43.84 |
| 5 | baseline | 3 | 0.06% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 48.51 |
| 6 | baseline | 2 | 0.38% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 53.87 |
| 7 | baseline | 2 | 0.06% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 46.38 |
| 8 | baseline | 3 | 0.04% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 40.58 |
| 9 | baseline | 2 | 0.05% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 37.58 |
| 10 | baseline | 1 | 0.06% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 47.49 |
| 11 | baseline | 1 | 0.06% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 46.88 |
| 12 | baseline | 3 | 0.06% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 45.47 |
| 1 | Hubble | 2 | 0.04% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 54.82 |
| 2 | Hubble | 3 | 0.22% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 52.20 |
| 3 | Hubble | 3 | 0.07% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 54.72 |
| 4 | Hubble | 2 | 0.07% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 55.27 |
| 5 | Hubble | 1 | 0.07% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 56.85 |
| 6 | Hubble | 1 | 0.08% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 59.39 |
| 7 | Hubble | 3 | 0.04% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 46.02 |
| 8 | Hubble | 1 | 0.05% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 59.78 |
| 9 | Hubble | 1 | 0.05% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 51.83 |
| 10 | Hubble | 3 | 0.70% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 51.73 |
| 11 | Hubble | 2 | 0.04% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 43.37 |
| 12 | Hubble | 2 | 0.04% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 60.25 |
| 1 | Hubble (agent only) | 1 | 0.06% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 52.85 |
| 2 | Hubble (agent only) | 2 | 0.03% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 34.89 |
| 3 | Hubble (agent only) | 1 | 0.08% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 51.21 |
| 4 | Hubble (agent only) | 3 | 0.05% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 64.41 |
| 5 | Hubble (agent only) | 2 | 0.05% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 52.23 |
| 6 | Hubble (agent only) | 3 | 0.07% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 39.46 |
| 7 | Hubble (agent only) | 1 | 0.03% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 56.45 |
| 8 | Hubble (agent only) | 2 | 0.03% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 45.34 |
| 9 | Hubble (agent only) | 3 | 0.03% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 58.87 |
| 10 | Hubble (agent only) | 2 | 0.04% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 35.26 |
| 11 | Hubble (agent only) | 3 | 0.06% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 44.57 |
| 12 | Hubble (agent only) | 1 | 0.05% | 6ac3f54ecde73a52e44b793f | 557c9d3a,53646b0c,6f764d5f | 38.18 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 7.68/7.31 | 9.31/8.37 | 13.11/11.16 | 12.68/9.35 | 1.06 |
| 1 | Hubble | 8.15/7.26 | 8.32/8.71 | 13.00/12.63 | 12.67/11.41 | 1.02 |
| 1 | Hubble (agent only) | 7.14/7.88 | 8.12/7.97 | 13.85/10.37 | 12.51/10.09 | 0.96 |
| 2 | baseline | 7.52/7.80 | 7.88/8.27 | 14.01/11.73 | 13.62/11.18 | 0.97 |
| 2 | Hubble | 7.48/6.97 | 7.85/8.67 | 11.82/11.24 | 10.38/12.44 | 0.99 |
| 2 | Hubble (agent only) | 7.19/7.90 | 8.27/8.94 | 13.15/10.70 | 12.50/11.64 | 1.03 |
| 3 | baseline | 7.42/9.22 | 7.90/10.80 | 11.39/12.86 | 10.86/12.67 | 1.12 |
| 3 | Hubble | 7.29/7.29 | 7.77/8.26 | 11.44/13.47 | 11.66/12.48 | 0.96 |
| 3 | Hubble (agent only) | 6.99/7.51 | 8.55/8.17 | 12.26/11.78 | 13.03/10.80 | 1.00 |
| 4 | baseline | 9.26/6.92 | 10.64/7.92 | 11.44/13.84 | 10.75/12.80 | 1.11 |
| 4 | Hubble | 7.27/7.45 | 9.10/8.86 | 12.66/14.09 | 10.19/12.30 | 1.08 |
| 4 | Hubble (agent only) | 7.70/7.99 | 8.86/8.54 | 13.68/13.37 | 11.81/11.72 | 1.04 |
| 5 | baseline | 7.95/8.28 | 9.05/8.79 | 12.54/12.13 | 11.43/13.29 | 1.07 |
| 5 | Hubble | 7.48/8.69 | 8.37/10.20 | 14.04/11.53 | 13.05/10.70 | 1.11 |
| 5 | Hubble (agent only) | 7.38/7.23 | 9.37/8.61 | 12.85/11.40 | 14.09/11.20 | 1.08 |
| 6 | baseline | 7.16/7.83 | 8.80/9.01 | 12.95/11.69 | 13.20/11.83 | 1.07 |
| 6 | Hubble | 7.06/7.53 | 8.12/8.82 | 12.53/11.08 | 12.92/10.90 | 1.01 |
| 6 | Hubble (agent only) | 7.77/7.45 | 8.05/8.43 | 12.13/14.31 | 12.88/11.93 | 0.99 |
| 7 | baseline | 7.89/7.78 | 8.01/7.92 | 13.18/11.63 | 11.35/11.32 | 0.95 |
| 7 | Hubble | 8.37/8.21 | 7.57/8.15 | 11.96/12.52 | 11.43/11.29 | 0.94 |
| 7 | Hubble (agent only) | 7.42/8.37 | 8.96/8.43 | 14.69/11.80 | 12.12/12.15 | 1.04 |
| 8 | baseline | 8.53/8.80 | 7.54/8.74 | 11.52/14.43 | 10.52/11.16 | 0.97 |
| 8 | Hubble | 8.22/9.37 | 8.24/7.92 | 13.70/11.93 | 12.65/10.97 | 0.97 |
| 8 | Hubble (agent only) | 8.94/10.11 | 9.00/8.63 | 13.17/12.12 | 12.87/10.64 | 1.06 |
| 9 | baseline | 10.63/9.06 | 10.93/9.28 | 13.91/11.74 | 11.86/11.16 | 1.21 |
| 9 | Hubble | 6.82/7.91 | 7.37/8.56 | 11.33/12.38 | 10.93/12.35 | 0.95 |
| 9 | Hubble (agent only) | 8.47/8.03 | 8.25/7.53 | 10.01/12.86 | 9.84/12.06 | 0.94 |
| 10 | baseline | 9.46/8.21 | 9.12/8.21 | 10.30/9.90 | 11.55/11.01 | 1.04 |
| 10 | Hubble | 7.90/7.50 | 8.31/8.41 | 12.48/12.48 | 10.87/12.16 | 1.00 |
| 10 | Hubble (agent only) | 9.74/7.72 | 10.63/7.56 | 14.52/11.74 | 13.62/12.32 | 1.09 |
| 11 | baseline | 9.18/7.32 | 9.12/7.42 | 12.95/13.50 | 13.13/11.86 | 0.99 |
| 11 | Hubble | 6.79/9.61 | 7.54/10.28 | 11.60/13.37 | 10.79/12.47 | 1.06 |
| 11 | Hubble (agent only) | 7.24/7.56 | 7.09/7.75 | 13.46/11.98 | 13.69/12.48 | 0.89 |
| 12 | baseline | 7.09/7.39 | 8.51/7.76 | 14.37/12.20 | 13.98/11.93 | 0.97 |
| 12 | Hubble | 6.86/7.57 | 7.38/7.47 | 10.66/14.39 | 11.55/13.79 | 0.89 |
| 12 | Hubble (agent only) | 6.80/7.27 | 7.46/7.92 | 14.28/15.00 | 11.18/14.16 | 0.92 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 55.37 ± 8.61 (n=12) | 61.17 ± 11.48 (n=12) | +12.00% [-2.82, +26.82] (n.s.) (< 26.8% at 95%) | 0.102 | 0.205 |
| keepalive | Hubble (agent only) | 55.37 ± 8.61 (n=12) | 57.81 ± 9.04 (n=12) | +7.37% [-9.51, +24.25] (n.s.) (< 24.3% at 95%) | 0.357 | 0.357 |
| newconn | Hubble | 64.88 ± 10.28 (n=12) | 75.94 ± 9.11 (n=12) | +19.96% [+4.06, +35.85] | 0.018 | 0.037 |
| newconn | Hubble (agent only) | 64.88 ± 10.28 (n=12) | 69.07 ± 12.20 (n=12) | +10.19% [-9.13, +29.51] (n.s.) (< 29.5% at 95%) | 0.270 | 0.270 |

## Excluded runs

None.

## Data warnings in used runs

| App | Rep | Condition | Warning |
|---|---|---|---|
| otel | 1 | hubble | Hubble lost 69 events during the run (ring buffer), 0 of them in the steady window |
| otel | 10 | hubble | Hubble lost 67 events during the run (ring buffer), 0 of them in the steady window |
| otel | 11 | hubble | Hubble lost 66 events during the run (ring buffer), 0 of them in the steady window |
| otel | 12 | hubble | Hubble lost 72 events during the run (ring buffer), 0 of them in the steady window |
| otel | 2 | hubble | Hubble lost 69 events during the run (ring buffer), 0 of them in the steady window |
| otel | 3 | hubble | Hubble lost 69 events during the run (ring buffer), 0 of them in the steady window |
| otel | 4 | hubble | Hubble lost 69 events during the run (ring buffer), 0 of them in the steady window |
| otel | 5 | hubble | Hubble lost 70 events during the run (ring buffer), 0 of them in the steady window |
| otel | 6 | hubble | Hubble lost 71 events during the run (ring buffer), 0 of them in the steady window |
| otel | 7 | hubble | Hubble lost 66 events during the run (ring buffer), 0 of them in the steady window |
| otel | 8 | hubble | Hubble lost 71 events during the run (ring buffer), 0 of them in the steady window |
| otel | 9 | hubble | Hubble lost 67 events during the run (ring buffer), 0 of them in the steady window |

## Method notes

- Observer CPU and memory include cilium-agent, cilium-envoy and cilium-operator in every condition, so the baseline row is not zero. The Δ columns are the cost of the technique.
- Cluster busy CPU comes from /proc/stat on each node (user + nice + system + irq + softirq; steal and iowait left out). It also catches indirect costs: API-server and kubelet work for `kubectl port-forward` and `kubectl gadget` streams, exec probes of the gadget DaemonSet, and BPF work in the app's syscalls or in softirq. The kernel here has CONFIG_IRQ_TIME_ACCOUNTING off, so softirq time is charged to whatever task it interrupts.
- The fixed-count time is the tool's own total (hey `Total`), so pod start-up is not in it.
- The steady-window per-flow cost is not reported: the journey-A load keeps connections open, so almost every new connection in the window is a kubelet probe. Per-request and per-connection costs come from the fixed-count tests.
- Events/s for Hubble and IG count client events whose event time falls inside the analysis window (client_bins.json), so both use the same window and the app namespace only.
- The projection is an estimate with two known gaps: no platform background traffic, and a different CPU model and kernel (6.12 here, 6.8 on test-cluster).
- Host-speed canary (bin/canary.py): every 2 s each node runs a fixed pure-Python integer loop and logs its thread CPU time. Iterations per CPU-second is the host speed index; it falls when the hypervisor gives the guest less work per CPU-second (unreported steal, a busy sibling thread, a lower clock). Normalised CPU = cores x speed / the app's median speed (per node); normalised fixed-count time = time x the workers' speed ratio during the test. The canary costs about 1% of one core per node and is counted as harness.
