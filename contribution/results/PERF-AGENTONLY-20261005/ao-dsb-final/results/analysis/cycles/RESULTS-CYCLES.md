# Capture overhead: interleaved cycles (randomized multiple interleaved trials)

Generated 2026-10-06 00:45 UTC by analyze/analyze.py from `/Users/shiv/Desktop/code/MasterThesis/contribution/perf-benchmark/../results/PERF-AGENTONLY-20261005/ao-dsb-final/results`. 36 run directories, 36 used, 0 excluded.

## Setup

- Cluster: iximiuz play, k3s, Cilium 1.19.5 configured like test-cluster. cp-01 has 2 vCPU and runs the load generator and the capture clients. worker-01 and worker-02 have 4 vCPU each and run the app.
- Conditions: baseline (Cilium, Hubble off, no other observer), Hubble (agent Hubble on, Relay, `hubble observe` through `kubectl port-forward` as in the thesis), Otterize (mapper and sniffers), IG trace_tcp (gadget DaemonSet and a streaming client), IG snapshot_socket (gadget DaemonSet and one snapshot near the end of the window). A metrics scraper fetches :9962, :9963 and :9965 every 15 s in every condition, like test-cluster' Prometheus.
- Each run: fresh Cilium agents and app pods, a 60 s idle segment (observer on, no load), 60 s warm-up, a 300 s steady window with the thesis journey-A load, then the fixed-count tests (1504 requests, concurrency 16, 1 repeats per mode, keep-alive and new connection per request).
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
| Hubble | quota-bound | dsb +0.123 | dsb +1.70% | dsb +11.8% | dsb +6.3% n.s. | dsb +0.51% |
| Hubble (agent only) | quota-bound | dsb +0.017 | dsb +0.10% | dsb +0.1% n.s. | dsb -2.5% n.s. | dsb +0.12% |

