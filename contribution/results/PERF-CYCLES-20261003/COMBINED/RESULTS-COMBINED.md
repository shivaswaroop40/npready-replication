# Capture overhead: combined results over all blocks

One row per (app, block). Blocks are not pooled because the host types differ (CPU speed and Spectre mitigation). Every Δ is the mean of the per-cycle paired differences (technique minus the same cycle's baseline) with its 95% CI over the block's 10 cycles. Verdict: 'robust' = significant after Holm and in both pre-declared checks (median/Wilcoxon, and without the block's first run); 'fragile' = significant after Holm only; 'n.s.' = not significant after Holm, with the upper 95% bound as the most the effect can be.

## Blocks

| Block | App | Cycles | Host type | Runs done | Retried attempts |
|---|---|---|---|---|---|
| boutique-b1 | Online Boutique | 1-10 | Intel Xeon Processor 1997 MHz, hardware (IBRS) | 50 | 1 |
| boutique-b2 | Online Boutique | 11-20 | AMD EPYC 2495 MHz, software (retpolines) | 50 | 0 |
| bank-b1 | Bank of Anthos | 1-10 | AMD EPYC 2495 MHz, software (retpolines) | 50 | 0 |
| bank-b2 | Bank of Anthos | 11-20 | AMD EPYC 4192 MHz, hardware (IBRS) | 50 | 0 |
| dsb-b1 | DSB social network | 1-10 | Intel Xeon Processor 1997 MHz, hardware (IBRS) | 50 | 2 |
| dsb-b2 | DSB social network | 11-20 | AMD EPYC 4192 MHz, hardware (IBRS) | 50 | 5 |
| otel-b1 | OpenTelemetry demo | 1-10 | Intel Xeon Processor 1997 MHz, hardware (IBRS) | 50 | 13 |
| otel-b2 | OpenTelemetry demo | 11-20 | AMD EPYC 4192 MHz, hardware (IBRS) | 50 | 12 |
| teastore-b1 | TeaStore | 1-10 | Intel Xeon Processor 1997 MHz, hardware (IBRS) | 50 | 1 |
| teastore-b2 | TeaStore | 11-20 | AMD EPYC 4192 MHz, hardware (IBRS) | 50 | 0 |

## Fixed-count time (GoLeash Table 5 format)

Time to finish TP_N requests at concurrency 16 (per app: boutique 3008, bank 608, dsb 1504, otel 7040, teastore 9152), one test per mode per cycle. w/o and with: mean ± SD over the block's 10 executions. Overhead: paired per-cycle % difference [95% CI].

| App | Block | Mode | Technique | w/o (s) | with (s) | Overhead [95% CI] | Verdict |
|---|---|---|---|---|---|---|---|
| Online Boutique | boutique-b1 | keep-alive | Hubble | 41.94 ± 9.12 | 40.62 ± 7.78 | -0.8% [-14.6, +13.0] | n.s. (< +13.0%) |
| Online Boutique | boutique-b1 | keep-alive | Otterize | 41.94 ± 9.12 | 41.33 ± 5.44 | +3.6% [-18.3, +25.4] | n.s. (< +25.4%) |
| Online Boutique | boutique-b1 | keep-alive | IG trace_tcp | 41.94 ± 9.12 | 38.45 ± 7.41 | -5.0% [-22.9, +13.0] | n.s. (< +13.0%) |
| Online Boutique | boutique-b1 | keep-alive | IG snapshot_socket | 41.94 ± 9.12 | 37.88 ± 6.14 | -6.6% [-20.7, +7.5] | n.s. (< +7.5%) |
| Online Boutique | boutique-b1 | new conn | Hubble | 37.37 ± 6.56 | 38.72 ± 6.17 | +5.2% [-6.7, +17.1] | n.s. (< +17.1%) |
| Online Boutique | boutique-b1 | new conn | Otterize | 37.37 ± 6.56 | 37.22 ± 7.43 | +3.2% [-19.8, +26.2] | n.s. (< +26.2%) |
| Online Boutique | boutique-b1 | new conn | IG trace_tcp | 37.37 ± 6.56 | 37.17 ± 5.51 | +1.7% [-12.9, +16.4] | n.s. (< +16.4%) |
| Online Boutique | boutique-b1 | new conn | IG snapshot_socket | 37.37 ± 6.56 | 36.68 ± 5.96 | -0.1% [-13.5, +13.3] | n.s. (< +13.3%) |
| Online Boutique | boutique-b2 | keep-alive | Hubble | 66.36 ± 2.33 | 66.99 ± 2.44 | +1.1% [-2.7, +4.8] | n.s. (< +4.8%) |
| Online Boutique | boutique-b2 | keep-alive | Otterize | 66.36 ± 2.33 | 65.48 ± 2.44 | -1.3% [-4.1, +1.5] | n.s. (< +1.5%) |
| Online Boutique | boutique-b2 | keep-alive | IG trace_tcp | 66.36 ± 2.33 | 66.94 ± 1.80 | +1.0% [-2.6, +4.6] | n.s. (< +4.6%) |
| Online Boutique | boutique-b2 | keep-alive | IG snapshot_socket | 66.36 ± 2.33 | 66.11 ± 2.78 | -0.3% [-3.3, +2.6] | n.s. (< +2.6%) |
| Online Boutique | boutique-b2 | new conn | Hubble | 65.19 ± 2.01 | 69.73 ± 2.82 | +7.1% [+3.0, +11.2] | robust |
| Online Boutique | boutique-b2 | new conn | Otterize | 65.19 ± 2.01 | 66.77 ± 2.56 | +2.5% [-0.6, +5.5] | n.s. (< +5.5%) |
| Online Boutique | boutique-b2 | new conn | IG trace_tcp | 65.19 ± 2.01 | 66.62 ± 1.82 | +2.3% [-1.0, +5.7] | n.s. (< +5.7%) |
| Online Boutique | boutique-b2 | new conn | IG snapshot_socket | 65.19 ± 2.01 | 66.68 ± 2.37 | +2.4% [-1.0, +5.8] | n.s. (< +5.8%) |
| Bank of Anthos | bank-b1 | keep-alive | Hubble | 49.98 ± 1.29 | 54.89 ± 1.72 | +9.9% [+6.6, +13.2] | robust |
| Bank of Anthos | bank-b1 | keep-alive | Otterize | 49.98 ± 1.29 | 51.19 ± 1.62 | +2.4% [-0.0, +4.9] | n.s. (< +4.9%) |
| Bank of Anthos | bank-b1 | keep-alive | IG trace_tcp | 49.98 ± 1.29 | 53.23 ± 1.48 | +6.5% [+4.3, +8.8] | robust |
| Bank of Anthos | bank-b1 | keep-alive | IG snapshot_socket | 49.98 ± 1.29 | 51.59 ± 1.86 | +3.2% [+1.0, +5.5] | robust |
| Bank of Anthos | bank-b1 | new conn | Hubble | 51.37 ± 1.27 | 56.26 ± 1.89 | +9.6% [+6.1, +13.1] | robust |
| Bank of Anthos | bank-b1 | new conn | Otterize | 51.37 ± 1.27 | 52.02 ± 1.59 | +1.3% [-1.2, +3.8] | n.s. (< +3.8%) |
| Bank of Anthos | bank-b1 | new conn | IG trace_tcp | 51.37 ± 1.27 | 54.43 ± 1.98 | +6.0% [+3.2, +8.7] | robust |
| Bank of Anthos | bank-b1 | new conn | IG snapshot_socket | 51.37 ± 1.27 | 51.82 ± 2.15 | +0.9% [-1.0, +2.8] | n.s. (< +2.8%) |
| Bank of Anthos | bank-b2 | keep-alive | Hubble | 13.93 ± 0.57 | 16.63 ± 0.56 | +19.6% [+15.3, +23.8] | robust |
| Bank of Anthos | bank-b2 | keep-alive | Otterize | 13.93 ± 0.57 | 14.66 ± 0.82 | +5.3% [+1.6, +8.9] | robust |
| Bank of Anthos | bank-b2 | keep-alive | IG trace_tcp | 13.93 ± 0.57 | 15.35 ± 0.66 | +10.3% [+5.7, +15.0] | robust |
| Bank of Anthos | bank-b2 | keep-alive | IG snapshot_socket | 13.93 ± 0.57 | 14.24 ± 0.63 | +2.4% [-2.3, +7.1] | n.s. (< +7.1%) |
| Bank of Anthos | bank-b2 | new conn | Hubble | 14.54 ± 0.74 | 17.24 ± 0.73 | +18.9% [+12.5, +25.2] | robust |
| Bank of Anthos | bank-b2 | new conn | Otterize | 14.54 ± 0.74 | 14.96 ± 0.38 | +3.1% [-1.6, +7.9] | n.s. (< +7.9%) |
| Bank of Anthos | bank-b2 | new conn | IG trace_tcp | 14.54 ± 0.74 | 15.90 ± 0.44 | +9.6% [+5.0, +14.2] | robust |
| Bank of Anthos | bank-b2 | new conn | IG snapshot_socket | 14.54 ± 0.74 | 14.78 ± 0.55 | +1.9% [-3.3, +7.2] | n.s. (< +7.2%) |
| DSB social network | dsb-b1 | keep-alive | Hubble | 50.10 ± 7.05 | 53.95 ± 6.07 | +10.2% [-6.2, +26.6] | n.s. (< +26.6%) |
| DSB social network | dsb-b1 | keep-alive | Otterize | 50.10 ± 7.05 | 50.23 ± 10.45 | +1.4% [-16.1, +19.0] | n.s. (< +19.0%) |
| DSB social network | dsb-b1 | keep-alive | IG trace_tcp | 50.10 ± 7.05 | 47.78 ± 5.41 | -3.8% [-12.0, +4.5] | n.s. (< +4.5%) |
| DSB social network | dsb-b1 | keep-alive | IG snapshot_socket | 50.10 ± 7.05 | 47.74 ± 4.29 | -3.1% [-14.1, +7.9] | n.s. (< +7.9%) |
| DSB social network | dsb-b1 | new conn | Hubble | 53.86 ± 7.42 | 55.60 ± 5.90 | +5.1% [-7.9, +18.1] | n.s. (< +18.1%) |
| DSB social network | dsb-b1 | new conn | Otterize | 53.86 ± 7.42 | 52.35 ± 4.95 | -1.4% [-12.4, +9.5] | n.s. (< +9.5%) |
| DSB social network | dsb-b1 | new conn | IG trace_tcp | 53.86 ± 7.42 | 49.64 ± 9.43 | -6.7% [-21.1, +7.7] | n.s. (< +7.7%) |
| DSB social network | dsb-b1 | new conn | IG snapshot_socket | 53.86 ± 7.42 | 50.02 ± 6.14 | -5.5% [-17.3, +6.3] | n.s. (< +6.3%) |
| DSB social network | dsb-b2 | keep-alive | Hubble | 18.12 ± 2.10 | 19.06 ± 1.48 | +6.0% [-1.1, +13.0] | n.s. (< +13.0%) |
| DSB social network | dsb-b2 | keep-alive | Otterize | 18.12 ± 2.10 | 18.79 ± 1.60 | +4.4% [-2.4, +11.2] | n.s. (< +11.2%) |
| DSB social network | dsb-b2 | keep-alive | IG trace_tcp | 18.12 ± 2.10 | 18.92 ± 0.95 | +5.3% [-1.8, +12.5] | n.s. (< +12.5%) |
| DSB social network | dsb-b2 | keep-alive | IG snapshot_socket | 18.12 ± 2.10 | 18.36 ± 1.33 | +2.1% [-4.5, +8.7] | n.s. (< +8.7%) |
| DSB social network | dsb-b2 | new conn | Hubble | 20.20 ± 1.92 | 23.03 ± 1.30 | +14.4% [+10.0, +18.8] | robust |
| DSB social network | dsb-b2 | new conn | Otterize | 20.20 ± 1.92 | 20.24 ± 1.30 | +0.6% [-4.0, +5.1] | n.s. (< +5.1%) |
| DSB social network | dsb-b2 | new conn | IG trace_tcp | 20.20 ± 1.92 | 21.52 ± 0.85 | +7.1% [+1.6, +12.7] | n.s. (< +12.7%) |
| DSB social network | dsb-b2 | new conn | IG snapshot_socket | 20.20 ± 1.92 | 19.89 ± 1.73 | -1.4% [-4.6, +1.9] | n.s. (< +1.9%) |
| OpenTelemetry demo | otel-b1 | keep-alive | Hubble | 41.11 ± 8.08 | 40.37 ± 8.58 | +3.1% [-21.9, +28.1] | n.s. (< +28.1%) |
| OpenTelemetry demo | otel-b1 | keep-alive | Otterize | 41.11 ± 8.08 | 41.45 ± 7.40 | +6.2% [-20.0, +32.5] | n.s. (< +32.5%) |
| OpenTelemetry demo | otel-b1 | keep-alive | IG trace_tcp | 41.11 ± 8.08 | 33.11 ± 3.76 | -17.0% [-30.0, -4.0] | n.s. (< -4.0%) |
| OpenTelemetry demo | otel-b1 | keep-alive | IG snapshot_socket | 41.11 ± 8.08 | 34.74 ± 5.40 | -12.4% [-27.9, +3.0] | n.s. (< +3.0%) |
| OpenTelemetry demo | otel-b1 | new conn | Hubble | 45.52 ± 7.87 | 50.65 ± 9.13 | +15.4% [-7.6, +38.4] | n.s. (< +38.4%) |
| OpenTelemetry demo | otel-b1 | new conn | Otterize | 45.52 ± 7.87 | 46.27 ± 8.69 | +6.0% [-18.7, +30.7] | n.s. (< +30.7%) |
| OpenTelemetry demo | otel-b1 | new conn | IG trace_tcp | 45.52 ± 7.87 | 43.20 ± 4.90 | -3.2% [-14.7, +8.3] | n.s. (< +8.3%) |
| OpenTelemetry demo | otel-b1 | new conn | IG snapshot_socket | 45.52 ± 7.87 | 39.41 ± 5.52 | -11.3% [-23.8, +1.2] | n.s. (< +1.2%) |
| OpenTelemetry demo | otel-b2 | keep-alive | Hubble | 30.93 ± 1.78 | 35.49 ± 4.59 | +15.2% [+2.5, +28.0] | n.s. (< +28.0%) |
| OpenTelemetry demo | otel-b2 | keep-alive | Otterize | 30.93 ± 1.78 | 37.17 ± 3.27 | +20.2% [+14.0, +26.5] | robust |
| OpenTelemetry demo | otel-b2 | keep-alive | IG trace_tcp | 30.93 ± 1.78 | 36.22 ± 5.68 | +17.4% [+3.3, +31.6] | n.s. (< +31.6%) |
| OpenTelemetry demo | otel-b2 | keep-alive | IG snapshot_socket | 30.93 ± 1.78 | 31.74 ± 4.63 | +3.2% [-9.7, +16.1] | n.s. (< +16.1%) |
| OpenTelemetry demo | otel-b2 | new conn | Hubble | 36.12 ± 5.03 | 46.30 ± 3.76 | +30.3% [+15.6, +45.0] | robust |
| OpenTelemetry demo | otel-b2 | new conn | Otterize | 36.12 ± 5.03 | 42.57 ± 7.74 | +19.6% [+0.5, +38.7] | n.s. (< +38.7%) |
| OpenTelemetry demo | otel-b2 | new conn | IG trace_tcp | 36.12 ± 5.03 | 41.33 ± 6.87 | +16.6% [-1.7, +34.9] | n.s. (< +34.9%) |
| OpenTelemetry demo | otel-b2 | new conn | IG snapshot_socket | 36.12 ± 5.03 | 37.96 ± 6.03 | +7.8% [-11.4, +27.0] | n.s. (< +27.0%) |
| TeaStore | teastore-b1 | keep-alive | Hubble | 49.09 ± 3.42 | 47.00 ± 8.20 | -4.1% [-16.3, +8.0] | n.s. (< +8.0%) |
| TeaStore | teastore-b1 | keep-alive | Otterize | 49.09 ± 3.42 | 40.01 ± 10.52 | -18.0% [-34.3, -1.8] | n.s. (< -1.8%) |
| TeaStore | teastore-b1 | keep-alive | IG trace_tcp | 49.09 ± 3.42 | 48.22 ± 2.41 | -1.3% [-7.6, +5.0] | n.s. (< +5.0%) |
| TeaStore | teastore-b1 | keep-alive | IG snapshot_socket | 49.09 ± 3.42 | 48.75 ± 4.65 | -0.4% [-8.1, +7.3] | n.s. (< +7.3%) |
| TeaStore | teastore-b1 | new conn | Hubble | 49.32 ± 3.38 | 56.87 ± 8.38 | +15.5% [+2.9, +28.2] | n.s. (< +28.2%) |
| TeaStore | teastore-b1 | new conn | Otterize | 49.32 ± 3.38 | 40.43 ± 10.46 | -17.6% [-33.6, -1.6] | n.s. (< -1.6%) |
| TeaStore | teastore-b1 | new conn | IG trace_tcp | 49.32 ± 3.38 | 49.13 ± 2.65 | +0.1% [-6.7, +6.9] | n.s. (< +6.9%) |
| TeaStore | teastore-b1 | new conn | IG snapshot_socket | 49.32 ± 3.38 | 48.61 ± 4.68 | -1.1% [-8.8, +6.5] | n.s. (< +6.5%) |
| TeaStore | teastore-b2 | keep-alive | Hubble | 49.19 ± 4.07 | 51.49 ± 3.48 | +5.4% [-3.5, +14.4] | n.s. (< +14.4%) |
| TeaStore | teastore-b2 | keep-alive | Otterize | 49.19 ± 4.07 | 48.83 ± 3.07 | -0.3% [-6.2, +5.6] | n.s. (< +5.6%) |
| TeaStore | teastore-b2 | keep-alive | IG trace_tcp | 49.19 ± 4.07 | 50.11 ± 2.74 | +2.4% [-3.7, +8.5] | n.s. (< +8.5%) |
| TeaStore | teastore-b2 | keep-alive | IG snapshot_socket | 49.19 ± 4.07 | 45.63 ± 7.68 | -7.1% [-18.1, +3.9] | n.s. (< +3.9%) |
| TeaStore | teastore-b2 | new conn | Hubble | 49.18 ± 3.95 | 61.40 ± 3.59 | +25.7% [+15.9, +35.5] | robust |
| TeaStore | teastore-b2 | new conn | Otterize | 49.18 ± 3.95 | 48.92 ± 3.09 | -0.1% [-5.8, +5.5] | n.s. (< +5.5%) |
| TeaStore | teastore-b2 | new conn | IG trace_tcp | 49.18 ± 3.95 | 51.23 ± 2.84 | +4.7% [-1.6, +10.9] | n.s. (< +10.9%) |
| TeaStore | teastore-b2 | new conn | IG snapshot_socket | 49.18 ± 3.95 | 45.67 ± 7.50 | -7.1% [-17.7, +3.5] | n.s. (< +3.5%) |

## Resource cost at the thesis load (steady window)

Δ observer CPU (cores) and Δ observer anonymous memory (MiB): the capture components and their clients, technique minus baseline, at each app's thesis journey-A load.

| App | Block | Technique | Δ observer CPU (cores) | Verdict | Δ anon memory (MiB) | Verdict |
|---|---|---|---|---|---|---|
| Online Boutique | boutique-b1 | Hubble | +0.050 [+0.041, +0.058] | robust | +91 [+88, +94] | robust |
| Online Boutique | boutique-b1 | Otterize | +0.052 [+0.047, +0.057] | robust | +79 [+76, +82] | robust |
| Online Boutique | boutique-b1 | IG trace_tcp | +0.078 [+0.073, +0.082] | robust | +133 [+128, +137] | robust |
| Online Boutique | boutique-b1 | IG snapshot_socket | +0.071 [+0.064, +0.077] | robust | +111 [+109, +113] | robust |
| Online Boutique | boutique-b2 | Hubble | +0.062 [+0.060, +0.063] | robust | +98 [+95, +101] | robust |
| Online Boutique | boutique-b2 | Otterize | +0.087 [+0.085, +0.088] | robust | +80 [+78, +82] | robust |
| Online Boutique | boutique-b2 | IG trace_tcp | +0.216 [+0.213, +0.219] | robust | +135 [+132, +138] | robust |
| Online Boutique | boutique-b2 | IG snapshot_socket | +0.211 [+0.207, +0.214] | robust | +114 [+110, +119] | robust |
| Bank of Anthos | bank-b1 | Hubble | +0.134 [+0.129, +0.140] | robust | +105 [+103, +108] | robust |
| Bank of Anthos | bank-b1 | Otterize | +0.141 [+0.139, +0.144] | robust | +81 [+78, +83] | robust |
| Bank of Anthos | bank-b1 | IG trace_tcp | +0.231 [+0.227, +0.234] | robust | +145 [+140, +149] | robust |
| Bank of Anthos | bank-b1 | IG snapshot_socket | +0.210 [+0.206, +0.214] | robust | +109 [+106, +112] | robust |
| Bank of Anthos | bank-b2 | Hubble | +0.047 [+0.045, +0.048] | robust | +106 [+103, +110] | robust |
| Bank of Anthos | bank-b2 | Otterize | +0.070 [+0.069, +0.071] | robust | +82 [+80, +85] | robust |
| Bank of Anthos | bank-b2 | IG trace_tcp | +0.078 [+0.075, +0.080] | robust | +143 [+137, +149] | robust |
| Bank of Anthos | bank-b2 | IG snapshot_socket | +0.070 [+0.067, +0.072] | robust | +113 [+110, +116] | robust |
| DSB social network | dsb-b1 | Hubble | +0.225 [+0.175, +0.276] | robust | +108 [+103, +113] | robust |
| DSB social network | dsb-b1 | Otterize | +0.088 [+0.081, +0.095] | robust | +81 [+79, +83] | robust |
| DSB social network | dsb-b1 | IG trace_tcp | +0.122 [+0.104, +0.139] | robust | +150 [+148, +152] | robust |
| DSB social network | dsb-b1 | IG snapshot_socket | +0.061 [+0.055, +0.066] | robust | +117 [+113, +121] | robust |
| DSB social network | dsb-b2 | Hubble | +0.106 [+0.085, +0.128] | robust | +110 [+106, +114] | robust |
| DSB social network | dsb-b2 | Otterize | +0.090 [+0.081, +0.099] | robust | +80 [+78, +83] | robust |
| DSB social network | dsb-b2 | IG trace_tcp | +0.096 [+0.089, +0.103] | robust | +150 [+145, +155] | robust |
| DSB social network | dsb-b2 | IG snapshot_socket | +0.071 [+0.064, +0.078] | robust | +116 [+113, +118] | robust |
| OpenTelemetry demo | otel-b1 | Hubble | +0.075 [+0.064, +0.086] | robust | +111 [+108, +115] | robust |
| OpenTelemetry demo | otel-b1 | Otterize | +0.061 [+0.055, +0.066] | robust | +82 [+79, +85] | robust |
| OpenTelemetry demo | otel-b1 | IG trace_tcp | +0.070 [+0.064, +0.076] | robust | +134 [+130, +137] | robust |
| OpenTelemetry demo | otel-b1 | IG snapshot_socket | +0.066 [+0.061, +0.070] | robust | +115 [+110, +119] | robust |
| OpenTelemetry demo | otel-b2 | Hubble | +0.035 [+0.034, +0.037] | robust | +112 [+109, +116] | robust |
| OpenTelemetry demo | otel-b2 | Otterize | +0.065 [+0.063, +0.067] | robust | +81 [+79, +82] | robust |
| OpenTelemetry demo | otel-b2 | IG trace_tcp | +0.069 [+0.068, +0.071] | robust | +135 [+132, +138] | robust |
| OpenTelemetry demo | otel-b2 | IG snapshot_socket | +0.069 [+0.068, +0.070] | robust | +115 [+112, +118] | robust |
| TeaStore | teastore-b1 | Hubble | +0.046 [+0.042, +0.050] | robust | +86 [+81, +90] | robust |
| TeaStore | teastore-b1 | Otterize | +0.048 [+0.043, +0.053] | robust | +81 [+79, +83] | robust |
| TeaStore | teastore-b1 | IG trace_tcp | +0.073 [+0.070, +0.077] | robust | +134 [+126, +142] | robust |
| TeaStore | teastore-b1 | IG snapshot_socket | +0.063 [+0.059, +0.068] | robust | +110 [+107, +113] | robust |
| TeaStore | teastore-b2 | Hubble | +0.031 [+0.026, +0.035] | robust | +87 [+85, +90] | robust |
| TeaStore | teastore-b2 | Otterize | +0.055 [+0.047, +0.062] | robust | +81 [+77, +85] | robust |
| TeaStore | teastore-b2 | IG trace_tcp | +0.081 [+0.072, +0.090] | robust | +137 [+133, +142] | robust |
| TeaStore | teastore-b2 | IG snapshot_socket | +0.074 [+0.067, +0.081] | robust | +111 [+108, +114] | robust |

## Cost under load (new-connection fixed-count tests)

Δ observer CPU and Δ node busy CPU (all nodes, cores) while the app serves one new TCP connection per request as fast as it can.

| App | Block | Technique | Δ observer CPU | Δ node busy CPU |
|---|---|---|---|---|
| Online Boutique | boutique-b1 | Hubble | +0.458 [+0.419, +0.498] | +0.588 [+0.500, +0.676] |
| Online Boutique | boutique-b1 | Otterize | +0.064 [+0.050, +0.078] | +0.052 [+0.020, +0.083] |
| Online Boutique | boutique-b1 | IG trace_tcp | +0.176 [+0.156, +0.197] | +0.301 [+0.200, +0.401] |
| Online Boutique | boutique-b1 | IG snapshot_socket | +0.082 [+0.066, +0.098] | +0.116 [+0.059, +0.173] |
| Online Boutique | boutique-b2 | Hubble | +0.592 [+0.576, +0.608] | +0.750 [+0.677, +0.823] |
| Online Boutique | boutique-b2 | Otterize | +0.118 [+0.114, +0.121] | +0.108 [+0.052, +0.164] |
| Online Boutique | boutique-b2 | IG trace_tcp | +0.317 [+0.313, +0.322] | +0.473 [+0.399, +0.548] |
| Online Boutique | boutique-b2 | IG snapshot_socket | +0.202 [+0.196, +0.208] | +0.195 [+0.138, +0.253] |
| Bank of Anthos | bank-b1 | Hubble | +0.724 [+0.679, +0.768] | +0.954 [+0.897, +1.010] |
| Bank of Anthos | bank-b1 | Otterize | +0.198 [+0.192, +0.204] | +0.165 [+0.125, +0.206] |
| Bank of Anthos | bank-b1 | IG trace_tcp | +0.345 [+0.338, +0.351] | +0.573 [+0.543, +0.602] |
| Bank of Anthos | bank-b1 | IG snapshot_socket | +0.202 [+0.197, +0.207] | +0.227 [+0.193, +0.260] |
| Bank of Anthos | bank-b2 | Hubble | +0.580 [+0.542, +0.617] | +0.801 [+0.694, +0.908] |
| Bank of Anthos | bank-b2 | Otterize | +0.117 [+0.110, +0.124] | +0.046 [-0.001, +0.092] |
| Bank of Anthos | bank-b2 | IG trace_tcp | +0.180 [+0.157, +0.204] | +0.377 [+0.267, +0.487] |
| Bank of Anthos | bank-b2 | IG snapshot_socket | +0.068 [+0.065, +0.072] | +0.093 [+0.031, +0.154] |
| DSB social network | dsb-b1 | Hubble | +0.378 [+0.341, +0.415] | +0.496 [+0.402, +0.590] |
| DSB social network | dsb-b1 | Otterize | +0.090 [+0.086, +0.094] | +0.107 [+0.080, +0.134] |
| DSB social network | dsb-b1 | IG trace_tcp | +0.154 [+0.138, +0.169] | +0.288 [+0.230, +0.345] |
| DSB social network | dsb-b1 | IG snapshot_socket | +0.058 [+0.053, +0.064] | +0.107 [+0.073, +0.142] |
| DSB social network | dsb-b2 | Hubble | +0.363 [+0.338, +0.387] | +0.480 [+0.424, +0.535] |
| DSB social network | dsb-b2 | Otterize | +0.093 [+0.086, +0.100] | +0.099 [+0.057, +0.141] |
| DSB social network | dsb-b2 | IG trace_tcp | +0.152 [+0.145, +0.159] | +0.258 [+0.203, +0.313] |
| DSB social network | dsb-b2 | IG snapshot_socket | +0.072 [+0.065, +0.080] | +0.095 [+0.047, +0.144] |
| OpenTelemetry demo | otel-b1 | Hubble | +0.766 [+0.701, +0.831] | +0.104 [-0.507, +0.715] |
| OpenTelemetry demo | otel-b1 | Otterize | +0.062 [+0.054, +0.069] | -0.097 [-1.036, +0.842] |
| OpenTelemetry demo | otel-b1 | IG trace_tcp | +0.295 [+0.279, +0.311] | +0.003 [-1.136, +1.141] |
| OpenTelemetry demo | otel-b1 | IG snapshot_socket | +0.082 [+0.077, +0.087] | -0.432 [-1.036, +0.171] |
| OpenTelemetry demo | otel-b2 | Hubble | +0.765 [+0.732, +0.798] | +1.403 [+0.475, +2.331] |
| OpenTelemetry demo | otel-b2 | Otterize | +0.094 [+0.089, +0.099] | +0.432 [-0.257, +1.121] |
| OpenTelemetry demo | otel-b2 | IG trace_tcp | +0.265 [+0.222, +0.308] | +0.024 [-0.805, +0.853] |
| OpenTelemetry demo | otel-b2 | IG snapshot_socket | +0.081 [+0.077, +0.085] | -0.032 [-0.834, +0.770] |
| TeaStore | teastore-b1 | Hubble | +0.599 [+0.548, +0.651] | +0.547 [+0.432, +0.661] |
| TeaStore | teastore-b1 | Otterize | +0.074 [+0.069, +0.080] | +0.152 [+0.047, +0.257] |
| TeaStore | teastore-b1 | IG trace_tcp | +0.195 [+0.173, +0.218] | +0.309 [+0.257, +0.361] |
| TeaStore | teastore-b1 | IG snapshot_socket | +0.064 [+0.060, +0.068] | +0.100 [+0.043, +0.157] |
| TeaStore | teastore-b2 | Hubble | +0.633 [+0.558, +0.708] | +0.706 [+0.552, +0.861] |
| TeaStore | teastore-b2 | Otterize | +0.104 [+0.093, +0.115] | +0.176 [+0.035, +0.317] |
| TeaStore | teastore-b2 | IG trace_tcp | +0.245 [+0.221, +0.270] | +0.561 [+0.423, +0.700] |
| TeaStore | teastore-b2 | IG snapshot_socket | +0.080 [+0.073, +0.087] | +0.486 [-0.133, +1.105] |

## Host type and Inspektor Gadget's own CPU

Steady-window CPU (cores) of the gadget DaemonSet pods and of cilium-agent at baseline. Hypothesis (FIXLOG, untested directly): hosts whose kernel mitigates Spectre v2 / retbleed in software (retpolines, return thunk) make the syscall-heavy gadget agent about 3x dearer.

| Block | Host type | gadget (ig_tcp) | gadget (ig_snap) | cilium-agent (baseline) |
|---|---|---|---|---|
| boutique-b1 | Intel Xeon Processor 1997 MHz, hardware (IBRS) | 0.074 | 0.071 | 0.082 |
| boutique-b2 | AMD EPYC 2495 MHz, software (retpolines) | 0.211 | 0.207 | 0.084 |
| bank-b1 | AMD EPYC 2495 MHz, software (retpolines) | 0.219 | 0.207 | 0.083 |
| bank-b2 | AMD EPYC 4192 MHz, hardware (IBRS) | 0.073 | 0.067 | 0.032 |
| dsb-b1 | Intel Xeon Processor 1997 MHz, hardware (IBRS) | 0.103 | 0.064 | 0.083 |
| dsb-b2 | AMD EPYC 4192 MHz, hardware (IBRS) | 0.088 | 0.071 | 0.039 |
| otel-b1 | Intel Xeon Processor 1997 MHz, hardware (IBRS) | 0.071 | 0.068 | 0.080 |
| otel-b2 | AMD EPYC 4192 MHz, hardware (IBRS) | 0.068 | 0.068 | 0.034 |
| teastore-b1 | Intel Xeon Processor 1997 MHz, hardware (IBRS) | 0.069 | 0.065 | 0.055 |
| teastore-b2 | AMD EPYC 4192 MHz, hardware (IBRS) | 0.077 | 0.072 | 0.038 |

## Throughput effects that survive every check

- bank-b1: Hubble slows the fixed-count test (keep-alive) by +9.9% [+6.6, +13.2]
- bank-b1: IG snapshot_socket slows the fixed-count test (keep-alive) by +3.2% [+1.0, +5.5]
- bank-b1: IG trace_tcp slows the fixed-count test (keep-alive) by +6.5% [+4.3, +8.8]
- bank-b1: Hubble slows the fixed-count test (new conn) by +9.6% [+6.1, +13.1]
- bank-b1: IG trace_tcp slows the fixed-count test (new conn) by +6.0% [+3.2, +8.7]
- bank-b2: Hubble slows the fixed-count test (keep-alive) by +19.6% [+15.3, +23.8]
- bank-b2: IG trace_tcp slows the fixed-count test (keep-alive) by +10.3% [+5.7, +15.0]
- bank-b2: Otterize slows the fixed-count test (keep-alive) by +5.3% [+1.6, +8.9]
- bank-b2: Hubble slows the fixed-count test (new conn) by +18.9% [+12.5, +25.2]
- bank-b2: IG trace_tcp slows the fixed-count test (new conn) by +9.6% [+5.0, +14.2]
- boutique-b2: Hubble slows the fixed-count test (new conn) by +7.1% [+3.0, +11.2]
- dsb-b2: Hubble slows the fixed-count test (new conn) by +14.4% [+10.0, +18.8]
- otel-b2: Otterize slows the fixed-count test (keep-alive) by +20.2% [+14.0, +26.5]
- otel-b2: Hubble slows the fixed-count test (new conn) by +30.3% [+15.6, +45.0]
- teastore-b2: Hubble slows the fixed-count test (new conn) by +25.7% [+15.9, +35.5]

Fragile results (significant after Holm only):

- none
