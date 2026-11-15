#!/usr/bin/env python3
"""Build the perfbench app bundles from the thesis results directories (laptop only).

Reads apps/<app>/app.env and the pinned thesis files under contribution/results/<RUN>/.
It never edits those files. For each app it writes:

  thesis/                verbatim copies of the pinned manifest(s) and journey-A files,
                         plus SHA256SUMS of every source file it read
  manifest.yaml          the thesis manifest with the adaptations in RECIPES below
  manifest.changes.txt   every field that differs from the thesis manifest; computed by a
                         structural diff of the two, so it cannot drift from what was done
  steady.yaml            journey-A generator as a Job; placeholder ${STEADY_SECONDS}
  steady-configmap.yaml  ConfigMap(s) the generator mounts, verbatim from the thesis file
  throughput.yaml        fixed-count hey Job; placeholders ${TP_N} ${TP_C} ${TP_FLAGS}
  images.txt             every image the bundle runs (manifest workloads with replicas > 0,
                         steady, throughput, extra jobs), one per line, exactly as written
                         in the pod specs so a pre-pull satisfies imagePullPolicy IfNotPresent

Templates contain no "$" other than the placeholders, "$?" and "$(": unrestricted envsubst
is therefore safe on them. Re-running is idempotent.

Usage: python3 apps/tools/prepare.py [app ...]
"""
import copy
import hashlib
import re
import shlex
import shutil
import sys
from pathlib import Path

import yaml

APPS_DIR = Path(__file__).resolve().parents[1]
RESULTS = APPS_DIR.parents[1] / "results"

HEY_IMAGE = "williamyeh/hey@sha256:6e63ae9c5801204cf7abe22c9ddf82d1bcbc7140ffd206a9bd83a8a643dcd6f2"
DSB_FORK_SHA = "0d49cb4d37aa1fa204bccf1a6d4a6179312ac804"  # dimoibiehg/DeathStarBench HEAD since 2024-05-13
DSB_CLONE = "git clone https://github.com/dimoibiehg/DeathStarBench.git /DeathStarBench"
# dsb/dsb_src.sh puts the files the two OpenResty init containers copy (from DSB_FORK_SHA) on every
# worker at this path, once per play. The init containers read it through a read-only hostPath
# instead of cloning about 130 MB from GitHub at every pod start.
DSB_SRC_HOSTPATH = "/var/lib/perfbench/dsb-src/DeathStarBench"

PB_LABELS = {"app.kubernetes.io/part-of": "perfbench"}
CP_NODE = "cp-01"
CP_TOLERATIONS = [
    {"key": "node-role.kubernetes.io/control-plane", "operator": "Exists", "effect": "NoSchedule"},
    {"key": "node-role.kubernetes.io/master", "operator": "Exists", "effect": "NoSchedule"},
]
LOCUST_CSVS = ["steady_stats.csv", "steady_failures.csv", "steady_exceptions.csv", "steady_stats_history.csv"]

BANK_TRACING_OFF = ["frontend", "userservice", "contacts", "balancereader", "ledgerwriter", "transactionhistory"]

