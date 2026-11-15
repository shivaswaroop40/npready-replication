# bank

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.069 [+0.051, +0.088] | <0.001 | <0.001 | +0.071 [+0.056, +0.086] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.081 [+0.060, +0.101] | <0.001 | <0.001 | +0.082 [+0.066, +0.098] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.112 [+0.092, +0.132] | <0.001 | <0.001 | +0.112 [+0.092, +0.132] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.094 [+0.075, +0.113] | <0.001 | <0.001 | +0.097 [+0.078, +0.115] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Hubble | +0.047 [+0.045, +0.048] | <0.001 | <0.001 | +0.047 [+0.045, +0.049] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.070 [+0.069, +0.071] | <0.001 | <0.001 | +0.070 [+0.068, +0.072] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.078 [+0.075, +0.080] | <0.001 | <0.001 | +0.077 [+0.074, +0.080] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.070 [+0.067, +0.072] | <0.001 | <0.001 | +0.070 [+0.068, +0.072] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | +0.004 [-0.008, +0.016] (n.s.) | 0.474 | 1.000 | +0.005 [-0.007, +0.016] (n.s.) | 0.393 | 1.000 | 10 |
| Δ app CPU (cores) | Otterize | -0.001 [-0.014, +0.012] (n.s.) | 0.863 | 1.000 | +0.000 [-0.012, +0.012] (n.s.) | 0.977 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | -0.001 [-0.017, +0.015] (n.s.) | 0.915 | 1.000 | +0.001 [-0.015, +0.017] (n.s.) | 0.915 | 1.000 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | -0.003 [-0.016, +0.009] (n.s.) | 0.547 | 1.000 | -0.002 [-0.015, +0.011] (n.s.) | 0.746 | 1.000 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.026 [+0.025, +0.028] | <0.001 | <0.001 | +0.027 [+0.026, +0.028] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.007 [+0.005, +0.009] | <0.001 | <0.001 | +0.007 [+0.006, +0.009] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.037 [+0.033, +0.040] | <0.001 | <0.001 | +0.036 [+0.031, +0.041] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.025 [+0.023, +0.027] | <0.001 | <0.001 | +0.025 [+0.024, +0.027] | <0.001 | <0.001 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +106 [+103, +110] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +82 [+80, +85] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +143 [+137, +149] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +113 [+110, +116] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +124 [+108, +140] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +102 [+84, +120] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +180 [+137, +222] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +122 [+117, +127] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | +19.6% [+15.3, +23.8] | <0.001 | <0.001 | +18.6% [+13.5, +23.8] | <0.001 | <0.001 | 10 |
| fixed-count time, keep-alive | Otterize | +5.3% [+1.6, +8.9] | 0.009 | 0.019 | +4.9% [-0.4, +10.1] (n.s.) | 0.066 | 0.133 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | +10.3% [+5.7, +15.0] | <0.001 | 0.002 | +10.4% [+4.3, +16.5] | 0.004 | 0.012 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | +2.4% [-2.3, +7.1] (n.s.) | 0.277 | 0.277 | +4.0% [-1.2, +9.1] (n.s.) | 0.115 | 0.133 | 10 |
| fixed-count time, new conn | Hubble | +18.9% [+12.5, +25.2] | <0.001 | <0.001 | +16.7% [+9.7, +23.6] | <0.001 | 0.002 | 10 |
| fixed-count time, new conn | Otterize | +3.1% [-1.6, +7.9] (n.s.) | 0.171 | 0.342 | +3.0% [-2.4, +8.3] (n.s.) | 0.241 | 0.481 | 10 |
| fixed-count time, new conn | IG trace_tcp | +9.6% [+5.0, +14.2] | 0.001 | 0.003 | +8.0% [+1.6, +14.4] | 0.020 | 0.060 | 10 |
| fixed-count time, new conn | IG snapshot_socket | +1.9% [-3.3, +7.2] (n.s.) | 0.421 | 0.421 | +2.0% [-2.8, +6.8] (n.s.) | 0.366 | 0.481 | 10 |
| canary speed, workers, steady window (check) | Hubble | +0.95% [-0.76, +2.66] (n.s.) | 0.242 | 0.593 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | +0.62% [-1.86, +3.09] (n.s.) | 0.588 | 0.593 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | +0.96% [-0.04, +1.95] (n.s.) | 0.059 | 0.235 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | +1.22% [-0.76, +3.20] (n.s.) | 0.198 | 0.593 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 4.1% raw, 5.9% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.21; new conn: CV of the baseline time across cycles 5.1% raw, 5.6% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.05.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 11 | 10-04 23:56 | otterize ig_tcp hubble ig_snap baseline | 13.5 | 13.4 | 13.9 | 14.0 | 0.135 | 0.135 | 15.95 | 0.99 | 15.95 |
| 12 | 10-05 00:54 | ig_tcp ig_snap otterize baseline hubble | 14.0 | 13.7 | 14.7 | 14.2 | 0.127 | 0.125 | 15.90 | 0.99 | 15.86 |
| 13 | 10-05 01:51 | hubble otterize baseline ig_tcp ig_snap | 14.6 | 14.2 | 15.9 | 15.4 | 0.131 | 0.129 | 15.92 | 0.99 | 15.98 |
| 14 | 10-05 02:50 | ig_snap ig_tcp baseline otterize hubble | 13.2 | 12.3 | 13.9 | 13.4 | 0.143 | 0.136 | 15.18 | 0.95 | 15.91 |
| 15 | 10-05 03:47 | hubble baseline otterize ig_snap ig_tcp | 14.2 | 14.7 | 14.6 | 15.1 | 0.140 | 0.142 | 16.23 | 1.01 | 16.07 |
| 16 | 10-05 04:45 | ig_tcp otterize ig_snap hubble baseline | 14.3 | 14.8 | 14.9 | 15.4 | 0.164 | 0.164 | 16.06 | 1.00 | 16.22 |
| 17 | 10-05 05:43 | ig_snap baseline ig_tcp hubble otterize | 14.9 | 14.1 | 15.5 | 15.0 | 0.137 | 0.135 | 15.80 | 0.98 | 16.17 |
| 18 | 10-05 06:40 | otterize hubble ig_tcp baseline ig_snap | 13.5 | 13.2 | 14.3 | 14.1 | 0.136 | 0.139 | 16.31 | 1.02 | 16.05 |
| 19 | 10-05 07:39 | baseline ig_snap hubble ig_tcp otterize | 13.6 | 13.1 | 13.8 | 13.3 | 0.158 | 0.157 | 15.88 | 0.99 | 16.04 |
| 20 | 10-05 08:36 | baseline hubble ig_snap otterize ig_tcp | 13.5 | 13.0 | 13.8 | 13.4 | 0.123 | 0.120 | 15.59 | 0.97 | 15.72 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 11 Otterize; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.047 [+0.045, +0.048] | <0.001 | +0.046 | 0.002 | +0.047 [+0.045, +0.048] | 10 | robust |
| Δ observer CPU | Otterize | +0.070 [+0.069, +0.071] | <0.001 | +0.070 | 0.002 | +0.071 [+0.069, +0.072] | 9 | robust |
| Δ observer CPU | IG trace_tcp | +0.078 [+0.075, +0.080] | <0.001 | +0.077 | 0.002 | +0.078 [+0.075, +0.080] | 10 | robust |
| Δ observer CPU | IG snapshot_socket | +0.070 [+0.067, +0.072] | <0.001 | +0.069 | 0.002 | +0.070 [+0.067, +0.072] | 10 | robust |
| Δ observer anon memory | Hubble | +106 [+103, +110] | <0.001 | +107 | 0.002 | +106 [+103, +110] | 10 | robust |
| Δ observer anon memory | Otterize | +82 [+80, +85] | <0.001 | +82 | 0.002 | +83 [+81, +86] | 9 | robust |
| Δ observer anon memory | IG trace_tcp | +143 [+137, +149] | <0.001 | +144 | 0.002 | +143 [+137, +149] | 10 | robust |
| Δ observer anon memory | IG snapshot_socket | +113 [+110, +116] | <0.001 | +115 | 0.002 | +113 [+110, +116] | 10 | robust |
| fixed-count time, keep-alive | Hubble | +19.6% [+15.3, +23.8] | <0.001 | +18.8% | 0.002 | +19.6% [+15.3, +23.8] | 10 | robust |
| fixed-count time, keep-alive | Otterize | +5.3% [+1.6, +8.9] | 0.037 | +4.7% | 0.010 | +5.4% [+1.3, +9.5] | 9 | robust |
| fixed-count time, keep-alive | IG trace_tcp | +10.3% [+5.7, +15.0] | 0.004 | +10.4% | 0.002 | +10.3% [+5.7, +15.0] | 10 | robust |
| fixed-count time, keep-alive | IG snapshot_socket | +2.4% [-2.3, +7.1] (n.s.) | 0.554 | +1.7% | 0.322 | +2.4% [-2.3, +7.1] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +18.9% [+12.5, +25.2] | <0.001 | +19.5% | 0.002 | +18.9% [+12.5, +25.2] | 10 | robust |
| fixed-count time, new conn | Otterize | +3.1% [-1.6, +7.9] (n.s.) | 0.513 | +3.8% | 0.160 | +3.0% [-2.4, +8.4] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | +9.6% [+5.0, +14.2] | 0.005 | +8.4% | 0.002 | +9.6% [+5.0, +14.2] | 10 | robust |
| fixed-count time, new conn | IG snapshot_socket | +1.9% [-3.3, +7.2] (n.s.) | 0.554 | +2.4% | 0.432 | +1.9% [-3.3, +7.2] (n.s.) | 10 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 608 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 1.11 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 13.93 ± 0.57 (n=10) | 16.63 ± 0.56 (n=10) | +19.57% [+15.33, +23.81] | <0.001 | <0.001 | frontend 0.75 | 3.03 |
| keepalive | Otterize | 13.93 ± 0.57 (n=10) | 14.66 ± 0.82 (n=10) | +5.27% [+1.65, +8.89] | 0.009 | 0.037 | frontend 1.01 | 3.06 |
| keepalive | IG trace_tcp | 13.93 ± 0.57 (n=10) | 15.35 ± 0.66 (n=10) | +10.34% [+5.72, +14.97] | <0.001 | 0.004 | frontend 0.91 | 3.03 |
| keepalive | IG snapshot_socket | 13.93 ± 0.57 (n=10) | 14.24 ± 0.63 (n=10) | +2.40% [-2.29, +7.08] (n.s.) (< 7.1% at 95%) | 0.277 | 0.554 | frontend 1.01 | 3.03 |
| newconn | Hubble | 14.54 ± 0.74 (n=10) | 17.24 ± 0.73 (n=10) | +18.88% [+12.53, +25.22] | <0.001 | <0.001 | frontend 0.71 | 4.00 |
| newconn | Otterize | 14.54 ± 0.74 (n=10) | 14.96 ± 0.38 (n=10) | +3.13% [-1.63, +7.89] (n.s.) (< 7.9% at 95%) | 0.171 | 0.513 | frontend 0.86 | 4.03 |
| newconn | IG trace_tcp | 14.54 ± 0.74 (n=10) | 15.90 ± 0.44 (n=10) | +9.61% [+5.05, +14.17] | 0.001 | 0.005 | frontend 0.98 | 4.01 |
| newconn | IG snapshot_socket | 14.54 ± 0.74 (n=10) | 14.78 ± 0.55 (n=10) | +1.94% [-3.27, +7.16] (n.s.) (< 7.2% at 95%) | 0.421 | 0.554 | frontend 1.03 | 4.00 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 13.93 ± 0.57 | 4.07% | 4.07% | 10 |
| newconn | 14.54 ± 0.74 | 5.08% | 5.08% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.041 ± 0.001 | 0.004 | - | 0.281 ± 0.018 | 0.107 | - | - | - | - |
| Hubble | 0.087 ± 0.002 | 0.008 | +0.047 [+0.045, +0.048] | 0.350 ± 0.023 | 0.114 | +0.069 [+0.051, +0.088] | +0.69% | +0.026 | <0.001 / <0.001 |
| Otterize | 0.111 ± 0.002 | 0.005 | +0.070 [+0.069, +0.071] | 0.362 ± 0.020 | 0.106 | +0.081 [+0.060, +0.101] | +0.81% | +0.007 | <0.001 / <0.001 |
| IG trace_tcp | 0.119 ± 0.004 | 0.005 | +0.078 [+0.075, +0.080] | 0.393 ± 0.020 | 0.110 | +0.112 [+0.092, +0.132] | +1.12% | +0.037 | <0.001 / <0.001 |
| IG snapshot_socket | 0.110 ± 0.003 | 0.008 | +0.070 [+0.067, +0.072] | 0.375 ± 0.017 | 0.106 | +0.094 [+0.075, +0.113] | +0.94% | +0.025 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.010 [+0.009, +0.012] | +0.004 [+0.002, +0.007] | +0.015 [+0.006, +0.025] | 23% |
| Otterize | +0.063 [+0.061, +0.065] | +0.009 [+0.007, +0.012] | +0.083 [+0.075, +0.091] | 90% |
| IG trace_tcp | +0.071 [+0.069, +0.074] | +0.026 [+0.024, +0.028] | +0.099 [+0.091, +0.107] | 92% |
| IG snapshot_socket | +0.068 [+0.066, +0.070] | +0.022 [+0.020, +0.025] | +0.095 [+0.087, +0.103] | 98% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.449 [+0.410, +0.488] | +0.652 [+0.602, +0.703] | +0.244 [+0.237, +0.252] | 0.94 → 0.77 | 19% |
| keepalive | Otterize | +0.113 [+0.106, +0.120] | +0.150 [+0.085, +0.216] | +0.012 [+0.005, +0.019] | 0.94 → 1.07 | 7% |
| keepalive | IG trace_tcp | +0.150 [+0.128, +0.173] | +0.340 [+0.272, +0.408] | +0.192 [+0.146, +0.238] | 0.94 → 0.92 | 12% |
| keepalive | IG snapshot_socket | +0.071 [+0.069, +0.073] | +0.129 [+0.055, +0.204] | +0.024 [+0.018, +0.031] | 0.94 → 1.02 | 8% |
| newconn | Hubble | +0.580 [+0.542, +0.617] | +0.801 [+0.694, +0.908] | +0.266 [+0.250, +0.281] | 1.16 → 0.74 | 24% |
| newconn | Otterize | +0.117 [+0.110, +0.124] | +0.046 [-0.001, +0.092] (n.s.) | +0.007 [-0.001, +0.015] (n.s.) | 1.16 → 0.88 | 7% |
| newconn | IG trace_tcp | +0.180 [+0.157, +0.204] | +0.377 [+0.267, +0.487] | +0.229 [+0.179, +0.279] | 1.16 → 1.03 | 16% |
| newconn | IG snapshot_socket | +0.068 [+0.065, +0.072] | +0.093 [+0.031, +0.154] | +0.027 [+0.019, +0.036] | 1.16 → 1.09 | 8% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 674 ± 17 | 2.7 | 1.75 | 368 | - | - | 3982 ± 46 | - | - |
| Hubble | 798 ± 29 (peak 815) | 12.5 | 8.97 | 474 | +106 [+103, +110] | +124 [+108, +140] | 4099 ± 54 | +0.66% | <0.001 / <0.001 |
| Otterize | 776 ± 34 (peak 781) | 2.8 | 1.70 | 450 | +82 [+80, +85] | +102 [+84, +120] | 4090 ± 65 | +0.52% | <0.001 / <0.001 |
| IG trace_tcp | 854 ± 65 (peak 860) | 3.4 | -0.56 | 510 | +143 [+137, +149] | +180 [+137, +222] | 4203 ± 67 | +0.89% | <0.001 / <0.001 |
| IG snapshot_socket | 796 ± 16 (peak 849) | 15.4 | 6.88 | 481 | +113 [+110, +116] | +122 [+117, +127] | 4157 ± 50 | +0.71% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.032 | 0.052 | 0.033 | 0.033 | 0.033 |
| cilium-envoy | 0.007 | 0.008 | 0.008 | 0.008 | 0.008 |
| cilium-operator | 0.002 | 0.002 | 0.002 | 0.002 | 0.002 |
| hubble-relay | 0.000 | 0.011 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.006 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.063 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.073 | 0.067 |
| client-hubble | 0.000 | 0.015 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.003 | 0.000 |
| app | 0.140 | 0.144 | 0.139 | 0.139 | 0.136 |
| loadgen | 0.005 | 0.005 | 0.005 | 0.005 | 0.005 |
| k3s | 0.074 | 0.100 | 0.080 | 0.111 | 0.099 |
| k8s-addons | 0.005 | 0.005 | 0.005 | 0.005 | 0.005 |
| os | 0.001 | 0.001 | 0.001 | 0.001 | 0.001 |
| harness | 0.019 | 0.019 | 0.019 | 0.020 | 0.019 |
| node | 0.281 | 0.350 | 0.362 | 0.393 | 0.375 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%. At under 5 req/s the window holds few requests; do not read the p95/p99 deltas.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 1.76 ± 0.03 | 9.4 ± 0.5 | - | 1090.0 ± 31.6 | - | 1470.0 ± 380.2 | - | 83.15 |
| Hubble | 1.74 ± 0.04 | 11.6 ± 0.5 | +23.8% [+17.1, +30.4] | 1100.0 ± 0.0 | +1.0% [-1.3, +3.3] (n.s.) | 1450.0 ± 353.6 | -0.6% [-7.4, +6.1] (n.s.) | 83.84 |
| Otterize | 1.77 ± 0.03 | 9.5 ± 0.5 | +1.4% [-5.2, +8.1] (n.s.) | 1080.0 ± 42.2 | -0.8% [-4.7, +3.0] (n.s.) | 1670.0 ± 374.3 | +19.5% [-7.7, +46.6] (n.s.) | 82.46 |
| IG trace_tcp | 1.75 ± 0.05 | 10.5 ± 0.5 | +12.0% [+6.1, +17.9] | 1090.0 ± 31.6 | +0.1% [-3.1, +3.3] (n.s.) | 1730.0 ± 405.7 | +28.7% [-9.0, +66.3] (n.s.) | 81.46 |
| IG snapshot_socket | 1.76 ± 0.04 | 9.7 ± 0.5 | +3.3% [-0.5, +7.2] (n.s.) | 1070.0 ± 48.3 | -1.7% [-6.0, +2.5] (n.s.) | 1440.0 ± 374.8 | +0.1% [-16.1, +16.3] (n.s.) | 85.35 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 9.3 | 3.15 | 6.17 | - | - | - | - | - |
| Hubble | 9.5 | 3.39 | 6.10 | +13745 [+12468, +15022] | +18299 [+16693, +19905] | +4570 [+4170, +4971] | +7079 [+6046, +8111] | 113.4 (thesis 101.3) |
| Otterize | 11.2 | 4.34 | 6.79 | +1405 [+1160, +1649] | +1516 [+1273, +1758] | +376 [+316, +436] | -218 [-592, +156] (n.s.) | - |
| IG trace_tcp | 9.2 | 3.17 | 6.00 | +2269 [+1623, +2914] | +3237 [+2537, +3937] | +808 [+633, +983] | +2408 [+1505, +3311] | 23.8 (thesis 28.8) |
| IG snapshot_socket | 9.4 | 3.16 | 6.24 | +73 [+8, +137] | +15 [-54, +84] (n.s.) | +4 [-13, +21] (n.s.) | -6 [-388, +377] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 13%. Lost events: 37 in the window, 115 over the whole run (fixed-count tests included). hubble_* series at the end: 255.

