#!/usr/bin/env python3
"""Laptop smoke test of the generator and throughput Jobs, without any cluster.

For each app it renders steady.yaml and throughput.yaml with plain, unrestricted envsubst
(proving the templates survive it), expands $(VAR) references the way the kubelet does, and
runs the exact container (image, command, args, env, mounts, user, read-only root) with
`docker run --platform linux/amd64` against a stub HTTP server that answers on every
in-cluster host name the Jobs use. bank/session.sh runs too, in a container with a fake
kubectl, against the same stub. Checks: generator exit code 0, every PB_* marker present,
locust CSVs with requests in them, wrk2 summary, hey [200] count == N in both modes, the bank
cookie reaches the stub, and the session token never appears in any output.

Usage: python3 apps/tools/local_smoke.py [--seconds 20] [app ...]
"""
import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

APPS_DIR = Path(__file__).resolve().parents[1]
NET = "pb-smoke"
STUB = "pb-smoke-stub"
STUB_IMAGE = "python:3.12-slim"
ALIASES = ["frontend", "opentelemetry-demo-frontend", "teastore-webui", "nginx-thrift",
           "nginx-thrift.dsb.svc.cluster.local"]


def b64u(o):
    return base64.urlsafe_b64encode(json.dumps(o).encode()).decode().rstrip("=")


TOKEN = f"{b64u({'alg': 'none'})}.{b64u({'exp': 1790999999, 'user': 'smoke'})}.c21va2U"

STUB_SRC = r'''
import http.server, socketserver, threading, sys
TOKEN = sys.argv[1]
class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def send(self, code, body=b'{"ok":true}', extra=()):
        self.send_response(code)
        for k, v in extra: self.send_header(k, v)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path.startswith("/home") and "token=" + TOKEN not in (self.headers.get("Cookie") or ""):
            return self.send(302, b"", [("Location", "/login")])
        self.send(200)
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path.startswith("/login"):
            return self.send(302, b"", [("Location", "/home"), ("Set-Cookie", "token=" + TOKEN + "; Max-Age=3600; Path=/")])
        self.send(200)
    def log_message(self, *a): pass
class T(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True
for p in (80, 8080):
    threading.Thread(target=T(("", p), H).serve_forever, daemon=True).start()
print("stub up", flush=True)
threading.Event().wait()
'''


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def envsubst(text, env):
    """Plain envsubst: replaces every $VAR / ${VAR}, unset ones with ''."""
    r = sh(["envsubst"], input=text, env={"PATH": os.environ["PATH"], **env})
    assert r.returncode == 0, r.stderr
    return r.stdout


def kubelet_expand(s, env):
    return re.sub(r"\$\(([A-Za-z_][A-Za-z0-9_]*)\)", lambda m: env.get(m.group(1), m.group(0)), s)


def docker_args_for(job, cm_dir, extra_env):
    pod = job["spec"]["template"]["spec"]
    (c,) = pod["containers"]
    env = {e["name"]: e["value"] for e in c.get("env", []) if "value" in e}
    env.update({e["name"]: extra_env[e["name"]] for e in c.get("env", []) if "valueFrom" in e})
    args = ["docker", "run", "--rm", "--platform", "linux/amd64", "--network", NET]
    sc = {**(pod.get("securityContext") or {}), **(c.get("securityContext") or {})}
    if sc.get("runAsUser") is not None:
        args += ["--user", f"{sc['runAsUser']}:{sc.get('runAsGroup', sc['runAsUser'])}"]
    if sc.get("readOnlyRootFilesystem"):
        args += ["--read-only"]
    vols = {v["name"]: v for v in pod.get("volumes", [])}
    for m in c.get("volumeMounts", []):
        v = vols[m["name"]]
        if "emptyDir" in v:
            args += ["--tmpfs", f"{m['mountPath']}:rw,mode=1777"]
        elif "configMap" in v:
            src = cm_dir / v["configMap"]["name"]
            src = src / m["subPath"] if m.get("subPath") else src
            args += ["-v", f"{src}:{m['mountPath']}:ro"]
        else:
            raise SystemExit(f"unsupported volume {v}")
    for k, v in env.items():
        args += ["-e", f"{k}={v}"]
    cmd = [kubelet_expand(x, env) for x in c["command"]]
    cargs = [kubelet_expand(x, env) for x in c.get("args", [])]
    return args + ["--entrypoint", cmd[0], c["image"], *cmd[1:], *cargs]


