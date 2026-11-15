# TeaStore (ribbon): deviations from the thesis setup

Thesis run: `results/TEASTORE-20260906` (journey A: 2026-09-06, 1200 s window, all observers on).
Every changed manifest field is listed in `manifest.changes.txt`, computed by `tools/prepare.py`.
`thesis/` holds verbatim copies, `thesis/SHA256SUMS` checksums.

## Manifest

| Change | Why |
|---|---|
| `imagePullPolicy: IfNotPresent` on all 7 containers | The images carry no tag, which means `:latest` and pull policy Always. `restart.sh` restarts every pod before every run and would contact Docker Hub each time (rate limits, slower start). The images are pre-pulled. All seven tags were last pushed on 2022-08-17 (`images.lock`), before the thesis run, so they are the images the thesis ran. |

Kept as in the thesis:
- `Service/teastore-webui` stays `NodePort` 30080. A NodePort needs no cloud load balancer.
- No resource requests or limits. Each image starts Tomcat through `dockermemoryconfigurator.jar`
  with `TOMCAT_HEAP_MEM_PERCENTAGE=50` (image config), which sets the heap to half of the memory
  the container sees; without a limit that is the node's memory. Workers here have 6.5 GiB against
  16 GB on test-cluster, so each JVM may grow to about 3.2 GiB instead of about 8 GiB. Absolute
  memory numbers are therefore not comparable with test-cluster; the relative comparison between
  conditions on this cluster is unaffected.
- Services register their pod IPs with the registry (`USE_POD_IP=true`).

## Steady generator (journey A)

From `workloads/loadgen-a.yaml`: `locustio/locust:2.31.5`, the browse `locustfile_A.py` (Locust port
of TeaStore's `teastore_browse.lua`: login, category, product, add to cart, profile; checked byte
for byte against the ConfigMap), `-u 8 -r 2`, host `http://teastore-webui:8080`, `--only-summary`,
same resources and labels (`run=load-test, journey=A`). Added: `--run-time ${STEADY_SECONDS}s`,
`--csv /tmp/pb/steady`, `--exit-code-on-error 0`. Pinned to cp-01 with a control-plane
toleration (thesis: on a worker).

## Fixed-count test

`GET /tools.descartes.teastore.webui/product?id=7`, anonymous. The webui asks auth whether the
session is logged in, loads the product and categories from persistence, gets recommendations
from the recommender and their products from persistence, and loads the images from the image
service. No login: the page renders for anonymous users and returns 200.

## Restart before every run

Tiers: `teastore-db` and `teastore-registry`; then `teastore-persistence`; then auth, image,
recommender and webui. The database has no volume, so every restart returns it to TeaStore's initial data set.
The pods have no readiness probes, so the end of a rollout does not mean the app is up:
`restart.sh` waits for three 200s in a row from `TP_URL`. Stale registry entries of the old pods
can cause a few errors in the first seconds; the warm-up covers that.
