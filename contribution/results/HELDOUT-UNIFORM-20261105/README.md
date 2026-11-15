# HELDOUT-UNIFORM-20261105: the held-out study rescored under the uniform adapter rule

## What this is

`rescore_heldout.py` rescores the five held-out applications of the two-journey study (thesis
Section `sec:twojourney`, Table `tab:twojourney`) from their stored raw captures. It does three
things.

1. **Stored.** It re-implements the tool-specific adapters of the five stored scorers line by
   line and recomputes every field of each application's `scores/scores.json`. The scorers are
   `BOUTIQUE-20260903/score_boutique.py`, `DSB-SOCIAL-20260904/score_dsb.py`,
   `BANK-20260904/score_bank.py`, `OTEL-20260906/score_otel.py` and
   `TEASTORE-20260906/score_teastore.py`. They share one template and differ only in the
   namespace, the role list, the `role()` variant and the `KNOWN_PORTS` set, which the script
   copies per application.
2. **Uniform.** It scores every application and tool again under the uniform rule of
   `RESCORE-20261104/rescore_platform.py`, the rule the thesis states in Section
   `sec:generators` for the single-window study.
3. **Facts.** It records, as data, the facts behind the held-out text corrections listed under
   "Facts" below.

The stored scorers use tool-specific retention rules:

- `trace_tcp` keeps connect events only, with the pre-DNAT Service port.
- `snapshot_socket` keeps ESTABLISHED TCP sockets only and sets direction from a hand-written
  `KNOWN_PORTS` list.
- Otterize keeps clients in the application namespace only.
- The flow synthesiser maps `reserved:host` to `kube-apiserver` and drops self pairs.

## How to run

    python3 rescore_heldout.py                   # about 20 s
    python3 rescore_heldout.py --write-manifest  # only to re-record the input hashes

Python 3 with PyYAML, which is used only to parse the stored policy YAMLs. The script imports
nothing from the stored scorers or from any other directory. It reads its inputs in place
under `contribution/results/<APP>/` and never writes there. It writes `output.txt` (its stdout)
and `output.json` next to itself.

It exits 1 if any input hash differs from `MANIFEST.sha256` or any check fails, either a
stored-score comparison or a `tab:twojourney` value. The run recorded here exited 0.

## Inputs

163 files, 3,387,803,207 bytes, almost all of it Hubble captures. `MANIFEST.sha256` holds the
sha256 of every input, with paths relative to `contribution/results/`. Every run checks each
hash and prints OK or BAD. Per application the script reads:

- `captureA/`: the Hubble capture, `ig_tcp.json`, `ig_snap.json`, `ipmap.json`,
  `otterize_t1.json` and `pods.txt`;
- `captureB/`: the Hubble capture and `pods.txt`;
- `attacks/A_<app>.json` and `policies/config_derived_edges.json`;
- `policies/netpol_<tool>.yaml` for all five tools;
- `enforce/<tool>/result.json`, `pods_after_restart.txt` (where present) and `hubble_drops.json`;
- the journey-A and journey-B load-generator manifests under `workloads/`, where present;
- `scores/scores.json` and the stored scorer (hashed only).

`RESCORE-20261104/rescore_platform.py` is also hashed, as the reference for the rule. It is not
imported.

## The uniform rule as applied here

The script applies the relaxations of `rescore_platform.py` (`RELAX_ALL` plus the synthesiser's
API-server mapping) to the held-out adapters. Each adapter keeps its own role map, `role()` and
`ns_role()` of the stored scorer.

