# Capture-cost study: every number the thesis quotes, with its provenance

Written 2026-10-06 for the thesis chapter `thesis/ch5b-capture-cost.tex` (Chapter 6, "The cost of
capture") and the places that refer to it (abstract, ch1, ch2, ch3, ch6, ch7, appendices). Every
number below is copied from an analysis output, not from raw run data. Where the thesis states a
number that no file states (a ratio, a range or a sum), it is marked **derived** and the arithmetic
is given.

Short names used below:

- `SUM` = `PERF-CYCLES-20261003/SUMMARY.md`
- `COMB` = `PERF-CYCLES-20261003/COMBINED/RESULTS-COMBINED.md`
- `T5` = `PERF-CYCLES-20261003/COMBINED/table5_combined.csv`
- `RES` = `PERF-CYCLES-20261003/COMBINED/resources_combined.csv`
- `BLK(<block>)` = `PERF-CYCLES-20261003/<block>-final/results/analysis/cycles/RESULTS-CYCLES.md`
- `AO` = `PERF-AGENTONLY-20261005/AGENT-ONLY-SUMMARY.md` (and `agent_only_summary.csv`)
- `FIX` = `../perf-benchmark/FIXLOG.md`
- `README` = `../perf-benchmark/README.md`
- `HAND` = `../perf-benchmark/HANDOVER.md`; `OPS` = `../perf-benchmark/ops/HANDOFF.md`
- `TJ` = `RESULTS-TWO-JOURNEY.md` (the generator study, unchanged)

Nothing here changes an existing result. The generator study (`RESULTS.md`, `TJ`) and the
capture-cost study ran on different clusters.

## 1. Set-up facts

| Quantity | Value | Source |
|---|---|---|
| Benchmark cluster | iximiuz Labs copy; k3s v1.36.3; Cilium 1.19.5; 1 control-plane VM of 2 vCPU, 2 worker VMs of 4 vCPU (6.5 GiB each); kernel 6.12 | `HAND` "What this is"; `README` "Differences from test-cluster"; `cluster/versions.lock` |
| Cilium configuration | 155 of 155 keys identical to the original cluster's saved configuration | `README` last line |
| IG versions | server v0.54.1, gadget images v0.55.1, as in the thesis captures | `README` deviation table; `FIX` representativeness row "IG gadget images" |
| Otterize | network-mapper chart 3.0.47 (v3.0.19) | `cluster/versions.lock` |
| Load in the steady window | the thesis journey-A load, generator users and rates identical to the thesis workloads; about 2 requests per second | `README` last line; `SUM` Limitations "No latency result" |
| Cycle | 60 s idle, 60 s warm-up, 300 s steady window, one fixed-count test per mode | `SUM` "What was measured"; `HAND` Design |
| Run length in cycle mode | 659 to 728 s for the five runs of one validation cycle; cycle 58.4 min | `FIX` "Validation on a real play", row "Cycle timing" |
| Analysis window | steady window minus its first 15 s and last 10 s; samples every 5 s | `BLK(bank-b2)` Setup; `README` Analysis |
| Fixed-count sizes (concurrency 16) | Boutique 3008, Bank 608, DSB 1504, OTel 7040, TeaStore 9152 | `COMB` "Fixed-count time" header |
| Fixed-count sizing rule | about 50 s per test at the app's measured rate, a multiple of 16 | `SUM` "What was measured" (608 to 9,152 requests, about 50 s); `ops/launch_block.sh` header |
| Blocks | 10 blocks, 2 per app, 10 cycles each, 50 runs each, 500 runs, no run lost | `SUM` Status; `COMB` Blocks table |
| Retried attempts per block | 1, 0, 0, 0, 2, 5, 13, 12, 1, 0 (boutique-b1 ... teastore-b2) | `COMB` Blocks table |
| Retried attempts, total | 34 | **derived**: sum of the row above |
| Williams design | 10 sequences (cyclic shifts of 0 1 4 2 3 and mirror images); every condition twice in every position and every ordered pair adjacent exactly twice per block of 10 | `README` "Interleaved short cycles", `FIX` host-drift table row 2 |
| Host types | A: Intel Xeon 1997 MHz, Spectre v2 mitigated in hardware (IBRS); B: AMD EPYC 2495 MHz, software (retpolines); C: AMD EPYC 4192 MHz, hardware (IBRS) | `COMB` Blocks table; `SUM` "Why not 3 long repetitions"; `FIX` "Update 2026-10-05" |
| Host per block | A: boutique-b1, dsb-b1, otel-b1, teastore-b1; B: boutique-b2, bank-b1; C: bank-b2, dsb-b2, otel-b2, teastore-b2 | `COMB` Blocks table |
| Statistics | mean of per-cycle paired differences, t-based 95% CI (df = cycles - 1 = 9); Holm per block over 4 methods x 4 primary endpoints | `COMB` header; `FIX` "Primary endpoints" (Holm family row) |
| Verdicts | robust = significant after Holm and in both sensitivity checks; fragile = Holm only; n.s. = not significant after Holm, upper 95% bound reported | `COMB` header |
| Fragile results | none | `COMB` last section |
| Primary endpoints and when they were fixed | Δ observer CPU, Δ observer anonymous memory, fixed-count time (keep-alive, new connection); decided 2026-10-03 ~09:30Z with 2-3 of 10 cycles of boutique-b1 and otel-b1 finished | `FIX` "Primary endpoints and % statistics" |
| Sensitivity checks and when they were fixed | median with Wilcoxon signed-rank; analysis without each block's first run; decided 2026-10-04 ~05:10Z with 4 of the 5 first blocks done; protocol unchanged | `FIX` "First run of a block" |

## 2. Why three long repetitions failed (drift evidence)

| Quantity | Value | Source |
|---|---|---|
| Same 10,000-request test, concurrency 16, full Boutique matrix | 141-154 s (baseline), 192-202 s (Hubble rep 1), 70-84 s (both IG snapshot_socket runs) | `README` "The problem"; `FIX` "Host drift" |
| Ratio slowest to fastest | 2.9 | **derived**: 202 / 70 = 2.89. `SUM` stated "up to 2.9 times". It divides a Hubble run by a `snapshot_socket` run, so it mixes conditions; the thesis keeps it only with that caveat and uses the within-condition ratio in the next row for host drift |
| Inside one IG trace_tcp run, nothing changed | new-connection tests 133.7, 119.9 and 77.9 s, started 22:47, 22:50 and 22:52Z | `README` "The problem" |
| False result with 3 long reps | IG snapshot_socket fixed-count time about -50% | `README`; `SUM` |
| Guest steal | 0.03 to 0.08% throughout | `README` "The problem" |
| Drift probe | 90 min, 36 tests of 2000 keep-alive requests in one condition: 15.8-41.1 s, CV 16.6% | `README` "Validation on a real play" |
| Drift within one condition, ratio slowest to fastest | 2.6 | **derived**: 41.1 / 15.8 = 2.60. This is the figure the abstract, Chapter 7 and `SUM` use for host drift ("by a factor of up to 2.6 within one condition over 90 minutes") |
| Canary failure | r(time, 1/speed) 0.41, R² 0.17; normalised CV 16.4% vs 16.6% raw | `README` "Validation on a real play"; `FIX` row "Does the canary track ..." |
| Drift shared between plays | 13 overlapping test pairs, r 0.76 (Spearman 0.80) | `README`; `FIX` row "Is the drift per play?" |
| Quantised test time | hey median latency at about 100, 200, 300 ms (CFS period levels) | `README`; `FIX` row "Why the fixed-count time jumps" |

## 3. Resource cost at the thesis load (steady window)

All 80 cells (10 blocks x 4 methods x 2 endpoints) are **robust**. Source: `COMB` "Resource cost at
the thesis load", `RES`. Values: Δ observer CPU (cores) / Δ observer anonymous memory (MiB).

| Block (host) | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|
| boutique-b1 (A) | +0.050 / +91 | +0.052 / +79 | +0.078 / +133 | +0.071 / +111 |
| boutique-b2 (B) | +0.062 / +98 | +0.087 / +80 | +0.216 / +135 | +0.211 / +114 |
| bank-b1 (B) | +0.134 / +105 | +0.141 / +81 | +0.231 / +145 | +0.210 / +109 |
| bank-b2 (C) | +0.047 / +106 | +0.070 / +82 | +0.078 / +143 | +0.070 / +113 |
| dsb-b1 (A) | +0.225 / +108 | +0.088 / +81 | +0.122 / +150 | +0.061 / +117 |
| dsb-b2 (C) | +0.106 / +110 | +0.090 / +80 | +0.096 / +150 | +0.071 / +116 |
| otel-b1 (A) | +0.075 / +111 | +0.061 / +82 | +0.070 / +134 | +0.066 / +115 |
| otel-b2 (C) | +0.035 / +112 | +0.065 / +81 | +0.069 / +135 | +0.069 / +115 |
| teastore-b1 (A) | +0.046 / +86 | +0.048 / +81 | +0.073 / +134 | +0.063 / +110 |
| teastore-b2 (C) | +0.031 / +87 | +0.055 / +81 | +0.081 / +137 | +0.074 / +111 |

Ranges over the 10 blocks (**derived** from `RES`, min and max of each column; `SUM` main result 2
and 3 gives the same ranges rounded):

| Method | Δ CPU (cores) | Δ anon memory (MiB) |
|---|---|---|
| Hubble | 0.031 to 0.225 | 86 to 112 |
| Otterize | 0.048 to 0.141 | 79 to 82 |
| IG trace_tcp | 0.069 to 0.231 | 133 to 150 |
| IG snapshot_socket | 0.061 to 0.211 | 109 to 117 |
| all methods | 0.031 to 0.231 | 79 to 150 |

- IG trace_tcp has the largest Δ memory of the four methods in every one of the 10 blocks
  (**derived** from `RES`, per-block maximum).
- Hubble's Δ CPU is highest on DSB on both host types where DSB ran: 0.225 on A (other A blocks
  0.046-0.075) and 0.106 on C (other C blocks 0.031-0.047). `SUM` main result 3; values from `RES`.