Diagnostic only, do not quote: the same, canary-normalised (each run scaled to the app's median canary speed). The 2026-10-03 validation showed the canary does not track the host drift (r 0.41, normalised CV 16.4% vs 16.6% raw) and inflates deltas 1.7-4.7x. The raw paired deltas above, over interleaved cycles, are the result.

| Technique | Δ observer CPU (cores) | Δ cluster CPU, % of capacity | Fixed-count overhead, keep-alive | Fixed-count overhead, new conn |
|---|---|---|---|---|
| Hubble | dsb +0.122 | dsb +1.68% | dsb +13.3% | dsb +6.5% n.s. |
| Hubble (agent only) | dsb +0.017 | dsb +0.10% | dsb +1.3% n.s. | dsb -2.0% n.s. |

## dsb

Runs used: baseline 12, Hubble 12, Hubble (agent only) 12.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.20 at 12 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.170 [+0.164, +0.175] | <0.001 | <0.001 | +0.168 [+0.162, +0.173] | <0.001 | <0.001 | 12 |
| Δ cluster busy CPU (cores) | Hubble (agent only) | +0.010 [+0.005, +0.015] | 0.002 | 0.002 | +0.010 [+0.004, +0.016] | 0.003 | 0.003 | 12 |
| Δ observer CPU (cores) | Hubble | +0.123 [+0.120, +0.126] | <0.001 | <0.001 | +0.122 [+0.119, +0.124] | <0.001 | <0.001 | 12 |
| Δ observer CPU (cores) | Hubble (agent only) | +0.017 [+0.016, +0.018] | <0.001 | <0.001 | +0.017 [+0.016, +0.019] | <0.001 | <0.001 | 12 |
| Δ app CPU (cores) | Hubble | +0.005 [+0.004, +0.006] | <0.001 | <0.001 | +0.005 [+0.004, +0.007] | <0.001 | <0.001 | 12 |
| Δ app CPU (cores) | Hubble (agent only) | +0.002 [+0.001, +0.003] | 0.002 | 0.002 | +0.002 [-0.000, +0.004] (n.s.) | 0.062 | 0.062 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.056 [+0.055, +0.058] | <0.001 | <0.001 | +0.055 [+0.053, +0.058] | <0.001 | <0.001 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble (agent only) | +0.001 [-0.000, +0.002] (n.s.) | 0.104 | 0.104 | +0.001 [-0.001, +0.003] (n.s.) | 0.263 | 0.263 | 12 |
| Δ observer anon memory (MiB, primary) | Hubble | +112 [+110, +114] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer anon memory (MiB, primary) | Hubble (agent only) | +32 [+30, +34] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble | +127 [+115, +139] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble (agent only) | +36 [+28, +43] | <0.001 | <0.001 | - | - | - | 12 |
| fixed-count time, keep-alive | Hubble | +11.8% [+6.6, +17.0] | <0.001 | <0.001 | +13.3% [+9.5, +17.1] | <0.001 | <0.001 | 12 |
| fixed-count time, keep-alive | Hubble (agent only) | +0.1% [-4.6, +4.9] (n.s.) | 0.947 | 0.947 | +1.3% [-2.5, +5.0] (n.s.) | 0.474 | 0.474 | 12 |
| fixed-count time, new conn | Hubble | +6.3% [-13.2, +25.7] (n.s.) | 0.492 | 0.985 | +6.5% [-13.0, +26.0] (n.s.) | 0.478 | 0.957 | 12 |
| fixed-count time, new conn | Hubble (agent only) | -2.5% [-20.7, +15.7] (n.s.) | 0.770 | 0.985 | -2.0% [-20.2, +16.2] (n.s.) | 0.813 | 0.957 | 12 |
| canary speed, workers, steady window (check) | Hubble | +0.23% [-1.43, +1.90] (n.s.) | 0.764 | 1.000 | - | - | - | 12 |
| canary speed, workers, steady window (check) | Hubble (agent only) | +0.28% [-1.81, +2.36] (n.s.) | 0.776 | 1.000 | - | - | - | 12 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 6.8% raw, 4.9% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.70; new conn: CV of the baseline time across cycles 152.6% raw, 156.5% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.33.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-05 18:19 | hubble baseline hubble_agent | 17.2 | 16.7 | 16.6 | 16.4 | 0.064 | 0.064 | 15.22 | 1.00 | 14.90 |
| 2 | 10-05 18:51 | hubble_agent baseline hubble | 15.8 | 15.5 | 18.3 | 17.6 | 0.062 | 0.062 | 15.08 | 0.99 | 15.07 |
| 3 | 10-05 19:23 | baseline hubble_agent hubble | 15.0 | 14.8 | 17.3 | 16.5 | 0.062 | 0.062 | 15.19 | 0.99 | 15.12 |
| 4 | 10-05 19:55 | baseline hubble hubble_agent | 16.5 | 16.2 | 17.4 | 17.1 | 0.062 | 0.060 | 15.19 | 0.99 | 15.24 |
| 5 | 10-05 20:27 | hubble hubble_agent baseline | 17.2 | 15.2 | 18.6 | 17.6 | 0.062 | 0.057 | 14.43 | 0.95 | 14.99 |
| 6 | 10-05 20:58 | hubble_agent hubble baseline | 15.4 | 15.9 | 16.6 | 17.1 | 0.062 | 0.064 | 15.64 | 1.02 | 15.43 |
| 7 | 10-05 21:30 | hubble hubble_agent baseline | 16.2 | 16.8 | 17.2 | 17.5 | 0.063 | 0.063 | 15.37 | 1.01 | 15.49 |
| 8 | 10-05 22:02 | baseline hubble_agent hubble | 15.5 | 15.7 | 18.6 | 18.7 | 0.062 | 0.062 | 15.27 | 1.00 | 15.24 |
| 9 | 10-05 22:34 | hubble_agent hubble baseline | 13.8 | 14.0 | 16.8 | 17.5 | 0.061 | 0.062 | 15.46 | 1.01 | 15.34 |
| 10 | 10-05 23:05 | baseline hubble hubble_agent | 15.2 | 15.3 | 183.1 | 189.6 | 0.062 | 0.062 | 15.32 | 1.00 | 15.48 |
| 11 | 10-05 23:40 | hubble baseline hubble_agent | 15.1 | 15.7 | 16.4 | 17.0 | 0.062 | 0.063 | 15.48 | 1.01 | 15.20 |
| 12 | 10-06 00:11 | hubble_agent baseline hubble | 17.3 | 15.9 | 19.1 | 18.5 | 0.061 | 0.058 | 14.77 | 0.97 | 15.17 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Hubble; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.123 [+0.120, +0.126] | <0.001 | +0.121 | <0.001 | +0.122 [+0.120, +0.125] | 11 | robust |
| Δ observer CPU | Hubble (agent only) | +0.017 [+0.016, +0.018] | <0.001 | +0.017 | <0.001 | +0.017 [+0.016, +0.018] | 12 | robust |
| Δ observer anon memory | Hubble | +112 [+110, +114] | <0.001 | +113 | <0.001 | +112 [+110, +115] | 11 | robust |
| Δ observer anon memory | Hubble (agent only) | +32 [+30, +34] | <0.001 | +32 | <0.001 | +32 [+30, +34] | 12 | robust |
| fixed-count time, keep-alive | Hubble | +11.8% [+6.6, +17.0] | 0.002 | +11.2% | <0.001 | +12.6% [+7.3, +18.0] | 11 | robust |
| fixed-count time, keep-alive | Hubble (agent only) | +0.1% [-4.6, +4.9] (n.s.) | 1.000 | +0.4% | 0.910 | +0.1% [-4.6, +4.9] (n.s.) | 12 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +6.3% [-13.2, +25.7] (n.s.) | 1.000 | +16.5% | 0.034 | +4.9% [-16.4, +26.2] (n.s.) | 11 | n.s. (primary) |
| fixed-count time, new conn | Hubble (agent only) | -2.5% [-20.7, +15.7] (n.s.) | 1.000 | +4.2% | 0.266 | -2.5% [-20.7, +15.7] (n.s.) | 12 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 1504 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 2.20 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 15.84 ± 1.07 (n=12) | 17.64 ± 0.58 (n=12) | +11.80% [+6.61, +17.00] | <0.001 | 0.002 | nginx-thrift 2.33 | 1.04 |
| keepalive | Hubble (agent only) | 15.84 ± 1.07 (n=12) | 15.79 ± 0.43 (n=12) | +0.15% [-4.57, +4.87] (n.s.) (< 4.9% at 95%) | 0.947 | 1.000 | nginx-thrift 2.16 | 1.04 |
| newconn | Hubble | 31.32 ± 47.80 (n=12) | 20.08 ± 0.60 (n=12) | +6.27% [-13.16, +25.70] (n.s.) (< 25.7% at 95%) | 0.492 | 1.000 | nginx-thrift 2.09 | 2.05 |
| newconn | Hubble (agent only) | 31.32 ± 47.80 (n=12) | 18.40 ± 1.04 (n=12) | -2.48% [-20.70, +15.73] (n.s.) (< 15.7% at 95%) | 0.770 | 1.000 | nginx-thrift 2.24 | 2.05 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 15.84 ± 1.07 | 6.78% | 6.78% | 12 |
| newconn | 31.32 ± 47.80 | 152.59% | 152.59% | 12 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.048 ± 0.002 | 0.006 | - | 0.226 ± 0.006 | 0.022 | - | - | - | - |
| Hubble | 0.171 ± 0.005 | 0.013 | +0.123 [+0.120, +0.126] | 0.396 ± 0.013 | 0.034 | +0.170 [+0.164, +0.175] | +1.70% | +0.056 | <0.001 / <0.001 |
| Hubble (agent only) | 0.065 ± 0.002 | 0.007 | +0.017 [+0.016, +0.018] | 0.236 ± 0.009 | 0.023 | +0.010 [+0.005, +0.015] | +0.10% | +0.001 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.005 [+0.004, +0.007] | -0.002 [-0.007, +0.004] (n.s.) | +0.003 [-0.003, +0.010] (n.s.) | 4% |
| Hubble (agent only) | +0.003 [+0.002, +0.005] | -0.002 [-0.007, +0.004] (n.s.) | -0.000 [-0.009, +0.008] (n.s.) | 19% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.267 [+0.258, +0.276] | +0.337 [+0.296, +0.378] | +0.096 [+0.088, +0.103] | 2.41 → 2.34 | 13% |
| keepalive | Hubble (agent only) | +0.024 [+0.021, +0.027] | -0.012 [-0.060, +0.035] (n.s.) | -0.006 [-0.012, -0.000] | 2.41 → 2.16 | 7% |
| newconn | Hubble | +0.418 [+0.402, +0.434] | +0.518 [+0.478, +0.557] | +0.143 [+0.135, +0.151] | 2.20 → 2.09 | 20% |
| newconn | Hubble (agent only) | +0.072 [+0.069, +0.075] | +0.045 [+0.017, +0.074] | -0.000 [-0.009, +0.008] (n.s.) | 2.20 → 2.25 | 10% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 679 ± 18 | 2.9 | 0.83 | 378 | - | - | 3741 ± 27 | - | - |
| Hubble | 805 ± 29 (peak 817) | 8.1 | 5.45 | 490 | +112 [+110, +114] | +127 [+115, +139] | 3880 ± 34 | +0.70% | <0.001 / <0.001 |
| Hubble (agent only) | 714 ± 18 (peak 725) | 7.4 | 5.02 | 410 | +32 [+30, +34] | +36 [+28, +43] | 3779 ± 18 | +0.20% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Hubble (agent only) |
|---|---|---|---|
| cilium-agent | 0.040 | 0.098 | 0.058 |
| cilium-envoy | 0.006 | 0.006 | 0.006 |
| cilium-operator | 0.002 | 0.002 | 0.002 |
| hubble-relay | 0.000 | 0.029 | 0.000 |
| client-hubble | 0.000 | 0.036 | 0.000 |
| app | 0.062 | 0.067 | 0.064 |
| loadgen | 0.005 | 0.005 | 0.005 |
| k3s | 0.107 | 0.163 | 0.108 |
| k8s-addons | 0.003 | 0.003 | 0.003 |
| os | 0.001 | 0.001 | 0.001 |
| harness | 0.021 | 0.021 | 0.021 |
| node | 0.226 | 0.396 | 0.236 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 19.98 ± 0.00 | 2.6 ± 0.2 | - | 3.5 ± 0.2 | - | 4.2 ± 0.3 | - | 0.13 |
| Hubble | 19.97 ± 0.01 | 3.3 ± 0.1 | +24.1% [+18.8, +29.4] | 4.4 ± 0.3 | +24.4% [+17.5, +31.2] | 5.5 ± 0.6 | +29.9% [+19.2, +40.5] | 0.14 |
| Hubble (agent only) | 19.98 ± 0.00 | 2.7 ± 0.2 | +4.4% [-1.7, +10.4] (n.s.) | 3.7 ± 0.3 | +4.6% [-2.0, +11.2] (n.s.) | 5.0 ± 2.2 | +19.2% [-13.0, +51.4] (n.s.) | 0.13 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 19.0 | 0.00 | 18.96 | - | - | - | - | - |
| Hubble | 19.2 | 0.20 | 19.01 | +3398 [+3224, +3572] | +6142 [+5922, +6362] | +2999 [+2892, +3107] | +3112 [+1202, +5022] | 331.7 (thesis 354.0) |
| Hubble (agent only) | 19.0 | 0.00 | 18.95 | +244 [+207, +281] | +961 [+890, +1031] | +468 [+434, +503] | -468 [-2367, +1430] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 4%. Lost events: 122 in the window, 220 over the whole run (fixed-count tests included). hubble_* series at the end: 303.

| Class | flows/s | share |
|---|---|---|
| app | 332.0 | 96% |
| probe | 0.3 | 0% |
| client_feedback | 2.7 | 1% |
| other | 11.5 | 3% |

### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about - cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.091 [+0.088, +0.095] | +0.120 | +0.135 [+0.126, +0.144] | +0.51% / +0.75% | +85 [+61, +109] | +0.15% |
| Hubble (agent only) | +0.021 [+0.019, +0.023] | +0.029 | +0.013 [+0.001, +0.025] | +0.12% / +0.07% | +44 [+21, +67] | +0.08% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 2 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 16.57 |
| 2 | baseline | 2 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 18.31 |
| 3 | baseline | 1 | 0.01% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 17.27 |
| 4 | baseline | 1 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 17.36 |
| 5 | baseline | 3 | 0.03% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 18.63 |
| 6 | baseline | 3 | 0.18% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 16.62 |
| 7 | baseline | 3 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 17.18 |
| 8 | baseline | 1 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 18.58 |
| 9 | baseline | 3 | 0.05% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 16.79 |
| 10 | baseline | 1 | 0.05% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 183.07 |
| 11 | baseline | 2 | 0.05% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 16.40 |
| 12 | baseline | 2 | 0.03% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 19.10 |
| 1 | Hubble | 1 | 0.07% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 20.06 |
| 2 | Hubble | 3 | 0.17% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 19.22 |
| 3 | Hubble | 3 | 0.08% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 20.54 |
| 4 | Hubble | 2 | 0.08% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 20.17 |
| 5 | Hubble | 1 | 0.02% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 21.38 |
| 6 | Hubble | 2 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 19.43 |
| 7 | Hubble | 1 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 20.39 |
| 8 | Hubble | 3 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 19.62 |
| 9 | Hubble | 2 | 0.02% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 20.07 |
| 10 | Hubble | 2 | 0.07% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 19.83 |
| 11 | Hubble | 1 | 0.05% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 19.62 |
| 12 | Hubble | 3 | 0.02% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 20.64 |
| 1 | Hubble (agent only) | 3 | 0.02% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 18.73 |
| 2 | Hubble (agent only) | 1 | 0.54% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 20.58 |
| 3 | Hubble (agent only) | 2 | 0.05% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 19.11 |
| 4 | Hubble (agent only) | 3 | 0.05% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 17.74 |
| 5 | Hubble (agent only) | 2 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 16.58 |
| 6 | Hubble (agent only) | 1 | 0.02% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 17.64 |
| 7 | Hubble (agent only) | 2 | 0.02% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 17.47 |
| 8 | Hubble (agent only) | 2 | 0.06% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 18.90 |
| 9 | Hubble (agent only) | 1 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 18.17 |
| 10 | Hubble (agent only) | 3 | 0.04% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 17.98 |
| 11 | Hubble (agent only) | 3 | 0.02% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 19.26 |
| 12 | Hubble (agent only) | 1 | 0.08% | 6ac3e7c9cde73a52e44a2a58 | 18bfc721,633b988b,b5f44529 | 18.68 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 15.52/15.80 | 15.14/15.31 | 14.73/14.84 | 14.53/15.61 | 1.00 |
| 1 | Hubble | 14.93/15.05 | 14.45/14.42 | 15.17/15.01 | 15.37/14.73 | 0.95 |
| 1 | Hubble (agent only) | 15.43/15.62 | 14.93/15.17 | 15.45/15.07 | 15.38/15.55 | 0.99 |
| 2 | baseline | 15.26/15.98 | 14.76/15.39 | 14.77/15.14 | 14.34/15.09 | 0.99 |
| 2 | Hubble | 15.54/15.79 | 15.17/15.35 | 15.84/15.78 | 15.26/15.77 | 1.00 |
| 2 | Hubble (agent only) | 14.83/14.87 | 14.78/14.96 | 13.83/14.74 | 14.44/15.11 | 0.97 |
| 3 | baseline | 14.98/15.49 | 15.28/15.10 | 15.17/15.05 | 14.25/14.89 | 0.99 |
| 3 | Hubble | 14.67/14.60 | 15.36/14.85 | 15.13/15.09 | 15.55/15.21 | 0.99 |
| 3 | Hubble (agent only) | 15.39/14.80 | 15.12/15.02 | 15.01/15.52 | 15.98/15.36 | 0.99 |
| 4 | baseline | 15.62/15.29 | 15.71/14.67 | 15.53/14.53 | 15.58/14.58 | 0.99 |
| 4 | Hubble | 15.57/15.65 | 15.45/15.11 | 15.52/15.94 | 14.81/14.98 | 1.00 |
| 4 | Hubble (agent only) | 15.18/14.49 | 15.47/15.03 | 15.72/15.58 | 16.24/16.13 | 1.00 |
| 5 | baseline | 15.83/13.77 | 15.56/13.31 | 14.61/12.35 | 15.34/13.58 | 0.95 |
| 5 | Hubble | 15.51/14.59 | 14.94/14.72 | 15.61/15.14 | 14.53/14.05 | 0.97 |
| 5 | Hubble (agent only) | 15.63/15.74 | 15.76/15.66 | 15.07/15.23 | 15.78/15.19 | 1.03 |
| 6 | baseline | 15.19/14.97 | 15.62/15.66 | 15.65/15.92 | 15.45/16.00 | 1.02 |
| 6 | Hubble | 15.84/15.30 | 15.28/15.41 | 15.23/14.63 | 15.28/15.60 | 1.00 |
| 6 | Hubble (agent only) | 15.99/15.66 | 15.41/15.19 | 15.62/14.69 | 14.88/15.27 | 1.00 |
| 7 | baseline | 15.54/15.91 | 15.28/15.45 | 15.55/16.11 | 15.43/15.67 | 1.01 |
| 7 | Hubble | 15.31/15.65 | 15.52/15.56 | 15.05/14.93 | 15.60/14.18 | 1.02 |
| 7 | Hubble (agent only) | 15.97/15.96 | 15.65/15.47 | 16.03/16.43 | 15.65/15.96 | 1.02 |
| 8 | baseline | 15.36/15.52 | 15.20/15.33 | 15.54/15.55 | 15.38/15.43 | 1.00 |
| 8 | Hubble | 15.65/15.73 | 15.29/15.35 | 15.45/15.24 | 15.23/15.87 | 1.00 |
| 8 | Hubble (agent only) | 15.66/15.19 | 15.36/14.90 | 14.99/14.61 | 15.90/15.39 | 0.99 |
| 9 | baseline | 15.47/15.48 | 15.29/15.63 | 15.77/15.33 | 15.37/16.42 | 1.01 |
| 9 | Hubble | 15.94/15.99 | 15.27/15.56 | 14.84/15.36 | 14.78/15.40 | 1.01 |
| 9 | Hubble (agent only) | 15.97/15.61 | 15.09/15.21 | 15.63/15.62 | 15.14/15.44 | 0.99 |
| 10 | baseline | 15.45/15.77 | 15.20/15.43 | 15.24/15.53 | 15.75/15.88 | 1.00 |
| 10 | Hubble | 15.96/15.62 | 15.52/15.35 | 14.49/15.00 | 15.59/14.66 | 1.01 |
| 10 | Hubble (agent only) | 15.66/15.55 | 15.86/15.52 | 16.00/15.97 | 16.12/16.22 | 1.03 |
| 11 | baseline | 15.70/15.30 | 15.31/15.65 | 15.63/16.19 | 15.68/15.91 | 1.01 |
| 11 | Hubble | 15.63/15.61 | 15.31/15.13 | 16.19/15.67 | 15.83/14.85 | 1.00 |
| 11 | Hubble (agent only) | 15.31/14.83 | 15.22/14.59 | 15.02/14.74 | 14.53/13.39 | 0.98 |
| 12 | baseline | 15.62/14.63 | 15.14/14.40 | 14.49/13.59 | 14.95/14.60 | 0.97 |
| 12 | Hubble | 15.89/16.23 | 15.49/15.71 | 15.64/15.74 | 16.03/16.12 | 1.02 |
| 12 | Hubble (agent only) | 15.36/15.71 | 15.16/15.14 | 15.09/15.39 | 14.47/14.73 | 0.99 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 15.64 ± 0.77 (n=12) | 17.69 ± 0.80 (n=12) | +13.27% [+9.47, +17.06] | <0.001 | <0.001 |
| keepalive | Hubble (agent only) | 15.64 ± 0.77 (n=12) | 15.81 ± 0.60 (n=12) | +1.27% [-2.49, +5.03] (n.s.) (< 5.0% at 95%) | 0.474 | 0.474 |
| newconn | Hubble | 31.76 ± 49.72 (n=12) | 20.00 ± 0.62 (n=12) | +6.49% [-12.98, +25.96] (n.s.) (< 26.0% at 95%) | 0.478 | 0.957 |
| newconn | Hubble (agent only) | 31.76 ± 49.72 (n=12) | 18.47 ± 0.96 (n=12) | -2.01% [-20.19, +16.18] (n.s.) (< 16.2% at 95%) | 0.813 | 0.957 |

## Excluded runs

None.

## Data warnings in used runs

| App | Rep | Condition | Warning |
|---|---|---|---|
| dsb | 1 | hubble | Hubble lost 221 events during the run (ring buffer), 120 of them in the steady window |
| dsb | 10 | hubble | Hubble lost 221 events during the run (ring buffer), 120 of them in the steady window |
| dsb | 11 | hubble | Hubble lost 221 events during the run (ring buffer), 122 of them in the steady window |
| dsb | 12 | hubble | Hubble lost 220 events during the run (ring buffer), 122 of them in the steady window |
| dsb | 2 | hubble | Hubble lost 221 events during the run (ring buffer), 122 of them in the steady window |
| dsb | 3 | hubble | Hubble lost 223 events during the run (ring buffer), 122 of them in the steady window |
| dsb | 4 | hubble | Hubble lost 221 events during the run (ring buffer), 122 of them in the steady window |
| dsb | 5 | hubble | Hubble lost 219 events during the run (ring buffer), 122 of them in the steady window |
| dsb | 6 | hubble | Hubble lost 219 events during the run (ring buffer), 122 of them in the steady window |
| dsb | 7 | hubble | Hubble lost 221 events during the run (ring buffer), 121 of them in the steady window |
| dsb | 8 | hubble | Hubble lost 220 events during the run (ring buffer), 122 of them in the steady window |
| dsb | 9 | hubble | Hubble lost 216 events during the run (ring buffer), 122 of them in the steady window |

## Method notes

- Observer CPU and memory include cilium-agent, cilium-envoy and cilium-operator in every condition, so the baseline row is not zero. The Δ columns are the cost of the technique.
- Cluster busy CPU comes from /proc/stat on each node (user + nice + system + irq + softirq; steal and iowait left out). It also catches indirect costs: API-server and kubelet work for `kubectl port-forward` and `kubectl gadget` streams, exec probes of the gadget DaemonSet, and BPF work in the app's syscalls or in softirq. The kernel here has CONFIG_IRQ_TIME_ACCOUNTING off, so softirq time is charged to whatever task it interrupts.
- The fixed-count time is the tool's own total (hey `Total`), so pod start-up is not in it.
- The steady-window per-flow cost is not reported: the journey-A load keeps connections open, so almost every new connection in the window is a kubelet probe. Per-request and per-connection costs come from the fixed-count tests.
- Events/s for Hubble and IG count client events whose event time falls inside the analysis window (client_bins.json), so both use the same window and the app namespace only.
- The projection is an estimate with two known gaps: no platform background traffic, and a different CPU model and kernel (6.12 here, 6.8 on test-cluster).
- Host-speed canary (bin/canary.py): every 2 s each node runs a fixed pure-Python integer loop and logs its thread CPU time. Iterations per CPU-second is the host speed index; it falls when the hypervisor gives the guest less work per CPU-second (unreported steal, a busy sibling thread, a lower clock). Normalised CPU = cores x speed / the app's median speed (per node); normalised fixed-count time = time x the workers' speed ratio during the test. The canary costs about 1% of one core per node and is counted as harness.
