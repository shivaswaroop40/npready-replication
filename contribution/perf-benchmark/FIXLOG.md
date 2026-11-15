# FIXLOG: review findings of 2026-10-02 -> action -> evidence

Fixer pass on play `6abf7eba882cd1c296de683a` (2026-10-02). Sources: the pilot report, the three
reviews (methodology, measurement, representativeness) and the orchestrator's items a-d.
Validation data: `contribution/results/PERF-PILOT-20261002-v2/` (VM `/opt/perfbench/results/_pilot2`),
analysed with the new `analyze.py`.

Verdicts: **fixed** (code changed and shown in the v2 data), **fixed (analysis)** (computed from data
the harness already had), **partly** (what was done and what was not), **rejected** (with the reason).

## Orchestrator items

| # | Issue | Action | Evidence |
|---|---|---|---|
| a | dsb: restart re-ran the 15+ min social-graph init and two 130 MB GitHub clones before every run | **fixed.** `apps/dsb/restart.sh` keeps every `*-mongodb`, `*-redis`, `*-memcached` Deployment running (`PB_RESTART_KEEP`, new in `apps/common.sh pb_restart_tiers`) and restarts jaeger + services, then media-frontend, then nginx-thrift. `deploy.sh` builds the graph once (`init.sh`); `restart.sh` calls `init.sh` without `--force`, which skips while the datastore pods (uid + restart count) are unchanged and rebuilds only if one was replaced. New `apps/dsb/dsb_src.sh` clones the fork once per play on cp-01 at `0d49cb4d`, keeps the 6 directories the init containers copy (676 KiB), ships them to every worker over ssh with a tree hash check; `prepare.py` recipe `git_local` turns the two init containers' `git clone` into `test .perfbench-commit = 0d49cb4d && cp ...` from a read-only hostPath. If a datastore restarts during the init, the retry is paced (`--limit 50`). | v2 dsb short matrix (`_pilot2/dsb`): `dsb_src.sh` clone + copy 12 s, 676 KiB, tree hash checked on both workers; deploy incl. the one-time init 1150 s (19.2 min): 962 users, 37,617 follows, 9,417 posts (7 + 7 failed requests, as the shipped script reports), 0 datastore restarts. Every run: `init ... already initialised ... skipping`, restart.sh 41 s, app_restart phase 62-63 s (incl. the new 20 s stability wait), 0 app restarts, 5/5 DONE, 0 warnings, short runs 667-729 s. Full-run estimate 68.8 min (39.3 min of it the 6 x 10000-request tests at 24.5-26.5 req/s): PLAN.json dsb (1 2 3) = 19.4 h. Two further fixes found on the way: (1) social-graph-mongodb was OOM-killed in every init at the chart's 128Mi, also with the job paced to 50 connections (`_pilot2/_dsb-failed-paced-oom`); the thesis init lost two Mongo pods the same way (thesis `pods.txt`), so the six Mongo limits go to 512Mi (prepare.py recipe, NOTES row; social-graph-mongodb then peaked at 135 MiB); (2) `init.sh` now stops an attempt as soon as a datastore restarts, empties all datastores and retries paced, so no graph is built on a partial one. Earlier failed attempts kept as `_pilot2/_dsb-*`. |
| b | bank: 6 x 10000 requests take ~77 min, a run ~100 min, more than the 90-min watchdog; matrix > 24 h | **fixed.** `run_matrix.sh --rep-list "<r> ..."` (orders depend only on app + rep, so a split runs the same orders); per-app `RUN_TIMEOUT` (and `EST_RUN_S`) in every `app.env`; `PB_RUN_TIMEOUT` still wins. N stays 10000. The validation showed bank is slower at c16 than the c8 smoke test suggested, and that the 900 s per-test watchdog also kills bank tests, so bank gets `TP_TIMEOUT_S=2400` and `RUN_TIMEOUT=10800`, and PLAN.json gives it one play per rep (two reps would need ~21.8 h). | v2 bank (`_pilot2/bank`, short window, TP_N=10000, c16): baseline keep-alive 818.3 s (12.22 req/s), newconn 848.5 s (11.79 req/s); Hubble 902.4 s (11.08) and 930.0 s (10.75); all four tests 10000 x [200], 0 errors, 0.00% non-2xx (< 1%). Runs 2246 s and 2533 s, 0 warnings. The first try (`_aborted/_bank-tp-watchdog-900s`) hit the 900 s per-test watchdog. Full-run estimate 118.9 min (87.3 min of fixed-count tests, app restart 106 s). |
| c | orchestrator needs progress and ETA per play | **fixed.** `run_matrix.sh` rewrites `$PB_RESULTS/STATUS.json` atomically at every stage and after every run: app, rep_list, conds, total_runs, done_runs, failed_runs (+ ids), current_run, current_run_started_at, matrix_started_at, mean_run_seconds (+ source: measured or app.env), eta_finish_epoch, last_update_epoch, stage, short, run_timeout_s, play_id. | `_pilot2/STATUS.json` during and after the boutique matrix, e.g. `{"done_runs":1,"current_run":"rep1/baseline","mean_run_seconds":621,"mean_run_seconds_source":"measured","eta_finish_epoch":1790952106,"stage":"running",...}` and at the end `stage: finished, done_runs 3, failed_runs 2, failed_run_ids [rep1/ig_tcp, rep1/ig_snap]` (the BPF check below), before the first run `mean_run_seconds_source: app.env`. |
| d | a plan that keeps every play under 20 h | **fixed.** New `bin/plan.py` measures fixed time, per-test overhead and fixed-count rates from short runs and writes `PLAN.json` (one entry per fresh play; est_hours includes 1 h setup, deploy/init and 5% slack). | `PLAN.json` (bin/plan.py over `_pilot2` + `plan_assumptions.json`): boutique (1 2 3) 14.7 h, dsb (1 2 3) 19.4 h, otel (1 2 3) 13.6 h (assumed from smoke rates x 0.7), teastore (1 2 3) 12.2 h (same), bank-a (1), bank-b (2), bank-c (3) 11.4 h each; max 19.37 h. Full runs: boutique 52.2, dsb 68.8, bank 118.9 min (measured); otel 47.9, teastore 42.7 min (assumed). Each est_hours = 1 h setup + deploy/init + runs x full run x 1.05. |