- DSB had the highest Hubble event rate of the thesis captures (354 lines/s): `FIX` representativeness
  row "No event-rate check vs the thesis".

Absolute values with standard deviations (Appendix table of the thesis), from `BLK(<block>)` tables
"CPU (cores, steady window)" (observer mean ± SD of the window means over the 10 cycles) and
"Memory (MiB, steady window)" (observer anonymous memory, mean over cycles; no SD is printed for it):

| Block | baseline | Hubble | Otterize | IG trace_tcp | IG snapshot_socket | anon MiB (base/Hub/Ott/tcp/snap) |
|---|---|---|---|---|---|---|
| boutique-b1 | 0.096 ± 0.005 | 0.146 ± 0.013 | 0.148 ± 0.006 | 0.174 ± 0.007 | 0.167 ± 0.008 | 371/462/450/504/482 |
| boutique-b2 | 0.097 ± 0.002 | 0.158 ± 0.002 | 0.183 ± 0.002 | 0.313 ± 0.004 | 0.307 ± 0.004 | 370/468/451/505/485 |
| bank-b1 | 0.095 ± 0.002 | 0.229 ± 0.008 | 0.236 ± 0.004 | 0.325 ± 0.004 | 0.305 ± 0.005 | 370/475/450/515/479 |
| bank-b2 | 0.041 ± 0.001 | 0.087 ± 0.002 | 0.111 ± 0.002 | 0.119 ± 0.004 | 0.110 ± 0.003 | 368/474/450/510/481 |
| dsb-b1 | 0.096 ± 0.009 | 0.321 ± 0.074 | 0.184 ± 0.011 | 0.218 ± 0.019 | 0.157 ± 0.006 | 377/485/458/527/495 |
| dsb-b2 | 0.047 ± 0.008 | 0.154 ± 0.033 | 0.138 ± 0.012 | 0.144 ± 0.012 | 0.119 ± 0.009 | 377/487/457/527/493 |
| otel-b1 | 0.093 ± 0.006 | 0.168 ± 0.019 | 0.153 ± 0.007 | 0.163 ± 0.006 | 0.158 ± 0.007 | 374/485/456/508/489 |
| otel-b2 | 0.040 ± 0.002 | 0.075 ± 0.003 | 0.105 ± 0.003 | 0.109 ± 0.003 | 0.109 ± 0.003 | 375/487/456/510/490 |
| teastore-b1 | 0.065 ± 0.004 | 0.111 ± 0.004 | 0.113 ± 0.009 | 0.139 ± 0.006 | 0.128 ± 0.005 | 367/453/448/502/477 |
| teastore-b2 | 0.047 ± 0.009 | 0.077 ± 0.014 | 0.101 ± 0.011 | 0.128 ± 0.014 | 0.120 ± 0.014 | 368/455/449/505/478 |

