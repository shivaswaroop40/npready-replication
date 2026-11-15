# Online Boutique: two-journey evaluation (generation ≠ evaluation), 2026-09-03/04

Answers the supervisor's critique: the benign workload the policies are generated from must
differ from the one they are evaluated against, the workload must not be authored by someone
who knows the application, and the evaluation must be against that second workload only.

- Application: Online Boutique v0.10.6 (Google), 11 services, deployed to namespace
  `boutique` on the thesis cluster from the pinned release manifest (`manifests/`).
- **Journey A (generation)**: Google's shipped Locust generator, unchanged
  (`workloads/locustfile_A_shipped.py`, `USERS=10`, browse-heavy default mix). 30 minutes.
  All four observers on: Hubble (our synthesiser), Otterize, IG `trace_tcp`, IG
  `snapshot_socket`. Our tool additionally read the manifests (`policies/config_derived_edges.json`,
  28 declared edges). No other tool sees configuration.
- **Journey B (evaluation)**: a purchase-path journey built only from Google's task functions,
  verbatim, with different task selection and weights (`workloads/locustfile_B_purchase.py`,
  `loadgenerator-b.yaml`). 20 minutes of traffic recorded (`captureB/`), then used as the
  evaluation workload for every tool, including ours. Configuration is an input to our tool and
  is never used as a reference.
- Nothing about either workload was written with knowledge of the platform under test.

## Evaluation on journey B (analytical and live)

Policies were generated from journey A only (`policies/netpol_*.yaml`, ingress policies keyed
on `app` labels). Analytical: which of journey B's 16 ingress edges the policy admits, and which
of the 8 attack edges (`attacks/A_boutique.json`) it admits. Live: each policy enforced in turn,
every deployment restarted one at a time so all connections re-establish under the policy, then
journey B run for 180 s while Hubble records every `POLICY_DENIED` drop (`enforce/<tool>/`).

| tool | admitted | false-deny vs B | over-privilege | live drops | Locust failures | pods not ready |
|---|---|---|---|---|---|---|
| synth (ours, traffic A) | 18 | **0.000** | 0.000 | **0** | 1 of ~650 (0.15 %) | 0 |
| synth + config (ours) | 28 | **0.000** | 0.000 | **0** | 1 (0.15 %) | 0 |
| Otterize | 16 | 0.000 | 0.000 | 0 | 1 (0.15 %) | 0 |
| IG snapshot_socket | 16 | 0.000 | 0.000 | 32 (see note 1) | 0 | 0 |
| IG trace_tcp | 1 | **0.938** | 0.000 | **600** | **21 of 21 (100 %)** | 0 |

Held-out result: a policy generated from the browse journey admitted every connection the
purchase journey needed, with zero attack edges admitted, and it did so live. The three
single-Locust failures are transients with no matching drop.

`trace_tcp` produced one rule, `loadgenerator→frontend`, because every inter-service gRPC
connection is a pool opened at pod start and never reconnects inside the window. Its policy
took the application off the air for the load generator: 600 drops, 100 % failures. Its
one rule also carried the Service port (80) rather than the pod port (8080), because a
`connect()` tracer sees the pre-DNAT tuple. Both are properties of the capture mechanism.

## Attacks (`attacks/`)

Recon probe from a disposable namespace: 10 of 11 boutique targets open on the unprotected
cluster (`recon_result.txt`). The 11th, `emailservice:8080`, was probed on the pod port; its
Service listens on 5000, so that line is a probe error, not a block. None of the 8 attack
edges appears in journey A's benign traffic and none is declared in configuration (both
checked mechanically by the scorer).

## Notes and caveats, stated plainly

1. **The 32 drops under `snapshot_socket` are not journey B.** Source identity is
   `reserved:world` from node addresses: the OVH load balancer's health checks on
   `frontend-external`, SNAT'd through the nodes, which began appearing as two worker nodes
   rejoined the LB pool mid-run. No tool observes that edge and every tool's policy denies
   it equally. It is the external half of the ingress edge, out of scope as in the thesis.
2. **`trace_tcp`'s live YAML covered only the frontend.** The generated files carry one policy per
   observed destination and no deny-all baseline for unobserved workloads, so in the live run the
   other ten services stayed default-allow. The analytical scores assume the thesis's allow-list
   semantics (deny unless listed). Journey B's outcome for `trace_tcp` is already the worst case
   (100 % failure); a deny-all baseline would not change it, but would make its live
   over-privilege the analytical 0.000 rather than "wide open". Kept as run; noted here.
3. **Cluster capacity changed during the work.** Between the captures (3 Sept) and the
   enforcement runs (4 Sept) two of three worker nodes disappeared from the cluster; the platform
   reported `Nodes: 1`. A first enforcement attempt was invalid (pods Pending, not failing) and is
   kept in `enforce-INVALID-surge-pending/` for the record. The valid run used a sequential
   scale-down/up restart, a verified policy apply, and Sock Shop scaled to zero to free CPU
   (restored afterwards). The nodes were re-added by hand during the Otterize iteration.
4. **Journey B's edge set equals journey A's at pair granularity.** The purchase mix exercised
   the same service edges as the browse mix, because Google's default mix already includes
   checkout. The held-out test is therefore genuine but not adversarial for this application; a
   journey that reaches an edge A never did would be a stronger test. The dependencies observation
   never sees here are the ten DNS edges that fire only at pod start, which configuration declares.
5. Otterize carries no ports; its rules allow all ports between each pair.

## Files

`manifests/` pinned app manifest · `workloads/` both locustfiles and the journey-B deployment ·
`captureA/`, `captureB/` Hubble, IG, Otterize snapshots, ipmap, logs ·
`policies/` config-derived edges and one NetworkPolicy set per tool ·
`attacks/` attack set, chart values, recon result · `enforce/<tool>/` drops, Locust output,
pod state, `result.json` · `scores/scores.json`, `summary.txt` ·
`boutique_capture.sh`, `enforce_eval.sh`, `score_boutique.py` reproduce everything.

## Erratum 2026-11-05

The attribution of the `trace_tcp` live outage above is corrected. All 600 drops fall on
`loadgenerator-b->frontend:8080`, the pair the single rule was meant to admit. The rule admits
port 80 only, because `score_boutique.py`'s adapter keeps connect events (11, all to the Service port
80) and drops the 11 matching accept events, which carry the pod port 8080. A uniform-rule adapter
would admit 80 and 8080. No drop falls on any of the 15 pairs `trace_tcp` missed; those destinations
had no policy and stayed default-allow. The pool mechanism explains the 0.938 false-deny and the
1.000 isolation-rule over-privilege, not the live outage. No score in this directory changes under
the uniform rule. Evidence: `../HELDOUT-UNIFORM-20261105/output.json`
(`facts.boutique_trace_tcp_entry_port`).
