# Generation cost (RQ3, generation side): offline, one laptop

Measured 2026-10-20. This file answers the generation half of RQ3: what the generators cost
when they turn a stored capture into a policy, and what fusion adds. The capture half is in
`RESULTS-PERFORMANCE.md`. Everything here ran offline on one laptop from the stored journey-A
captures and the shipped manifests of the five held-out applications. No cluster was used.

Scripts, raw data and outputs: `contribution/perf-benchmark/generation-cost/`
(`bench.py` timing driver, `gen_synth.py` step 1, `gen_fuse.py` step 3, `common.py` shared code,
`verify.py` correctness check, `summarize.py` tables; `runs.csv` one row per process, `env.json`
machine and versions, `out/<APP>/` outputs of the last repetition, `out/verify.json`).

## 1. Machine and software

| Item | Value |
|---|---|
| Model | `hw.model` Mac14,10 |
| CPU | Apple M2 Pro, 12 cores (8 performance, 4 efficiency) |
| RAM | 32 GiB (`hw.memsize` 34359738368) |
| OS | macOS 27.0 (build 26A428), arm64 |
| Power | AC power |
| Python | 3.14.7 (Homebrew), PyYAML 6.0.3 |
| npready | 0.3.0, editable install of `netpol-readiness` at commit `bf5ad33` (`/opt/homebrew/bin/npready`) |
| Run | 2026-10-20 07:42 to 07:46 (+0200), 3 min 19 s |

The laptop was not idle. Load average was 3.5 to 3.8 on 12 cores during the run (`env.json`),
with a LaTeX build, virtual machines and a terminal active. Every measured step is a single
thread, so contention is limited, and the spread between repetitions stayed small (section 5).

## 2. What each step runs

| Step | What it does | Code path |
|---|---|---|
| 1. Observation-only generation | stored journey-A Hubble capture (`captureA/hubble_<app>.json`) to the synthesiser's edge set, then the synth NetworkPolicy YAML | `hubble_edges()` imported unchanged from each app's `score_<app>.py`, then a YAML renderer (see below) |
| 2. Configuration derivation | shipped manifests to the declared edge set | `npready derive --manifests <path> --json <out>`; path is `manifests/` except Bank, which uses `bank-all.yaml` (see section 4) |
| 3. Fusion | union of the step 1 and step 2 edge sets, then the fused NetworkPolicy YAML | reads both outputs from disk, maps config names with the app's `role()` exactly as `score_<app>.py` `config_edges()` does, takes the union, renders |

Notes on the code paths:

- The thesis's synth edge set and fused edge set are the ones `score_<app>.py` builds:
  `pairs(hubble_edges(captureA))` and `pairs(hubble_edges(captureA)) | pairs(config_edges())`.
  Steps 1 and 3 call that code, not a copy.
- The script that wrote `policies/netpol_synth.yaml` and `policies/netpol_synth_plus_config.yaml`
  was not retained. It is not in `contribution/` or in `thesis-harness`. The renderer in
  `generation-cost/common.py` is a reconstruction. Section 4 checks it against the stored YAML.
  `thesis-harness/synthesize/synth.py` is an earlier synthesiser with a different input format and
  output layout. It did not produce these five apps' policies and is not measured.
- `npready fuse` is not measured. It is a coverage-scoring command that needs the ground-truth
  and attack sets as inputs. It reports coverage by source and does not write the fused policy.
- Each step is a fresh process, so its time includes interpreter start-up. Two reference processes
  show that floor: `python3 -c pass` and `npready --version` (section 5).

## 3. Method

- Every measurement is one fresh process wrapped in `/usr/bin/time -l`.
- 2 warm-up repetitions (recorded with `warmup=1` in `runs.csv`, excluded) and 20 measured
  repetitions per step per app.
- One repetition runs the two reference processes, then for each app in turn step 1, step 2 and
  step 3. Step 3 reads what steps 1 and 2 just wrote. Each app's output directory is deleted
  before its steps run.
