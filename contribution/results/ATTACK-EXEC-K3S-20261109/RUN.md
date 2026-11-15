# Rerunning the attack execution on k3s

1. Two Ubuntu 24.04 machines, `cp-01` (172.16.0.2) and `worker-01` (172.16.0.3), with root ssh from
   cp-01 to worker-01. On cp-01, `bash cluster.sh` installs k3s v1.36.3+k3s1 (no flannel, no
   kube-proxy, no k3s network-policy controller) and Cilium v1.16.5 with kube-proxy replacement,
   Hubble and Kubernetes IPAM.
2. Put the held-out study folders next to the scripts (`BOUTIQUE-20260903`, `BANK-20260904`,
   `DSB-SOCIAL-20260904`, `OTEL-20260906`, `TEASTORE-20260906`; only `manifests/`, `attacks/A_*.json`,
   `policies/netpol_*.yaml` and `score_*.py` are needed).
3. Run `bash run_app_settled.sh <app>` for each of `boutique teastore bank dsb otel`. It deploys the
   application, waits for Ready and then 120 s, runs `probe_k3s.py`, records the pods and deletes the
   namespace. (`run_app.sh` is the same without the 120 s wait; it was used for the first pass.)

`probe_k3s.py` differs from `ATTACK-EXEC-20261028/probe.py` only here:

    2c2
    < """Execute the attack edges of one application on the kind+Cilium cluster.
    > """Execute the attack edges of one application on the k3s+Cilium cluster.
    9c9
    < KC = ["kubectl", "--context", "kind-attack-exec", "-n", NS]
    > KC = ["kubectl", "-n", NS]
