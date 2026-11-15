# otel

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.044 [+0.039, +0.049] | <0.001 | <0.001 | +0.038 [+0.029, +0.047] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.067 [+0.057, +0.078] | <0.001 | <0.001 | +0.061 [+0.044, +0.077] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.096 [+0.087, +0.106] | <0.001 | <0.001 | +0.101 [+0.088, +0.114] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.090 [+0.082, +0.098] | <0.001 | <0.001 | +0.088 [+0.075, +0.101] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Hubble | +0.035 [+0.034, +0.037] | <0.001 | <0.001 | +0.034 [+0.032, +0.035] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.065 [+0.063, +0.067] | <0.001 | <0.001 | +0.062 [+0.059, +0.066] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.069 [+0.068, +0.071] | <0.001 | <0.001 | +0.070 [+0.068, +0.072] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.069 [+0.068, +0.070] | <0.001 | <0.001 | +0.068 [+0.066, +0.071] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | -0.001 [-0.004, +0.002] (n.s.) | 0.611 | 1.000 | -0.003 [-0.009, +0.003] (n.s.) | 0.273 | 1.000 | 10 |
| Δ app CPU (cores) | Otterize | -0.002 [-0.006, +0.003] (n.s.) | 0.409 | 1.000 | -0.004 [-0.013, +0.005] (n.s.) | 0.325 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | +0.000 [-0.003, +0.003] (n.s.) | 0.865 | 1.000 | +0.003 [-0.004, +0.010] (n.s.) | 0.346 | 1.000 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | -0.002 [-0.005, +0.001] (n.s.) | 0.252 | 1.000 | -0.002 [-0.010, +0.005] (n.s.) | 0.489 | 1.000 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.020 [+0.019, +0.022] | <0.001 | <0.001 | +0.018 [+0.015, +0.021] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.005 [+0.002, +0.007] | 0.001 | 0.001 | +0.003 [+0.000, +0.007] | 0.035 | 0.035 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.024 [+0.022, +0.026] | <0.001 | <0.001 | +0.025 [+0.022, +0.028] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.023 [+0.021, +0.024] | <0.001 | <0.001 | +0.022 [+0.019, +0.026] | <0.001 | <0.001 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +112 [+109, +116] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +81 [+79, +82] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +135 [+132, +138] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +115 [+112, +118] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +134 [+105, +163] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +90 [+76, +105] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +153 [+149, +156] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +142 [+100, +185] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | +15.2% [+2.5, +28.0] | 0.025 | 0.064 | +12.5% [+1.1, +23.9] | 0.035 | 0.070 | 10 |
| fixed-count time, keep-alive | Otterize | +20.2% [+14.0, +26.5] | <0.001 | <0.001 | +18.6% [+9.6, +27.7] | 0.001 | 0.005 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | +17.4% [+3.3, +31.6] | 0.021 | 0.064 | +18.7% [+4.9, +32.6] | 0.014 | 0.041 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | +3.2% [-9.7, +16.1] (n.s.) | 0.589 | 0.589 | +1.5% [-12.4, +15.4] (n.s.) | 0.815 | 0.815 | 10 |
| fixed-count time, new conn | Hubble | +30.3% [+15.6, +45.0] | 0.001 | 0.005 | +26.9% [+11.1, +42.7] | 0.004 | 0.016 | 10 |
| fixed-count time, new conn | Otterize | +19.6% [+0.5, +38.7] | 0.045 | 0.135 | +18.0% [-4.6, +40.6] (n.s.) | 0.104 | 0.250 | 10 |
| fixed-count time, new conn | IG trace_tcp | +16.6% [-1.7, +34.9] (n.s.) | 0.071 | 0.141 | +17.0% [-2.7, +36.8] (n.s.) | 0.083 | 0.250 | 10 |
| fixed-count time, new conn | IG snapshot_socket | +7.8% [-11.4, +27.0] (n.s.) | 0.384 | 0.384 | +6.9% [-15.8, +29.6] (n.s.) | 0.508 | 0.508 | 10 |
| canary speed, workers, steady window (check) | Hubble | -1.77% [-5.40, +1.85] (n.s.) | 0.297 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | -1.75% [-7.04, +3.54] (n.s.) | 0.473 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | +1.61% [-2.56, +5.78] (n.s.) | 0.406 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | -0.22% [-4.67, +4.23] (n.s.) | 0.914 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 5.8% raw, 8.0% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.24; new conn: CV of the baseline time across cycles 13.9% raw, 18.0% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.64.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 10-04 16:09 | hubble baseline otterize ig_snap ig_tcp | 31.2 | 29.3 | 33.1 | 29.9 | 0.146 | 0.146 | 15.87 | 1.00 | 15.60 |
| 12 | 10-04 17:19 | ig_snap ig_tcp baseline otterize hubble | 30.6 | 28.0 | 37.2 | 35.5 | 0.147 | 0.146 | 15.82 | 1.00 | 15.72 |
| 13 | 10-04 18:18 | baseline hubble ig_snap otterize ig_tcp | 34.9 | 33.1 | 39.8 | 37.2 | 0.155 | 0.153 | 15.71 | 0.99 | 15.61 |
| 14 | 10-04 19:16 | ig_snap baseline ig_tcp hubble otterize | 30.2 | 27.5 | 32.8 | 29.6 | 0.155 | 0.150 | 15.33 | 0.97 | 15.70 |
| 15 | 10-04 20:41 | otterize ig_tcp hubble ig_snap baseline | 31.5 | 29.5 | 38.2 | 36.3 | 0.144 | 0.146 | 16.13 | 1.02 | 15.69 |
| 16 | 10-04 21:53 | hubble otterize baseline ig_tcp ig_snap | 30.6 | 28.5 | 36.2 | 34.4 | 0.142 | 0.145 | 16.17 | 1.02 | 16.07 |
| 17 | 10-04 22:52 | baseline ig_snap hubble ig_tcp otterize | 32.2 | 30.1 | 46.7 | 45.6 | 0.144 | 0.147 | 16.14 | 1.02 | 15.46 |
| 18 | 10-05 00:13 | ig_tcp ig_snap otterize baseline hubble | 29.6 | 24.2 | 30.7 | 24.4 | 0.143 | 0.123 | 13.93 | 0.88 | 15.39 |
| 19 | 10-05 01:36 | ig_tcp otterize ig_snap hubble baseline | 28.1 | 27.0 | 29.4 | 27.1 | 0.141 | 0.141 | 15.88 | 1.00 | 15.27 |
| 20 | 10-05 02:47 | otterize hubble ig_tcp baseline ig_snap | 30.2 | 28.9 | 37.1 | 35.6 | 0.149 | 0.149 | 15.96 | 1.01 | 15.52 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 11 Hubble; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.035 [+0.034, +0.037] | <0.001 | +0.036 | 0.002 | +0.035 [+0.034, +0.037] | 9 | robust |
| Δ observer CPU | Otterize | +0.065 [+0.063, +0.067] | <0.001 | +0.065 | 0.002 | +0.065 [+0.063, +0.067] | 10 | robust |
| Δ observer CPU | IG trace_tcp | +0.069 [+0.068, +0.071] | <0.001 | +0.070 | 0.002 | +0.069 [+0.068, +0.071] | 10 | robust |
| Δ observer CPU | IG snapshot_socket | +0.069 [+0.068, +0.070] | <0.001 | +0.069 | 0.002 | +0.069 [+0.068, +0.070] | 10 | robust |
| Δ observer anon memory | Hubble | +112 [+109, +116] | <0.001 | +113 | 0.002 | +113 [+109, +117] | 9 | robust |
| Δ observer anon memory | Otterize | +81 [+79, +82] | <0.001 | +81 | 0.002 | +81 [+79, +82] | 10 | robust |
| Δ observer anon memory | IG trace_tcp | +135 [+132, +138] | <0.001 | +135 | 0.002 | +135 [+132, +138] | 10 | robust |
| Δ observer anon memory | IG snapshot_socket | +115 [+112, +118] | <0.001 | +113 | 0.002 | +115 [+112, +118] | 10 | robust |
| fixed-count time, keep-alive | Hubble | +15.2% [+2.5, +28.0] | 0.128 | +11.5% | 0.020 | +15.7% [+1.1, +30.2] | 9 | n.s. (primary) |
| fixed-count time, keep-alive | Otterize | +20.2% [+14.0, +26.5] | <0.001 | +20.5% | 0.002 | +20.2% [+14.0, +26.5] | 10 | robust |
| fixed-count time, keep-alive | IG trace_tcp | +17.4% [+3.3, +31.6] | 0.128 | +17.0% | 0.027 | +17.4% [+3.3, +31.6] | 10 | n.s. (primary) |
| fixed-count time, keep-alive | IG snapshot_socket | +3.2% [-9.7, +16.1] (n.s.) | 0.768 | +0.3% | 1.000 | +3.2% [-9.7, +16.1] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +30.3% [+15.6, +45.0] | 0.008 | +30.0% | 0.002 | +29.0% [+12.6, +45.4] | 9 | robust |
| fixed-count time, new conn | Otterize | +19.6% [+0.5, +38.7] | 0.180 | +16.1% | 0.027 | +19.6% [+0.5, +38.7] | 10 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | +16.6% [-1.7, +34.9] (n.s.) | 0.212 | +13.0% | 0.064 | +16.6% [-1.7, +34.9] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | IG snapshot_socket | +7.8% [-11.4, +27.0] (n.s.) | 0.768 | +3.8% | 0.557 | +7.8% [-11.4, +27.0] (n.s.) | 10 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 7040 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **node-bound** (baseline newconn bottleneck throttled 0.00 s/s), so node CPU limits the test. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 30.93 ± 1.78 (n=10) | 35.49 ± 4.59 (n=10) | +15.25% [+2.46, +28.04] | 0.025 | 0.128 | opentelemetry-demo-quoteservice 0.00 | 0.00 |
| keepalive | Otterize | 30.93 ± 1.78 (n=10) | 37.17 ± 3.27 (n=10) | +20.22% [+13.95, +26.49] | <0.001 | <0.001 | opentelemetry-demo-shippingservice 0.00 | 0.00 |
| keepalive | IG trace_tcp | 30.93 ± 1.78 (n=10) | 36.22 ± 5.68 (n=10) | +17.45% [+3.26, +31.63] | 0.021 | 0.128 | opentelemetry-demo-currencyservice 0.00 | 0.00 |
| keepalive | IG snapshot_socket | 30.93 ± 1.78 (n=10) | 31.74 ± 4.63 (n=10) | +3.19% [-9.69, +16.08] (n.s.) (< 16.1% at 95%) | 0.589 | 0.768 | opentelemetry-demo-checkoutservice 0.00 | 0.00 |
| newconn | Hubble | 36.12 ± 5.03 (n=10) | 46.30 ± 3.76 (n=10) | +30.32% [+15.64, +44.99] | 0.001 | 0.008 | opentelemetry-demo-quoteservice 0.00 | 1.00 |
| newconn | Otterize | 36.12 ± 5.03 (n=10) | 42.57 ± 7.74 (n=10) | +19.59% [+0.53, +38.65] | 0.045 | 0.180 | opentelemetry-demo-shippingservice 0.00 | 1.00 |
| newconn | IG trace_tcp | 36.12 ± 5.03 (n=10) | 41.33 ± 6.87 (n=10) | +16.58% [-1.71, +34.87] (n.s.) (< 34.9% at 95%) | 0.071 | 0.212 | opentelemetry-demo-currencyservice 0.00 | 1.00 |
| newconn | IG snapshot_socket | 36.12 ± 5.03 (n=10) | 37.96 ± 6.03 (n=10) | +7.78% [-11.45, +27.01] (n.s.) (< 27.0% at 95%) | 0.384 | 0.768 | opentelemetry-demo-checkoutservice 0.00 | 1.00 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 30.93 ± 1.78 | 5.77% | 5.77% | 10 |
| newconn | 36.12 ± 5.03 | 13.93% | 13.93% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.040 ± 0.002 | 0.004 | - | 0.305 ± 0.011 | 0.034 | - | - | - | - |
| Hubble | 0.075 ± 0.003 | 0.007 | +0.035 [+0.034, +0.037] | 0.349 ± 0.009 | 0.037 | +0.044 [+0.039, +0.049] | +0.44% | +0.020 | <0.001 / <0.001 |
| Otterize | 0.105 ± 0.003 | 0.006 | +0.065 [+0.063, +0.067] | 0.372 ± 0.012 | 0.032 | +0.067 [+0.057, +0.078] | +0.67% | +0.005 | <0.001 / <0.001 |
| IG trace_tcp | 0.109 ± 0.003 | 0.007 | +0.069 [+0.068, +0.071] | 0.401 ± 0.010 | 0.035 | +0.096 [+0.087, +0.106] | +0.96% | +0.024 | <0.001 / <0.001 |
| IG snapshot_socket | 0.109 ± 0.003 | 0.008 | +0.069 [+0.068, +0.070] | 0.395 ± 0.009 | 0.033 | +0.090 [+0.082, +0.098] | +0.90% | +0.023 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.024 [+0.022, +0.026] | +0.015 [+0.011, +0.018] | +0.029 [+0.022, +0.035] | 67% |
| Otterize | +0.064 [+0.063, +0.066] | +0.010 [+0.007, +0.012] | +0.073 [+0.066, +0.079] | 100% |
| IG trace_tcp | +0.068 [+0.067, +0.070] | +0.024 [+0.022, +0.027] | +0.089 [+0.083, +0.095] | 98% |
| IG snapshot_socket | +0.068 [+0.067, +0.069] | +0.024 [+0.020, +0.028] | +0.090 [+0.083, +0.098] | 98% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.039 [+0.036, +0.042] | +0.735 [-0.146, +1.617] (n.s.) | +0.002 [-0.024, +0.028] (n.s.) | 0.00 → 0.00 | 10% |
| keepalive | Otterize | +0.073 [+0.071, +0.075] | +0.640 [-0.095, +1.376] (n.s.) | -0.023 [-0.041, -0.004] | 0.00 → 0.00 | 9% |
| keepalive | IG trace_tcp | +0.079 [+0.075, +0.082] | +0.279 [-0.247, +0.805] (n.s.) | +0.006 [-0.012, +0.024] (n.s.) | 0.00 → 0.00 | 10% |
| keepalive | IG snapshot_socket | +0.079 [+0.076, +0.081] | +0.255 [-0.326, +0.836] (n.s.) | +0.026 [+0.002, +0.050] | 0.00 → 0.00 | 11% |
| newconn | Hubble | +0.765 [+0.732, +0.798] | +1.403 [+0.475, +2.331] | +0.352 [+0.325, +0.380] | 0.00 → 0.00 | 41% |
| newconn | Otterize | +0.094 [+0.089, +0.099] | +0.432 [-0.257, +1.121] (n.s.) | -0.010 [-0.039, +0.018] (n.s.) | 0.00 → 0.00 | 13% |
| newconn | IG trace_tcp | +0.265 [+0.222, +0.308] | +0.024 [-0.805, +0.853] (n.s.) | +0.308 [+0.208, +0.409] | 0.00 → 0.00 | 30% |
| newconn | IG snapshot_socket | +0.081 [+0.077, +0.085] | -0.032 [-0.834, +0.770] (n.s.) | +0.024 [-0.004, +0.051] (n.s.) | 0.00 → 0.00 | 16% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 664 ± 11 | 2.2 | 1.12 | 375 | - | - | 4833 ± 65 | - | - |
| Hubble | 798 ± 51 (peak 808) | 6.0 | 4.20 | 487 | +112 [+109, +116] | +134 [+105, +163] | 4953 ± 70 | +0.70% | <0.001 / <0.001 |
| Otterize | 754 ± 32 (peak 759) | 3.0 | 1.61 | 456 | +81 [+79, +82] | +90 [+76, +105] | 4930 ± 65 | +0.50% | <0.001 / <0.001 |
| IG trace_tcp | 816 ± 13 (peak 838) | 12.0 | -7.80 | 510 | +135 [+132, +138] | +153 [+149, +156] | 5053 ± 40 | +0.84% | <0.001 / <0.001 |
| IG snapshot_socket | 806 ± 71 (peak 853) | 15.6 | 5.23 | 490 | +115 [+112, +118] | +142 [+100, +185] | 5004 ± 60 | +0.72% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.034 | 0.051 | 0.034 | 0.035 | 0.035 |
| cilium-envoy | 0.004 | 0.004 | 0.004 | 0.004 | 0.004 |
| cilium-operator | 0.002 | 0.002 | 0.002 | 0.002 | 0.002 |
| hubble-relay | 0.000 | 0.008 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.005 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.059 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.068 | 0.068 |
| client-hubble | 0.000 | 0.010 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 |
| app | 0.147 | 0.146 | 0.145 | 0.147 | 0.145 |
| loadgen | 0.014 | 0.014 | 0.014 | 0.015 | 0.014 |
| k3s | 0.091 | 0.112 | 0.096 | 0.116 | 0.114 |
| k8s-addons | 0.004 | 0.004 | 0.005 | 0.004 | 0.004 |
| os | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 |
| harness | 0.020 | 0.020 | 0.020 | 0.020 | 0.020 |
| node | 0.305 | 0.349 | 0.372 | 0.401 | 0.395 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 17.03 ± 0.22 | 3.2 ± 0.4 | - | 7.3 ± 0.5 | - | 11.8 ± 1.2 | - | 0.00 |
| Hubble | 16.96 ± 0.13 | 3.2 ± 0.4 | +0.8% [-9.1, +10.7] (n.s.) | 7.6 ± 0.5 | +4.3% [-0.7, +9.2] (n.s.) | 11.6 ± 0.7 | -0.9% [-8.8, +7.0] (n.s.) | 0.00 |
| Otterize | 17.06 ± 0.18 | 3.1 ± 0.3 | -2.5% [-8.2, +3.2] (n.s.) | 7.4 ± 0.5 | +1.8% [-5.3, +8.9] (n.s.) | 11.9 ± 0.7 | +1.7% [-6.5, +9.9] (n.s.) | 0.00 |
| IG trace_tcp | 17.06 ± 0.21 | 3.2 ± 0.4 | +0.8% [-9.1, +10.7] (n.s.) | 7.6 ± 0.5 | +4.5% [-2.2, +11.1] (n.s.) | 12.0 ± 0.7 | +2.6% [-5.7, +11.0] (n.s.) | 0.00 |
| IG snapshot_socket | 17.00 ± 0.17 | 3.2 ± 0.4 | +0.8% [-9.1, +10.7] (n.s.) | 7.6 ± 0.5 | +4.3% [-0.7, +9.2] (n.s.) | 11.7 ± 0.5 | -0.1% [-6.5, +6.3] (n.s.) | 0.00 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 0.2 | 0.22 | 0.02 | - | - | - | - | - |
| Hubble | 0.4 | 0.42 | 0.02 | +89 [+66, +111] | +5185 [+5032, +5339] | +5185 [+5031, +5338] | +16812 [+10392, +23232] | 61.0 (thesis 72.3) |
| Otterize | 1.5 | 1.44 | 0.05 | +52 [+43, +60] | +199 [+162, +235] | +198 [+162, +235] | +6175 [+1308, +11041] | - |
| IG trace_tcp | 0.2 | 0.22 | 0.03 | +61 [+38, +83] | +1192 [+987, +1397] | +1192 [+987, +1397] | +2976 [-3466, +9417] (n.s.) | 1.3 (thesis 3.8) |
| IG snapshot_socket | 0.3 | 0.22 | 0.03 | +51 [+36, +66] | +75 [+55, +95] | +75 [+55, +95] | +315 [-7503, +8133] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 45%. Lost events: 0 in the window, 66 over the whole run (fixed-count tests included). hubble_* series at the end: 455.

