# boutique

Runs used: baseline 12, Hubble 12, Hubble (agent only) 12.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.20 at 12 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.044 [+0.021, +0.068] | 0.001 | 0.003 | +0.061 [+0.048, +0.075] | <0.001 | <0.001 | 12 |
| Δ cluster busy CPU (cores) | Hubble (agent only) | -0.002 [-0.012, +0.008] (n.s.) | 0.657 | 0.657 | +0.009 [-0.003, +0.021] (n.s.) | 0.132 | 0.132 | 12 |
| Δ observer CPU (cores) | Hubble | +0.038 [+0.031, +0.045] | <0.001 | <0.001 | +0.043 [+0.037, +0.048] | <0.001 | <0.001 | 12 |
| Δ observer CPU (cores) | Hubble (agent only) | +0.010 [+0.008, +0.012] | <0.001 | <0.001 | +0.013 [+0.010, +0.016] | <0.001 | <0.001 | 12 |
| Δ app CPU (cores) | Hubble | -0.003 [-0.008, +0.001] (n.s.) | 0.124 | 0.124 | +0.001 [-0.002, +0.005] (n.s.) | 0.459 | 0.919 | 12 |
| Δ app CPU (cores) | Hubble (agent only) | -0.003 [-0.004, -0.001] | 0.004 | 0.007 | +0.001 [-0.002, +0.003] (n.s.) | 0.538 | 0.919 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.016 [+0.004, +0.028] | 0.015 | 0.030 | +0.023 [+0.014, +0.033] | <0.001 | <0.001 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble (agent only) | -0.003 [-0.006, -0.000] | 0.033 | 0.033 | +0.001 [-0.005, +0.008] (n.s.) | 0.624 | 0.624 | 12 |
| Δ observer anon memory (MiB, primary) | Hubble | +99 [+96, +102] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer anon memory (MiB, primary) | Hubble (agent only) | +33 [+30, +36] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble | +111 [+98, +123] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble (agent only) | +34 [+32, +36] | <0.001 | <0.001 | - | - | - | 12 |
| fixed-count time, keep-alive | Hubble | -1.7% [-8.6, +5.2] (n.s.) | 0.600 | 1.000 | +2.7% [-6.3, +11.7] (n.s.) | 0.523 | 1.000 | 12 |
| fixed-count time, keep-alive | Hubble (agent only) | -2.1% [-12.9, +8.7] (n.s.) | 0.678 | 1.000 | +3.0% [-11.2, +17.3] (n.s.) | 0.648 | 1.000 | 12 |
| fixed-count time, new conn | Hubble | +5.0% [-3.1, +13.2] (n.s.) | 0.199 | 0.399 | +10.3% [-2.4, +23.1] (n.s.) | 0.102 | 0.204 | 12 |
| fixed-count time, new conn | Hubble (agent only) | +5.3% [-8.0, +18.5] (n.s.) | 0.401 | 0.401 | +6.4% [-1.5, +14.3] (n.s.) | 0.103 | 0.204 | 12 |
| canary speed, workers, steady window (check) | Hubble | +7.81% [-2.27, +17.88] (n.s.) | 0.116 | 0.129 | - | - | - | 12 |
| canary speed, workers, steady window (check) | Hubble (agent only) | +4.60% [-0.33, +9.53] (n.s.) | 0.064 | 0.129 | - | - | - | 12 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 9.8% raw, 10.0% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.68; new conn: CV of the baseline time across cycles 15.3% raw, 11.1% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.70.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-05 18:25 | hubble_agent hubble baseline | 37.8 | 33.6 | 30.3 | 36.6 | 0.067 | 0.061 | 8.12 | 0.92 | 7.90 |
| 2 | 10-05 18:59 | hubble baseline hubble_agent | 41.1 | 42.4 | 29.7 | 32.4 | 0.069 | 0.059 | 7.53 | 0.86 | 8.78 |
| 3 | 10-05 19:33 | hubble hubble_agent baseline | 36.7 | 39.4 | 44.0 | 42.1 | 0.066 | 0.060 | 7.92 | 0.90 | 8.79 |
| 4 | 10-05 20:07 | baseline hubble_agent hubble | 32.0 | 43.5 | 38.2 | 44.8 | 0.071 | 0.062 | 7.74 | 0.88 | 8.80 |
| 5 | 10-05 20:40 | hubble_agent baseline hubble | 41.4 | 39.7 | 43.3 | 42.4 | 0.061 | 0.057 | 8.28 | 0.94 | 8.59 |
| 6 | 10-05 21:15 | baseline hubble hubble_agent | 36.5 | 37.6 | 41.5 | 39.2 | 0.062 | 0.059 | 8.41 | 0.96 | 9.10 |
| 7 | 10-05 21:48 | hubble_agent hubble baseline | 39.0 | 37.9 | 41.0 | 36.1 | 0.061 | 0.059 | 8.56 | 0.97 | 8.75 |
| 8 | 10-05 22:22 | baseline hubble_agent hubble | 38.6 | 35.5 | 32.7 | 31.1 | 0.055 | 0.060 | 9.57 | 1.09 | 9.94 |
| 9 | 10-05 22:55 | baseline hubble hubble_agent | 34.5 | 30.2 | 41.8 | 39.7 | 0.052 | 0.059 | 9.97 | 1.13 | 9.96 |
| 10 | 10-05 23:30 | hubble_agent baseline hubble | 30.6 | 37.9 | 42.0 | 43.1 | 0.060 | 0.060 | 8.77 | 1.00 | 9.15 |
| 11 | 10-06 00:03 | hubble hubble_agent baseline | 32.6 | 41.8 | 32.0 | 42.7 | 0.063 | 0.065 | 9.45 | 1.08 | 8.76 |
| 12 | 10-06 00:37 | hubble baseline hubble_agent | 33.7 | 40.5 | 30.6 | 40.9 | 0.064 | 0.070 | 9.77 | 1.11 | 9.40 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Hubble (agent only); that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.038 [+0.031, +0.045] | <0.001 | +0.041 | <0.001 | +0.038 [+0.031, +0.045] | 12 | robust |
| Δ observer CPU | Hubble (agent only) | +0.010 [+0.008, +0.012] | <0.001 | +0.011 | <0.001 | +0.010 [+0.008, +0.012] | 11 | robust |
| Δ observer anon memory | Hubble | +99 [+96, +102] | <0.001 | +99 | <0.001 | +99 [+96, +102] | 12 | robust |
| Δ observer anon memory | Hubble (agent only) | +33 [+30, +36] | <0.001 | +33 | <0.001 | +33 [+31, +36] | 11 | robust |
| fixed-count time, keep-alive | Hubble | -1.7% [-8.6, +5.2] (n.s.) | 1.000 | -5.7% | 0.519 | -1.7% [-8.6, +5.2] (n.s.) | 12 | n.s. (primary) |
| fixed-count time, keep-alive | Hubble (agent only) | -2.1% [-12.9, +8.7] (n.s.) | 1.000 | -2.9% | 0.910 | -3.9% [-15.0, +7.3] (n.s.) | 11 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +5.0% [-3.1, +13.2] (n.s.) | 0.797 | +4.3% | 0.301 | +5.0% [-3.1, +13.2] (n.s.) | 12 | n.s. (primary) |
| fixed-count time, new conn | Hubble (agent only) | +5.3% [-8.0, +18.5] (n.s.) | 1.000 | +1.2% | 0.470 | +2.0% [-10.4, +14.4] (n.s.) | 11 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 3008 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 0.87 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 36.20 ± 3.56 (n=12) | 35.48 ± 4.25 (n=12) | -1.69% [-8.56, +5.19] (n.s.) (< 5.2% at 95%) | 0.600 | 1.000 | recommendationservice 0.90 | 0.00 |
| keepalive | Hubble (agent only) | 36.20 ± 3.56 (n=12) | 35.34 ± 6.63 (n=12) | -2.09% [-12.89, +8.71] (n.s.) (< 8.7% at 95%) | 0.678 | 1.000 | recommendationservice 0.83 | 0.01 |
| newconn | Hubble | 37.27 ± 5.69 (n=12) | 38.56 ± 2.97 (n=12) | +5.04% [-3.08, +13.17] (n.s.) (< 13.2% at 95%) | 0.199 | 0.797 | recommendationservice 0.88 | 1.00 |
| newconn | Hubble (agent only) | 37.27 ± 5.69 (n=12) | 38.53 ± 6.02 (n=12) | +5.26% [-7.99, +18.51] (n.s.) (< 18.5% at 95%) | 0.401 | 1.000 | recommendationservice 0.80 | 1.00 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 36.20 ± 3.56 | 9.85% | 9.85% | 12 |
| newconn | 37.27 ± 5.69 | 15.26% | 15.26% | 12 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.076 ± 0.003 | 0.009 | - | 0.321 ± 0.025 | 0.047 | - | - | - | - |
| Hubble | 0.114 ± 0.011 | 0.017 | +0.038 [+0.031, +0.045] | 0.365 ± 0.035 | 0.062 | +0.044 [+0.021, +0.068] | +0.44% | +0.016 | <0.001 / <0.001 |
| Hubble (agent only) | 0.086 ± 0.005 | 0.011 | +0.010 [+0.008, +0.012] | 0.319 ± 0.029 | 0.046 | -0.002 [-0.012, +0.008] (n.s.) | -0.02% | -0.003 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.021 [+0.016, +0.025] | +0.004 [-0.007, +0.014] (n.s.) | +0.021 [+0.001, +0.041] | 54% |
| Hubble (agent only) | +0.008 [+0.004, +0.011] | -0.002 [-0.010, +0.006] (n.s.) | -0.001 [-0.017, +0.015] (n.s.) | 77% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.032 [+0.025, +0.038] | +0.030 [-0.011, +0.070] (n.s.) | +0.013 [+0.004, +0.022] | 1.37 → 1.39 | 10% |
| keepalive | Hubble (agent only) | +0.009 [+0.004, +0.014] | +0.009 [-0.036, +0.054] (n.s.) | +0.002 [-0.010, +0.013] (n.s.) | 1.37 → 1.37 | 9% |
| newconn | Hubble | +0.449 [+0.423, +0.475] | +0.601 [+0.541, +0.662] | +0.179 [+0.164, +0.194] | 1.35 → 1.40 | 26% |
| newconn | Hubble (agent only) | +0.107 [+0.105, +0.109] | +0.092 [+0.047, +0.136] | +0.004 [-0.007, +0.015] (n.s.) | 1.35 → 1.30 | 14% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 686 ± 2 | 2.8 | 1.66 | 367 | - | - | 3218 ± 38 | - | - |
| Hubble | 797 ± 19 (peak 812) | 11.3 | 8.13 | 466 | +99 [+96, +102] | +111 [+98, +123] | 3326 ± 37 | +0.62% | <0.001 / <0.001 |
| Hubble (agent only) | 720 ± 4 (peak 735) | 10.3 | 7.40 | 400 | +33 [+30, +36] | +34 [+32, +36] | 3246 ± 43 | +0.21% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Hubble (agent only) |
|---|---|---|---|
| cilium-agent | 0.065 | 0.081 | 0.075 |
| cilium-envoy | 0.008 | 0.007 | 0.008 |
| cilium-operator | 0.004 | 0.003 | 0.004 |
| hubble-relay | 0.000 | 0.010 | 0.000 |
| client-hubble | 0.000 | 0.012 | 0.000 |
| app | 0.063 | 0.059 | 0.060 |
| loadgen | 0.005 | 0.005 | 0.005 |
| k3s | 0.156 | 0.172 | 0.153 |
| k8s-addons | 0.006 | 0.006 | 0.006 |
| os | 0.001 | 0.001 | 0.001 |
| harness | 0.033 | 0.031 | 0.032 |
| node | 0.321 | 0.365 | 0.319 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%. At under 5 req/s the window holds few requests; do not read the p95/p99 deltas.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 2.20 ± 0.07 | 16.1 ± 2.7 | - | 28.6 ± 2.2 | - | 64.0 ± 13.8 | - | 0.00 |
| Hubble | 2.18 ± 0.07 | 14.8 ± 2.1 | -6.4% [-14.8, +2.0] (n.s.) | 28.4 ± 1.8 | -0.1% [-6.4, +6.3] (n.s.) | 54.3 ± 13.9 | -8.6% [-32.2, +15.0] (n.s.) | 0.04 |
| Hubble (agent only) | 2.19 ± 0.06 | 15.4 ± 2.7 | -4.0% [-8.5, +0.4] (n.s.) | 27.9 ± 2.3 | -2.1% [-6.8, +2.5] (n.s.) | 60.8 ± 18.4 | -1.3% [-22.3, +19.6] (n.s.) | 0.01 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 2.9 | 2.84 | 0.03 | - | - | - | - | - |
| Hubble | 3.1 | 3.03 | 0.05 | +156 [+34, +277] | +5793 [+5365, +6221] | +5796 [+5365, +6226] | +8294 [+7166, +9422] | 32.6 (thesis 33.2) |
| Hubble (agent only) | 2.9 | 2.83 | 0.04 | +24 [-41, +89] (n.s.) | +1337 [+1224, +1450] | +1337 [+1224, +1450] | +1644 [+133, +3156] | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 30%. Lost events: 0 in the window, 62 over the whole run (fixed-count tests included). hubble_* series at the end: 307.

