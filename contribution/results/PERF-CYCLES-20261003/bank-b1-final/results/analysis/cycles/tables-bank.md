# bank

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.182 [+0.144, +0.220] | <0.001 | <0.001 | +0.186 [+0.147, +0.224] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.147 [+0.101, +0.192] | <0.001 | <0.001 | +0.149 [+0.106, +0.191] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.295 [+0.244, +0.345] | <0.001 | <0.001 | +0.315 [+0.261, +0.369] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.217 [+0.177, +0.258] | <0.001 | <0.001 | +0.223 [+0.182, +0.265] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Hubble | +0.134 [+0.129, +0.140] | <0.001 | <0.001 | +0.135 [+0.129, +0.142] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.141 [+0.139, +0.144] | <0.001 | <0.001 | +0.141 [+0.139, +0.144] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.231 [+0.227, +0.234] | <0.001 | <0.001 | +0.236 [+0.231, +0.240] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.210 [+0.206, +0.214] | <0.001 | <0.001 | +0.211 [+0.206, +0.216] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | -0.006 [-0.033, +0.021] (n.s.) | 0.621 | 1.000 | -0.006 [-0.031, +0.019] (n.s.) | 0.591 | 1.000 | 10 |
| Δ app CPU (cores) | Otterize | +0.002 [-0.028, +0.032] (n.s.) | 0.884 | 1.000 | +0.003 [-0.024, +0.031] (n.s.) | 0.796 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | -0.009 [-0.049, +0.032] (n.s.) | 0.629 | 1.000 | -0.003 [-0.044, +0.038] (n.s.) | 0.876 | 1.000 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | -0.029 [-0.059, +0.001] (n.s.) | 0.055 | 0.222 | -0.028 [-0.058, +0.003] (n.s.) | 0.069 | 0.276 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.072 [+0.068, +0.075] | <0.001 | <0.001 | +0.074 [+0.070, +0.078] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.012 [+0.010, +0.015] | <0.001 | <0.001 | +0.012 [+0.011, +0.014] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.097 [+0.093, +0.101] | <0.001 | <0.001 | +0.103 [+0.098, +0.109] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.057 [+0.054, +0.060] | <0.001 | <0.001 | +0.059 [+0.055, +0.064] | <0.001 | <0.001 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +105 [+103, +108] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +81 [+78, +83] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +145 [+140, +149] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +109 [+106, +112] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +124 [+107, +141] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +99 [+72, +126] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +187 [+141, +234] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +118 [+114, +122] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | +9.9% [+6.6, +13.2] | <0.001 | <0.001 | +13.7% [+9.4, +18.0] | <0.001 | <0.001 | 10 |
| fixed-count time, keep-alive | Otterize | +2.4% [-0.0, +4.9] (n.s.) | 0.052 | 0.052 | +3.8% [+1.2, +6.4] | 0.009 | 0.018 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | +6.5% [+4.3, +8.8] | <0.001 | <0.001 | +10.2% [+8.1, +12.3] | <0.001 | <0.001 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | +3.2% [+1.0, +5.5] | 0.011 | 0.021 | +2.6% [-0.3, +5.5] (n.s.) | 0.073 | 0.073 | 10 |
| fixed-count time, new conn | Hubble | +9.6% [+6.1, +13.1] | <0.001 | <0.001 | +13.9% [+9.1, +18.7] | <0.001 | <0.001 | 10 |
| fixed-count time, new conn | Otterize | +1.3% [-1.2, +3.8] (n.s.) | 0.266 | 0.533 | +3.9% [+1.7, +6.0] | 0.003 | 0.006 | 10 |
| fixed-count time, new conn | IG trace_tcp | +6.0% [+3.2, +8.7] | <0.001 | 0.003 | +11.7% [+9.2, +14.1] | <0.001 | <0.001 | 10 |
| fixed-count time, new conn | IG snapshot_socket | +0.9% [-1.0, +2.8] (n.s.) | 0.326 | 0.533 | +1.7% [-2.2, +5.6] (n.s.) | 0.356 | 0.356 | 10 |
| canary speed, workers, steady window (check) | Hubble | -0.15% [-1.49, +1.18] (n.s.) | 0.803 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | +0.16% [-1.22, +1.53] (n.s.) | 0.802 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | +1.39% [+0.13, +2.64] | 0.034 | 0.136 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | +0.01% [-1.36, +1.37] (n.s.) | 0.991 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 2.6% raw, 2.2% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.53; new conn: CV of the baseline time across cycles 2.5% raw, 2.6% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.46.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-03 16:16 | hubble otterize baseline ig_tcp ig_snap | 51.7 | 50.6 | 51.2 | 51.1 | 0.353 | 0.353 | 3.38 | 1.00 | 3.40 |
| 2 | 10-03 17:23 | hubble baseline otterize ig_snap ig_tcp | 49.8 | 48.5 | 51.2 | 48.9 | 0.323 | 0.326 | 3.38 | 1.00 | 3.40 |
| 3 | 10-03 18:31 | ig_tcp otterize ig_snap hubble baseline | 48.3 | 48.0 | 49.4 | 50.5 | 0.350 | 0.361 | 3.44 | 1.02 | 3.39 |
| 4 | 10-03 19:37 | ig_snap baseline ig_tcp hubble otterize | 49.9 | 48.3 | 52.4 | 51.6 | 0.369 | 0.369 | 3.35 | 0.99 | 3.35 |
| 5 | 10-03 20:45 | ig_tcp ig_snap otterize baseline hubble | 49.8 | 49.9 | 51.7 | 52.6 | 0.355 | 0.359 | 3.40 | 1.01 | 3.37 |
| 6 | 10-03 21:53 | otterize hubble ig_tcp baseline ig_snap | 51.0 | 48.9 | 51.9 | 49.7 | 0.414 | 0.402 | 3.29 | 0.98 | 3.37 |
| 7 | 10-03 23:00 | baseline hubble ig_snap otterize ig_tcp | 52.2 | 50.3 | 54.0 | 51.5 | 0.379 | 0.375 | 3.33 | 0.99 | 3.37 |
| 8 | 10-04 00:08 | otterize ig_tcp hubble ig_snap baseline | 49.4 | 49.6 | 51.2 | 49.2 | 0.346 | 0.342 | 3.35 | 0.99 | 3.36 |
| 9 | 10-04 01:16 | ig_snap ig_tcp baseline otterize hubble | 48.6 | 47.5 | 50.1 | 49.0 | 0.332 | 0.336 | 3.38 | 1.00 | 3.36 |
| 10 | 10-04 02:23 | baseline ig_snap hubble ig_tcp otterize | 49.0 | 48.0 | 50.6 | 49.2 | 0.360 | 0.355 | 3.33 | 0.99 | 3.36 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Hubble; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.134 [+0.129, +0.140] | <0.001 | +0.135 | 0.002 | +0.134 [+0.128, +0.140] | 9 | robust |
| Δ observer CPU | Otterize | +0.141 [+0.139, +0.144] | <0.001 | +0.141 | 0.002 | +0.141 [+0.139, +0.144] | 10 | robust |
| Δ observer CPU | IG trace_tcp | +0.231 [+0.227, +0.234] | <0.001 | +0.229 | 0.002 | +0.231 [+0.227, +0.234] | 10 | robust |
| Δ observer CPU | IG snapshot_socket | +0.210 [+0.206, +0.214] | <0.001 | +0.211 | 0.002 | +0.210 [+0.206, +0.214] | 10 | robust |
| Δ observer anon memory | Hubble | +105 [+103, +108] | <0.001 | +106 | 0.002 | +105 [+102, +108] | 9 | robust |
| Δ observer anon memory | Otterize | +81 [+78, +83] | <0.001 | +80 | 0.002 | +81 [+78, +83] | 10 | robust |
| Δ observer anon memory | IG trace_tcp | +145 [+140, +149] | <0.001 | +144 | 0.002 | +145 [+140, +149] | 10 | robust |
| Δ observer anon memory | IG snapshot_socket | +109 [+106, +112] | <0.001 | +108 | 0.002 | +109 [+106, +112] | 10 | robust |
| fixed-count time, keep-alive | Hubble | +9.9% [+6.6, +13.2] | <0.001 | +10.5% | 0.002 | +10.6% [+7.2, +13.9] | 9 | robust |
| fixed-count time, keep-alive | Otterize | +2.4% [-0.0, +4.9] (n.s.) | 0.155 | +1.6% | 0.037 | +2.4% [-0.0, +4.9] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | IG trace_tcp | +6.5% [+4.3, +8.8] | <0.001 | +6.2% | 0.002 | +6.5% [+4.3, +8.8] | 10 | robust |
| fixed-count time, keep-alive | IG snapshot_socket | +3.2% [+1.0, +5.5] | 0.042 | +4.3% | 0.027 | +3.2% [+1.0, +5.5] | 10 | robust |
| fixed-count time, new conn | Hubble | +9.6% [+6.1, +13.1] | <0.001 | +8.7% | 0.002 | +9.9% [+6.0, +13.7] | 9 | robust |
| fixed-count time, new conn | Otterize | +1.3% [-1.2, +3.8] (n.s.) | 0.533 | +0.8% | 0.275 | +1.3% [-1.2, +3.8] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | +6.0% [+3.2, +8.7] | 0.004 | +7.1% | 0.002 | +6.0% [+3.2, +8.7] | 10 | robust |
| fixed-count time, new conn | IG snapshot_socket | +0.9% [-1.0, +2.8] (n.s.) | 0.533 | +1.2% | 0.557 | +0.9% [-1.0, +2.8] (n.s.) | 10 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 608 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 1.08 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 49.98 ± 1.29 (n=10) | 54.89 ± 1.72 (n=10) | +9.89% [+6.58, +13.21] | <0.001 | <0.001 | frontend 0.99 | 3.03 |
| keepalive | Otterize | 49.98 ± 1.29 (n=10) | 51.19 ± 1.62 (n=10) | +2.45% [-0.02, +4.91] (n.s.) (< 4.9% at 95%) | 0.052 | 0.155 | frontend 1.01 | 3.13 |
| keepalive | IG trace_tcp | 49.98 ± 1.29 (n=10) | 53.23 ± 1.48 (n=10) | +6.54% [+4.33, +8.75] | <0.001 | <0.001 | frontend 1.04 | 3.03 |
| keepalive | IG snapshot_socket | 49.98 ± 1.29 (n=10) | 51.59 ± 1.86 (n=10) | +3.24% [+0.96, +5.52] | 0.011 | 0.042 | frontend 1.08 | 3.03 |
| newconn | Hubble | 51.37 ± 1.27 (n=10) | 56.26 ± 1.89 (n=10) | +9.60% [+6.15, +13.06] | <0.001 | <0.001 | frontend 0.93 | 4.00 |
| newconn | Otterize | 51.37 ± 1.27 (n=10) | 52.02 ± 1.59 (n=10) | +1.32% [-1.20, +3.83] (n.s.) (< 3.8% at 95%) | 0.266 | 0.533 | frontend 1.31 | 4.09 |
| newconn | IG trace_tcp | 51.37 ± 1.27 (n=10) | 54.43 ± 1.98 (n=10) | +5.99% [+3.23, +8.75] | <0.001 | 0.004 | frontend 1.08 | 4.00 |
| newconn | IG snapshot_socket | 51.37 ± 1.27 (n=10) | 51.82 ± 2.15 (n=10) | +0.88% [-1.03, +2.78] (n.s.) (< 2.8% at 95%) | 0.326 | 0.533 | frontend 0.84 | 4.00 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 49.98 ± 1.29 | 2.58% | 2.58% | 10 |
| newconn | 51.37 ± 1.27 | 2.48% | 2.48% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.095 ± 0.002 | 0.008 | - | 0.814 ± 0.034 | 0.237 | - | - | - | - |
| Hubble | 0.229 ± 0.008 | 0.024 | +0.134 [+0.129, +0.140] | 0.996 ± 0.041 | 0.242 | +0.182 [+0.144, +0.220] | +1.82% | +0.072 | <0.001 / <0.001 |
| Otterize | 0.236 ± 0.004 | 0.013 | +0.141 [+0.139, +0.144] | 0.961 ± 0.044 | 0.236 | +0.147 [+0.101, +0.192] | +1.47% | +0.012 | <0.001 / <0.001 |
| IG trace_tcp | 0.325 ± 0.004 | 0.014 | +0.231 [+0.227, +0.234] | 1.109 ± 0.064 | 0.238 | +0.295 [+0.244, +0.345] | +2.95% | +0.097 | <0.001 / <0.001 |
| IG snapshot_socket | 0.305 ± 0.005 | 0.019 | +0.210 [+0.206, +0.214] | 1.032 ± 0.053 | 0.229 | +0.217 [+0.177, +0.258] | +2.17% | +0.057 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.028 [+0.025, +0.030] | +0.006 [-0.002, +0.015] (n.s.) | +0.034 [+0.017, +0.051] | 21% |
| Otterize | +0.125 [+0.122, +0.127] | +0.023 [+0.015, +0.032] | +0.150 [+0.136, +0.164] | 88% |
| IG trace_tcp | +0.216 [+0.213, +0.220] | +0.065 [+0.058, +0.072] | +0.270 [+0.260, +0.279] | 94% |
| IG snapshot_socket | +0.209 [+0.206, +0.213] | +0.055 [+0.049, +0.061] | +0.257 [+0.240, +0.274] | 100% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.613 [+0.571, +0.655] | +0.824 [+0.745, +0.903] | +0.294 [+0.281, +0.306] | 1.25 → 1.07 | 32% |
| keepalive | Otterize | +0.192 [+0.187, +0.197] | +0.184 [+0.143, +0.226] | +0.009 [+0.004, +0.015] | 1.25 → 1.11 | 15% |
| keepalive | IG trace_tcp | +0.317 [+0.312, +0.322] | +0.511 [+0.464, +0.558] | +0.266 [+0.258, +0.274] | 1.25 → 1.11 | 23% |
| keepalive | IG snapshot_socket | +0.202 [+0.196, +0.207] | +0.232 [+0.207, +0.257] | +0.055 [+0.047, +0.062] | 1.25 → 1.14 | 18% |
| newconn | Hubble | +0.724 [+0.679, +0.768] | +0.954 [+0.897, +1.010] | +0.323 [+0.308, +0.338] | 1.17 → 0.98 | 36% |
| newconn | Otterize | +0.198 [+0.192, +0.204] | +0.165 [+0.125, +0.206] | +0.011 [+0.005, +0.016] | 1.17 → 1.38 | 15% |
| newconn | IG trace_tcp | +0.345 [+0.338, +0.351] | +0.573 [+0.543, +0.602] | +0.298 [+0.290, +0.307] | 1.17 → 1.16 | 26% |
| newconn | IG snapshot_socket | +0.202 [+0.197, +0.207] | +0.227 [+0.193, +0.260] | +0.054 [+0.049, +0.060] | 1.17 → 0.91 | 19% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 671 ± 18 | 2.7 | 1.40 | 370 | - | - | 3977 ± 48 | - | - |
| Hubble | 795 ± 36 (peak 813) | 13.8 | 9.93 | 475 | +105 [+103, +108] | +124 [+107, +141] | 4089 ± 54 | +0.66% | <0.001 / <0.001 |
| Otterize | 770 ± 46 (peak 775) | 3.4 | 2.16 | 450 | +81 [+78, +83] | +99 [+72, +126] | 4091 ± 49 | +0.50% | <0.001 / <0.001 |
| IG trace_tcp | 858 ± 72 (peak 871) | 6.5 | -3.13 | 515 | +145 [+140, +149] | +187 [+141, +234] | 4212 ± 43 | +0.91% | <0.001 / <0.001 |
| IG snapshot_socket | 789 ± 18 (peak 841) | 16.4 | 7.92 | 479 | +109 [+106, +112] | +118 [+114, +122] | 4157 ± 38 | +0.68% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.083 | 0.138 | 0.083 | 0.085 | 0.085 |
| cilium-envoy | 0.007 | 0.007 | 0.007 | 0.007 | 0.007 |
| cilium-operator | 0.005 | 0.005 | 0.005 | 0.005 | 0.005 |
| hubble-relay | 0.000 | 0.033 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.016 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.125 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.219 | 0.207 |
| client-hubble | 0.000 | 0.047 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.010 | 0.001 |
| app | 0.358 | 0.352 | 0.360 | 0.349 | 0.329 |
| loadgen | 0.010 | 0.012 | 0.010 | 0.011 | 0.010 |
| k3s | 0.188 | 0.258 | 0.199 | 0.285 | 0.245 |
| k8s-addons | 0.011 | 0.012 | 0.012 | 0.011 | 0.011 |
| os | 0.003 | 0.003 | 0.002 | 0.003 | 0.003 |
| harness | 0.079 | 0.079 | 0.080 | 0.078 | 0.079 |
| node | 0.814 | 0.996 | 0.961 | 1.109 | 1.032 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%. At under 5 req/s the window holds few requests; do not read the p95/p99 deltas.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 1.55 ± 0.03 | 26.7 ± 0.5 | - | 3690.0 ± 292.3 | - | 7200.0 ± 894.4 | - | 85.43 |
| Hubble | 1.56 ± 0.04 | 34.6 ± 1.9 | +29.7% [+23.9, +35.4] | 3710.0 ± 414.9 | +1.3% [-9.5, +12.1] (n.s.) | 6860.0 ± 730.6 | -3.2% [-15.9, +9.6] (n.s.) | 81.98 |
| Otterize | 1.56 ± 0.04 | 27.4 ± 0.8 | +2.6% [+0.1, +5.2] | 3740.0 ± 320.4 | +2.1% [-7.2, +11.4] (n.s.) | 6850.0 ± 966.4 | -3.2% [-17.8, +11.3] (n.s.) | 79.63 |
| IG trace_tcp | 1.57 ± 0.04 | 29.9 ± 1.3 | +12.0% [+9.0, +15.0] | 3810.0 ± 604.5 | +4.0% [-10.0, +18.0] (n.s.) | 7560.0 ± 943.0 | +7.0% [-9.5, +23.6] (n.s.) | 80.02 |
| IG snapshot_socket | 1.58 ± 0.06 | 27.2 ± 0.6 | +1.9% [-0.0, +3.8] (n.s.) | 3770.0 ± 715.0 | +2.0% [-9.3, +13.3] (n.s.) | 6820.0 ± 823.0 | -3.7% [-16.6, +9.2] (n.s.) | 80.28 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 7.0 | 1.67 | 5.34 | - | - | - | - | - |
| Hubble | 7.1 | 1.87 | 5.20 | +54782 [+50547, +59017] | +66820 [+62336, +71304] | +16702 [+15573, +17830] | +23457 [+21991, +24923] | 101.2 (thesis 101.3) |
| Otterize | 8.3 | 2.41 | 5.91 | +5934 [+5463, +6405] | +6578 [+6044, +7113] | +1608 [+1477, +1738] | +265 [-637, +1168] (n.s.) | - |
| IG trace_tcp | 6.8 | 1.65 | 5.16 | +9168 [+8706, +9631] | +12021 [+11394, +12649] | +3005 [+2848, +3162] | +8024 [+7216, +8832] | 24.8 (thesis 28.8) |
| IG snapshot_socket | 6.8 | 1.66 | 5.15 | -669 [-1128, -210] | -639 [-1046, -233] | -160 [-262, -58] | -486 [-1278, +307] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 25%. Lost events: 6 in the window, 115 over the whole run (fixed-count tests included). hubble_* series at the end: 256.

