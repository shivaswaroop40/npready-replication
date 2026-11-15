# Executed attack edges on the five held-out applications, k3s (2026-11-09)

This is the attack execution of record for the thesis. It reruns `ATTACK-EXEC-20261028/` (a kind
cluster) on k3s with the same spec, inputs and harness. Every one of the 234 probes gives the same
result as the kind run.

## Environment

A throwaway cluster on iximiuz Labs, not the Ankra-managed one (`env.json`, `raw/versions.txt`):

| item | value |
|---|---|
| Cluster | k3s v1.36.3+k3s1, two nodes (cp-01 server, worker-01 agent), pod CIDR 10.42.0.0/16 |
| CNI | Cilium v1.16.5, kube-proxy replacement, Hubble enabled, Kubernetes IPAM, VXLAN tunnel |
| Host | two Ubuntu 24.04.5 VMs (kernel 6.1.167), 4 vCPU / 7 GiB and 4 vCPU / 8 GiB |

## Inputs

Copied unchanged from the held-out study folders and checked by SHA-256 on the VM (51 files):
each application's stored manifests, `attacks/A_*.json`, `policies/netpol_*.yaml` and `score_*.py`
(used only for its `role()` mapping). `probe_k3s.py` is `ATTACK-EXEC-20261028/probe.py` with one
line changed, the kube-context (`diff` in `RUN.md`).

## Results

Attack edges reachable (lower is better). Over-privilege = reachable / |A|.

| application | \|A\| | unprotected | synth | synth+config | Otterize | snapshot | trace\_tcp |
|---|---|---|---|---|---|---|---|
| Online Boutique | 8 | 8/8 | 0/8 | 0/8 | 0/8 | 0/8 | **8/8** |
| Bank of Anthos | 8 | 8/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| DSB social network | 8 | 8/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| OpenTelemetry demo | 8 | 8/8 | 0/8 | 0/8 | 0/8 | 0/8 | 0/8 |
| TeaStore | 7 | 7/7 | 0/7 | 0/7 | 0/7 | 0/7 | 0/7 |

Executed over-privilege is 0.000 in 24 of 25 cells and 1.000 for `trace_tcp` on Online Boutique.
All 39 attack edges connect on the unprotected cluster. Compared edge by edge with
`ATTACK-EXEC-20261028/per-app/*.json`, all 234 probes (39 edges x 6 rounds) agree.

## Deviations, stated plainly

1. **TeaStore, first attempt.** The manifest has no readiness probes, so pods report Ready before
   MariaDB listens. In the first attempt (`raw/out/teastore/`) the first two unprotected probes,
   `webui->db` and `image->db`, were refused, while later probes to the same database connected.
   The run of record (`raw/out/teastore-settled/`, copied to `per-app/teastore.json`) waits 120 s
   after Ready. All 7 edges then connect unprotected. The under-policy results are 0/7 for every
   policy in both attempts.
2. **Bank of Anthos.** As in the kind run, `userservice` needs `ENABLE_TRACING=false` outside GCP.
   The other services with tracing on crash-loop (`raw/out/bank/pods_before.txt`). None is an
   attack target, and the attack sources are probe pods carrying their labels, so the result does
   not depend on them.
3. **DSB.** One probe, `media-frontend->post-storage-mongodb:27017` under the fused policy, recorded
   no pod log. It is the same edge as in the kind run and is counted as not reachable. The same
   edge is denied with return code 1 under the synthesiser policy, and the fused policy only adds
   allow rules, none for that source.
4. **OpenTelemetry demo.** It ran in full. Unlike the kind run, no component was scaled down. Only
   Grafana's Helm test pod failed; it is not part of any attack edge.

## Files

- `per-app/<app>.json`: per-edge results with each `nc` return code (run of record).
- `raw/out/<app>/`: apply log, probe log, pods with node and IP before and after probing.
- `raw/versions.txt`, `raw/cluster.log`: cluster versions and install log.
- `cluster.sh`, `run_app.sh`, `run_app_settled.sh`, `probe_k3s.py`: the harness (`RUN.md`).
