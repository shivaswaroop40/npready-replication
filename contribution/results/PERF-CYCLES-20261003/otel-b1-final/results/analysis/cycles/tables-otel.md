# otel

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.068 [+0.028, +0.108] | 0.004 | 0.004 | +0.076 [-0.011, +0.163] (n.s.) | 0.079 | 0.157 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.051 [+0.035, +0.067] | <0.001 | <0.001 | +0.061 [-0.039, +0.161] (n.s.) | 0.200 | 0.200 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.085 [+0.055, +0.116] | <0.001 | <0.001 | +0.101 [+0.032, +0.170] | 0.009 | 0.037 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.075 [+0.041, +0.110] | <0.001 | 0.002 | +0.102 [+0.005, +0.198] | 0.041 | 0.124 | 10 |
| Δ observer CPU (cores) | Hubble | +0.075 [+0.064, +0.086] | <0.001 | <0.001 | +0.081 [+0.066, +0.096] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.061 [+0.055, +0.066] | <0.001 | <0.001 | +0.065 [+0.044, +0.086] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.070 [+0.064, +0.076] | <0.001 | <0.001 | +0.077 [+0.061, +0.093] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.066 [+0.061, +0.070] | <0.001 | <0.001 | +0.074 [+0.056, +0.092] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | -0.015 [-0.030, -0.001] | 0.040 | 0.160 | -0.024 [-0.080, +0.033] (n.s.) | 0.365 | 1.000 | 10 |
| Δ app CPU (cores) | Otterize | -0.004 [-0.013, +0.005] (n.s.) | 0.317 | 0.348 | +0.003 [-0.051, +0.057] (n.s.) | 0.905 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | -0.009 [-0.018, +0.001] (n.s.) | 0.073 | 0.220 | -0.018 [-0.069, +0.033] (n.s.) | 0.454 | 1.000 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | -0.008 [-0.021, +0.004] (n.s.) | 0.174 | 0.348 | -0.001 [-0.056, +0.053] (n.s.) | 0.952 | 1.000 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.030 [+0.014, +0.046] | 0.002 | 0.007 | +0.038 [+0.011, +0.065] | 0.011 | 0.034 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.001 [-0.007, +0.009] (n.s.) | 0.883 | 0.883 | +0.001 [-0.029, +0.030] (n.s.) | 0.969 | 0.969 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.030 [+0.019, +0.040] | <0.001 | <0.001 | +0.042 [+0.016, +0.068] | 0.005 | 0.021 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.023 [+0.007, +0.038] | 0.008 | 0.017 | +0.030 [+0.001, +0.060] | 0.045 | 0.091 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +111 [+108, +115] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +82 [+79, +85] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +134 [+130, +137] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +115 [+110, +119] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +128 [+110, +146] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +92 [+73, +110] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +157 [+141, +173] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +170 [+116, +225] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | +3.1% [-21.9, +28.1] (n.s.) | 0.783 | 1.000 | +4.6% [-25.2, +34.4] (n.s.) | 0.735 | 1.000 | 10 |
| fixed-count time, keep-alive | Otterize | +6.2% [-20.0, +32.5] (n.s.) | 0.605 | 1.000 | +2.8% [-20.3, +26.0] (n.s.) | 0.787 | 1.000 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | -17.0% [-30.0, -4.0] | 0.016 | 0.064 | -15.1% [-30.2, -0.1] | 0.049 | 0.197 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | -12.4% [-27.9, +3.0] (n.s.) | 0.102 | 0.307 | -13.5% [-29.0, +2.1] (n.s.) | 0.081 | 0.244 | 10 |
| fixed-count time, new conn | Hubble | +15.4% [-7.6, +38.4] (n.s.) | 0.164 | 0.493 | +13.9% [-9.4, +37.1] (n.s.) | 0.210 | 0.629 | 10 |
| fixed-count time, new conn | Otterize | +6.0% [-18.7, +30.7] (n.s.) | 0.595 | 1.000 | +6.5% [-14.2, +27.2] (n.s.) | 0.498 | 0.853 | 10 |
| fixed-count time, new conn | IG trace_tcp | -3.2% [-14.7, +8.3] (n.s.) | 0.546 | 1.000 | -4.3% [-16.0, +7.4] (n.s.) | 0.427 | 0.853 | 10 |
| fixed-count time, new conn | IG snapshot_socket | -11.3% [-23.8, +1.2] (n.s.) | 0.072 | 0.288 | -9.5% [-22.1, +3.2] (n.s.) | 0.125 | 0.499 | 10 |
| canary speed, workers, steady window (check) | Hubble | +0.84% [-14.04, +15.72] (n.s.) | 0.901 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | +3.69% [-14.94, +22.33] (n.s.) | 0.664 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | -0.15% [-15.22, +14.93] (n.s.) | 0.983 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | +3.79% [-12.06, +19.64] (n.s.) | 0.602 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 19.7% raw, 21.3% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.10; new conn: CV of the baseline time across cycles 17.3% raw, 15.5% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.55.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-03 06:30 | baseline hubble ig_snap otterize ig_tcp | 50.2 | 80.3 | 56.6 | 82.5 | 0.277 | 0.349 | 9.51 | 1.22 | 8.95 |
| 2 | 10-03 07:30 | otterize hubble ig_tcp baseline ig_snap | 42.0 | 74.6 | 47.8 | 74.8 | 0.279 | 0.285 | 8.64 | 1.11 | 7.72 |
| 3 | 10-03 08:29 | baseline ig_snap hubble ig_tcp otterize | 40.3 | 66.0 | 46.8 | 72.9 | 0.291 | 0.297 | 8.24 | 1.06 | 8.07 |
| 4 | 10-03 09:39 | hubble otterize baseline ig_tcp ig_snap | 54.2 | 94.2 | 58.7 | 90.6 | 0.285 | 0.243 | 6.85 | 0.88 | 8.45 |
| 5 | 10-03 10:39 | ig_snap baseline ig_tcp hubble otterize | 35.7 | 59.2 | 42.0 | 67.4 | 0.294 | 0.243 | 6.50 | 0.84 | 7.54 |
| 6 | 10-03 12:01 | otterize ig_tcp hubble ig_snap baseline | 47.2 | 70.7 | 48.1 | 79.4 | 0.291 | 0.335 | 8.42 | 1.08 | 8.47 |
| 7 | 10-03 13:12 | ig_tcp ig_snap otterize baseline hubble | 28.6 | 43.6 | 34.7 | 55.6 | 0.263 | 0.260 | 7.53 | 0.97 | 8.32 |
| 8 | 10-03 14:36 | ig_snap ig_tcp baseline otterize hubble | 38.2 | 60.3 | 43.6 | 66.0 | 0.272 | 0.388 | 11.23 | 1.45 | 9.17 |
| 9 | 10-03 15:58 | hubble baseline otterize ig_snap ig_tcp | 31.4 | 53.5 | 35.7 | 57.8 | 0.285 | 0.259 | 6.92 | 0.89 | 7.95 |
| 10 | 10-03 17:10 | ig_tcp otterize ig_snap hubble baseline | 43.4 | 66.2 | 41.2 | 64.2 | 0.262 | 0.374 | 10.07 | 1.30 | 8.84 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 baseline; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.075 [+0.064, +0.086] | <0.001 | +0.080 | 0.002 | +0.076 [+0.063, +0.089] | 9 | robust |
| Δ observer CPU | Otterize | +0.061 [+0.055, +0.066] | <0.001 | +0.062 | 0.002 | +0.063 [+0.059, +0.066] | 9 | robust |
| Δ observer CPU | IG trace_tcp | +0.070 [+0.064, +0.076] | <0.001 | +0.069 | 0.002 | +0.072 [+0.066, +0.077] | 9 | robust |
| Δ observer CPU | IG snapshot_socket | +0.066 [+0.061, +0.070] | <0.001 | +0.065 | 0.002 | +0.066 [+0.061, +0.071] | 9 | robust |
| Δ observer anon memory | Hubble | +111 [+108, +115] | <0.001 | +112 | 0.002 | +111 [+107, +115] | 9 | robust |
| Δ observer anon memory | Otterize | +82 [+79, +85] | <0.001 | +82 | 0.002 | +82 [+78, +85] | 9 | robust |
| Δ observer anon memory | IG trace_tcp | +134 [+130, +137] | <0.001 | +134 | 0.002 | +133 [+129, +137] | 9 | robust |
| Δ observer anon memory | IG snapshot_socket | +115 [+110, +119] | <0.001 | +115 | 0.002 | +113 [+110, +116] | 9 | robust |
| fixed-count time, keep-alive | Hubble | +3.1% [-21.9, +28.1] (n.s.) | 1.000 | +2.1% | 1.000 | +6.6% [-20.5, +33.7] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | Otterize | +6.2% [-20.0, +32.5] (n.s.) | 1.000 | -0.1% | 1.000 | +8.8% [-20.3, +38.0] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | IG trace_tcp | -17.0% [-30.0, -4.0] | 0.127 | -22.9% | 0.064 | -15.1% [-29.1, -1.1] | 9 | n.s. (primary) |
| fixed-count time, keep-alive | IG snapshot_socket | -12.4% [-27.9, +3.0] (n.s.) | 0.615 | -14.9% | 0.131 | -10.8% [-27.9, +6.3] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +15.4% [-7.6, +38.4] (n.s.) | 0.822 | +19.0% | 0.232 | +19.3% [-4.9, +43.5] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | Otterize | +6.0% [-18.7, +30.7] (n.s.) | 1.000 | +0.5% | 0.922 | +10.6% [-14.9, +36.2] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | -3.2% [-14.7, +8.3] (n.s.) | 1.000 | -5.4% | 0.557 | -2.6% [-15.7, +10.4] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG snapshot_socket | -11.3% [-23.8, +1.2] (n.s.) | 0.504 | -3.9% | 0.131 | -9.9% [-23.8, +3.9] (n.s.) | 9 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 7040 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **node-bound** (baseline newconn bottleneck throttled 0.00 s/s), so node CPU limits the test. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 41.11 ± 8.08 (n=10) | 40.37 ± 8.58 (n=10) | +3.14% [-21.86, +28.14] (n.s.) (< 28.1% at 95%) | 0.783 | 1.000 | opentelemetry-demo-productcatalogservice 0.00 | 0.00 |
| keepalive | Otterize | 41.11 ± 8.08 (n=10) | 41.45 ± 7.40 (n=10) | +6.23% [-20.05, +32.52] (n.s.) (< 32.5% at 95%) | 0.605 | 1.000 | opentelemetry-demo-otelcol 0.00 | 0.00 |
| keepalive | IG trace_tcp | 41.11 ± 8.08 (n=10) | 33.11 ± 3.76 (n=10) | -17.02% [-30.02, -4.03] | 0.016 | 0.127 | opentelemetry-demo-quoteservice 0.00 | 0.00 |
| keepalive | IG snapshot_socket | 41.11 ± 8.08 (n=10) | 34.74 ± 5.40 (n=10) | -12.41% [-27.85, +3.03] (n.s.) (< 3.0% at 95%) | 0.102 | 0.615 | opentelemetry-demo-productcatalogservice 0.00 | 0.00 |
| newconn | Hubble | 45.52 ± 7.87 (n=10) | 50.65 ± 9.13 (n=10) | +15.39% [-7.61, +38.39] (n.s.) (< 38.4% at 95%) | 0.164 | 0.822 | opentelemetry-demo-productcatalogservice 0.00 | 1.00 |
| newconn | Otterize | 45.52 ± 7.87 (n=10) | 46.27 ± 8.69 (n=10) | +6.02% [-18.69, +30.74] (n.s.) (< 30.7% at 95%) | 0.595 | 1.000 | opentelemetry-demo-otelcol 0.00 | 1.00 |
| newconn | IG trace_tcp | 45.52 ± 7.87 (n=10) | 43.20 ± 4.90 (n=10) | -3.19% [-14.70, +8.32] (n.s.) (< 8.3% at 95%) | 0.546 | 1.000 | opentelemetry-demo-quoteservice 0.00 | 1.00 |
| newconn | IG snapshot_socket | 45.52 ± 7.87 (n=10) | 39.41 ± 5.52 (n=10) | -11.30% [-23.83, +1.24] (n.s.) (< 1.2% at 95%) | 0.072 | 0.504 | opentelemetry-demo-productcatalogservice 0.00 | 1.00 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 41.11 ± 8.08 | 19.65% | 19.65% | 10 |
| newconn | 45.52 ± 7.87 | 17.30% | 17.30% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.093 ± 0.006 | 0.009 | - | 0.643 ± 0.034 | 0.058 | - | - | - | - |
| Hubble | 0.168 ± 0.019 | 0.020 | +0.075 [+0.064, +0.086] | 0.711 ± 0.069 | 0.082 | +0.068 [+0.028, +0.108] | +0.68% | +0.030 | <0.001 / <0.001 |
| Otterize | 0.153 ± 0.007 | 0.015 | +0.061 [+0.055, +0.066] | 0.693 ± 0.024 | 0.072 | +0.051 [+0.035, +0.067] | +0.51% | +0.001 | <0.001 / <0.001 |
| IG trace_tcp | 0.163 ± 0.006 | 0.012 | +0.070 [+0.064, +0.076] | 0.728 ± 0.039 | 0.072 | +0.085 [+0.055, +0.116] | +0.85% | +0.030 | <0.001 / <0.001 |
| IG snapshot_socket | 0.158 ± 0.007 | 0.011 | +0.066 [+0.061, +0.070] | 0.718 ± 0.049 | 0.059 | +0.075 [+0.041, +0.110] | +0.75% | +0.023 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.060 [+0.044, +0.075] | +0.029 [+0.007, +0.051] | +0.076 [+0.032, +0.120] | 79% |
| Otterize | +0.071 [+0.059, +0.083] | +0.023 [+0.002, +0.044] | +0.088 [+0.047, +0.129] | 117% |
| IG trace_tcp | +0.075 [+0.058, +0.091] | +0.044 [+0.013, +0.074] | +0.120 [+0.057, +0.182] | 107% |
| IG snapshot_socket | +0.070 [+0.062, +0.078] | +0.039 [+0.021, +0.057] | +0.116 [+0.080, +0.152] | 107% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.040 [+0.037, +0.043] | -0.750 [-1.294, -0.206] | +0.021 [-0.003, +0.045] (n.s.) | 0.00 → 0.00 | 11% |
| keepalive | Otterize | +0.048 [+0.041, +0.054] | -0.211 [-0.912, +0.490] (n.s.) | +0.013 [-0.012, +0.038] (n.s.) | 0.00 → 0.00 | 10% |
| keepalive | IG trace_tcp | +0.084 [+0.078, +0.089] | -0.660 [-1.431, +0.111] (n.s.) | +0.043 [+0.023, +0.063] | 0.00 → 0.00 | 12% |
| keepalive | IG snapshot_socket | +0.083 [+0.073, +0.092] | -0.576 [-1.075, -0.077] | +0.037 [+0.013, +0.061] | 0.00 → 0.00 | 12% |
| newconn | Hubble | +0.766 [+0.701, +0.831] | +0.104 [-0.507, +0.715] (n.s.) | +0.342 [+0.296, +0.389] | 0.00 → 0.00 | 42% |
| newconn | Otterize | +0.062 [+0.054, +0.069] | -0.097 [-1.036, +0.842] (n.s.) | +0.004 [-0.018, +0.025] (n.s.) | 0.00 → 0.00 | 15% |
| newconn | IG trace_tcp | +0.295 [+0.279, +0.311] | +0.003 [-1.136, +1.141] (n.s.) | +0.314 [+0.283, +0.345] | 0.00 → 0.00 | 32% |
| newconn | IG snapshot_socket | +0.082 [+0.077, +0.087] | -0.432 [-1.036, +0.171] (n.s.) | +0.027 [+0.007, +0.048] | 0.00 → 0.00 | 17% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 665 ± 15 | 2.9 | 1.25 | 374 | - | - | 4899 ± 86 | - | - |
| Hubble | 793 ± 30 (peak 804) | 6.4 | 4.63 | 485 | +111 [+108, +115] | +128 [+110, +146] | 5014 ± 80 | +0.70% | <0.001 / <0.001 |
| Otterize | 757 ± 32 (peak 761) | 2.8 | 0.93 | 456 | +82 [+79, +85] | +92 [+73, +110] | 5003 ± 85 | +0.51% | <0.001 / <0.001 |
| IG trace_tcp | 822 ± 20 (peak 841) | 10.7 | -6.64 | 508 | +134 [+130, +137] | +157 [+141, +173] | 5121 ± 88 | +0.84% | <0.001 / <0.001 |
| IG snapshot_socket | 836 ± 85 (peak 882) | 15.0 | 5.04 | 489 | +115 [+110, +119] | +170 [+116, +225] | 5088 ± 80 | +0.72% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.080 | 0.111 | 0.079 | 0.078 | 0.078 |
| cilium-envoy | 0.009 | 0.009 | 0.009 | 0.009 | 0.008 |
| cilium-operator | 0.004 | 0.004 | 0.004 | 0.004 | 0.004 |
| hubble-relay | 0.000 | 0.020 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.006 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.055 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.071 | 0.068 |
| client-hubble | 0.000 | 0.024 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 |
| app | 0.280 | 0.265 | 0.276 | 0.271 | 0.271 |
| loadgen | 0.031 | 0.029 | 0.030 | 0.030 | 0.030 |
| k3s | 0.204 | 0.234 | 0.204 | 0.234 | 0.227 |
| k8s-addons | 0.011 | 0.010 | 0.011 | 0.010 | 0.010 |
| os | 0.002 | 0.002 | 0.002 | 0.001 | 0.002 |
| harness | 0.036 | 0.035 | 0.036 | 0.035 | 0.035 |
| node | 0.643 | 0.711 | 0.693 | 0.728 | 0.718 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 16.98 ± 0.21 | 6.7 ± 0.5 | - | 22.3 ± 0.7 | - | 29.5 ± 1.1 | - | 0.00 |
| Hubble | 16.93 ± 0.19 | 6.0 ± 0.5 | -10.2% [-15.3, -5.2] | 22.0 ± 1.2 | -1.3% [-5.1, +2.4] (n.s.) | 30.0 ± 1.9 | +1.7% [-1.7, +5.0] (n.s.) | 0.00 |
| Otterize | 16.82 ± 0.17 | 6.5 ± 0.7 | -2.4% [-12.7, +7.9] (n.s.) | 22.8 ± 1.2 | +2.3% [-2.3, +7.0] (n.s.) | 31.0 ± 4.8 | +5.2% [-7.0, +17.5] (n.s.) | 0.00 |
| IG trace_tcp | 16.91 ± 0.20 | 6.2 ± 0.4 | -7.1% [-12.5, -1.8] | 22.3 ± 0.8 | +0.1% [-3.6, +3.9] (n.s.) | 29.0 ± 0.8 | -1.5% [-5.6, +2.6] (n.s.) | 0.00 |
| IG snapshot_socket | 16.94 ± 0.11 | 6.3 ± 0.5 | -5.2% [-14.5, +4.0] (n.s.) | 21.7 ± 1.3 | -2.6% [-7.0, +1.8] (n.s.) | 28.6 ± 0.8 | -2.9% [-6.5, +0.7] (n.s.) | 0.00 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 0.2 | 0.22 | 0.02 | - | - | - | - | - |
| Hubble | 0.4 | 0.42 | 0.02 | -126 [-267, +15] (n.s.) | +5225 [+4874, +5576] | +5224 [+4873, +5575] | +3875 [-3334, +11084] (n.s.) | 61.8 (thesis 72.3) |
| Otterize | 1.5 | 1.44 | 0.02 | -144 [-235, -54] | -62 [-153, +29] (n.s.) | -62 [-153, +29] (n.s.) | -1189 [-10526, +8148] (n.s.) | - |
| IG trace_tcp | 0.2 | 0.22 | 0.03 | +94 [-15, +204] (n.s.) | +1447 [+1302, +1593] | +1447 [+1301, +1593] | -2006 [-11272, +7260] (n.s.) | 1.3 (thesis 3.8) |
| IG snapshot_socket | 0.3 | 0.22 | 0.04 | +110 [+31, +188] | +111 [+29, +192] | +111 [+29, +192] | -7072 [-12446, -1697] | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 45%. Lost events: 0 in the window, 68 over the whole run (fixed-count tests included). hubble_* series at the end: 457.