| Class | flows/s | share |
|---|---|---|
| app | 83.5 | 75% |
| probe | 13.7 | 12% |
| client_feedback | 2.7 | 2% |
| other | 11.6 | 10% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.210 [+0.206, +0.214] cores. Standing (window before the snapshot) minus baseline observer: +0.207 cores; one snapshot adds 1.13 ± 0.30 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.716 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.101 [+0.096, +0.107] | +0.135 | +0.149 [+0.098, +0.199] | +0.56% / +0.83% | +92 [+64, +120] | +0.16% |
| Otterize | +0.197 [+0.193, +0.201] | +0.204 | +0.218 [+0.165, +0.270] | +1.10% / +1.21% | +128 [+88, +168] | +0.22% |
| IG trace_tcp | +0.418 [+0.410, +0.425] | +0.421 | +0.528 [+0.483, +0.574] | +2.32% / +2.94% | +360 [+270, +449] | +0.62% |
| IG snapshot_socket | +0.404 [+0.397, +0.411] | +0.403 | +0.450 [+0.397, +0.504] | +2.24% / +2.50% | +257 [+245, +269] | +0.44% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 3 | 0.10% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.17 |
| 2 | baseline | 2 | 0.23% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.22 |
| 3 | baseline | 5 | 0.06% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 49.40 |
| 4 | baseline | 2 | 0.05% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 52.40 |
| 5 | baseline | 4 | 0.05% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.72 |
| 6 | baseline | 4 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.91 |
| 7 | baseline | 1 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 53.98 |
| 8 | baseline | 5 | 0.01% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.18 |
| 9 | baseline | 3 | 0.04% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 50.07 |
| 10 | baseline | 1 | 0.01% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 50.61 |
| 1 | Hubble | 1 | 0.60% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 54.93 |
| 2 | Hubble | 1 | 0.24% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 55.29 |
| 3 | Hubble | 4 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 56.03 |
| 4 | Hubble | 4 | 0.03% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 58.22 |
| 5 | Hubble | 5 | 0.33% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 54.50 |
| 6 | Hubble | 2 | 0.19% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 53.20 |
| 7 | Hubble | 2 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 56.95 |
| 8 | Hubble | 3 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 56.04 |
| 9 | Hubble | 5 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 58.40 |
| 10 | Hubble | 3 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 59.06 |
| 1 | Otterize | 2 | 0.72% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 53.85 |
| 2 | Otterize | 3 | 0.06% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 52.63 |
| 3 | Otterize | 2 | 0.23% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 49.86 |
| 4 | Otterize | 5 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.31 |
| 5 | Otterize | 3 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 54.10 |
| 6 | Otterize | 1 | 0.22% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 52.20 |
| 7 | Otterize | 4 | 0.04% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.50 |
| 8 | Otterize | 1 | 0.04% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 50.67 |
| 9 | Otterize | 4 | 0.04% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 50.10 |
| 10 | Otterize | 5 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 53.98 |
| 1 | IG trace_tcp | 4 | 0.03% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 54.58 |
| 2 | IG trace_tcp | 5 | 0.04% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 55.25 |
| 3 | IG trace_tcp | 1 | 0.04% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 55.00 |
| 4 | IG trace_tcp | 3 | 0.84% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 54.17 |
| 5 | IG trace_tcp | 1 | 0.18% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 56.79 |
| 6 | IG trace_tcp | 3 | 0.50% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 56.71 |
| 7 | IG trace_tcp | 5 | 0.04% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 55.02 |
| 8 | IG trace_tcp | 2 | 0.03% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 52.09 |
| 9 | IG trace_tcp | 2 | 0.14% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 50.22 |
| 10 | IG trace_tcp | 4 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 54.44 |
| 1 | IG snapshot_socket | 5 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 50.20 |
| 2 | IG snapshot_socket | 4 | 0.03% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 54.10 |
| 3 | IG snapshot_socket | 3 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 48.23 |
| 4 | IG snapshot_socket | 1 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 52.28 |
| 5 | IG snapshot_socket | 2 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 52.43 |
| 6 | IG snapshot_socket | 5 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 50.70 |
| 7 | IG snapshot_socket | 3 | 0.07% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 56.10 |
| 8 | IG snapshot_socket | 4 | 0.01% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.71 |
| 9 | IG snapshot_socket | 1 | 0.03% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.18 |
| 10 | IG snapshot_socket | 2 | 0.02% | 6ac12926fd87f1b081910fc2 | 12650c4b,cc74c6c0,262e16e3 | 51.32 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 3.27/3.34 | 3.39/3.37 | 3.26/3.35 | 3.38/3.36 | 1.00 |
| 1 | Hubble | 3.23/3.20 | 3.44/3.34 | 3.34/3.19 | 3.55/3.24 | 1.00 |
| 1 | Otterize | 3.40/3.29 | 3.42/3.37 | 3.34/3.22 | 3.32/3.44 | 1.01 |
| 1 | IG trace_tcp | 3.44/3.23 | 3.45/3.38 | 3.74/3.34 | 3.69/3.65 | 1.01 |
| 1 | IG snapshot_socket | 3.43/3.55 | 3.43/3.44 | 3.30/3.26 | 3.40/3.25 | 1.02 |
| 2 | baseline | 3.42/3.40 | 3.44/3.31 | 3.28/3.30 | 3.25/3.20 | 1.00 |
| 2 | Hubble | 3.33/3.33 | 3.49/3.40 | 3.43/3.38 | 3.47/3.34 | 1.02 |
| 2 | Otterize | 3.44/3.37 | 3.42/3.43 | 3.23/3.53 | 3.24/3.58 | 1.01 |
| 2 | IG trace_tcp | 3.29/3.30 | 3.42/3.27 | 3.59/3.24 | 3.63/3.27 | 0.99 |
| 2 | IG snapshot_socket | 3.40/3.43 | 3.38/3.41 | 3.36/3.27 | 3.46/3.27 | 1.00 |
| 3 | baseline | 3.50/3.34 | 3.53/3.35 | 3.50/3.20 | 3.59/3.31 | 1.02 |
| 3 | Hubble | 3.28/3.34 | 3.37/3.37 | 3.45/3.58 | 3.37/3.56 | 1.00 |
| 3 | Otterize | 3.42/3.38 | 3.37/3.45 | 3.47/3.33 | 3.56/3.36 | 1.01 |
| 3 | IG trace_tcp | 3.31/3.27 | 3.46/3.34 | 3.34/3.41 | 3.35/3.60 | 1.01 |
| 3 | IG snapshot_socket | 3.39/3.37 | 3.38/3.25 | 3.25/3.21 | 3.29/3.24 | 0.98 |
| 4 | baseline | 3.29/3.30 | 3.40/3.31 | 3.22/3.32 | 3.25/3.41 | 0.99 |
| 4 | Hubble | 3.22/3.39 | 3.34/3.28 | 3.37/3.46 | 3.39/3.29 | 0.98 |
| 4 | Otterize | 3.19/3.27 | 3.32/3.28 | 3.34/3.38 | 3.30/3.38 | 0.98 |
| 4 | IG trace_tcp | 3.24/3.38 | 3.39/3.47 | 3.31/3.54 | 3.23/3.59 | 1.02 |
| 4 | IG snapshot_socket | 3.33/3.25 | 3.39/3.32 | 3.26/3.17 | 3.28/3.34 | 0.99 |
| 5 | baseline | 3.40/3.32 | 3.43/3.37 | 3.38/3.38 | 3.45/3.42 | 1.01 |
| 5 | Hubble | 3.38/3.38 | 3.38/3.32 | 3.34/3.29 | 3.20/3.42 | 0.99 |
| 5 | Otterize | 3.28/3.32 | 3.36/3.25 | 3.15/3.46 | 3.21/3.45 | 0.98 |
| 5 | IG trace_tcp | 3.38/3.44 | 3.35/3.46 | 3.35/3.42 | 3.42/3.50 | 1.01 |
| 5 | IG snapshot_socket | 3.27/3.38 | 3.27/3.45 | 3.30/3.55 | 3.38/3.44 | 1.00 |
| 6 | baseline | 3.19/3.26 | 3.28/3.31 | 3.24/3.25 | 3.28/3.18 | 0.98 |
| 6 | Hubble | 3.35/3.47 | 3.44/3.41 | 3.80/3.38 | 4.08/3.43 | 1.01 |
| 6 | Otterize | 3.45/3.39 | 3.42/3.41 | 3.34/3.26 | 3.31/3.51 | 1.01 |
| 6 | IG trace_tcp | 3.31/3.28 | 3.41/3.28 | 3.25/3.31 | 3.49/3.36 | 0.99 |
| 6 | IG snapshot_socket | 3.29/3.26 | 3.41/3.32 | 3.22/3.23 | 3.32/3.22 | 1.00 |
| 7 | baseline | 3.28/3.33 | 3.36/3.31 | 3.24/3.27 | 3.21/3.23 | 0.99 |
| 7 | Hubble | 3.28/3.37 | 3.38/3.28 | 3.28/3.40 | 3.35/3.38 | 0.99 |
| 7 | Otterize | 3.29/3.29 | 3.31/3.35 | 3.31/3.36 | 3.56/3.39 | 0.99 |
| 7 | IG trace_tcp | 3.54/3.27 | 3.66/3.28 | 3.71/3.34 | 3.53/3.34 | 1.03 |
| 7 | IG snapshot_socket | 3.34/3.34 | 3.33/3.48 | 3.35/3.28 | 3.30/3.38 | 1.01 |
| 8 | baseline | 3.44/3.31 | 3.34/3.35 | 3.36/3.42 | 3.20/3.29 | 0.99 |
| 8 | Hubble | 3.29/3.43 | 3.25/3.38 | 3.33/3.61 | 3.27/3.58 | 0.98 |
| 8 | Otterize | 3.26/3.28 | 3.29/3.42 | 3.48/3.40 | 3.47/3.31 | 0.99 |
| 8 | IG trace_tcp | 3.28/3.36 | 3.39/3.38 | 3.30/3.46 | 3.54/3.62 | 1.00 |
| 8 | IG snapshot_socket | 3.28/3.33 | 3.39/3.38 | 3.25/3.35 | 3.28/3.58 | 1.00 |
| 9 | baseline | 3.46/3.26 | 3.34/3.42 | 3.33/3.26 | 3.31/3.29 | 1.00 |
| 9 | Hubble | 3.28/3.23 | 3.34/3.31 | 3.28/3.90 | 3.34/3.80 | 0.98 |
| 9 | Otterize | 3.36/3.30 | 3.41/3.28 | 3.38/3.26 | 3.47/3.38 | 0.99 |
| 9 | IG trace_tcp | 3.36/3.27 | 3.50/3.37 | 3.50/3.38 | 3.61/3.52 | 1.02 |
| 9 | IG snapshot_socket | 3.33/3.32 | 3.30/3.38 | 3.35/3.29 | 3.29/3.26 | 0.99 |
| 10 | baseline | 3.27/3.20 | 3.33/3.33 | 3.38/3.25 | 3.24/3.32 | 0.99 |
| 10 | Hubble | 3.20/3.35 | 3.26/3.40 | 3.22/3.42 | 3.15/3.50 | 0.99 |
| 10 | Otterize | 3.37/3.30 | 3.35/3.45 | 3.45/3.34 | 3.30/3.27 | 1.01 |
| 10 | IG trace_tcp | 3.42/3.45 | 3.45/3.47 | 3.41/3.52 | 3.30/3.47 | 1.02 |
| 10 | IG snapshot_socket | 3.27/3.18 | 3.33/3.22 | 3.24/3.26 | 3.39/3.24 | 0.97 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 48.96 ± 1.07 (n=10) | 55.63 ± 2.05 (n=10) | +13.72% [+9.41, +18.02] | <0.001 | <0.001 |
| keepalive | Otterize | 48.96 ± 1.07 (n=10) | 50.80 ± 1.54 (n=10) | +3.79% [+1.22, +6.37] | 0.009 | 0.018 |
| keepalive | IG trace_tcp | 48.96 ± 1.07 (n=10) | 53.96 ± 1.74 (n=10) | +10.22% [+8.09, +12.35] | <0.001 | <0.001 |
| keepalive | IG snapshot_socket | 48.96 ± 1.07 (n=10) | 50.25 ± 2.36 (n=10) | +2.62% [-0.30, +5.54] (n.s.) (< 5.5% at 95%) | 0.073 | 0.073 |
| newconn | Hubble | 50.31 ± 1.33 (n=10) | 57.24 ± 2.27 (n=10) | +13.89% [+9.09, +18.69] | <0.001 | <0.001 |
| newconn | Otterize | 50.31 ± 1.33 (n=10) | 52.23 ± 1.20 (n=10) | +3.86% [+1.67, +6.05] | 0.003 | 0.006 |
| newconn | IG trace_tcp | 50.31 ± 1.33 (n=10) | 56.17 ± 1.88 (n=10) | +11.66% [+9.21, +14.12] | <0.001 | <0.001 |
| newconn | IG snapshot_socket | 50.31 ± 1.33 (n=10) | 51.14 ± 2.64 (n=10) | +1.67% [-2.22, +5.57] (n.s.) (< 5.6% at 95%) | 0.356 | 0.356 |
