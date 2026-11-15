# Two-journey external-validity study (canonical numbers), 2026-09-03/04

Answers the supervisor critique that generation and evaluation must use *different* benign
workloads, both authored without knowledge of the platform, with evaluation against the second
workload only and configuration used solely as an input to the tool, never as the reference.

Protocol per application: a shipped, third-party load generator drives a **generation** journey A
(all four observers on; our tool also reads the manifests); a **different** shipped journey B is the
**evaluation** workload. Policies are generated from A. Each is scored against B analytically (which
of B's legitimate edges the policy admits, which of the attack edges) and enforced live (policy
applied, every workload restarted so connections re-establish under it, journey B run 180 s, Hubble
`POLICY_DENIED` drops counted). Every number below is read from the stored `scores/scores.json` and
`enforce/<tool>/result.json` by the per-app scorer; regenerate with `<app>/score_*.py`.

## Coverage of journey B's edges, by source

| application | B edges | observation (A) | config alone | union | artifact |
|---|---|---|---|---|---|
| Online Boutique | 16 | 16 (100 %) | 16 (100 %) | 16 | `BOUTIQUE-20260903/` |
| DSB social network | 30 | 14 (47 %) | 0 (0 %) | 14 (47 %) | `DSB-SOCIAL-20260904/` |
| Bank of Anthos | 12 | 11 (92 %) | 12 (100 %) | 12 | `BANK-20260904/` |
| OpenTelemetry demo | 25 | 20 (80 %) | 25 (100 %) | 25 | `OTEL-20260906/` |
| TeaStore | 12 | 12 (100 %) | 6 (50 %) | 12 | `TEASTORE-20260906/` |

## False-deny against journey B, and live enforcement

Over-privilege was 0.000 for every tool on every application *as scored from the policy rules*; see the 2026-10-28 correction at the end (trace_tcp on Online Boutique is 1.000 under the Kubernetes isolation rule). No attack edge appeared in any
generation-journey traffic. "Live drops" counts packets denied on application edges during 180 s of
journey B under the enforced policy (external load-balancer health-check drops excluded).

**Online Boutique** (B needs 16 edges, |A|=8):

| tool | false-deny vs B | live drops |
|---|---|---|
| synth (ours) | 0.000 | 0 |
| synth + config | 0.000 | 0 |
| Otterize | 0.000 | 0 |
| IG snapshot_socket | 0.000 | 0 (32 external health-check only) |
| IG trace_tcp | 0.938 | 600 | over-privilege 1.000 under the isolation rule (correction below) |

**DSB social network** (B needs 30 edges, |A|=8):

| tool | false-deny vs B | live drops |
|---|---|---|
| synth (ours) | 0.533 | 1942 |
| synth + config | 0.533 | 2011 |
| Otterize | 0.833 | 3249 |
| IG trace_tcp | 0.833 | 3260 |
| IG snapshot_socket | 0.267 | 2052 |

Every tool severed `nginx-thrift`→`compose-post-service` and took composing offline. The 16 edges the
synthesiser misses are the entire compose chain, which the timeline-read journey never fires.

**Bank of Anthos** (B needs 12 edges, |A|=8):

| tool | false-deny vs B | live drops | note |
|---|---|---|---|
| synth (ours) | 0.083 | 264 | all on `frontend`→`ledgerwriter` (payment/deposit); `/payment` and `/deposit` 100 % fail |
| **synth + config** | **0.000** | **0** | 12 drops were external health-check only; payments return to baseline latency |
| Otterize | 0.083 | 336 | all on `frontend`→`ledgerwriter` |
| IG trace_tcp | 0.333 | 210 | frontend hop, pre-DNAT port (50 further drops were unidentified peers) |
| IG snapshot_socket | 0.500 | 40 | login path |

## The taxonomy this establishes

- **Observation sufficient** (Online Boutique and TeaStore): every dependency is exercised by any browsing session, so
  A's edges already cover B's. Configuration adds nothing it needs.
- **Observation insufficient, configuration recovers it** (Bank of Anthos and OpenTelemetry demo): journey A (sign-up) never fires the
  payment edge journey B needs; configuration declares it; fusion supplies it live at zero drops and
  zero security cost. This is the positive fusion result with third-party workloads on both sides.
