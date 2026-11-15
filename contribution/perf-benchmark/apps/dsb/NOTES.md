# DeathStarBench socialNetwork: deviations from the thesis setup

Thesis run: `results/DSB-SOCIAL-20260904` (chart @6ecb097, journey A: 2026-09-04, 1200 s window,
all observers on). Every changed manifest field is listed in `manifest.changes.txt`, computed by
`tools/prepare.py`. `thesis/` holds verbatim copies, `thesis/SHA256SUMS` checksums.
`dsb-init-job.yaml` is the thesis `workloads/dsb-init-job.yaml`, byte for byte.

## Manifest

| Change | Why |
|---|---|
| `nginx-thrift` and `media-frontend` init containers: `git clone https://github.com/dimoibiehg/DeathStarBench.git /DeathStarBench && cp ...` becomes `test "$(cat /DeathStarBench/.perfbench-commit)" = 0d49cb4d37aa1fa204bccf1a6d4a6179312ac804 && cp ...` (the same `cp` commands), with `/DeathStarBench` a read-only hostPath (`/var/lib/perfbench/dsb-src/DeathStarBench`, type Directory) | The thesis cloned the fork's HEAD (about 130 MB) from GitHub at every pod start. With a restart before every run that was two clones per run, on GitHub's availability. `dsb_src.sh` (run by `deploy.sh`) clones the fork once per play on cp-01 at `0d49cb4d`, keeps the six directories the init containers copy (676 KiB), and puts them on every worker over ssh, with a tree hash it checks on each node. The fork's HEAD has been `0d49cb4d` since 2024-05-13 (GitHub API, checked 2026-10-02), so the thesis copied the same files. The init containers still run `cp` into the same emptyDirs; if the copy is missing or not the pinned commit, the pod does not start. |

| The six `*-mongodb` Deployments: memory limit 128Mi -> 512Mi (request unchanged, 128Mi) | At 128Mi the Mongo pods are OOM-killed while the social graph is built. The thesis init lost two of them (`captureA/pods.txt`: social-graph-mongodb restarted about 9 minutes and user-mongodb about 15 minutes into the init, before journey A started), so the thesis read a partial graph whose size depended on when the kills happened. Here social-graph-mongodb was killed in every init (pilot, and twice in the v2 validation, even with the job paced to 50 connections). With 512Mi the graph is built completely and is the same in every play. Mongo memory is app memory; the observer deltas do not depend on it. These six pods move from QoS Guaranteed to Burstable. |

Nothing else changes. No Service is a LoadBalancer, and every container already had
`imagePullPolicy: IfNotPresent`. Requests of the 27 pods: 2.70 CPU, 3456 MiB (limits equal
requests, 128 MiB per container as shipped, except the six Mongo memory limits above).

## Social graph initialisation

The thesis ran `dsb-init-job.yaml` once after deploying: the shipped `init_social_graph.py` on
socfb-Reed98 with `--compose` (962 users, follows, about 9.4k posts). The benchmark does the same:
`deploy.sh` runs `init.sh` once. The mongodb, redis and memcached pods have no volumes, so a
restart would empty them; `restart.sh` therefore keeps them running (see below) and every run
reads timelines from the same graph. Journey A and the fixed-count test only read, so the
datastores do not grow between runs.

- `init.sh` records the datastore pods and their restart counts in ConfigMap `perfbench-dsb-init`.
  `deploy.sh` and `restart.sh` skip the init while that record matches. If a datastore pod was
  replaced or restarted since (an OOM kill, a node problem), `restart.sh` rebuilds the graph before
  the run (about 20-30 minutes; `RUN_TIMEOUT=7200` leaves room for it), so no run reads a partial
  graph.
- With the chart's 128 MiB limits, two Mongo pods restarted during the thesis init, and
  social-graph-mongodb was OOM-killed during both pilot inits here (with 200 simultaneous requests
  the services open many Mongo connections). `init.sh` watches the datastore pods while the job
  runs. If one restarts, it stops the job at once, empties every datastore (a rollout restart; they
  have no volumes), and runs the same job again paced to 50 simultaneous connections
  (`init_social_graph.py --limit 50`; the thesis job uses the default 200). Its JSON then reports
  `"attempts":2`. The graph is the same as a clean single run; building on top of a partial first
  graph would have left duplicate follows and posts. A restart during the second attempt fails
  the step. A rebuild before a run (a datastore replaced since the last init) also empties the
  datastores first.
- The job image is `python:3.12-slim` and runs `pip install aiohttp` (unpinned) from PyPI, as in
  the thesis. It runs on a worker, once, when the app is deployed.

## Steady generator (journey A)

From `workloads/wrk2-A.yaml`: the shipped `read-home-timeline.lua` under
`deathstarbench/wrk2-client:latest`, `-D exp -t 2 -c 8 -R 20 -L`, against
`http://nginx-thrift.dsb.svc.cluster.local:8080/wrk2-api/home-timeline/read`, same resources and
labels (`app=wrk2-client, journey=A`).

- The thesis Deployment looped `wrk -d 300; sleep 2`. The Job makes one continuous run of
  `-d ${STEADY_SECONDS}s`, so it prints one `-L` summary for the whole Job. The 8 connections are
  opened once instead of every 300 s, and the 2 s gaps are gone.
- wrk2 has no per-interval output. Its numbers cover the whole Job, warm-up included; at a fixed
  open-loop rate of 20 req/s that mainly touches the latency tail.
- Pinned to cp-01 with a control-plane toleration (thesis: on a worker).

## Fixed-count test

`GET /wrk2-api/home-timeline/read?user_id=1&start=0&stop=10` on `nginx-thrift:8080`: the journey A
endpoint with fixed arguments. nginx-thrift calls home-timeline-service, which reads
home-timeline-redis and calls post-storage-service, which reads post-storage-memcached and falls
back to post-storage-mongodb. No login. The check before the init uses `GET /` (static page),
because the timeline is empty until the init has run.

## Restart before every run

The datastores (every `*-mongodb`, `*-redis` and `*-memcached` Deployment, 15 of the 27 pods) keep
running between runs (`PB_RESTART_KEEP` in `restart.sh`). Tiers: jaeger and every service; then
`media-frontend`; then `nginx-thrift` last, so its connection pools open against the new services
(the thesis restarted nginx-thrift before journey A for the same reason). Then the init check
(normally a skip), then three 200s in a row from `TP_URL`.

Deviation from the other apps, which restart every workload: the stateless dsb services start
fresh for every run, but the datastores and their caches carry over from the previous run. The
memcached caches are warm after the first run; the 180 s warm-up before each window warms them in
the first run too. The thesis likewise built the graph once and then ran journey A against it.

## Images

`social-network-microservices:latest`, `jaeger all-in-one:latest` and `wrk2-client:latest` were
last pushed before the thesis run (`images.lock`), so they are the images the thesis ran.
`alpine/git:latest` (init containers, git clone only) and `python:3.12-slim` (init job) were
re-pushed after it.
