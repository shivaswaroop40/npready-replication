# OpenTelemetry demo (manifest 1.12.0, images 1.11.1): deviations from the thesis setup

Thesis run: `results/OTEL-20260906` (journey A: 2026-09-06, 1200 s window, all observers on).
Every changed manifest field is listed in `manifest.changes.txt`, computed by `tools/prepare.py`.
`thesis/` holds verbatim copies, `thesis/SHA256SUMS` checksums.

## Manifest

| Change | Why |
|---|---|
| replicas -> 0 for grafana, jaeger, prometheus-server, frontendproxy, loadgenerator (Deployments) and otel-demo-opensearch (StatefulSet) | Thesis post-apply step (spec section 5, `enforce_missing_three.sh:29-43`), written into the manifest. The thesis applied the manifest and then scaled down, so these pods started briefly; here they never start and their images are never pulled. The end state is the same. `deploy.sh` still runs the scale commands; they are no-ops. |
| `imagePullPolicy: IfNotPresent` on the `busybox:latest` init containers of accounting, cart, checkout and frauddetection | Without a policy, `:latest` means Always, and `restart.sh` would contact Docker Hub for every restart of these four pods (rate limits, slower start). The images are pre-pulled. The init containers only wait for kafka or valkey. |
| `opentelemetry-demo-productcatalogservice` memory limit 20Mi -> 128Mi | Found in the pilot on 2026-10-02. At 20Mi the pod sat at its limit from the first requests (memory.current pinned at 20 MiB, no OOM kill), burned about 200m CPU in reclaim and stopped answering: every request to the recommendations API timed out after 20 s, so no fixed-count test could finish. On test-cluster the same pod was starved too: it was OOM-killed 5 times in 29 minutes (`captureA/pods.txt`). With a 64Mi limit it peaked at 63 MB under 100 req/s, so 128Mi leaves headroom. No other limit was changed. The app's absolute memory is therefore 108 MiB higher at most than on test-cluster, and productcatalog no longer restarts during a run. |

Kept as in the thesis:
- The Grafana Secret holds the chart's published default login. Grafana runs at 0 replicas.
- The `opentelemetry-demo-grafana-test` Pod (a Helm test hook rendered into the manifest;
  `kubectl apply` creates it). With Grafana at 0 it fails once and stays finished. It uses no CPU
  afterwards, and `restart.sh` does not touch it.
- The collector still exports to the scaled-down Jaeger, Prometheus and OpenSearch and logs export
  errors, as it did on test-cluster.
- The collector's ClusterRole for the k8sattributes processor, which watches pods cluster-wide.

Memory: the containers set limits and no requests, so requests default to the limits:
2890 MiB for the 18 running pods. CPU is unbounded.

## Steady generator (journey A)

From `workloads/loadgen-a.yaml`: `locustio/locust:2.31.5`, the browse `locustfile_A.py` (checked byte
for byte against the ConfigMap), `-u 8 -r 2`, host `http://opentelemetry-demo-frontend:8080`,
`--only-summary`, same resources and labels. Added: `--run-time ${STEADY_SECONDS}s`,
`--csv /tmp/pb/steady`, `--exit-code-on-error 0`. Pinned to cp-01 with a control-plane toleration
(thesis: on a worker).

## Fixed-count test

`GET /api/recommendations?productIds=0PUK6V6EV0&currencyCode=EUR` on the frontend (port 8080; the
front proxy is at 0 as in the thesis). The frontend calls recommendationservice, which lists the
catalogue from productcatalogservice and checks a flag in flagd. The frontend then calls
productcatalogservice GetProduct and currencyservice Convert for each of 4 recommended products
(source: `src/frontend/pages/api/recommendations.ts` and `services/ProductCatalog.service.ts` at tag
1.11.1). With EUR, every price goes through currencyservice. No login. Product 0PUK6V6EV0 is not
the one the `productCatalogFailure` flag breaks, and all flags stay at their defaults (off).

## Restart before every run

Tiers: kafka, valkey, flagd and the collector first, then every other running Deployment.
Then three 200s in a row from `TP_URL`.

## Images

The demo images are tag-pinned to 1.11.1-* on ghcr.io (`images.lock` has the digests).
`valkey/valkey:7.2-alpine` (cart store) and `busybox:latest` (wait loops) were re-pushed after the
thesis run, so those two can differ from what the thesis ran.