- **Observation insufficient, configuration cannot recover it** (DSB): the missing compose chain is
  declared, but in a mounted JSON file our derivation does not parse (a tool limitation, not a
  code-only application), and the file lists every service to every service, so parsing it would
  over-declare. Fusion here would trade false-deny for over-privilege.

## The five applications

| application | case | key number |
|---|---|---|
| Online Boutique | observation sufficient | synth false-deny 0.000 |
| TeaStore | observation sufficient | synth false-deny 0.000; trace_tcp severs the JDBC pool `persistence`->`db` live (204 drops) |
| Bank of Anthos | observation insufficient, configuration recovers | synth 0.083 -> synth+config 0.000, live 264 drops -> 0 |
| OpenTelemetry demo | observation insufficient, configuration recovers | synth 0.200 -> synth+config 0.000, checkout fan-out severed then restored; live drops 342 / 0 / otterize 0 / snapshot 256 / trace_tcp 380 |
| DeathStarBench social | observation insufficient, configuration cannot recover | every tool severs the compose chain; config finds 0 (JSON, over-declares) |

Over-privilege was 0.000 in 24 of 25 tool-and-application cells, and 1.000 for trace_tcp on Online Boutique (executed on a local Cilium cluster 2026-10-28, see ATTACK-EXEC-20261028/; no attack edge appeared in any
generation-journey traffic. Sock Shop was attempted and is inconclusive (checkout broken in the
shipped images), recorded separately and not counted.

## What this study makes the headline result (added 2026-09-08)

The taxonomy above is the visible output, but three sharper statements come out of it, and the
thesis has been reordered to lead with them.

1. **The security axis carries no information.** 25 of 25 cells at over-privilege 0.000, on top of
   bit-identical security numbers across the earlier three runs. Every distinction between these
   generators is on the deployability axis, so a "policy generation" benchmark that reports attack
   blocking is reporting a constant.

2. **Policy safety is bounded by journey coverage, and nothing in-band detects it.** The same
   synthesiser, unchanged code, scored 0.000 / 0.000 / 0.083 / 0.200 / 0.533 across the five
   applications. The only variable was whether the shipped journey A reached the code paths journey
   B needs; that spread is comparable to the spread between the five tools. There is no signal for
   it inside the generation traffic, because a policy admits the flows it was built from, so
   grading it against its own window measures transcription. A held-out workload is the only thing
   that produces a number.
   *Caveat, stated in ch8:* five pairs, one per application, so this data does not separate "the
   workload pair decides" from "the application decides". Holding one application fixed and
   swapping which shipped journeys play A and B would settle it and is the cheapest experiment left.

3. **A fraction of edges is the wrong unit.** Bank: 11 of 12 edges admitted (0.083) and every
   payment failed; snapshot_socket 6 of 12 (0.500) and every login failed. Sixfold difference in
   the fraction, same operational outcome. TeaStore fused: 0.000 and still 2 live drops that
   changed nothing. Published generator evaluations report exactly these fractions.

**Capture mechanism (replicated here, claim C3).** trace_tcp cannot see a pool opened before the
window. Boutique: 1 rule, 0.938, 600 drops, 100% failure. TeaStore: severs the JDBC pool alone,
204 drops. The mirrored fault: snapshot_socket's best-in-class 25 pairs on DSB came from sockets
the graph-loading job left open, which is neither journey. This is a property of the sensor, so it
does not depend on n.

**Fusion is demoted to a partial remedy.** Positive on Bank and OTel (two independent replications,
live, zero security cost), unnecessary on Boutique and TeaStore, and zero on DSB. Quote it with the
DSB case attached.

## Corrections this study forces on earlier text

1. **Sock Shop checkout edges.** Attempted with the vendor's official Locust (which places orders);
   Sock Shop's checkout is broken in the shipped image combination (carts `Unsupported OP_QUERY`
   against a modern Mongo; front-end crash on `POST /orders`), so no order-fan-out edge ever leaves
   the front-end and journey B reached the same 10 edges as journey A. Inconclusive, not used as a
   data point (`SOCKSHOP-20260904/PARTIAL-INCONCLUSIVE.md`). The earlier claim that these edges are
   "event-gated dependencies the driver did not trigger" is corrected: they do not fire even under
   the vendor's order-placing script, because checkout errors inside the application. This is an
   application-health boundary, not an observation ceiling.
