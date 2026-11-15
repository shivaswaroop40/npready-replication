# App bundles

One directory per application: `boutique`, `bank`, `dsb`, `otel`, `teastore`. Each reproduces the
thesis deployment and its journey A workload, adapted only where this cluster forces it.
Each `NOTES.md` lists the differences and the reasons.

## Files in `apps/<app>/`

| File | Use |
|---|---|
| `app.env` | `APP_NS`, `STEADY_*`, `TP_URL`, `TP_HEADERS`, `TP_PRE_HOOK`, `READY_TIMEOUT`. Plain `KEY=value`, safe to `source`. |
| `deploy.sh` | Namespace, manifest, generator ConfigMaps, thesis post-apply steps, waits until every workload is rolled out and `TP_URL` answers. Idempotent. |
| `restart.sh` | Run at the start of every run. Restarts every running Deployment/StatefulSet in dependency tiers, waits for the rollouts and for old pods to finish terminating, redoes per-app state (bank: session cookie; dsb: social graph), then needs three `TP_EXPECT_STATUS` answers in a row from `TP_URL`. |
| `undeploy.sh` | Deletes the manifest's objects (including cluster-scoped ones) and the namespace, and waits. |
| `steady.yaml` | Journey A generator as Job `pb-steady`. Placeholder `${STEADY_SECONDS}`. |
| `throughput.yaml` | Fixed-count test as Job `pb-tp` (hey). Placeholders `${TP_N}`, `${TP_C}`, `${TP_FLAGS}`. |
| `manifest.yaml` | Generated from the thesis manifest; `manifest.changes.txt` lists every changed field. |
| `steady-configmap.yaml` | Locustfile / wrk2 scripts, verbatim from the thesis (applied by `deploy.sh`; boutique has none, its locustfile is baked into the image). |
| `images.txt` | Every image the bundle runs, exactly as written in the pod specs. `images.lock` has the digests these resolved to on 2026-10-02, and for floating tags the last push date. |
| `bank/session.sh` | Refreshes the demo-user cookie in Secret `perfbench-session`. It is bank's `TP_PRE_HOOK`. |
| `dsb/init.sh`, `dsb/dsb-init-job.yaml` | Social-graph initialisation (thesis post-apply step). |

All scripts run on cp-01 as root and need `kubectl`, `jq`, `curl` (bank also `openssl`, `python3`).
`KUBECONFIG` defaults to `/etc/rancher/k3s/k3s.yaml`. HTTP checks go from cp-01 to the Service
ClusterIP, so no probe pod is created. Progress goes to stderr; stdout carries one JSON line, e.g.
`{"app":"boutique","ns":"boutique","step":"restart","ok":true,"seconds":74,"pods":11,"ready":11,"restarts":0,"not_ready":[],"nodes":{"worker-01":6,"worker-02":5}}`.
A failure exits non-zero with a `FATAL:` line on stderr.

## Using the Jobs

```bash
cd /opt/perfbench/apps/<app>; set -a; . ./app.env; set +a

# pre-pull (once per node)
while read -r img; do k3s crictl pull "$img"; done < images.txt

# steady generator. The harness (bin/run_one.sh) runs the template twice: Job pb-warmup with
# STEADY_SECONDS=WARMUP_S, then Job pb-steady with STEADY_SECONDS=STEADY_S, so no warm-up request
# reaches the steady numbers (wrk2 cannot cut it out). By hand, one Job:
kubectl -n "$APP_NS" delete job "$STEADY_JOB" --ignore-not-found --wait
STEADY_SECONDS=$STEADY_S envsubst '${STEADY_SECONDS}' < steady.yaml | kubectl apply -f -
# wait for .status.succeeded=1 (or .status.failed>=1), then:
kubectl -n "$APP_NS" logs "job/$STEADY_JOB" > steady.log

# fixed-count test, once per mode and repeat
[ -n "$TP_PRE_HOOK" ] && ./"$TP_PRE_HOOK" >&2        # bank: refresh the session cookie
kubectl -n "$APP_NS" delete job "$TP_JOB" --ignore-not-found --wait
TP_N=10000 TP_C=16 TP_FLAGS=-disable-keepalive envsubst '${TP_N} ${TP_C} ${TP_FLAGS}' < throughput.yaml | kubectl apply -f -
kubectl -n "$APP_NS" logs "job/$TP_JOB" > tp-newconn-1.log    # after it completes
```