- The warm-ups read every capture, so all measured runs read from a warm page cache. The numbers
  are compute cost, not disk cost.
- Wall time: `/usr/bin/time -l` "real" (10 ms resolution) and the driver's `perf_counter` around
  the same process (sub-millisecond, includes the fork of `/usr/bin/time`). The tables use
  `perf_counter`; the two differ by at most 13 ms in any run (10 ms resolution plus the fork).
- CPU time: user + sys from `/usr/bin/time -l` (10 ms resolution).
- Peak memory: "maximum resident set size" from `/usr/bin/time -l` (bytes on macOS), shown in MiB.
- Instructions retired, also from `/usr/bin/time -l`, as a measure that does not depend on load.

## 4. Input sizes, output sizes and correctness

Input and output sizes (from `out/verify.json`):

| App | Hubble flow records | Hubble capture | Manifest objects | Manifest bytes | Synth edges (pairs / triples) | Declared edges | Fused pairs | Pairs added by config | Policies | Ingress rules synth / fused |
|---|---|---|---|---|---|---|---|---|---|---|
| Boutique | 60,903 | 102.5 MiB | 35 | 22.1 KiB | 18 / 18 | 28 | 28 | 10 | 11 | 16 / 16 |
| DSB | 443,091 | 985.9 MiB | 81 | 194.1 KiB | 18 / 18 | 27 | 42 | 24 | 27 | 14 / 14 |
| Bank | 125,787 | 271.1 MiB | 23 | 38.9 KiB | 16 / 16 | 24 | 24 | 8 | 8 | 11 / 15 |
| OTel | 89,926 | 219.5 MiB | 74 | 327.6 KiB | 26 / 26 | 66 | 51 | 25 | 17 | 19 / 29 |
| TeaStore | 55,785 | 133.8 MiB | 10 | 4.5 KiB | 18 / 18 | 13 | 20 | 2 | 7 | 12 / 12 |

Flow records are JSON lines in the capture. Edge counts include DNS egress edges; the policies are
ingress-only, so DNS edges add pairs but no ingress rules. That is why Boutique, DSB and TeaStore
gain pairs from configuration but no rules.

Correctness check (`verify.py`, run on the outputs of the last measured repetition):

| App | Step 1: synth pairs vs `scores.json` admit | Step 1: YAML | Step 2: vs `config_derived_edges.json` | Step 3: fused pairs vs `scores.json` admit | Step 3: YAML |
|---|---|---|---|---|---|
| Boutique | 18 = 18 | byte-identical | identical | 28 = 28 | byte-identical |
| DSB | 18 = 18 | byte-identical | identical | 42 = 42 | byte-identical |
| Bank | 16 = 16 | byte-identical | identical | 24 = 24 | byte-identical |
| OTel | 26 = 26 | same enforcement semantics | identical | 51 = 51 | same enforcement semantics |
| TeaStore | 18 = 18 | byte-identical | identical | 20 = 20 | byte-identical |

"Admit" is the field `analytical.<tool>.admit` in `scores/scores.json` for `synth (ours, traffic A)`
and `synth_plus_config (ours, traffic A + config)`. "Same enforcement semantics" means the same
selected workloads, each admitting the same set of (source selector, port). Every step matches the
stored result in all five apps. There is no mismatch to report. Two details:

- **OTel YAML is not byte-identical.** The stored file lists `deny-accountingservice` last, and it
  writes the frontend's policy as `allow-frontend` with an empty `ingress:`. The reconstruction
  writes it as `deny-frontend`. Both deny all ingress to the frontend. The empty rule exists because
  the stored OTel policy carries no rule for the load generator. The reconstruction reproduces that
  with an OTel-only setting (`skip_src` in `common.py`), taken from the stored policy and the OTel
  README.