The within-window SD of the 5-s values (burstiness) is in the same `BLK` tables, column "SD in
window", and is not quoted in the thesis.

## 4. Cost under connection churn (new-connection fixed-count tests)

Δ observer CPU (cores) during the new-connection tests. Source: `COMB` "Cost under load".

| Block | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|
| boutique-b1 | +0.458 | +0.064 | +0.176 | +0.082 |
| boutique-b2 | +0.592 | +0.118 | +0.317 | +0.202 |
| bank-b1 | +0.724 | +0.198 | +0.345 | +0.202 |
| bank-b2 | +0.580 | +0.117 | +0.180 | +0.068 |
| dsb-b1 | +0.378 | +0.090 | +0.154 | +0.058 |
| dsb-b2 | +0.363 | +0.093 | +0.152 | +0.072 |
| otel-b1 | +0.766 | +0.062 | +0.295 | +0.082 |
| otel-b2 | +0.765 | +0.094 | +0.265 | +0.081 |
| teastore-b1 | +0.599 | +0.074 | +0.195 | +0.064 |
| teastore-b2 | +0.633 | +0.104 | +0.245 | +0.080 |

**Derived** (range of the column; ratio = this table / section 3 Δ CPU of the same block):

| Method | under churn (cores) | ratio to thesis-load cost |
|---|---|---|
| Hubble | 0.363 to 0.766 | 1.7 to 21.7 |
| IG trace_tcp | 0.152 to 0.345 | 1.3 to 4.2 |
| Otterize | 0.062 to 0.198 | 1.0 to 1.9 |
| IG snapshot_socket | 0.058 to 0.202 | 0.96 to 1.25 |

