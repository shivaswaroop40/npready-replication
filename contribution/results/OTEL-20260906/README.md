# OpenTelemetry demo: two-journey evaluation, second fusion-positive, 2026-09-06

Fifth application under the two-journey protocol, chosen to give the fusion-positive result a second
application with third-party workloads. OTel demo (Google's Astronomy Shop lineage) declares every
service address in an environment variable, and its shipped API separates browsing from checkout, so
a browse journey never fires the checkout fan-out that a checkout journey needs, and configuration
declares that fan-out.

- Application: `opentelemetry-demo` v1.12.0, deployed from the pinned Kubernetes manifest into
  namespace `otel` (17 application services; the observability stack, opensearch/grafana/jaeger/
  prometheus/frontend-proxy, was scaled to zero to fit the cluster, leaving the collector).
- **Journey A (generation)**: browse only, built from the shipped Locust tasks (index, product,
  recommendations, ads, cart), 20 minutes, all four observers on; our tool also read the manifest.
- **Journey B (evaluation)**: checkout, the same shipped tasks plus `POST /api/checkout`, 20 minutes.
  The checkout path fans out to payment, shipping, email and currency; browsing never touches it.
- Attack set: 8 edges from a compromised identity to a datastore/bus or service it never uses
  (`attacks/A_otel.json`). Recon: 8 of 8 targets open on the unprotected app.

## Result

Journey B needs 25 service edges. Over-privilege was 0.000 for every tool; no attack edge appeared
in browse traffic.

| tool | admitted | false-deny vs B | over-priv. |
|---|---|---|---|
| synth (ours, traffic A) | 26 | 0.200 | 0.000 |
| **synth + config (ours)** | 51 | **0.000** | 0.000 |
| Otterize | 23 | 0.080 | 0.000 |
| IG trace_tcp | 4 | 0.840 | 0.000 |
| IG snapshot_socket | 21 | 0.160 | 0.000 |

The five edges the browse-trained synth policy denies are exactly the checkout fan-out:
`checkoutservice`$\rightarrow${`currencyservice`, `emailservice`, `paymentservice`, `shippingservice`}
and `shippingservice`$\rightarrow$`quoteservice`. Configuration declares all five, so synth+config
denies none.

## Live enforcement (targeted)

OTel's dependency chains make a full restart of all 17 services under each policy impractical, so the
live check was targeted at the edge that matters: apply the policy, restart the checkout path
(`checkoutservice` and `frontend`) so its pooled connections re-establish under the policy, run
journey B for 180 seconds, count drops (`enforce/`).

- **synth**: 678 drops. The checkout fan-out is severed:
  `checkoutservice`$\rightarrow$`paymentservice`, `$\rightarrow$shippingservice`,
  `$\rightarrow$currencyservice`, 114 drops each. `POST /api/checkout` fails.
- **synth + config**: those three edges drop **zero** packets; checkout completes.
- A constant `loadgen`$\rightarrow$`frontend:8080` drop count (336) appears under both policies and
  cancels out of the comparison; it is the load generator's own ingress and does not affect the
  checkout-fan-out result.

This reproduces the Bank of Anthos fusion result on a second application: observation of the
generation journey misses a real dependency, configuration supplies it, and the fused policy admits
it live at zero security cost.

## Caveats

- One run through the protocol.
- The observability stack was scaled to zero; the collector was kept, so services export traces
  normally. This does not change the application dependency graph being measured.
- Live enforcement is targeted at the checkout path rather than a full 17-service restart; the other
  four applications had the full restart. The analytical false-deny (0.200 to 0.000) is the primary
  result; the targeted live run confirms its direction.

## The other three tools, enforced live (added 2026-09-10)

The 6 Sept run enforced only `synth` and `synth_plus_config`. The remaining three were scored on
paper but not enforced, which left the one row where a competing tool beats ours untested. They
were run on 2026-09-10 under the same targeted protocol (`enforce_missing_three.sh`); the namespace
had been torn down, so the demo was redeployed from the same pinned manifest first.

| tool | app-edge drops | minus the 336 driver constant | what it severed |
|---|---|---|---|
| synth (6 Sept) | 678 | **342** | `checkout`->{`payment`,`shipping`,`currency`}, 114 each |
| synth + config (6 Sept) | 336 | **0** | nothing |
| Otterize | 336 | **0** | nothing |
| IG snapshot_socket | 592 | **256** | `checkout`->`productcatalog` (128), `checkout`->`cart` (128) |
| IG trace_tcp | 716 | **380** | `accounting`->`kafka` (112), `frauddetection`->`kafka` (106), `checkout`->`kafka` (106), `cart`->`valkey` (10), five `*`->`flagd` gRPC streams |

Two things follow.

**Otterize matches the fused policy here.** It drops nothing live, so on this application it is as
safe to enforce as observation fused with configuration, and safer than observation alone. This is
the only application in the study where a competing tool equals the fused result, and reporting it
is the reason the run was done.

**trace_tcp fails on pools again, on a third protocol family.** Its 380 drops are Kafka producer
connections, a Redis pool and gRPC feature-flag streams, all opened once at pod start. Together
with Boutique (gRPC) and TeaStore (JDBC) this is the third independent replication of the
capture-mechanism result.

Two conditions had to be corrected before the numbers were valid, and a first attempt was discarded:
the shipped `loadgenerator` was still running and driving journey-A-like traffic through the
journey-B window, and `frontendproxy` had not finished terminating. Both are scaled to zero in the
script. Edge naming matches `score_otel.py`'s `role()` so these figures are comparable with the
6 Sept ones. Post-run apiserver health: ok. Namespace left deployed with no policies.

## Files
`manifests/`, `workloads/` (browse and checkout locustfiles, deployments), `captureA/`, `captureB/`,
`policies/`, `attacks/`, `enforce/`, `scores/`, `otel_capture.sh`, `enforce_targeted.sh`, `score_otel.py`.

## Erratum 2026-11-05

- The constant 336 drops on `loadgen-b->frontend:8080` appear under all five policies because no
  stored policy has a `loadgen` selector, although every adapter keeps the `loadgen->frontend` edge.
  `loadgen-a` and `loadgen-b` share `app.kubernetes.io/component=loadgen`, so the cause is not a
  differently labelled driver.
- The fused policy's 8 pairs beyond L_B are all in the declared set. Only 3 are declared for
  `frontend` itself (currencyservice, shippingservice, flagd). The other 5 (`frontend->frontend`,
  `frontend->imageprovider`, `frontend->loadgen`, `frontend->opentelemetry-demo-jaeger`,
  `loadgen->flagd`) exist only through `role()` prefix matching of `frontendproxy` and
  `loadgenerator`, neither of which has a pod in either capture.
- No score in this directory changes under the uniform rule. `scores/scores.json` has an empty live
  block; the live numbers come from `enforce/*/result.json`.
- Evidence: `../HELDOUT-UNIFORM-20261105/output.json` (`facts.otel_loadgen_and_fused`).
