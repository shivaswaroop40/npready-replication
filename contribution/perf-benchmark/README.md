# perf-benchmark

This benchmark measures what each traffic-capture method costs on a cluster set up like test-cluster. It covers 5 apps, 5 conditions and 3 repetitions. Each run records CPU, memory, generator latency and throughput, and the time to finish a fixed number of requests (the format of GoLeash, Cesarano, Monperrus and Natella, arXiv 2505.11016, Table 5). The analysis reports every number relative to a baseline run of the same app.

Conditions: `baseline`, `hubble`, `otterize`, `ig_tcp`, `ig_snap`. The baseline runs Cilium with Hubble off and no other observer.

The host's speed drifts by a factor of up to 2.6 within one condition over 90 minutes, which 3 long reps cannot separate from the conditions. So the harness can also run K short interleaved cycles (one run of every condition per cycle, Williams-design order) with a host-speed canary on every node, and the analysis reports every CPU and fixed-count number raw and canary-normalised. See "Host drift and interleaved cycles".

## Layout

```
cluster/   install.sh, Helm values, versions.lock, NOTES.md   (infra)
bin/       cond.sh                                            (infra)
bin/       sampler.py lib.sh run_one.sh run_matrix.sh collect.sh client_bins.py
bin/       canary.py drift_probe.sh drift_join.py             (host-speed canary and drift probe)
bin/       prepull_all.sh smoke_app.sh plan.py                (helpers; plan.py writes PLAN.json)
cluster/gadget.env                                            gadget image tag (v0.55.1, as the thesis ran)
PLAN.json  one play per entry: app, reps, estimated hours (<= 20), watchdog
           (bin/plan.py <results_root> --assume plan_assumptions.json --out PLAN.json)
FIXLOG.md  review findings -> action -> evidence (2026-10-02)
apps/<app>/ app.env deploy.sh undeploy.sh restart.sh steady.yaml throughput.yaml images.txt NOTES.md  (apps)
analyze/   analyze.py selftest.py sanity_check.py
tests/mockcluster/  end-to-end test of the shell harness against a mock cluster (Docker)
```

On the VM the tree lives in `/opt/perfbench/`. Runs write to `/opt/perfbench/results/<app>/rep<r>/<cond>/` on cp-01, interleaved cycles to `/opt/perfbench/results/<app>/cycle<k>/<cond>/` (see "Host drift and interleaved cycles").

## Run it

Everything below runs on cp-01 as root, except `collect.sh` and the analysis, which run on the laptop. Never point any of it at play `6abf7d3feb9990eadd5f4488`. Another agent uses that play for a tutorial, and `collect.sh` refuses it.

1. Upload the tree, unless the infra install already did:

   ```
   labctl cp -m cp-01 -u root -r contribution/perf-benchmark <play-id>:/opt/perfbench
   ```

   Then pre-pull every image once (about 7 GiB per worker; it writes `results/_prepull/summary.txt`):

   ```
   setsid nohup bash /opt/perfbench/bin/prepull_all.sh > /opt/perfbench/results/_prepull.out 2>&1 < /dev/null &
   ```

   `bin/smoke_app.sh <app>` checks one bundle on the real cluster in about 5 minutes: deploy, a
   `wget` of `TP_URL` from a pod on cp-01, a 60 s steady Job, one 200-request fixed-count test per
   mode, memory per node, undeploy. It writes `results/_smoke/<app>/summary.json`.

2. Check the pipeline with one short run (60 s warm-up, 240 s window, 2000 requests per mode). It takes about 10 minutes:

   ```
   /opt/perfbench/apps/bank/deploy.sh
   /opt/perfbench/bin/run_one.sh bank hubble 1 --short
   ```

   Look at `results/bank/rep1/hubble/run.log`, `warnings.txt` and `meta.json`. A short run uses the same directory as a full one. The full matrix does not count it as done, moves it aside and runs it again.

