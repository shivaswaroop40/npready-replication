# What the four capture methods cost: results summary

Status: the main measurements finished on 2026-10-05 (10 blocks, 500 runs, no run lost). The agent-only Hubble experiment finished on 2026-10-06 (5 blocks, 180 runs, none failed).
Main numbers come from `COMBINED/RESULTS-COMBINED.md`. Agent-only numbers come from `../PERF-AGENTONLY-20261005/AGENT-ONLY-SUMMARY.md`. Decisions are logged in `../../perf-benchmark/FIXLOG.md`.

## What was measured

- **Methods:** Hubble, Otterize, Inspektor Gadget (IG) `trace_tcp`, and IG `snapshot_socket`. In the main study, Hubble means the full stack: Hubble in the Cilium agent, the metrics server, Relay and a streaming `hubble observe` client. Hubble in the agent only (the Helm default) is a separate experiment, described below.
- **Baseline:** Cilium with Hubble switched off and nothing else running.
- **Apps:** Online Boutique, Bank of Anthos, DSB social network, OpenTelemetry demo, TeaStore.
- **Cluster:** an iximiuz Labs copy of `test-cluster` (k3s 1.36.3, Cilium 1.19.5 with the same 155 settings). It has one 2-vCPU control-plane node and two 4-vCPU workers.
- **One cycle:** each of the five conditions once, in a balanced order. A cycle has 60 s idle, 60 s warm-up, a 5-minute steady window at the thesis load, and one fixed-count test per mode.
- **Fixed-count test (GoLeash Table 5):** time to send a fixed number of requests, at concurrency 16. The size is set per app so that a test lasts about 50 s (608 to 9,152 requests). Two modes: keep-alive, and a new TCP connection per request.
- **One block:** 10 cycles on one fresh play. Each app has two blocks, so 20 cycles.
- **Comparison:** every method is compared with the baseline of the same cycle. The result is the mean of the 10 paired differences with a 95% confidence interval.

Why not 3 long repetitions: the iximiuz hosts changed speed by a factor of up to 2.6 within one condition over 90 minutes (drift probe: 15.8 to 41.1 s), and 3 long runs let that drift land on one method. A test showed a false 50% speed-up for `snapshot_socket`. Short interleaved cycles in balanced order turn the drift into noise that the interval shows. This is the RMIT method (Abedi and Brecht, ICPE 2017).

The two blocks of an app ran on **different host types**, which were not under our control. They are never pooled. Host A is Intel Xeon 2.0 GHz with hardware Spectre protection. Host B is AMD EPYC 2.5 GHz with software protection (retpolines). Host C is AMD EPYC 4.2 GHz with hardware protection.

## Main results

1. **Every method costs CPU and memory at the thesis load.** This holds in all 10 blocks and passes every check.
2. **Memory cost varies little with the app.** Hubble (full stack) +86 to +112 MiB, Otterize +79 to +82, IG `trace_tcp` +133 to +150, IG `snapshot_socket` +109 to +117.
3. **CPU cost at the thesis load is small.** Extra observer CPU: Hubble (full stack) 0.03 to 0.23 cores, Otterize 0.05 to 0.14, IG `trace_tcp` 0.07 to 0.23, IG `snapshot_socket` 0.06 to 0.21. Hubble costs most on DSB, the app with the most traffic in the thesis captures, on both host types where DSB was measured.
4. **The full Hubble stack slows an app that opens many connections.** With a new connection per request it slows the fixed-count test in every app where the measurement could resolve it (4 of the 10 blocks were too noisy to tell): Boutique +7%, Bank +10% and +19%, DSB +14%, OTel +30%, TeaStore +26%. In the main study, with keep-alive, it shows only on Bank (+10% and +20%). In the agent-only experiment, the full-stack condition also slowed DSB with keep-alive (+11.8%, 95% interval 6.6 to 17.0). Item 8 says what is known about where these slowdowns come from.
5. **The other methods rarely show a slowdown.** IG `trace_tcp` costs Bank +6% to +10%. Otterize costs OTel +20% (keep-alive, one block) and Bank +5% (one block). IG `snapshot_socket` costs Bank +3% (one block). Everything else is not detectable.
6. **Under heavy connection load, the full Hubble stack costs the most CPU.** It uses 0.36 to 0.77 extra cores, which is 2 to 22 times its cost at the thesis load. IG `trace_tcp` uses 0.15 to 0.35 (1.3 to 4 times). Otterize uses 0.06 to 0.20 (1 to 2 times). IG `snapshot_socket` uses 0.06 to 0.20 and barely changes.
7. **IG's CPU cost depends on the host.** The gadget agent uses about 0.21 cores on host B and 0.06 to 0.10 on every other block. Same app, two hosts (Bank): 0.219 against 0.073 cores.
8. **The default install (Hubble in the agent only) costs 0.008 to 0.018 extra cores and 20 to 46 MiB of anonymous memory, and no slowdown was detected.** Both costs are robust in all five apps. The fixed-count test shows no detectable slowdown in any app or mode. The upper bounds, taking each app's worse mode, run from below 4.5% (TeaStore) to below 27.6% (OTel), so this is not a claim of no overhead. On DSB and TeaStore the intervals are tight, and the full stack is slower than agent-only in the same cycles. So on those two apps the slowdown comes from the opt-in parts (the metrics server, Relay and the streaming client), not from Hubble in the agent. On Boutique, Bank and OTel the agent-only upper bounds (8.7% to 27.6%) cannot exclude a slowdown as large as the full stack's. The experiment does not separate the three opt-in parts.