Note: `SUM` and `HAND` say "2 to 22 times" for Hubble. The exact minimum is dsb-b1, 0.378 / 0.225
= 1.68, so the thesis says 1.7 to 21.7 (maximum otel-b2, 0.765 / 0.035 = 21.7; computed from the
unrounded CSV values). `SUM` says 1.3 to 4 for trace_tcp; the exact maximum is otel-b1, 4.2.
Hubble's Δ is the largest of the four methods in every block (**derived**, per-row maximum).

## 5. Fixed-count time (GoLeash Table 5 format)

Source: `T5` and `COMB` "Fixed-count time". The thesis tables reproduce `SUM` "Throughput" (cells
"n.s., <X%" give the upper 95% bound rounded **up** to the next whole percent; bold = robust).
Checked cell by cell against the unrounded `ci_hi` in `T5` (for example boutique-b1 keep-alive
Hubble 13.01 -> "<14%").

Robust slowdowns (point estimate and 95% CI, `COMB` "Throughput effects that survive every check"):

| Block (host) | Method | Mode | Overhead [95% CI] |
|---|---|---|---|
| boutique-b2 (B) | Hubble | new conn | +7.1% [+3.0, +11.2] |
| bank-b1 (B) | Hubble | keep-alive | +9.9% [+6.6, +13.2] |
| bank-b1 (B) | Hubble | new conn | +9.6% [+6.1, +13.1] |
| bank-b1 (B) | IG trace_tcp | keep-alive | +6.5% [+4.3, +8.8] |
| bank-b1 (B) | IG trace_tcp | new conn | +6.0% [+3.2, +8.7] |
| bank-b1 (B) | IG snapshot_socket | keep-alive | +3.2% [+1.0, +5.5] |
| bank-b2 (C) | Hubble | keep-alive | +19.6% [+15.3, +23.8] |
| bank-b2 (C) | Hubble | new conn | +18.9% [+12.5, +25.2] |
| bank-b2 (C) | IG trace_tcp | keep-alive | +10.3% [+5.7, +15.0] |
| bank-b2 (C) | IG trace_tcp | new conn | +9.6% [+5.0, +14.2] |
| bank-b2 (C) | Otterize | keep-alive | +5.3% [+1.6, +8.9] |
| dsb-b2 (C) | Hubble | new conn | +14.4% [+10.0, +18.8] |
| otel-b2 (C) | Otterize | keep-alive | +20.2% [+14.0, +26.5] |
| otel-b2 (C) | Hubble | new conn | +30.3% [+15.6, +45.0] |
| teastore-b2 (C) | Hubble | new conn | +25.7% [+15.9, +35.5] |