3. Start the matrix for one play's share of an app (see `PLAN.json`: one entry per fresh play, each
   estimated at 20 hours or less including install, pre-pull and deploy), detached, so it survives
   the SSH session:

   ```
   echo <play-id> > /opt/perfbench/PLAY_ID      # recorded in every meta.json
   ( setsid nohup /opt/perfbench/bin/run_matrix.sh bank --rep-list "1 2" > /opt/perfbench/results/bank.matrix.out 2>&1 < /dev/null & )
   tail -f /opt/perfbench/results/bank/PROGRESS.log
   cat /opt/perfbench/results/STATUS.json        # progress, mean run time, ETA
   ```

   `STATUS.json` is rewritten at every stage change and after every run: `app`, `rep_list`, `conds`,
   `total_runs`, `done_runs`, `failed_runs` (+ `failed_run_ids`), `current_run`,
   `current_run_started_at`, `matrix_started_at`, `mean_run_seconds` (measured runs of this
   invocation, else `EST_RUN_S` from app.env), `eta_finish_epoch`, `last_update_epoch`, plus `stage`
   (prepull, deploy, running, finished, deploy_failed), `run_timeout_s` and `play_id`. An orchestrator
   compares `eta_finish_epoch` with the play's expiry.

   How long a full run takes depends on how fast the app serves the fixed-count tests (6 x 10000
   requests). `bin/plan.py <results_root>...` measures it from short runs and writes `PLAN.json`;
   see that file for the current estimates and their basis. The whole matrix (about 83 hours of runs) does
   not fit one 24-hour play, so every app runs on its own fresh play, and bank (about 2 hours per
   run) runs one rep per play. Each app sets its own watchdogs in `app.env`: `RUN_TIMEOUT` per run
   (bank 10800 s) and `TP_TIMEOUT_S` per fixed-count test (bank 2400 s, default 900 s). The order
   of the conditions in a rep depends only on app and rep, so a
   split matrix runs exactly the orders an unsplit one would.

4. Resume after a crash or a play restart by running the same `run_matrix.sh` command again. It skips every run that has a `DONE` file and replays the saved order. If the play itself had to be replaced, rerun the whole rep that was in progress on the new play: the analysis pairs a technique only with the baseline of the same rep on the same play and machines (`meta.json` `host`), and flags any rep that spans two.

5. Pull the results to the laptop and analyse them:

   ```
   bin/collect.sh <play-id> ~/perf-results            # add --with-raw for hubble.json / ig_tcp.json
   python3 analyze/analyze.py ~/perf-results/results
   open ~/perf-results/results/analysis/RESULTS-PERF.md
   python3 analyze/sanity_check.py ~/perf-results/results   # per-run checks, exit 1 on any failure
   ```

   `sanity_check.py` checks that each condition's observers were on or off (from `cond_state` and
   from the samples), that the samplers covered the window without gaps, that cp-01 stayed under
   75 % CPU during the fixed-count tests, that those tests got more than 99 % 2xx, and that Hubble
   flows, IG output and Otterize intents appear only in their own condition.

`run_matrix.sh` options: `--reps N` (3) or `--rep-list "1 2"`, `--cycles K` or `--cycle-list "1 2"` (interleaved short cycles, see below), `--short`, `--conds "baseline hubble"`, `--retries N` (1), `--keep` (do not undeploy at the end) and `--force-other-apps`.

`run_one.sh <app> <cond> <rep|cycle> [--short | --profile full|short|cycle] [--force]`: `--short` is the same as `--profile short`; `--profile cycle` takes the 3rd argument as the cycle number and writes to `cycle<k>/`.

