# Cluster notes (infra)

How the perf-benchmark cluster was built, how it differs from test-cluster, and why.
Built 2026-10-02. Exact versions and digests are in `versions.lock`.

## Play

- iximiuz Labs play `6abf7eba882cd1c296de683a` (flexbox), started 2026-10-02 09:51Z.
  Lifetime 1440 min. Persistent: at expiry it is stopped with its state kept, not destroyed.
- Machines, checked inside the VMs with `nproc` and `free -m`:

  | Machine | IP | vCPU | RAM (free -m total) | Disk | Role |
  |---|---|---|---|---|---|
  | cp-01 | 172.16.0.2 | 2 | 2981 MiB | 40 GiB | k3s server (etcd), tainted control-plane:NoSchedule |
  | worker-01 | 172.16.0.3 | 4 | 6502 MiB | 80 GiB | k3s agent |
  | worker-02 | 172.16.0.4 | 4 | 6502 MiB | 80 GiB | k3s agent |

- Rootfs ubuntu-24-04 (Ubuntu 24.04.4 LTS). Kernel 6.12.80 (iximiuz `6.12`, Firecracker).
  `/sys/kernel/btf/vmlinux` exists. Every module Cilium needs loads (vxlan, cls_bpf,
  sch_ingress, xt_TPROXY, xt_socket, xt_CT, xt_set, nf_conntrack_netlink, ...). The 6.1
  fallback was not needed.
- Root on cp-01 reaches both workers over ssh without a password (the play image ships the key).
- cgroup v2 with the systemd driver (`kubepods.slice`), as on test-cluster.

## k3s

- v1.36.3+k3s1 on all three nodes, containerd 2.3.2-k3s2 (the same containerd as test-cluster).
- Server config (`/etc/rancher/k3s/config.yaml` on cp-01): `cluster-init`, `flannel-backend: none`,
  `disable-network-policy`, `disable: [traefik, servicelb]`, `node-taint:
  node-role.kubernetes.io/control-plane:NoSchedule`, `kubelet-arg: cgroup-driver=systemd`.
- Differences from test-cluster and why:
  - One server instead of three. The play budget is 10 vCPU / 16 GiB. etcd still runs embedded
    (`--cluster-init`), as a single member.
  - `local-storage` is kept (test-cluster disabled it after 08-24 and used Cinder, which does not
    exist here). metrics-server is kept as on test-cluster.
  - No `--disable-cloud-controller` and no `cloud-provider=external`: there is no OpenStack CCM here.
  - test-cluster worker default-0 stayed on v1.36.2. Here every node runs v1.36.3.
  - coredns, metrics-server and local-path-provisioner tolerate the control-plane taint and the
    scheduler put them on cp-01. Where they ran on test-cluster is not recorded.
- With `flannel-backend: none`, k3s writes no CNI section into its containerd config, so
  containerd uses the stock `/etc/cni/net.d` and `/opt/cni/bin`. Those are the Cilium chart
  defaults, so `cilium-values.yaml` does not set CNI paths.
- Not installed (they ran on test-cluster but are not part of this benchmark): Traefik,
  cert-manager, external-dns, OpenStack CCM and Cinder CSI, Kyverno, Trivy,
  kube-prometheus-stack, the Ankra platform replica. Their background load is not reproduced.
  This is why the results are reported relative to baseline.
- Kernel sysctls are left at the image defaults (for example `fs.inotify.max_user_instances=128`,
  `nf_conntrack_max=131072` on cp-01).

## Cilium 1.19.5

- Helm release `cilium` in kube-system, chart 1.19.5, values in `cilium-values.yaml`.
  Images: cilium v1.19.5, cilium-envoy v1.36.8, operator-generic v1.19.5, hubble-relay v1.19.5
  (digests in `versions.lock`). These match test-cluster.