15 robust effects in 80 throughput cells; 0 fragile (`COMB`).

Baseline (w/o) fixed-count time, mean ± SD over 10 tests (`T5` `wo_s`, `wo_sd`):

| Block | keep-alive (s) | new conn (s) | baseline CV keep-alive / new conn (**derived**, SD/mean) |
|---|---|---|---|
| boutique-b1 (A) | 41.9 ± 9.1 | 37.4 ± 6.6 | 21.7% / 17.5% |
| boutique-b2 (B) | 66.4 ± 2.3 | 65.2 ± 2.0 | 3.5% / 3.1% |
| bank-b1 (B) | 50.0 ± 1.3 | 51.4 ± 1.3 | 2.6% / 2.5% |
| bank-b2 (C) | 13.9 ± 0.6 | 14.5 ± 0.7 | 4.1% / 5.1% |
| dsb-b1 (A) | 50.1 ± 7.1 | 53.9 ± 7.4 | 14.1% / 13.8% |
| dsb-b2 (C) | 18.1 ± 2.1 | 20.2 ± 1.9 | 11.6% / 9.5% |
| otel-b1 (A) | 41.1 ± 8.1 | 45.5 ± 7.9 | 19.7% / 17.3% |
| otel-b2 (C) | 30.9 ± 1.8 | 36.1 ± 5.0 | 5.8% / 13.9% |
| teastore-b1 (A) | 49.1 ± 3.4 | 49.3 ± 3.4 | 7.0% / 6.8% |
| teastore-b2 (C) | 49.2 ± 4.1 | 49.2 ± 3.9 | 8.3% / 8.0% |

- Host A baseline variation 7% to 22% between cycles: `SUM` "How to read it" (exact 6.8% to 21.7%
  above). Widest host-A upper bound 39% (otel-b1 new conn Hubble, 38.4 -> "<39%").
- The three "n.s.\*" cells (interval below zero before correction, n.s. after): otel-b1 keep-alive
  IG trace_tcp -17.0% [-30.0, -4.0]; teastore-b1 Otterize keep-alive -18.0% [-34.3, -1.8] and new
  conn -17.6% [-33.6, -1.6]. `T5`; `SUM` footnote.
- Quota-bound (Boutique, Bank, DSB) vs node-bound (OTel, TeaStore; 0.00 s/s). The classification is
  in `SUM` Limitations ("Why the apps differ is only partly explained"). The baseline throttling of the
  most throttled container is 0.8 to 2.2 s/s in the new-connection test only (**derived**: per-block mean
  of `bottleneck_thr` over the baseline runs in `fixed_count_tests.csv`, 0.77 to 2.18); with keep-alive it
  is 0.85 to 2.46, and 2.46 on both DSB blocks. No `SUM` or `FIX` entry states the range.

## 6. Agent-only Hubble (default configuration)