2. **A tool change was made during the study and recorded.** The derivation did not parse JDBC URLs
   (`jdbc:postgresql://host:5432/db` read as host `jdbc`), so Bank's `ledger-db` edges were missed.
   Fixed generically with a regression test before Bank's capture ran; `netpol-readiness v0.2.1-jdbc`.
   The deciding Bank edge, `frontend`→`ledgerwriter`, is a plain `host:port` declaration unaffected
   by the fix.

## Caveats (also in each app README)

- Each application was run through the protocol **once**; the three-run study establishes the
  instrument's stability, this study establishes external validity, and neither substitutes for the
  other.
- Boutique's journey B is not adversarial: Google's default mix already includes checkout, so B's
  edges are a subset of A's. It is a genuine held-out test but not a demanding one.
- The platform's workload is still author-written; the three OSS applications remove that bias, the
  platform does not.
- Do not read the Locust/wrk2 failure percentages as the policy effect. Bank's authenticated journey
  already reports ~63 % check failures unprotected; the drops and per-endpoint latency are the signal.

## OTel n/r cells closed (2026-09-10)

The 6 Sept OTel run enforced only our two policies live; Otterize, IG snapshot_socket and IG
trace_tcp were scored on paper only. That left the single row where a competitor beats us untested,
so all three were enforced live on 2026-09-10 (`OTEL-20260906/enforce_missing_three.sh`, demo
redeployed from the pinned manifest). App-edge drops, excluding the 336-drop journey-B driver
constant that appears under every policy: synth 342, synth+config 0, **Otterize 0**, snapshot 256,
trace_tcp 380.

- Otterize equals the fused policy live on this application. It is the only application in the study
  where that happens, and it must be stated when the OTel row is quoted.
- trace_tcp's 380 drops are Kafka producers, a Redis pool and gRPC flag streams: a third independent
  replication of the capture-mechanism result after Boutique (gRPC) and TeaStore (JDBC).
- A first attempt was discarded as contaminated: the shipped `loadgenerator` was still running
  through the journey-B window. It is scaled to zero in the script.



## Correction 2026-10-28: over-privilege under the Kubernetes isolation rule

The per-app scorers compute over-privilege from the ingress rules of the rendered policies. A
workload that no NetworkPolicy selects is, by the specification, non-isolated and accepts every
source. `scripts/reproduce_from_policies.py` now applies that rule (output
`REPRO-FROM-POLICIES-20261028.txt`). In 24 of 25 cells every attack target is selected by a policy
whose allow-list excludes the attack source, so the stored 0.000 stands. In the 25th, `trace_tcp` on
Online Boutique, the rendered policy selects only `frontend` (the one connection the tracer saw), so
`cartservice`, `checkoutservice`, `emailservice`, `paymentservice` and `redis-cart` are non-isolated
and all 8 attack edges would pass: over-privilege 1.000. Reachability of the held-out attack edges
without a policy follows from the default-allow model and from each edge targeting a port the
destination Service serves (checked against the stored manifests); denial of non-admitted
connections by the CNI is demonstrated by the POLICY_DENIED drops the live runs recorded on these
same policies. The attack edges themselves were not executed.


## Executed 2026-10-28: the attack edges were run, not only scored

On 2026-10-28 every held-out attack edge was executed on a local kind cluster with Cilium v1.16.5
(not the Ankra cluster; `ATTACK-EXEC-20261028/env.json`). Each application was deployed from the
same stored manifests, and each attack edge was a TCP connect from a pod carrying the source
workload's identity to a destination pod, run unprotected and then under each generated policy. The
executed over-privilege equals the analytical over-privilege in every cell:

- unprotected: all 39 attack edges reachable (Bank's userservice needed its GCP tracing exporter
  disabled to boot outside GCP; once serving, the last edge connected);
- under policy: 0.000 for synth, synth+config, Otterize and snapshot on all five applications;
  1.000 for `trace_tcp` on Online Boutique (its single policy selects only the frontend, leaving the
  five attack targets non-isolated); 0.000 for `trace_tcp` on the other four.

Full table and per-edge logs: `ATTACK-EXEC-20261028/RESULTS-ATTACK-EXEC.md` and `per-app/*.json`.

**2026-11-09 rerun on k3s (run of record):** `ATTACK-EXEC-K3S-20261109/` (k3s v1.36.3, two nodes, Cilium v1.16.5, kube-proxy replacement, Hubble). All 234 probes agree with the kind run edge by edge; same table.
This supersedes the "computed, not executed" framing of the correction above.

## Admitted ingress pairs beyond L_B (2026-11-04)

