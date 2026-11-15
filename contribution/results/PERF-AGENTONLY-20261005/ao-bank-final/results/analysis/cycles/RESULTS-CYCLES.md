# Capture overhead: interleaved cycles (randomized multiple interleaved trials)

Generated 2026-10-06 01:25 UTC by analyze/analyze.py from `/Users/shiv/Desktop/code/MasterThesis/contribution/perf-benchmark/../results/PERF-AGENTONLY-20261005/ao-bank-final/results`. 36 run directories, 36 used, 0 excluded.

## Setup

- Cluster: iximiuz play, k3s, Cilium 1.19.5 configured like test-cluster. cp-01 has 2 vCPU and runs the load generator and the capture clients. worker-01 and worker-02 have 4 vCPU each and run the app.
- Conditions: baseline (Cilium, Hubble off, no other observer), Hubble (agent Hubble on, Relay, `hubble observe` through `kubectl port-forward` as in the thesis), Otterize (mapper and sniffers), IG trace_tcp (gadget DaemonSet and a streaming client), IG snapshot_socket (gadget DaemonSet and one snapshot near the end of the window). A metrics scraper fetches :9962, :9963 and :9965 every 15 s in every condition, like test-cluster' Prometheus.
- Each run: fresh Cilium agents and app pods, a 60 s idle segment (observer on, no load), 60 s warm-up, a 300 s steady window with the thesis journey-A load, then the fixed-count tests (608 requests, concurrency 16, 1 repeats per mode, keep-alive and new connection per request).
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
| Hubble | quota-bound | bank +0.083 | bank +0.99% | bank +6.1% n.s. | bank +12.1% | bank +0.35% |
| Hubble (agent only) | quota-bound | bank +0.018 | bank -0.06% n.s. | bank +5.1% n.s. | bank +7.2% n.s. | bank +0.13% |