Source: `AO` (both tables) and `agent_only_summary.csv`. 12 cycles per app, one block per app,
conditions baseline / full Hubble / agent-only, all 6 orders twice, 36 runs per app, 180 runs,
0 failed. Retried attempts: Boutique 0, Bank 0, DSB 1, OTel 5, TeaStore 1. Hosts: Boutique, Bank,
OTel on host A (Intel 1997 MHz); DSB, TeaStore on host C (AMD 4192 MHz).

| App | Δ CPU (cores) | Δ anon (MiB) | keep-alive | new conn |
|---|---|---|---|---|
| Boutique (A) | +0.010 [+0.008, +0.012] | +33 [+30, +36] | -2.1% [-12.9, +8.7] | +5.3% [-8.0, +18.5] |
| Bank (A) | +0.018 [+0.014, +0.022] | +43 [+40, +46] | +5.1% [-6.9, +17.1] | +7.2% [-1.3, +15.7] |
| DSB (C) | +0.017 [+0.016, +0.018] | +32 [+30, +34] | +0.1% [-4.6, +4.9] | -2.5% [-20.7, +15.7] |
| OTel (A) | +0.017 [+0.014, +0.020] | +46 [+44, +49] | +6.1% [-13.6, +25.9] | +7.8% [-12.0, +27.6] |
| TeaStore (C) | +0.008 [+0.007, +0.009] | +20 [+18, +23] | -0.6% [-5.1, +4.0] | -0.1% [-4.7, +4.5] |

CPU and memory robust in all five apps; every fixed-count interval includes zero (n.s.).
Per-app largest upper bound (**derived**, max of the two modes): Boutique 18.5%, Bank 17.1%,
DSB 15.7%, OTel 27.6%, TeaStore 4.5%. Range of those: 4.5% to 27.6%.

Agent-only minus full stack, same cycles (secondary, `AO` second table): DSB keep-alive -10.4%
[-12.3, -8.5], new conn -8.2% [-12.7, -3.7]; TeaStore new conn -17.5% [-21.0, -13.9]; the other
throughput contrasts n.s. Agent-only share of the full stack's extra observer CPU: Boutique 27%,
Bank 22%, DSB 14%, OTel 25%, TeaStore 29% (range 14% to 29%). Δ memory agent-only minus full:
-64 to -80 MiB. Host-A agent-only blocks: the baseline fixed-count time varies 10% to 17% between
cycles (`AO` guide, corrected 2026-10-06; the earlier "14% to 22%" was the main study's range and
is not used). Boutique keep-alive upper bound +8.7%; widest bound OTel new connection +27.6%.
The agent's own CPU share inside the full stack, 41% to 47%, is from `AO` guide and `FIX`
"Agent-only Hubble experiment".

Reading rules followed (from `AO` "How to read this"): "no detectable slowdown, upper bound X%",
never "no overhead". On DSB and TeaStore, where the intervals are tight, the full stack's slowdown comes
from the opt-in parts (metrics server, Relay, streaming client) taken together. On Boutique, Bank and
OTel the agent-only upper bounds (8.7% to 27.6%) cannot exclude a slowdown as large as the full stack's.
The experiment does not separate the three parts.

## 7. Host type and Inspektor Gadget's agent

Source: `COMB` "Host type and Inspektor Gadget's own CPU". Steady-window CPU (cores).

| Block (host) | gadget (trace_tcp) | gadget (snapshot_socket) | cilium-agent at baseline |
|---|---|---|---|
| boutique-b1 (A) | 0.074 | 0.071 | 0.082 |
| boutique-b2 (B) | 0.211 | 0.207 | 0.084 |
| bank-b1 (B) | 0.219 | 0.207 | 0.083 |
| bank-b2 (C) | 0.073 | 0.067 | 0.032 |
| dsb-b1 (A) | 0.103 | 0.064 | 0.083 |
| dsb-b2 (C) | 0.088 | 0.071 | 0.039 |
| otel-b1 (A) | 0.071 | 0.068 | 0.080 |
| otel-b2 (C) | 0.068 | 0.068 | 0.034 |
| teastore-b1 (A) | 0.069 | 0.065 | 0.055 |
| teastore-b2 (C) | 0.077 | 0.072 | 0.038 |