RECIPES = {
    "boutique": {
        "run": "BOUTIQUE-20260903",
        "manifests": ["manifests/online-boutique-v0.10.6.yaml"],
        "thesis_copies": ["manifests/online-boutique-v0.10.6.yaml", "workloads/locustfile_A_shipped.py",
                          "boutique_capture.sh"],
        # thesis post-apply step: shipped loadgenerator scaled to 0 (boutique_capture.sh:36-42)
        "replicas0": [("Deployment", "loadgenerator")],
        # journey A ran the shipped Deployment itself, so its pod template is the generator
        "steady_base": ("manifests/online-boutique-v0.10.6.yaml", "Deployment", "loadgenerator"),
        "steady_configmaps": [],
        "steady_labels": {"app": "loadgenerator", "journey": "A"},
        # emailservice and recommendationservice (Python, 200m CPU limit, liveness with no initial
        # delay, 3 x 5 s) can need more than 15 s to open their port on these vCPUs, so they
        # crash-loop: emailservice in the pilot, recommendationservice in the v2 ig_snap run (IG's
        # standing exec/fanotify probes on the node). A startupProbe holds liveness off until the
        # first success; steady-state probes and resources are unchanged.
        "startup_probe": ["emailservice", "recommendationservice"],
    },
    "bank": {
        "run": "BANK-20260904",
        # per-file manifests, not bank-all.yaml: bank-all.yaml glues "---" onto the last line
        # of jwt-secret.yaml, which merges the Secret into the next document. jwt-secret.yaml
        # itself holds the demo private key and is replaced by a key generated in deploy.sh.
        "manifests": ["manifests/accounts-db.yaml", "manifests/balance-reader.yaml", "manifests/config.yaml",
                      "manifests/contacts.yaml", "manifests/frontend.yaml", "manifests/ledger-db.yaml",
                      "manifests/ledger-writer.yaml", "manifests/loadgenerator.yaml",
                      "manifests/transaction-history.yaml", "manifests/userservice.yaml"],
        "excluded": ["manifests/jwt-secret.yaml", "bank-all.yaml"],
        "thesis_copies": ["manifests/accounts-db.yaml", "manifests/balance-reader.yaml", "manifests/config.yaml",
                          "manifests/contacts.yaml", "manifests/frontend.yaml", "manifests/ledger-db.yaml",
                          "manifests/ledger-writer.yaml", "manifests/loadgenerator.yaml",
                          "manifests/transaction-history.yaml", "manifests/userservice.yaml",
                          "workloads/loadgenerator-a.yaml", "workloads/locustfile_A.py", "bank_capture.sh"],
        "replicas0": [("Deployment", "loadgenerator")],
        # thesis post-apply step (spec section 5): set env ENABLE_TRACING/ENABLE_METRICS=false
        "set_env": {d: {"ENABLE_TRACING": "false", "ENABLE_METRICS": "false"} for d in BANK_TRACING_OFF},
        "steady_base": ("workloads/loadgenerator-a.yaml", "Deployment", "loadgenerator-a"),
        "steady_configmaps": [("workloads/loadgenerator-a.yaml", "locustfile-a", "workloads/locustfile_A.py")],
        "steady_labels": None,  # take the thesis pod labels
        "loglevel": "info",
        "tp_secret_env": ("PB_SESSION_TOKEN", "perfbench-session", "token"),
        # JDK 17.0.4 in these images dies at start-up on kernel 6.12 (NPE in
        # CgroupInfo.getMountPoint: 6.12 drops "memory" from /proc/cgroups; JDK-8349988).
        # Container detection is switched off and its result passed explicitly instead
        # (see jvm_flags), so the JVM still sees 1 CPU and its 512Mi limit as on test-cluster.
        "jvm_container_fix": ["balancereader", "ledgerwriter", "transactionhistory"],
    },
    "dsb": {
        "run": "DSB-SOCIAL-20260904",
        "manifests": ["manifests/dsb-social-rendered.yaml"],
        "thesis_copies": ["manifests/dsb-social-rendered.yaml", "workloads/wrk2-A.yaml",
                          "workloads/wrk2-scripts-configmap.yaml", "workloads/read-home-timeline.lua",
                          "dsb_capture.sh"],
        "verbatim": {"workloads/dsb-init-job.yaml": "dsb-init-job.yaml"},
        "git_local": True,
        "steady_base": ("workloads/wrk2-A.yaml", "Deployment", "wrk2-a"),
        "steady_configmaps": [("workloads/wrk2-scripts-configmap.yaml", "wrk2-scripts", None)],
        "steady_labels": None,
        "extra_images": ["python:3.12-slim"],  # dsb-init-job.yaml
        # The six MongoDB Deployments are OOM-killed at the chart's 128Mi limit while the social
        # graph is built: twice in the thesis init (pods.txt: social-graph-mongodb and user-mongodb
        # restarted during the init, so the thesis read a partial graph) and in every init here,
        # even paced to 50 connections. The limit goes to 512Mi (request unchanged) so the graph is
        # built completely and is the same in every play. Mongo memory is app memory; the observer
        # deltas do not depend on it.
        "set_limits": {d: {"memory": "512Mi"} for d in (
            "media-mongodb", "post-storage-mongodb", "social-graph-mongodb", "url-shorten-mongodb",
            "user-mongodb", "user-timeline-mongodb")},
    },
    "otel": {
        "run": "OTEL-20260906",
        "manifests": ["manifests/otel-demo-1.12.0.yaml"],
        "thesis_copies": ["manifests/otel-demo-1.12.0.yaml", "workloads/loadgen-a.yaml", "workloads/locustfile_A.py",
                          "otel_capture.sh", "enforce_missing_three.sh"],
        # thesis post-apply step (spec section 5, enforce_missing_three.sh:29-43)
        "replicas0": [("Deployment", "opentelemetry-demo-grafana"), ("Deployment", "opentelemetry-demo-jaeger"),
                      ("Deployment", "opentelemetry-demo-prometheus-server"),
                      ("Deployment", "opentelemetry-demo-frontendproxy"),
                      ("Deployment", "opentelemetry-demo-loadgenerator"), ("StatefulSet", "otel-demo-opensearch")],
        "steady_base": ("workloads/loadgen-a.yaml", "Deployment", "loadgen-a"),
        "steady_configmaps": [("workloads/loadgen-a.yaml", "locustfile-a", "workloads/locustfile_A.py")],
        "steady_labels": None,
        # productcatalogservice at its 20Mi limit: on test-cluster it was OOM-killed 5 times in 29 min
        # (captureA/pods.txt); here it sits pinned at 20 MiB in reclaim, burns ~200m CPU and stops
        # answering (requests time out after 20 s), so no fixed-count test can finish. Peak seen
        # with 64Mi under 100 req/s: 63 MB. 128Mi leaves headroom. See NOTES.md.
        "set_limits": {"opentelemetry-demo-productcatalogservice": {"memory": "128Mi"}},
    },
    "teastore": {
        "run": "TEASTORE-20260906",
        "manifests": ["manifests/teastore-ribbon.yaml"],
        "thesis_copies": ["manifests/teastore-ribbon.yaml", "workloads/loadgen-a.yaml", "workloads/locustfile_A.py",
                          "teastore_capture.sh"],
        "steady_base": ("workloads/loadgen-a.yaml", "Deployment", "loadgen-a"),
        "steady_configmaps": [("workloads/loadgen-a.yaml", "locustfile-a", "workloads/locustfile_A.py")],
        "steady_labels": None,
    },
}


