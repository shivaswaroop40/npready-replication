# dsb

Runs used: baseline 10, Hubble 10, Otterize 10, IG trace_tcp 10, IG snapshot_socket 10.

In the standard tables below (from the Table 5 on), 'rep' means one interleaved cycle: the cycle is the block of the paired comparison.

### Interleaved cycles: paired deltas, raw and canary-normalised

Every cycle ran each condition once (Williams-design order), so each technique is paired with the baseline of the same cycle, about an hour apart at most, and slow host drift cancels in the difference (randomized multiple interleaved trials, Abedi and Brecht, ICPE 2017). Δ = mean of the per-cycle differences (technique minus the same cycle's baseline) with its 95% CI (t, df = cycles - 1; t = 2.26 at 10 cycles); fixed-count rows give the overhead in % of the baseline time. Holm: adjusted across the techniques, separately for each endpoint and variant. Canary-normalised: each node's CPU x (its canary speed in that window / its median speed over this app's runs), fixed-count time x the workers' speed ratio during that test, so a run on a fast host is scaled up to the median host speed. Memory is not normalised. The last row is a check: the canary's own speed should not differ by condition (CI including 0); if it does, the observer's load slows the canary and the normalised Δ understates the overhead.

| Endpoint | Technique | raw Δ [95% CI] | p | Holm p | normalised Δ [95% CI] | p | Holm p | cycles |
|---|---|---|---|---|---|---|---|---|
| Δ cluster busy CPU (cores) | Hubble | +0.298 [+0.219, +0.376] | <0.001 | <0.001 | +0.370 [+0.258, +0.483] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | Otterize | +0.087 [+0.051, +0.123] | <0.001 | <0.001 | +0.129 [+0.023, +0.235] | 0.023 | 0.046 | 10 |
| Δ cluster busy CPU (cores) | IG trace_tcp | +0.201 [+0.143, +0.260] | <0.001 | <0.001 | +0.346 [+0.222, +0.470] | <0.001 | <0.001 | 10 |
| Δ cluster busy CPU (cores) | IG snapshot_socket | +0.094 [+0.073, +0.115] | <0.001 | <0.001 | +0.091 [-0.016, +0.199] (n.s.) | 0.087 | 0.087 | 10 |
| Δ observer CPU (cores) | Hubble | +0.225 [+0.175, +0.276] | <0.001 | <0.001 | +0.255 [+0.209, +0.302] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | Otterize | +0.088 [+0.081, +0.095] | <0.001 | <0.001 | +0.099 [+0.076, +0.122] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG trace_tcp | +0.122 [+0.104, +0.139] | <0.001 | <0.001 | +0.162 [+0.128, +0.195] | <0.001 | <0.001 | 10 |
| Δ observer CPU (cores) | IG snapshot_socket | +0.061 [+0.055, +0.066] | <0.001 | <0.001 | +0.060 [+0.039, +0.081] | <0.001 | <0.001 | 10 |
| Δ app CPU (cores) | Hubble | +0.004 [-0.009, +0.016] (n.s.) | 0.504 | 1.000 | +0.009 [-0.035, +0.054] (n.s.) | 0.647 | 1.000 | 10 |
| Δ app CPU (cores) | Otterize | -0.002 [-0.016, +0.012] (n.s.) | 0.762 | 1.000 | +0.006 [-0.032, +0.044] (n.s.) | 0.737 | 1.000 | 10 |
| Δ app CPU (cores) | IG trace_tcp | -0.006 [-0.018, +0.007] (n.s.) | 0.341 | 1.000 | +0.034 [-0.016, +0.084] (n.s.) | 0.161 | 0.645 | 10 |
| Δ app CPU (cores) | IG snapshot_socket | -0.006 [-0.016, +0.004] (n.s.) | 0.221 | 0.885 | -0.001 [-0.039, +0.036] (n.s.) | 0.941 | 1.000 | 10 |
| Δ k3s/containerd CPU (cores) | Hubble | +0.099 [+0.080, +0.118] | <0.001 | <0.001 | +0.132 [+0.088, +0.177] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | Otterize | +0.004 [-0.013, +0.021] (n.s.) | 0.623 | 0.623 | +0.020 [-0.022, +0.061] (n.s.) | 0.308 | 0.463 | 10 |
| Δ k3s/containerd CPU (cores) | IG trace_tcp | +0.112 [+0.080, +0.144] | <0.001 | <0.001 | +0.169 [+0.121, +0.218] | <0.001 | <0.001 | 10 |
| Δ k3s/containerd CPU (cores) | IG snapshot_socket | +0.030 [+0.018, +0.042] | <0.001 | <0.001 | +0.022 [-0.017, +0.062] (n.s.) | 0.232 | 0.463 | 10 |
| Δ observer anon memory (MiB, primary) | Hubble | +108 [+103, +113] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | Otterize | +81 [+79, +83] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG trace_tcp | +150 [+148, +152] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer anon memory (MiB, primary) | IG snapshot_socket | +117 [+113, +121] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Hubble | +125 [+109, +141] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | Otterize | +97 [+69, +124] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG trace_tcp | +189 [+144, +233] | <0.001 | <0.001 | - | - | - | 10 |
| Δ observer memory, working set (MiB) | IG snapshot_socket | +126 [+121, +131] | <0.001 | <0.001 | - | - | - | 10 |
| fixed-count time, keep-alive | Hubble | +10.2% [-6.2, +26.6] (n.s.) | 0.192 | 0.770 | +17.7% [-4.3, +39.8] (n.s.) | 0.102 | 0.306 | 10 |
| fixed-count time, keep-alive | Otterize | +1.4% [-16.1, +19.0] (n.s.) | 0.857 | 1.000 | +4.8% [-14.1, +23.8] (n.s.) | 0.578 | 1.000 | 10 |
| fixed-count time, keep-alive | IG trace_tcp | -3.8% [-12.0, +4.5] (n.s.) | 0.325 | 0.976 | +20.1% [-1.2, +41.5] (n.s.) | 0.061 | 0.245 | 10 |
| fixed-count time, keep-alive | IG snapshot_socket | -3.1% [-14.1, +7.9] (n.s.) | 0.537 | 1.000 | +0.9% [-16.5, +18.2] (n.s.) | 0.914 | 1.000 | 10 |
| fixed-count time, new conn | Hubble | +5.1% [-7.9, +18.1] (n.s.) | 0.400 | 1.000 | +27.0% [-4.4, +58.3] (n.s.) | 0.084 | 0.284 | 10 |
| fixed-count time, new conn | Otterize | -1.4% [-12.4, +9.5] (n.s.) | 0.777 | 1.000 | +4.5% [-16.3, +25.4] (n.s.) | 0.634 | 1.000 | 10 |
| fixed-count time, new conn | IG trace_tcp | -6.7% [-21.1, +7.7] (n.s.) | 0.321 | 1.000 | +22.2% [-2.3, +46.8] (n.s.) | 0.071 | 0.284 | 10 |
| fixed-count time, new conn | IG snapshot_socket | -5.5% [-17.3, +6.3] (n.s.) | 0.316 | 1.000 | +1.6% [-13.3, +16.5] (n.s.) | 0.811 | 1.000 | 10 |
| canary speed, workers, steady window (check) | Hubble | +4.63% [-17.22, +26.48] (n.s.) | 0.643 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | Otterize | +6.10% [-11.60, +23.79] (n.s.) | 0.456 | 1.000 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG trace_tcp | +23.82% [-2.97, +50.61] (n.s.) | 0.075 | 0.301 | - | - | - | 10 |
| canary speed, workers, steady window (check) | IG snapshot_socket | +5.29% [-13.78, +24.36] (n.s.) | 0.546 | 1.000 | - | - | - | 10 |

### Drift diagnostic (per cycle)

The baseline run of each block: fixed-count time (s) raw and canary-normalised, app CPU in the steady window (cores) raw and normalised, the workers' canary speed in that window (million iterations per CPU-second) and its ratio to the app's median, and the mean canary speed over all runs of the cycle. If the host drifts, the raw baseline times move with 1/speed and the normalised ones stay flat. keep-alive: CV of the baseline time across cycles 14.1% raw, 26.1% normalised; correlation of the raw time with 1/canary speed during the tests r = 0.27; new conn: CV of the baseline time across cycles 13.8% raw, 27.3% normalised; correlation of the raw time with 1/canary speed during the tests r = -0.03.

| Cycle | start (UTC) | order | keep-alive s | norm. | new conn s | norm. | app CPU | norm. | canary speed | ratio | cycle mean speed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10-03 18:41 | otterize ig_tcp hubble ig_snap baseline | 45.1 | 42.6 | 45.8 | 44.2 | 0.166 | 0.168 | 7.32 | 1.01 | 7.94 |
| 2 | 10-03 19:41 | baseline ig_snap hubble ig_tcp otterize | 42.7 | 46.2 | 41.7 | 37.7 | 0.150 | 0.147 | 7.32 | 1.01 | 7.43 |
| 3 | 10-03 20:40 | ig_tcp ig_snap otterize baseline hubble | 57.1 | 54.0 | 61.3 | 56.7 | 0.197 | 0.187 | 6.78 | 0.94 | 8.54 |
| 4 | 10-03 21:42 | ig_tcp otterize ig_snap hubble baseline | 63.0 | 51.9 | 65.3 | 56.7 | 0.199 | 0.164 | 6.11 | 0.84 | 8.90 |
| 5 | 10-03 22:43 | ig_snap ig_tcp baseline otterize hubble | 44.0 | 59.6 | 47.8 | 59.0 | 0.181 | 0.191 | 8.75 | 1.22 | 7.68 |
| 6 | 10-03 23:44 | hubble baseline otterize ig_snap ig_tcp | 43.1 | 47.6 | 52.4 | 59.6 | 0.182 | 0.176 | 7.95 | 1.08 | 7.78 |
| 7 | 10-04 00:44 | ig_snap baseline ig_tcp hubble otterize | 50.7 | 52.3 | 54.6 | 55.5 | 0.172 | 0.171 | 7.52 | 1.03 | 8.60 |
| 8 | 10-04 01:45 | hubble otterize baseline ig_tcp ig_snap | 52.5 | 49.9 | 56.7 | 51.8 | 0.175 | 0.163 | 6.60 | 0.91 | 8.06 |
| 9 | 10-04 02:46 | baseline hubble ig_snap otterize ig_tcp | 56.7 | 90.9 | 60.8 | 96.5 | 0.189 | 0.292 | 12.04 | 1.65 | 7.90 |
| 10 | 10-04 03:47 | otterize hubble ig_tcp baseline ig_snap | 46.2 | 42.6 | 52.4 | 51.1 | 0.175 | 0.152 | 6.61 | 0.91 | 7.29 |

### Sensitivity: median and without each block's first run (pre-declared)

Declared on 2026-10-04 before the last blocks finished (FIXLOG). Primary = mean of the per-cycle paired differences with its 95% CI and Holm p. Median = median of the same differences, with a Wilcoxon signed-rank p (exact without ties). Without first run = the primary analysis with the first run of each block left out (cycle 1 Otterize; that cycle loses only that condition's pair). 'robust' = significant after Holm and in both checks; 'fragile' = significant after Holm but not in both checks.

| Endpoint | Technique | Primary Δ [95% CI] | Holm p | Median Δ | Wilcoxon p | Without first run Δ [95% CI] | pairs | Verdict |
|---|---|---|---|---|---|---|---|---|
| Δ observer CPU | Hubble | +0.225 [+0.175, +0.276] | <0.001 | +0.222 | 0.002 | +0.225 [+0.175, +0.276] | 10 | robust |
| Δ observer CPU | Otterize | +0.088 [+0.081, +0.095] | <0.001 | +0.090 | 0.002 | +0.090 [+0.083, +0.097] | 9 | robust |
| Δ observer CPU | IG trace_tcp | +0.122 [+0.104, +0.139] | <0.001 | +0.112 | 0.002 | +0.122 [+0.104, +0.139] | 10 | robust |
| Δ observer CPU | IG snapshot_socket | +0.061 [+0.055, +0.066] | <0.001 | +0.061 | 0.002 | +0.061 [+0.055, +0.066] | 10 | robust |
| Δ observer anon memory | Hubble | +108 [+103, +113] | <0.001 | +108 | 0.002 | +108 [+103, +113] | 10 | robust |
| Δ observer anon memory | Otterize | +81 [+79, +83] | <0.001 | +80 | 0.002 | +81 [+78, +83] | 9 | robust |
| Δ observer anon memory | IG trace_tcp | +150 [+148, +152] | <0.001 | +149 | 0.002 | +150 [+148, +152] | 10 | robust |
| Δ observer anon memory | IG snapshot_socket | +117 [+113, +121] | <0.001 | +117 | 0.002 | +117 [+113, +121] | 10 | robust |
| fixed-count time, keep-alive | Hubble | +10.2% [-6.2, +26.6] (n.s.) | 1.000 | +8.5% | 0.193 | +10.2% [-6.2, +26.6] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | Otterize | +1.4% [-16.1, +19.0] (n.s.) | 1.000 | +1.3% | 0.695 | +7.4% [-5.6, +20.3] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, keep-alive | IG trace_tcp | -3.8% [-12.0, +4.5] (n.s.) | 1.000 | -3.9% | 0.275 | -3.8% [-12.0, +4.5] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, keep-alive | IG snapshot_socket | -3.1% [-14.1, +7.9] (n.s.) | 1.000 | -3.1% | 0.846 | -3.1% [-14.1, +7.9] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | Hubble | +5.1% [-7.9, +18.1] (n.s.) | 1.000 | +2.2% | 0.432 | +5.1% [-7.9, +18.1] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | Otterize | -1.4% [-12.4, +9.5] (n.s.) | 1.000 | -5.2% | 0.492 | -0.1% [-12.1, +11.9] (n.s.) | 9 | n.s. (primary) |
| fixed-count time, new conn | IG trace_tcp | -6.7% [-21.1, +7.7] (n.s.) | 1.000 | -4.9% | 0.275 | -6.7% [-21.1, +7.7] (n.s.) | 10 | n.s. (primary) |
| fixed-count time, new conn | IG snapshot_socket | -5.5% [-17.3, +6.3] (n.s.) | 1.000 | -5.2% | 0.232 | -5.5% [-17.3, +6.3] (n.s.) | 10 | n.s. (primary) |

### Fixed-count time (GoLeash Table 5 format)

Time to finish 1504 requests at concurrency 16. w/o and with: mean ± SD over all executions (n = runs x repeats), as GoLeash reports its 10 executions. Overhead: mean of the per-rep paired overheads with its 95% CI (t, df = reps - 1); n.s. = the CI includes 0, and the upper CI bound is then the most the overhead can be. p: paired t-test; Holm: adjusted over this app's primary endpoints. Bottleneck: the app container with the most CFS throttling during the tests (s/s); this app is **quota-bound** (baseline newconn bottleneck throttled 1.99 s/s), so the test measures how fast throttled app cgroups drain their quota; it sees observer cost only where it is charged to those cgroups. conn/req: background-corrected new connections accepted per request.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p | bottleneck (thr s/s) | conn/req |
|---|---|---|---|---|---|---|---|---|
| keepalive | Hubble | 50.10 ± 7.05 (n=10) | 53.95 ± 6.07 (n=10) | +10.21% [-6.18, +26.60] (n.s.) (< 26.6% at 95%) | 0.192 | 1.000 | nginx-thrift 1.96 | 1.05 |
| keepalive | Otterize | 50.10 ± 7.05 (n=10) | 50.23 ± 10.45 (n=10) | +1.45% [-16.15, +19.04] (n.s.) (< 19.0% at 95%) | 0.857 | 1.000 | nginx-thrift 2.18 | 1.08 |
| keepalive | IG trace_tcp | 50.10 ± 7.05 (n=10) | 47.78 ± 5.41 (n=10) | -3.79% [-12.05, +4.46] (n.s.) (< 4.5% at 95%) | 0.325 | 1.000 | nginx-thrift 2.43 | 1.05 |
| keepalive | IG snapshot_socket | 50.10 ± 7.05 (n=10) | 47.74 ± 4.29 (n=10) | -3.11% [-14.08, +7.86] (n.s.) (< 7.9% at 95%) | 0.537 | 1.000 | nginx-thrift 2.58 | 1.05 |
| newconn | Hubble | 53.86 ± 7.42 (n=10) | 55.60 ± 5.90 (n=10) | +5.07% [-7.91, +18.06] (n.s.) (< 18.1% at 95%) | 0.400 | 1.000 | nginx-thrift 2.12 | 2.07 |
| newconn | Otterize | 53.86 ± 7.42 (n=10) | 52.35 ± 4.95 (n=10) | -1.41% [-12.36, +9.54] (n.s.) (< 9.5% at 95%) | 0.777 | 1.000 | nginx-thrift 2.31 | 2.11 |
| newconn | IG trace_tcp | 53.86 ± 7.42 (n=10) | 49.64 ± 9.43 (n=10) | -6.70% [-21.14, +7.74] (n.s.) (< 7.7% at 95%) | 0.321 | 1.000 | nginx-thrift 2.36 | 2.07 |
| newconn | IG snapshot_socket | 53.86 ± 7.42 (n=10) | 50.02 ± 6.14 (n=10) | -5.52% [-17.30, +6.25] (n.s.) (< 6.3% at 95%) | 0.316 | 1.000 | nginx-thrift 2.24 | 2.07 |

A/A noise floor (baseline only): the SD of the baseline run means is the run-to-run noise any overhead has to beat; the SD over executions includes the within-run repeats.

| Mode | baseline run means (s) | CV of run means | CV over executions | runs |
|---|---|---|---|---|
| keepalive | 50.10 ± 7.05 | 14.07% | 14.07% | 10 |
| newconn | 53.86 ± 7.42 | 13.78% | 13.78% | 10 |

### CPU (cores, steady window)

Observer = capture components plus their clients. Cluster busy = busy CPU of all 10 vCPUs. Two SDs: '±' is the SD of the window means over reps (reproducibility); 'SD in window' is the mean over reps of the SD of the 5-s values inside the window (burstiness). Δ = paired per-rep difference [95% CI]. Δ k3s is the kubelet/containerd/API-server change, which observer cgroups do not show. The transferable numbers are Δ cores and Δ % of capacity; '% of the bench baseline' is in overhead_cpu.csv only, because this cluster's baseline lacks the test-cluster platform load and that ratio would overstate the overhead several times.

| Technique | Observer | SD in window | Δ observer | Cluster busy | SD in window | Δ cluster | Δ % of capacity | Δ k3s | p / Holm p (Δ observer, primary) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 0.096 ± 0.009 | 0.009 | - | 0.588 ± 0.039 | 0.042 | - | - | - | - |
| Hubble | 0.321 ± 0.074 | 0.021 | +0.225 [+0.175, +0.276] | 0.886 ± 0.124 | 0.049 | +0.298 [+0.219, +0.376] | +2.98% | +0.099 | <0.001 / <0.001 |
| Otterize | 0.184 ± 0.011 | 0.014 | +0.088 [+0.081, +0.095] | 0.675 ± 0.034 | 0.049 | +0.087 [+0.051, +0.123] | +0.87% | +0.004 | <0.001 / <0.001 |
| IG trace_tcp | 0.218 ± 0.019 | 0.015 | +0.122 [+0.104, +0.139] | 0.790 ± 0.062 | 0.063 | +0.201 [+0.143, +0.260] | +2.01% | +0.112 | <0.001 / <0.001 |
| IG snapshot_socket | 0.157 ± 0.006 | 0.010 | +0.061 [+0.055, +0.066] | 0.682 ± 0.035 | 0.041 | +0.094 [+0.073, +0.115] | +0.94% | +0.030 | <0.001 / <0.001 |

### Standing cost (idle segment: observer on, app up, no load)

Paired Δ vs baseline over the idle segment before the warm-up. 'Share' = idle Δ observer / steady Δ observer: the part of the steady cost that does not depend on traffic.

| Technique | Δ observer | Δ k3s | Δ node busy | Share |
|---|---|---|---|---|
| Hubble | +0.011 [+0.007, +0.015] | +0.006 [-0.004, +0.017] (n.s.) | +0.007 [-0.015, +0.029] (n.s.) | 5% |
| Otterize | +0.069 [+0.063, +0.074] | +0.002 [-0.011, +0.016] (n.s.) | +0.076 [+0.041, +0.110] | 78% |
| IG trace_tcp | +0.067 [+0.059, +0.074] | +0.038 [+0.023, +0.054] | +0.095 [+0.059, +0.131] | 55% |
| IG snapshot_socket | +0.059 [+0.055, +0.064] | +0.028 [+0.013, +0.043] | +0.088 [+0.056, +0.120] | 98% |

### CPU during the fixed-count tests (cores)

Mean over the test windows of each run; Δ = paired per-rep difference [95% CI]. App throttled = CFS throttled time of all app containers, s/s (baseline → technique). cp-01 busy = generator node, % of its 2 vCPUs.

| Mode | Technique | Δ observer | Δ node busy | Δ k3s | App throttled s/s | cp-01 busy |
|---|---|---|---|---|---|---|
| keepalive | Hubble | +0.199 [+0.158, +0.240] | +0.246 [+0.171, +0.322] | +0.080 [+0.067, +0.093] | 2.48 → 1.99 | 14% |
| keepalive | Otterize | +0.080 [+0.071, +0.090] | +0.068 [+0.032, +0.105] | -0.001 [-0.018, +0.016] (n.s.) | 2.48 → 2.20 | 9% |
| keepalive | IG trace_tcp | +0.112 [+0.099, +0.125] | +0.191 [+0.149, +0.233] | +0.097 [+0.077, +0.117] | 2.48 → 2.46 | 12% |
| keepalive | IG snapshot_socket | +0.059 [+0.055, +0.063] | +0.116 [+0.079, +0.152] | +0.029 [+0.019, +0.038] | 2.48 → 2.61 | 11% |
| newconn | Hubble | +0.378 [+0.341, +0.415] | +0.496 [+0.402, +0.590] | +0.125 [+0.109, +0.141] | 2.01 → 2.14 | 20% |
| newconn | Otterize | +0.090 [+0.086, +0.094] | +0.107 [+0.080, +0.134] | +0.006 [-0.006, +0.018] (n.s.) | 2.01 → 2.33 | 11% |
| newconn | IG trace_tcp | +0.154 [+0.138, +0.169] | +0.288 [+0.230, +0.345] | +0.136 [+0.102, +0.169] | 2.01 → 2.39 | 17% |
| newconn | IG snapshot_socket | +0.058 [+0.053, +0.064] | +0.107 [+0.073, +0.142] | +0.026 [+0.011, +0.040] | 2.01 → 2.28 | 12% |

### Memory (MiB, steady window)

Observer working set = memory.current minus inactive_file (as the kubelet counts it); anon = anonymous memory only (no page cache). SD in window = SD of the 5-s values; slope = MiB per minute over the window (a stationarity check: a rising observer is not at steady state). Cluster used = MemTotal - MemAvailable; it is a different measure from component working sets, so do not compare the two columns.

| Technique | Observer WS | SD in window | slope MiB/min | anon | Δ observer anon (primary) | Δ observer WS | Cluster used | Δ obs anon % of memory | p / Holm p (Δ anon) |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 673 ± 18 | 4.2 | 0.85 | 377 | - | - | 3836 ± 27 | - | - |
| Hubble | 798 ± 30 (peak 812) | 9.6 | 6.55 | 485 | +108 [+103, +113] | +125 [+109, +141] | 3951 ± 31 | +0.67% | <0.001 / <0.001 |
| Otterize | 770 ± 50 (peak 777) | 4.1 | 0.75 | 458 | +81 [+79, +83] | +97 [+69, +124] | 3949 ± 37 | +0.50% | <0.001 / <0.001 |
| IG trace_tcp | 862 ± 72 (peak 876) | 7.2 | -3.00 | 527 | +150 [+148, +152] | +189 [+144, +233] | 4069 ± 32 | +0.94% | <0.001 / <0.001 |
| IG snapshot_socket | 799 ± 17 (peak 845) | 15.8 | 2.38 | 495 | +117 [+113, +121] | +126 [+121, +131] | 4019 ± 28 | +0.73% | <0.001 / <0.001 |

### Where the CPU goes (cores, steady window, mean over runs)

| Component | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|
| cilium-agent | 0.083 | 0.177 | 0.082 | 0.080 | 0.080 |
| cilium-envoy | 0.009 | 0.009 | 0.009 | 0.008 | 0.008 |
| cilium-operator | 0.004 | 0.004 | 0.004 | 0.004 | 0.004 |
| hubble-relay | 0.000 | 0.055 | 0.000 | 0.000 | 0.000 |
| otterize-mapper | 0.000 | 0.000 | 0.004 | 0.000 | 0.000 |
| otterize-sniffer | 0.000 | 0.000 | 0.086 | 0.000 | 0.000 |
| gadget | 0.000 | 0.000 | 0.000 | 0.103 | 0.064 |
| client-hubble | 0.000 | 0.076 | 0.000 | 0.000 | 0.000 |
| client-ig | 0.000 | 0.000 | 0.000 | 0.022 | 0.000 |
| app | 0.179 | 0.182 | 0.177 | 0.173 | 0.173 |
| loadgen | 0.006 | 0.006 | 0.006 | 0.006 | 0.006 |
| k3s | 0.227 | 0.326 | 0.230 | 0.340 | 0.257 |
| k8s-addons | 0.008 | 0.008 | 0.009 | 0.008 | 0.008 |
| os | 0.002 | 0.001 | 0.002 | 0.001 | 0.002 |
| harness | 0.039 | 0.037 | 0.037 | 0.035 | 0.039 |
| node | 0.588 | 0.886 | 0.675 | 0.790 | 0.682 |

### Steady window: generator throughput and latency (exploratory)

req/s is set by the generator (locust users and think time, or the wrk2 -R rate), so it is a controlled input, not an outcome; throughput claims come from the fixed-count table. Latency percentiles come from the generator's whole-Job summary; locust rounds times above 100 ms to two significant digits, so one bucket step is 5-10%.

| Technique | req/s | p50 (ms) | Δ p50 | p95 (ms) | Δ p95 | p99 (ms) | Δ p99 | fail % |
|---|---|---|---|---|---|---|---|---|
| baseline | 19.87 ± 0.21 | 272.1 ± 352.5 | - | 5186.1 ± 7839.5 | - | 8452.7 ± 12416.6 | - | 0.14 |
| Hubble | 19.92 ± 0.10 | 445.7 ± 804.1 | +359.9% [-94.6, +814.4] (n.s.) | 2330.4 ± 3276.7 | +178.7% [-69.9, +427.3] (n.s.) | 3285.9 ± 3993.3 | +133.0% [-59.3, +325.3] (n.s.) | 0.13 |
| Otterize | 19.97 ± 0.01 | 91.1 ± 57.6 | +113.8% [-199.4, +427.0] (n.s.) | 893.3 ± 430.9 | +38.3% [-89.1, +165.8] (n.s.) | 1712.0 ± 834.9 | +46.5% [-98.5, +191.5] (n.s.) | 0.13 |
| IG trace_tcp | 19.97 ± 0.01 | 72.6 ± 47.8 | +13.2% [-119.5, +145.9] (n.s.) | 864.1 ± 919.9 | -18.1% [-71.8, +35.6] (n.s.) | 1564.2 ± 1500.0 | -13.1% [-70.9, +44.7] (n.s.) | 0.13 |
| IG snapshot_socket | 19.98 ± 0.00 | 75.1 ± 51.8 | +24.9% [-117.3, +167.2] (n.s.) | 634.8 ± 274.6 | -14.0% [-76.7, +48.6] (n.s.) | 1185.4 ± 499.8 | -7.4% [-82.6, +67.9] (n.s.) | 0.13 |

### Cost per request and per new connection

flows/s: new TCP connections accepted by pods on the workers in the steady window (PassiveOpens over the pod network namespaces). bg/s: the same counter in the idle segment, with no load: kubelet probes and other background. app/s = flows - bg. Keep-alive load opens almost no connections, so a per-flow cost from the steady window would divide idle cost by the probe rate; the costs below come from the fixed-count tests instead: the observer CPU above its idle level during a test, per request (exact count) and per new connection (newconn tests, background-corrected), as the paired Δ vs baseline [95% CI], in CPU-µs. 1 CPU-µs per connection = 1 millicore per 1000 connections/s. node/conn uses all busy CPU (indirect costs included). events/s: the capture client's events with event time inside the analysis window, next to the thesis journey-A capture rate of the same app.

| Technique | flows/s | bg/s | app/s | Δ obs µs/req keep-alive | Δ obs µs/req newconn | Δ obs µs/conn | Δ node µs/conn | events/s |
|---|---|---|---|---|---|---|---|---|
| baseline | 19.1 | 0.00 | 19.05 | - | - | - | - | - |
| Hubble | 19.3 | 0.20 | 19.15 | +7065 [+5408, +8723] | +14175 [+12146, +16204] | +6835 [+5864, +7805] | +9244 [+7221, +11268] | 242.3 (thesis 354.0) |
| Otterize | 21.1 | 0.95 | 20.10 | +482 [+165, +800] | +766 [+515, +1017] | +362 [+243, +481] | +354 [-467, +1174] (n.s.) | - |
| IG trace_tcp | 19.1 | 0.00 | 19.15 | +1445 [+1226, +1664] | +3073 [+2407, +3740] | +1485 [+1163, +1806] | +2996 [+1587, +4405] | 76.6 (thesis 76.1) |
| IG snapshot_socket | 19.1 | 0.00 | 19.14 | -20 [-128, +88] (n.s.) | -45 [-175, +84] (n.s.) | -22 [-84, +41] (n.s.) | -48 [-1135, +1039] (n.s.) | - |

### Hubble: what the agents processed (steady window, all namespaces)

Flows processed/s by class, from hubble_flows_processed_total with identity context. client_feedback = traffic to and from hubble-relay (the capture client's own stream); probe = to or from reserved:host. cp-01 share of all flows: 6%. Lost events: 91 in the window, 205 over the whole run (fixed-count tests included). hubble_* series at the end: 292.

| Class | flows/s | share |
|---|---|---|
| app | 242.6 | 94% |
| probe | 0.3 | 0% |
| client_feedback | 2.7 | 1% |
| other | 11.4 | 4% |

### IG snapshot_socket: standing cost vs one snapshot

Δ observer over the whole window +0.061 [+0.055, +0.066] cores. Standing (window before the snapshot) minus baseline observer: +0.060 cores; one snapshot adds 0.24 ± 0.19 CPU-seconds (observer + k3s, above the standing rate). The window mean therefore depends on the window length; the two numbers above do not.


### test-cluster projection (estimate)

Observer only: the capture components' cost measured on the 3 bench nodes (they carry the whole app load, which test-cluster split over its nodes too), plus for each node test-cluster has in addition (2 control planes, 1 worker) that role's standing cost from the idle segment. Upper: the earlier method, every test-cluster node costs what the bench node of its role costs under load; it triples cp-01, which here also carries the generator and the capture clients. Observer + indirect: all busy CPU except the bench's clients, generator and harness (adds k3s/containerd/API-server work, kernel time and BPF work charged to the app), scaled the same way. Clients are left out: in the thesis they ran on the laptop. Platform background traffic (ns ankra, monitoring, sock-shop) is not in the bench, so these are app-attributable costs. Isolated per technique; test-cluster ran Hubble, IG trace_tcp and Otterize together, and assuming the costs add up, that configuration costs about +0.440 cores (observer only). Memory % uses about 57.0 GiB.

| Technique | Δ CPU observer | upper | Δ CPU obs + indirect | % of 18 vCPU (obs / all) | Δ memory (MiB) | % of 57.0 GiB |
|---|---|---|---|---|---|---|
| Hubble | +0.159 [+0.119, +0.199] | +0.206 | +0.228 [+0.157, +0.299] | +0.88% / +1.27% | +79 [+61, +96] | +0.13% |
| Otterize | +0.119 [+0.109, +0.129] | +0.130 | +0.119 [+0.058, +0.180] | +0.66% / +0.66% | +121 [+85, +158] | +0.21% |
| IG trace_tcp | +0.161 [+0.142, +0.180] | +0.178 | +0.271 [+0.201, +0.341] | +0.90% / +1.51% | +370 [+283, +458] | +0.63% |
| IG snapshot_socket | +0.117 [+0.107, +0.127] | +0.118 | +0.170 [+0.134, +0.205] | +0.65% / +0.94% | +274 [+262, +287] | +0.47% |

### Runs: order position, steal, host

| Rep | Technique | Position | Steal (mean of nodes) | Play | Boot ids | newconn time (s) |
|---|---|---|---|---|---|---|
| 1 | baseline | 5 | 0.03% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 45.78 |
| 2 | baseline | 1 | 0.13% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 41.70 |
| 3 | baseline | 4 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 61.25 |
| 4 | baseline | 5 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 65.29 |
| 5 | baseline | 3 | 0.14% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 47.78 |
| 6 | baseline | 2 | 0.17% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 52.39 |
| 7 | baseline | 2 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 54.55 |
| 8 | baseline | 3 | 0.03% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 56.67 |
| 9 | baseline | 1 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 60.77 |
| 10 | baseline | 4 | 0.21% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 52.41 |
| 1 | Hubble | 3 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 47.03 |
| 2 | Hubble | 3 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 54.96 |
| 3 | Hubble | 5 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 57.72 |
| 4 | Hubble | 4 | 0.20% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 48.52 |
| 5 | Hubble | 5 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 60.66 |
| 6 | Hubble | 1 | 0.07% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 63.12 |
| 7 | Hubble | 4 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 55.41 |
| 8 | Hubble | 1 | 0.07% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 64.39 |
| 9 | Hubble | 2 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 52.73 |
| 10 | Hubble | 2 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 51.50 |
| 1 | Otterize | 1 | 0.47% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 39.76 |
| 2 | Otterize | 5 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 55.62 |
| 3 | Otterize | 3 | 0.94% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 51.72 |
| 4 | Otterize | 2 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 55.25 |
| 5 | Otterize | 4 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 51.69 |
| 6 | Otterize | 3 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 55.29 |
| 7 | Otterize | 5 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 57.87 |
| 8 | Otterize | 2 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 52.55 |
| 9 | Otterize | 4 | 0.03% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 52.97 |
| 10 | Otterize | 1 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 50.78 |
| 1 | IG trace_tcp | 2 | 0.07% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 47.17 |
| 2 | IG trace_tcp | 4 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 51.62 |
| 3 | IG trace_tcp | 1 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 54.61 |
| 4 | IG trace_tcp | 1 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 56.67 |
| 5 | IG trace_tcp | 2 | 0.13% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 52.08 |
| 6 | IG trace_tcp | 5 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 49.60 |
| 7 | IG trace_tcp | 3 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 53.33 |
| 8 | IG trace_tcp | 4 | 0.03% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 54.09 |
| 9 | IG trace_tcp | 5 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 53.36 |
| 10 | IG trace_tcp | 3 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 23.88 |
| 1 | IG snapshot_socket | 4 | 0.13% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 45.51 |
| 2 | IG snapshot_socket | 2 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 46.10 |
| 3 | IG snapshot_socket | 2 | 0.08% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 54.78 |
| 4 | IG snapshot_socket | 3 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 38.37 |
| 5 | IG snapshot_socket | 1 | 0.05% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 58.38 |
| 6 | IG snapshot_socket | 4 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 49.73 |
| 7 | IG snapshot_socket | 1 | 0.06% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 46.49 |
| 8 | IG snapshot_socket | 5 | 0.04% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 53.61 |
| 9 | IG snapshot_socket | 3 | 0.03% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 57.08 |
| 10 | IG snapshot_socket | 5 | 0.31% | 6ac1484133e2d67d2b592f48 | 6ef7a7ed,80c1521f,e5ce0aa1 | 50.19 |

### Host-speed canary per segment

Million canary iterations per CPU-second, one value per worker (worker-01, worker-02), over the idle segment, the steady window and the fixed-count tests of each mode. Ratio: the workers' steady-window speed over the app's median. Every value per node and segment is in canary_segments.csv.

| Cycle | Technique | idle | steady | keep-alive tests | new conn tests | ratio |
|---|---|---|---|---|---|---|
| 1 | baseline | 7.25/7.86 | 7.74/6.90 | 7.20/6.52 | 7.42/6.62 | 1.01 |
| 1 | Hubble | 7.90/7.56 | 7.26/8.12 | 7.79/8.66 | 8.32/8.97 | 1.06 |
| 1 | Otterize | 9.15/6.84 | 10.22/8.04 | 11.93/10.62 | 9.46/7.75 | 1.25 |
| 1 | IG trace_tcp | 9.38/7.58 | 8.65/7.54 | 9.00/6.15 | 8.43/6.86 | 1.11 |
| 1 | IG snapshot_socket | 8.72/5.95 | 8.17/6.76 | 8.27/5.98 | 8.70/7.56 | 1.02 |
| 2 | baseline | 7.53/7.24 | 7.37/7.28 | 7.95/7.76 | 6.76/6.36 | 1.01 |
| 2 | Hubble | 6.92/10.35 | 6.51/9.93 | 7.37/11.26 | 7.99/12.11 | 1.15 |
| 2 | Otterize | 8.52/7.21 | 8.26/7.00 | 8.16/6.94 | 8.24/7.12 | 1.05 |
| 2 | IG trace_tcp | 8.34/6.93 | 7.45/6.88 | 8.03/6.56 | 7.67/7.15 | 0.99 |
| 2 | IG snapshot_socket | 7.92/7.46 | 7.14/6.43 | 7.81/6.82 | 8.06/6.88 | 0.93 |
| 3 | baseline | 6.87/6.90 | 6.88/6.68 | 6.71/6.99 | 6.93/6.52 | 0.94 |
| 3 | Hubble | 7.97/6.99 | 8.64/7.28 | 9.06/7.61 | 11.17/9.78 | 1.09 |
| 3 | Otterize | 7.30/7.91 | 7.46/9.55 | 6.55/8.12 | 6.94/8.75 | 1.18 |
| 3 | IG trace_tcp | 10.36/11.29 | 9.43/11.75 | 9.66/11.12 | 8.83/12.22 | 1.47 |
| 3 | IG snapshot_socket | 10.68/6.24 | 11.47/6.26 | 11.71/6.51 | 11.84/6.62 | 1.20 |
| 4 | baseline | 7.20/6.57 | 6.24/5.97 | 6.21/5.76 | 6.41/6.20 | 0.84 |
| 4 | Hubble | 11.17/6.77 | 12.47/6.71 | 11.89/8.37 | 12.69/7.00 | 1.30 |
| 4 | Otterize | 7.53/7.60 | 8.09/7.61 | 9.54/7.97 | 8.46/7.84 | 1.08 |
| 4 | IG trace_tcp | 12.41/10.32 | 12.37/12.29 | 11.35/12.89 | 12.37/12.72 | 1.70 |
| 4 | IG snapshot_socket | 8.91/8.81 | 9.43/7.84 | 9.25/6.87 | 10.62/8.77 | 1.18 |
| 5 | baseline | 6.98/9.83 | 7.22/10.28 | 7.64/11.81 | 7.93/9.88 | 1.22 |
| 5 | Hubble | 6.11/6.23 | 5.85/6.30 | 5.82/6.67 | 6.21/8.24 | 0.84 |
| 5 | Otterize | 7.10/7.02 | 7.20/6.46 | 7.40/6.15 | 6.30/6.71 | 0.94 |
| 5 | IG trace_tcp | 10.89/9.54 | 11.11/10.36 | 10.93/10.46 | 11.59/11.15 | 1.48 |
| 5 | IG snapshot_socket | 6.04/6.28 | 6.01/6.03 | 6.52/6.54 | 6.32/6.33 | 0.83 |
| 6 | baseline | 9.02/5.58 | 9.66/6.23 | 9.36/6.78 | 9.97/6.70 | 1.08 |
| 6 | Hubble | 6.79/6.16 | 5.62/6.18 | 5.65/6.56 | 6.01/7.06 | 0.82 |
| 6 | Otterize | 6.91/7.58 | 6.77/7.57 | 6.49/7.31 | 6.85/7.25 | 0.99 |
| 6 | IG trace_tcp | 10.14/7.67 | 10.64/7.67 | 11.14/8.78 | 10.83/8.67 | 1.25 |
| 6 | IG snapshot_socket | 11.22/7.22 | 10.83/6.60 | 10.30/6.96 | 11.27/6.80 | 1.19 |
| 7 | baseline | 8.49/7.76 | 8.43/6.61 | 8.23/6.82 | 8.09/6.72 | 1.03 |
| 7 | Hubble | 12.11/7.34 | 11.30/6.41 | 11.89/6.94 | 11.25/6.36 | 1.20 |
| 7 | Otterize | 11.96/7.22 | 11.60/7.05 | 11.33/6.92 | 12.66/7.23 | 1.27 |
| 7 | IG trace_tcp | 10.19/8.15 | 10.69/8.80 | 11.90/8.92 | 12.62/9.22 | 1.34 |
| 7 | IG snapshot_socket | 6.89/8.35 | 7.07/7.99 | 7.39/8.56 | 6.93/8.42 | 1.04 |
| 8 | baseline | 7.42/7.51 | 6.70/6.50 | 6.78/6.99 | 6.46/6.78 | 0.91 |
| 8 | Hubble | 11.36/7.25 | 10.72/6.36 | 11.48/7.13 | 13.77/8.19 | 1.16 |
| 8 | Otterize | 9.58/7.26 | 10.21/6.68 | 10.82/7.01 | 9.83/6.62 | 1.15 |
| 8 | IG trace_tcp | 10.69/6.78 | 10.49/6.87 | 11.23/7.63 | 10.67/7.65 | 1.18 |
| 8 | IG snapshot_socket | 7.14/10.13 | 6.67/9.40 | 6.99/10.22 | 6.81/9.63 | 1.12 |
| 9 | baseline | 13.86/10.04 | 14.01/10.07 | 13.02/10.36 | 13.29/9.90 | 1.65 |
| 9 | Hubble | 7.01/7.47 | 6.82/6.41 | 7.63/6.81 | 7.22/6.46 | 0.91 |
| 9 | Otterize | 8.15/6.62 | 7.32/6.38 | 7.42/7.06 | 7.92/6.21 | 0.94 |
| 9 | IG trace_tcp | 8.09/6.90 | 7.56/6.29 | 7.63/7.43 | 7.20/7.94 | 0.95 |
| 9 | IG snapshot_socket | 8.38/7.06 | 8.07/6.09 | 8.01/6.33 | 7.91/6.39 | 0.97 |
| 10 | baseline | 6.30/6.30 | 6.48/6.73 | 6.50/6.85 | 6.93/7.20 | 0.91 |
| 10 | Hubble | 8.15/7.71 | 7.39/6.98 | 7.64/7.09 | 9.29/8.23 | 0.99 |
| 10 | Otterize | 7.92/8.06 | 6.71/6.63 | 6.83/6.16 | 7.27/7.01 | 0.92 |
| 10 | IG trace_tcp | 7.32/8.25 | 7.21/8.02 | 9.37/9.26 | 10.88/12.30 | 1.05 |
| 10 | IG snapshot_socket | 8.03/9.64 | 7.46/9.32 | 7.45/9.20 | 7.34/8.83 | 1.16 |

### Fixed-count time, canary-normalised (Table 5 format)

As the Table 5 above, with every execution's time multiplied by the workers' canary speed ratio during that execution. Holm: across the techniques, per mode.

| Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | p | Holm p |
|---|---|---|---|---|---|---|
| keepalive | Hubble | 53.76 ± 14.06 (n=10) | 60.19 ± 10.14 (n=10) | +17.74% [-4.30, +39.77] (n.s.) (< 39.8% at 95%) | 0.102 | 0.306 |
| keepalive | Otterize | 53.76 ± 14.06 (n=10) | 54.07 ± 10.37 (n=10) | +4.84% [-14.12, +23.79] (n.s.) (< 23.8% at 95%) | 0.578 | 1.000 |
| keepalive | IG trace_tcp | 53.76 ± 14.06 (n=10) | 62.67 ± 14.95 (n=10) | +20.15% [-1.17, +41.46] (n.s.) (< 41.5% at 95%) | 0.061 | 0.245 |
| keepalive | IG snapshot_socket | 53.76 ± 14.06 (n=10) | 51.87 ± 8.19 (n=10) | +0.85% [-16.50, +18.20] (n.s.) (< 18.2% at 95%) | 0.914 | 1.000 |
| newconn | Hubble | 56.88 ± 15.53 (n=10) | 67.34 ± 14.12 (n=10) | +26.95% [-4.42, +58.32] (n.s.) (< 58.3% at 95%) | 0.084 | 0.284 |
| newconn | Otterize | 56.88 ± 15.53 (n=10) | 56.27 ± 9.32 (n=10) | +4.54% [-16.32, +25.41] (n.s.) (< 25.4% at 95%) | 0.634 | 1.000 |
| newconn | IG trace_tcp | 56.88 ± 15.53 (n=10) | 66.97 ± 18.17 (n=10) | +22.24% [-2.34, +46.81] (n.s.) (< 46.8% at 95%) | 0.071 | 0.284 |
| newconn | IG snapshot_socket | 56.88 ± 15.53 (n=10) | 55.30 ± 6.71 (n=10) | +1.63% [-13.29, +16.54] (n.s.) (< 16.5% at 95%) | 0.811 | 1.000 |