- **Bank derivation input.** `npready derive --manifests manifests/` gives the same 24 records as
  the stored file but in a different order. `npready derive --manifests bank-all.yaml` reproduces
  the stored file exactly, order included, so that is the call measured here. `bank-all.yaml` is
  `manifests/` without the `jwt-key` Secret (23 objects instead of 24). An earlier full run with
  `manifests/` as the Bank input (not kept) gave the same 88 ms median for step 2.

## 5. Results

Median [min to max] over 20 repetitions. Wall in ms, CPU in s, peak RSS in MiB, instructions in 10^9.

### Step 1: observation-only generation (Hubble capture to synth edges and policy)

| App | Wall ms | CPU s (user+sys) | Peak RSS MiB | Instructions 10^9 |
|---|---|---|---|---|
| Boutique | 526 [520-538] | 0.51 [0.51-0.53] | 15.0 [14.9-15.0] | 9.34 [9.29-9.39] |
| DSB | 4854 [4754-4922] | 4.84 [4.74-4.91] | 15.0 [14.9-15.1] | 86.59 [86.25-87.03] |
| Bank | 1285 [1252-1299] | 1.27 [1.23-1.29] | 14.9 [14.9-15.1] | 22.79 [22.74-22.88] |
| OTel | 968 [947-990] | 0.96 [0.94-0.98] | 16.6 [16.5-16.7] | 17.17 [17.10-17.21] |
| TeaStore | 647 [634-658] | 0.63 [0.61-0.64] | 15.0 [14.9-15.0] | 11.16 [11.08-11.21] |

### Step 2: configuration derivation (`npready derive`)

| App | Wall ms | CPU s (user+sys) | Peak RSS MiB | Instructions 10^9 |
|---|---|---|---|---|
| Boutique | 81 [80-89] | 0.06 [0.06-0.08] | 22.1 [22.0-22.1] | 0.92 [0.91-0.92] |
| DSB | 142 [141-149] | 0.12 [0.12-0.14] | 22.4 [22.3-22.6] | 2.01 [2.00-2.02] |
| Bank | 88 [87-96] | 0.07 [0.07-0.08] | 22.2 [22.2-22.3] | 1.04 [1.04-1.05] |
| OTel | 189 [187-200] | 0.18 [0.17-0.19] | 22.7 [22.6-23.1] | 2.83 [2.82-2.84] |
| TeaStore | 63 [61-67] | 0.04 [0.04-0.05] | 22.0 [22.0-22.1] | 0.62 [0.62-0.63] |

### Step 3: fusion (union and fused policy)

| App | Wall ms | CPU s (user+sys) | Peak RSS MiB | Instructions 10^9 |
|---|---|---|---|---|
| Boutique | 26 [25-28] | 0.01 [0.01-0.01] | 15.0 [14.9-15.0] | 0.20 [0.20-0.20] |
| DSB | 26 [26-28] | 0.01 [0.01-0.01] | 15.0 [14.9-15.0] | 0.20 [0.20-0.20] |
| Bank | 26 [25-30] | 0.01 [0.01-0.01] | 15.0 [14.9-15.1] | 0.20 [0.20-0.20] |
| OTel | 30 [29-34] | 0.01 [0.01-0.02] | 16.5 [16.4-16.6] | 0.23 [0.23-0.24] |
| TeaStore | 25 [25-29] | 0.01 [0.01-0.01] | 15.0 [14.9-15.0] | 0.20 [0.20-0.20] |

### Reference processes (start-up only, no work)

| Process | Wall ms | CPU s (user+sys) | Peak RSS MiB | Instructions 10^9 |
|---|---|---|---|---|
| `python3 -c pass` | 22 [21-23] | 0.01 [0.01-0.01] | 14.2 [14.2-14.3] | 0.17 [0.17-0.17] |
| `npready --version` | 54 [53-57] | 0.04 [0.04-0.04] | 21.9 [21.9-22.3] | 0.51 [0.51-0.51] |