# ---------------------------------------------------------------- yaml helpers
class Dumper(yaml.SafeDumper):
    pass


def _str(dumper, s):
    return dumper.represent_scalar("tag:yaml.org,2002:str", s, style="|" if "\n" in s else None)


Dumper.add_representer(str, _str)


def dump(docs):
    return yaml.dump_all(docs, Dumper=Dumper, sort_keys=False, default_flow_style=False, width=4096,
                         explicit_start=True)


def load_docs(paths):
    docs = []
    for p in paths:
        docs += [d for d in yaml.safe_load_all(p.read_text()) if d]
    return docs


def split_docs_text(text):
    return [t.strip("\n") + "\n" for t in re.split(r"^---[ \t]*$", text, flags=re.M) if t.strip()]


def load_env(path):
    env = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        k, v = line.split("=", 1)
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        env[k] = v
    return env


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------------------------------------------------------------- manifest transforms
def pod_spec(d):
    if d["kind"] in ("Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job"):
        return d["spec"]["template"]["spec"]
    if d["kind"] == "Pod":
        return d["spec"]
    return None


def containers(spec):
    return list(spec.get("initContainers") or []) + list(spec.get("containers") or [])


def effective_pull_policy(c):
    if c.get("imagePullPolicy"):
        return c["imagePullPolicy"]
    img = c["image"]
    if "@" in img:
        return "IfNotPresent"
    last = img.rsplit("/", 1)[-1]
    tag = last.split(":", 1)[1] if ":" in last else None
    return "Always" if tag in (None, "latest") else "IfNotPresent"