`run_one.sh` and `run_matrix.sh` read these environment overrides: `PB_IDLE_S`, `PB_WARMUP_S`, `PB_STEADY_S`, `PB_TP_REPS`, `PB_TP_N`, `PB_TP_C`, `PB_TP_PAUSE_S`, `PB_SNAP_LEAD_S`, `PB_TP_TIMEOUT_S` (wins over the app's `TP_TIMEOUT_S`, default 900 s per fixed-count test), `PB_SAMPLE_S`, `PB_GADGET_TAG`, `PB_PLAY_ID`, `PB_RESULTS`, `PB_RUN_TIMEOUT` (wins over the app's `RUN_TIMEOUT` and `RUN_TIMEOUT_CYCLE`), and for the host-speed canary `PB_CANARY` (0 = off), `PB_CANARY_S` (2) and `PB_CANARY_ITERS` (canary.py's default, 150000).

## What one run does

`run_one.sh <app> <cond> <rep> [--short]` follows these steps and writes a timestamp for each one to `phases.tsv` and `meta.json`.

0. The host facts of every node go to `hostinfo.json`: play id, boot id, machine id, CPU model and MHz, CPU vulnerabilities, kernel command line, and the kernel config switches that decide where IRQ and BPF time is accounted.
1. `cond.sh <cond>` switches the cluster, restarts the Cilium agents and verifies the state. Its JSON line goes to `cond_state.json`.
2. `apps/<app>/restart.sh` restarts the app pods (dsb keeps its datastores; see its NOTES). For `otterize`, the harness then restarts the mapper once more, right before capture, as the thesis "otterize reset" did. Then `bpf_pre.json` records the BPF programs by type on every node; the run fails if any tracing program (kprobe, tracepoint, raw_tracepoint, perf_event) is loaded, which would be a gadget left from an earlier run.
3. The host-speed canary (`bin/canary.py`, scope `pb-canary`) and a sampler start on each node; the sampler samples every 5 s. `pb-scrape` fetches the Cilium agent, operator and Hubble metrics of every node every 15 s in every condition, as test-cluster' Prometheus did. Then the condition's client starts. `hubble` runs `kubectl port-forward svc/hubble-relay` and `hubble observe --server localhost:4247 --namespace <ns> -o json --follow`, each in a loop that restarts it, as the thesis capture scripts did. `ig_tcp` runs `kubectl gadget run trace_tcp:<tag> -n <ns> -o json` (tag from `cluster/gadget.env`). `otterize` sends the t0 GraphQL query.
3b. Idle segment, `IDLE_S` (60 s): observer on, app up, no load. It gives each condition's standing cost and the background connection rate (kubelet probes), with conntrack/TCP snapshots at both ends.
4. Warm-up. Job `pb-warmup` runs `steady.yaml` with `STEADY_SECONDS=WARMUP_S` (180 s).
5. Steady window. Job `pb-steady` runs `steady.yaml` with `STEADY_SECONDS=STEADY_S` (1200 s). The window starts when its pod is running. For `ig_snap`, `snapshot_socket` runs in the last 45 s of the window with load still on, up to 3 tries of 12 s each.
6. The harness saves the generator output to `steady.log`.
7. Fixed-count tests. For keepalive and then newconn, the harness runs `throughput.yaml` 3 times (`TP_N=10000`, `TP_C=16`), 20 s apart. Before each test it runs the app's `TP_PRE_HOOK`, if set (bank refreshes its session cookie). The output goes to `tp/<mode>-<i>.log`.
8. For `otterize`, the t1 query runs. The harness takes conntrack and Cilium/Hubble metrics snapshots around the window and around each test.
9. `bpf_final.json` records the BPF programs again with the clients still running (trace_tcp's kprobes must be there in `ig_tcp` and nowhere else). The clients and samplers stop. `client_bins.py` counts the client events per 5-s bin of event time (`client_bins.json`). The harness writes `meta.json`, then `DONE` on success, or `FAILED` with the reason.

A run directory without `DONE` moves to `<cond>.attempt-<time>` before the next attempt. The analysis ignores those directories.

Each client process runs in its own transient scope, `pb-<name>.scope`, so the sampler can measure it. Each sampler runs as the transient service `perfbench-sampler.service` on its node. The canary runs in the transient scope `pb-canary.scope` on every node; the analysis counts it as harness.

### Files in a run directory

| File | Content |
|---|---|
| `meta.json` | Phases, parameters, app.env, node info, clock offsets, cond.sh state, versions, fixed-count tests, warnings |
| `samples-<node>.csv.gz` | One row per cgroup per tick. CPU counters, memory, node totals. |
| `samples-<node>.csv.info.json` | Sampler details, including its own CPU use |
| `canary-<node>.csv.gz`, `canary-<node>.csv.info.json` | Host-speed canary: one row per kernel run (end time, CPU used for it, wall time, thread CPU time, iterations); its own CPU use |
| `steady.log`, `warmup.log` | Generator output |
| `tp/<mode>-<i>.log` | Fixed-count tool output |
| `ct/<label>.<node>.txt` | `/proc/net/stat/nf_conntrack` and `conntrack -S` |
| `metrics/<label>.<node>.{cilium,hubble}.prom` | Filtered scrapes of ports 9962 and 9965 |
| `hubble.json.gz`, `ig_tcp.json.gz`, `ig_snap.json`, `otterize_t{0,1}.json` | Client output |
| `client_bins.json` | Client events per 5-s bin of event time (Hubble flows, IG events by type) |
| `hostinfo.json`, `bpf_pre.json`, `bpf_final.json` | Host identity and kernel facts; BPF programs by type and observer ports per node |
| `scrape.log`, `hubble-pf.err` | The 15-s metrics scraper; the Hubble port-forward |
| `jobs/*.json` | The exact Job manifests applied |
| `run.log`, `warnings.txt`, `FAILED` | What happened |

## Notes for the app bundles

- The harness renders `steady.yaml` and `throughput.yaml` itself. It replaces `${VAR}` and `$VAR` only for the variables in `app.env`, plus `STEADY_SECONDS`, `TP_N`, `TP_C`, `TP_FLAGS`, `TP_URL`, `TP_HEADERS` and `APP_NS`. Every other `$` stays as written.
- Each template must contain exactly one Job. The harness renames it (`pb-warmup`, `pb-steady`, `pb-tp-<mode>-<i>`), sets `backoffLimit: 0`, removes `ttlSecondsAfterFinished` so the logs survive, and adds the label `perfbench=1`. Other objects, such as ConfigMaps, go through `kubectl apply` unchanged.
- `TP_FLAGS` is empty for keepalive and `-disable-keepalive` for newconn. An app can override these with `TP_FLAGS_KEEPALIVE` and `TP_FLAGS_NEWCONN` in `app.env`. An empty value has to survive the shell, so use it inside `sh -c "hey ... ${TP_FLAGS} ..."` and not as a separate `args` item.
- The steady generator runs as two Jobs from the same template, `pb-warmup` and then `pb-steady`. The apps README describes one Job across warm-up and window. Both work with the templates, and the two-Job form keeps warm-up out of every generator number, wrk2 included.
- The analysis reads these generator formats: the locust stats CSV (the header line `Type,Name,Request Count,...` and an `Aggregated` row), the locust summary tables, and wrk2 `-L` output. wrk2 prints no 95% line, so the analysis takes p95 from its detailed spectrum. When the log has `steady_stats_history.csv`, req/s and failure % cover exactly the analysis window. For fixed-count output it reads hey, oha and ab.
- A fixed-count test counts only if the number of `TP_EXPECT_STATUS` answers (default 200) equals `TP_N`. A bank cookie that expired shows up as `[302]` and voids the test. `--tp-tolerance` relaxes this.
- The harness judges a generator by its parsed stats, not by its exit code.

## Analysis

`analyze/analyze.py <results_root>` needs only the standard library. It uses scipy for the t-test when scipy is installed. It writes to `<results_root>/analysis/`:

- `RESULTS-PERF.md`, a summary in plain English: per-app tables, the excluded runs and the data warnings.
- `tables-<app>.md`, the same tables for one app.
- CSV files: `table5_fixed_count`, `overhead_cpu`, `overhead_memory`, `idle_standing_cost`, `fixed_count_cpu`, `latency_throughput`, `fixed_count_rps`, `normalised_cost`, `hubble_flow_mix`, `projection_shiv_thesis`, `components_cpu_mem`, `summary_across_apps`, `runs` (one row per run, every metric), `components_per_node`, `fixed_count_tests`, `excluded_runs` and `data_flags`.

The analysis window is the steady window minus 15 s at the start and 10 s at the end (`--trim-head`, `--trim-tail`). Nodes write their own clock into the samples, and the analysis shifts each node by the clock offset measured at the start of the run. It reads full runs only, unless you pass `--short`.

Statistics. Each rep is a block. Every overhead is the mean of the per-rep differences (technique minus the same rep's baseline, paired only when both runs come from the same play and machines), with a t-based 95% CI (df = reps - 1) and a paired t-test. "n.s." means the CI includes 0; for fixed-count overheads the upper CI bound is then reported. Four primary endpoints per technique (Δ cluster busy CPU, Δ observer memory, fixed-count time keep-alive and new connection) get Holm-adjusted p-values per app; everything else is exploratory. Welch's test on the run values stays in the CSVs as a second check. Table 5 gives mean ± SD over all executions (runs x repeats, as GoLeash reports its executions) and, separately, the SD of the baseline run means as the A/A noise floor. CPU and memory tables give both the SD over reps of the window means and the mean within-window SD of the 5-s values; memory also gets anon, the end value and the slope over the window.

Fixed-count context. For every test the analysis takes CPU per group, the app's CFS throttling and the most throttled app container from the samples, and the background-corrected connections per request. An app whose bottleneck container is throttled more than 0.1 s/s in the baseline newconn test is "quota-bound"; the summary across apps keeps quota-bound and node-bound apps apart. Cost per request and per new connection (observer CPU above its idle level during the test, in CPU-µs) replaces the steady-window "per flow" ratio, which divided idle cost by the kubelet probe rate.

The groups:

| Group | Contents |
|---|---|
| observer | cilium-agent, cilium-envoy, cilium-operator, hubble-relay, Otterize mapper and sniffer, gadget, and the `pb-*` client scopes |
| app | app pods |
| loadgen | `pb-*` Job pods and app-namespace pods on cp-01 |
| k8s_system | k3s and containerd units, other kube-system pods |
| node | `/proc/stat` busy time and `MemTotal - MemAvailable` |

The test-cluster projection (3 control planes and 3 workers, 18 vCPU, about 57 GiB) is an estimate. Main value: the observer components' cost measured on the 3 bench nodes, which carry the whole app load, plus the idle-segment cost of each node role for the nodes test-cluster has in addition (2 control planes, 1 worker). Upper bound: the earlier method, every test-cluster node costs what the bench node of its role costs under load (it triples cp-01, which also carries the generator and the clients). A third column adds the indirect costs: all busy CPU except the bench's clients, generator and harness. Clients are left out, because in the thesis they ran on the laptop. The bench has no platform background traffic, so the projection is app-attributable cost. It is per technique; the report also gives the sum for the thesis configuration (Hubble, IG trace_tcp and Otterize together), assuming the costs add up.

## Tests

- `python3 analyze/selftest.py` builds a synthetic results tree with known overheads, runs the analysis and checks that the tables recover the injected values. It also checks the parsers against real thesis output and, when scipy is installed, the built-in Welch test against scipy. Its third app runs 10 interleaved cycles on a host whose speed drifts by ±35% plus a 15% step; it checks that the canary-normalised deltas recover the injected overheads, that the drift diagnostic sees the drift, that Holm is applied across techniques, that the pb-canary scope counts as harness, and that `pb_williams` in `lib.sh` is balanced (needs bash >= 4 on PATH).
- `tests/mockcluster/run.sh` runs the real `run_matrix.sh`, `run_one.sh`, `drift_probe.sh`, samplers and canaries in an Ubuntu 24.04 container against a mock `kubectl`, `systemd-run`, `systemctl`, `ssh` and `scp` (workers act as remote nodes), then analyses the result. It needs Docker and takes about 30 minutes.
- `sampler.py` takes `--cgroup-root`, `--proc-root`, `--pods-log-dir`, `--crictl` and `--duration`, so it can run against a fake cgroup tree.

## Host drift and interleaved cycles

### The problem

The iximiuz host changes speed by a factor of up to 2.6 within one condition over 90 minutes (drift probe), whatever the condition. The full Boutique matrix (play 6ac00b02af86f3063ad20ec3, pulled to `contribution/results/PERF-FULL-20261002/`) shows it. The same 10000-request test at c16 took 141-154 s in the baseline run (21:08-21:22Z), 192-202 s in Hubble rep 1 (20:19-20:38Z) and 70-84 s in both IG snapshot_socket runs (23:20-00:05Z). Inside one IG trace_tcp run, with nothing changed, three new-connection tests took 133.7 s, 119.9 s and 77.9 s (started 22:47, 22:50 and 22:52Z). Steady-window CPU at the same 2.2 req/s load moved too: app 0.033-0.053 cores in the two fast runs against 0.075-0.081 in the others, k3s 0.110-0.170 against 0.205-0.244, cilium-agent 0.038-0.056 against 0.072-0.076 (Hubble off). Guest steal stayed at 0.03-0.08% throughout, so the hypervisor does not report the contention. With 3 long reps, the drift lands on conditions: IG snapshot_socket shows a false "-50%" fixed-count time.

Two additions deal with it. Both follow the cloud benchmarking literature: performance in shared clouds varies over time and between hosts and has to be measured, not assumed away (Leitner and Cito, "Patterns in the Chaos", ACM TOIT 16(3), 2016, doi:10.1145/2885497; Laaber, Scheuner and Leitner, "Software microbenchmarking in the cloud. How bad is it really?", Empirical Software Engineering 24, 2019, doi:10.1007/s10664-019-09681-1). The run order follows randomized multiple interleaved trials (RMIT; Abedi and Brecht, "Conducting Repeatable Experiments in Highly Variable Cloud Computing Environments", ICPE 2017, doi:10.1145/3030207.3030229).

### Host-speed canary

`bin/canary.py` runs on every node in its own scope `pb-canary`, started and stopped with the samplers (`pb_canary_*` in `lib.sh`). Every 2 s it runs a fixed pure-Python integer loop (a 31-bit LCG, 150000 iterations) and writes one row to `canary-<node>.csv`: end time, iterations, wall time and the thread's CPU time. The loop makes no syscalls and fits in L1, so it measures how much work one guest CPU-second buys and is barely touched by the guest's own cache traffic. It opens no socket, so Hubble, IG and Otterize see nothing of it.

- Speed index = iterations per CPU-second (the one used) and per wall-second (in the CSVs). A hypervisor that does not report steal charges the stolen time to the running thread, so a slower host means fewer iterations per CPU-second.
- Cost: the template's vCPUs report `Intel(R) Xeon(R) Processor` at 1996.8 MHz. On them the fastest kernel run took 7.8 ms (52 ns per iteration) and the median 12.5 ms, 23 ms on a contended worker: 0.64-1.04% of one core (play 6ac0684da347f7b916c94378, 2026-10-03). Every row records the real time; the analysis flags a canary above 1.5% of a core (`own_cpu_pct_of_core` in its info.json).
- It rotates its CPU affinity over the vCPUs, one per run (column `cpu`), so every vCPU is sampled equally.
- `PB_CANARY=0` switches it off. A canary that fails to start costs a warning and the normalised numbers of that run, not the run.

### Interleaved short cycles

`run_matrix.sh <app> --cycles K` (or `--cycle-list "1 2 3"` to split over plays) runs K cycles. A cycle runs every condition once with `run_one.sh --profile cycle`; cond.sh, the restart, the stability wait, the idle segment, the canary, the samplers and the clients are as in a full run. Only the timings change:

| | full | cycle |
|---|---|---|
| idle segment | 60 s | 60 s |
| warm-up | 180 s | 60 s |
| steady window | 1200 s | 300 s |
| fixed-count tests | 3 x 10000 per mode | 1 x `TP_N_CYCLE` per mode |
| run time | 43-119 min | about 12-13 min |
| results | `rep<r>/<cond>/` | `cycle<k>/<cond>/` |

`TP_N_CYCLE` in each `app.env` sizes a test to about 30-60 s at the app's measured c16 rate. It must be a multiple of `TP_C` (16), because hey sends N/C requests per worker: the first real cycle used 3000, hey sent 2992, and the analysis rejected every test (`run_one.sh` and `drift_probe.sh` now warn). Values: boutique 3008 (41.6-45.8 req/s in the v2 pilot, median 67-68 and range 49-143 in the full matrix), bank 608 (10.8-12.2 req/s), dsb 1504 (23.3-27.9 req/s), otel 4000 and teastore 5008 (no c16 run yet: c8 smoke rates 78-99 and 118-139 req/s, and those x0.7). Check otel and teastore after their first cycle. `EST_RUN_S_CYCLE` (730-800 s) feeds STATUS.json before the first run ends; `RUN_TIMEOUT_CYCLE` is the run watchdog (2400 s; bank 3000; dsb 4200, room for one graph rebuild).

Order: cycle k uses sequence k of a Williams design for 5 conditions (Williams, "Experimental designs balanced for the estimation of residual effects of treatments", Australian Journal of Scientific Research A 2, 1949, doi:10.1071/CH9490149). Its 10 sequences are the cyclic shifts of `0 1 4 2 3` and their mirror images. Over them, every condition sits twice in every position, and every ordered pair of conditions is adjacent exactly twice (first-order carry-over balance). Cycles 1-10 use the 10 sequences in an order shuffled with the seed sha256("<app>:williams:1"); cycles 11-20 reuse the set in a fresh order (seed ...:williams:2). Only whole sets of 10 cycles are fully balanced. `cycle<k>/ORDER.json` records seed, sequence, block and order, and a resumed matrix reuses it; `meta.json` has `order_pos`, `order_design` and `order_seq`.

STATUS.json in a cycle matrix has `layout: "cycle"`, `profile: "cycle"`, `cycle_list`, `cycles_total`, `cycles_done` (cycles with every condition DONE) and `current_cycle`; `rep_list` is empty. A rep matrix has the same fields as before plus `layout` and `profile`. The run counts, ETA and play id work the same, so `ops/monitor.py` needs no change; give a cycle play its cycle watchdog as `run_timeout_s` in `ops/plays.json` (monitor.py calls a play stuck after that plus 15 minutes without a STATUS update).

Time budget: a cycle (5 runs) takes about 61-67 minutes, so 10 cycles take 10-11 hours and fit one 24-hour play with setup. For 20 cycles, run `--cycle-list "1 2 ... 10"` and `"11 ... 20"` on two plays. The analysis pairs within a cycle, so a cycle must not span two plays.

```
( setsid nohup /opt/perfbench/bin/run_matrix.sh boutique --cycles 10 > /opt/perfbench/results/boutique.cycles.out 2>&1 < /dev/null & )
```

### Drift probe

`bin/drift_probe.sh <app> <minutes> <interval_s> [--cond <cond>] [--tp-n N]` checks the canary against the real workload. With the app deployed and the cluster in one condition (`--cond` runs cond.sh first; otherwise the state as found goes to `cond_found.txt`), it runs the canary on every node and starts one fixed-count test every `interval_s` seconds: 2000 requests, keep-alive, `TP_C` from app.env (default 16). It takes the benchmark lock. Results go to `results/_drift/<app>-<UTC time>/`:

- `timeline.csv`: per test, the start, test time, req/s, the canary speed per node during the test, the workers' speed in the pause before it, their ratio to the probe's median and the normalised test time. It is rewritten after every test.
- `summary.json`: the CV of the test time raw and normalised, the correlation of the test time with 1/speed, and `load_vs_pause_speed_median` (canary speed during a test / in the pause before it; 1.0 means the guest's own load does not slow the canary).

Run one before relying on the normalisation, e.g. `drift_probe.sh boutique 360 120 --cond baseline` (6 hours, a test every 2 minutes). If the canary tracks the host, r is close to 1 and the normalised CV is much smaller than the raw one.

### Validation on a real play (2026-10-03)

Play 6ac0684da347f7b916c94378, Boutique in baseline; data in `contribution/results/PERF-DRIFT-20261003/`.

- Drift probe, 90 minutes, 36 tests of 2000 keep-alive requests at c16, one every 150 s (02:33-04:01Z): test time 15.8-41.1 s, CV 16.6%. The canary moved too (workers' speed during the tests 8.2-12.4 M iterations per CPU-second, CV 9.9%), but it explains little of the test time: r with 1/speed 0.41 (Spearman 0.46), R² 0.17; worker-02 (recommendationservice, productcatalog) r 0.53, worker-01 (frontend) r 0.14. Normalised CV 16.4% against 16.6% raw. Measured in the pauses between tests (guest idle), the canary does not correlate with the test time at all (r -0.04 to 0.13).
- Part of the in-test correlation comes from the test's own load: the canary runs 8.5% faster during a test than in the pause before it (median), and on worker-02 that ratio rises with the test's req/s (r 0.70).
- The test time takes discrete levels set by the CFS period (100 ms). The hey median latency sits at about 300 ms (26 tests, 32-41 s), 200 ms (8 tests, 25-32 s) or 100 ms (2 tests, 16-26 s). The full matrix shows the same levels in its 72 tests of 10000 requests pulled by 04:04Z: p50 near 300 ms in 27 tests (155-205 s), near 200 ms in 31 (115-165 s), near 100 ms in 14 (70-112 s). Presumably a small change in host speed moves the throttled containers to another level. The time then changes in steps of 30-50%, which a linear correction by a speed index cannot follow.
- The drift is shared between plays. The full-matrix play 6ac00b02 ran tests at the same clock times (read from its pulled data): over 13 overlapping test pairs the time per 1000 requests correlates with r 0.76 (Spearman 0.80). From 02:51 to 03:07Z both plays sat at the 200-ms level (12.5-14.9 and 13.0-14.3 s per 1000 requests), although that play ran Otterize and this one baseline.
- One interleaved cycle (`--cycles 1`): 5 runs DONE in 659-728 s, 58.4 minutes for the cycle; canary data from all 3 nodes in every run. The canary's steady-window speed differed by +16% to +62% between the technique runs and the baseline run, and the normalised Δ cluster busy CPU came out 1.7-4.7 times the raw one (+0.19 to +0.37 against +0.06 to +0.11 cores), while the raw app CPU stayed at 0.077-0.090 cores.

Conclusion: on this platform the canary is not a usable normaliser. Quote the raw paired deltas of the cycle design; read the canary columns as a diagnostic only. The interleaved order does not depend on the canary and stays the defence against drift.

### Analysis

`analyze.py` reads both layouts. Rep-layout runs give exactly the old outputs in `analysis/`, unless a run has canary data. Cycle-layout runs are analysed separately into `analysis/cycles/` (`RESULTS-CYCLES.md`, `tables-<app>.md` and the same CSVs; a cycle is the block a rep is, so the "Rep" columns there hold cycle numbers).

- Canary speed per segment: the mean speed per node over the idle segment, the steady window and each fixed-count test (ratio of summed iterations to summed CPU time over the kernel runs whose midpoint falls in the segment, clock offsets applied). File `canary_segments.csv`; a table per app with one value per worker.
- Canary normalisation: the reference of a node is the median of its steady-window speeds over the app's used runs (per layout). Normalised CPU = each node's cores x (its speed in the window / its reference), summed (`cn.cpu.<scope>.<group>` in runs.csv). Normalised fixed-count time = time x the workers' mean speed ratio during that test (`cn.tp.<mode>.time_s`). A run on a fast host is scaled up to the median host speed.
- Paired deltas, raw and normalised side by side (`paired_deltas.csv`, first table of each app): Δ cluster busy, observer, app and k3s CPU, Δ observer memory (raw only), fixed-count time per mode in %. Each is the mean of the per-cycle differences against the same cycle's baseline, with a t-based 95% CI (df = cycles - 1), the paired p and Holm across the 4 techniques per endpoint and variant. The last row is a check: the canary's own speed should not differ by condition. If it does, the observer's load slows the canary, and the normalised Δ understates the overhead.
- Drift diagnostic (`drift_per_block.csv`, `drift_summary.csv`): per cycle, the start time, the order, the baseline's fixed-count times and app CPU raw and normalised, its canary speed and ratio, and the cycle's mean speed. Below it: the CV of the baseline times across cycles raw and normalised, and the correlation of the raw time with 1/speed.
- Table 5 keeps its format; with canary data a second Table 5 uses the normalised times (`table5_fixed_count_normalised.csv`).

For rep-layout runs with canary data (any run made with this harness from now on), the same paired table, drift table (per rep), canary table and normalised Table 5 are added after the standard sections of the app.

### Limits

- The canary failed its validation on the real play (see above): it explains at most about a third of the workload's drift (R² 0.17 for the workers' mean, 0.34 with both workers fitted freely), its in-test speed partly follows the guest's own load, and the fixed-count time moves in CFS-period steps.

- The canary measures CPU speed for a small, compute-bound loop. Slowdowns from memory bandwidth or last-level cache contention reach it only partly. The drift probe shows how much of the workload's drift it explains.
- Normalising assumes the work scales with 1/speed. That holds for CPU-bound and CFS-quota-bound work (the quota is in CPU time); time spent waiting on I/O or the network does not scale.
- With fewer than 10 cycles, or a cycle with a failed run, the design is not fully balanced. The order is still randomised, and the analysis drops the unpaired runs.

## Choices that differ from the plain protocol

- Warm-up and steady window use two Jobs from the same template. One Job across both would mix warm-up requests into the steady latency numbers. Between the Jobs there is a gap of a few seconds without load, and the 15 s trim covers it.
- `ig_snap` takes its snapshot in the last 45 s of the steady window, while the load still runs, as the thesis capture scripts did. A snapshot after the generator stops would see an idle app. Its cost therefore counts in the steady-window numbers.
- The sampler does not read `memory.peak`, because that value covers the whole life of the cgroup. Peak memory comes from the samples inside the window.
- Raw client streams are gzipped after the samplers stop. `collect.sh` leaves them out unless you pass `--with-raw`. Their line counts are in `meta.json`, their per-5-s event counts in `client_bins.json`.
- Conditions run in a balanced order (`pb_shuffle` in `lib.sh`): for the 5 conditions and reps 1-3, three rows of a position design in which every condition takes three different positions, the mean position of every condition is 3 ± 1/3, and no condition follows the same one twice. Baseline sits at positions 2, 4 and 3; the other four conditions are assigned to columns by a shuffle seeded with sha256(app). Other reps and condition subsets use the old seeded shuffle.
- The run length is the supervisor's protocol stretched by the fixed-count tests: 60 s idle + 180 s warm-up + 1200 s window take 24 minutes, and 6 x 10000 requests take about 11 (teastore, estimated) to 87 (bank, measured) minutes, so a full run lasts about 43 to 119 minutes instead of about 30 (measured on 2026-10-02: boutique 52, dsb 69, bank 119). The protocol is kept the same for all apps (TP_N = 10000, 3 repeats per mode); the 24-hour play limit is met by giving every app its own play, and bank one play per rep (PLAN.json).

## Differences from test-cluster that do not change the deltas

| Item | Bench | test-cluster |
|---|---|---|
| Control plane | 1 k3s server, embedded etcd (`--cluster-init`), 2 vCPU | 3 servers, 3 etcd members, c3-4 |
| Workers | 2 x 4 vCPU, 6.5 GiB | 3 x b3-16-flex, 4 vCPU, 16 GB |
| Kernel | 6.12 (Firecracker), IRQ time accounting off | 6.8 Ubuntu on OVH KVM |
| k3s | v1.36.3 everywhere, local-storage kept, no cloud provider, metrics-server v0.9.0 | v1.36.3 (one node v1.36.2), Cinder CSI, OpenStack CCM, metrics-server v0.8.1 |
| Platform | none besides the app (no kube-prometheus-stack, Kyverno, Trivy, Traefik, cert-manager, Ankra agent) | all of them |
| Generator, clients | Jobs and client scopes on cp-01 | generator on a worker, clients on the laptop |
| IG | server v0.54.1, gadget images v0.55.1 | the same (`:latest` was built with v0.55.1) |

Cilium config: 155 of 155 keys of the saved cilium-config are identical. Generator users and rates match the thesis workloads exactly.