| Class | flows/s | share |
|---|---|---|
| app | 12.9 | 27% |
| probe | 20.9 | 43% |
| client_feedback | 2.7 | 6% |
| other | 11.6 | 24% |

### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about - cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.034 [+0.026, +0.042] | +0.039 | +0.042 [+0.007, +0.076] | +0.19% / +0.23% | +72 [+60, +85] | +0.12% |
| Hubble (agent only) | +0.017 [+0.013, +0.022] | +0.020 | +0.002 [-0.021, +0.025] (n.s.) | +0.10% / +0.01% | +39 [+34, +44] | +0.07% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 3 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 30.32 |
| 2 | baseline | 2 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 29.71 |
| 3 | baseline | 3 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 44.00 |
| 4 | baseline | 1 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 38.25 |
| 5 | baseline | 2 | 0.06% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 43.30 |
| 6 | baseline | 1 | 0.07% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 41.47 |
| 7 | baseline | 3 | 0.09% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 41.01 |
| 8 | baseline | 1 | 0.08% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 32.70 |
| 9 | baseline | 1 | 0.16% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 41.79 |
| 10 | baseline | 2 | 0.05% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 42.03 |
| 11 | baseline | 3 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 32.03 |
| 12 | baseline | 2 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 30.58 |
| 1 | Hubble | 2 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 34.29 |
| 2 | Hubble | 1 | 1.27% (high) | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 37.35 |
| 3 | Hubble | 1 | 0.04% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 38.72 |
| 4 | Hubble | 3 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 41.91 |
| 5 | Hubble | 3 | 0.05% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 43.31 |
| 6 | Hubble | 2 | 0.26% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 39.53 |
| 7 | Hubble | 2 | 0.06% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 40.20 |
| 8 | Hubble | 3 | 0.10% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 38.14 |
| 9 | Hubble | 2 | 0.06% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 40.94 |
| 10 | Hubble | 3 | 0.04% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 36.18 |
| 11 | Hubble | 1 | 0.02% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 38.91 |
| 12 | Hubble | 1 | 0.04% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 33.22 |
| 1 | Hubble (agent only) | 1 | 0.02% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 42.70 |
| 2 | Hubble (agent only) | 3 | 0.04% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 40.52 |
| 3 | Hubble (agent only) | 2 | 0.02% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 42.99 |
| 4 | Hubble (agent only) | 2 | 0.03% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 36.10 |
| 5 | Hubble (agent only) | 1 | 0.06% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 41.94 |
| 6 | Hubble (agent only) | 3 | 0.07% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 39.60 |
| 7 | Hubble (agent only) | 1 | 0.25% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 25.12 |
| 8 | Hubble (agent only) | 2 | 0.28% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 35.03 |
| 9 | Hubble (agent only) | 3 | 0.06% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 46.51 |
| 10 | Hubble (agent only) | 1 | 0.04% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 42.99 |
| 11 | Hubble (agent only) | 2 | 0.06% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 38.26 |
| 12 | Hubble (agent only) | 3 | 0.06% | 6ac3eb0dcde73a52e44a8476 | 9ced4e79,ccd38189,ef0f78a9 | 30.63 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 10.52/9.62 | 8.64/7.60 | 8.28/7.36 | 12.15/9.08 | 0.92 |
| 1 | Hubble | 8.49/9.40 | 7.68/7.92 | 10.70/10.85 | 11.95/12.15 | 0.89 |
| 1 | Hubble (agent only) | 7.94/11.03 | 7.26/8.30 | 10.59/8.59 | 8.88/7.50 | 0.89 |
| 2 | baseline | 9.63/11.04 | 7.45/7.62 | 8.69/9.42 | 9.22/9.90 | 0.86 |
| 2 | Hubble | 11.28/11.03 | 11.05/10.43 | 7.86/7.58 | 9.10/9.87 | 1.22 |
| 2 | Hubble (agent only) | 9.74/9.23 | 8.03/8.07 | 7.56/9.65 | 8.30/9.77 | 0.92 |
| 3 | baseline | 9.34/10.61 | 7.84/8.01 | 9.94/8.93 | 8.05/8.75 | 0.90 |
| 3 | Hubble | 11.55/9.33 | 11.01/8.41 | 11.76/9.24 | 9.20/7.88 | 1.10 |
| 3 | Hubble (agent only) | 8.89/10.14 | 9.73/7.72 | 9.46/9.29 | 10.80/9.80 | 0.99 |
| 4 | baseline | 8.61/7.89 | 7.77/7.71 | 12.91/11.04 | 10.61/9.98 | 0.88 |
| 4 | Hubble | 10.05/9.99 | 9.64/9.63 | 10.35/11.94 | 10.53/11.75 | 1.10 |
| 4 | Hubble (agent only) | 10.23/9.99 | 7.69/10.36 | 8.93/9.90 | 9.09/10.58 | 1.03 |
| 5 | baseline | 10.59/9.48 | 8.28/8.29 | 8.57/8.26 | 9.11/8.09 | 0.94 |
| 5 | Hubble | 10.35/9.82 | 10.05/7.70 | 10.72/7.56 | 11.72/6.95 | 1.01 |
| 5 | Hubble (agent only) | 8.48/9.52 | 8.33/8.89 | 9.56/9.24 | 9.71/9.18 | 0.98 |
| 6 | baseline | 10.47/10.04 | 8.15/8.66 | 8.86/9.21 | 7.36/9.23 | 0.96 |
| 6 | Hubble | 10.40/10.78 | 8.34/11.02 | 8.91/9.75 | 8.80/8.36 | 1.10 |
| 6 | Hubble (agent only) | 9.79/10.78 | 9.33/9.11 | 12.54/9.68 | 10.88/7.58 | 1.05 |
| 7 | baseline | 8.08/7.61 | 8.69/8.43 | 8.69/8.39 | 7.78/7.68 | 0.97 |
| 7 | Hubble | 7.96/8.43 | 8.59/8.87 | 8.08/7.55 | 7.94/7.53 | 0.99 |
| 7 | Hubble (agent only) | 8.23/9.21 | 9.10/8.81 | 12.77/12.49 | 12.94/9.86 | 1.02 |
| 8 | baseline | 8.12/7.84 | 9.38/9.76 | 7.82/8.33 | 7.22/9.45 | 1.09 |
| 8 | Hubble | 10.59/12.17 | 10.16/10.35 | 7.52/9.84 | 10.55/12.36 | 1.17 |
| 8 | Hubble (agent only) | 8.79/9.29 | 10.09/9.93 | 8.34/7.66 | 10.45/7.21 | 1.14 |
| 9 | baseline | 8.26/8.03 | 10.19/9.75 | 7.29/8.08 | 6.88/9.77 | 1.13 |
| 9 | Hubble | 8.67/7.20 | 9.72/9.82 | 8.52/9.41 | 9.54/8.57 | 1.11 |
| 9 | Hubble (agent only) | 9.15/8.97 | 9.81/10.47 | 8.94/9.44 | 8.51/8.56 | 1.16 |
| 10 | baseline | 7.43/7.61 | 9.27/8.27 | 10.34/11.38 | 8.29/9.69 | 1.00 |
| 10 | Hubble | 7.96/7.02 | 9.46/8.02 | 9.85/10.84 | 9.53/10.69 | 0.99 |
| 10 | Hubble (agent only) | 8.34/9.16 | 9.35/10.56 | 9.60/9.96 | 9.73/10.08 | 1.13 |
| 11 | baseline | 7.74/11.61 | 7.87/11.03 | 11.43/11.12 | 11.74/11.66 | 1.08 |
| 11 | Hubble | 8.03/8.10 | 8.23/8.72 | 11.76/11.69 | 9.09/8.49 | 0.96 |
| 11 | Hubble (agent only) | 8.04/7.71 | 8.56/8.14 | 10.52/8.40 | 9.90/8.77 | 0.95 |
| 12 | baseline | 11.45/8.06 | 10.88/8.67 | 10.89/10.23 | 11.71/11.78 | 1.11 |
| 12 | Hubble | 9.38/8.35 | 9.00/8.44 | 11.85/10.28 | 12.46/9.95 | 0.99 |
| 12 | Hubble (agent only) | 8.93/10.74 | 8.75/10.66 | 11.32/10.74 | 10.14/11.33 | 1.11 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 38.33 ± 3.82 (n=12) | 39.07 ± 4.49 (n=12) | +2.69% [-6.29, +11.67] (n.s.) (< 11.7% at 95%) | 0.523 | 1.000 |
| keepalive | Hubble (agent only) | 38.33 ± 3.82 (n=12) | 38.88 ± 5.96 (n=12) | +3.04% [-11.20, +17.28] (n.s.) (< 17.3% at 95%) | 0.648 | 1.000 |
| newconn | Hubble | 39.24 ± 4.36 (n=12) | 42.75 ± 5.28 (n=12) | +10.34% [-2.42, +23.10] (n.s.) (< 23.1% at 95%) | 0.102 | 0.204 |
| newconn | Hubble (agent only) | 39.24 ± 4.36 (n=12) | 41.53 ± 5.18 (n=12) | +6.38% [-1.52, +14.27] (n.s.) (< 14.3% at 95%) | 0.103 | 0.204 |