def _qty_bytes(q):
    units = {"Ki": 2**10, "Mi": 2**20, "Gi": 2**30, "Ti": 2**40, "k": 10**3, "M": 10**6, "G": 10**9, "T": 10**12}
    for u, m in units.items():
        if str(q).endswith(u):
            return int(float(str(q)[:-len(u)]) * m)
    return int(q)


def jvm_flags(limits):
    """What JDK 17 container detection would compute from the limits, as explicit flags:
    CPU = ceil(quota), memory = the limit. Container detection itself is turned off."""
    flags = ["-XX:-UseContainerSupport"]
    cpu = limits.get("cpu")
    if cpu is not None:
        cores = float(str(cpu)[:-1]) / 1000 if str(cpu).endswith("m") else float(cpu)
        flags.append(f"-XX:ActiveProcessorCount={max(1, -(-cores // 1)):.0f}")
    if limits.get("memory") is not None:
        flags.append(f"-XX:MaxRAM={_qty_bytes(limits['memory'])}")
    return " ".join(flags)


def adapt(app, docs, recipe):
    for d in docs:
        kind, name = d["kind"], d["metadata"]["name"]
        # The iximiuz cluster has no cloud load balancer (servicelb disabled): LoadBalancer -> ClusterIP.
        if kind == "Service" and d["spec"].get("type") == "LoadBalancer":
            d["spec"]["type"] = "ClusterIP"
            for p in d["spec"].get("ports", []):
                p.pop("nodePort", None)
            for f in ("externalTrafficPolicy", "loadBalancerIP", "loadBalancerSourceRanges",
                      "allocateLoadBalancerNodePorts", "healthCheckNodePort"):
                d["spec"].pop(f, None)
        spec = pod_spec(d)
        if spec is not None:
            # restart.sh restarts every workload before every run; ":latest" images would be
            # re-pulled from Docker Hub each time. Pre-pulled images are used instead.
            for c in containers(spec):
                if effective_pull_policy(c) == "Always":
                    c["imagePullPolicy"] = "IfNotPresent"
        if (kind, name) in recipe.get("replicas0", []):
            d["spec"]["replicas"] = 0
        if kind == "Deployment" and name in recipe.get("set_env", {}):
            for c in d["spec"]["template"]["spec"]["containers"]:
                env = c.setdefault("env", [])
                for k, v in recipe["set_env"][name].items():
                    hit = [e for e in env if e.get("name") == k]
                    if hit:
                        hit[0].pop("valueFrom", None)
                        hit[0]["value"] = v
                    else:
                        env.append({"name": k, "value": v})
        if kind == "Deployment" and name in recipe.get("startup_probe", []):
            for c in d["spec"]["template"]["spec"]["containers"]:
                lp = c.get("livenessProbe")
                assert lp, f"{app}: {name}/{c['name']} has no livenessProbe to copy"
                sp = {k: copy.deepcopy(v) for k, v in lp.items() if k in ("grpc", "httpGet", "tcpSocket", "exec")}
                sp.update({"periodSeconds": 2, "timeoutSeconds": lp.get("timeoutSeconds", 1), "failureThreshold": 90})
                c["startupProbe"] = sp
        if kind == "Deployment" and name in recipe.get("set_limits", {}):
            for c in d["spec"]["template"]["spec"]["containers"]:
                c.setdefault("resources", {}).setdefault("limits", {}).update(recipe["set_limits"][name])
        if kind == "Deployment" and name in recipe.get("jvm_container_fix", []):
            for c in d["spec"]["template"]["spec"]["containers"]:
                env = c.setdefault("env", [])
                assert not [e for e in env if e.get("name") == "JAVA_TOOL_OPTIONS"], f"{app}: {name} sets JAVA_TOOL_OPTIONS"
                env.append({"name": "JAVA_TOOL_OPTIONS", "value": jvm_flags(c.get("resources", {}).get("limits", {}))})
        if recipe.get("git_local") and spec is not None:
            for c in spec.get("initContainers") or []:
                if not any(DSB_CLONE in a for a in c.get("args", [])):
                    continue
                # same cp commands as the thesis, from the pinned local copy instead of a fresh clone;
                # the test fails the init container if the copy is not the pinned commit
                c["args"] = [a.replace(DSB_CLONE + " &&",
                                       f'test "$(cat /DeathStarBench/.perfbench-commit)" = {DSB_FORK_SHA} &&')
                             for a in c.get("args", [])]
                c.setdefault("volumeMounts", []).append(
                    {"name": "perfbench-dsb-src", "mountPath": "/DeathStarBench", "readOnly": True})
                vols = spec.setdefault("volumes", [])
                if not [v for v in vols if v.get("name") == "perfbench-dsb-src"]:
                    vols.append({"name": "perfbench-dsb-src",
                                 "hostPath": {"path": DSB_SRC_HOSTPATH, "type": "Directory"}})
    # every requested change must have found its target
    have = {(d["kind"], d["metadata"]["name"]) for d in docs}
    for t in recipe.get("replicas0", []):
        assert t in have, f"{app}: replicas0 target {t} not in manifest"
    for n in recipe.get("set_env", {}):
        assert ("Deployment", n) in have, f"{app}: set_env target {n} not in manifest"
    for n in recipe.get("set_limits", {}):
        assert ("Deployment", n) in have, f"{app}: set_limits target {n} not in manifest"
    for n in recipe.get("jvm_container_fix", []):
        assert ("Deployment", n) in have, f"{app}: jvm_container_fix target {n} not in manifest"
    for n in recipe.get("startup_probe", []):
        assert ("Deployment", n) in have, f"{app}: startup_probe target {n} not in manifest"
    if recipe.get("git_local"):
        n = sum(a.count(DSB_FORK_SHA) for d in docs if pod_spec(d) for c in (pod_spec(d).get("initContainers") or [])
                for a in c.get("args", []))
        assert n == 2, f"dsb: expected 2 init containers reading the pinned local copy, got {n}"
        left = sum(a.count("git clone") for d in docs if pod_spec(d) for c in (pod_spec(d).get("initContainers") or [])
                   for a in c.get("args", []))
        assert left == 0, f"dsb: {left} init containers still clone from GitHub"
    return docs