- Config diff. `diff_cilium_config.py` compares the live `cilium-config` key by key with the
  test-cluster dump `cilium-config-20260910.json` (155 keys, 2026-09-10). With the cluster in the
  hubble condition, which is the state test-cluster was in:

  ```
  saved keys 155, live keys 157, identical 155, changed 0, only-in-saved 0, only-in-live 2
  EXTRA     enable-hubble-open-metrics: live='false'
  EXTRA     hubble-metrics-server-enable-tls: live='false'
  ```

  All 155 saved keys are present with the same values. No node, IP or cluster-specific key
  differs: the dump holds none (`cluster-name default`, `cluster-id 0`, ipam `kubernetes`, so
  pod CIDRs live on the Node objects, not in the ConfigMap).

  The two extra keys and why they are harmless:
  - On test-cluster the Hubble metrics were added with a `kubectl patch` on 2026-07-27, which
    set only `hubble-metrics` and `hubble-metrics-server`. Here the chart sets them, and the chart
    always writes these two companion keys next to them. Both are `false`, which is also the
    agent's default when the key is absent. The running behaviour is the same.

  Three keys needed explicit values to appear at all: `debug-verbose`, `nodeport-addresses`
  and `policy-cidr-match-mode` are empty strings in the dump. The chart writes them only when
  the value key exists, so the test-cluster install values must have set them to empty values.
  `cilium-values.yaml` does the same. `controller-group-metrics` is absent from the dump, so
  `prometheus.controllerGroupMetrics` is set to an empty list.

- The other conditions change only what `bin/cond.sh` changes: `enable-hubble=false`, and the
  keys `hubble-metrics` and `hubble-metrics-server` are removed. In Cilium 1.19 the Hubble
  metrics server is a separate cell. With only `enable-hubble=false`, port 9965 stayed open on
  every node; the first cond.sh test caught this. Removing the two keys gives the agent default
  (no metrics server). That is also how test-cluster looked before the 07-27 patch.
- Hubble Relay. The thesis deployed Relay from the platform's own manifests (`hubble-relay.yaml` and
  `hubble-certgen.yaml`, client certificate minted from the `cilium-ca` secret). Here the chart
  deploys it (`hubble.relay.enabled: true`) so cond.sh can scale it. Same image (v1.19.5), same
  listen address `:4245`, same Service `hubble-relay` port 80 to 4245, same TLS settings, no
  resource requests or limits. The chart's relay config differs only in form: the peer service
  is written as an FQDN with a trailing dot, and `retry-timeout`, `sort-buffer-len-max` and
  `sort-buffer-drain-timeout` are present but empty (so they keep their defaults). The client
  certificate comes from the chart's Helm-generated CA, not from a certgen job.
- No resource requests or limits on cilium-agent or cilium-envoy (chart defaults), as on
  test-cluster. The cilium DaemonSet update strategy is the chart default (maxUnavailable 2).
- The two cilium-operator replicas landed on the workers. The analysis counts them in the
  observer group, as the contract says.

## Otterize network-mapper 3.0.47

- Helm release `network-mapper` in otterize-system (the same release name as test-cluster), chart
  3.0.47 from `https://helm.otterize.com`, default values (`otterize-values.yaml` is empty).
  Images `otterize/network-mapper:v3.0.19` and `otterize/network-mapper-sniffer:v3.0.19`.
- Deployment `otterize-network-mapper` (1 replica, Service :9090 `/query`). DaemonSet
  `otterize-network-sniffer` (hostNetwork). It has no control-plane toleration, so it runs on
  the 2 workers only, as on test-cluster (3 workers). Service `otterize-pii-detector` exists, as
  it did on test-cluster.
- Chart telemetry settings are left at the chart defaults. The test-cluster values were never
  saved; they are believed to be the defaults too.

## Inspektor Gadget v0.54.1