**Derived** ranges: gadget on host B 0.207 to 0.219; on hosts A and C 0.064 to 0.103.
cilium-agent at baseline: host A 0.055 to 0.083, host B 0.083 to 0.084, host C 0.032 to 0.039.
Same app, two hosts: Bank 0.219 (B) vs 0.073 (C) (`SUM` result 7). Mechanism (software
retpolines and return thunks make system calls dearer; the gadget agent is syscall-heavy) is an
untested hypothesis: `FIX` "Host type changes Inspektor Gadget's CPU cost" and its update.

## 8. Behaviour under stress (no method broken on purpose)

| Quantity | Value | Source |
|---|---|---|
| Hubble lost events, steady window, mean per run | none for Boutique, OTel, TeaStore; 6 to 37 for Bank; about 100 for DSB | `SUM` "When the method is stressed" |
| Hubble lost events, whole run incl. fixed-count tests | on average per run: block means 64 to 205; single runs 59 to 261 | `SUM` same section (block means); single-run range **derived** from `hubble.lost_events_run` in the ten `runs.csv` files, Hubble runs |
| OTel services restarting at their thesis memory limits under the fixed-count load | 25 retried attempts across the two OTel blocks (13 and 12); no restart at the thesis load; no run lost | `SUM`; `COMB` Blocks; `OPS` host list (otel-b1: 1 IG warm-up + 12 app OOM restarts) |
| RQ2 of the benchmark brief (breaking a method on purpose) | not tested | `SUM`; `HAND` |

## 9. Projection to the original cluster (estimate)

Source: `SUM` "Projection" table; per-block projection tables in `BLK(<block>)`. Observer CPU only,
thesis load, % of the original cluster's 18 vCPU, range over blocks.

| Method | % of 18 vCPU |
|---|---|
| Hubble | 0.14 to 0.88% |
| Otterize | 0.39 to 1.10% |
| IG trace_tcp | 0.75 to 0.90% (2.3% on host B) |
| IG snapshot_socket | 0.65 to 0.78% (2.2% on host B) |
| Hubble + Otterize + IG trace_tcp (the thesis set-up, assuming the costs add) | 1.3 to 2.4% (3.3 to 4.0% on host B) |

App-attributable only; the platform and its monitoring added traffic that is not in these numbers.
18 vCPU = 3 control-plane nodes x 2 vCPU + 3 workers x 4 vCPU (`README` deviation table).

## 10. Joined finding with the generator study (different clusters)

Generator-study numbers are unchanged, from `TJ` and thesis Table `tab:twojourney`. The three
capture methods compared on both axes are Otterize, IG trace_tcp and IG snapshot_socket. Hubble is
a capture source for the flow synthesiser, not a standalone generator, so it has no false-deny of
its own.

| App | trace_tcp false-deny vs B (Otterize, snapshot) | trace_tcp live drops (Otterize, snapshot) | trace_tcp worst or tied-worst of the three? |
|---|---|---|---|
| Online Boutique | 0.938 (0.000, 0.000) | 600 (0, 0) | yes, both |
| DSB social network | 0.833 (0.833, 0.267) | 3260 (3249, 2052) | tied-worst on false-deny, worst on drops |
| Bank of Anthos | 0.333 (0.083, 0.500) | 210 (336, 40) | no |
| OpenTelemetry demo | 0.840 (0.080, 0.160) | 380 (0, 256) | yes, both |
| TeaStore | 0.083 (0.000, 0.000) | 204 (0, 2) | yes, both |

**Derived**: trace_tcp is worst or tied-worst on false-deny or live drops in 4 of 5 apps (all but
Bank), and has the largest Δ memory in all 10 blocks of section 3.

## 11. Campaign size (sustainability)

