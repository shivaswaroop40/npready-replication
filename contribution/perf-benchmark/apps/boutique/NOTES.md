# Online Boutique v0.10.6: deviations from the thesis setup

Thesis run: `results/BOUTIQUE-20260903` (journey A: 2026-09-03, 1800 s window, all observers on).
Every changed manifest field is listed in `manifest.changes.txt`, which `tools/prepare.py` computes
by diffing the thesis manifest against `manifest.yaml`. `thesis/` holds verbatim copies and
`thesis/SHA256SUMS` the checksums of the files read.

## Manifest

| Change | Why |
|---|---|
| `Service/frontend-external`: `LoadBalancer` -> `ClusterIP` | No cloud load balancer here (servicelb is disabled). On test-cluster this Service had an OVH LB whose health checks reached the frontend through the nodes (thesis README, note 1). That background traffic is absent here. |
| `Deployment/loadgenerator`: replicas 1 -> 0 | The thesis post-apply step (scale the shipped generator to 0, `boutique_capture.sh:36-42`), written into the manifest so a re-apply cannot start it. `deploy.sh` still runs the scale command; it is a no-op. |
| `Deployment/emailservice`: `startupProbe` added (gRPC :8080, every 2 s, up to 90 tries) | Found in the pilot on 2026-10-02. The Python server needs about 16 s at its 200m CPU limit to open :8080 on these vCPUs. Its liveness probe has no initial delay and gives up after 3 x 5 s, so the pod was killed before it ever listened and crash-looped (4 restarts in 100 s). On test-cluster it started in time (0 restarts, `captureA/pods.txt`). The startup probe only holds liveness off until the first success. The steady-state probes, resources and image are unchanged. |
| `Deployment/recommendationservice`: `startupProbe` added (gRPC :8080, every 2 s, up to 90 tries) | Found in the v2 validation on 2026-10-02: in the ig_snap run it crash-looped right after the restart (4 restarts before the window, 3 more during the run). Same cause as emailservice: a Python gRPC server at a 200m limit whose liveness probe has no initial delay and gives up after 3 x 5 s; with the IG DaemonSet on, every exec on the node also runs IG's standing BPF programs, so start-up took longer. 0 restarts on test-cluster. Same fix, steady-state probes unchanged. |

No storage, no resource or replica changes. Requests of the 11 running pods: 1.27 CPU, 1112 MiB.
They fit the two 4 vCPU / 6.5 GiB workers with room for a full rolling restart.

## Steady generator (journey A)

Journey A in the thesis was the shipped `loadgenerator` Deployment itself (Google's `UserBehavior`,
`USERS=10`, `RATE=1`). `steady.yaml` is that pod template as a Job:

- Same image tag (`loadgenerator:v0.10.6`, locust 2.43.0 inside), env, resources, service account
  and security context (uid 1000, read-only root). The baked `/loadgen/locustfile.py` was checked
  byte for byte against `workloads/locustfile_A_shipped.py`; they are identical.
- The command is the image entrypoint with its env values written out
  (`locust --host=http://frontend:80 --headless -u 10 -r 1`), plus `--run-time ${STEADY_SECONDS}s`,
  `--csv /tmp/pb/steady` (an emptyDir), `--only-summary` and `--exit-code-on-error 0`. The last two
  change only console output and the exit code, not the load.
- The `frontend-check` init container (a busybox wait loop) is dropped; `restart.sh` already waits
  until the frontend answers.
- Pinned to cp-01 with a control-plane toleration. In the thesis the generator ran on a worker.
  Here it stays off the measured workers.
- Pod labels `app=loadgenerator, journey=A` as in the thesis, plus the perfbench labels.

## Fixed-count test

`GET /product/OLJCESPC7Z` through `frontend:80`. One page load calls productcatalog, currency,
cart, recommendation (which calls productcatalog) and ad. No login. hey runs with
`-disable-redirects`, so any 3xx shows up in the status count.

## Restart before every run

`restart.sh` restarts `redis-cart` first, then every other running Deployment, waits for the
rollouts and for old pods to finish terminating, then needs three 200s in a row from `TP_URL`.
The cart store has no volume, so carts start empty in every run.

## Images

Application images are tag-pinned to v0.10.6 and resolve to the digests in `images.lock`.
`redis:alpine` is a floating tag, re-pushed on 2026-09-24, after the thesis run, so the redis-cart
image can differ from the one the thesis ran. The thesis did not record that digest.
