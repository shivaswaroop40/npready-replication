# DeathStarBench social network: two-journey evaluation, 2026-09-04

Second application under the supervisor's protocol (generation workload ≠ evaluation workload,
both third-party, evaluation against the second workload only, configuration only ever an input
to our tool). Chosen because its shipped wrk2 scripts exercise different service chains, so the
evaluation journey can need edges the generation journey never fires. Boutique could not do that.

- Application: DeathStarBench `socialNetwork` at commit `6ecb097`, deployed from its Helm chart
  (27 deployments) into namespace `dsb` on the thesis cluster (`manifests/dsb-social-rendered.yaml`).
  Social graph initialised with the shipped `init_social_graph.py` on the shipped `socfb-Reed98`
  dataset: 962 users, 37,381 follows (243 failed on transient Mongo timeouts), 9,424 posts.
  `nginx-thrift` restarted before journey A so its connection pools were fresh.
- **Journey A (generation)**: the shipped `read-home-timeline.lua` under wrk2 (`-t 2 -c 8 -R 20`),
  20 minutes. All four observers on. Our tool also read the rendered chart.
- **Journey B (evaluation)**: the shipped `compose-post.lua`, same wrk2 settings, 20 minutes.
  Both scripts are DeathStarBench's, unmodified (`workloads/`). Both returned 2xx throughout
  (5,993 requests per 5-minute run, 8 timeouts).
- Attack set: 8 edges from a compromised legitimate identity to a datastore or service it never
  uses (`attacks/A_dsb.json`). Recon from a disposable namespace: **11 of 11** targets open on the
  unprotected app (`attacks/recon_result.txt`). None of the 8 appears in journey A's traffic.

## What each observer saw in journey A (service pairs, DNS excluded)

| observer | pairs | what it is |
|---|---|---|
| our synthesiser (Hubble) | 14 | the read path plus datastore heartbeats on idle pools |
| Otterize | 5 | new connections it sniffed |
| IG trace_tcp | 5 | `connect()` events only |
| IG snapshot_socket | 25 | includes the whole compose chain: thrift pools opened during graph initialisation and never closed |
| our configuration derivation | **0** | see below |

## Evaluation against journey B (30 service edges)

| tool | admitted | false-deny vs B | over-privilege | live drops | wrk2 failures | pods not ready |
|---|---|---|---|---|---|---|
| synth (ours, traffic A) | 18 | **0.533** | 0.000 | 1942 | not captured (see note) | 1 |
| synth + config (ours) | 42 | **0.533** | 0.000 | 2011 | 111/111 | 1 |
| Otterize | 5 | **0.833** | 0.000 | 3249 | 112/112 | 1 |
| IG trace_tcp | 5 | **0.833** | 0.000 | 3260 | 112/112 | 1 |
| IG snapshot_socket | 25 | **0.267** | 0.000 | 2052 | 112/112 | 0 |

The 16 edges the synthesiser's policy denies are exactly the compose chain:
`nginx-thrift→compose-post-service`, `compose-post-service→{unique-id, text, media, user,
user-timeline, home-timeline, post-storage}`, `text-service→{url-shorten, user-mention}`,
`user-mention-service→user-memcached`, `home-timeline-service→social-graph-service`, and four
jaeger span edges. None fires during a timeline read. Watching timeline reads for longer cannot
produce them. This is the observation ceiling demonstrated with third-party workloads on both
sides, which the platform result could not claim.

## Configuration derivation on DSB: a boundary, stated precisely

DeathStarBench declares its entire service graph in `service-config.json`, mounted from a
ConfigMap into every service pod. Two facts:

1. Our derivation scans mounted ConfigMap values, but the file is JSON: each hostname is wrapped in
   quotes and braces, so no token matched the Service catalogue and nothing was derived. That is a
   parser gap, not a code-only application. A tool that parsed JSON would recover the graph.
2. Seventeen services share one identical file listing all 30 addresses. Parsing it would declare
   the complete graph, every workload to every service, which is the over-permissive-configuration
   case the thesis already flags. Fusion here would trade false-deny for over-privilege.

So on this application configuration does not rescue observation, and the reason is not that the
dependencies are undeclared. The tool was not modified during the experiment.

## Caveats

- `snapshot_socket`'s 25 pairs include pools opened by the graph initialisation, which composes
  posts. Those pools would exist in production from prior real traffic too, but strictly they came
  from a workload that is neither A nor B. The synthesiser saw only packets that flowed during A.
- Two Mongo pods restarted once during initialisation under the chart's 128 Mi limits; stable after.
- Policies are ingress-only, keyed on `app` labels, one per observed destination, plus a
  deny-all-ingress baseline for every unobserved workload (allow-list semantics, matching the
  scorer). Boutique's live run lacked that baseline; it changed nothing there.
- Otterize carries no ports; its rules allow all ports between each pair.
- wrk2 prints its summary only at the end of a run. For the synth iteration the run was 300 s inside a 180 s window, so no summary was captured; 1,918 of its 1,942 drops are on the compose entry hop, the same failure the other four show at 100 %. The run length was shortened to 150 s for the remaining tools.
- The one pod not ready at the readiness cutoff in four iterations was `user-timeline-service`, still in ContainerCreating (scheduling delay, not a policy effect); `snapshot_socket`'s iteration had none.

## Files

`manifests/` rendered chart · `workloads/` shipped Lua scripts, wrk2 deployments, init job ·
`captureA/`, `captureB/` Hubble, IG, Otterize, ipmap, wrk2 output · `policies/` config-derived edges
and per-tool NetworkPolicy sets · `attacks/` set, values, recon · `enforce/<tool>/` drops, wrk2
output, pods, `result.json` · `scores/` · `dsb_capture.sh`, `enforce_dsb.sh`, `score_dsb.py`.

## Erratum 2026-11-05

The values above are under `score_dsb.py`'s tool-specific rule, which is the rule of the enforced
policies. Its `snapshot_socket` adapter keeps ESTABLISHED TCP only and dropped 19 UDP sockets with a
remote port: 15 to `jaeger:6831` from 12 services and 4 from `nginx-thrift` to `kube-dns:53`. Under the
platform's uniform rule, `snapshot_socket` is |P| 38 (stored 25), beyond L_B 10 (stored 3), false-deny
0.100 (stored 0.267), over-privilege 0.000. The 13 added pairs include 5 L_B edges, all to `jaeger`.
"Includes the whole compose chain" and the 10 compose-chain edges hold under the stored rule; the
uniform rule adds 4 more L_B edges that the synthesiser misses, all to `jaeger`. Still missed:
`nginx-thrift->compose-post-service`, `post-storage-service->post-storage-memcached`,
`user-mention-service->user-memcached`. No other cell changes. Evidence:
`../HELDOUT-UNIFORM-20261105/output.json` (`apps.dsb.tools.ig_snapshot_socket`, `facts.dsb_snapshot_udp`).