| Adapter | Uniform rule |
|---|---|
| Flow synthesiser (Hubble), and `L_B` from journey B | Non-reply flows with a TCP or UDP destination port. Sources must be workload roles: reserved `world`, `host`, `remote-node` and `health` sources are skipped, as on the platform. A `kube-system` source maps to DNS, as `features/resolve_roles.py` does on the platform. A source in another namespace is kept when `role()` of its pod name maps it. `reserved:kube-apiserver` and `reserved:host` map to `kube-apiserver`, as `resolve_roles.py` does. Self pairs are kept. |
| Fused policy | The uniform synthesiser edges plus the stored `config_edges()`, unchanged. |
| Otterize | Clients in every namespace except the attack namespaces, mapped by `role()` of their name. Intents to the application namespace, to `kube-system` (DNS) and to `default/kubernetes` (`kube-apiserver`). Self pairs kept. |
| IG `trace_tcp` | Connect events (pod to peer, on `dst.port`) and accept events (peer to pod, on the pod's own `src.port`). A peer that is not in the ipmap and is a global address maps to `world`. Close events are not kept. |
| IG `snapshot_socket` | ESTABLISHED TCP sockets and UDP sockets with a remote port. Both sides are kept at port granularity. Self pairs kept. |

`L_B` is the ingress subset of the uniform Hubble edges of journey B. It drops the destinations
`kube-dns`, `world`, `kube-apiserver`, `node` and `remote-node`. False-deny is
`|L_B \ P| / |L_B|`. Over-privilege is `|A ∩ P| / |A|` under the allow-list model. *Beyond `L_B`*
counts the pairs in `P` whose destination is outside that list and that `L_B` does not hold,
as in the note to `tab:twojourney`.

**Direction of a `snapshot_socket` socket.** `rescore_platform.py` treats a socket as client
side when its remote port is below 32768. Online Boutique serves gRPC on port 50051, above that
threshold. There the threshold reverses the client-side sockets and adds three pairs that no
tool reported: `paymentservice->checkoutservice`, `shippingservice->checkoutservice` and
`shippingservice->frontend`. The headline therefore sets direction from the capture itself. A
socket is server side when its local port is one on which the same role holds a LISTEN socket
in the same snapshot, and client side in the converse case. If neither holds, the platform
threshold decides. The literal threshold rule is reported as the sensitivity
`snapshot_eph_direction`. It changes no false-deny or over-privilege value in any application.
It changes `|P|` only on Online Boutique (16 to 19, beyond `L_B` 0 to 3).

**Isolation rule.** For Online Boutique the script also computes over-privilege under the
isolation rule of Section `sec:metrics`: an attack edge counts as admitted when no policy
selects its target or a policy admits it. The stored renderer for Online Boutique wrote one
policy per destination that has an ingress edge. The script checks this against the five
stored YAMLs and uses the same rule for the uniform edges.

**Port granularity.** The stored scorers report pair granularity only. The script also scores
the port-carrying tools at `(src, dst, port)` granularity against the journey-B Hubble triples.
These values are computed here and do not exist in any stored score file.

## Checks

| Group | PASS | FAIL |
|---|---|---|
| Stored `scores/scores.json`, field by field (Online Boutique 63, DSB 63, Bank of Anthos 63, OpenTelemetry demo 38, TeaStore 58) | 285 | 0 |
| `tab:twojourney` as printed on 2026-11-05 (`\|L_B\|`, `\|A\|`, and per tool `\|P\|`, beyond `L_B`, false-deny, over-privilege), from the stored adapters | 110 | 0 |
| Input hashes | 163 OK | 0 BAD |

The stored live-enforcement blocks are compared for every entry they hold. The stored
OpenTelemetry `scores.json` holds an empty live block, and the stored TeaStore `scores.json` has
no `trace_tcp` entry, although `enforce/<tool>/result.json` exists for them. Those entries are
listed under `apps.<app>.live_entries_not_in_stored_scores` and are not compared.

The script also checks each stored `policies/netpol_<tool>.yaml` against the stored adapter's
ingress triples (`apps.<app>.render_check`). All 20 policies of Online Boutique, DSB, Bank of
Anthos and TeaStore equal their adapter output exactly. On the OpenTelemetry demo, every policy
lacks the adapter's `loadgen` source edges. The fused policy also lacks
`frontend->loadgen:8089` and `frontend->opentelemetry-demo-jaeger:16686`, whose destinations have
no policy.

## Results: stored against uniform

Pair granularity. `|P|`, beyond `L_B`, false-deny against journey B and over-privilege
(allow-list; for Online Boutique also the isolation-rule value after the slash). From
`output.json` `table`.

| Application | Tool | Stored | Uniform | Changed |
|---|---|---|---|---|
| Online Boutique (`\|L_B\|`=16, `\|A\|`=8) | flow synthesiser | 18, 0, 0.000, 0.000/0.000 | 18, 0, 0.000, 0.000/0.000 | no |
| | fused policy | 28, 0, 0.000, 0.000/0.000 | 28, 0, 0.000, 0.000/0.000 | no |
| | Otterize | 16, 0, 0.000, 0.000/0.000 | 16, 0, 0.000, 0.000/0.000 | no |
| | IG `snapshot_socket` | 16, 0, 0.000, 0.000/0.000 | 16, 0, 0.000, 0.000/0.000 | no |
| | IG `trace_tcp` | 1, 0, 0.938, 0.000/1.000 | 1, 0, 0.938, 0.000/1.000 | no |
| DSB social network (`\|L_B\|`=30, `\|A\|`=8) | flow synthesiser | 18, 0, 0.533, 0.000 | 18, 0, 0.533, 0.000 | no |
| | fused policy | 42, 0, 0.533, 0.000 | 42, 0, 0.533, 0.000 | no |
| | Otterize | 5, 0, 0.833, 0.000 | 5, 0, 0.833, 0.000 | no |
| | IG `snapshot_socket` | 25, 3, 0.267, 0.000 | **38, 10, 0.100**, 0.000 | **yes** |
| | IG `trace_tcp` | 5, 0, 0.833, 0.000 | 5, 0, 0.833, 0.000 | no |
| Bank of Anthos (`\|L_B\|`=12, `\|A\|`=8) | flow synthesiser | 16, 0, 0.083, 0.000 | 16, 0, 0.083, 0.000 | no |
| | fused policy | 24, 3, 0.000, 0.000 | 24, 3, 0.000, 0.000 | no |
| | Otterize | 11, 0, 0.083, 0.000 | 11, 0, 0.083, 0.000 | no |
| | IG `snapshot_socket` | 6, 0, 0.500, 0.000 | 6, 0, 0.500, 0.000 | no |
| | IG `trace_tcp` | 8, 0, 0.333, 0.000 | 8, 0, 0.333, 0.000 | no |
| OpenTelemetry demo (`\|L_B\|`=25, `\|A\|`=8) | flow synthesiser | 26, 0, 0.200, 0.000 | 26, 0, 0.200, 0.000 | no |
| | fused policy | 51, 8, 0.000, 0.000 | 51, 8, 0.000, 0.000 | no |
| | Otterize | 23, 0, 0.080, 0.000 | 23, 0, 0.080, 0.000 | no |
| | IG `snapshot_socket` | 21, 0, 0.160, 0.000 | 21, 0, 0.160, 0.000 | no |
| | IG `trace_tcp` | 4, 0, 0.840, 0.000 | 4, 0, 0.840, 0.000 | no |
| TeaStore (`\|L_B\|`=12, `\|A\|`=7) | flow synthesiser | 18, 0, 0.000, 0.000 | 18, 0, 0.000, 0.000 | no |
| | fused policy | 20, 0, 0.000, 0.000 | 20, 0, 0.000, 0.000 | no |
| | Otterize | 12, 0, 0.000, 0.000 | 12, 0, 0.000, 0.000 | no |
| | IG `snapshot_socket` | 12, 0, 0.000, 0.000 | 12, 0, 0.000, 0.000 | no |
| | IG `trace_tcp` | 11, 0, 0.083, 0.000 | 11, 0, 0.083, 0.000 | no |

`L_B` is the same set under both rules in all five applications. One cell changes: IG
`snapshot_socket` on DSB. Its adapter dropped 19 UDP sockets with a remote port: 15 to
`jaeger:6831` from 12 services, and 4 from `nginx-thrift` to `kube-dns:53`. Under the uniform rule
they add 13 pairs. Five of them are `L_B` edges (`media-service`, `nginx-thrift`,
`social-graph-service`, `unique-id-service` and `user-service` to `jaeger`). Still missed under
the uniform rule:
`nginx-thrift->compose-post-service`, `post-storage-service->post-storage-memcached` and
`user-mention-service->user-memcached`. Over-privilege is 0.000 in every allow-list cell under
both rules. The Online Boutique `trace_tcp` isolation-rule value is 1.000 under both rules,
because both edge sets reach only `frontend`.

Port granularity (computed here), stored against uniform:

| Application | Tool | Stored | Uniform |
|---|---|---|---|
| Online Boutique | IG `trace_tcp` | 1.000 (16/16) | 0.938 (15/16) |
| Bank of Anthos | IG `trace_tcp` | 0.417 (5/12) | 0.333 (4/12) |

Every other port-granularity value equals its pair-granularity value under the same rule
(`apps.<app>.tools.<tool>.{stored,uniform}.false_deny_port`).

Sensitivities outside the uniform rule (`apps.<app>.sensitivity`):

- `trace_tcp_plus_close`, `trace_tcp` close events kept: Bank of Anthos 0.333 to 0.250 (adds
  `ledgerwriter->balancereader`), TeaStore 0.083 to 0.000 (adds `persistence->db`),
  OpenTelemetry demo 0.840 to 0.680. Online Boutique and DSB do not change.
- `snapshot_all_tcp_states`, non-ESTABLISHED TCP sockets kept: Bank of Anthos 0.500 to 0.167,
  DSB 0.100 to 0.067. The others do not change.
- `snapshot_eph_direction`, the platform's literal direction threshold: see above.

## Facts behind the text corrections (`output.json` `facts`)

- `boutique_trace_tcp_entry_port` and `bank_trace_tcp_entry_port`. For `loadgenerator->frontend`,
  trace_tcp recorded connect events on port 80 (11 on Online Boutique, 1,288 on Bank of Anthos)
  and the same number of accept events on port 8080. `L_B` holds port 8080. The stored adapter
  and the rendered `trace_tcp` policy carry port 80 only. The uniform adapter carries 80 and
  8080, the same ports as the rendered `snapshot_socket` policy. `loadgenerator-b` carries
  `app=loadgenerator`.
  - Online Boutique: all 600 live drops are `loadgenerator-b->frontend:8080`, POLICY_DENIED
    ingress. The `trace_tcp` policy selects only `frontend`; the other eleven roles have no
    policy. None of the drops is on one of the 15 pairs `trace_tcp` missed. Those 15 pairs
    have no policy on their destination. For each of them, Hubble recorded flows in capture A,
    `trace_tcp` recorded no event of any type, and the snapshot holds ESTABLISHED sockets. The
    32 `snapshot_socket` drops all come from `reserved:world`.
  - Bank of Anthos: 210 drops are `loadgenerator-b->frontend:8080` and 50 come from
    `reserved:world`. None is on one of the four pairs `trace_tcp` missed. For three of those
    four, `trace_tcp` recorded no connect or accept event in capture A, and another record shows
    a connection that was already open. `contacts->accounts-db` and `userservice->accounts-db`
    appear as ESTABLISHED sockets in the snapshot. `ledgerwriter->balancereader` appears in 2
    `trace_tcp` close events. The fourth, `frontend->ledgerwriter`, has no Hubble flow and no
    Inspektor Gadget record in capture A.
- `otel_loadgen_and_fused`.
  - No stored policy has a selector that maps to `loadgen`. Every policy uses the label key
    `app.kubernetes.io/component`. The journey-A and journey-B generators both carry
    `app.kubernetes.io/component=loadgen`. Under every policy, 336 drops are
    `loadgen-b->frontend:8080`.
  - The fused policy admits 8 pairs beyond `L_B`, all of them in the declared set. Three are
    declared for `frontend` itself: `currencyservice`, `shippingservice` and `flagd`. Five exist
    only through `role()` prefix matching of `frontendproxy` and `loadgenerator`, neither of
    which has a pod in either capture. These five are `frontend->frontend`,
    `frontend->imageprovider`, `frontend->loadgen`, `frontend->opentelemetry-demo-jaeger` and
    `loadgen->flagd`. Of these five, the rendered fused policy admits only `frontend->frontend`
    and `frontend->imageprovider`.
- `teastore_trace_tcp_db_pool`. Between `persistence` and `db`, `trace_tcp` recorded no connect
  or accept event. It recorded 2 close events by `mysqld` on the `db` pod, from port 3306 to
  `persistence`. The adapter discarded them. The snapshot holds the pool as ESTABLISHED sockets
  on both pods. The rendered `trace_tcp` policy selects `db` with no allowed source.
- `dsb_snapshot_udp`. The UDP socket counts above, the stored and uniform scores, and the 14
  `L_B` edges that the uniform `snapshot_socket` admits and the flow synthesiser does not.

## Limits

- A uniform render of any policy was never enforced. No live drop count exists for it, and this
  artifact gives none. The live columns of `tab:twojourney` were measured under the policies
  rendered from the stored adapters.
- The renderer that wrote `policies/*.yaml` was not retained. The render check compares the
  YAMLs with the adapter output; it cannot show how the renderer chose its targets beyond what
  the YAMLs hold.
- The isolation-rule value of the uniform edge sets is computed for Online Boutique only. For
  the stored rendered policies it is computed in every application
  (`apps.<app>.isolation_rule_stored_policies`). Outside Online Boutique `trace_tcp`, every stored
  policy selects every attack target, and every value is 0.000. The uniform value for the other
  four applications would depend on how their renderer chose its targets, which was not
  retained.
- The `snapshot_socket` direction rule departs from the platform's literal threshold, for the
  reason given above. Both are reported.
- `role()` matches by prefix. It maps `frontendproxy` to `frontend` and `loadgenerator` to
  `loadgen` in the declared set of the OpenTelemetry demo. The rescore keeps the stored role
  maps and the stored `config_edges()` unchanged, so these matches remain in the fused policy
  under both rules.
- Close events and non-ESTABLISHED sockets are outside the uniform rule, as on the platform.
  Their effect is reported only as a sensitivity.