Diagnostic only, do not quote: the same, canary-normalised (each run scaled to the app's median canary speed). The 2026-10-03 validation showed the canary does not track the host drift (r 0.41, normalised CV 16.4% vs 16.6% raw) and inflates deltas 1.7-4.7x. The raw paired deltas above, over interleaved cycles, are the result.

| Technique | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn |
|---|---|---|---|---|
| Hubble | bank +0.091 | bank +1.26% | bank +10.4% | bank +10.7% |
| Hubble (agent only) | bank +0.022 | bank +0.17% n.s. | bank +8.7% n.s. | bank +3.8% n.s. |

## bank

Runs used: baseline 12, Hubble 12, Hubble (agent only) 12.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.20 at 12 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.099 [+0.078, +0.120] | <0.001 | <0.001 | +0.126 [+0.093, +0.158] | <0.001 | <0.001 | 12 |
| Δ cluster busy CPU (cores) | Hubble (agent only) | -0.006 [-0.028, +0.016] (n.s.) | 0.534 | 0.534 | +0.017 [-0.022, +0.057] (n.s.) | 0.358 | 0.358 | 12 |
| Δ observer CPU (cores) | Hubble | +0.083 [+0.077, +0.089] | <0.001 | <0.001 | +0.091 [+0.083, +0.100] | <0.001 | <0.001 | 12 |
| Δ observer CPU (cores) | Hubble (agent only) | +0.018 [+0.014, +0.022] | <0.001 | <0.001 | +0.022 [+0.015, +0.029] | <0.001 | <0.001 | 12 |
| Δ app CPU (cores) | Hubble | -0.014 [-0.028, -0.000] | 0.048 | 0.096 | -0.008 [-0.030, +0.015] (n.s.) | 0.472 | 0.944 | 12 |
| Δ app CPU (cores) | Hubble (agent only) | -0.013 [-0.033, +0.006] (n.s.) | 0.164 | 0.164 | -0.005 [-0.031, +0.021] (n.s.) | 0.704 | 0.944 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.039 [+0.033, +0.045] | <0.001 | <0.001 | +0.050 [+0.040, +0.060] | <0.001 | <0.001 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble (agent only) | -0.003 [-0.008, +0.002] (n.s.) | 0.190 | 0.190 | +0.006 [-0.005, +0.017] (n.s.) | 0.269 | 0.269 | 12 |
| Δ observer anon memory (MiB, primary) | Hubble | +111 [+108, +113] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer anon memory (MiB, primary) | Hubble (agent only) | +43 [+40, +46] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble | +122 [+109, +134] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble (agent only) | +42 [+36, +49] | <0.001 | <0.001 | - | - | - | 12 |
| fixed-count time, keep-alive | Hubble | +6.1% [-4.2, +16.4] (n.s.) | 0.217 | 0.434 | +10.4% [+0.2, +20.6] | 0.046 | 0.092 | 12 |
| fixed-count time, keep-alive | Hubble (agent only) | +5.1% [-6.9, +17.1] (n.s.) | 0.366 | 0.434 | +8.7% [-0.5, +17.9] (n.s.) | 0.061 | 0.092 | 12 |
| fixed-count time, new conn | Hubble | +12.1% [+4.5, +19.7] | 0.005 | 0.010 | +10.7% [+2.3, +19.1] | 0.017 | 0.034 | 12 |
| fixed-count time, new conn | Hubble (agent only) | +7.2% [-1.3, +15.7] (n.s.) | 0.088 | 0.088 | +3.8% [-2.4, +10.0] (n.s.) | 0.203 | 0.203 | 12 |
| canary speed, workers, steady window (check) | Hubble | +4.94% [-2.30, +12.17] (n.s.) | 0.161 | 0.322 | - | - | - | 12 |
| canary speed, workers, steady window (check) | Hubble (agent only) | +2.68% [-2.26, +7.62] (n.s.) | 0.258 | 0.322 | - | - | - | 12 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 11.3% raw, 12.8% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.43; new conn: CV of the baseline time across cycles 12.6% raw, 7.6% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.80.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-05 18:26 | hubble_agent hubble baseline | 27.0 | 25.7 | 18.6 | 26.6 | 0.226 | 0.212 | 8.11 | 0.92 | 8.01 |
| 2 | 10-05 19:01 | hubble hubble_agent baseline | 20.8 | 25.0 | 23.1 | 26.6 | 0.222 | 0.226 | 8.64 | 0.98 | 9.08 |
| 3 | 10-05 19:35 | hubble baseline hubble_agent | 23.5 | 25.1 | 27.7 | 29.7 | 0.198 | 0.230 | 9.67 | 1.10 | 9.86 |
| 4 | 10-05 20:10 | baseline hubble_agent hubble | 24.9 | 27.4 | 27.3 | 29.3 | 0.188 | 0.189 | 8.83 | 1.01 | 8.75 |
| 5 | 10-05 20:44 | hubble_agent baseline hubble | 25.5 | 31.4 | 27.0 | 31.3 | 0.176 | 0.175 | 8.73 | 0.99 | 9.03 |
| 6 | 10-05 21:19 | baseline hubble hubble_agent | 24.1 | 24.3 | 24.6 | 26.8 | 0.224 | 0.220 | 8.84 | 1.01 | 9.09 |
| 7 | 10-05 21:54 | baseline hubble_agent hubble | 23.6 | 30.7 | 25.6 | 31.1 | 0.244 | 0.238 | 8.76 | 1.00 | 9.49 |
| 8 | 10-05 22:28 | hubble_agent baseline hubble | 27.4 | 26.2 | 31.0 | 33.6 | 0.230 | 0.233 | 8.85 | 1.01 | 8.91 |
| 9 | 10-05 23:03 | baseline hubble hubble_agent | 24.2 | 27.7 | 23.7 | 29.6 | 0.239 | 0.230 | 8.73 | 0.99 | 9.56 |
| 10 | 10-05 23:38 | hubble hubble_agent baseline | 29.9 | 36.3 | 26.1 | 28.2 | 0.209 | 0.198 | 8.40 | 0.96 | 8.25 |
| 11 | 10-06 00:12 | hubble_agent hubble baseline | 19.6 | 26.2 | 21.9 | 28.6 | 0.204 | 0.187 | 8.01 | 0.91 | 8.81 |
| 12 | 10-06 00:47 | hubble baseline hubble_agent | 24.5 | 31.5 | 24.6 | 31.8 | 0.217 | 0.255 | 9.82 | 1.12 | 9.09 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Hubble (agent only); that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.083 [+0.077, +0.089] | <0.001 | +0.085 | <0.001 | +0.083 [+0.077, +0.089] | 12 | robust |
| Δ observer CPU | Hubble (agent only) | +0.018 [+0.014, +0.022] | <0.001 | +0.020 | <0.001 | +0.018 [+0.014, +0.023] | 11 | robust |
| Δ observer anon memory | Hubble | +111 [+108, +113] | <0.001 | +111 | <0.001 | +111 [+108, +113] | 12 | robust |
| Δ observer anon memory | Hubble (agent only) | +43 [+40, +46] | <0.001 | +43 | <0.001 | +43 [+40, +47] | 11 | robust |
| fixed-count time, keep-alive | Hubble | +6.1% [-4.2, +16.4] (n.s.) | 0.434 | +6.7% | 0.176 | +6.1% [-4.2, +16.4] (n.s.) | 12 | n.s. (primary) |
| fixed-count time, keep-alive | Hubble (agent only) | +5.1% [-6.9, +17.1] (n.s.) | 0.434 | +2.7% | 0.569 | +4.3% [-8.9, +17.4] (n.s.) | 11 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +12.1% [+4.5, +19.7] | 0.020 | +14.0% | 0.009 | +12.1% [+4.5, +19.7] | 12 | robust |
| fixed-count time, new conn | Hubble (agent only) | +7.2% [-1.3, +15.7] (n.s.) | 0.265 | +2.4% | 0.151 | +4.6% [-2.4, +11.6] (n.s.) | 11 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 608 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 1.02 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 24.58 ± 2.78 (n=12) | 25.76 ± 2.61 (n=12) | +6.12% [-4.16, +16.40] (n.s.) (< 16.4% at 95%) | 0.217 | 0.434 | frontend 1.01 | 3.03 |
| keepalive | Hubble (agent only) | 24.58 ± 2.78 (n=12) | 25.47 ± 2.69 (n=12) | +5.14% [-6.86, +17.14] (n.s.) (< 17.1% at 95%) | 0.366 | 0.434 | frontend 1.22 | 3.03 |
| newconn | Hubble | 25.10 ± 3.16 (n=12) | 27.86 ± 2.24 (n=12) | +12.11% [+4.47, +19.74] | 0.005 | 0.020 | frontend 1.09 | 4.00 |
| newconn | Hubble (agent only) | 25.10 ± 3.16 (n=12) | 26.63 ± 2.37 (n=12) | +7.22% [-1.27, +15.71] (n.s.) (< 15.7% at 95%) | 0.088 | 0.265 | frontend 1.17 | 4.01 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 24.58 ± 2.78 | 11.29% | 11.29% | 12 |
| newconn | 25.10 ± 3.16 | 12.58% | 12.58% | 12 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.076 ± 0.003 | 0.008 | - | 0.488 ± 0.029 | 0.132 | - | - | - | - |
| Hubble | 0.159 ± 0.010 | 0.020 | +0.083 [+0.077, +0.089] | 0.587 ± 0.029 | 0.121 | +0.099 [+0.078, +0.120] | +0.99% | +0.039 | <0.001 / <0.001 |
| Hubble (agent only) | 0.094 ± 0.005 | 0.010 | +0.018 [+0.014, +0.022] | 0.482 ± 0.026 | 0.118 | -0.006 [-0.028, +0.016] (n.s.) | -0.06% | -0.003 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.018 [+0.012, +0.025] | +0.004 [-0.007, +0.014] (n.s.) | +0.020 [-0.001, +0.040] (n.s.) | 22% |
| Hubble (agent only) | +0.006 [+0.002, +0.009] | -0.002 [-0.008, +0.004] (n.s.) | -0.001 [-0.015, +0.013] (n.s.) | 31% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.516 [+0.496, +0.536] | +0.714 [+0.685, +0.742] | +0.213 [+0.201, +0.226] | 1.03 → 1.03 | 23% |
| keepalive | Hubble (agent only) | +0.108 [+0.098, +0.118] | +0.071 [+0.031, +0.112] | -0.006 [-0.018, +0.006] (n.s.) | 1.03 → 1.23 | 10% |
| newconn | Hubble | +0.599 [+0.583, +0.615] | +0.792 [+0.750, +0.833] | +0.233 [+0.218, +0.248] | 1.06 → 1.13 | 26% |
| newconn | Hubble (agent only) | +0.131 [+0.125, +0.138] | +0.092 [+0.061, +0.124] | -0.000 [-0.012, +0.012] (n.s.) | 1.06 → 1.21 | 12% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 686 ± 15 | 2.4 | 1.46 | 369 | - | - | 3942 ± 29 | - | - |
| Hubble | 808 ± 24 (peak 825) | 14.1 | 10.02 | 480 | +111 [+108, +113] | +122 [+109, +134] | 4065 ± 32 | +0.69% | <0.001 / <0.001 |
| Hubble (agent only) | 728 ± 12 (peak 743) | 13.4 | 9.41 | 412 | +43 [+40, +46] | +42 [+36, +49] | 3981 ± 37 | +0.27% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Hubble (agent only) |
|---|---|---|---|
| cilium-agent | 0.065 | 0.098 | 0.083 |
| cilium-envoy | 0.008 | 0.007 | 0.007 |
| cilium-operator | 0.003 | 0.003 | 0.003 |
| hubble-relay | 0.000 | 0.022 | 0.000 |
| client-hubble | 0.000 | 0.028 | 0.000 |
| app | 0.215 | 0.201 | 0.201 |
| loadgen | 0.010 | 0.010 | 0.009 |
| k3s | 0.145 | 0.184 | 0.142 |
| k8s-addons | 0.009 | 0.008 | 0.008 |
| os | 0.001 | 0.001 | 0.001 |
| harness | 0.032 | 0.031 | 0.031 |
| node | 0.488 | 0.587 | 0.482 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%. At under 5 req/s the window holds few requests; do not read the p95/p99 deltas.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 1.73 ± 0.02 | 20.2 ± 3.1 | - | 1391.7 ± 79.3 | - | 2741.7 ± 748.9 | - | 84.37 |
| Hubble | 1.72 ± 0.03 | 21.2 ± 2.4 | +6.6% [-4.1, +17.3] (n.s.) | 1341.7 ± 51.5 | -3.3% [-7.8, +1.3] (n.s.) | 2533.3 ± 702.4 | +2.1% [-28.5, +32.7] (n.s.) | 85.62 |
| Hubble (agent only) | 1.72 ± 0.04 | 19.8 ± 3.2 | -0.5% [-12.8, +11.7] (n.s.) | 1341.7 ± 66.9 | -3.2% [-8.8, +2.4] (n.s.) | 2525.0 ± 564.3 | +1.9% [-28.8, +32.6] (n.s.) | 82.66 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 7.6 | 1.55 | 6.06 | - | - | - | - | - |
| Hubble | 7.8 | 1.78 | 6.03 | +22752 [+20898, +24606] | +28923 [+27396, +30451] | +7228 [+6844, +7612] | +10409 [+9342, +11475] | 117.6 (thesis 101.3) |
| Hubble (agent only) | 7.5 | 1.56 | 5.94 | +4636 [+3893, +5379] | +5894 [+5316, +6472] | +1471 [+1326, +1617] | +1434 [+776, +2092] | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 23%. Lost events: 26 in the window, 123 over the whole run (fixed-count tests included). hubble_* series at the end: 253.

| Class | flows/s | share |
|---|---|---|
| app | 99.7 | 78% |
| probe | 13.7 | 11% |
| client_feedback | 2.7 | 2% |
| other | 11.5 | 9% |

### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about - cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.063 [+0.054, +0.073] | +0.083 | +0.079 [+0.043, +0.116] | +0.35% / +0.44% | +74 [+53, +95] | +0.13% |
| Hubble (agent only) | +0.024 [+0.018, +0.029] | +0.035 | -0.008 [-0.031, +0.016] (n.s.) | +0.13% / -0.04% | +41 [+22, +60] | +0.07% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 3 | 0.17% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 18.64 |
| 2 | baseline | 3 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 23.06 |
| 3 | baseline | 2 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 27.72 |
| 4 | baseline | 1 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 27.29 |
| 5 | baseline | 2 | 0.06% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 27.02 |
| 6 | baseline | 1 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 24.56 |
| 7 | baseline | 1 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 25.60 |
| 8 | baseline | 2 | 0.06% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 30.99 |
| 9 | baseline | 1 | 0.03% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 23.71 |
| 10 | baseline | 3 | 0.03% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 26.10 |
| 11 | baseline | 3 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 21.92 |
| 12 | baseline | 2 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 24.59 |
| 1 | Hubble | 2 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 24.25 |
| 2 | Hubble | 1 | 0.65% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 24.39 |
| 3 | Hubble | 1 | 0.03% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 28.17 |
| 4 | Hubble | 3 | 0.07% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 28.69 |
| 5 | Hubble | 3 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 31.08 |
| 6 | Hubble | 2 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 29.12 |
| 7 | Hubble | 3 | 0.06% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 28.90 |
| 8 | Hubble | 3 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 29.50 |
| 9 | Hubble | 2 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 29.12 |
| 10 | Hubble | 1 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 24.50 |
| 11 | Hubble | 2 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 28.17 |
| 12 | Hubble | 1 | 0.03% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 28.49 |
| 1 | Hubble (agent only) | 1 | 0.02% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 25.29 |
| 2 | Hubble (agent only) | 2 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 23.35 |
| 3 | Hubble (agent only) | 3 | 0.03% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 27.89 |
| 4 | Hubble (agent only) | 2 | 0.21% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 27.87 |
| 5 | Hubble (agent only) | 1 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 28.10 |
| 6 | Hubble (agent only) | 3 | 0.05% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 25.66 |
| 7 | Hubble (agent only) | 2 | 0.06% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 24.82 |
| 8 | Hubble (agent only) | 1 | 0.32% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 29.58 |
| 9 | Hubble (agent only) | 3 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 24.37 |
| 10 | Hubble (agent only) | 2 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 30.18 |
| 11 | Hubble (agent only) | 1 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 28.79 |
| 12 | Hubble (agent only) | 3 | 0.04% | 6ac3eb38c5845e5b26c55ad9 | b7519818,daae82a2,b5c47804 | 23.70 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 7.17/7.06 | 8.40/7.81 | 7.49/9.25 | 12.03/13.00 | 0.92 |
| 1 | Hubble | 6.81/7.45 | 8.21/8.05 | 9.53/8.38 | 7.01/9.06 | 0.93 |
| 1 | Hubble (agent only) | 7.94/7.21 | 8.40/7.20 | 8.58/8.27 | 9.31/10.40 | 0.89 |
| 2 | baseline | 7.92/7.25 | 9.39/7.90 | 11.48/9.62 | 10.04/10.20 | 0.98 |
| 2 | Hubble | 9.82/10.66 | 10.00/10.23 | 9.68/12.67 | 12.27/13.37 | 1.15 |
| 2 | Hubble (agent only) | 7.73/7.22 | 8.50/8.44 | 11.32/9.51 | 10.42/11.36 | 0.96 |
| 3 | baseline | 7.50/10.22 | 8.37/10.97 | 9.63/9.15 | 9.78/9.06 | 1.10 |
| 3 | Hubble | 10.36/7.55 | 11.25/8.22 | 10.89/10.82 | 10.46/10.68 | 1.11 |
| 3 | Hubble (agent only) | 9.32/9.72 | 9.84/10.52 | 11.26/12.22 | 10.50/11.01 | 1.16 |
| 4 | baseline | 7.75/7.52 | 8.98/8.67 | 8.97/10.33 | 8.94/9.93 | 1.01 |
| 4 | Hubble | 7.92/7.35 | 9.26/8.35 | 11.17/8.42 | 10.04/9.76 | 1.00 |
| 4 | Hubble (agent only) | 7.38/7.81 | 8.48/8.77 | 10.00/8.95 | 10.42/10.81 | 0.98 |
| 5 | baseline | 8.40/7.46 | 8.70/8.76 | 9.87/11.76 | 9.09/11.24 | 0.99 |
| 5 | Hubble | 7.32/7.85 | 9.99/9.14 | 9.43/10.56 | 9.09/9.47 | 1.09 |
| 5 | Hubble (agent only) | 6.83/6.82 | 8.45/9.13 | 10.26/9.40 | 8.58/7.88 | 1.00 |
| 6 | baseline | 7.40/7.29 | 8.36/9.31 | 8.09/9.61 | 8.92/10.25 | 1.01 |
| 6 | Hubble | 8.61/9.45 | 8.96/9.42 | 11.37/11.13 | 10.35/10.40 | 1.05 |
| 6 | Hubble (agent only) | 7.97/8.82 | 9.48/8.99 | 12.28/9.96 | 10.04/10.71 | 1.05 |
| 7 | baseline | 7.33/7.12 | 8.31/9.21 | 10.43/12.41 | 10.92/10.44 | 1.00 |
| 7 | Hubble | 11.07/7.08 | 11.66/8.57 | 9.64/9.64 | 10.40/8.54 | 1.15 |
| 7 | Hubble (agent only) | 10.18/7.45 | 10.99/8.20 | 11.62/10.94 | 9.94/10.86 | 1.09 |
| 8 | baseline | 8.00/8.78 | 8.89/8.81 | 7.68/9.12 | 8.63/10.42 | 1.01 |
| 8 | Hubble | 8.40/7.66 | 8.75/8.20 | 11.18/9.72 | 9.70/11.03 | 0.97 |
| 8 | Hubble (agent only) | 7.14/8.21 | 9.79/9.00 | 11.29/11.63 | 9.49/11.78 | 1.07 |
| 9 | baseline | 9.71/8.21 | 8.17/9.28 | 8.79/11.32 | 10.79/11.11 | 0.99 |
| 9 | Hubble | 6.96/9.27 | 8.81/9.87 | 9.56/12.14 | 10.60/10.93 | 1.06 |
| 9 | Hubble (agent only) | 12.43/10.03 | 12.19/9.02 | 11.55/10.46 | 11.57/11.66 | 1.21 |
| 10 | baseline | 8.73/8.47 | 8.20/8.60 | 9.63/11.68 | 9.31/9.64 | 0.96 |
| 10 | Hubble | 8.09/8.25 | 7.87/8.03 | 13.44/11.08 | 11.14/11.24 | 0.91 |
| 10 | Hubble (agent only) | 7.61/8.44 | 8.57/8.25 | 11.35/9.74 | 9.11/6.89 | 0.96 |
| 11 | baseline | 7.53/7.74 | 7.79/8.23 | 11.20/12.35 | 11.46/11.43 | 0.91 |
| 11 | Hubble | 10.77/8.73 | 11.44/9.13 | 10.53/9.58 | 10.10/9.82 | 1.17 |
| 11 | Hubble (agent only) | 9.22/8.27 | 8.58/7.71 | 8.95/7.79 | 9.49/8.50 | 0.93 |
| 12 | baseline | 9.21/10.05 | 8.78/10.86 | 12.22/10.32 | 11.49/11.21 | 1.12 |
| 12 | Hubble | 8.11/7.45 | 8.84/8.18 | 10.48/10.70 | 10.69/10.19 | 0.97 |
| 12 | Hubble (agent only) | 8.36/9.11 | 9.03/8.82 | 12.88/11.91 | 11.04/10.70 | 1.02 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 28.13 ± 3.60 (n=12) | 30.74 ± 3.44 (n=12) | +10.43% [+0.23, +20.63] | 0.046 | 0.092 |
| keepalive | Hubble (agent only) | 28.13 ± 3.60 (n=12) | 30.17 ± 1.87 (n=12) | +8.72% [-0.48, +17.92] (n.s.) (< 17.9% at 95%) | 0.061 | 0.092 |
| newconn | Hubble | 29.44 ± 2.23 (n=12) | 32.51 ± 3.60 (n=12) | +10.72% [+2.34, +19.10] | 0.017 | 0.034 |
| newconn | Hubble (agent only) | 29.44 ± 2.23 (n=12) | 30.48 ± 2.89 (n=12) | +3.81% [-2.39, +10.00] (n.s.) (< 10.0% at 95%) | 0.203 | 0.203 |

## Excluded runs

None.

## Data warnings in used runs

| App | Rep | Condition | Warning |
|---|---|---|---|
| bank | 1 | hubble | Hubble lost 131 events during the run (ring buffer), 39 of them in the steady window |
| bank | 10 | hubble | Hubble lost 119 events during the run (ring buffer), 24 of them in the steady window |
| bank | 11 | hubble | Hubble lost 101 events during the run (ring buffer), 0 of them in the steady window |
| bank | 12 | hubble | Hubble lost 138 events during the run (ring buffer), 41 of them in the steady window |
| bank | 2 | hubble | Hubble lost 133 events during the run (ring buffer), 37 of them in the steady window |
| bank | 3 | hubble | Hubble lost 115 events during the run (ring buffer), 19 of them in the steady window |
| bank | 4 | hubble | Hubble lost 102 events during the run (ring buffer), 1 of them in the steady window |
| bank | 5 | hubble | Hubble lost 132 events during the run (ring buffer), 34 of them in the steady window |
| bank | 6 | hubble | Hubble lost 121 events during the run (ring buffer), 25 of them in the steady window |
| bank | 7 | hubble | Hubble lost 99 events during the run (ring buffer), 0 of them in the steady window |
| bank | 8 | hubble | Hubble lost 141 events during the run (ring buffer), 41 of them in the steady window |
| bank | 9 | hubble | Hubble lost 145 events during the run (ring buffer), 45 of them in the steady window |

## Method notes

- Observer CPU and memory include cilium-agent, cilium-envoy and cilium-operator in every condition, so the baseline row is not zero. The Δ columns are the cost of the technique.
- Cluster busy CPU comes from /proc/stat on each node (user + nice + system + irq + softirq; steal and iowait left out). It also catches indirect costs: API-server and kubelet work for `kubectl port-forward` and `kubectl gadget` streams, exec probes of the gadget DaemonSet, and BPF work in the app's syscalls or in softirq. The kernel here has CONFIG_IRQ_TIME_ACCOUNTING off, so softirq time is charged to whatever task it interrupts.
- The fixed-count time is the tool's own total (hey `Total`), so pod start-up is not in it.
- The steady-window per-flow cost is not reported: the journey-A load keeps connections open, so almost every new connection in the window is a kubelet probe. Per-request and per-connection costs come from the fixed-count tests.
- Events/s for Hubble and IG count client events whose event time falls inside the analysis window (client_bins.json), so both use the same window and the app namespace only.
- The projection is an estimate with two known gaps: no platform background traffic, and a different CPU model and kernel (6.12 here, 6.8 on test-cluster).
- Host-speed canary (bin/canary.py): every 2 s each node runs a fixed pure-Python integer loop and logs its thread CPU time. Iterations per CPU-second is the host speed index; it falls when the hypervisor gives the guest less work per CPU-second (unreported steal, a busy sibling thread, a lower clock). Normalised CPU = cores x speed / the app's median speed (per node); normalised fixed-count time = time x the workers' speed ratio during the test. The canary costs about 1% of one core per node and is counted as harness.