## Methodology review

| Issue | Sev. | Verdict and action | Evidence |
|---|---|---|---|
| Matrix cannot finish in 24 h | blocker | **fixed** by plan, not by shortening the protocol: every app gets its own fresh play, bank three (one per rep). The reviewer's "never split one app" is overridden by the orchestrator (keep N=10000 for bank); the split is made safe by per-rep pairing, recorded host identity and a balanced order that is the same split or unsplit. The supervisor's ~30 min per run becomes 37-105 min (protocol kept the same for all apps; README says so). | PLAN.json; all est_hours <= 20 |
| "Flows/s" counts kubelet probes | major | **fixed.** New idle segment (60 s, observer on, no load) with TCP-accept snapshots gives the background rate per run; steady flows are background-corrected (`flows.app_per_s`). The steady "mcores per 1k flows/s" table is dropped from the report; costs per request (exact) and per new connection (newconn tests, background-corrected) come from the fixed-count windows: observer (and node) CPU above the idle level x test time / count. | boutique v2: background 2.81/s (idle segment), steady accepts 2.91/s, so app-driven 0.07/s (keep-alive locust): the reviewers' probe finding confirmed. Background-corrected connections per request: newconn 1.00, keep-alive 0.009 (boutique); dsb newconn 2.07, keep-alive 1.04, bg 0.0/s (no probes in that chart). Since 15:10 the snapshots also carry per-netns counters, so a pod that goes away between two snapshots (otterize's mapper reset made one boutique background negative) no longer moves the sum. |
| Table 5 power, SD level vs GoLeash | major | **partly.** Table 5 now gives mean ± SD over all executions (runs x repeats, n = 9 per cell at 3 reps), the paired overhead with a 95% CI and, when n.s., the upper CI bound ("< X% at 95%"), plus an A/A table (CV of baseline run means). TP_N and the 3 repeats are kept: the orchestrator fixed N=10000 for all apps, and 4-5 repeats per mode would add 25-50% run time (bank would need three plays). | table5_fixed_count.csv columns `wo_exec_*`, `with_exec_*`, `overhead_ci_*`, `aa_cv_pct` |
| Unpaired Welch, no CI, uncalibrated 2xSD rule, no multiplicity | major | **fixed (analysis).** `Agg.cmp` pairs technique and baseline by rep (only same play + machines), reports mean of per-rep deltas with t-based 95% CI (df = n-1) and paired p; "n.s." = CI contains 0 (replaces the 2xSD rule, kept in CSV as `within_2sd`). Holm over 4 primary endpoints x 4 techniques per app; the rest labelled exploratory; Welch kept as a CSV column. The summary across apps carries n.s. per value. | `selftest.py` OK; RESULTS-PERF.md "How to read" |
| Within-window SD never reported | major | **fixed (analysis).** CPU table has both SDs (± over reps; "SD in window" = mean of 5-s SDs); memory gets SD in window, slope (MiB/min), anon and end value. | overhead_cpu.csv `*_sd_in_window`; overhead_memory.csv `obs_slope_mib_per_min` |
| CPU/memory only at journey-A load | major | **fixed (analysis).** Per fixed-count test: observer, node, k3s, app CPU, cp-01 busy, app throttled s/s and the most throttled container; new table "CPU during the fixed-count tests" and `fixed_count_cpu.csv`. | boutique v2 newconn: Δ observer during the tests Hubble +0.537, IG trace_tcp +0.347, Otterize +0.119 cores (steady window: +0.059/+0.218/+0.086); app throttled 2.64 s/s baseline. dsb newconn: Hubble +0.616, IG +0.307. Table `fixed_count_cpu.csv`. |
| "% of baseline cluster" not transferable | major | **fixed (report).** Removed from the Markdown tables (CSV column renamed `..._pct_of_bench_base`); tables lead with Δ cores, Δ % of capacity and the projection; "How to read" says why. A test-cluster "% of its baseline" was not computed: no saved per-node busy-CPU totals of test-cluster were at hand. | RESULTS-PERF.md CPU table |
| Projection omits k3s; triples cp-01 | major | **fixed (analysis + harness).** Main projection = cost on the 3 bench nodes + idle-segment cost of the node role for each extra test-cluster node (2 CP, 1 worker); "upper" = old method; third column "observer + indirect" = node busy minus clients, generator and harness (k3s, kernel, BPF in app cgroups), scaled the same way. Memory denominator 57 GiB (worker capacity 15989976Ki x 3 + ~3.75 GiB x 3). | boutique v2, Hubble: main +0.056, upper +0.063, observer+indirect +0.105 cores; IG trace_tcp +0.422 / +0.410 / +0.587 (k3s and BPF work included in the third). dsb Hubble main +0.246 vs upper +0.322. |
| No play/host identity in meta.json | major | **fixed.** `hostinfo.json` per run (play id, boot_id, machine-id, CPU model/MHz, vulnerabilities, cmdline without the random seed, kernel config switches) -> `meta.json` `host`. `analyze.py` pairs only same play + machines and flags any app or rep that spans host sets. `/opt/perfbench/PLAY_ID` is written at upload. | every v2 meta.json has `host.play_id = 6abf7eba882cd1c296de683a`, boot ids b99142cf/97c864cc/61b4050b, CPU "AMD EPYC" 2495 MHz, CONFIG_HZ 250, PREEMPT_DYNAMIC y, CONFIG_IRQ_TIME_ACCOUNTING not set; per-run table in RESULTS-PERF.md shows play and boot ids. |
| Seeded shuffle unbalanced | minor | **fixed.** `pb_shuffle`: for the 5 conditions and reps 1-3, three rows of a position design (each condition at 3 different positions, mean position 3 ± 1/3, no repeated adjacency); baseline at positions 2, 4, 3; other conditions mapped to columns by sha256(app). Still a function of app + rep only. Position recorded (`order_pos`) and shown per run. | boutique rep1 order `hubble baseline otterize ig_tcp ig_snap` (design `balanced`) |
| Hubble client skipped the API-server path | minor | **fixed.** `hubble observe --server localhost:4247` through `kubectl port-forward svc/hubble-relay 4247:80`, each in its own restart loop and pb-* scope, as `bank_capture.sh` did. | boutique hubble run: 47,568 lines, 0 observe and 0 port-forward restarts |
| Hubble and IG events/s windows differ | minor | **fixed.** New `bin/client_bins.py` (end of each run) counts client events per 5-s bin of event time; analysis counts both tools inside the same analysis window. | same-window client events/s vs the thesis capture: boutique Hubble 32.0 (thesis 33.2), IG 5.7 (5.7); dsb Hubble 340.0 (354.0), IG 76.5 (76.1). The v1 pilot reported 101 and 23 lines/s for boutique (client lifetime incl. the fixed-count tests). |
| Steady latency quantised; steady req/s fixed by design | minor | **partly (report).** Steady latency moved out of the summary, the table is labelled exploratory, req/s labelled a controlled input, bucket limit and low-rate warning printed. Histogram-based window percentiles not implemented. | RESULTS-PERF.md steady section |
| ig_snap mixes standing and per-snapshot cost | minor | **fixed (analysis).** Standing cost (window before the snapshot) and CPU-seconds per snapshot (observer + k3s above the standing rate) reported separately. Leftover-gadget check: `bpf_pre.json` fails a run if any tracing program is loaded before it starts. | boutique v2 ig_snap (crash-looped run, excluded): standing Δ observer +0.198 of +0.201; one snapshot 0.57 CPU-s. dsb ig_snap: one snapshot 1.10 CPU-s; standing share 97% (idle segment). |

