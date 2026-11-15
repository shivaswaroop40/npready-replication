#!/usr/bin/env bash
# Laptop-only checks of the app bundles; contacts no cluster.
#   1. prepare.py is idempotent (re-running changes no file)
#   2. every YAML parses; templates render with the placeholders only
#   3. kubeconform -strict (Kubernetes JSON schemas, master) on every object the bundles apply
#   4. bash -n on every script
#   5. consistency: Job namespaces, TP_URL in throughput.yaml, images.txt covers every pod spec
#   6. no private key or session token in the bundle
# `kubectl apply --dry-run=client` cannot be used offline: it still needs API discovery.
# Usage: bash apps/tools/validate.sh
set -euo pipefail
APPS="$(cd "$(dirname "$0")/.." && pwd)"
KUBECONFORM=ghcr.io/yannh/kubeconform@sha256:faffaf43f95aa6425306e1ab8d6fcad72acb9049158f38e574c085ea1ec0f64e
fail=0
say() { printf '%s\n' "$*"; }
bad() { printf 'FAIL %s\n' "$*"; fail=1; }

# 1 ---------------------------------------------------------------- idempotency
before=$(cd "$APPS" && find . -path ./tools/.smoke -prune -o -type f ! -name '*.pyc' -print0 | sort -z | xargs -0 shasum -a 256)
python3 "$APPS/tools/prepare.py" >/dev/null
after=$(cd "$APPS" && find . -path ./tools/.smoke -prune -o -type f ! -name '*.pyc' -print0 | sort -z | xargs -0 shasum -a 256)
[ "$before" = "$after" ] && say "ok   prepare.py idempotent" || bad "prepare.py changed files on re-run"

# 2 + 5 ---------------------------------------------------------- parse, render, consistency
render=$(mktemp -d)
trap 'rm -rf "$render"' EXIT
python3 - "$APPS" "$render" <<'EOF' || fail=1
import os, re, subprocess, sys
from pathlib import Path
import yaml
apps, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(apps / "tools"))
from prepare import load_env, pod_spec, containers
ok = True
def bad(m):
    global ok; ok = False; print("FAIL " + m)
def subst(text, env, allowed):
    r = subprocess.run(["envsubst"], input=text, capture_output=True, text=True,
                       env={"PATH": os.environ["PATH"], **env})
    r2 = subprocess.run(["envsubst", " ".join("${%s}" % k for k in allowed)], input=text, capture_output=True,
                        text=True, env={"PATH": os.environ["PATH"], **env})
    if r.stdout != r2.stdout:
        bad("template has a $VAR other than " + ",".join(allowed))
    return r.stdout
for app in ["boutique", "bank", "dsb", "otel", "teastore"]:
    d = apps / app
    env = load_env(d / "app.env")
    for f in sorted(d.rglob("*.yaml")):
        try:
            list(yaml.safe_load_all(f.read_text()))
        except Exception as e:
            bad(f"{f}: {e}")
    s = subst((d / "steady.yaml").read_text(), {"STEADY_SECONDS": "1380"}, ["STEADY_SECONDS"])
    t = subst((d / "throughput.yaml").read_text(), {"TP_N": "10000", "TP_C": "16", "TP_FLAGS": "-disable-keepalive"},
              ["TP_N", "TP_C", "TP_FLAGS"])
    (out / app).mkdir()
    (out / app / "steady.rendered.yaml").write_text(s)
    (out / app / "throughput.rendered.yaml").write_text(t)
    for name, text in (("steady", s), ("throughput", t)):
        docs = [x for x in yaml.safe_load_all(text) if x]
        if len(docs) != 1 or docs[0]["kind"] != "Job":
            bad(f"{app} {name}: expected one Job")
            continue
        j = docs[0]
        if j["metadata"]["namespace"] != env["APP_NS"]:
            bad(f"{app} {name}: namespace {j['metadata']['namespace']} != {env['APP_NS']}")
        want = env["STEADY_JOB"] if name == "steady" else env["TP_JOB"]
        if j["metadata"]["name"] != want:
            bad(f"{app} {name}: Job name {j['metadata']['name']} != {want}")
        ps = j["spec"]["template"]["spec"]
        if ps.get("nodeSelector", {}).get("kubernetes.io/hostname") != "cp-01":
            bad(f"{app} {name}: not pinned to cp-01")
        if "${" in text.split("---", 1)[1]:
            bad(f"{app} {name}: unrendered placeholder left")
    if f"'{env['TP_URL']}'" not in t:
        bad(f"{app}: TP_URL from app.env not in throughput.yaml")
    imgs = set((d / "images.txt").read_text().split())
    used = set()
    files = [d / "manifest.yaml", out / app / "steady.rendered.yaml", out / app / "throughput.rendered.yaml"]
    files += [d / "dsb-init-job.yaml"] if (d / "dsb-init-job.yaml").exists() else []
    for f in files:
        for x in yaml.safe_load_all(f.read_text()):
            if not x or pod_spec(x) is None:
                continue
            if x["kind"] in ("Deployment", "StatefulSet") and x["spec"].get("replicas", 1) == 0:
                continue
            used |= {c["image"] for c in containers(pod_spec(x))}
    if used - imgs:
        bad(f"{app}: images.txt misses {sorted(used - imgs)}")
    if imgs - used:
        bad(f"{app}: images.txt lists unused {sorted(imgs - used)}")
    print(f"ok   {app}: yaml parses, templates render, {len(imgs)} images covered")
sys.exit(0 if ok else 1)
EOF

# 3 ---------------------------------------------------------------- schemas
files=()
for app in boutique bank dsb otel teastore; do
  files+=("/apps/$app/manifest.yaml" "/render/$app/steady.rendered.yaml" "/render/$app/throughput.rendered.yaml")
  [ -f "$APPS/$app/steady-configmap.yaml" ] && files+=("/apps/$app/steady-configmap.yaml")
  [ -f "$APPS/$app/dsb-init-job.yaml" ] && files+=("/apps/$app/dsb-init-job.yaml")
done
if out=$(docker run --rm -v "$APPS:/apps:ro" -v "$render:/render:ro" "$KUBECONFORM" \
      -strict -summary -kubernetes-version master "${files[@]}" 2>&1); then
  say "ok   kubeconform: $(printf '%s\n' "$out" | tail -n1)"
else
  printf '%s\n' "$out" | tail -n 20
  bad "kubeconform"
fi

# 4 ---------------------------------------------------------------- scripts
for f in "$APPS"/common.sh "$APPS"/*/*.sh "$APPS"/tools/*.sh; do
  bash -n "$f" || bad "bash -n $f"
done
say "ok   bash -n on $(ls "$APPS"/common.sh "$APPS"/*/*.sh "$APPS"/tools/*.sh | wc -l | tr -d ' ') scripts"

# 6 ---------------------------------------------------------------- secrets
if grep -rIl --exclude-dir=.smoke --exclude=validate.sh -e 'PRIVATE KEY' -e 'LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVk' "$APPS"; then
  bad "private key material in the bundle"
else
  say "ok   no private key material"
fi

[ "$fail" = 0 ] && say "ALL CHECKS PASSED" || { say "SOME CHECKS FAILED"; exit 1; }
