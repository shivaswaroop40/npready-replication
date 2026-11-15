# TeaStore: two-journey evaluation, observation-sufficient, 2026-09-06

Fifth application under the two-journey protocol. TeaStore (Descartes Research) uses a service
registry for discovery, so most inter-service edges are not declared in configuration, and its
shipped load profiles separate browsing from buying. It is included as a fifth independent
application; it lands as a second observation-sufficient case alongside Online Boutique.

- Application: TeaStore (`descartesresearch/teastore-*`), the ribbon single-webui deployment,
  7 services in namespace `teastore` (webui, auth, image, recommender, persistence, registry, db).
- **Journey A (generation)**: browse, reproducing TeaStore's own `teastore_browse.lua` sequence
  (login, category, product, add-to-cart, profile) as Locust, 20 minutes, all four observers on.
- **Journey B (evaluation)**: buy, reproducing `teastore_buy.lua` (the browse sequence plus the
  order and confirm steps), 20 minutes.
- Attack set: 7 edges from a compromised identity to the database or a service it never uses
  (`attacks/A_teastore.json`).

## Result

Journey B needs 12 service edges. Over-privilege was 0.000 for every tool; no attack edge appeared
in browse traffic.

| tool | false-deny vs B | live app-edge drops |
|---|---|---|
| synth (ours) | 0.000 | 4 |
| synth + config | 0.000 | 2 |
| Otterize | 0.000 | 0 |
| IG snapshot_socket | 0.000 | 2 |
| IG trace_tcp | 0.083 | (loop) |

Journey A (browse) already observed the full functional graph, including the edges resolved through
the registry (`webui`$\rightarrow${`auth`, `image`, `persistence`, `recommender`},
`auth`$\rightarrow$`persistence`, `persistence`$\rightarrow$`db`), because Hubble records the actual
flows regardless of how the service addresses are discovered. The buy journey reaches the same
service edges, so observation of the browse journey suffices and every observer denies nothing of
journey B. Configuration declares only the registry and database edges (6), all of which observation
already saw, so fusion adds nothing here.

The few live drops (2 to 4 on application edges under each policy) are the recommender re-reading
`persistence` on its periodic retraining timer, an event-gated edge that did not fire during every
window; the remaining drops in the raw counts are to unresolved or external sources and are excluded.
No policy broke the application: browse and buy both complete under every generated policy.

> **Correction 2026-10-08:** the sentence above is not supported by the stored artifacts. Each
> `enforce/<tool>/locust_B.txt` stops after start-up and holds no success or failure counts, and the
> `trace_tcp` policy dropped 204 packets on the JDBC pool `persistence`->`db`. Whether browse and buy
> completed under each policy was not recorded.

## Where it sits in the taxonomy

TeaStore is the second observation-sufficient application (with Online Boutique). Together the five
applications are: observation sufficient (Boutique, TeaStore); observation insufficient and
configuration recovers it (Bank of Anthos, OpenTelemetry demo); observation insufficient and
configuration cannot recover it (DeathStarBench social).

## Caveats
- One run through the protocol.
- The journeys reproduce TeaStore's shipped `.lua` load profiles as Locust rather than running its
  Java LIMBO driver; the request sequences are TeaStore's, the harness is ours (as for Boutique and
  OTel).
- Registry-based discovery means configuration declares few edges; this does not affect the result,
  because observation already covers journey B.

## Files
`manifests/`, `workloads/` (browse and buy locustfiles, deployments), `captureA/`, `captureB/`,
`policies/`, `attacks/`, `enforce/`, `scores/`, `teastore_capture.sh`, `enforce_teastore.sh`,
`score_teastore.py`.
