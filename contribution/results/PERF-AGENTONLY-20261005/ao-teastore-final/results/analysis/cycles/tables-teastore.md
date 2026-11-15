# teastore

Runs used: baseline 12, Hubble 12, Hubble (agent only) 12.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.20 at 12 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.047 [+0.038, +0.055] | <0.001 | <0.001 | +0.042 [+0.033, +0.051] | <0.001 | <0.001 | 12 |
| Δ cluster busy CPU (cores) | Hubble (agent only) | +0.004 [-0.007, +0.015] (n.s.) | 0.455 | 0.455 | -0.000 [-0.012, +0.011] (n.s.) | 0.955 | 0.955 | 12 |
| Δ observer CPU (cores) | Hubble | +0.028 [+0.027, +0.029] | <0.001 | <0.001 | +0.027 [+0.026, +0.029] | <0.001 | <0.001 | 12 |
| Δ observer CPU (cores) | Hubble (agent only) | +0.008 [+0.007, +0.009] | <0.001 | <0.001 | +0.008 [+0.007, +0.009] | <0.001 | <0.001 | 12 |
| Δ app CPU (cores) | Hubble | +0.003 [-0.002, +0.008] (n.s.) | 0.187 | 0.375 | +0.000 [-0.006, +0.007] (n.s.) | 0.909 | 0.909 | 12 |
| Δ app CPU (cores) | Hubble (agent only) | -0.000 [-0.005, +0.004] (n.s.) | 0.839 | 0.839 | -0.003 [-0.010, +0.004] (n.s.) | 0.315 | 0.630 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.017 [+0.016, +0.018] | <0.001 | <0.001 | +0.016 [+0.015, +0.018] | <0.001 | <0.001 | 12 |
| Δ k3s/containerd CPU (cores) | Hubble (agent only) | -0.000 [-0.001, +0.001] (n.s.) | 0.549 | 0.549 | -0.001 [-0.002, +0.000] (n.s.) | 0.083 | 0.083 | 12 |
| Δ observer anon memory (MiB, primary) | Hubble | +85 [+82, +87] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer anon memory (MiB, primary) | Hubble (agent only) | +20 [+18, +23] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble | +100 [+69, +131] | <0.001 | <0.001 | - | - | - | 12 |
| Δ observer memory, working set (MiB) | Hubble (agent only) | +13 [+2, +25] | 0.030 | 0.030 | - | - | - | 12 |
| fixed-count time, keep-alive | Hubble | +1.1% [-4.6, +6.8] (n.s.) | 0.681 | 1.000 | -0.4% [-6.0, +5.2] (n.s.) | 0.888 | 0.888 | 12 |
| fixed-count time, keep-alive | Hubble (agent only) | -0.6% [-5.1, +4.0] (n.s.) | 0.792 | 1.000 | -2.1% [-7.2, +3.0] (n.s.) | 0.379 | 0.757 | 12 |
| fixed-count time, new conn | Hubble | +21.4% [+15.0, +27.7] | <0.001 | <0.001 | +18.7% [+12.4, +25.1] | <0.001 | <0.001 | 12 |
| fixed-count time, new conn | Hubble (agent only) | -0.1% [-4.7, +4.5] (n.s.) | 0.960 | 0.960 | -2.1% [-6.4, +2.2] (n.s.) | 0.310 | 0.310 | 12 |
| canary speed, workers, steady window (check) | Hubble | -1.16% [-2.28, -0.05] | 0.043 | 0.085 | - | - | - | 12 |
| canary speed, workers, steady window (check) | Hubble (agent only) | -1.20% [-3.44, +1.04] (n.s.) | 0.264 | 0.264 | - | - | - | 12 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 4.9% raw, 6.0% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.35; new conn: CV of the baseline time across cycles 5.0% raw, 5.5% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.08.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-05 18:14 | hubble baseline hubble_agent | 47.1 | 45.9 | 46.8 | 45.9 | 0.274 | 0.271 | 15.37 | 0.99 | 15.39 |
| 2 | 10-05 18:50 | hubble hubble_agent baseline | 49.4 | 47.1 | 49.3 | 46.9 | 0.278 | 0.268 | 15.05 | 0.97 | 15.24 |
| 3 | 10-05 19:25 | hubble_agent hubble baseline | 48.7 | 48.2 | 48.7 | 46.7 | 0.268 | 0.268 | 15.45 | 0.99 | 15.44 |
| 4 | 10-05 20:01 | baseline hubble hubble_agent | 45.6 | 44.1 | 46.0 | 44.3 | 0.280 | 0.276 | 15.39 | 0.99 | 15.36 |
| 5 | 10-05 20:36 | hubble_agent baseline hubble | 47.4 | 47.2 | 47.7 | 46.3 | 0.268 | 0.270 | 15.70 | 1.01 | 15.64 |
| 6 | 10-05 21:12 | baseline hubble_agent hubble | 51.6 | 50.4 | 51.5 | 49.3 | 0.271 | 0.267 | 15.18 | 0.98 | 15.38 |
| 7 | 10-05 21:47 | hubble baseline hubble_agent | 46.6 | 46.9 | 46.5 | 46.4 | 0.260 | 0.269 | 15.94 | 1.03 | 15.58 |
| 8 | 10-05 22:23 | baseline hubble hubble_agent | 49.7 | 47.6 | 49.5 | 48.0 | 0.274 | 0.270 | 15.37 | 0.99 | 14.70 |
| 9 | 10-05 22:58 | hubble hubble_agent baseline | 51.0 | 51.1 | 50.8 | 50.4 | 0.258 | 0.265 | 15.89 | 1.02 | 15.49 |
| 10 | 10-05 23:34 | hubble_agent baseline hubble | 52.4 | 52.1 | 52.4 | 52.4 | 0.254 | 0.259 | 15.77 | 1.01 | 15.68 |
| 11 | 10-06 00:10 | baseline hubble_agent hubble | 52.6 | 53.7 | 53.0 | 52.7 | 0.262 | 0.266 | 15.76 | 1.01 | 15.59 |
| 12 | 10-06 00:45 | hubble_agent hubble baseline | 46.8 | 45.2 | 46.6 | 46.9 | 0.260 | 0.272 | 16.25 | 1.05 | 16.15 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Hubble; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.028 [+0.027, +0.029] | <0.001 | +0.028 | <0.001 | +0.028 [+0.027, +0.029] | 11 | robust |
| Δ observer CPU | Hubble (agent only) | +0.008 [+0.007, +0.009] | <0.001 | +0.008 | <0.001 | +0.008 [+0.007, +0.009] | 12 | robust |
| Δ observer anon memory | Hubble | +85 [+82, +87] | <0.001 | +85 | <0.001 | +85 [+82, +87] | 11 | robust |
| Δ observer anon memory | Hubble (agent only) | +20 [+18, +23] | <0.001 | +20 | <0.001 | +20 [+18, +23] | 12 | robust |
| fixed-count time, keep-alive | Hubble | +1.1% [-4.6, +6.8] (n.s.) | 1.000 | +1.6% | 0.791 | -0.0% [-5.8, +5.7] (n.s.) | 11 | n.s. (primary) |
| fixed-count time, keep-alive | Hubble (agent only) | -0.6% [-5.1, +4.0] (n.s.) | 1.000 | -0.3% | 0.791 | -0.6% [-5.1, +4.0] (n.s.) | 12 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +21.4% [+15.0, +27.7] | <0.001 | +22.6% | <0.001 | +20.2% [+13.7, +26.6] | 11 | robust |
| fixed-count time, new conn | Hubble (agent only) | -0.1% [-4.7, +4.5] (n.s.) | 1.000 | -0.2% | 0.970 | -0.1% [-4.7, +4.5] (n.s.) | 12 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 9152 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **node-bound** (baseline newconn bottleneck throttled 0.00 s/s), so node CPU limits the test. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 49.08 ± 2.41 (n=12) | 49.47 ± 3.05 (n=12) | +1.10% [-4.63, +6.83] (n.s.) (< 6.8% at 95%) | 0.681 | 1.000 | teastore-persistence 0.00 | 0.18 |
| keepalive | Hubble (agent only) | 49.08 ± 2.41 (n=12) | 48.73 ± 3.13 (n=12) | -0.56% [-5.08, +3.96] (n.s.) (< 4.0% at 95%) | 0.792 | 1.000 | teastore-registry 0.00 | 0.18 |
| newconn | Hubble | 49.06 ± 2.43 (n=12) | 59.36 ± 3.19 (n=12) | +21.35% [+14.98, +27.73] | <0.001 | <0.001 | teastore-persistence 0.00 | 1.17 |
| newconn | Hubble (agent only) | 49.06 ± 2.43 (n=12) | 48.92 ± 3.08 (n=12) | -0.11% [-4.71, +4.49] (n.s.) (< 4.5% at 95%) | 0.960 | 1.000 | teastore-registry 0.00 | 1.17 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 49.08 ± 2.41 | 4.91% | 4.91% | 12 |
| newconn | 49.06 ± 2.43 | 4.95% | 4.95% | 12 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.044 ± 0.002 | 0.004 | - | 0.424 ± 0.014 | 0.057 | - | - | - | - |
| Hubble | 0.072 ± 0.003 | 0.008 | +0.028 [+0.027, +0.029] | 0.471 ± 0.011 | 0.062 | +0.047 [+0.038, +0.055] | +0.47% | +0.017 | <0.001 / <0.001 |
| Hubble (agent only) | 0.052 ± 0.002 | 0.004 | +0.008 [+0.007, +0.009] | 0.428 ± 0.009 | 0.056 | +0.004 [-0.007, +0.015] (n.s.) | +0.04% | -0.000 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.006 [+0.005, +0.007] | +0.002 [-0.001, +0.004] (n.s.) | -0.001 [-0.012, +0.009] (n.s.) | 22% |
| Hubble (agent only) | +0.003 [+0.002, +0.004] | +0.000 [-0.004, +0.005] (n.s.) | -0.004 [-0.019, +0.012] (n.s.) | 34% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.159 [+0.150, +0.168] | +0.311 [+0.211, +0.411] | +0.106 [+0.102, +0.110] | 0.00 → 0.00 | 14% |
| keepalive | Hubble (agent only) | +0.033 [+0.029, +0.036] | +0.052 [-0.036, +0.140] (n.s.) | -0.002 [-0.004, +0.001] (n.s.) | 0.00 → 0.00 | 9% |
| newconn | Hubble | +0.616 [+0.593, +0.638] | +0.684 [+0.596, +0.771] | +0.273 [+0.264, +0.281] | 0.00 → 0.00 | 30% |
| newconn | Hubble (agent only) | +0.157 [+0.150, +0.164] | +0.171 [+0.096, +0.247] | +0.001 [-0.001, +0.003] (n.s.) | 0.00 → 0.00 | 16% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 668 ± 20 | 2.1 | 1.15 | 370 | - | - | 5752 ± 109 | - | - |
| Hubble | 768 ± 57 (peak 787) | 13.8 | 10.09 | 454 | +85 [+82, +87] | +100 [+69, +131] | 5784 ± 103 | +0.53% | <0.001 / <0.001 |
| Hubble (agent only) | 681 ± 17 (peak 698) | 11.4 | 8.38 | 390 | +20 [+18, +23] | +13 [+2, +25] | 5659 ± 105 | +0.13% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Hubble (agent only) |
|---|---|---|---|
| cilium-agent | 0.036 | 0.050 | 0.045 |
| cilium-envoy | 0.006 | 0.005 | 0.006 |
| cilium-operator | 0.002 | 0.002 | 0.002 |
| hubble-relay | 0.000 | 0.007 | 0.000 |
| client-hubble | 0.000 | 0.009 | 0.000 |
| app | 0.267 | 0.270 | 0.267 |
| loadgen | 0.017 | 0.018 | 0.018 |
| k3s | 0.080 | 0.097 | 0.079 |
| k8s-addons | 0.003 | 0.003 | 0.003 |
| os | 0.001 | 0.001 | 0.001 |
| harness | 0.020 | 0.020 | 0.020 |
| node | 0.424 | 0.471 | 0.428 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 10.84 ± 0.05 | 9.4 ± 0.5 | - | 26.2 ± 1.0 | - | 30.9 ± 1.7 | - | 6.55 |
| Hubble | 10.88 ± 0.13 | 9.7 ± 0.5 | +2.8% [-0.4, +6.0] (n.s.) | 27.5 ± 1.3 | +5.2% [+1.8, +8.5] | 32.7 ± 2.6 | +5.8% [+0.7, +10.8] | 6.65 |
| Hubble (agent only) | 10.96 ± 0.11 | 9.6 ± 0.5 | +2.1% [-3.5, +7.8] (n.s.) | 26.6 ± 0.7 | +1.7% [-1.1, +4.5] (n.s.) | 31.0 ± 1.3 | +0.5% [-3.7, +4.8] (n.s.) | 7.23 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 3.0 | 0.07 | 2.91 | - | - | - | - | - |
| Hubble | 3.2 | 0.25 | 2.95 | +857 [+802, +912] | +4108 [+4024, +4193] | +3506 [+3434, +3579] | +5315 [+5018, +5611] | 39.3 (thesis 44.7) |
| Hubble (agent only) | 3.0 | 0.07 | 2.98 | +165 [+149, +182] | +858 [+839, +877] | +732 [+716, +748] | +823 [+633, +1012] | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 32%. Lost events: 0 in the window, 88 over the whole run (fixed-count tests included). hubble_* series at the end: 264.