| Class | flows/s | share |
|---|---|---|
| app | 60.2 | 79% |
| probe | 1.8 | 2% |
| client_feedback | 2.7 | 3% |
| other | 11.7 | 15% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.069 [+0.068, +0.070] cores. Standing (window before the snapshot) minus baseline observer: +0.068 cores; one snapshot adds 0.34 ± 0.12 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.265 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.036 [+0.033, +0.039] | +0.041 | +0.053 [+0.044, +0.061] | +0.20% / +0.29% | +118 [+57, +179] | +0.20% |
| Otterize | +0.094 [+0.091, +0.098] | +0.095 | +0.105 [+0.089, +0.121] | +0.52% / +0.58% | +118 [+96, +141] | +0.20% |
| IG trace_tcp | +0.135 [+0.133, +0.137] | +0.135 | +0.183 [+0.170, +0.196] | +0.75% / +1.01% | +323 [+310, +336] | +0.55% |
| IG snapshot_socket | +0.135 [+0.133, +0.136] | +0.135 | +0.176 [+0.161, +0.190] | +0.75% / +0.98% | +312 [+227, +397] | +0.53% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 11 | baseline | 2 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 33.13 |
| 12 | baseline | 3 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 37.23 |
| 13 | baseline | 1 | 0.45% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 39.81 |
| 14 | baseline | 2 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 32.76 |
| 15 | baseline | 5 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 38.24 |
| 16 | baseline | 3 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 36.21 |
| 17 | baseline | 1 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 46.70 |
| 18 | baseline | 4 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 30.66 |
| 19 | baseline | 5 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 29.37 |
| 20 | baseline | 4 | 0.32% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 37.13 |
| 11 | Hubble | 1 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 46.97 |
| 12 | Hubble | 5 | 0.05% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 39.24 |
| 13 | Hubble | 2 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 46.58 |
| 14 | Hubble | 4 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 49.65 |
| 15 | Hubble | 3 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 52.74 |
| 16 | Hubble | 1 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 43.90 |
| 17 | Hubble | 3 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 47.07 |
| 18 | Hubble | 5 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 42.90 |
| 19 | Hubble | 4 | 0.02% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 48.59 |
| 20 | Hubble | 2 | 0.07% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 45.32 |
| 11 | Otterize | 3 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 44.84 |
| 12 | Otterize | 4 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 35.44 |
| 13 | Otterize | 4 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 47.41 |
| 14 | Otterize | 5 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 60.09 |
| 15 | Otterize | 1 | 0.04% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 42.18 |
| 16 | Otterize | 2 | 0.04% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 46.51 |
| 17 | Otterize | 5 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 40.80 |
| 18 | Otterize | 3 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 34.67 |
| 19 | Otterize | 2 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 34.96 |
| 20 | Otterize | 1 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 38.84 |
| 11 | IG trace_tcp | 5 | 0.07% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 37.23 |
| 12 | IG trace_tcp | 2 | 0.04% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 54.92 |
| 13 | IG trace_tcp | 5 | 0.08% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 35.56 |
| 14 | IG trace_tcp | 3 | 0.04% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 37.20 |
| 15 | IG trace_tcp | 2 | 0.07% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 41.07 |
| 16 | IG trace_tcp | 4 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 45.97 |
| 17 | IG trace_tcp | 4 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 34.83 |
| 18 | IG trace_tcp | 1 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 33.93 |
| 19 | IG trace_tcp | 1 | 0.02% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 47.87 |
| 20 | IG trace_tcp | 3 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 44.69 |
| 11 | IG snapshot_socket | 4 | 0.05% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 31.76 |
| 12 | IG snapshot_socket | 1 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 43.04 |
| 13 | IG snapshot_socket | 3 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 32.76 |
| 14 | IG snapshot_socket | 1 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 35.34 |
| 15 | IG snapshot_socket | 4 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 30.82 |
| 16 | IG snapshot_socket | 5 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 47.23 |
| 17 | IG snapshot_socket | 2 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 33.68 |
| 18 | IG snapshot_socket | 2 | 0.01% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 43.55 |
| 19 | IG snapshot_socket | 3 | 0.03% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 44.41 |
| 20 | IG snapshot_socket | 5 | 0.04% | 6ac2778394d679d21b07a3d7 | 13ebd51a,ac25ea1d,cc9347f0 | 37.04 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 11 | baseline | 15.38/15.63 | 15.88/15.87 | 15.17/14.65 | 14.51/14.18 | 1.00 |
| 11 | Hubble | 14.88/14.91 | 14.97/14.95 | 14.11/14.44 | 14.23/14.17 | 0.94 |
| 11 | Otterize | 15.95/14.91 | 15.59/14.83 | 14.99/13.99 | 15.41/13.72 | 0.96 |
| 11 | IG trace_tcp | 16.09/15.92 | 16.19/15.90 | 14.41/14.68 | 14.19/13.94 | 1.01 |
| 11 | IG snapshot_socket | 15.58/15.96 | 15.92/15.87 | 14.87/14.44 | 14.37/14.68 | 1.00 |
| 12 | baseline | 15.90/15.92 | 15.91/15.74 | 14.54/14.52 | 15.31/14.98 | 1.00 |
| 12 | Hubble | 15.68/15.42 | 15.83/15.38 | 15.02/14.68 | 15.05/14.13 | 0.98 |
| 12 | Otterize | 15.62/15.59 | 15.46/15.79 | 14.55/14.75 | 14.77/14.90 | 0.98 |
| 12 | IG trace_tcp | 15.57/16.15 | 16.00/15.90 | 15.89/14.83 | 15.52/14.92 | 1.00 |
| 12 | IG snapshot_socket | 16.67/15.30 | 16.31/14.93 | 14.46/13.85 | 15.56/13.91 | 0.98 |
| 13 | baseline | 16.03/15.88 | 15.74/15.68 | 15.20/14.93 | 14.83/14.88 | 0.99 |
| 13 | Hubble | 15.60/15.92 | 15.62/15.82 | 14.12/14.52 | 15.07/14.80 | 0.99 |
| 13 | Otterize | 16.23/16.14 | 16.09/16.07 | 15.43/15.30 | 14.47/15.44 | 1.01 |
| 13 | IG trace_tcp | 16.30/14.60 | 16.14/14.36 | 15.45/14.09 | 14.92/13.92 | 0.96 |
| 13 | IG snapshot_socket | 15.43/15.42 | 15.22/15.41 | 14.37/14.24 | 13.97/14.21 | 0.96 |
| 14 | baseline | 15.73/14.56 | 15.41/15.25 | 14.49/14.37 | 14.73/13.96 | 0.97 |
| 14 | Hubble | 16.51/15.99 | 16.13/15.82 | 14.67/14.74 | 14.66/14.17 | 1.01 |
| 14 | Otterize | 14.49/15.96 | 14.42/15.79 | 13.87/14.55 | 14.26/14.78 | 0.95 |
| 14 | IG trace_tcp | 15.86/16.13 | 16.28/16.28 | 14.71/15.01 | 14.62/14.45 | 1.03 |
| 14 | IG snapshot_socket | 15.99/15.92 | 15.95/15.62 | 14.30/13.10 | 14.80/13.54 | 0.99 |
| 15 | baseline | 15.85/16.05 | 16.04/16.23 | 14.98/14.74 | 14.45/15.71 | 1.02 |
| 15 | Hubble | 16.09/15.38 | 15.85/15.20 | 15.71/13.98 | 15.30/14.08 | 0.98 |
| 15 | Otterize | 15.71/14.32 | 15.74/14.56 | 14.94/14.40 | 14.50/13.67 | 0.95 |
| 15 | IG trace_tcp | 16.23/15.37 | 16.01/15.43 | 15.35/14.47 | 15.08/14.06 | 0.99 |
| 15 | IG snapshot_socket | 16.12/15.85 | 15.98/15.91 | 14.61/14.57 | 14.72/14.45 | 1.00 |
| 16 | baseline | 16.19/15.80 | 16.34/16.00 | 15.38/14.21 | 15.67/14.54 | 1.02 |
| 16 | Hubble | 15.87/16.29 | 15.77/16.05 | 15.06/15.03 | 14.40/14.59 | 1.00 |
| 16 | Otterize | 16.44/16.18 | 16.15/15.83 | 14.64/15.31 | 14.98/15.56 | 1.01 |
| 16 | IG trace_tcp | 16.16/16.16 | 16.23/16.07 | 15.33/15.31 | 15.17/14.67 | 1.02 |
| 16 | IG snapshot_socket | 16.22/16.28 | 16.14/16.14 | 15.34/15.36 | 15.40/15.50 | 1.02 |
| 17 | baseline | 16.30/16.35 | 16.13/16.16 | 14.11/15.58 | 15.24/15.75 | 1.02 |
| 17 | Hubble | 15.74/15.98 | 15.69/16.06 | 14.90/15.07 | 13.98/15.07 | 1.00 |
| 17 | Otterize | 15.71/11.45 | 15.67/11.18 | 14.70/9.76 | 14.62/9.54 | 0.84 |
| 17 | IG trace_tcp | 16.33/15.85 | 16.01/15.79 | 14.58/13.96 | 15.06/14.04 | 1.00 |
| 17 | IG snapshot_socket | 15.70/16.28 | 15.78/16.09 | 13.92/14.28 | 14.08/14.18 | 1.00 |
| 18 | baseline | 16.01/12.04 | 15.96/11.91 | 14.83/11.13 | 14.43/10.90 | 0.88 |
| 18 | Hubble | 16.32/14.30 | 16.01/14.09 | 14.23/12.24 | 15.40/13.07 | 0.95 |
| 18 | Otterize | 15.76/15.95 | 15.56/15.98 | 14.31/15.00 | 14.40/14.11 | 0.99 |
| 18 | IG trace_tcp | 16.65/16.36 | 16.26/16.20 | 15.43/14.70 | 14.77/14.78 | 1.02 |
| 18 | IG snapshot_socket | 16.41/15.92 | 16.17/15.79 | 14.98/15.22 | 14.93/15.15 | 1.01 |
| 19 | baseline | 16.21/15.89 | 16.07/15.70 | 15.26/15.18 | 14.60/14.68 | 1.00 |
| 19 | Hubble | 15.49/13.99 | 15.35/13.88 | 14.30/12.50 | 14.11/11.73 | 0.92 |
| 19 | Otterize | 15.23/16.28 | 15.09/16.27 | 13.58/15.28 | 13.88/15.45 | 0.99 |
| 19 | IG trace_tcp | 16.08/16.21 | 16.06/15.73 | 15.16/14.36 | 15.11/14.58 | 1.00 |
| 19 | IG snapshot_socket | 16.27/12.72 | 16.01/12.57 | 15.16/12.08 | 14.37/11.94 | 0.90 |
| 20 | baseline | 16.25/16.19 | 16.08/15.84 | 15.30/15.06 | 14.85/15.59 | 1.01 |
| 20 | Hubble | 13.88/16.00 | 13.44/15.95 | 12.60/15.08 | 12.13/15.00 | 0.93 |
| 20 | Otterize | 16.18/15.47 | 16.16/15.48 | 14.93/14.82 | 13.56/14.56 | 1.00 |
| 20 | IG trace_tcp | 15.56/16.31 | 15.36/16.08 | 14.69/14.36 | 14.70/14.73 | 0.99 |
| 20 | IG snapshot_socket | 16.30/14.76 | 16.16/14.63 | 15.21/13.64 | 15.09/13.38 | 0.97 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 28.61 ± 2.30 (n=10) | 32.08 ± 4.49 (n=10) | +12.50% [+1.09, +23.91] | 0.035 | 0.070 |
| keepalive | Otterize | 28.61 ± 2.30 (n=10) | 33.85 ± 3.79 (n=10) | +18.65% [+9.55, +27.74] | 0.001 | 0.005 |
| keepalive | IG trace_tcp | 28.61 ± 2.30 (n=10) | 33.88 ± 5.57 (n=10) | +18.74% [+4.87, +32.60] | 0.014 | 0.041 |
| keepalive | IG snapshot_socket | 28.61 ± 2.30 (n=10) | 28.82 ± 4.86 (n=10) | +1.48% [-12.40, +15.37] (n.s.) (< 15.4% at 95%) | 0.815 | 0.815 |
| newconn | Hubble | 33.57 ± 6.04 (n=10) | 41.56 ± 3.75 (n=10) | +26.91% [+11.12, +42.70] | 0.004 | 0.016 |
| newconn | Otterize | 33.57 ± 6.04 (n=10) | 38.48 ± 7.82 (n=10) | +18.04% [-4.55, +40.63] (n.s.) (< 40.6% at 95%) | 0.104 | 0.250 |
| newconn | IG trace_tcp | 33.57 ± 6.04 (n=10) | 38.25 ± 7.07 (n=10) | +17.02% [-2.75, +36.79] (n.s.) (< 36.8% at 95%) | 0.083 | 0.250 |
| newconn | IG snapshot_socket | 33.57 ± 6.04 (n=10) | 34.50 ± 6.15 (n=10) | +6.91% [-15.78, +29.59] (n.s.) (< 29.6% at 95%) | 0.508 | 0.508 |
