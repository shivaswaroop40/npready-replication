# Bank of Anthos v0.6.10: deviations from the thesis setup

Thesis run: `results/BANK-20260904` (journey A: 2026-09-04, 1200 s window, all observers on).
Every changed manifest field is listed in `manifest.changes.txt`, computed by `tools/prepare.py`
from a diff against the thesis files. `thesis/` holds verbatim copies, `thesis/SHA256SUMS` checksums.

## Source files

`manifest.yaml` is built from the per-file `manifests/*.yaml` of the thesis run, not from
`bank-all.yaml`. `bank-all.yaml` is a concatenation in which `jwt-secret.yaml` had no trailing
newline, so its `---` separator landed at the end of the public-key line. That merges the
`jwt-key` Secret and the following `ledger-db-config` ConfigMap into one YAML document; a parser
keeps one of the two. PyYAML reads 23 objects from `bank-all.yaml` and no Secret. The cluster
ran with both objects, so the thesis most likely applied the separate files.

`manifests/jwt-secret.yaml` is not copied: it holds the published demo private key. `deploy.sh`
generates a key pair once per namespace instead (RSA 4096, traditional PEM private key, SPKI
public key, the same Secret name and keys). Only this pair signs and checks the tokens, so the
app behaves the same. Both files are listed with their checksums in `thesis/SHA256SUMS`.

## Manifest

| Change | Why |
|---|---|
| `ENABLE_TRACING=false`, `ENABLE_METRICS=false` on frontend, userservice, contacts, balancereader, ledgerwriter, transactionhistory | Thesis post-apply step (spec section 5): the exporters need GCP credentials. The thesis ran `kubectl set env` after apply, which also added `ENABLE_METRICS` to the three Python services. The manifest now carries the same values, so a re-apply does not undo them. `deploy.sh` still runs the same `set env`; it is a no-op. |
| `Service/frontend`: `LoadBalancer` -> `ClusterIP` | No cloud load balancer here. On test-cluster the OVH LB health checks hit the frontend (`?->frontend:8080` drops in the thesis README). |
| `Deployment/loadgenerator`: replicas 1 -> 0 | Thesis post-apply step (scale the shipped generator to 0), written into the manifest. |
| `JAVA_TOOL_OPTIONS=-XX:-UseContainerSupport -XX:ActiveProcessorCount=1 -XX:MaxRAM=536870912` on balancereader, ledgerwriter, transactionhistory | Found in the pilot on 2026-10-02. The JDK in these images (17.0.4.1) dies at start-up on kernel 6.12 with `NullPointerException: Cannot invoke "jdk.internal.platform.CgroupInfo.getMountPoint()"`, in Spring's `processorMetrics` bean. Kernel 6.12 no longer lists the `memory` controller in `/proc/cgroups` when cgroup v1 memory support is compiled out, and older JDKs rely on that file (fixed upstream by JDK-8349988). test-cluster ran kernel 6.8, where these pods started normally. The flags turn container detection off and pass its result explicitly: 1 CPU (the 500m quota rounded up) and 512Mi of memory, which is what the JVM saw on test-cluster. The images set no `JAVA_TOOL_OPTIONS` of their own. The services now start in about 55 s. |

Requests of the 8 running pods: 0.96 CPU, 1664 MiB. Both databases use emptyDir and re-seed the
demo data on every start.

## Steady generator (journey A)

Taken from `workloads/loadgenerator-a.yaml`: Google's `AllTasks.UnauthenticatedTasks` (view login,
view sign-up, sign up), the shipped loadgenerator image, `USERS=5`, `LOG_LEVEL=info`, the
`locustfile-a` ConfigMap mounted over `/app/locustfile.py`, uid 1000, same resources.

- Image: the thesis Deployment used the tag `loadgenerator:v0.6.10`; the Job uses the same tag with
  the digest from the thesis manifest (`@sha256:dd7e27f1...`). The tag resolves to that digest today
  (`images.lock`). Locust inside is 2.44.4.
- The command is the image entrypoint written out (`locust --host=http://frontend:80 --loglevel info
  --headless --users=5`; spawn rate defaults to 1, written as `-r 1`), plus `--run-time`, `--csv`,
  `--only-summary`, `--exit-code-on-error 0`. The thesis run printed periodic stats; that only
  changes console output.
- About 90 % of journey A requests are marked failed by Google's own checks (`GET /login` and
  `GET /signup` redirect once the user is signed up), with or without observers. Read throughput
  and latency from the CSVs, not the failure rate.
- Pinned to cp-01 with a control-plane toleration (thesis: on a worker).

## Fixed-count test

`GET /home` as the demo user. The frontend calls balancereader, transactionhistory and contacts;
each checks the JWT; balancereader and transactionhistory read the ledger, contacts reads
accounts-db. Journey A never reaches this path (it stays unauthenticated), but no unauthenticated
GET fans out: `/login` and `/signup` are rendered by the frontend alone.

The session cookie:

1. `session.sh` reads the demo login from the app's ConfigMap `demo-data-config`, posts it to
   `/login` through the frontend ClusterIP with curl on cp-01, and takes the `token` cookie from the
   302 response.
2. It stores the value in Secret `perfbench-session` (key `token`) and checks that `/home` answers
   200 with it. The value never appears in argv, stdout or a file outside a 0700 temp dir.
3. `throughput.yaml` maps the Secret to `PB_SESSION_TOKEN` and passes
   `-H 'Cookie: token=$(PB_SESSION_TOKEN)'`; the kubelet expands `$(...)` when it starts the pod.

Tokens expire after 3600 s (`TOKEN_EXPIRY_SECONDS`). `deploy.sh` and `restart.sh` both refresh the
cookie, and `TP_PRE_HOOK=session.sh` lets the harness refresh it before each throughput Job.
hey runs with `-disable-redirects`: an expired cookie shows up as `[302]` responses instead of
silently measuring the login page.

## Run time and the 24-hour play budget

`/home` serves about 11 req/s at c16 (the three Java services are capped at 500m): in the v2
validation on 2026-10-02 one 10,000-request test took 902 s keep-alive and 930 s with a new
connection per request (Hubble on), each with 10,000 x [200] and no errors. The six tests of a run
take about 92 minutes and a full run about 2 hours. `app.env` therefore sets `TP_TIMEOUT_S=2400`
(the harness default of 900 s per test killed the first validation test) and `RUN_TIMEOUT=10800`.
The 15 runs (about 30 hours) do not fit one play, and two reps do not
fit the 20-hour budget either (about 21.8 hours), so PLAN.json gives bank one play per rep
(`run_matrix.sh bank --rep-list "1"`, `"2"`, `"3"`). The condition order of a rep depends only on
app and rep, and every overhead is the paired difference within a rep, so a rep never mixes hosts;
`meta.json` records the play and the machines of every run, and `analyze.py` pairs only runs of one
rep on the same host set.

## Restart before every run

`restart.sh` restarts the two databases first, then every other running Deployment, waits for old
pods to go, refreshes the cookie and checks `/home`. Users signed up in earlier runs are gone after
a restart; the demo user comes back with the seed data.

## Images

All nine application images and the generator are digest-pinned, as in the thesis manifest.
