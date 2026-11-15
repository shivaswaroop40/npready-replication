# Replication package: enforcement-readiness of generated Kubernetes NetworkPolicies

Code, inputs and derived results for the master's thesis *Enforcement-readiness of generated
Kubernetes NetworkPolicies* (Shivaswaroop Nittoor Krishnamurthy, KTH, 2026). Paths match the
`contribution/...` paths cited in the thesis's Appendix A. The fusion technique itself is the
separate tool `npready`: https://github.com/shivaswaroop40/netpol-readiness

## What is here

| Path | What it backs |
|---|---|
| `contribution/results/{BOUTIQUE-20260903,DSB-SOCIAL-20260904,BANK-20260904,OTEL-20260906,TEASTORE-20260906}/` | Held-out study (Section 6.1.3, Table 6.9): stored manifests, attack sets (`attacks/A_*.json`), every generated policy (`policies/`), scores (`scores/`), live enforcement results (`enforce/*/result.json`) and each application's scorer (`score_*.py`) |
| `contribution/scripts/reproduce_from_policies.py`, `contribution/results/REPRO-FROM-POLICIES-20261028.txt`, `REPRODUCE.md` | Offline reproduction of the held-out scores from the stored policies (Appendix A) |
| `contribution/results/HELDOUT-UNIFORM-20261105/` | Held-out rescore under the uniform adapter rule (Section 5.2.3) |
| `contribution/results/ATTACK-EXEC-K3S-20261109/` | Executed attack edges on a two-node k3s + Cilium cluster (Appendix A), with the harness |
| `contribution/results/PERF-CYCLES-20261003/`, `PERF-AGENTONLY-20261005/`, `CAPTURE-LATENCY-20261114/` | Capture-cost study (Section 6.3): combined report, per-block analysis tables, the capture-load latency table (Table 6.14) and the CPU standard deviations |
| `contribution/perf-benchmark/` | Harness of the capture-cost study |
| `contribution/figures/` | Scripts for the figures, and the figures |

## Run

```
pip install pyyaml matplotlib
python3 contribution/scripts/reproduce_from_policies.py            # held-out scores from the stored policies
python3 contribution/results/CAPTURE-LATENCY-20261114/capture_latency.py
python3 contribution/results/CAPTURE-LATENCY-20261114/capture_cpu.py
```

## What is not here, and why

- **Raw flow captures** of the held-out study (`captureA/`, `captureB/`, raw drop logs). They name the
  nodes of the cluster they ran on, which belonged to the industrial partner. They will be archived
  separately with those identifiers replaced. `HELDOUT-UNIFORM-20261105/rescore_heldout.py` needs them.
- **The platform study** (the industrial partner's control plane): its reference and attack sets reveal
  the platform's internal topology and are withheld under the anonymisation agreement, as the thesis
  states. Figure scripts that plot platform results (`generate_figures.py`, parts of `deck_figures.py`)
  need those withheld files.
- **Raw per-run directories** of the capture-cost study; the per-block analysis tables are included.
- **The upstream DeathStarBench repository**; the rendered manifest used is in
  `DSB-SOCIAL-20260904/manifests/`.

The name of the test cluster is replaced by `test-cluster` in the cost-study reports.

## License

Apache License 2.0 (see `LICENSE`). Third-party application manifests keep their upstream licenses.