## Throughput: GoLeash Table 5 format

Cells show the slowdown of the fixed-count test against the baseline of the same cycles. **Bold** means significant after Holm correction and in both sensitivity checks (median with Wilcoxon test, and without the block's first run; fixed on 2026-10-04, after four blocks were done). "n.s., <X%" means not significant, and the effect is below X% at 95% confidence. "w/o" is the baseline time, mean ± SD over 10 tests.

**Keep-alive**

| App | Block | Host | w/o (s) | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|---|---|
| Online Boutique | boutique-b1 | A | 41.9 ± 9.1 | n.s., <14% | n.s., <26% | n.s., <14% | n.s., <8% |
| Online Boutique | boutique-b2 | B | 66.4 ± 2.3 | n.s., <5% | n.s., <2% | n.s., <5% | n.s., <3% |
| Bank of Anthos | bank-b1 | B | 50.0 ± 1.3 | **+9.9%** | n.s., <5% | **+6.5%** | **+3.2%** |
| Bank of Anthos | bank-b2 | C | 13.9 ± 0.6 | **+19.6%** | **+5.3%** | **+10.3%** | n.s., <8% |
| DSB social network | dsb-b1 | A | 50.1 ± 7.1 | n.s., <27% | n.s., <20% | n.s., <5% | n.s., <8% |
| DSB social network | dsb-b2 | C | 18.1 ± 2.1 | n.s., <14% | n.s., <12% | n.s., <13% | n.s., <9% |
| OpenTelemetry demo | otel-b1 | A | 41.1 ± 8.1 | n.s., <29% | n.s., <33% | n.s.* | n.s., <4% |
| OpenTelemetry demo | otel-b2 | C | 30.9 ± 1.8 | n.s., <29% | **+20.2%** | n.s., <32% | n.s., <17% |
| TeaStore | teastore-b1 | A | 49.1 ± 3.4 | n.s., <9% | n.s.* | n.s., <6% | n.s., <8% |
| TeaStore | teastore-b2 | C | 49.2 ± 4.1 | n.s., <15% | n.s., <6% | n.s., <9% | n.s., <4% |

**New connection per request**

| App | Block | Host | w/o (s) | Hubble | Otterize | IG trace_tcp | IG snapshot_socket |
|---|---|---|---|---|---|---|---|
| Online Boutique | boutique-b1 | A | 37.4 ± 6.6 | n.s., <18% | n.s., <27% | n.s., <17% | n.s., <14% |
| Online Boutique | boutique-b2 | B | 65.2 ± 2.0 | **+7.1%** | n.s., <6% | n.s., <6% | n.s., <6% |
| Bank of Anthos | bank-b1 | B | 51.4 ± 1.3 | **+9.6%** | n.s., <4% | **+6.0%** | n.s., <3% |
| Bank of Anthos | bank-b2 | C | 14.5 ± 0.7 | **+18.9%** | n.s., <8% | **+9.6%** | n.s., <8% |
| DSB social network | dsb-b1 | A | 53.9 ± 7.4 | n.s., <19% | n.s., <10% | n.s., <8% | n.s., <7% |
| DSB social network | dsb-b2 | C | 20.2 ± 1.9 | **+14.4%** | n.s., <6% | n.s., <13% | n.s., <2% |
| OpenTelemetry demo | otel-b1 | A | 45.5 ± 7.9 | n.s., <39% | n.s., <31% | n.s., <9% | n.s., <2% |
| OpenTelemetry demo | otel-b2 | C | 36.1 ± 5.0 | **+30.3%** | n.s., <39% | n.s., <35% | n.s., <28% |
| TeaStore | teastore-b1 | A | 49.3 ± 3.4 | n.s., <29% | n.s.* | n.s., <7% | n.s., <7% |
| TeaStore | teastore-b2 | C | 49.2 ± 3.9 | **+25.7%** | n.s., <6% | n.s., <11% | n.s., <4% |

\* The interval is below zero before correction and not significant after it. A method cannot make an app faster, so this is read as host drift.

How to read it:

- **Host A blocks are noisy.** Their baseline varies 7% to 22% between cycles, so many of their upper bounds are wide (up to 39%). They rule out little. None of them contradicts the precise blocks: for new-connection Hubble, every Host A interval contains the matching Host B or C estimate.
- **Seconds are not comparable between blocks.** Bank takes 50 s on host B and 14 s on host C for the same 608 requests. Only the percentage inside a block is meaningful.
- **Hubble here is the full stack.** Agent-only Hubble, the default install, has its own section below.
- **Faster hosts show larger percentages.** On Bank, Hubble costs +10% on the slow host and +20% on the fast one. This suggests that the cost per connection is fixed, so it weighs more when the app is quicker. Only Bank supports this clearly.

## Agent-only Hubble: what a default install pays

The main study measured the full Hubble stack. A default Helm install runs Hubble in the Cilium agent only, with no metrics server, Relay or client. This experiment measures that default. Full report: `../PERF-AGENTONLY-20261005/AGENT-ONLY-SUMMARY.md`, with `agent_only_summary.csv`.

- **Conditions per cycle:** baseline (Hubble off), full Hubble (agent, metrics server, Relay and a streaming client) and agent-only Hubble. Aggregation stays at the cluster's `medium`, which is also the Helm default. The Cilium version is 1.19.5.
- **Design:** 12 cycles per app on one fresh play, with all 6 condition orders twice. The cycle profile, the fixed-count tests and the paired analysis are as in the main study. That is 36 runs per app, 180 in total, none failed. Each app is one block on one host type and is never pooled.
- **Endpoints:** fixed before the data came in (FIXLOG, 2026-10-05): observer CPU, observer anonymous memory, and fixed-count time. The verdict uses Holm correction over the two Hubble conditions, the median with a Wilcoxon test, and the analysis without the first run. "n.s., <X%" has the same meaning as in Table 5.
- **One harness fix:** on two plays the first agent-only switch failed its check, because Hubble reported Warning for a few seconds after the agent restart. The fix waits for Hubble to be ready before the check. It runs before anything is measured (FIXLOG, 2026-10-05).

**Agent-only Hubble against baseline.** Mean of the 12 paired per-cycle differences, with the 95% confidence interval. Host A is the Intel Xeon 1997 MHz type and host C is the AMD EPYC 4192 MHz type, as defined above. Bounds are rounded up to a whole percent, as in Table 5.

| App | Host | Extra CPU (cores) | Extra anonymous memory (MiB) | Fixed-count, keep-alive | Fixed-count, new connection |
|---|---|---|---|---|---|
| Online Boutique | A | +0.010 [+0.008, +0.012] | +33 [+30, +36] | n.s., <9% | n.s., <19% |
| Bank of Anthos | A | +0.018 [+0.014, +0.022] | +43 [+40, +46] | n.s., <18% | n.s., <16% |
| DSB social network | C | +0.017 [+0.016, +0.018] | +32 [+30, +34] | n.s., <5% | n.s., <16% |
| OpenTelemetry demo | A | +0.017 [+0.014, +0.020] | +46 [+44, +49] | n.s., <26% | n.s., <28% |
| TeaStore | C | +0.008 [+0.007, +0.009] | +20 [+18, +23] | n.s., <4% | n.s., <5% |

**Agent-only against the full stack, same cycles (secondary).** Agent-only minus full stack. A negative number means agent-only costs less or runs faster. The fixed-count cells compare the test time of the two conditions in the same cycle, in %. "n.s." means the interval includes zero. The last column is the agent-only share of the full stack's extra observer CPU over baseline. This contrast is not in the Holm family and has no sensitivity checks.

| App | Host | Extra CPU (cores) | Extra anonymous memory (MiB) | Fixed-count, keep-alive | Fixed-count, new connection | Agent-only share of extra CPU |
|---|---|---|---|---|---|---|
| Online Boutique | A | -0.027 [-0.035, -0.020] | -66 [-70, -62] | +0.9% [-13.3, +15.0] n.s. | +0.4% [-10.2, +11.0] n.s. | 27% |
| Bank of Anthos | A | -0.065 [-0.072, -0.058] | -67 [-71, -64] | +0.2% [-11.4, +11.7] n.s. | -3.9% [-11.0, +3.2] n.s. | 22% |
| DSB social network | C | -0.106 [-0.108, -0.104] | -80 [-82, -79] | -10.4% [-12.3, -8.5] | -8.2% [-12.7, -3.7] | 14% |
| OpenTelemetry demo | A | -0.050 [-0.052, -0.047] | -67 [-71, -63] | -3.4% [-21.4, +14.6] n.s. | -10.2% [-23.7, +3.4] n.s. | 25% |
| TeaStore | C | -0.020 [-0.021, -0.018] | -64 [-66, -62] | -1.3% [-5.8, +3.3] n.s. | -17.5% [-21.0, -13.9] | 29% |

How to read it:

- **The default install has a measured cost.** Extra CPU and extra memory are robust in all five apps. Agent-only Hubble accounts for 14% to 29% of the full stack's extra observer CPU and 24% to 41% of its extra anonymous memory.
- **No slowdown was detected, which is not "no overhead".** Every fixed-count interval includes zero. The upper bounds are the numbers to quote: TeaStore below 4.5% in both modes, DSB below 4.9% with keep-alive, Boutique below 8.7% with keep-alive. The other cells are wide. The widest is below 27.6% (OTel, new connection).
- **Intel blocks are wide.** Boutique, Bank and OTel ran on Intel hosts. The baseline test time varies by 10% to 17% between cycles there (standard deviation over mean), so they cannot rule out a slowdown of up to 9% (Boutique, keep-alive) to 28% (OTel, new connection).
- **DSB with a new connection per request is wide although the host is AMD.** The baseline test time in that cell is very spread out (mean 31 s, standard deviation 48 s), which most likely explains the wide interval.
- **The full stack is clearly slower than agent-only on DSB and TeaStore.** On DSB the agent-only tests take 10.4% (keep-alive) and 8.2% (new connection) less time than the full stack. On TeaStore with a new connection per request they take 17.5% less. In the other seven cells the interval includes zero, so those contrasts say nothing either way.
- **On DSB and TeaStore the slowdown comes from the opt-in parts, not from Hubble in the agent.** The evidence is clear there. On Boutique, Bank and OTel the intervals are too wide to separate the two conditions, and the agent-only upper bounds (8.7% to 27.6%) cannot exclude a slowdown as large as the full stack's. The opt-in parts are the metrics server, Relay and the streaming client. This experiment turns the three on together, so it cannot say which one matters. None should be blamed alone. The client also ran on the same 2-vCPU node as the load generator.

## Cost under load and projection to test-cluster

In the new-connection tests the app serves one new connection per request, as fast as it can. Extra observer CPU over the 10 blocks: Hubble 0.36 to 0.77 cores, IG `trace_tcp` 0.15 to 0.35, Otterize 0.06 to 0.20, IG `snapshot_socket` 0.06 to 0.20.

Projection to `test-cluster` (18 vCPU, observer CPU only, at the thesis load, range over blocks):

| Method | Extra CPU as % of 18 vCPU |
|---|---|
| Hubble | 0.14 to 0.88% |
| Otterize | 0.39 to 1.10% |
| IG `trace_tcp` | 0.75 to 0.90% (2.3% on host B) |
| IG `snapshot_socket` | 0.65 to 0.78% (2.2% on host B) |
| Hubble, Otterize and IG `trace_tcp` together (the thesis set-up) | 1.3 to 2.4% (3.3 to 4.0% on host B) |

The OVH CPU type of `test-cluster` is unknown, so this is a range, not one number. The last row adds the three costs, which assumes they do not interact. It counts cost caused by the apps only. The Ankra platform and its monitoring added more traffic, which is not in these numbers.

## When the method is stressed (RQ2)

- **Hubble loses events.** Mean per Hubble run: none in the steady window for Boutique, OTel and TeaStore; 6 to 37 for Bank; about 100 for DSB. Over a whole run, including the fixed-count tests, the block means are 64 to 205 lost events per run (single runs 59 to 261). These counts are small but not zero. A lost event is a flow the generated policy never sees.
- **The OTel services run out of memory.** At their thesis memory limits, the Java and .NET services restart under the fixed-count load (25 retried attempts across the two OTel blocks). They never restarted at the thesis load.
- **Gap:** no test broke a capture method on purpose. If RQ2 needs one, it still has to be run.

## Limitations

- **The agent-only gap is closed.** The main "Hubble" condition is the full stack. The default install (agent only) was measured separately, in the section above.
- **Host type was not controlled.** Three host types appeared. IG's cost depends on the host, so every cost is stated per host type.
- **The IG host effect is a hypothesis.** Software protection makes system calls dearer, and the gadget agent makes many. No system-call count was taken to test this.
- **Smaller cluster.** Two workers instead of three, and no Ankra platform, Prometheus, Kyverno or Trivy running beside the apps.
- **Shared node.** The load generator and the capture clients run on the 2-vCPU control-plane node. In the thesis the clients ran on a laptop. For Hubble this applies to the full stack only, because agent-only has no client. The full-stack slowdown may therefore include the client and the load generator competing for that node. The experiment cannot tell.
- **Agent-only: Intel blocks give wide bounds.** Boutique, Bank and OTel ran on Intel hosts, where the baseline test time varies by 10% to 17% between cycles. Their upper bounds are 9% to 28%, so "no detectable slowdown" there does not exclude a slowdown of that size.
- **Agent-only: one block per app.** Each app has 12 cycles on one host type. The experiment cannot show whether Hubble's cost depends on the host type.
- **Agent-only: the opt-in parts are not separated.** The metrics server, Relay and the streaming client were always switched on together. The experiment cannot say which one slows an app.
- **Agent-only: one setting.** Aggregation stayed at `medium` (the Helm default) and the Cilium version was 1.19.5. Other aggregation levels, other settings and other versions were not tested.
- **Agent-only against full stack is a secondary contrast.** It has no Holm correction and no sensitivity checks. Only three of the ten fixed-count cells are clear (DSB both modes, TeaStore new connection).
- **One short fixed-count test per mode and cycle.** GoLeash used 10,000 requests and 10 repetitions. Here each cell has 10 tests. The request count differs per app, so compare percentages only.
- **Why the apps differ is only partly explained.** Boutique, Bank and DSB are limited by container CPU quotas. OTel and TeaStore are not throttled, so we call them node-bound. TeaStore takes 49 s on every host, so its limit may not be CPU at all.
- **OTel differs from the thesis capture.** `prometheus-server` was kept at zero replicas, so OTel event rates are lower than in the thesis.
- **No latency result.** The steady window runs at only about 2 requests per second, so its latency numbers are too coarse to quote. Latency of the fixed-count tests was recorded in the stored logs but is not summarised.
- **Host speed correction failed.** A fixed CPU task on each node did not track the drift (correlation 0.41), so no correction is applied. The cycle design is the only defence.
- **Standard deviations.** The tables show confidence intervals. The SD of CPU and memory (across cycles and inside the window) is in each block's `RESULTS-CYCLES.md`.

## Where things are

- Combined report and CSV files: `COMBINED/` (`RESULTS-COMBINED.md`, `table5_combined.csv`, `resources_combined.csv`).
- Per block: `<block>-final/results/analysis/cycles/RESULTS-CYCLES.md`, with raw data in the same folder.
- Agent-only experiment: `../PERF-AGENTONLY-20261005/` (`AGENT-ONLY-SUMMARY.md`, `agent_only_summary.csv`). Per app: `ao-<app>-final/results/analysis/cycles/` (`RESULTS-CYCLES.md`, `paired_deltas.csv`, `table5_fixed_count.csv`).
- Earlier evidence for the drift problem: `../PERF-FULL-20261002/` (3 long repetitions) and `../PERF-DRIFT-20261003/` (drift probe).
- Harness, decisions and per-block log: `../../perf-benchmark/` (`FIXLOG.md`, `ops/HANDOFF.md`). The agent-only design is declared in `FIXLOG.md` (2026-10-05) and its result is logged there (2026-10-06).
