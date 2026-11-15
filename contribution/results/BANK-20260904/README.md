# Bank of Anthos: two-journey evaluation with configuration fusion, 2026-09-04

Third application under the supervisor's protocol (generation workload ≠ evaluation workload, both
built from the vendor's shipped load-test classes, evaluation against the second workload only,
configuration only ever an input to our tool). Chosen because its dependencies are declared in
environment variables and its shipped Locust file has two disjoint user classes, so a journey can
need an edge the other never fires and configuration can be tested as the source that supplies it.

- Application: Bank of Anthos v0.6.10 (Google), 7 deployments + 2 StatefulSets, deployed from the
  pinned `kubernetes-manifests/` into namespace `bank` (`manifests/`). Tracing and metrics exporters
  set off (they require GCP credentials at boot).
- **Journey A (generation)**: Google's `AllTasks.UnauthenticatedTasks` (view login, view sign-up,
  sign up), verbatim, 20 minutes. All four observers on. Our tool also read the manifests.
- **Journey B (evaluation)**: Google's `AllTasks.AuthenticatedTasks` (home, payment, deposit,
  login, logout), verbatim, preceded once by Google's sign-up body so the user exists. 20 minutes.
- Tool change recorded before any capture: the derivation did not parse JDBC URLs
  (`jdbc:postgresql://ledger-db:5432/db` was read as host `jdbc`). Fixed generically with a
  regression test, tagged `netpol-readiness v0.2.1-jdbc`, before journey A ran.

## What journey A fired, and what configuration declares

| source | service pairs (DNS excluded) |
|---|---|
| our synthesiser (Hubble) | 11 |
| Otterize | 11 |
| IG trace_tcp | 8 |
| IG snapshot_socket | 6 |
| our configuration derivation | 15 |

Declared but never observed in A: `frontend→ledgerwriter`, `ledgerwriter→contacts`,
`ledgerwriter→transactionhistory`, `ledgerwriter→userservice`. `frontend→ledgerwriter` is the
payment and deposit path. Nothing observed in A was undeclared. No attack edge appears in A's
traffic or in the configuration.

## Evaluation against journey B

| tool | admitted | false-deny vs B | over-privilege | live drops | Locust failures | pods not ready |
|---|---|---|---|---|---|---|
| synth (ours, traffic A) | 16 | **0.083** | 0.000 | 264 | 140(53.85%) | 0 |
| synth + config (ours) | 24 | **0.000** | 0.000 | 12 | 115(37.34%) | 0 |
| Otterize | 11 | **0.083** | 0.000 | 336 | 114(47.50%) | 0 |
| IG trace_tcp | 8 | **0.333** | 0.000 | 260 | 5(100.00%) | 0 |
| IG snapshot_socket | 6 | **0.500** | 0.000 | 40 | 197(70.86%) | 0 |

Observation of the sign-up journey missed one edge journey B needs, `frontend→ledgerwriter`, the
payment and deposit path. Live, the synth policy dropped every packet on it (264 drops, all on that
edge) and `/payment` and `/deposit` failed 100 % with 1.5 to 2.3 s average latency as the frontend
timed out on ledgerwriter. The configuration declared that edge. With it added, the fused policy
produced zero drops on any application edge (its 12 drops are the external health-check source
`?→frontend:8080`, out of scope), and `/payment` and `/deposit` returned to the unprotected
pattern at 117 to 137 ms. Over-privilege stayed 0.000: none of the four declared-but-unobserved
edges is an attack edge. This is the fusion result with both workloads taken from the vendor's own
load test: observation was not enough, configuration supplied exactly what it missed, at no
security cost.

**Read the Locust column carefully.** Google's `AuthenticatedTasks` fail their own response checks
after logout and on login redirects even with no policy: the unprotected journey B baseline is
62.8 % "failures" (`captureB/locust_output.txt`). The policy effect is visible in the drops and in
the per-endpoint latency, not in the aggregate failure percentage.

## Attacks

8 edges from a compromised legitimate identity to a datastore or service it never uses
(`attacks/A_bank.json`). Recon from a disposable namespace: 8 of 8 targets open on the unprotected
app (`attacks/recon_result.txt`).

## Caveats

- Locust marks some journey-A requests failed because Google's sign-up helper logs the user in and
  `GET /login` then redirects; those requests still reach the frontend. Journey B carries the same
  kind of check failures on logout. Neither is a network failure.
- Both databases use `emptyDir`, so the enforcement loop's restarts re-seed them from the demo data;
  journey B signs up fresh users on start, so this does not affect it.
- Policies are ingress-only on `app` labels with a deny-all-ingress baseline for unobserved
  workloads; Otterize rules carry no ports.

## Files

`manifests/`, `bank-all.yaml` · `workloads/` shipped locustfile, journey A/B files and deployments ·
`captureA/`, `captureB/` · `policies/` config-derived edges and per-tool NetworkPolicy sets ·
`attacks/` · `enforce/<tool>/` · `scores/` · `bank_capture.sh`, `enforce_bank.sh`, `score_bank.py`.

## Erratum 2026-11-05

`trace_tcp`'s live drops are 210 on `loadgenerator-b->frontend:8080` (plus 50 from `reserved:world`,
excluded from the reported count). The rendered rule admits port 80 only, because `score_bank.py`'s
adapter keeps connect events (1,288, all to the Service port 80); the 1,288 matching accept events
carry the pod port 8080. No drop falls on any of the 4 pairs `trace_tcp` missed. Three of those misses
appear only on connections already open (two ESTABLISHED sockets, one through two close events);
`frontend->ledgerwriter` has no record in capture A. Pooled connections therefore explain 3 of the 4
analytic misses, not the live drops. No score in this directory changes under the uniform rule.
Evidence: `../HELDOUT-UNIFORM-20261105/output.json` (`facts.bank_trace_tcp_entry_port`).
