# Reproducing the held-out numbers with the released tool

The released package `npready` (https://github.com/shivaswaroop40/netpol-readiness,
v0.3.0, Apache-2.0) reproduces the false-deny and over-privilege values in the
two-journey study (Table 6.9 / `tab:twojourney`) from the retained captures. The check
is offline and needs no cluster.

```bash
pip install npready            # or: pip install -e path/to/netpol-readiness
```

For each held-out application under `contribution/results/<APP>/`, the reference set L is
the evaluation journey's ingress edges (destinations `kube-dns`, `world`, `kube-apiserver`
are out of scope and excluded from the denominator); the admitted set P is the synthesiser's
observed edges from journey A, or their union with the config-derived set for the fused
policy. Scoring with the released library reproduces:

| application            | synth | + config | over-privilege |
|------------------------|-------|----------|----------------|
| Online Boutique        | 0.000 | 0.000    | 0.000          |
| Bank of Anthos         | 0.083 | 0.000    | 0.000          |
| OpenTelemetry demo     | 0.200 | 0.000    | 0.000          |
| TeaStore               | 0.000 | 0.000    | 0.000          |
| DeathStarBench social  | 0.533 | 0.533    | 0.000          |

Between the version the experiments used (v0.2.1) and the current release (v0.3.0),
`graph.py` and `policy.py` are byte-identical and `score.py` differs only by the additive
`fuse()` function, so the derivation and scoring that produce these numbers are unchanged.
The per-application scorers (`score_<app>.py`) reconstruct L, A, P and O from the stored
`captureA/`, `captureB/`, `policies/` and `attacks/` files; `scores/scores.json` holds the
canonical values.

**Scorer re-run, 2026-09-23.** All five `score_<app>.py` scripts were re-run from their
directories and reproduced the stored analytical values exactly. `OTEL-20260906/score_otel.py`
needed a two-line fix: the three later enforcement runs wrote `total_drops` instead of
`drops_total` and no `locust_fails` field, which made the script crash before writing. It now
reads either field name. The analytical scores are unaffected. Re-running TeaStore's and
OpenTelemetry's scorers also adds live-enforcement entries for runs that finished after the
stored `scores.json` was written; the stored files were kept as they were.