Per tool and application, the ingress identity pairs a policy admits that journey B did not use
(`P_ing \ L_B`, same ingress filter as the scorers): 0 everywhere except IG snapshot on DSB (3),
synth+config on Bank of Anthos (3) and synth+config on the OpenTelemetry demo (8). The fused
policy's extra pairs are all declared-only. On the OpenTelemetry demo the fused policy admits 33
ingress pairs (51 over all destinations), 25 of them in L_B. Source: `EXCESS-20261104/`
(`excess.py`, `output.txt`), which cross-checks every |P| against the stored `scores.json`.

## Audit 2026-11-05: which adapter rule the held-out scorers use, and what the uniform rule changes

Source: `HELDOUT-UNIFORM-20261105/` (`rescore_heldout.py`, `output.json`, `output.txt`, `README.md`,
`MANIFEST.sha256`). The script reads the stored files under each application directory in place,
checks 163 input hashes, and passes 395 of 395 checks (285 field-by-field against each stored
`scores/scores.json`, 110 against `tab:twojourney` as printed on 2026-11-05). The sections above
are kept as history; where they differ from this section, this section holds.

**Rule.** The five held-out scorers apply tool-specific retention rules. `trace_tcp` keeps connect
events only, which carry the Service port (pre-DNAT). `snapshot_socket` keeps ESTABLISHED TCP only,
with direction from a hand-written `KNOWN_PORTS` list. Otterize keeps in-namespace clients only. The
live policies were rendered from these adapters, so every table above keeps the stored values: the
analytic score and the live drops in a row describe the same enforced policy.

**Uniform-rule sensitivity** (`cells_changed`, `table`, `apps.<app>.tools.<tool>.{stored,uniform}`).
One cell changes: DSB IG `snapshot_socket`, |P| 25 -> 38, beyond L_B 3 -> 10, false-deny
0.267 -> 0.100, over-privilege 0.000 -> 0.000. Its adapter dropped 19 UDP sockets with a remote port:
15 to `jaeger:6831` from 12 services and 4 from `nginx-thrift` to `kube-dns:53`
(`facts.dsb_snapshot_udp`). They add 13 pairs, 5 of them L_B edges, all to `jaeger`. L_B is the same
set under both rules in all five applications. Over-privilege is 0.000 in every allow-list cell;
Boutique `trace_tcp` stays 1.000 under the isolation rule. No ranking or direction changes.

**trace_tcp live outages, re-attributed** (`facts.boutique_trace_tcp_entry_port`,
`facts.bank_trace_tcp_entry_port`). The Boutique outage (600 drops, 21 of 21 Locust requests failed)
and the Bank drops (210 counted, plus 50 from `reserved:world` excluded) all fall on
`loadgenerator-b->frontend:8080`. The rendered `trace_tcp` rule admits port 80 only, because the
adapter keeps connect events (11 on Boutique, 1,288 on Bank, all to port 80); the matching accept
events (same counts) carry 8080, and a uniform render would admit 80 and 8080. No drop falls on a pair
`trace_tcp` missed; on Boutique none of those destinations has a policy and they stayed
default-allow. The connection-pool explanation holds for the analytic misses only: on Boutique all 15
misses appear only on pre-existing connections; on Bank 3 of 4 (two ESTABLISHED sockets, one through
two close events), while `frontend->ledgerwriter` has no record in capture A. No uniform-rule policy
was enforced, so no live number for one exists.

**OpenTelemetry** (`facts.otel_loadgen_and_fused`). The constant 336 drops on
`loadgen-b->frontend:8080` appear under all five policies because no stored policy has a `loadgen`
selector at all, although every adapter keeps the `loadgen->frontend` edge. `loadgen-a` and `loadgen-b`
share `app.kubernetes.io/component=loadgen`, so the cause is not a label difference. The fused
policy's 8 pairs beyond L_B are all in the declared set; 3 are declared for `frontend` itself
(currencyservice, shippingservice, flagd) and 5 exist only through `role()` prefix matching of
`frontendproxy` and `loadgenerator`, neither of which has a pod in either capture.

**TeaStore** (`facts.teastore_trace_tcp_db_pool`). `trace_tcp` recorded no connect or accept event
between persistence and db, but it did record 2 close events by `mysqld` from port 3306. It never
sees the pool's connect; the adapter discards close events. The rendered policy is deny-db (204 drops).