def diff(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in list(a) + [k for k in b if k not in a]:
            p = f"{path}.{k}" if path else str(k)
            if k not in b:
                out.append(f"{p}: {flow(a[k])} -> (removed)")
            elif k not in a:
                out.append(f"{p}: (absent) -> {flow(b[k])}")
            else:
                out += diff(a[k], b[k], p)
        return out
    if isinstance(a, list) and isinstance(b, list):
        out = []
        for i in range(max(len(a), len(b))):
            p = f"{path}[{i}]"
            if i >= len(b):
                out.append(f"{p}: {flow(a[i])} -> (removed)")
            elif i >= len(a):
                out.append(f"{p}: (absent) -> {flow(b[i])}")
            else:
                out += diff(a[i], b[i], p)
        return out
    return [] if a == b else [f"{path}: {flow(a)} -> {flow(b)}"]


def flow(v):
    s = yaml.safe_dump(v, default_flow_style=True, width=100000).strip()
    s = s[:-4].strip() if s.endswith("\n...") else s
    return s if len(s) <= 400 else s[:400] + " ..."


# ---------------------------------------------------------------- generator jobs
def job_skeleton(app, ns, name, role, pod_labels):
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {"name": name, "namespace": ns,
                     "labels": {**PB_LABELS, "perfbench/role": role, "perfbench/app": app}},
        "spec": {"backoffLimit": 0,
                 "template": {"metadata": {"labels": {**pod_labels, **PB_LABELS, "perfbench/role": role,
                                                      "perfbench/app": app}},
                              "spec": {"restartPolicy": "Never",
                                       "nodeSelector": {"kubernetes.io/hostname": CP_NODE},
                                       "tolerations": copy.deepcopy(CP_TOLERATIONS)}}},
    }