| Class | flows/s | share |
|---|---|---|
| app | 60.9 | 79% |
| probe | 1.8 | 2% |
| client_feedback | 2.7 | 3% |
| other | 11.7 | 15% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.066 [+0.061, +0.070] cores. Standing (window before the snapshot) minus baseline observer: +0.065 cores; one snapshot adds 0.06 ± 0.37 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.309 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.075 [+0.058, +0.092] | +0.080 | +0.093 [+0.027, +0.159] | +0.42% / +0.52% | +110 [+65, +156] | +0.19% |
| Otterize | +0.096 [+0.082, +0.109] | +0.089 | +0.106 [+0.059, +0.152] | +0.53% / +0.59% | +120 [+80, +160] | +0.21% |
| IG trace_tcp | +0.138 [+0.115, +0.160] | +0.133 | +0.198 [+0.115, +0.282] | +0.76% / +1.10% | +330 [+283, +377] | +0.56% |
| IG snapshot_socket | +0.131 [+0.121, +0.141] | +0.127 | +0.190 [+0.141, +0.239] | +0.73% / +1.05% | +390 [+253, +527] | +0.67% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 1 | 0.15% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 56.59 |
| 2 | baseline | 4 | 0.06% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 47.76 |
| 3 | baseline | 1 | 0.07% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 46.82 |
| 4 | baseline | 3 | 0.04% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 58.68 |
| 5 | baseline | 2 | 0.09% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 42.05 |
| 6 | baseline | 5 | 0.05% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 48.12 |
| 7 | baseline | 4 | 0.17% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 34.68 |
| 8 | baseline | 3 | 0.38% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 43.63 |
| 9 | baseline | 2 | 0.06% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 35.67 |
| 10 | baseline | 5 | 0.15% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 41.20 |
| 1 | Hubble | 2 | 0.27% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 45.28 |
| 2 | Hubble | 2 | 0.04% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 48.09 |
| 3 | Hubble | 3 | 0.35% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 41.58 |
| 4 | Hubble | 1 | 0.04% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 39.05 |
| 5 | Hubble | 4 | 0.04% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 54.18 |
| 6 | Hubble | 3 | 0.06% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 62.67 |
| 7 | Hubble | 5 | 0.16% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 58.42 |
| 8 | Hubble | 5 | 0.18% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 65.84 |
| 9 | Hubble | 1 | 0.13% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 46.46 |
| 10 | Hubble | 4 | 0.17% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 44.95 |
| 1 | Otterize | 4 | 0.19% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 36.47 |
| 2 | Otterize | 1 | 0.16% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 43.26 |
| 3 | Otterize | 5 | 0.05% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 50.17 |
| 4 | Otterize | 2 | 0.05% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 49.34 |
| 5 | Otterize | 5 | 0.12% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 54.29 |
| 6 | Otterize | 1 | 0.11% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 33.43 |
| 7 | Otterize | 3 | 2.42% (high) | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 62.45 |
| 8 | Otterize | 4 | 0.13% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 46.60 |
| 9 | Otterize | 3 | 0.09% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 47.88 |
| 10 | Otterize | 2 | 0.21% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 38.83 |
| 1 | IG trace_tcp | 5 | 0.39% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 52.00 |
| 2 | IG trace_tcp | 3 | 0.03% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 41.52 |
| 3 | IG trace_tcp | 4 | 0.08% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 34.86 |
| 4 | IG trace_tcp | 4 | 0.05% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 49.87 |
| 5 | IG trace_tcp | 3 | 0.05% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 44.68 |
| 6 | IG trace_tcp | 2 | 0.08% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 39.21 |
| 7 | IG trace_tcp | 1 | 0.12% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 42.05 |
| 8 | IG trace_tcp | 2 | 0.07% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 42.42 |
| 9 | IG trace_tcp | 5 | 0.12% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 43.42 |
| 10 | IG trace_tcp | 1 | 0.04% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 41.98 |
| 1 | IG snapshot_socket | 3 | 0.04% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 43.32 |
| 2 | IG snapshot_socket | 5 | 0.16% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 45.44 |
| 3 | IG snapshot_socket | 2 | 0.03% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 34.01 |
| 4 | IG snapshot_socket | 5 | 0.04% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 33.32 |
| 5 | IG snapshot_socket | 1 | 0.05% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 44.57 |
| 6 | IG snapshot_socket | 4 | 0.05% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 35.39 |
| 7 | IG snapshot_socket | 2 | 0.05% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 34.95 |
| 8 | IG snapshot_socket | 1 | 0.34% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 48.04 |
| 9 | IG snapshot_socket | 4 | 0.09% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 35.07 |
| 10 | IG snapshot_socket | 3 | 0.23% | 6ac09d76a347f7b916cfbcb0 | 8cf687b9,5c8aaa38,058fb69b | 40.02 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 13.25/7.99 | 11.00/8.03 | 11.30/13.49 | 10.61/11.99 | 1.22 |
| 1 | Hubble | 10.41/10.05 | 8.16/9.32 | 11.75/13.62 | 11.03/12.89 | 1.13 |
| 1 | Otterize | 8.22/6.45 | 8.29/7.99 | 12.11/11.15 | 11.59/13.27 | 1.05 |
| 1 | IG trace_tcp | 8.96/9.76 | 7.99/8.88 | 14.34/12.49 | 12.30/11.46 | 1.09 |
| 1 | IG snapshot_socket | 6.68/13.04 | 6.64/13.16 | 12.53/12.91 | 12.64/11.95 | 1.29 |
| 2 | baseline | 11.38/5.89 | 10.27/7.01 | 13.29/14.27 | 12.56/11.78 | 1.11 |
| 2 | Hubble | 6.27/6.27 | 7.37/6.83 | 12.86/13.43 | 12.19/10.94 | 0.91 |
| 2 | Otterize | 7.05/6.63 | 8.49/7.13 | 12.62/11.51 | 12.15/12.20 | 1.00 |
| 2 | IG trace_tcp | 6.84/6.60 | 7.23/6.61 | 11.54/11.31 | 10.97/11.09 | 0.89 |
| 2 | IG snapshot_socket | 7.60/8.02 | 8.00/8.28 | 10.80/13.12 | 11.08/13.45 | 1.05 |
| 3 | baseline | 9.54/6.50 | 9.21/7.26 | 13.94/11.58 | 12.92/11.30 | 1.06 |
| 3 | Hubble | 6.83/11.41 | 7.84/12.08 | 12.15/12.57 | 12.44/11.18 | 1.29 |
| 3 | Otterize | 7.04/6.69 | 7.07/6.40 | 14.02/12.68 | 14.16/11.17 | 0.87 |
| 3 | IG trace_tcp | 7.42/6.66 | 7.93/7.71 | 13.07/13.56 | 13.42/12.32 | 1.01 |
| 3 | IG snapshot_socket | 7.76/7.26 | 7.64/7.55 | 12.55/13.35 | 13.21/11.17 | 0.98 |
| 4 | baseline | 7.18/6.49 | 6.45/7.25 | 15.00/12.07 | 12.56/11.46 | 0.88 |
| 4 | Hubble | 6.35/6.18 | 7.04/6.97 | 11.93/12.82 | 11.69/11.61 | 0.90 |
| 4 | Otterize | 7.37/6.67 | 8.51/6.86 | 11.24/12.86 | 11.77/12.89 | 0.99 |
| 4 | IG trace_tcp | 11.88/7.66 | 11.51/7.61 | 12.12/13.56 | 11.97/13.08 | 1.22 |
| 4 | IG snapshot_socket | 10.36/11.05 | 10.97/11.36 | 13.33/11.62 | 12.62/11.96 | 1.44 |
| 5 | baseline | 6.39/6.10 | 6.90/6.10 | 13.38/12.46 | 13.08/11.86 | 0.84 |
| 5 | Hubble | 6.41/7.63 | 7.18/7.72 | 11.31/14.15 | 10.74/13.02 | 0.96 |
| 5 | Otterize | 12.84/7.04 | 11.10/7.04 | 12.18/14.15 | 11.52/13.66 | 1.16 |
| 5 | IG trace_tcp | 6.95/6.59 | 8.14/6.99 | 13.53/13.98 | 13.58/12.63 | 0.97 |
| 5 | IG snapshot_socket | 6.84/6.85 | 6.94/7.32 | 11.79/14.55 | 11.93/13.55 | 0.92 |
| 6 | baseline | 9.85/7.76 | 10.24/6.59 | 10.70/12.48 | 12.27/13.32 | 1.08 |
| 6 | Hubble | 7.07/6.06 | 7.97/6.70 | 12.23/14.32 | 11.62/13.45 | 0.94 |
| 6 | Otterize | 10.85/6.32 | 11.12/7.28 | 13.02/11.29 | 12.01/11.96 | 1.18 |
| 6 | IG trace_tcp | 10.34/8.31 | 10.59/9.13 | 11.21/10.96 | 11.36/11.94 | 1.27 |
| 6 | IG snapshot_socket | 6.93/6.49 | 8.06/7.06 | 11.73/11.29 | 12.79/12.89 | 0.97 |
| 7 | baseline | 8.86/8.41 | 7.45/7.60 | 11.94/11.73 | 12.49/12.40 | 0.97 |
| 7 | Hubble | 7.11/12.13 | 7.62/12.68 | 12.11/14.30 | 10.98/13.16 | 1.32 |
| 7 | Otterize | 6.07/7.39 | 8.05/9.18 | 9.88/10.13 | 10.26/11.25 | 1.11 |
| 7 | IG trace_tcp | 7.24/6.23 | 8.36/7.47 | 12.41/12.06 | 12.55/10.47 | 1.02 |
| 7 | IG snapshot_socket | 7.41/7.59 | 7.26/7.49 | 13.12/13.95 | 10.89/12.73 | 0.95 |
| 8 | baseline | 10.67/11.45 | 11.11/11.34 | 11.47/13.02 | 10.81/12.64 | 1.45 |
| 8 | Hubble | 6.75/6.83 | 6.89/7.41 | 13.14/11.13 | 12.94/12.18 | 0.92 |
| 8 | Otterize | 11.07/6.58 | 11.17/7.39 | 10.92/12.97 | 12.34/12.58 | 1.19 |
| 8 | IG trace_tcp | 6.81/8.05 | 8.45/8.81 | 12.41/12.41 | 10.28/10.63 | 1.11 |
| 8 | IG snapshot_socket | 6.45/6.22 | 9.49/9.59 | 10.59/9.87 | 10.79/12.84 | 1.23 |
| 9 | baseline | 6.55/7.04 | 6.85/6.98 | 13.42/13.10 | 11.43/13.68 | 0.89 |
| 9 | Hubble | 7.35/6.44 | 7.96/7.64 | 10.78/14.29 | 10.88/13.01 | 1.00 |
| 9 | Otterize | 10.62/9.08 | 10.79/9.94 | 13.92/13.56 | 13.56/11.80 | 1.33 |
| 9 | IG trace_tcp | 6.90/6.92 | 7.73/6.96 | 12.74/14.21 | 12.40/11.74 | 0.94 |
| 9 | IG snapshot_socket | 6.91/6.20 | 7.58/7.04 | 12.54/13.16 | 11.99/13.83 | 0.94 |
| 10 | baseline | 10.38/14.40 | 8.19/11.95 | 11.03/12.63 | 11.23/12.92 | 1.30 |
| 10 | Hubble | 10.81/14.40 | 9.11/10.63 | 11.08/11.18 | 12.05/11.74 | 1.27 |
| 10 | Otterize | 7.28/6.54 | 7.52/6.84 | 13.35/12.52 | 12.86/14.04 | 0.92 |
| 10 | IG trace_tcp | 6.77/6.82 | 7.06/7.72 | 14.34/14.35 | 12.60/14.20 | 0.95 |
| 10 | IG snapshot_socket | 11.33/7.22 | 11.40/7.96 | 14.79/11.83 | 13.52/12.56 | 1.24 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 66.89 ± 14.24 (n=10) | 65.69 ± 15.96 (n=10) | +4.60% [-25.25, +34.44] (n.s.) (< 34.4% at 95%) | 0.735 | 1.000 |
| keepalive | Otterize | 66.89 ± 14.24 (n=10) | 65.36 ± 11.15 (n=10) | +2.85% [-20.30, +26.00] (n.s.) (< 26.0% at 95%) | 0.787 | 1.000 |
| keepalive | IG trace_tcp | 66.89 ± 14.24 (n=10) | 54.60 ± 6.65 (n=10) | -15.14% [-30.23, -0.06] | 0.049 | 0.197 |
| keepalive | IG snapshot_socket | 66.89 ± 14.24 (n=10) | 55.41 ± 6.45 (n=10) | -13.47% [-29.00, +2.06] (n.s.) (< 2.1% at 95%) | 0.081 | 0.244 |
| newconn | Hubble | 71.13 ± 11.05 (n=10) | 78.58 ± 16.26 (n=10) | +13.88% [-9.37, +37.13] (n.s.) (< 37.1% at 95%) | 0.210 | 0.629 |
| newconn | Otterize | 71.13 ± 11.05 (n=10) | 73.30 ± 11.91 (n=10) | +6.47% [-14.25, +27.19] (n.s.) (< 27.2% at 95%) | 0.498 | 0.853 |
| newconn | IG trace_tcp | 71.13 ± 11.05 (n=10) | 67.02 ± 9.30 (n=10) | -4.30% [-15.99, +7.38] (n.s.) (< 7.4% at 95%) | 0.427 | 0.853 |
| newconn | IG snapshot_socket | 71.13 ± 11.05 (n=10) | 63.05 ± 8.67 (n=10) | -9.46% [-22.10, +3.18] (n.s.) (< 3.2% at 95%) | 0.125 | 0.499 |