| Quantity | Value | Source |
|---|---|---|
| Main study | 500 runs in 10 blocks | `COMB` |
| Agent-only study | 180 runs in 5 blocks | `AO` |
| Pilots | pilot v1 and v2, the 3-repetition Boutique matrix, a 90-min drift probe and one validation cycle | `FIX`; `README` |
| Campaign span | 2026-10-02 (cluster lock 10:32Z) to 2026-10-06 03:12Z, about 89 h of wall-clock time | **derived** from `cluster/versions.lock` header and `FIX` last section |
| Duration of one main block | 9.5 to 11.7 h for the four blocks with start and end times recorded (teastore-b1 10.3 h, boutique-b2 11.0 h, dsb-b2 9.5 h, otel-b2 11.7 h); `README` gives 10-11 h for 10 cycles | `OPS` host list; `README` time budget |
| Duration of one agent-only block | about 8 to 9 h (started 18:10-19:10Z on 2026-10-05, finished by 03:12Z on 2026-10-06) | `OPS`; `FIX` |
| Play size | one play = 3 VMs, 10 vCPU in total | `README`; `cluster/versions.lock` |

Open point for the author: the brief for the thesis update gives "roughly 90 iximiuz play-hours".
That matches the wall-clock span above. Summed over plays, the block durations above give of the
order of 100 play-hours for the main blocks and 40 for the agent-only blocks, before the pilots.
The thesis states both the span and the per-block durations, and no single total.

## 12. Other numbers quoted in the thesis text

| Thesis statement | Value | Source |
|---|---|---|
| IG Δ observer CPU by host (Chapter 6, resources) | both gadgets 0.210 to 0.231 cores on host B; 0.061 to 0.122 on hosts A and C | **derived** from section 3 (min/max of the IG columns by host) |
| Cluster-wide busy CPU drifts with the host | moves 1.5 to 2 times with host drift; observer group barely moves | `FIX` "Primary endpoints" row "Primary CPU endpoint" |
| Working set vs anonymous memory | gadget container WS 323 MiB (cycle 1) vs 138 MiB (cycle 2), anon 114 vs 120 MiB | `FIX` "Primary endpoints" row "Primary memory endpoint" |
| Quota-bound throttling at baseline, most throttled container | 0.8 to 2.2 s/s in the new-connection test only (Boutique, Bank, DSB); with keep-alive 0.85 to 2.46, reaching 2.46 on DSB; 0.00 s/s (OTel, TeaStore) | **derived** from `fixed_count_tests.csv` (`bottleneck_thr`, baseline rows, mean per block); classification in `SUM` Limitations |
| TeaStore baseline time | 49.1 s (host A) and 49.2 s (host C), both modes | `T5` |
| Run length | 11 to 12 min (659 to 728 s) | `FIX` "Cycle timing" |
| Generator-node load check | control-plane VM below 75% busy during the fixed-count tests | `README` step 5 (`sanity_check.py`) |
| Agent-only upper bounds, range | per app, the worse of the two modes: 4.5% (TeaStore) to 27.6% (OTel) | section 6 table, per-app worst case |
| Host-A agent-only bounds | 8.7% (Boutique keep-alive) to 27.6% (OTel new conn) | section 6 table; `AO` guide (corrected) |
| Hubble robust new-connection slowdowns | 6 of 10 blocks, at least one per app; range 7.1% to 30.3% | section 5 table |
| Hubble is the only method with a robust slowdown in every app | trace_tcp, Otterize and snapshot_socket slow only Bank and (Otterize) OTel | section 5 table |
| Abstract ranges | 0.03 to 0.23 cores (0.031 to 0.231 rounded to two places), 79 to 150 MiB, 7 to 30% (7.1 to 30.3) | sections 3 and 5 |
| Cilium production use | 29% of organisations (16% evaluating), CNCF 2025 survey, Figure 19, Q32, n = 395-596; 628 respondents, September 2025 | `thesis/CITATIONS-TODO.md` entry `cncf2025survey` (read from the survey PDF) |
| Cilium tuning-guide figure | "somewhere between 1-15%", present since the v1.10 docs (release 2021-05-20) | `thesis/CITATIONS-TODO.md` entry `ciliumtuning` |
