# Agent-only Hubble experiment: summary

Conditions per cycle: baseline (Hubble off), full Hubble (agent + metrics + Relay + streaming client) and **agent-only Hubble** (Hubble on in the Cilium agent, no metrics server, no Relay, no client: the Helm default). 12 cycles per app on one fresh play, all 6 orders twice. Each cell is the mean of the paired per-cycle differences with its 95% CI over cycles; n.s. = the interval includes zero. One block per app, never pooled across host types.

## Runs

| App | Host | Runs done | Cycles with agent-only |
|---|---|---|---|
| Online Boutique | Intel 1997 MHz | 36 | 12 |
| Bank of Anthos | Intel 1997 MHz | 36 | 12 |
| DSB social network | AMD EPYC 4192 MHz | 36 | 12 |
| OpenTelemetry demo | Intel 1997 MHz | 36 | 12 |
| TeaStore | AMD EPYC 4192 MHz | 36 | 12 |

## Agent-only Hubble against baseline (headline)

Pre-declared primary endpoints: observer CPU (cores), observer anonymous memory (MiB), fixed-count time (%, keep-alive and new connection). Verdict: robust / fragile / n.s. as in the main study (Holm over the two techniques, median/Wilcoxon, without the first run).

| App | Δ observer CPU (cores) | Δ anon memory (MiB) | Fixed-count, keep-alive | Fixed-count, new connection |
|---|---|---|---|---|
| Online Boutique | +0.010 [+0.008, +0.012] robust | +33 [+30, +36] robust | -2.1% [-12.9, +8.7] n.s. (primary) | +5.3% [-8.0, +18.5] n.s. (primary) |
| Bank of Anthos | +0.018 [+0.014, +0.022] robust | +43 [+40, +46] robust | +5.1% [-6.9, +17.1] n.s. (primary) | +7.2% [-1.3, +15.7] n.s. (primary) |
| DSB social network | +0.017 [+0.016, +0.018] robust | +32 [+30, +34] robust | +0.1% [-4.6, +4.9] n.s. (primary) | -2.5% [-20.7, +15.7] n.s. (primary) |
| OpenTelemetry demo | +0.017 [+0.014, +0.020] robust | +46 [+44, +49] robust | +6.1% [-13.6, +25.9] n.s. (primary) | +7.8% [-12.0, +27.6] n.s. (primary) |
| TeaStore | +0.008 [+0.007, +0.009] robust | +20 [+18, +23] robust | -0.6% [-5.1, +4.0] n.s. (primary) | -0.1% [-4.7, +4.5] n.s. (primary) |

## Agent-only against the full Hubble stack (same cycles; secondary)

Agent-only minus full stack. A negative number means the agent-only setup uses less. The last column is the agent-only share of the full stack's extra observer CPU over baseline.

| App | Δ observer CPU (cores) | Δ anon memory (MiB) | Fixed-count, keep-alive | Fixed-count, new connection | Agent-only share of extra CPU |
|---|---|---|---|---|---|
| Online Boutique | -0.027 [-0.035, -0.020] | -66 [-70, -62] | +0.9% [-13.3, +15.0] (n.s.) | +0.4% [-10.2, +11.0] (n.s.) | 27% |
| Bank of Anthos | -0.065 [-0.072, -0.058] | -67 [-71, -64] | +0.2% [-11.4, +11.7] (n.s.) | -3.9% [-11.0, +3.2] (n.s.) | 22% |
| DSB social network | -0.106 [-0.108, -0.104] | -80 [-82, -79] | -10.4% [-12.3, -8.5] | -8.2% [-12.7, -3.7] | 14% |
| OpenTelemetry demo | -0.050 [-0.052, -0.047] | -67 [-71, -63] | -3.4% [-21.4, +14.6] (n.s.) | -10.2% [-23.7, +3.4] (n.s.) | 25% |
| TeaStore | -0.020 [-0.021, -0.018] | -64 [-66, -62] | -1.3% [-5.8, +3.3] (n.s.) | -17.5% [-21.0, -13.9] | 29% |

## How to read this (shared guide for every document that quotes it)

- **Hosts differ.** Boutique, Bank and OTel ran on Intel Xeon 2.0 GHz hosts; DSB and TeaStore on AMD EPYC 4.2 GHz hosts.
  Intervals on the Intel blocks are wide (the baseline fixed-count time varies 10% to 17% between cycles in these
  blocks), so they cannot rule out a throughput effect of up to about 9% (Boutique keep-alive, +8.7%) to 28% (OTel,
  +27.6% with a new connection per request). TeaStore (AMD) is the tightest block:
  agent-only Hubble costs less than +4.5% in both modes. DSB (AMD): less than +4.9% with keep-alive, wide
  with a new connection per request (up to +15.7%).
- **Headline.** The default install (Hubble in the agent only) costs +0.008 to +0.018 cores and +20 to +46 MiB of
  anonymous memory, robust in all five apps. It shows **no detectable fixed-count slowdown in any app** (every
  interval includes zero). Say "no detectable slowdown, upper bound X%" with the per-app bound, never "no overhead".
- **Full stack against agent-only, same cycles.** Where the intervals are tight, the full stack is slower than
  agent-only: DSB -8% to -10% (agent-only minus full) and TeaStore -17.5% with a new connection per request. So on DSB and TeaStore,
  where the intervals are tight, the slowdown comes from the opt-in parts (metrics server, Relay, streaming
  `hubble observe` client), not from Hubble in the agent. On Boutique, Bank and OTel the agent-only upper bounds
  (8.7% to 27.6%) cannot exclude a slowdown as large as the full stack's, so those three are not attributed. The experiment does not separate those three parts, and the client ran on the
  same 2-vCPU node as the load generator. Do not attribute the slowdown to any single opt-in part.
- **CPU shares.** Agent-only is 14% to 29% of the full stack's extra observer CPU. The agent's own CPU inside the full
  stack (41% to 47%, from the main study) is higher because enabling the metrics server adds work inside the agent.
- **Design.** 12 cycles per app, one fresh play each, baseline / full Hubble / agent-only in all 6 orders twice.
  36 runs per app, 180 in total, 0 failed runs. Retried attempts: Boutique 0, Bank 0, DSB 1, OTel 5, TeaStore 1.
  The first `hubble_agent` switch failed on two plays because of a verification race (Hubble reported Warning for a few
  seconds after the agent restart); fixed on 2026-10-05 (FIXLOG).
- **Config.** Agent-only keeps the cluster's `monitor-aggregation: medium` (also the Helm default); Cilium 1.19.5.
