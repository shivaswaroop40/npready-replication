"""Recompute held-out false-deny and over-privilege from the stored policies/*.yaml,
scores.json's L_B list and attacks/A_*.json, without the raw flow captures.
Over-privilege follows the Kubernetes isolation rule (2026-10-28): an attack target that no
NetworkPolicy selects is non-isolated and therefore admits the attack source."""
import json, glob, os, sys, importlib.util, yaml
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
APPS = {"BOUTIQUE-20260903": "boutique", "DSB-SOCIAL-20260904": "dsb", "BANK-20260904": "bank",
        "OTEL-20260906": "otel", "TEASTORE-20260906": "teastore"}
TOOLS = {"synth": "synth (ours, traffic A)", "synth_plus_config": "synth_plus_config (ours, traffic A + config)",
         "otterize": "otterize", "ig_trace_tcp": "ig_trace_tcp", "ig_snapshot_socket": "ig_snapshot_socket"}
def load_scorer(d):
    f = glob.glob(os.path.join(R, d, "score_*.py"))[0]
    spec = importlib.util.spec_from_file_location("sc", f); m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m); return m
def sel_names(sel):
    ml = (sel or {}).get("matchLabels") or {}
    for k in ("app", "run", "app.kubernetes.io/component", "app.kubernetes.io/name", "service", "name"):
        if k in ml:
            v = ml[k]
            return v[len("teastore-"):] if v.startswith("teastore-") else v
    return None
bad = 0
for d, short in APPS.items():
    sc = load_scorer(d)
    s = json.load(open(os.path.join(R, d, "scores", "scores.json")))
    LB = {tuple(x.split("->")) for x in s["L_B"]}
    LBi = {(a, b) for a, b in LB if b not in ("kube-dns", "world", "kube-apiserver")}
    A = {(e[0], e[1]) for e in json.load(open(glob.glob(os.path.join(R, d, "attacks", "A_*.json"))[0]))["edges"]}
    role = sc.role
    for t, key in TOOLS.items():
        f = os.path.join(R, d, "policies", f"netpol_{t}.yaml")
        if not os.path.exists(f): print(d, t, "no policy file"); continue
        P = set(); isolated = set()
        for np in yaml.safe_load_all(open(f)):
            if not np or np.get("kind") != "NetworkPolicy": continue
            dst = role(sel_names(np["spec"].get("podSelector")) or "")
            isolated.add(dst)  # a workload selected by any NetworkPolicy is isolated for ingress
            for r in np["spec"].get("ingress") or []:
                for fr in r.get("from") or []:
                    src = role(sel_names(fr.get("podSelector")) or "")
                    if src and dst: P.add((src, dst))
        # Kubernetes isolation rule: a target no policy selects is non-isolated and admits every source.
        admitted_attacks = {(a, b) for a, b in A if (a, b) in P or b not in isolated}
        unisolated = sorted({b for a, b in A if b not in isolated})
        fd = round(len(LBi - P) / len(LBi), 3); op = round(len(admitted_attacks) / len(A), 3)
        st = s["analytical"][key]
        ok = (fd == st["false_deny"] and op == st["over_privilege"])
        bad += not ok
        extra = sorted(f"{a}->{b}" for a,b in (LBi-P)) ; extra=[e for e in extra if e not in st["missed_legit"]]
        print(f"{short:9} {t:20} fd {fd:.3f} (stored {st['false_deny']:.3f})  op {op:.3f} (stored {st['over_privilege']:.3f})  {'OK' if ok else 'MISMATCH '+str(extra)}" + (f"  [non-isolated attack targets: {unisolated}]" if unisolated else ""))
print("mismatches:", bad)