- The templates contain no `$` other than the placeholders, `$?` and `$(...)`, so plain `envsubst`
  without a variable list also works. Do not run `envsubst` on `manifest.yaml`: the OTel Grafana
  dashboards contain `${...}` text.
- Jobs have `backoffLimit: 0`, `restartPolicy: Never`, fixed names (delete before re-creating) and
  pod labels `app.kubernetes.io/part-of=perfbench`, `perfbench/role=steady|throughput`,
  `perfbench/app=<app>`. They run on cp-01 (`nodeSelector kubernetes.io/hostname=cp-01` plus
  control-plane toleration). The generator's exit code becomes the Job's: a broken locustfile or
  wrk2 error fails the Job. Request failures do not (`--exit-code-on-error 0`).
- `TP_FLAGS` empty = keep-alive (C persistent connections); `-disable-keepalive` = one connection per
  request. hey gives each of the C workers N/C requests: keep N a multiple of C (10000 and 2000 with
  C=16 are). hey's printed percentiles need N >= 100.

## Output formats

Steady log (`kubectl logs job/pb-steady`):

```
PB_STEADY_BEGIN epoch=<s> app=<app> kind=locust|wrk2 users=<n> rate=<r> seconds=<STEADY_SECONDS>
... generator console output (locust: final summary only; wrk2: full -L report) ...
PB_STEADY_RC=<exit code> epoch=<s>
=== PB_FILE steady_stats.csv ===             (locust only, also steady_failures.csv,
<csv>                                         steady_exceptions.csv, steady_stats_history.csv)
=== PB_END ===
```

- locust `steady_stats.csv`: one row per endpoint plus `Aggregated`: request and failure counts,
  median/average/min/max ms, req/s, percentiles 50 to 100 %. These cover the whole Job (in the
  harness, the steady window only; the warm-up is a separate Job).
- locust `steady_stats_history.csv`: one aggregated row per second with a Unix `Timestamp`, current
  req/s and percentiles, and cumulative `Total Request Count` / `Total Failure Count`. Use it to cut
  the warm-up out: steady-window requests = difference of the cumulative counts at the window
  edges.
- wrk2 (dsb) prints one report for the whole run: `Requests/sec:`, the
  `Latency Distribution (HdrHistogram - Recorded Latency)` lines (50 % to 100 %) and the
  `Detailed Percentile spectrum`. It has no per-interval output; the harness's separate warm-up
  Job keeps the warm-up out of it.

Throughput log (`kubectl logs job/pb-tp`): `PB_TP_BEGIN epoch= app= n= c= flags=[...] url=`, then
hey's report (`Total: <s> secs`, `Requests/sec`, `Latency distribution` 10 to 99 %,
`Status code distribution: [200] <n> responses`, `Error distribution` if any), then
`PB_TP_RC=<rc> epoch=<s>` and `=== PB_END ===`. A run is valid only if `[200]` equals `TP_N`.
hey does not follow redirects here, so an expired bank cookie shows up as `[302]`.

## Laptop tools (`apps/tools/`, never touch a cluster)

| Tool | What it does |
|---|---|
| `prepare.py` | Builds every generated file from the thesis results directories and `app.env`. |
| `validate.sh` | prepare.py idempotency, YAML parse, template rendering, kubeconform `-strict` on all objects, `bash -n`, image coverage, private-key scan. |
| `local_smoke.py` | Runs each rendered generator and hey Job in the real images with `docker run` against a stub HTTP server, both TP modes, plus `bank/session.sh` with a fake kubectl. Logs land in `tools/.smoke/`. |
| `resolve_images.py` | Writes `images.lock`. |

`kubectl apply --dry-run=client` is not used: it still needs API discovery, so it fails without a
cluster. kubeconform does the schema check instead.

Not tested here: anything that needs the cluster (`deploy.sh`, `restart.sh`, `init.sh`,
`undeploy.sh` against real pods; the TP URLs answering 200 from the real apps). The helpers in
`common.sh` were tested with a stub kubectl.