## Measurement review

| Issue | Sev. | Verdict and action | Evidence |
|---|---|---|---|
| Fixed-count test quota-bound; noise as large as overheads | major | **partly.** Bottleneck container and its throttled s/s next to every Table-5 row; A/A noise table; the method text states the quota-bound meaning; the summary across apps keeps quota-bound and node-bound apps apart. Not done: a second, non-quota-bound fixed-count target (protocol change, more run time). | boutique: bottleneck recommendationservice/frontend, 1.1-1.5 s/s throttled; dsb: nginx-thrift 0.7-3.0 s/s; both apps classed quota-bound. A/A: boutique baseline fixed-count time 43.41 s (v1) vs 45.31 s (v2) keep-alive, 42.71 vs 48.12 s newconn: run-to-run noise of 4-13% on this shared host, now printed as the A/A table. |
| Flows normaliser counts probes | major | **fixed**, see methodology row. | |
| Hubble traces its own client; projection triples cp-01 | major | **fixed (analysis).** Flow mix per class (app, probe, client_feedback = to/from hubble-relay, other) from `hubble_flows_processed_total` identity labels, plus cp-01 share; projection no longer triples cp-01. | boutique v1 (direct relay ClusterIP): client_feedback 42% of the flows processed, cp-01 57%. v2 (port-forward like the thesis): client_feedback 6%, probes 44%, app 26%, cp-01 30%; Δ k3s under Hubble +0.043 (v1 +0.011): the API-server path cost is now in. dsb v2: app 96%, client_feedback 1%. |
| "% of baseline cluster" near-idle denominator | major | **fixed (report)**, see methodology row; the idle segment splits idle and traffic-driven cost ("Standing cost" table, share column). | |
| IG cost misattributed (k3s rise from exec probes) | major | **fixed (report + check).** Δ k3s column in the CPU, idle and fixed-count tables; projection "observer + indirect" counts it. Gadget DaemonSet spec checked live: liveness, readiness and startup are all `exec /bin/gadgettracermanager -liveness`, period 5 s (the stock `kubectl gadget deploy` v0.54.1 spec, which test-cluster also used). | idle segment (no load): Δ k3s +0.067 (ig_snap) and +0.078 (ig_tcp) cores in boutique, +0.086/+0.070 in dsb, vs +0.022/+0.035 for Hubble. bpftool on a worker with only the gadget DaemonSet on shows IG's standing programs `ig_execve_e/_x`, `ig_sched_exec` (tracepoints) and `ig_fa_pick_e/_x` (kprobes), which run on every exec on the node, the 2 exec probes per 5 s included. |
| Short-lived cgroups lose CPU before first sample | minor | **fixed (analysis).** A cgroup that first appears after the first tick of a segment is counted from 0 (capped at 64 cores as a sanity guard). CPU after a scope's last tick is still not captured. | selftest restart check OK |
| Events/s scopes | minor | **fixed**, see methodology row. | |
| Steady latency coarse | minor | **partly**, see methodology row (no bootstrap CI). | |
| Working set includes active page cache | minor | **fixed (analysis).** anon next to working set, end-of-window value and slope; the table says not to compare component WS with node "used". | overhead_memory.csv |
| No BPF state per run | minor | **fixed.** `bpf_pre.json` (before samplers; the run fails on any kprobe, tracepoint, raw_tracepoint or perf_event program) and `bpf_final.json` (clients still running; warning unless ig_tcp has tracing programs and the others have none) with listening observer ports; `sanity_check.py` checks both. | first v2 IG runs failed `bpf_pre` with 15 tracing programs (5 per node): IG's standing container-collection set, loaded by the DaemonSet with no gadget running (names above). The check now separates that set; v2 runs: baseline/hubble/otterize 0 tracing programs before and after; ig_tcp 15 standing + 39 gadget programs at the end; ig_snap 15 + 0. Listening ports: 9962 everywhere, 9963 on the workers, 9965 only under Hubble. |
| Sampler timestamp before crictl refresh | minor | **fixed.** `ts` taken after `mapper.refresh()`. | bin/sampler.py |
| Hubble ring-buffer losses after the window not reported | minor | **fixed (analysis).** Lost events over the whole run (final scrape; counters start at the cond.sh agent restart), flagged when > 0. | boutique v2 Hubble: 0 lost in the window, 62 over the run; dsb Hubble: 97 in the window, 255 over the run (both flagged in RESULTS-PERF.md). |
| Steal not reported | minor | **fixed (analysis).** Steal per run in the per-run table, flagged when above twice the app median and 1%. | per-run table |

