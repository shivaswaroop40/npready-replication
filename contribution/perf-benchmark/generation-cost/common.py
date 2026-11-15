"""Shared pieces for the generation-cost benchmark.

The edge extraction is NOT reimplemented here. Step 1 calls hubble_edges() from each
application's own score_<app>.py (the code that produced the thesis's synth edge sets),
and step 3 uses that module's role() to map config-derived names, exactly as its
config_edges() does. Only the YAML renderer is reconstructed: the script that wrote
policies/netpol_synth*.yaml was not retained in either repository. verify.py checks the
reconstruction against the stored YAML on enforcement semantics.
"""
import importlib.util
import os
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.normpath(os.path.join(HERE, "..", "..", "results"))

# Per-application parameters. 'client' roles get no policy of their own (load generators).
# 'skip_src' reproduces the stored OTel policy, which carries no rule for the load generator
# (README OTEL-20260906: the loadgen->frontend drops "appear under both policies").
APPS = {
    "BOUTIQUE-20260903": dict(score="score_boutique.py", hubble="hubble_boutique.json", ns="boutique",
                              key="app", client={"loadgenerator"}, skip_src=set()),
    "DSB-SOCIAL-20260904": dict(score="score_dsb.py", hubble="hubble_dsb.json", ns="dsb",
                                key="app", client={"wrk2-client"}, skip_src=set()),
    # Bank: the stored config_derived_edges.json is reproduced record-for-record and in order from
    # bank-all.yaml (manifests/ minus the jwt-key Secret); manifests/ gives the same set in another order.
    "BANK-20260904": dict(score="score_bank.py", hubble="hubble_bank.json", ns="bank",
                          key="app", client={"loadgenerator"}, skip_src=set(), manifests="bank-all.yaml"),
    "OTEL-20260906": dict(score="score_otel.py", hubble="hubble_otel.json", ns="otel",
                          key="app.kubernetes.io/component", client={"loadgen"}, skip_src={"loadgen"}),
    "TEASTORE-20260906": dict(score="score_teastore.py", hubble="hubble_teastore.json", ns="teastore",
                              key="run", client={"load-test"}, skip_src=set()),
}
EGRESS_ONLY = ("kube-dns", "world", "kube-apiserver")


def app_dir(app):
    return os.path.join(RESULTS, app)


def manifests_path(app):
    return os.path.join(app_dir(app), APPS[app].get("manifests", "manifests"))


def load_score_module(app):
    path = os.path.join(app_dir(app), APPS[app]["score"])
    spec = importlib.util.spec_from_file_location("score_" + app.split("-")[0].lower(), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def label_value(app, role):
    if app == "TEASTORE-20260906" and role != "load-test":
        return "teastore-" + role
    return role


def render(app, mod, triples, generated_from):
    """Ingress NetworkPolicy per non-client workload role: allow-<role> listing every observed or
    declared (source, port), or a deny-all-ingress baseline when nothing reaches it."""
    p = APPS[app]
    targets = sorted(r for r in mod.SVCS if r not in p["client"])
    rules = {}
    for s, d, port in triples:
        if d in EGRESS_ONLY or d not in targets or s in p["skip_src"]:
            continue
        rules.setdefault(d, {}).setdefault(s, set()).add(int(port))
    k = p["key"]
    docs = []
    for d in targets:
        sel = f"{{matchLabels: {{{k}: {label_value(app, d)}}}}}"
        if d in rules:
            body = [f"  ingress:"]
            for s in sorted(rules[d]):
                ports = ", ".join(f"{{port: {x}, protocol: TCP}}" for x in sorted(rules[d][s]))
                body += ["  - from:",
                         f"    - podSelector: {{matchLabels: {{{k}: {label_value(app, s)}}}}}",
                         f"    ports: [{ports}]"]
            name, lab = f"allow-{d}", "thesis.ankra.dev/journey: A"
        else:
            body, name, lab = [], f"deny-{d}", "thesis.ankra.dev/baseline: deny-all-ingress"
        docs.append("\n".join([
            "apiVersion: networking.k8s.io/v1", "kind: NetworkPolicy", "metadata:",
            f"  name: {name}", f"  namespace: {p['ns']}",
            f"  labels: {{thesis.ankra.dev/generated-from: {generated_from}, {lab}}}",
            "spec:", f"  podSelector: {sel}", "  policyTypes: [Ingress]"] + body))
    return "\n---\n".join(docs) + "\n"


def config_triples(mod, derived):
    """Same mapping as score_<app>.py config_edges(), applied to a freshly derived JSON."""
    e = set()
    for x in derived["needed"]:
        s = x["src"].split("/")[-1]
        dst = x["dst"]
        dn = dst.split("/")[-1] if "/" in dst else dst
        d2 = "kube-dns" if dn == "kube-dns" else (mod.role(dn) or dn)
        if mod.role(s) and d2:
            e.add((mod.role(s), d2, int(x["port"])))
    return e
