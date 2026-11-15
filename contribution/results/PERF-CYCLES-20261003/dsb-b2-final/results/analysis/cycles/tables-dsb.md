# dsb

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.144 [+0.115, +0.174] | <0.001 | <0.001 | +0.143 [+0.117, +0.169] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.085 [+0.063, +0.108] | <0.001 | <0.001 | +0.082 [+0.063, +0.101] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.145 [+0.128, +0.161] | <0.001 | <0.001 | +0.147 [+0.134, +0.160] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.089 [+0.071, +0.106] | <0.001 | <0.001 | +0.087 [+0.076, +0.099] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Hubble | +0.106 [+0.085, +0.128] | <0.001 | <0.001 | +0.105 [+0.085, +0.124] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.090 [+0.081, +0.099] | <0.001 | <0.001 | +0.087 [+0.079, +0.096] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.096 [+0.089, +0.103] | <0.001 | <0.001 | +0.096 [+0.091, +0.101] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.071 [+0.064, +0.078] | <0.001 | <0.001 | +0.070 [+0.065, +0.075] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | +0.005 [+0.003, +0.007] | <0.001 | <0.001 | +0.006 [+0.004, +0.007] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Otterize | +0.001 [-0.004, +0.006] (n.s.) | 0.634 | 1.000 | +0.001 [-0.003, +0.005] (n.s.) | 0.611 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | +0.003 [-0.001, +0.007] (n.s.) | 0.178 | 0.533 | +0.004 [+0.001, +0.006] | 0.006 | 0.018 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | -0.000 [-0.005, +0.004] (n.s.) | 0.853 | 1.000 | -0.001 [-0.004, +0.002] (n.s.) | 0.656 | 1.000 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.051 [+0.044, +0.057] | <0.001 | <0.001 | +0.050 [+0.045, +0.055] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.004 [-0.003, +0.011] (n.s.) | 0.219 | 0.219 | +0.003 [-0.003, +0.009] (n.s.) | 0.268 | 0.268 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.062 [+0.053, +0.071] | <0.001 | <0.001 | +0.062 [+0.054, +0.071] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.023 [+0.016, +0.030] | <0.001 | <0.001 | +0.023 [+0.019, +0.027] | <0.001 | <0.001 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +110 [+106, +114] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +80 [+78, +83] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +150 [+145, +155] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +116 [+113, +118] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +126 [+109, +142] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +96 [+70, +122] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +188 [+146, +231] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +123 [+121, +126] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | +6.0% [-1.1, +13.0] (n.s.) | 0.088 | 0.352 | +8.6% [-0.4, +17.5] (n.s.) | 0.058 | 0.231 | 10 |
| fixed-count time, keep-alive | Otterize | +4.4% [-2.4, +11.2] (n.s.) | 0.178 | 0.377 | +3.0% [-5.5, +11.5] (n.s.) | 0.445 | 0.891 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | +5.3% [-1.8, +12.5] (n.s.) | 0.126 | 0.377 | +4.9% [-0.6, +10.5] (n.s.) | 0.077 | 0.231 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | +2.1% [-4.5, +8.7] (n.s.) | 0.494 | 0.494 | +2.5% [-5.3, +10.4] (n.s.) | 0.481 | 0.891 | 10 |
| fixed-count time, new conn | Hubble | +14.4% [+10.0, +18.8] | <0.001 | <0.001 | +14.8% [+11.7, +18.0] | <0.001 | <0.001 | 10 |
| fixed-count time, new conn | Otterize | +0.6% [-4.0, +5.1] (n.s.) | 0.776 | 0.776 | -0.8% [-6.7, +5.0] (n.s.) | 0.751 | 0.804 | 10 |
| fixed-count time, new conn | IG trace_tcp | +7.1% [+1.6, +12.7] | 0.017 | 0.051 | +9.2% [+4.1, +14.2] | 0.003 | 0.008 | 10 |
| fixed-count time, new conn | IG snapshot_socket | -1.4% [-4.6, +1.9] (n.s.) | 0.368 | 0.735 | -1.6% [-5.6, +2.4] (n.s.) | 0.402 | 0.804 | 10 |
| canary speed, workers, steady window (check) | Hubble | +0.44% [-1.52, +2.39] (n.s.) | 0.626 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | -0.65% [-7.15, +5.84] (n.s.) | 0.825 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | +1.61% [-1.28, +4.51] (n.s.) | 0.240 | 0.960 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | -0.25% [-3.39, +2.88] (n.s.) | 0.859 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 11.6% raw, 7.2% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.81; new conn: CV of the baseline time across cycles 9.5% raw, 4.7% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.90.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 10-04 14:25 | otterize hubble ig_tcp baseline ig_snap | 22.4 | 18.8 | 24.9 | 21.4 | 0.074 | 0.066 | 13.93 | 0.89 | 14.07 |
| 12 | 10-04 15:21 | baseline hubble ig_snap otterize ig_tcp | 20.6 | 18.4 | 22.2 | 21.1 | 0.076 | 0.068 | 14.15 | 0.91 | 15.09 |
| 13 | 10-04 16:18 | ig_snap baseline ig_tcp hubble otterize | 17.8 | 18.2 | 19.8 | 20.2 | 0.059 | 0.060 | 15.62 | 1.00 | 15.43 |
| 14 | 10-04 17:13 | ig_snap ig_tcp baseline otterize hubble | 18.9 | 19.0 | 19.2 | 18.5 | 0.060 | 0.060 | 15.39 | 0.99 | 15.52 |
| 15 | 10-04 18:09 | otterize ig_tcp hubble ig_snap baseline | 16.7 | 16.4 | 19.3 | 18.9 | 0.062 | 0.060 | 15.05 | 0.97 | 15.46 |
| 16 | 10-04 19:05 | ig_tcp otterize ig_snap hubble baseline | 18.0 | 18.4 | 19.8 | 20.1 | 0.060 | 0.060 | 15.77 | 1.01 | 14.57 |
| 17 | 10-04 20:02 | ig_tcp ig_snap otterize baseline hubble | 17.4 | 17.8 | 19.6 | 19.6 | 0.058 | 0.058 | 15.65 | 1.00 | 15.57 |
| 18 | 10-04 20:58 | hubble baseline otterize ig_snap ig_tcp | 15.8 | 15.9 | 18.9 | 18.9 | 0.057 | 0.059 | 16.02 | 1.03 | 16.13 |
| 19 | 10-04 21:53 | hubble otterize baseline ig_tcp ig_snap | 18.0 | 18.3 | 19.3 | 19.8 | 0.056 | 0.057 | 15.86 | 1.02 | 15.98 |
| 20 | 10-04 22:49 | baseline ig_snap hubble ig_tcp otterize | 15.6 | 15.4 | 18.9 | 19.7 | 0.056 | 0.058 | 16.09 | 1.03 | 15.93 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 11 Otterize; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.106 [+0.085, +0.128] | <0.001 | +0.122 | 0.002 | +0.106 [+0.085, +0.128] | 10 | robust |
| Δ observer CPU | Otterize | +0.090 [+0.081, +0.099] | <0.001 | +0.093 | 0.002 | +0.088 [+0.080, +0.097] | 9 | robust |
| Δ observer CPU | IG trace_tcp | +0.096 [+0.089, +0.103] | <0.001 | +0.092 | 0.002 | +0.096 [+0.089, +0.103] | 10 | robust |
| Δ observer CPU | IG snapshot_socket | +0.071 [+0.064, +0.078] | <0.001 | +0.073 | 0.002 | +0.071 [+0.064, +0.078] | 10 | robust |
| Δ observer anon memory | Hubble | +110 [+106, +114] | <0.001 | +110 | 0.002 | +110 [+106, +114] | 10 | robust |
| Δ observer anon memory | Otterize | +80 [+78, +83] | <0.001 | +80 | 0.002 | +81 [+78, +83] | 9 | robust |
| Δ observer anon memory | IG trace_tcp | +150 [+145, +155] | <0.001 | +147 | 0.002 | +150 [+145, +155] | 10 | robust |
| Δ observer anon memory | IG snapshot_socket | +116 [+113, +118] | <0.001 | +115 | 0.002 | +116 [+113, +118] | 10 | robust |
| fixed-count time, keep-alive | Hubble | +6.0% [-1.1, +13.0] (n.s.) | 0.528 | +5.2% | 0.131 | +6.0% [-1.1, +13.0] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | Otterize | +4.4% [-2.4, +11.2] (n.s.) | 0.711 | +3.9% | 0.131 | +5.2% [-2.3, +12.7] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | IG trace_tcp | +5.3% [-1.8, +12.5] (n.s.) | 0.628 | +5.5% | 0.193 | +5.3% [-1.8, +12.5] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | IG snapshot_socket | +2.1% [-4.5, +8.7] (n.s.) | 1.000 | -0.3% | 0.695 | +2.1% [-4.5, +8.7] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +14.4% [+10.0, +18.8] | <0.001 | +15.0% | 0.002 | +14.4% [+10.0, +18.8] | 10 | robust |
| fixed-count time, new conn | Otterize | +0.6% [-4.0, +5.1] (n.s.) | 1.000 | +1.8% | 0.375 | +1.4% [-3.4, +6.1] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | +7.1% [+1.6, +12.7] | 0.119 | +11.2% | 0.020 | +7.1% [+1.6, +12.7] | 10 | n.s. (primary) |
| fixed-count time, new conn | IG snapshot_socket | -1.4% [-4.6, +1.9] (n.s.) | 1.000 | -0.9% | 0.375 | -1.4% [-4.6, +1.9] (n.s.) | 10 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 1504 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 2.18 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 18.12 ± 2.10 (n=10) | 19.06 ± 1.48 (n=10) | +5.98% [-1.09, +13.04] (n.s.) (< 13.0% at 95%) | 0.088 | 0.528 | nginx-thrift 2.63 | 1.04 |
| keepalive | Otterize | 18.12 ± 2.10 (n=10) | 18.79 ± 1.60 (n=10) | +4.40% [-2.41, +11.20] (n.s.) (< 11.2% at 95%) | 0.178 | 0.711 | nginx-thrift 2.55 | 1.05 |
| keepalive | IG trace_tcp | 18.12 ± 2.10 (n=10) | 18.92 ± 0.95 (n=10) | +5.34% [-1.82, +12.50] (n.s.) (< 12.5% at 95%) | 0.126 | 0.628 | nginx-thrift 2.39 | 1.04 |
| keepalive | IG snapshot_socket | 18.12 ± 2.10 (n=10) | 18.36 ± 1.33 (n=10) | +2.09% [-4.54, +8.71] (n.s.) (< 8.7% at 95%) | 0.494 | 1.000 | nginx-thrift 2.20 | 1.04 |
| newconn | Hubble | 20.20 ± 1.92 (n=10) | 23.03 ± 1.30 (n=10) | +14.44% [+10.05, +18.83] | <0.001 | <0.001 | nginx-thrift 2.23 | 2.05 |
| newconn | Otterize | 20.20 ± 1.92 (n=10) | 20.24 ± 1.30 (n=10) | +0.59% [-3.96, +5.13] (n.s.) (< 5.1% at 95%) | 0.776 | 1.000 | nginx-thrift 2.24 | 2.07 |
| newconn | IG trace_tcp | 20.20 ± 1.92 (n=10) | 21.52 ± 0.85 (n=10) | +7.15% [+1.61, +12.68] | 0.017 | 0.119 | nginx-thrift 2.17 | 2.05 |
| newconn | IG snapshot_socket | 20.20 ± 1.92 (n=10) | 19.89 ± 1.73 (n=10) | -1.35% [-4.58, +1.87] (n.s.) (< 1.9% at 95%) | 0.368 | 1.000 | nginx-thrift 2.35 | 2.05 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 18.12 ± 2.10 | 11.62% | 11.62% | 10 |
| newconn | 20.20 ± 1.92 | 9.49% | 9.49% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.047 ± 0.008 | 0.006 | - | 0.233 ± 0.028 | 0.021 | - | - | - | - |
| Hubble | 0.154 ± 0.033 | 0.014 | +0.106 [+0.085, +0.128] | 0.378 ± 0.053 | 0.036 | +0.144 [+0.115, +0.174] | +1.44% | +0.051 | <0.001 / <0.001 |
| Otterize | 0.138 ± 0.012 | 0.008 | +0.090 [+0.081, +0.099] | 0.319 ± 0.028 | 0.025 | +0.085 [+0.063, +0.108] | +0.85% | +0.004 | <0.001 / <0.001 |
| IG trace_tcp | 0.144 ± 0.012 | 0.008 | +0.096 [+0.089, +0.103] | 0.378 ± 0.029 | 0.028 | +0.145 [+0.128, +0.161] | +1.45% | +0.062 | <0.001 / <0.001 |
| IG snapshot_socket | 0.119 ± 0.009 | 0.009 | +0.071 [+0.064, +0.078] | 0.322 ± 0.026 | 0.025 | +0.089 [+0.071, +0.106] | +0.89% | +0.023 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.005 [+0.002, +0.008] | -0.003 [-0.012, +0.005] (n.s.) | -0.004 [-0.020, +0.013] (n.s.) | 5% |
| Otterize | +0.073 [+0.068, +0.079] | -0.002 [-0.013, +0.010] (n.s.) | +0.068 [+0.049, +0.087] | 81% |
| IG trace_tcp | +0.068 [+0.063, +0.073] | +0.014 [+0.004, +0.025] | +0.075 [+0.057, +0.093] | 71% |
| IG snapshot_socket | +0.070 [+0.066, +0.074] | +0.022 [+0.012, +0.032] | +0.084 [+0.069, +0.098] | 99% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.207 [+0.164, +0.250] | +0.271 [+0.205, +0.338] | +0.080 [+0.067, +0.092] | 2.46 → 2.63 | 12% |
| keepalive | Otterize | +0.095 [+0.084, +0.106] | +0.100 [+0.040, +0.161] | +0.007 [-0.002, +0.016] (n.s.) | 2.46 → 2.55 | 7% |
| keepalive | IG trace_tcp | +0.115 [+0.105, +0.125] | +0.181 [+0.109, +0.254] | +0.093 [+0.077, +0.108] | 2.46 → 2.40 | 10% |
| keepalive | IG snapshot_socket | +0.069 [+0.061, +0.077] | +0.075 [+0.014, +0.136] | +0.021 [+0.011, +0.031] | 2.46 → 2.20 | 8% |
| newconn | Hubble | +0.363 [+0.338, +0.387] | +0.480 [+0.424, +0.535] | +0.128 [+0.118, +0.138] | 2.19 → 2.23 | 18% |
| newconn | Otterize | +0.093 [+0.086, +0.100] | +0.099 [+0.057, +0.141] | -0.002 [-0.013, +0.010] (n.s.) | 2.19 → 2.24 | 7% |
| newconn | IG trace_tcp | +0.152 [+0.145, +0.159] | +0.258 [+0.203, +0.313] | +0.133 [+0.118, +0.148] | 2.19 → 2.17 | 14% |
| newconn | IG snapshot_socket | +0.072 [+0.065, +0.080] | +0.095 [+0.047, +0.144] | +0.019 [+0.009, +0.028] | 2.19 → 2.35 | 9% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 678 ± 19 | 2.7 | -0.01 | 377 | - | - | 3787 ± 26 | - | - |
| Hubble | 804 ± 32 (peak 814) | 7.8 | 5.21 | 487 | +110 [+106, +114] | +126 [+109, +142] | 3911 ± 47 | +0.69% | <0.001 / <0.001 |
| Otterize | 774 ± 49 (peak 780) | 3.1 | 1.17 | 457 | +80 [+78, +83] | +96 [+70, +122] | 3896 ± 43 | +0.50% | <0.001 / <0.001 |
| IG trace_tcp | 866 ± 71 (peak 881) | 6.6 | -3.65 | 527 | +150 [+145, +155] | +188 [+146, +231] | 4036 ± 35 | +0.94% | <0.001 / <0.001 |
| IG snapshot_socket | 801 ± 19 (peak 842) | 14.7 | 2.41 | 493 | +116 [+113, +118] | +123 [+121, +126] | 3976 ± 35 | +0.72% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.039 | 0.088 | 0.038 | 0.039 | 0.040 |
| cilium-envoy | 0.006 | 0.005 | 0.006 | 0.006 | 0.005 |
| cilium-operator | 0.002 | 0.002 | 0.002 | 0.002 | 0.002 |
| hubble-relay | 0.000 | 0.025 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.004 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.087 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.088 | 0.071 |
| client-hubble | 0.000 | 0.033 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.009 | 0.000 |
| app | 0.062 | 0.067 | 0.063 | 0.065 | 0.062 |
| loadgen | 0.005 | 0.004 | 0.004 | 0.004 | 0.005 |
| k3s | 0.106 | 0.157 | 0.110 | 0.168 | 0.129 |
| k8s-addons | 0.003 | 0.003 | 0.004 | 0.003 | 0.003 |
| os | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 |
| harness | 0.021 | 0.021 | 0.021 | 0.021 | 0.021 |
| node | 0.233 | 0.378 | 0.319 | 0.378 | 0.322 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 19.98 ± 0.00 | 2.8 ± 0.3 | - | 3.7 ± 0.5 | - | 4.3 ± 0.8 | - | 0.13 |
| Hubble | 19.98 ± 0.00 | 3.2 ± 0.3 | +15.2% [+8.0, +22.4] | 4.3 ± 0.6 | +17.5% [+11.1, +23.9] | 9.9 ± 14.5 | +100.2% [-62.9, +263.3] (n.s.) | 0.13 |
| Otterize | 19.97 ± 0.01 | 2.9 ± 0.3 | +4.5% [-3.0, +11.9] (n.s.) | 3.9 ± 0.9 | +7.8% [-4.9, +20.5] (n.s.) | 7.3 ± 9.1 | +58.2% [-56.4, +172.7] (n.s.) | 0.14 |
| IG trace_tcp | 19.98 ± 0.00 | 2.9 ± 0.1 | +5.5% [-1.1, +12.1] (n.s.) | 3.8 ± 0.2 | +5.4% [-1.4, +12.1] (n.s.) | 4.8 ± 0.8 | +11.7% [+1.0, +22.4] (n.s.) | 0.13 |
| IG snapshot_socket | 19.98 ± 0.00 | 2.7 ± 0.3 | -2.1% [-8.5, +4.4] (n.s.) | 3.6 ± 0.4 | -1.8% [-8.8, +5.2] (n.s.) | 5.0 ± 2.7 | +18.3% [-26.4, +63.1] (n.s.) | 0.13 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 19.0 | 0.00 | 18.99 | - | - | - | - | - |
| Hubble | 19.2 | 0.20 | 19.00 | +2862 [+2194, +3531] | +5935 [+5417, +6454] | +2892 [+2640, +3145] | +4138 [+3745, +4530] | 286.8 (thesis 354.0) |
| Otterize | 21.0 | 0.95 | 20.03 | +307 [+177, +436] | +301 [+232, +370] | +146 [+112, +179] | +217 [-110, +544] (n.s.) | - |
| IG trace_tcp | 19.0 | 0.00 | 18.97 | +651 [+535, +766] | +1326 [+1195, +1456] | +647 [+583, +710] | +1562 [+1108, +2016] | 72.2 (thesis 76.1) |
| IG snapshot_socket | 19.0 | 0.00 | 19.01 | -16 [-88, +57] (n.s.) | +35 [-42, +113] (n.s.) | +17 [-21, +55] (n.s.) | +87 [-340, +513] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 5%. Lost events: 103 in the window, 196 over the whole run (fixed-count tests included). hubble_* series at the end: 290.