Reading the tables:

- Step 1 time grows with the size of the capture. It works out at 4.4 to 5.1 ms per MiB of capture
  on this machine (**derived**: median wall / capture size, for example DSB 4854 ms / 985.9 MiB).
  DSB's 1 GB capture is the slowest at 4.9 s.
- Step 1 memory does not grow with the capture. `hubble_edges()` reads one line at a time, so
  peak RSS stays at 15 to 17 MiB, less than 2.5 MiB above a bare interpreter (14.2 MiB).
- Step 2's peak RSS (22 MiB) is almost all `npready` start-up: `npready --version` alone uses 21.9 MiB.
- Step 3 is close to interpreter start-up: 25 to 30 ms against 22 ms for `python3 -c pass`.

## 6. What fusion adds over observation-only generation

Per repetition, step 2 + step 3 compared with step 1 (medians over the 20 repetitions):

| App | Step 1 wall ms | Steps 2+3 wall ms | Steps 2+3 / step 1 | Step 1 CPU s | Steps 2+3 CPU s | Step 1 peak RSS MiB | Peak RSS of steps 2, 3 MiB |
|---|---|---|---|---|---|---|---|
| Boutique | 526 | 107 | 20 % | 0.51 | 0.07 | 15.0 | 22.1 |
| DSB | 4854 | 169 | 3 % | 4.84 | 0.14 | 15.0 | 22.4 |
| Bank | 1285 | 114 | 9 % | 1.27 | 0.08 | 14.9 | 22.2 |
| OTel | 968 | 222 | 23 % | 0.96 | 0.19 | 16.6 | 22.7 |
| TeaStore | 647 | 88 | 14 % | 0.63 | 0.05 | 15.0 | 22.0 |

In plain terms: on this laptop, fusion adds 88 to 222 ms of wall time and 0.05 to 0.19 CPU-seconds
per application. That is 3 % to 23 % of the time observation-only generation already takes from the
stored capture. Peak memory rises from 15 to 17 MiB to 22 to 23 MiB, because the `npready` process
starts larger. These are one-off costs per generation, not running costs.

Much of the added time is process start-up. Without it, derivation takes 9 to 135 ms and the union
and render take 3 to 8 ms (**derived**: step 2 median minus 54 ms `npready` start-up; step 3 median
minus 22 ms Python start-up).

The relative figure depends on the capture size, not on fusion. Fusion's cost follows the manifests
(OTel has the largest manifests, 327.6 KiB, and the largest cost), while step 1 follows the capture.
DSB's 1 GB capture makes fusion 3 % of the total; TeaStore's small capture makes it 14 %.

Capture side, for scale only: during capture Hubble costs 0.031 to 0.225 cores of extra observer
CPU and 86 to 112 MiB of extra observer anonymous memory, sustained for as long as capture runs
(`RESULTS-PERFORMANCE.md` section 3, "Ranges over the 10 blocks", row Hubble). Those are rates on
the iximiuz benchmark cluster. The numbers above are one-off costs on a laptop, so the two are not
directly comparable.

## 7. Limits

- One machine, offline, warm page cache, other work running. The cluster nodes and the thesis's
  original capture hosts were not used. The absolute times will differ on other hardware.
- The YAML renderer is a reconstruction of a script that was not kept. It reproduces the stored
  policies (byte-identical in 4 of 5 apps, same enforcement semantics in OTel). Its cost is part of
  steps 1 and 3 and is small next to step 1's capture parsing.
- Each step is timed as a separate process, the way an operator would run it. An implementation that
  ran all three steps in one process would avoid most of the start-up cost in section 6.
- `/usr/bin/time -l` reports CPU and "real" at 10 ms resolution. For steps 2 and 3 that resolution is
  coarse; the `perf_counter` wall times and the instruction counts are the finer measures.
- Only journey A captures were used, since those are the ones the thesis generated policies from.