## Representativeness review

| Issue | Sev. | Verdict and action | Evidence |
|---|---|---|---|
| Projection triples cp-01 traffic cost | major | **fixed**, see methodology row (needs the idle segment, which is now in every run). | |
| Projection drops indirect costs | major | **fixed**, "observer + indirect" column; `CONFIG_IRQ_TIME_ACCOUNTING` recorded per node (not set on these 6.12 nodes, so softirq time lands in the interrupted task's cgroup). | hostinfo.json |
| Headline "% of baseline" | major | **fixed (report)**, see methodology row. | |
| No platform background traffic | major | **partly.** Projection labelled "app-attributable, platform background excluded"; an exploratory fit Δ cluster CPU = a + b x app connection rate across apps is printed once >= 3 apps exist. Not done: a sock-shop background sensitivity rep (no room in the 20 h plan). | RESULTS-PERF.md summary |
| Hubble/Cilium metrics never scraped | minor | **fixed.** `pb-scrape` scope curls :9962, :9963, :9965 of every node every 15 s in every condition (classified as harness); the number of hubble_* series at the end is recorded. | scrape.log, `scrape_cycles` in kv.tsv |
| IG gadget images differ from the thesis | minor | **fixed.** `cluster/gadget.env` `GADGET_TAG=v0.55.1` (thesis `:latest` = built with v0.55.1, warning in every thesis `ig_tcp.err`), used by `cond.sh`'s warm-up and run_one's clients; server check stays v0.54.1 (`IG_TAG`). Digests recorded in gadget.env. | v2 ig runs: `kubectl gadget run trace_tcp:v0.55.1`, `client_err.ig_snap.err.version_warning = built with ig v0.55.1 and it's being run with v0.54.1` (the thesis warning); trace_tcp produced 5.7 (boutique) and 76.5 (dsb) events/s, snapshot_socket 60 entries on the first try (boutique). |
| cp-01 shared; Hubble path | minor | **fixed / reported**: port-forward path as the thesis; cp-01 busy % per condition in the fixed-count CPU table and Table-5 CSV. | |
| Host and kernel facts not recorded | minor | **fixed**, hostinfo.json (see above). | |
| Conditions isolated | minor | **fixed (report).** Projection labelled per technique; the sum Hubble + IG trace_tcp + Otterize is printed as the thesis-configuration estimate. No extra "all" run (outside the matrix budget). | |
| 2 workers, 6.5 GiB; memory denominator | minor | **fixed (analysis)**: 57 GiB denominator; absolute app numbers labelled not comparable (README deviation table). | |
| No event-rate check vs the thesis | minor | **fixed (analysis).** Steady-window client events/s next to the thesis captureA rate (Hubble/IG lines/s, first to last event: boutique 33.2/5.7, bank 101.3/28.8, dsb 354.0/76.1, otel 72.3/3.8, teastore 44.7/15.7, computed from the thesis files); flagged outside 0.5-2x. | same-window client events/s vs the thesis capture: boutique Hubble 32.0 (thesis 33.2), IG 5.7 (5.7); dsb Hubble 340.0 (354.0), IG 76.5 (76.1). The v1 pilot reported 101 and 23 lines/s for boutique (client lifetime incl. the fixed-count tests). |
| k3s topology and flags | minor | **fixed (docs).** Deviation table in README. | README |

## Found during the v2 validation (this pass)

| Issue | Action | Evidence |
|---|---|---|
| boutique recommendationservice crash-looped after the restart in the ig_snap run (4 restarts before the window, 3 during), yet the run passed the "all pods Ready" check and finished DONE with fixed-count times halved | `prepare.py` startupProbe recipe now also covers recommendationservice (same cause as emailservice: Python gRPC, 200m, liveness 3 x 5 s from t=0). `run_one.sh`: pods must stay Ready with unchanged restart counts for 20 s before the run goes on, and a run whose app containers restart during it now FAILS (run_matrix retries it) instead of warning. `analyze.py` and `sanity_check.py` exclude/flag such runs. | `_pilot2/boutique/rep1/ig_snap.crashloop-20261002` (newconn 24.6 s vs 48.1 s baseline); rerun `_pilot2/boutique/rep1/ig_snap`: 0 restarts, fixed-count 44.6 s / 45.6 s, snapshot on the first try, DONE without warnings |
| IG DaemonSet loads 5 tracing programs per node with no gadget running, so the new `bpf_pre` check failed every IG run | `pb_bpf_state` names programs; IG's standing set (`ig_execve_*`, `ig_sched_exec`, `ig_fa_pick_*`) is expected in IG conditions; anything else fails the run | see BPF row above |
| bank: one 10000-request test at c16 ran past the 900 s per-test watchdog | `TP_TIMEOUT_S` per app (`PB_TP_TIMEOUT_S` > app.env > 900); bank 2400 s; bank `RUN_TIMEOUT` 10800 s | `_pilot2/_bank-tp-watchdog-900s/rep1/hubble` (`timeout 900s; pod phase Running`) |
| dsb Mongo OOM in every init; first paced retry still OOM; paced job render failed (`kubectl create --dry-run` prints two JSON objects, not a List) | Mongo limits 512Mi; init stops early, empties datastores, retries paced; render wrapped with `jq -s` | `_pilot2/_dsb-*` dirs; final deploy 0 restarts |
| pod-netns accept counters fall when a pod goes away between two snapshots (boutique otterize background 1.2/s vs 2.8/s elsewhere) | per-netns lines in every ct snapshot; analysis sums only namespaces present in both | runs after 17:10 UTC carry `# podnet_ns` lines |

## Pilot problems carried over

| Problem | Action |
|---|---|
| dsb restart (blocker) | item a |
| bank watchdog (blocker) | item b |
| schedule > 24 h | item d / PLAN.json |
| normalised cost meaningless for boutique | methodology "flows" row |
| teastore 404s right after deploy | not reproducible without a teastore run; check `fail %` of the first full teastore run |
| kernel 6.12 vs 6.8 | recorded per run (hostinfo); README deviation table |

## Host drift (2026-10-03): host-speed canary and interleaved short cycles

Finding: the full Boutique matrix (play 6ac00b02af86f3063ad20ec3, pulled to
`contribution/results/PERF-FULL-20261002/`) shows the iximiuz host's speed drifting by up to
about 2x over minutes to hours, whatever the condition. 10000-request tests at c16: baseline
141-154 s (21:08-21:22Z), Hubble rep 1 192-202 s (20:19-20:38Z), both IG snapshot_socket runs
70-84 s (23:20-00:05Z); one IG trace_tcp run, nothing changed, new-conn tests 133.7, 119.9 and
77.9 s (started 22:47, 22:50, 22:52Z). Steady-window CPU at the same load: app 0.033-0.053 vs
0.075-0.081 cores, k3s 0.110-0.170 vs 0.205-0.244, cilium-agent 0.038-0.056 vs 0.072-0.076.
Steal 0.03-0.08% in every run (computed with analyze.py from the pulled data). With 3 long reps
the drift lands on conditions (IG snapshot_socket: a false -50% fixed-count time). That matrix
used the old code and was not touched; its results still analyse to identical outputs.

| Issue | Action | Evidence |
|---|---|---|
| Host speed is not observable (steal ~0.05%) | **added** `bin/canary.py`: every 2 s a fixed pure-Python LCG loop (150000 iterations, no syscalls, L1-sized, no network) per node in scope `pb-canary`; logs ts, wall_ns, thread cpu_ns, iterations, vCPU (affinity rotates), involuntary context switches. `lib.sh pb_canary_{path,kill,start,ok,stop_fetch}` mirror `pb_sampler_*`; run_one starts it before the samplers and stops it after them; `PB_CANARY=0` turns it off; a canary failure is a warning. analyze.py counts `pb-canary*` as harness. | `--calibrate`: 72 ns/iteration on Python 3.12.3 (aarch64 container), 79 ns on 3.14 (macOS) -> 11 ms per run there, an estimated 15-24 ms (0.75-1.2% of a core) on the 2.5 GHz EPYC vCPUs; measured cost in the mock cluster 0.64% of a core (incl. start-up). It stops cleanly on SIGTERM and writes its own CPU use to info.json; the analysis flags > 1.5%. selftest: a pb-canary scope lands in harness, not in clients or observer (a mutation that drops the rule fails 2 checks). |
| Drift aliases onto conditions with 3 long reps | **added** `run_matrix.sh --cycles K` / `--cycle-list`: K short cycles, each runs every condition once with `run_one.sh --profile cycle` (60 s idle, 60 s warm-up, 300 s window, 1 x `TP_N_CYCLE` per mode; cond.sh and the per-run protocol unchanged) into `cycle<k>/<cond>/`. Order per cycle from a Williams design for 5 conditions (`lib.sh pb_williams`: cyclic shifts of 0 1 4 2 3 and their mirror images, 10 sequences; cycles 1-10 in an order shuffled by sha256("<app>:williams:1"), 11-20 by ...:2), saved to `cycle<k>/ORDER.json`. STATUS.json gains layout, profile, cycle_list, cycles_total, cycles_done, current_cycle (rep matrices keep their fields and gain layout and profile). | pb_williams output checked for boutique and bank, cycles 1-20: every condition twice in every position and every ordered pair adjacent exactly twice in each block of 10 (also in selftest). Mock cluster (below): 2 cycles = 10 runs DONE in the Williams orders, a second call skips all 10. |
| Fixed-count size for short cycles | **added** `TP_N_CYCLE` per app.env, sized for ~30-60 s a test: boutique 3000, bank 600, dsb 1500, otel 4000, teastore 5000; plus `EST_RUN_S_CYCLE` (730-800 s) and `RUN_TIMEOUT_CYCLE` (2400 s; bank 3000; dsb 4200 for one graph rebuild). | Rates from the pulled runs (hey Requests/sec): boutique 41.6-45.8 (v2 pilot, 2000 req), 49-143, median 67-68 (full matrix); bank 10.8-12.2; dsb 23.3-27.9. otel and teastore only have c8 smoke rates (77.8-99.5, 117.8-139.0), so check them after the first cycle. |
| Is the canary a good proxy for the workload? | **added** `bin/drift_probe.sh <app> <minutes> <interval_s> [--cond c]` + `bin/drift_join.py`: canary on all nodes, a 2000-request keep-alive test every interval_s, `timeline.csv` (test time, canary speed per node during the test and in the pause before it, normalised time) and `summary.json` (CV raw vs normalised, r of time with 1/speed, canary speed under load vs in the pauses). Takes the lock; rewrites the timeline after every test. | Mock cluster: 2-minute probe, a test every 20 s, every test with a canary speed; summary and timeline written, live copies removed. Not run on a real play (laptop-only task). |
| Analysis | **added** to analyze.py: cycle layout discovery (analysed separately into `analysis/cycles/`, RESULTS-CYCLES.md); canary speed per node and segment (idle, steady, each test; `canary_segments.csv`); normalisation per app and layout (reference = median steady speed per node; CPU x speed ratio per node, fixed-count time x the workers' ratio during the test: `cn.*` metrics); paired raw vs normalised deltas with t CI (df = blocks - 1) and Holm across techniques per endpoint (`paired_deltas.csv`), a canary-speed-by-condition check row, a drift diagnostic per block (`drift_per_block.csv`, `drift_summary.csv`) and a normalised Table 5. Table 5 keeps its format. These sections appear only for cycle data or runs with canary data. | Old outputs unchanged: original vs new analyze.py on the original selftest tree, the live Boutique full-matrix data and both pilot sets (`--short`) give identical files except the "Generated" line (diff -r). selftest synthC (10 cycles, host speed ±35% + a 15% step): normalised Δ observer x median speed within 0.006 cores of the injected 0.43/0.14/0.26/0.03, normalised fixed-count overheads within 0.3 points of +2/+1/+3/0% and +5/+3/+8/0%, while the raw ones are swamped by the drift (newconn Hubble +8.9% [-11.1, +28.9]); baseline time CV across cycles 30.6% raw vs 0.0-0.1% normalised, r = 1.00. Mutations (no normalisation, canary not harness, canary clock offset ignored, no Holm) each fail selftest. |
| Shell harness untested off the cluster | **added** `tests/mockcluster/` (Docker, Ubuntu 24.04 as on the nodes): the real run_matrix/run_one/drift_probe/sampler/canary against a mock kubectl, systemd-run, systemctl, ssh and scp (workers act as remote nodes), then `check.py` and the analysis. | see the end-to-end row below |
| End-to-end (mock cluster) | `tests/mockcluster/run.sh`: 2-cycle matrix, the same call again, a rep matrix and a `--short` run (old interfaces), three bad argument combinations, a 2-minute drift probe, then `check.py` and the analysis, in Ubuntu 24.04 / bash 5.2 / Python 3.12. | 2026-10-03, 29 min: 10 cycle runs DONE in the pb_williams orders (cycle 1 sequence 6, cycle 2 sequence 0), TP_N 1500 from TP_N_CYCLE, 1 test per mode, canary CSV + info from all 3 nodes (workers fetched from their remote paths, stopped cleanly on SIGTERM, 0.64% of a core); STATUS.json layout cycle, cycle_list [1, 2], cycles_done 2, 10/10; the second call skipped all 10; rep1 (profile full) and the `--short` run with `PB_CANARY=0` (no canary files) DONE; `--cycles` with `--short` or `--rep-list` and `--short --profile cycle` exit 2; drift probe 6 tests, each with a canary speed, canary under load / in the pauses 0.98; afterwards the lock was free and no canary or sampler process was left. Only warnings: the mock's missing BPF programs (ig_tcp) and Otterize mapper. The run found one bug, fixed: `drift_join.py` wrote the epoch columns with 6 significant digits (now `%.3f`; check.py tests it). |
| Found on the way, not changed | `analyze.py _mode_info` breaks a tie between two bottleneck names with `max(set(vs), key=vs.count)`, so the name depends on Python's per-process string hash seed. In the full Boutique data the Hubble newconn bottleneck flips between `recommendationservice` and `frontend` (one rep each) from one analysis run to the next. Old and new analyze.py agree for any fixed `PYTHONHASHSEED`. Left as it is so the old outputs stay as they were; a fix is `max(sorted(set(vs)), key=vs.count)`. | PYTHONHASHSEED 1-4: original and new outputs identical (diff -r); unset seed: the original gave `recommendationservice` in one run and `frontend` in another |

## Validation on a real play (2026-10-03, play 6ac0684da347f7b916c94378)

Fresh play from template `perfbench-test-cluster-e8e3df6c`; tree uploaded (176 file hashes checked), BOOTCHECK OK, Boutique deployed, cond.sh baseline. Data: `contribution/results/PERF-DRIFT-20261003/` (`results/_drift/` probe, `results/boutique/cycle1/` cycle, `tpn3008-check/` rerun). README "Validation on a real play" has the numbers.

| Issue | Action | Evidence |
|---|---|---|
| `TP_N_CYCLE` not a multiple of `TP_C`: hey sends N/C requests per worker, so boutique's 3000 at c16 sent 2992 and the analysis rejected all 10 fixed-count tests of the cycle (Table 5 empty, app classed node-bound for lack of data). bank 600, dsb 1504 and teastore 5000 had the same fault; the mock's hey did not divide, so the mock run missed it | **fixed.** `TP_N_CYCLE` boutique 3008, bank 608, dsb 1504, teastore 5008 (otel 4000 was fine); `run_one.sh` and `drift_probe.sh` warn when N is not a multiple of C; mockapp 1500 -> 1504 and check.py with it | cycle1 `fixed_count_tests.csv`: 10 x "2992 x [200] of 3000", valid False. Rerun `run_one.sh boutique baseline 1 --profile cycle` with 3008 (`PB_RESULTS=results/_validation/tpn3008`): keep-alive and new conn 3008 x [200], valid, 44.3 s each, no warnings. With `--tp-tolerance 0.005` the cycle's fixed-count tables fill in (Table 5, bottleneck, quota-bound), so the analysis path works. Old full runs use 10000/16 and are unaffected. Mock cluster rerun after the change (29 min): check OK, no warnings, 10 cycle runs with tp_n 1504; shellcheck clean on run_one.sh and drift_probe.sh; selftest OK |
| Does the canary track the workload's drift? | **no (not changed in code).** README says to quote the raw paired deltas and read the canary as a diagnostic | drift probe 90 min, 36 tests: test time 15.8-41.1 s (CV 16.6%); r(time, 1/canary speed) 0.41 workers' mean, 0.53 worker-02, 0.14 worker-01; R² 0.17; normalised CV 16.4%. Pause speed (guest idle) r -0.04 to 0.13. Canary 8.5% faster during a test than in the pause before it; on worker-02 that ratio follows the test's req/s (r 0.70). Cycle: canary speed in the steady window +16% to +62% against the baseline run, normalised Δ cluster busy 1.7-4.7x raw |
| Why the fixed-count time jumps by up to 2x | **found, not changed.** The hey median latency of Boutique sits on CFS-period levels (about 100, 200, 300 ms); the test time moves in steps between them | probe: 26 tests at ~300 ms (32-41 s), 8 at ~200 ms (25-32 s), 2 at ~100 ms (16-26 s); full matrix (72 tests): 27 / 31 / 14 tests at the same three levels, 155-205 / 115-165 / 70-112 s |
| Is the drift per play? | **found.** It is shared between plays at the same clock time | 13 overlapping test pairs with play 6ac00b02 (its pulled data only): s per 1000 requests r 0.76, Spearman 0.80; 02:51-03:07Z both at the 200-ms level (12.5-14.9 vs 13.0-14.3 s/1k) while that play ran Otterize and this one baseline |
| Cycle timing | measured | 5 runs DONE in 659-728 s (otterize 724, hubble 728, ig_tcp 677, baseline 659, ig_snap 711), cycle 3506 s = 58.4 min; STATUS.json layout cycle, cycles_done 1, mean_run_seconds 699; Williams sequence 9, order otterize hubble ig_tcp baseline ig_snap; every run with canary CSV + info from 3 nodes (0.64-1.04% of a core); sanity_check OK for all 5; afterwards no canary, sampler or lock left; app undeployed |
| Canary cost on the real vCPUs | measured | `Intel(R) Xeon(R) Processor` 1996.8 MHz (not the EPYC assumed): fastest kernel run 7.75-7.85 ms (52 ns/iteration), median 12.5 ms on cp-01 and worker-01, 23 ms on worker-02 (a more contended VM); own CPU 0.65 / 0.66 / 1.04% of a core |
| Not changed: analysis prose | `RESULTS-CYCLES.md` says of the normalised summary "Under host drift these are the numbers to quote". The validation says the opposite; change the text in analyze.py before the cycle results are written up | `analysis/cycles/RESULTS-CYCLES.md` of this run |

## Primary endpoints and % statistics (2026-10-03 ~09:30Z, before the cycle data is in)

Decided with 2-3 of 10 cycles of boutique-b1 and otel-b1 finished, from the drift review and the
health audit, and fixed in `analyze/analyze.py` (`PRIMARY`):

| Item | Decision | Reason / evidence |
|---|---|---|
| Primary CPU endpoint | **Δ observer CPU (cores)**, steady window. Δ cluster busy stays as a secondary column. | Cluster busy moves 1.5-2x with host drift; observer-group cores barely drift (drift review, 2026-10-03). Indirect costs (k3s, BPF work charged to app cgroups) are reported in the "observer + indirect" projection and the Δ k3s column. |
| Primary memory endpoint | **Δ observer anonymous memory (MiB)**. Working set stays as a secondary column. | Working set includes reclaimable page cache that comes and goes: gadget container cycle1/ig_tcp WS 323 MiB (file 194) vs cycle2 WS 138 (file 3), while anon was 114 vs 120. Paired Δ for IG trace_tcp: WS +236 [-1205, +1676] vs anon +139 [+129, +149] over 2 cycles. |
| % endpoints (fixed-count time) | p, the n.s. flag and the Holm input now come from the per-cycle % differences, the same numbers as the printed % CI. | Before, the CI came from % differences and p / n.s. from absolute seconds, so a row could print a CI that excludes 0 and still be marked n.s. (boutique keep-alive IG snapshot). `selftest.py` passes after the change. |
| Holm family | Per app: 4 techniques x {observer CPU, observer anon memory, fixed-count keep-alive, fixed-count new conn}. | Unchanged in size; only the two resource endpoints changed. |

## First run of a block: sensitivity analyses (2026-10-04 ~05:10Z, 4 of 5 block 1s done)

Observation: the first run of a block (cycle 1, position 1) sometimes sits far from the rest of the
block. Fixed-count time, z against all 50 runs of the block: boutique-b1 otterize -1.0 / -1.4,
otel-b1 baseline +1.6 / +1.4, bank-b1 (AMD) hubble +0.7 / +0.7, dsb-b1 otterize -4.0 (keep-alive,
fastest of 50) / -1.8; teastore-b1 otterize about 25 s vs 45-58 s for the other runs of cycle 1.
The sign differs between blocks and the effect vanishes on the stable AMD host, so this reads as
host drift landing on the first run, not as a systematic warm-up bias.

Decision, made before the remaining blocks finish:
- Primary analysis is unchanged: all cycles, paired per cycle (mean of per-cycle deltas, t CI, Holm).
- Two pre-declared sensitivity analyses are reported next to it for every block:
  (1) the same analysis without the first run of each block (its cycle is then unpaired for that
  condition only), and (2) the median of the per-cycle paired deltas with a Wilcoxon signed-rank test.
- A conclusion that holds in the primary analysis but not in both sensitivity analyses is reported as
  fragile.
- The protocol is not changed for blocks already running or still to come, so all blocks stay comparable.
Implemented the same day: `wilcoxon_p`, `first_run_ids`, `sensitivity_part` in analyze.py; a
"Sensitivity" section in RESULTS-CYCLES.md and `sensitivity.csv`. selftest passes. On dsb-b1 and
bank-b1, every result that is significant after Holm is also significant in both checks ("robust").

## Host type changes Inspektor Gadget's CPU cost (observation, 2026-10-04)

Steady-window CPU of the `gadget` DaemonSet pods in the ig_tcp condition: Intel blocks 0.069-0.103
cores (boutique-b1 0.074, otel-b1 0.071, dsb-b1 0.103, teastore-b1 0.069); AMD blocks 0.211-0.219
(bank-b1 0.219, boutique-b2 0.211; the AMD v2 pilot showed 0.213). cilium-agent at baseline is about
0.08 on both, k3s about 0.19-0.21 on both, so the host type does not inflate CPU accounting in general.
Same kernel (6.12.80) and 4 vCPUs on both.
Mitigations differ: Intel uses Enhanced IBRS (hardware) and is not affected by retbleed or SRSO; the
AMD hosts use retpolines, an "untrained return thunk" for retbleed and SMT disabled for SRSO.
Hypothesis, not tested: software retpolines and return thunks make every syscall and kernel return
dearer, and the gadget agent (BPF map/perf-buffer reads, /proc container scans) is syscall-heavy, so
it pays more than cilium-agent. Test: syscall counts of the gadget process on each host type
(`perf trace -s` or `strace -c -f -p <pid>` for 60 s).
Consequence for reporting: absolute CPU is reported per host type (blocks are not pooled across host
types); IG's standing cost is stated as hardware-dependent.

## Gadget warm-up retry (2026-10-04 ~19:50Z, for blocks launched from now on)

`cond.sh` (ig_tcp / ig_snap): the trace_tcp warm-up after fresh gadget pods sometimes exits rc=1
(VERIFY FAILED: gadget warm-up trace_tcp rc=1): boutique-b1 1, otel-b1 1, dsb-b1 1, teastore-b1 1,
dsb-b2 4 (AMD; one run passed only on attempt 3), otel-b2 1 (AMD). Each costs a run attempt; three
in a row would lose the run. Now the warm-up is tried up to 3 times, 5 s apart, and each failure's
stderr is kept in /var/tmp/perfbench-gadget-warmup-tcp.err.<try> on cp-01. This runs during the
condition switch, before anything is measured, so it does not change the protocol. Applies to bank-b2
and teastore-b2; dsb-b2 and otel-b2 keep the earlier cond.sh (no live play is modified).

### Update 2026-10-05 ~00:00Z: three host types, not two

dsb-b2 landed on a third host type: "AMD EPYC" at 4192.1 MHz (newer generation), with spectre_v2
"Enhanced / Automatic IBRS" (hardware), retbleed "Not affected", spec_rstack_overflow "Safe RET".
Its gadget CPU (ig_tcp) is 0.088 cores and cilium-agent at baseline 0.039, in line with the Intel hosts
(gadget 0.069-0.103). So the high IG cost is not "AMD": it is the 2495 MHz EPYC type, the only one
using software retpolines and an untrained return thunk. Across all 7 blocks so far, gadget CPU is
about 0.21 exactly on the hosts with software mitigations and 0.07-0.10 on the hosts with hardware
IBRS, which is what the syscall-cost hypothesis predicts. Still untested directly (no syscall counts).
Reporting: host type = CPU model + MHz + spectre_v2/retbleed mitigation, recorded per block.

## Agent-only Hubble experiment (declared 2026-10-05, before any data)

Why: the research for the KubeCon proposals found that Hubble inside the Cilium agent is on by default
(Helm chart since v1.9) but Relay, UI, metrics and flow export are opt-in. Our "hubble" condition is the
full stack (agent + metrics server :9965 + Relay + a streaming `hubble observe` client), so it does not
measure what a default install pays. The agent is only 41-47% of the full stack's component CPU.

New condition `hubble_agent`: `enable-hubble=true`, `hubble-metrics` and `hubble-metrics-server` absent,
Relay scaled to 0, no client, Otterize and IG off. Aggregation stays at the cluster's `medium`, which is
also the Helm default. Everything else as in the main design.

Design: per app, conditions `baseline`, `hubble`, `hubble_agent`; 12 cycles = two complete sets of the 6
possible orders (every condition in every position 4 times), each set in a seeded shuffled order; one
fresh play per app, run in parallel. Same cycle profile (60 s idle, 60 s warm-up, 300 s window,
one fixed-count test per mode, same TP_N_CYCLE per app). Results go to `PERF-AGENTONLY-20261005/`, never
into the main `COMBINED` report (that report keeps its 5 conditions and 10 blocks).

Pre-declared analysis (same rules as the main study): primary endpoints are observer CPU, observer
anonymous memory, fixed-count time (keep-alive, new connection); paired per cycle, 95% CI over cycles,
Holm over the two techniques (`hubble`, `hubble_agent`) per app; the median/Wilcoxon and
without-first-run checks apply unchanged. Headline contrast: `hubble_agent` against `baseline` per app.
Secondary contrast: `hubble_agent` against `hubble` in the same cycles (not in the Holm family).
Per-host-type reporting rule unchanged. If `hubble_agent` shows no detectable fixed-count slowdown, that
is reported with its upper bound, not as "no overhead".

### Agent-only experiment: Hubble verification race (2026-10-05 ~19:03Z)

Found on the first runs: the first `hubble_agent` switch failed its verification on 2 of the first 4 plays
(dsb, teastore; "hubble=Warning metrics=Disabled" a few seconds after the agent restart); the harness
retried and the retry passed. Cause: nothing waits for the agent's Hubble server to reach Ok before
`cond.sh` verifies (the full `hubble` condition is spared by its Relay wait). Fix: when Hubble is meant to
be on, `cond.sh` polls up to 60 s for `hubble=Ok` before verifying. Verification-only: it runs in the
condition switch, before the app restart and the idle segment, so nothing measured changes. Pushed
to the 4 running plays at about 19:03Z by atomic rename (identical sha256 to the local file); the fifth (otel)
uploads the fixed file. Runs before the fix are unaffected: failed attempts are discarded and retried.

## Agent-only experiment: result (2026-10-06 03:12Z)

All five blocks finished: 36/36 runs each, 0 failed, every check passed, plays destroyed by the finisher.
Results: `contribution/results/PERF-AGENTONLY-20261005/AGENT-ONLY-SUMMARY.md` (with a shared reading guide).
Pre-declared analysis applied unchanged. Headline: default Hubble (agent only) costs +0.008 to +0.018 cores and
+20 to +46 MiB, robust, with no detectable fixed-count slowdown in any app (bounds from <4.5% on TeaStore to <28% on OTel,
host-dependent). The full stack's 7% to 30% slowdowns therefore come from the opt-in parts; which part is not separated.