def steady_script(app, env, recipe):
    kind = env["STEADY_KIND"]
    begin = (f'echo "PB_STEADY_BEGIN epoch=$(date +%s) app={app} kind={kind} '
             f'users={env.get("STEADY_USERS", "-")} rate={env.get("STEADY_RATE", "-")} seconds=${{STEADY_SECONDS}}"')
    if kind == "locust":
        cmd = ["locust", "-f", env["STEADY_LOCUSTFILE"], f"--host={env['STEADY_HOST']}", "--headless",
               "-u", env["STEADY_USERS"], "-r", env["STEADY_RATE"]]
        if recipe.get("loglevel"):
            cmd += ["--loglevel", recipe["loglevel"]]
        cmd += ["--run-time", "${STEADY_SECONDS}s", "--only-summary", "--csv", "/tmp/pb/steady",
                "--exit-code-on-error", "0"]
        files = LOCUST_CSVS
    elif kind == "wrk2":
        a = shlex.split(env["STEADY_WRK2_ARGS"])
        cmd = ["/usr/local/bin/wrk", *a[:a.index("-L")], "-d", "${STEADY_SECONDS}s", *a[a.index("-L"):],
               env["STEADY_URL"], "-R", env["STEADY_RATE"]]
        files = []
    else:
        raise SystemExit(f"{app}: unknown STEADY_KIND {kind}")
    lines = [begin, " ".join(cmd), "echo $? > /tmp/pb/rc",
             'echo "PB_STEADY_RC=$(cat /tmp/pb/rc) epoch=$(date +%s)"']
    for f in files:
        lines += [f'echo "=== PB_FILE {f} ==="', f"cat /tmp/pb/{f}"]
    lines += ['echo "=== PB_END ==="', 'exit "$(cat /tmp/pb/rc)"']
    return "\n".join(lines) + "\n"


def build_steady(app, env, recipe, src_root):
    f, kind, name = recipe["steady_base"]
    base = [d for d in load_docs([src_root / f]) if d["kind"] == kind and d["metadata"]["name"] == name]
    assert len(base) == 1, f"{app}: steady base {kind}/{name} not found in {f}"
    tmpl = copy.deepcopy(base[0]["spec"]["template"])
    labels = recipe["steady_labels"] if recipe["steady_labels"] is not None else tmpl["metadata"]["labels"]
    job = job_skeleton(app, env["APP_NS"], env["STEADY_JOB"], "steady", labels)
    pod = job["spec"]["template"]["spec"]
    src = tmpl["spec"]
    assert len(src["containers"]) == 1, f"{app}: steady base has {len(src['containers'])} containers"
    for k in ("serviceAccountName", "terminationGracePeriodSeconds", "securityContext"):
        if k in src:
            pod[k] = src[k]
    c = copy.deepcopy(src["containers"][0])
    thesis_image = c["image"]
    assert thesis_image.split("@")[0] == env["STEADY_IMAGE"].split("@")[0], \
        f"{app}: STEADY_IMAGE {env['STEADY_IMAGE']} is not the thesis image {thesis_image}"
    c["image"] = env["STEADY_IMAGE"]
    c["imagePullPolicy"] = "IfNotPresent"
    c.pop("args", None)
    c["command"] = ["/bin/sh", "-c"]
    c["args"] = [steady_script(app, env, recipe)]
    c["volumeMounts"] = list(c.get("volumeMounts") or []) + [{"name": "pb-out", "mountPath": "/tmp/pb"}]
    pod["containers"] = [c]
    pod["volumes"] = list(src.get("volumes") or []) + [{"name": "pb-out", "emptyDir": {}}]
    header = (f"# perfbench steady generator for {app}: thesis journey A as a Job pinned to {CP_NODE}.\n"
              f"# Generated by apps/tools/prepare.py from results/{recipe['run']}/{f} ({kind}/{name}).\n"
              "# Placeholder: ${STEADY_SECONDS} (whole Job duration; locust run-time / wrk2 -d).\n"
              "# Collect with: kubectl -n " + env["APP_NS"] + " logs job/" + env["STEADY_JOB"] +
              "  (markers PB_STEADY_BEGIN, PB_STEADY_RC, === PB_FILE <name> ===, === PB_END ===)\n")
    return header + dump([job]), thesis_image