| Class | flows/s | share |
|---|---|---|
| app | 39.5 | 73% |
| probe | 0.3 | 1% |
| client_feedback | 2.7 | 5% |
| other | 11.4 | 21% |

### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about - cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.024 [+0.022, +0.026] | +0.030 | +0.039 [+0.023, +0.056] | +0.13% / +0.22% | +66 [-7, +138] (n.s.) | +0.11% |
| Hubble (agent only) | +0.012 [+0.010, +0.013] | +0.016 | +0.001 [-0.019, +0.021] (n.s.) | +0.06% / +0.01% | -1 [-35, +33] (n.s.) | -0.00% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 2 | 0.03% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 46.78 |
| 2 | baseline | 3 | 0.11% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 49.27 |
| 3 | baseline | 3 | 0.13% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 48.70 |
| 4 | baseline | 1 | 0.04% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 45.96 |
| 5 | baseline | 2 | 0.03% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 47.74 |
| 6 | baseline | 1 | 0.06% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 51.51 |
| 7 | baseline | 2 | 0.02% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 46.49 |
| 8 | baseline | 1 | 0.04% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 49.45 |
| 9 | baseline | 3 | 0.04% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 50.82 |
| 10 | baseline | 2 | 0.02% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 52.38 |
| 11 | baseline | 1 | 0.06% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 52.99 |
| 12 | baseline | 3 | 0.04% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 46.63 |
| 1 | Hubble | 1 | 0.05% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 62.81 |
| 2 | Hubble | 1 | 0.63% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 56.35 |
| 3 | Hubble | 2 | 0.02% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 58.03 |
| 4 | Hubble | 2 | 0.08% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 56.96 |
| 5 | Hubble | 3 | 0.02% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 65.45 |
| 6 | Hubble | 3 | 0.05% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 55.56 |
| 7 | Hubble | 1 | 0.04% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 59.72 |
| 8 | Hubble | 2 | 0.04% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 63.13 |
| 9 | Hubble | 1 | 0.02% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 61.60 |
| 10 | Hubble | 3 | 0.74% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 58.10 |
| 11 | Hubble | 3 | 0.02% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 56.16 |
| 12 | Hubble | 2 | 0.03% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 58.43 |
| 1 | Hubble (agent only) | 3 | 0.02% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 50.76 |
| 2 | Hubble (agent only) | 2 | 0.04% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 44.53 |
| 3 | Hubble (agent only) | 1 | 0.13% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 44.24 |
| 4 | Hubble (agent only) | 3 | 0.01% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 51.35 |
| 5 | Hubble (agent only) | 1 | 0.03% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 48.00 |
| 6 | Hubble (agent only) | 2 | 0.03% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 47.93 |
| 7 | Hubble (agent only) | 3 | 0.06% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 45.45 |
| 8 | Hubble (agent only) | 3 | 0.03% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 53.68 |
| 9 | Hubble (agent only) | 2 | 0.09% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 51.73 |
| 10 | Hubble (agent only) | 1 | 0.06% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 51.93 |
| 11 | Hubble (agent only) | 2 | 0.03% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 49.29 |
| 12 | Hubble (agent only) | 1 | 0.01% | 6ac3e838c5845e5b26c4ef44 | 78dae5a5,0557a80e,19a2ce23 | 48.20 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 15.48/14.93 | 15.40/15.33 | 15.02/15.30 | 15.14/15.35 | 0.99 |
| 1 | Hubble | 15.82/14.47 | 15.85/14.58 | 14.59/13.88 | 14.96/14.16 | 0.98 |
| 1 | Hubble (agent only) | 15.45/15.17 | 15.70/15.50 | 15.29/15.37 | 14.57/15.58 | 1.00 |
| 2 | baseline | 14.75/15.10 | 15.26/14.84 | 14.39/15.24 | 14.62/14.94 | 0.97 |
| 2 | Hubble | 15.82/15.38 | 15.23/15.09 | 15.15/14.59 | 14.91/14.22 | 0.98 |
| 2 | Hubble (agent only) | 15.54/15.61 | 15.42/15.62 | 14.91/15.45 | 14.51/15.57 | 1.00 |
| 3 | baseline | 15.15/15.29 | 15.34/15.56 | 14.94/15.78 | 14.87/14.94 | 0.99 |
| 3 | Hubble | 15.31/15.28 | 15.56/15.27 | 15.17/15.40 | 15.17/14.59 | 0.99 |
| 3 | Hubble (agent only) | 15.79/15.37 | 15.42/15.48 | 14.29/14.62 | 14.55/15.49 | 0.99 |
| 4 | baseline | 15.98/15.30 | 15.64/15.14 | 14.82/15.21 | 15.02/14.91 | 0.99 |
| 4 | Hubble | 15.83/15.50 | 15.70/15.37 | 15.80/15.09 | 15.14/14.41 | 1.00 |
| 4 | Hubble (agent only) | 14.90/15.75 | 14.52/15.78 | 14.35/15.31 | 14.18/15.42 | 0.97 |
| 5 | baseline | 16.10/15.96 | 15.82/15.58 | 15.58/15.37 | 15.06/15.11 | 1.01 |
| 5 | Hubble | 15.58/15.40 | 15.64/15.28 | 15.56/14.53 | 15.44/14.77 | 0.99 |
| 5 | Hubble (agent only) | 15.69/15.66 | 15.69/15.81 | 15.34/15.38 | 15.17/15.57 | 1.01 |
| 6 | baseline | 14.79/15.50 | 14.81/15.55 | 14.66/15.69 | 14.43/15.30 | 0.98 |
| 6 | Hubble | 15.65/15.34 | 15.75/14.93 | 15.60/14.64 | 14.45/13.95 | 0.99 |
| 6 | Hubble (agent only) | 15.81/16.32 | 15.41/15.85 | 14.77/15.75 | 14.29/15.16 | 1.01 |
| 7 | baseline | 15.68/16.12 | 15.76/16.12 | 15.27/15.94 | 15.24/15.77 | 1.03 |
| 7 | Hubble | 15.74/16.03 | 15.79/15.72 | 15.53/15.33 | 15.25/14.76 | 1.01 |
| 7 | Hubble (agent only) | 15.32/15.81 | 14.63/15.45 | 14.66/15.45 | 14.63/15.30 | 0.97 |
| 8 | baseline | 16.17/15.50 | 15.47/15.27 | 14.58/15.17 | 15.23/14.94 | 0.99 |
| 8 | Hubble | 14.78/15.32 | 14.28/15.05 | 14.18/14.98 | 14.06/15.04 | 0.94 |
| 8 | Hubble (agent only) | 15.11/12.96 | 14.99/13.12 | 14.92/12.91 | 14.65/13.17 | 0.90 |
| 9 | baseline | 15.98/16.12 | 15.71/16.08 | 15.57/15.55 | 15.10/15.75 | 1.02 |
| 9 | Hubble | 14.74/15.83 | 15.54/15.36 | 15.40/15.06 | 15.11/15.05 | 0.99 |
| 9 | Hubble (agent only) | 15.47/15.83 | 14.98/15.24 | 14.24/15.38 | 14.06/15.33 | 0.97 |
| 10 | baseline | 15.63/15.74 | 15.62/15.92 | 15.35/15.52 | 15.70/15.39 | 1.01 |
| 10 | Hubble | 16.25/16.02 | 16.03/15.27 | 15.52/14.20 | 15.91/15.41 | 1.01 |
| 10 | Hubble (agent only) | 15.81/15.56 | 15.46/15.76 | 14.66/15.58 | 14.45/15.52 | 1.00 |
| 11 | baseline | 16.16/15.81 | 15.72/15.81 | 15.67/16.07 | 15.53/15.37 | 1.01 |
| 11 | Hubble | 15.24/15.93 | 14.99/15.43 | 15.12/15.36 | 15.19/14.75 | 0.98 |
| 11 | Hubble (agent only) | 16.09/16.17 | 15.77/15.83 | 14.83/15.52 | 14.39/15.04 | 1.02 |
| 12 | baseline | 16.77/16.51 | 16.31/16.20 | 14.55/15.49 | 15.22/16.06 | 1.05 |
| 12 | Hubble | 16.46/15.83 | 16.39/15.76 | 16.09/14.73 | 15.19/15.18 | 1.03 |
| 12 | Hubble (agent only) | 16.50/16.22 | 16.16/16.08 | 16.05/15.82 | 15.21/16.00 | 1.04 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 48.28 ± 2.91 (n=12) | 47.91 ± 2.55 (n=12) | -0.37% [-5.98, +5.25] (n.s.) (< 5.2% at 95%) | 0.888 | 0.888 |
| keepalive | Hubble (agent only) | 48.28 ± 2.91 (n=12) | 47.13 ± 2.97 (n=12) | -2.12% [-7.20, +2.96] (n.s.) (< 3.0% at 95%) | 0.379 | 0.757 |
| newconn | Hubble | 48.02 ± 2.64 (n=12) | 56.84 ± 3.53 (n=12) | +18.71% [+12.37, +25.05] | <0.001 | <0.001 |
| newconn | Hubble (agent only) | 48.02 ± 2.64 (n=12) | 46.91 ± 2.54 (n=12) | -2.10% [-6.44, +2.24] (n.s.) (< 2.2% at 95%) | 0.310 | 0.310 |