def write_configmaps(app_dir, out):
    f = app_dir / "steady-configmap.yaml"
    if not f.exists():
        return
    for d in yaml.safe_load_all(f.read_text()):
        if d and d["kind"] == "ConfigMap":
            p = out / d["metadata"]["name"]
            p.mkdir(parents=True, exist_ok=True)
            for k, v in d["data"].items():
                (p / k).write_text(v)


def check(cond, msg, problems):
    if not cond:
        problems.append(msg)


def smoke_app(app, seconds):
    app_dir = APPS_DIR / app
    env = dict(l.split("=", 1) for l in sh(["bash", "-c", f"set -a; . {app_dir}/app.env; env"]).stdout.splitlines()
               if "=" in l)
    problems, notes = [], []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        os.chmod(td, 0o755)
        write_configmaps(app_dir, td)
        for p in td.rglob("*"):
            os.chmod(p, 0o755 if p.is_dir() else 0o644)

        # ---- steady
        tmpl = (app_dir / "steady.yaml").read_text()
        rendered = envsubst(tmpl, {"STEADY_SECONDS": str(seconds)})
        restricted = sh(["envsubst", "${STEADY_SECONDS}"], input=tmpl,
                        env={"PATH": os.environ["PATH"], "STEADY_SECONDS": str(seconds)}).stdout
        check(rendered == restricted, "steady.yaml: unrestricted envsubst differs from restricted", problems)
        (job,) = [d for d in yaml.safe_load_all(rendered) if d]
        t0 = time.time()
        r = sh(docker_args_for(job, td, {}), timeout=seconds + 180)
        out = r.stdout + r.stderr
        (APPS_DIR / "tools" / ".smoke").mkdir(exist_ok=True)
        (APPS_DIR / "tools" / ".smoke" / f"{app}-steady.log").write_text(out)
        check(r.returncode == 0, f"steady exit {r.returncode}", problems)
        for m in ("PB_STEADY_BEGIN", "PB_STEADY_RC=0", "=== PB_END ==="):
            check(m in out, f"steady output lacks {m}", problems)
        if env["STEADY_KIND"] == "locust":
            for f in ("steady_stats.csv", "steady_failures.csv", "steady_exceptions.csv", "steady_stats_history.csv"):
                check(f"=== PB_FILE {f} ===" in out, f"no {f}", problems)
            stats = out.split("=== PB_FILE steady_stats.csv ===")[1].split("=== PB_FILE")[0].strip().splitlines()
            agg = [l for l in stats if ",Aggregated," in l]
            n = int(agg[0].split(",")[2]) if agg else 0
            check(n > 0, "locust Aggregated row has no requests", problems)
            notes.append(f"locust {n} requests in {time.time() - t0:.0f}s, header: {stats[0][:80]}...")
        else:
            m = re.search(r"Requests/sec:\s+([\d.]+)", out)
            check(bool(m), "wrk2 summary lacks Requests/sec", problems)
            check("Detailed Percentile spectrum" in out, "wrk2 -L spectrum missing", problems)
            notes.append(f"wrk2 {m.group(1) if m else '?'} req/s in {time.time() - t0:.0f}s")

        # ---- throughput, both modes
        tmpl = (app_dir / "throughput.yaml").read_text()
        for flags in ("", "-disable-keepalive"):
            vals = {"TP_N": "64", "TP_C": "4", "TP_FLAGS": flags}
            rendered = envsubst(tmpl, vals)
            restricted = sh(["envsubst", "${TP_N} ${TP_C} ${TP_FLAGS}"], input=tmpl,
                            env={"PATH": os.environ["PATH"], **vals}).stdout
            check(rendered == restricted, "throughput.yaml: unrestricted envsubst differs", problems)
            (job,) = [d for d in yaml.safe_load_all(rendered) if d]
            r = sh(docker_args_for(job, td, {"PB_SESSION_TOKEN": TOKEN}), timeout=180)
            out = r.stdout + r.stderr
            mode = flags or "keepalive"
            (APPS_DIR / "tools" / ".smoke" / f"{app}-tp-{mode}.log").write_text(out)
            check(r.returncode == 0, f"tp {mode} exit {r.returncode}", problems)
            check("PB_TP_RC=0" in out and "=== PB_END ===" in out, f"tp {mode} markers missing", problems)
            m = re.search(r"\[200\]\s+(\d+) responses", out)
            check(bool(m) and m.group(1) == "64", f"tp {mode}: expected 64 x [200], got {m.group(0) if m else out[-300:]}",
                  problems)
            check(TOKEN not in out, f"tp {mode}: token printed", problems)
            tot = re.search(r"Total:\s+([\d.]+) secs", out)
            notes.append(f"hey {mode}: 64 x 200 in {tot.group(1) if tot else '?'}s")
    return app, problems, notes