- `kubectl gadget deploy --image ghcr.io/inspektor-gadget/inspektor-gadget:v0.54.1` with
  kubectl-gadget v0.54.1. DaemonSet `gadget/gadget` on all 3 nodes (it tolerates every
  NoSchedule and NoExecute taint), as on test-cluster (all 6 nodes). The gadget pods are not
  hostNetwork.
- Gadgets are pinned to `trace_tcp:v0.54.1` and `snapshot_socket:v0.54.1`. Both tags exist on
  ghcr.io. The thesis ran `:latest` with a v0.55.0 client against the v0.54.1 server, which
  printed version-skew warnings. Here the client and server match.

## Tools on cp-01

- kubectl (k3s v1.36.3), helm v4.3.0, cilium-cli v0.20.1, hubble v1.19.4 (the newest 1.19.x
  CLI; no 1.19.5 CLI release exists, and the laptop used 1.19.4 too), kubectl-gadget v0.54.1,
  jq, python3, conntrack, envsubst (gettext-base).
- `hey` 0.1.4 comes from the Ubuntu archive (`apt install hey`). The upstream binary on S3
  returns 403. The fixed-count throughput test itself runs as a Job inside the cluster
  (apps bundle); `hey` on cp-01 is only a convenience.
- conntrack is installed on both workers. `nf_conntrack_netlink` is loaded on every node and
  listed in `/etc/modules-load.d/perfbench.conf`, so `conntrack -S` works.
- `KUBECONFIG=/etc/rancher/k3s/k3s.yaml` is exported in root's `.bashrc`.

## Condition switch (`bin/cond.sh`)

Every call runs the same sequence, whatever the previous condition was:

1. Every observer off: `hubble-relay` and every Deployment in otterize-system scaled to 0;
   `otterize-network-sniffer` and `gadget` gated with nodeSelector `perfbench.off=true`.
   Waits until no relay, otterize or gadget pod exists.
2. `cilium-config`: `enable-hubble` set to true or false. The two hubble-metrics keys are
   restored to the test-cluster values, or removed.
3. `kubectl rollout restart ds/cilium`, then wait until the DaemonSet is fully rolled out and
   `cilium-dbg status --brief` prints OK in every agent.
4. The condition's observers start as new pods: relay scaled to 1 (hubble); mapper scaled to 1
   and the sniffer un-gated (otterize); gadget un-gated (ig_tcp, ig_snap). For ig_tcp and
   ig_snap, both gadgets then run once against ns `gadget` to warm the image store (see below).
5. Verify: the ConfigMap keys; each agent's `hubble.state` and `hubble-metrics.state` from
   `cilium-dbg status -o json`; TCP reachability of :9965 and :9962 on all 3 node IPs; relay,
   otterize and gadget pod counts. Hubble also gets `hubble status` via the relay ClusterIP
   (`Connected Nodes: 3/3`). Otterize gets a GraphQL `serviceIntents` query on the mapper
   ClusterIP :9090. Gadget gets the server version from `kubectl gadget version`.

It prints one JSON line and exits 1 on any mismatch. A `flock` on `/run/perfbench-cond.lock`
stops two calls from running at once. One switch takes about 30 to 80 s; the otterize
condition is the slowest.

The mapper is a new pod in the otterize condition, which matches the thesis "otterize reset".
run_one.sh may still restart it at run start; a second restart does no harm.

Gadget warm-up. The gadget pods keep pulled gadget images (trace_tcp, snapshot_socket) in an
emptyDir, not in containerd, so `install.sh prepull` cannot pre-pull them and every fresh gadget
pod starts with an empty store. Measured on fresh pods: snapshot_socket took 4.5 s to its JSON
cold and 0.6 s warm, and `trace_tcp -t 3` took 8.3 s cold and 4.5 s warm. On test-cluster the
gadget pods ran for weeks, so their stores were warm. cond.sh therefore runs
`snapshot_socket:v0.54.1` and `trace_tcp:v0.54.1 -t 2` once against ns `gadget` in both IG
conditions. The pull stays out of the measured run, and ig_tcp and ig_snap get the same
pre-run sequence. This also checks that both gadgets work (`warmup_*` fields in the JSON line).