| Class | flows/s | share |
|---|---|---|
| app | 96.3 | 78% |
| probe | 18.0 | 15% |
| client_feedback | 2.7 | 2% |
| other | 7.0 | 6% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.070 [+0.067, +0.072] cores. Standing (window before the snapshot) minus baseline observer: +0.068 cores; one snapshot adds 0.41 ± 0.12 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.279 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.037 [+0.035, +0.039] | +0.046 | +0.064 [+0.043, +0.084] | +0.20% / +0.35% | +92 [+65, +120] | +0.16% |
| Otterize | +0.100 [+0.097, +0.103] | +0.103 | +0.127 [+0.106, +0.149] | +0.56% / +0.71% | +140 [+106, +173] | +0.24% |
| IG trace_tcp | +0.142 [+0.138, +0.146] | +0.145 | +0.202 [+0.177, +0.227] | +0.79% / +1.12% | +360 [+277, +443] | +0.62% |
| IG snapshot_socket | +0.134 [+0.130, +0.139] | +0.135 | +0.183 [+0.159, +0.208] | +0.75% / +1.02% | +265 [+252, +277] | +0.45% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 11 | baseline | 5 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 13.90 |
| 12 | baseline | 4 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.71 |
| 13 | baseline | 3 | 0.00% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.92 |
| 14 | baseline | 3 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 13.92 |
| 15 | baseline | 2 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.60 |
| 16 | baseline | 5 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.94 |
| 17 | baseline | 2 | 0.00% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.50 |
| 18 | baseline | 4 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.32 |
| 19 | baseline | 1 | 0.26% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 13.80 |
| 20 | baseline | 1 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 13.82 |
| 11 | Hubble | 3 | 0.03% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.81 |
| 12 | Hubble | 5 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.53 |
| 13 | Hubble | 1 | 0.03% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.72 |
| 14 | Hubble | 5 | 0.05% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 18.42 |
| 15 | Hubble | 1 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 18.31 |
| 16 | Hubble | 4 | 0.00% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.89 |
| 17 | Hubble | 4 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 17.07 |
| 18 | Hubble | 2 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 17.10 |
| 19 | Hubble | 3 | 0.05% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 18.01 |
| 20 | Hubble | 2 | 0.05% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.53 |
| 11 | Otterize | 1 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.51 |
| 12 | Otterize | 3 | 0.04% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.81 |
| 13 | Otterize | 2 | 0.04% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.51 |
| 14 | Otterize | 4 | 0.03% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.71 |
| 15 | Otterize | 3 | 0.24% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.07 |
| 16 | Otterize | 2 | 0.03% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.86 |
| 17 | Otterize | 5 | 0.03% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.99 |
| 18 | Otterize | 1 | 0.04% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.02 |
| 19 | Otterize | 5 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.31 |
| 20 | Otterize | 4 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.78 |
| 11 | IG trace_tcp | 2 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.47 |
| 12 | IG trace_tcp | 1 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.48 |
| 13 | IG trace_tcp | 4 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.12 |
| 14 | IG trace_tcp | 2 | 0.00% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.00 |
| 15 | IG trace_tcp | 5 | 0.00% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.50 |
| 16 | IG trace_tcp | 1 | 0.04% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.14 |
| 17 | IG trace_tcp | 3 | 0.04% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.51 |
| 18 | IG trace_tcp | 3 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.79 |
| 19 | IG trace_tcp | 4 | 0.04% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.98 |
| 20 | IG trace_tcp | 5 | 0.01% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 16.03 |
| 11 | IG snapshot_socket | 4 | 0.05% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.92 |
| 12 | IG snapshot_socket | 2 | 0.06% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.17 |
| 13 | IG snapshot_socket | 5 | 0.03% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.72 |
| 14 | IG snapshot_socket | 1 | 0.03% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 13.79 |
| 15 | IG snapshot_socket | 4 | 0.02% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.89 |
| 16 | IG snapshot_socket | 3 | 0.06% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.55 |
| 17 | IG snapshot_socket | 1 | 0.03% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.10 |
| 18 | IG snapshot_socket | 5 | 0.36% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 14.72 |
| 19 | IG snapshot_socket | 2 | 0.04% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.48 |
| 20 | IG snapshot_socket | 3 | 0.07% | 6ac2e54594d679d21b15f79c | 7bcffd72,c70a8b65,a11f086d | 15.49 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 11 | baseline | 15.68/15.66 | 15.98/15.93 | 15.64/16.26 | 16.26/16.18 | 0.99 |
| 11 | Hubble | 15.76/16.02 | 16.11/16.05 | 13.45/15.25 | 13.83/15.08 | 1.00 |
| 11 | Otterize | 16.17/16.19 | 16.03/16.02 | 16.41/16.24 | 16.42/16.23 | 1.00 |
| 11 | IG trace_tcp | 15.21/15.63 | 15.65/16.03 | 15.56/15.95 | 15.57/15.70 | 0.99 |
| 11 | IG snapshot_socket | 15.00/16.47 | 15.33/16.34 | 14.81/16.27 | 14.75/16.63 | 0.99 |
| 12 | baseline | 16.06/15.56 | 16.17/15.64 | 15.86/15.51 | 16.34/14.76 | 0.99 |
| 12 | Hubble | 16.32/15.84 | 15.98/15.63 | 16.24/15.51 | 16.08/15.37 | 0.98 |
| 12 | Otterize | 15.57/15.86 | 15.41/16.00 | 15.56/15.12 | 14.99/15.23 | 0.98 |
| 12 | IG trace_tcp | 15.91/15.44 | 16.00/15.77 | 14.87/16.06 | 15.28/15.93 | 0.99 |
| 12 | IG snapshot_socket | 16.51/16.34 | 15.99/15.98 | 15.91/16.40 | 15.89/16.39 | 1.00 |
| 13 | baseline | 15.95/16.52 | 15.54/16.30 | 15.27/16.02 | 14.59/16.40 | 0.99 |
| 13 | Hubble | 16.04/14.87 | 15.99/14.92 | 16.07/14.59 | 16.16/14.85 | 0.96 |
| 13 | Otterize | 16.49/16.03 | 16.28/16.03 | 15.73/14.20 | 16.54/15.38 | 1.01 |
| 13 | IG trace_tcp | 15.98/16.31 | 16.03/16.03 | 15.50/14.86 | 15.99/15.33 | 1.00 |
| 13 | IG snapshot_socket | 16.27/16.40 | 16.21/16.44 | 16.00/16.85 | 16.38/16.79 | 1.02 |
| 14 | baseline | 15.10/15.65 | 14.95/15.41 | 14.91/15.11 | 15.11/15.83 | 0.95 |
| 14 | Hubble | 16.47/16.10 | 16.34/15.86 | 15.95/15.53 | 16.28/15.58 | 1.00 |
| 14 | Otterize | 16.38/16.57 | 16.18/16.42 | 16.06/16.73 | 16.12/15.95 | 1.02 |
| 14 | IG trace_tcp | 15.25/15.75 | 15.28/16.20 | 15.10/16.16 | 15.16/16.03 | 0.98 |
| 14 | IG snapshot_socket | 16.45/16.39 | 16.25/16.24 | 15.81/15.73 | 14.81/15.84 | 1.01 |
| 15 | baseline | 16.44/16.64 | 16.20/16.25 | 16.65/16.59 | 16.40/16.71 | 1.01 |
| 15 | Hubble | 16.58/16.03 | 16.32/15.86 | 16.08/15.70 | 14.38/15.69 | 1.00 |
| 15 | Otterize | 15.73/16.28 | 15.87/16.05 | 15.80/14.81 | 15.80/15.55 | 0.99 |
| 15 | IG trace_tcp | 16.04/15.96 | 16.06/16.24 | 16.32/15.99 | 15.58/15.73 | 1.01 |
| 15 | IG snapshot_socket | 15.75/16.30 | 15.67/16.13 | 15.87/16.34 | 15.75/15.75 | 0.99 |
| 16 | baseline | 16.52/16.44 | 15.96/16.16 | 16.57/16.69 | 16.31/16.72 | 1.00 |
| 16 | Hubble | 16.55/16.48 | 16.29/16.39 | 16.03/16.07 | 16.00/15.99 | 1.02 |
| 16 | Otterize | 15.44/15.52 | 16.02/16.42 | 15.82/16.27 | 15.98/16.53 | 1.01 |
| 16 | IG trace_tcp | 16.29/15.98 | 16.26/16.15 | 16.19/15.42 | 14.79/14.54 | 1.01 |
| 16 | IG snapshot_socket | 16.58/16.14 | 16.33/16.21 | 15.65/16.38 | 16.34/15.67 | 1.01 |
| 17 | baseline | 15.91/16.02 | 15.83/15.76 | 14.53/15.78 | 15.05/15.94 | 0.98 |
| 17 | Hubble | 16.15/16.47 | 16.09/16.29 | 16.01/15.65 | 15.95/16.27 | 1.01 |
| 17 | Otterize | 16.02/16.12 | 16.18/16.32 | 16.22/15.93 | 15.36/16.22 | 1.01 |
| 17 | IG trace_tcp | 16.27/16.33 | 16.04/16.23 | 16.31/16.34 | 16.02/16.26 | 1.01 |
| 17 | IG snapshot_socket | 16.43/15.82 | 16.46/16.47 | 16.25/15.73 | 16.67/15.76 | 1.03 |
| 18 | baseline | 16.63/16.24 | 16.52/16.10 | 15.02/16.29 | 15.91/15.81 | 1.02 |
| 18 | Hubble | 16.22/16.69 | 16.27/16.31 | 16.20/16.10 | 15.72/16.17 | 1.01 |
| 18 | Otterize | 14.37/16.16 | 14.45/16.14 | 14.29/15.98 | 14.16/16.15 | 0.95 |
| 18 | IG trace_tcp | 16.46/16.78 | 16.35/16.29 | 16.20/14.68 | 15.96/14.81 | 1.02 |
| 18 | IG snapshot_socket | 16.32/16.74 | 15.73/16.30 | 15.62/15.76 | 16.16/15.15 | 1.00 |
| 19 | baseline | 16.06/15.96 | 15.97/15.78 | 15.23/15.65 | 15.18/15.79 | 0.99 |
| 19 | Hubble | 16.30/16.46 | 16.09/15.96 | 15.55/14.73 | 16.06/14.71 | 1.00 |
| 19 | Otterize | 16.39/16.50 | 15.97/16.25 | 15.83/16.05 | 15.97/15.85 | 1.00 |
| 19 | IG trace_tcp | 16.58/16.44 | 16.20/16.28 | 16.17/15.14 | 16.29/16.08 | 1.01 |
| 19 | IG snapshot_socket | 15.85/16.51 | 15.84/16.10 | 16.10/16.57 | 15.48/16.35 | 0.99 |
| 20 | baseline | 16.03/16.22 | 15.58/15.60 | 15.52/15.35 | 16.11/15.10 | 0.97 |
| 20 | Hubble | 15.57/15.84 | 15.88/15.89 | 16.08/15.01 | 15.89/14.42 | 0.99 |
| 20 | Otterize | 16.06/15.65 | 15.61/15.77 | 14.96/14.83 | 15.97/15.45 | 0.98 |
| 20 | IG trace_tcp | 15.62/15.87 | 15.49/16.03 | 15.78/15.49 | 15.99/14.35 | 0.98 |
| 20 | IG snapshot_socket | 15.96/15.54 | 15.86/15.49 | 15.85/15.15 | 14.76/15.57 | 0.98 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 13.64 ± 0.80 (n=10) | 16.15 ± 0.70 (n=10) | +18.63% [+13.45, +23.81] | <0.001 | <0.001 |
| keepalive | Otterize | 13.64 ± 0.80 (n=10) | 14.27 ± 0.69 (n=10) | +4.86% [-0.40, +10.12] (n.s.) (< 10.1% at 95%) | 0.066 | 0.133 |
| keepalive | IG trace_tcp | 13.64 ± 0.80 (n=10) | 15.01 ± 0.76 (n=10) | +10.39% [+4.27, +16.52] | 0.004 | 0.012 |
| keepalive | IG snapshot_socket | 13.64 ± 0.80 (n=10) | 14.15 ± 0.69 (n=10) | +3.96% [-1.18, +9.11] (n.s.) (< 9.1% at 95%) | 0.115 | 0.133 |
| newconn | Hubble | 14.33 ± 0.81 (n=10) | 16.67 ± 0.91 (n=10) | +16.66% [+9.70, +23.63] | <0.001 | 0.002 |
| newconn | Otterize | 14.33 ± 0.81 (n=10) | 14.71 ± 0.45 (n=10) | +2.97% [-2.38, +8.32] (n.s.) (< 8.3% at 95%) | 0.241 | 0.481 |
| newconn | IG trace_tcp | 14.33 ± 0.81 (n=10) | 15.43 ± 0.77 (n=10) | +8.02% [+1.60, +14.44] | 0.020 | 0.060 |
| newconn | IG snapshot_socket | 14.33 ± 0.81 (n=10) | 14.59 ± 0.63 (n=10) | +2.02% [-2.79, +6.84] (n.s.) (< 6.8% at 95%) | 0.366 | 0.481 |