def smoke_session():
    """bank/session.sh in a container with a fake kubectl, against the stub."""
    problems = []
    ip = sh(["docker", "inspect", "-f", f"{{{{(index .NetworkSettings.Networks \"{NET}\").IPAddress}}}}", STUB]).stdout.strip()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        fake = td / "kubectl"
        fake.write_text(f"""#!/bin/bash
args="$*"
case "$args" in
  *"get cm demo-data-config"*DEMO_LOGIN_USERNAME*) printf testuser ;;
  *"get cm demo-data-config"*DEMO_LOGIN_PASSWORD*) printf 'not-a-real-pass' ;;
  *"get svc frontend"*) printf {ip} ;;
  *"create secret generic perfbench-session"*) for a in "$@"; do case "$a" in --from-file=token=*) f=${{a#--from-file=token=}};; esac; done
      printf 'kind: Secret\\ndata:\\n  token: %s\\n' "$(base64 -w0 < "$f")" ;;
  *"apply -f -"*) cat > /out/secret.yaml ;;
  *) echo "fake kubectl: unexpected: $args" >&2; exit 1 ;;
esac
""")
        fake.chmod(0o755)
        out_dir = td / "out"
        out_dir.mkdir()
        r = sh(["docker", "run", "--rm", "--platform", "linux/amd64", "--network", NET,
                "-v", f"{APPS_DIR}:/apps:ro", "-v", f"{fake}:/usr/local/bin/kubectl:ro", "-v", f"{out_dir}:/out",
                "python:3.12-slim", "bash", "-c",
                "apt-get -qq update >/dev/null && apt-get -qq install -y curl jq >/dev/null 2>&1 && /apps/bank/session.sh"],
               timeout=300)
        out = r.stdout + r.stderr
        (APPS_DIR / "tools" / ".smoke" / "bank-session.log").write_text(out)
        check(r.returncode == 0, f"session.sh exit {r.returncode}: {out[-500:]}", problems)
        check(TOKEN not in out, "session.sh printed the token", problems)
        check('"token_exp_epoch":1790999999' in r.stdout, f"session.sh JSON wrong: {r.stdout}", problems)
        sec = (out_dir / "secret.yaml").read_text() if (out_dir / "secret.yaml").exists() else ""
        m = re.search(r"token: (\S+)", sec)
        check(bool(m) and base64.b64decode(m.group(1)).decode() == TOKEN, "Secret does not carry the cookie value", problems)
    return "bank/session.sh", problems, [r.stdout.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=int, default=20)
    ap.add_argument("apps", nargs="*", default=["boutique", "bank", "dsb", "otel", "teastore"])
    a = ap.parse_args()
    sh(["docker", "rm", "-f", STUB])
    sh(["docker", "network", "create", NET])
    run = ["docker", "run", "-d", "--name", STUB, "--network", NET]
    for al in ALIASES:
        run += ["--network-alias", al]
    r = sh(run + [STUB_IMAGE, "python", "-c", STUB_SRC, TOKEN])
    assert r.returncode == 0, r.stderr
    time.sleep(3)
    try:
        with ThreadPoolExecutor(len(a.apps)) as ex:
            results = list(ex.map(lambda x: smoke_app(x, a.seconds), a.apps))
        if "bank" in a.apps:
            results.append(smoke_session())
    finally:
        sh(["docker", "rm", "-f", STUB])
        sh(["docker", "network", "rm", NET])
    bad = 0
    for app, problems, notes in results:
        print(f"{'OK  ' if not problems else 'FAIL'} {app}: " + " | ".join(notes))
        for p in problems:
            print(f"     - {p}")
        bad += bool(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