| Class | flows/s | share |
|---|---|---|
| app | 286.9 | 95% |
| probe | 0.3 | 0% |
| client_feedback | 2.7 | 1% |
| other | 11.6 | 4% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.071 [+0.064, +0.078] cores. Standing (window before the snapshot) minus baseline observer: +0.070 cores; one snapshot adds 0.35 ± 0.11 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.355 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.078 [+0.061, +0.094] | +0.101 | +0.106 [+0.075, +0.137] | +0.43% / +0.59% | +79 [+62, +96] | +0.13% |
| Otterize | +0.124 [+0.111, +0.137] | +0.133 | +0.112 [+0.077, +0.147] | +0.69% / +0.62% | +125 [+87, +163] | +0.21% |
| IG trace_tcp | +0.153 [+0.143, +0.163] | +0.163 | +0.207 [+0.176, +0.237] | +0.85% / +1.15% | +364 [+279, +450] | +0.62% |
| IG snapshot_socket | +0.138 [+0.128, +0.148] | +0.138 | +0.169 [+0.142, +0.196] | +0.77% / +0.94% | +269 [+263, +274] | +0.46% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 11 | baseline | 4 | 0.10% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 24.91 |
| 12 | baseline | 1 | 0.17% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 22.25 |
| 13 | baseline | 2 | 0.18% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.83 |
| 14 | baseline | 3 | 0.19% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.16 |
| 15 | baseline | 5 | 0.05% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.33 |
| 16 | baseline | 5 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.80 |
| 17 | baseline | 4 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.57 |
| 18 | baseline | 2 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 18.91 |
| 19 | baseline | 3 | 0.03% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.31 |
| 20 | baseline | 1 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 18.89 |
| 11 | Hubble | 2 | 0.21% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 25.05 |
| 12 | Hubble | 2 | 0.52% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 25.26 |
| 13 | Hubble | 4 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 22.20 |
| 14 | Hubble | 5 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 22.69 |
| 15 | Hubble | 3 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 21.31 |
| 16 | Hubble | 4 | 0.05% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 23.48 |
| 17 | Hubble | 5 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 23.14 |
| 18 | Hubble | 1 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 21.98 |
| 19 | Hubble | 1 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 21.97 |
| 20 | Hubble | 3 | 0.11% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 23.22 |
| 11 | Otterize | 1 | 0.62% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 23.35 |
| 12 | Otterize | 4 | 0.03% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.24 |
| 13 | Otterize | 5 | 0.24% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 20.18 |
| 14 | Otterize | 4 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 20.87 |
| 15 | Otterize | 1 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.44 |
| 16 | Otterize | 2 | 0.06% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 20.74 |
| 17 | Otterize | 3 | 0.26% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 20.68 |
| 18 | Otterize | 3 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.26 |
| 19 | Otterize | 2 | 0.08% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.70 |
| 20 | Otterize | 5 | 0.03% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 18.92 |
| 11 | IG trace_tcp | 3 | 0.21% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 22.77 |
| 12 | IG trace_tcp | 5 | 0.08% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 21.38 |
| 13 | IG trace_tcp | 3 | 0.13% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 22.08 |
| 14 | IG trace_tcp | 2 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 21.83 |
| 15 | IG trace_tcp | 2 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 21.62 |
| 16 | IG trace_tcp | 1 | 0.06% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 22.40 |
| 17 | IG trace_tcp | 1 | 0.03% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 20.58 |
| 18 | IG trace_tcp | 5 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 21.00 |
| 19 | IG trace_tcp | 4 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 21.66 |
| 20 | IG trace_tcp | 4 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.91 |
| 11 | IG snapshot_socket | 5 | 0.20% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 24.53 |
| 12 | IG snapshot_socket | 3 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.72 |
| 13 | IG snapshot_socket | 1 | 0.62% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 20.00 |
| 14 | IG snapshot_socket | 1 | 0.05% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.03 |
| 15 | IG snapshot_socket | 4 | 0.37% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 20.39 |
| 16 | IG snapshot_socket | 3 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.56 |
| 17 | IG snapshot_socket | 2 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 18.88 |
| 18 | IG snapshot_socket | 4 | 0.01% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 19.42 |
| 19 | IG snapshot_socket | 5 | 0.03% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 18.49 |
| 20 | IG snapshot_socket | 2 | 0.04% | 6ac25d9a33e2d67d2b77a861 | 5ae2836b,f36218b5,d4335b59 | 18.88 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 11 | baseline | 12.90/13.41 | 13.66/14.20 | 13.20/12.96 | 12.82/13.96 | 0.89 |
| 11 | Hubble | 14.94/14.31 | 14.78/14.21 | 14.75/14.78 | 14.73/14.62 | 0.93 |
| 11 | Otterize | 15.26/15.22 | 14.11/14.26 | 13.91/14.36 | 13.73/14.88 | 0.91 |
| 11 | IG trace_tcp | 15.16/14.94 | 14.82/14.59 | 14.32/14.01 | 14.74/14.75 | 0.94 |
| 11 | IG snapshot_socket | 14.76/11.83 | 14.17/11.95 | 13.97/11.87 | 13.55/11.86 | 0.84 |
| 12 | baseline | 14.36/13.95 | 14.35/13.96 | 13.99/13.86 | 14.99/14.65 | 0.91 |
| 12 | Hubble | 13.21/13.64 | 14.45/14.45 | 15.53/14.15 | 16.06/15.05 | 0.93 |
| 12 | Otterize | 15.78/15.47 | 16.15/15.96 | 16.49/15.76 | 15.79/15.98 | 1.03 |
| 12 | IG trace_tcp | 15.76/16.09 | 15.42/15.74 | 15.62/15.43 | 16.02/16.36 | 1.00 |
| 12 | IG snapshot_socket | 14.61/15.53 | 14.77/15.61 | 14.85/15.40 | 14.97/15.12 | 0.97 |
| 13 | baseline | 15.37/15.91 | 15.70/15.54 | 16.23/15.65 | 15.79/15.98 | 1.00 |
| 13 | Hubble | 15.30/15.79 | 14.77/15.64 | 15.34/15.99 | 15.16/15.64 | 0.98 |
| 13 | Otterize | 15.75/16.25 | 15.37/15.66 | 14.95/14.43 | 15.87/14.47 | 0.99 |
| 13 | IG trace_tcp | 16.35/15.87 | 15.62/15.17 | 16.05/13.75 | 15.97/14.85 | 0.99 |
| 13 | IG snapshot_socket | 15.33/16.09 | 15.22/15.63 | 15.71/15.59 | 15.03/16.55 | 0.99 |
| 14 | baseline | 16.05/15.82 | 15.32/15.47 | 16.18/15.11 | 15.38/14.72 | 0.99 |
| 14 | Hubble | 15.64/15.49 | 15.29/15.36 | 13.93/15.39 | 13.26/15.13 | 0.98 |
| 14 | Otterize | 15.60/15.84 | 15.50/15.52 | 15.88/15.65 | 14.90/15.32 | 0.99 |
| 14 | IG trace_tcp | 15.86/16.22 | 15.68/15.97 | 15.53/15.39 | 15.92/16.02 | 1.01 |
| 14 | IG snapshot_socket | 15.09/15.72 | 15.39/15.71 | 15.51/16.02 | 15.61/16.41 | 1.00 |
| 15 | baseline | 15.42/15.24 | 14.99/15.11 | 15.38/15.21 | 15.12/15.33 | 0.97 |
| 15 | Hubble | 15.74/16.35 | 15.56/16.00 | 16.16/16.29 | 15.41/15.89 | 1.01 |
| 15 | Otterize | 14.86/15.63 | 14.73/15.97 | 15.04/15.95 | 15.02/16.50 | 0.98 |
| 15 | IG trace_tcp | 16.07/15.67 | 15.95/15.20 | 15.35/13.29 | 16.62/13.81 | 1.00 |
| 15 | IG snapshot_socket | 16.45/16.31 | 15.56/15.50 | 15.40/14.76 | 15.31/14.83 | 1.00 |
| 16 | baseline | 16.07/15.46 | 15.96/15.57 | 15.61/16.29 | 16.29/15.39 | 1.01 |
| 16 | Hubble | 14.67/15.30 | 14.95/15.37 | 15.22/16.02 | 15.32/15.36 | 0.97 |
| 16 | Otterize | 13.20/11.61 | 12.91/11.21 | 12.87/10.58 | 13.37/11.02 | 0.77 |
| 16 | IG trace_tcp | 15.58/15.47 | 15.22/15.31 | 15.48/15.30 | 15.57/15.37 | 0.98 |
| 16 | IG snapshot_socket | 14.25/15.39 | 14.06/15.14 | 14.04/14.71 | 14.22/15.55 | 0.94 |
| 17 | baseline | 15.53/15.15 | 15.67/15.63 | 15.83/16.01 | 15.64/15.58 | 1.00 |
| 17 | Hubble | 16.14/16.07 | 15.84/15.79 | 16.41/15.57 | 16.29/15.76 | 1.01 |
| 17 | Otterize | 15.93/15.73 | 15.45/15.64 | 15.00/15.01 | 15.35/16.09 | 1.00 |
| 17 | IG trace_tcp | 15.45/16.17 | 15.23/15.70 | 15.05/15.96 | 15.39/15.38 | 0.99 |
| 17 | IG snapshot_socket | 15.96/15.11 | 15.66/15.07 | 15.85/15.02 | 15.82/14.53 | 0.99 |
| 18 | baseline | 15.67/16.17 | 16.00/16.04 | 15.24/16.19 | 15.13/16.10 | 1.03 |
| 18 | Hubble | 16.29/16.11 | 15.96/15.72 | 16.22/15.86 | 16.21/15.80 | 1.02 |
| 18 | Otterize | 16.56/16.51 | 16.33/16.31 | 16.24/16.57 | 15.73/16.32 | 1.05 |
| 18 | IG trace_tcp | 16.53/16.33 | 16.48/16.00 | 16.49/15.38 | 16.48/16.33 | 1.04 |
| 18 | IG snapshot_socket | 16.50/16.39 | 16.36/16.10 | 16.90/15.60 | 15.61/16.04 | 1.04 |
| 19 | baseline | 16.23/16.18 | 15.82/15.90 | 16.04/15.65 | 16.58/15.34 | 1.02 |
| 19 | Hubble | 16.44/16.28 | 15.91/16.01 | 15.96/15.63 | 15.39/15.98 | 1.02 |
| 19 | Otterize | 16.11/15.93 | 16.04/15.62 | 15.69/15.53 | 15.58/15.72 | 1.02 |
| 19 | IG trace_tcp | 16.11/16.20 | 15.97/15.99 | 15.86/16.19 | 16.35/16.40 | 1.03 |
| 19 | IG snapshot_socket | 16.05/15.74 | 16.31/16.24 | 16.54/16.20 | 16.54/16.29 | 1.04 |
| 20 | baseline | 16.32/16.05 | 16.18/16.01 | 14.56/16.36 | 16.10/16.47 | 1.03 |
| 20 | Hubble | 16.04/15.80 | 16.04/16.07 | 16.38/16.51 | 15.45/15.92 | 1.03 |
| 20 | Otterize | 15.07/16.23 | 15.63/16.09 | 15.57/15.73 | 15.12/16.24 | 1.02 |
| 20 | IG trace_tcp | 16.10/15.75 | 16.16/15.33 | 14.44/15.54 | 15.07/15.72 | 1.01 |
| 20 | IG snapshot_socket | 16.50/15.74 | 16.16/15.60 | 16.80/15.89 | 16.84/16.22 | 1.02 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 17.66 ± 1.27 (n=10) | 19.06 ± 1.32 (n=10) | +8.59% [-0.35, +17.54] (n.s.) (< 17.5% at 95%) | 0.058 | 0.231 |
| keepalive | Otterize | 17.66 ± 1.27 (n=10) | 18.12 ± 1.87 (n=10) | +3.00% [-5.51, +11.52] (n.s.) (< 11.5% at 95%) | 0.445 | 0.891 |
| keepalive | IG trace_tcp | 17.66 ± 1.27 (n=10) | 18.45 ± 0.81 (n=10) | +4.91% [-0.65, +10.47] (n.s.) (< 10.5% at 95%) | 0.077 | 0.231 |
| keepalive | IG snapshot_socket | 17.66 ± 1.27 (n=10) | 18.00 ± 0.91 (n=10) | +2.55% [-5.29, +10.39] (n.s.) (< 10.4% at 95%) | 0.481 | 0.891 |
| newconn | Hubble | 19.83 ± 0.94 (n=10) | 22.77 ± 1.32 (n=10) | +14.85% [+11.70, +17.99] | <0.001 | <0.001 |
| newconn | Otterize | 19.83 ± 0.94 (n=10) | 19.62 ± 1.37 (n=10) | -0.85% [-6.72, +5.02] (n.s.) (< 5.0% at 95%) | 0.751 | 0.804 |
| newconn | IG trace_tcp | 19.83 ± 0.94 (n=10) | 21.60 ± 0.98 (n=10) | +9.18% [+4.12, +14.24] | 0.003 | 0.008 |
| newconn | IG snapshot_socket | 19.83 ± 0.94 (n=10) | 19.48 ± 0.61 (n=10) | -1.56% [-5.56, +2.44] (n.s.) (< 2.4% at 95%) | 0.402 | 0.804 |