def build_throughput(app, env, recipe):
    job = job_skeleton(app, env["APP_NS"], env["TP_JOB"], "throughput", {})
    pod = job["spec"]["template"]["spec"]
    pod["terminationGracePeriodSeconds"] = 5
    url = env["TP_URL"]
    hdr = f" -H '{env['TP_HEADERS']}'" if env.get("TP_HEADERS") else ""
    script = "\n".join([
        f'echo "PB_TP_BEGIN epoch=$(date +%s) app={app} n=${{TP_N}} c=${{TP_C}} flags=[${{TP_FLAGS}}] url={url}"',
        f"/hey -n ${{TP_N}} -c ${{TP_C}} ${{TP_FLAGS}} -disable-redirects{hdr} '{url}'",
        "echo $? > /tmp/rc",
        'echo "PB_TP_RC=$(cat /tmp/rc) epoch=$(date +%s)"',
        'echo "=== PB_END ==="',
        'exit "$(cat /tmp/rc)"',
    ]) + "\n"
    c = {"name": "hey", "image": HEY_IMAGE, "imagePullPolicy": "IfNotPresent",
         "command": ["/bin/sh", "-c"], "args": [script],
         "resources": {"requests": {"cpu": "100m", "memory": "64Mi"}, "limits": {"memory": "256Mi"}}}
    if recipe.get("tp_secret_env"):
        var, secret, key = recipe["tp_secret_env"]
        assert f"$({var})" in env.get("TP_HEADERS", ""), f"{app}: TP_HEADERS must reference $({var})"
        c["env"] = [{"name": var, "valueFrom": {"secretKeyRef": {"name": secret, "key": key}}}]
    pod["containers"] = [c]
    header = (f"# perfbench fixed-count test for {app}: hey, N requests at concurrency C against TP_URL.\n"
              "# Generated by apps/tools/prepare.py. Placeholders: ${TP_N} ${TP_C} ${TP_FLAGS}\n"
              "#   TP_FLAGS: empty = keep-alive (16 persistent connections); -disable-keepalive = new\n"
              "#   connection per request. hey runs N/C requests per worker, so N must be a multiple of C.\n"
              "# Collect with: kubectl -n " + env["APP_NS"] + " logs job/" + env["TP_JOB"] +
              "  (markers PB_TP_BEGIN, PB_TP_RC, === PB_END ===)\n")
    return header + dump([job])


def images_of(docs):
    out = []
    for d in docs:
        spec = pod_spec(d)
        if spec is None:
            continue
        if d["kind"] in ("Deployment", "StatefulSet") and d["spec"].get("replicas", 1) == 0:
            continue
        out += [c["image"] for c in containers(spec)]
    return out