snapshot_socket prints its JSON array and then never exits. That is why the thesis loop kills
it after 12 s. The run_one.sh loop must do the same.

## Smoke test (`cluster/smoke.sh`)

It creates ns `pb-smoke` (a busybox httpd server, plus a wget loop client on the other worker)
and switches through hubble, otterize and ig_tcp with cond.sh. It checks that each observer
returns data, then ends in baseline and deletes the namespace. Results are in
`/opt/perfbench/results/_infra-smoke/` on cp-01. See the evidence section below.

## Other version notes

- k3s v1.36.3+k3s1 ships metrics-server v0.9.0 and coredns 1.14.6. test-cluster ran
  metrics-server v0.8.1; coredns 1.14.6 matches its post-upgrade state.
- The test-cluster dump `cilium-config-20260910.json` lives under `_PRIVATE-DO-NOT-SHARE/`
  on the laptop. It is not copied into this tree. It was copied to the VM as
  `/opt/perfbench/cluster/cilium-config-20260910.json`, where `install.sh verify` and
  `smoke.sh` read it.

## Evidence (2026-10-02, play 6abf7eba882cd1c296de683a)

Files on cp-01 under `/opt/perfbench/results/_infra-smoke/`.

Config diff in the hubble condition (`cilium_config_diff_hubble.txt`): 155 of 155 saved keys
identical, 2 extra keys (see above). In baseline (`cilium_config_diff_baseline.txt`) the only
other differences are the three keys cond.sh owns: `enable-hubble` false, `hubble-metrics`
and `hubble-metrics-server` absent.

Smoke test (`smoke.json`, one switch through every observer via cond.sh):
`{"smoke_ok":true,"hubble_flows":150,"otterize_cli_to_srv":1,"ig_trace_tcp_events_25s":62,"ig_snapshot_socket_entries":60}`.
In words: `hubble observe` through the relay returned 150 pb-smoke flows; the Otterize
GraphQL `serviceIntents` answer had the intent cli to srv; `trace_tcp:v0.54.1` streamed 62
JSON events in 25 s; `snapshot_socket:v0.54.1` returned 60 sockets on the first try.

cond.sh cycle baseline, hubble, otterize, ig_tcp, ig_snap, baseline with the final cond.sh
(`cycle-final2/cycle.jsonl`). Every call exited 0 with `ok:true` and no errors:

| cond | secs | enable-hubble | agents hubble / metrics | :9965 open | :9962 open | relay | otterize pods (mapper, sniffer) | gadget pods | gadget warm-up |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 33 | false | Disabled / Disabled x3 | 0/3 | 3/3 | 0 | 0 | 0 | - |
| hubble | 42 | true | Ok / Ok x3 | 3/3 | 3/3 | 1, 3/3 nodes | 0 | 0 | - |
| otterize | 77 | false | Disabled / Disabled x3 | 0/3 | 3/3 | 0 | 3 (1, 2), GraphQL ok | 0 | - |
| ig_tcp | 79 | false | Disabled / Disabled x3 | 0/3 | 3/3 | 0 | 0 | 3, server v0.54.1 | snapshot 21 entries, trace_tcp rc 0 |
| ig_snap | 50 | false | Disabled / Disabled x3 | 0/3 | 3/3 | 0 | 0 | 3, server v0.54.1 | snapshot 21 entries, trace_tcp rc 0 |
| baseline | 33 | false | Disabled / Disabled x3 | 0/3 | 3/3 | 0 | 0 | 0 | - |

A re-run of `install.sh prereqs k3s clis lock baseline` on the built cluster changed nothing
(the k3s config files kept the same md5) and ended with a verified baseline. The cluster was
left in baseline.