# ---------------------------------------------------------------- main
def build(app):
    recipe = RECIPES[app]
    out = APPS_DIR / app
    src_root = RESULTS / recipe["run"]
    env = load_env(out / "app.env")
    assert env["APP"] == app

    # thesis copies + checksums of everything read
    tdir = out / "thesis"
    if tdir.exists():
        shutil.rmtree(tdir)
    read = sorted(set(recipe["manifests"] + recipe["thesis_copies"] + list(recipe.get("verbatim", {}))
                      + [f for f, _, _ in [recipe["steady_base"]]]
                      + [f for f, _, _ in recipe["steady_configmaps"]]
                      + [lf for _, _, lf in recipe["steady_configmaps"] if lf]))
    sums = [f"# sha256 of the thesis files this bundle was built from, relative to results/{recipe['run']}/"]
    for rel in read:
        sums.append(f"{sha256(src_root / rel)}  {rel}")
    for rel in recipe.get("excluded", []):
        sums.append(f"{sha256(src_root / rel)}  {rel}  (read for the checksum only; not copied, see NOTES.md)")
    for rel in recipe["thesis_copies"]:
        dst = tdir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_root / rel, dst)
    (tdir / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    for rel, name in recipe.get("verbatim", {}).items():
        shutil.copyfile(src_root / rel, out / name)

    # manifest
    paths = [src_root / m for m in recipe["manifests"]]
    orig = load_docs(paths)
    adapted = adapt(app, copy.deepcopy(orig), recipe)
    text = dump(adapted)
    assert yaml.safe_load_all(text) and [d for d in yaml.safe_load_all(text) if d] == adapted, "round trip changed data"
    src_list = ", ".join(recipe["manifests"])
    (out / "manifest.yaml").write_text(
        f"# Generated by apps/tools/prepare.py from results/{recipe['run']}/{{{src_list}}}.\n"
        "# Do not edit: change the recipe and re-run. Every difference from the thesis manifest is\n"
        "# listed in manifest.changes.txt. Apply with: kubectl -n " + env["APP_NS"] + " apply -f manifest.yaml\n"
        + text)
    changes = [f"# {app}: fields of manifest.yaml that differ from the thesis manifest",
               f"# source: results/{recipe['run']}/{{{src_list}}}",
               f"# objects: {len(orig)} in thesis, {len(adapted)} in manifest.yaml"]
    for rel in recipe.get("excluded", []):
        changes.append(f"# not used: results/{recipe['run']}/{rel} (see NOTES.md)")
    for a, b in zip(orig, adapted):
        for line in diff(a, b):
            changes.append(f"{a['kind']}/{a['metadata']['name']}: {line}")
    (out / "manifest.changes.txt").write_text("\n".join(changes) + "\n")

    # steady generator + its ConfigMaps
    steady_text, thesis_image = build_steady(app, env, recipe, src_root)
    (out / "steady.yaml").write_text(steady_text)
    cms = []
    for f, name, lf in recipe["steady_configmaps"]:
        hit = [t for t in split_docs_text((src_root / f).read_text())
               if (yaml.safe_load(t) or {}).get("kind") == "ConfigMap"
               and yaml.safe_load(t)["metadata"]["name"] == name]
        assert len(hit) == 1, f"{app}: ConfigMap {name} not found in {f}"
        cm = yaml.safe_load(hit[0])
        assert cm["metadata"].get("namespace") in (None, env["APP_NS"]), f"{app}: ConfigMap {name} namespace"
        if lf:  # the mounted locustfile must be the thesis journey-A file, byte for byte
            assert cm["data"]["locustfile.py"] == (src_root / lf).read_text(), f"{app}: {name} != {lf}"
        cms.append(f"# verbatim from results/{recipe['run']}/{f} (ConfigMap {name})\n" + hit[0])
    cm_path = out / "steady-configmap.yaml"
    if cms:
        cm_path.write_text("---\n".join(cms))
    elif cm_path.exists():
        cm_path.unlink()

    (out / "throughput.yaml").write_text(build_throughput(app, env, recipe))

    # images
    steady_docs = [d for d in yaml.safe_load_all(steady_text) if d]
    tp_docs = [d for d in yaml.safe_load_all((out / "throughput.yaml").read_text()) if d]
    imgs = sorted(set(images_of(adapted) + images_of(steady_docs) + images_of(tp_docs)
                      + recipe.get("extra_images", [])))
    (out / "images.txt").write_text("\n".join(imgs) + "\n")
    print(f"{app}: {len(adapted)} objects, {sum(1 for _ in changes) - 3} changed fields, "
          f"{len(imgs)} images, steady image {env['STEADY_IMAGE']} (thesis {thesis_image})")


if __name__ == "__main__":
    for a in sys.argv[1:] or list(RECIPES):
        build(a)
