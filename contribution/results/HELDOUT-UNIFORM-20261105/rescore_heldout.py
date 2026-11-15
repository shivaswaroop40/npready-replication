#!/usr/bin/env python3
"""Offline rescore of the five held-out applications under the uniform adapter rule.

Read-only. Reads the stored raw captures, scores, policies and enforcement records under
contribution/results/<APP>/ in place and never writes there. Writes output.txt and output.json
next to this script (and MANIFEST.sha256 with --write-manifest). Python 3 standard library plus
PyYAML, which is used only to parse the stored policy YAMLs.

Three parts:
  1. STORED. The tool-specific adapters of the five stored scorers
     (score_boutique.py, score_bank.py, score_otel.py, score_teastore.py, score_dsb.py),
     re-implemented here line by line and parameterised per application. Every field of each
     application's scores/scores.json is recomputed and compared. The script exits 1 if any
     comparison fails.
  2. UNIFORM. The uniform rule of RESCORE-20261104/rescore_platform.py (RELAX_ALL plus the
     synthesiser's API-server mapping), applied to the held-out adapters. See README.md.
  3. FACTS. The data behind the held-out text corrections (trace_tcp ports and live drops on
     Online Boutique and Bank of Anthos, the OpenTelemetry loadgen selector and fused pairs,
     the TeaStore JDBC-pool close events, the DSB snapshot UDP sockets).

Usage:
  python3 rescore_heldout.py                   # verify inputs against MANIFEST.sha256, rescore
  python3 rescore_heldout.py --write-manifest  # (re)write MANIFEST.sha256 from the current inputs
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import sys
from collections import Counter, defaultdict

import yaml

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)                                   # contribution/results
RULE_REF = os.path.join(RES, "RESCORE-20261104", "rescore_platform.py")   # hashed, not imported
MANIFEST = os.path.join(HERE, "MANIFEST.sha256")

EPH = 32768                       # rescore_platform.py snapshot direction threshold
ATTACK_NS = {"thesis-revalidate", "thesis-attacks"}           # rescore_platform.py ATTACK_NS
EGR_STORED = ("kube-dns", "world", "kube-apiserver")          # score_<app>.py L_B_ing filter
EGR_UNIFORM = ("kube-dns", "world", "kube-apiserver", "node", "remote-node")  # rescore_platform OOS
TOOLS = ["synth", "synth_plus_config", "otterize", "ig_trace_tcp", "ig_snapshot_socket"]
STORED_NAME = {"synth": "synth (ours, traffic A)",
               "synth_plus_config": "synth_plus_config (ours, traffic A + config)",
               "otterize": "otterize", "ig_trace_tcp": "ig_trace_tcp",
               "ig_snapshot_socket": "ig_snapshot_socket"}
LABEL = {"synth": "flow synthesiser", "synth_plus_config": "fused policy", "otterize": "Otterize",
         "ig_trace_tcp": "IG trace_tcp", "ig_snapshot_socket": "IG snapshot_socket"}
PORT_TOOLS = ["synth", "synth_plus_config", "ig_trace_tcp", "ig_snapshot_socket"]

# ------------------------------------------------------------------------------ applications
# Values copied from each stored scorer: NS, SVCS, KNOWN_PORTS, the role() variant, file names.
APPS = {
    "boutique": dict(
        dir="BOUTIQUE-20260903", ns="boutique", scorer="score_boutique.py",
        hubble="hubble_boutique.json", attacks="A_boutique.json", role_kind="plain",
        title="Online Boutique",
        svcs=["productcatalogservice", "recommendationservice", "checkoutservice", "currencyservice",
              "paymentservice", "shippingservice", "emailservice", "cartservice", "adservice",
              "frontend", "redis-cart", "loadgenerator"],
        known_ports={6379, 7070, 3550, 7000, 50051, 8080, 5050, 9555, 80, 8080, 53},
        live_kind="template"),
    "dsb": dict(
        dir="DSB-SOCIAL-20260904", ns="dsb", scorer="score_dsb.py",
        hubble="hubble_dsb.json", attacks="A_dsb.json", role_kind="dsb",
        title="DSB social network",
        svcs=['compose-post-service', 'home-timeline-redis', 'home-timeline-service', 'jaeger',
              'media-frontend', 'media-memcached', 'media-mongodb', 'media-service', 'nginx-thrift',
              'post-storage-memcached', 'post-storage-mongodb', 'post-storage-service',
              'social-graph-mongodb', 'social-graph-redis', 'social-graph-service', 'text-service',
              'unique-id-service', 'url-shorten-memcached', 'url-shorten-mongodb',
              'url-shorten-service', 'user-memcached', 'user-mention-service', 'user-mongodb',
              'user-service', 'user-timeline-mongodb', 'user-timeline-redis',
              'user-timeline-service', 'wrk2-client'],
        known_ports={9090, 27017, 6379, 11211, 8080, 80, 53, 16686, 14268, 4317, 4318, 6831, 5775},
        live_kind="template"),
    "bank": dict(
        dir="BANK-20260904", ns="bank", scorer="score_bank.py",
        hubble="hubble_bank.json", attacks="A_bank.json", role_kind="plain",
        title="Bank of Anthos",
        svcs=['accounts-db', 'balancereader', 'contacts', 'frontend', 'ledger-db', 'ledgerwriter',
              'loadgenerator', 'transactionhistory', 'userservice'],
        known_ports={8080, 5432, 80, 53},
        live_kind="template"),
    "otel": dict(
        dir="OTEL-20260906", ns="otel", scorer="score_otel.py",
        hubble="hubble_otel.json", attacks="A_otel.json", role_kind="otel",
        title="OpenTelemetry demo",
        svcs=['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice',
              'flagd', 'frauddetectionservice', 'frontend', 'imageprovider', 'kafka',
              'paymentservice', 'productcatalogservice', 'quoteservice', 'recommendationservice',
              'shippingservice', 'valkey', 'accountingservice', 'loadgen'],
        known_ports={8080, 6379, 9092, 8013, 53, 8081},
        live_kind="otel"),
    "teastore": dict(
        dir="TEASTORE-20260906", ns="teastore", scorer="score_teastore.py",
        hubble="hubble_teastore.json", attacks="A_teastore.json", role_kind="teastore",
        title="TeaStore",
        svcs=['auth', 'db', 'image', 'persistence', 'recommender', 'registry', 'webui', 'load-test'],
        known_ports={8080, 3306, 53},
        live_kind="template"),
}
APP_ORDER = ["boutique", "dsb", "bank", "otel", "teastore"]       # tab:twojourney row order

# tab:twojourney as printed in thesis/ch4-experiments.tex on 2026-11-05:
# (|P|, beyond L_B, false-deny (B), over-privilege). Over-privilege is the executed value; for
# trace_tcp on Online Boutique it equals the isolation-rule value, elsewhere the allow-list value.
THESIS_TWOJOURNEY = {
    "boutique": {"L_B": 16, "A": 8,
                 "synth": (18, 0, 0.000, 0.000), "synth_plus_config": (28, 0, 0.000, 0.000),
                 "otterize": (16, 0, 0.000, 0.000), "ig_snapshot_socket": (16, 0, 0.000, 0.000),
                 "ig_trace_tcp": (1, 0, 0.938, 1.000)},
    "dsb": {"L_B": 30, "A": 8,
            "synth": (18, 0, 0.533, 0.000), "synth_plus_config": (42, 0, 0.533, 0.000),
            "otterize": (5, 0, 0.833, 0.000), "ig_snapshot_socket": (25, 3, 0.267, 0.000),
            "ig_trace_tcp": (5, 0, 0.833, 0.000)},
    "bank": {"L_B": 12, "A": 8,
             "synth": (16, 0, 0.083, 0.000), "synth_plus_config": (24, 3, 0.000, 0.000),
             "otterize": (11, 0, 0.083, 0.000), "ig_snapshot_socket": (6, 0, 0.500, 0.000),
             "ig_trace_tcp": (8, 0, 0.333, 0.000)},
    "otel": {"L_B": 25, "A": 8,
             "synth": (26, 0, 0.200, 0.000), "synth_plus_config": (51, 8, 0.000, 0.000),
             "otterize": (23, 0, 0.080, 0.000), "ig_snapshot_socket": (21, 0, 0.160, 0.000),
             "ig_trace_tcp": (4, 0, 0.840, 0.000)},
    "teastore": {"L_B": 12, "A": 7,
                 "synth": (18, 0, 0.000, 0.000), "synth_plus_config": (20, 0, 0.000, 0.000),
                 "otterize": (12, 0, 0.000, 0.000), "ig_snapshot_socket": (12, 0, 0.000, 0.000),
                 "ig_trace_tcp": (11, 0, 0.083, 0.000)},
}

OUT_LINES: list[str] = []


def out(s=""):
    print(s)
    OUT_LINES.append(s)


def banner(title):
    out("\n" + "=" * 100)
    out(title)
    out("=" * 100)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def r3(x):
    return round(x, 3)


def fe(e):
    return "->".join(str(x) for x in e[:2]) + (f":{e[2]}" if len(e) > 2 and e[2] is not None else "")


def is_global(addr):
    try:
        return ipaddress.ip_address(addr).is_global
    except ValueError:
        return False


def jsonl(path):
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def strip_hash(pod):
    """Pod name without the ReplicaSet and pod hash (for reporting drop sources only)."""
    return re.sub(r"-[a-z0-9]{6,10}(-[a-z0-9]{4,5})?$", "", pod or "")


# ------------------------------------------------------------------------------ the App class
class App:
    def __init__(self, key):
        c = APPS[key]
        self.key, self.c = key, c
        self.art = os.path.join(RES, c["dir"])
        self.ns = c["ns"]
        self.svcs = c["svcs"]
        self.known = c["known_ports"]
        self.capA = os.path.join(self.art, "captureA")
        self.capB = os.path.join(self.art, "captureB")

    def p(self, *parts):
        return os.path.join(self.art, *parts)

    # role() exactly as each stored scorer defines it
    def role(self, pod):
        pod = pod or ""
        k = self.c["role_kind"]
        if k == "otel":
            pod = pod.replace("opentelemetry-demo-", "")
            pod = re.sub(r"-[a-z0-9]{6,10}(-[a-z0-9]{4,5})?$", "", pod)
        elif k == "teastore":
            pod = pod.replace("teastore-", "")
            pod = re.sub(r"-[a-z0-9]{6,10}(-[a-z0-9]{4,5})?$", "", pod)
            if pod.startswith("loadgen"):
                return "load-test"
        elif k == "dsb":
            if pod.startswith("wrk2-"):
                return "wrk2-client"
        for s in sorted(self.svcs, key=len, reverse=True):
            if pod.startswith(s):
                return s
        return None

    def ns_role(self, ns, pod):                   # stored ns_role()
        if ns == self.ns:
            return self.role(pod)
        if ns == "kube-system":
            return "kube-dns"
        return None

    # ---- uniform role maps (rescore_platform.py peer_role with RELAX_ALL) --------------------
    def client_role_u(self, ns, name, kube_system_source=False):
        """Client / pod / Hubble-source side. other_ns: a client outside the app namespace is kept
        when the adapter's own role map (role() of its name) maps it; attack namespaces and atk-
        pods are dropped. As on the platform, only the flow synthesiser maps a kube-system source
        to DNS (features/resolve_roles.py gives it infra-dns); Otterize and IG clients get the
        role of their name only (rescore_platform.py otterize_edges, ig_tcp_edges)."""
        if ns in ATTACK_NS or (name or "").startswith("atk-"):
            return None, None
        if ns == self.ns:
            return self.role(name), None
        if ns == "kube-system" and kube_system_source:
            return "kube-dns", "dns_source"
        r = self.role(name)
        return r, ("other_ns" if r else None)

    def peer_role_u(self, ns, name):
        """Destination / peer side: the adapter's own ns_role() plus the apiserver relaxation."""
        if ns == self.ns:
            return self.role(name), None
        if ns == "kube-system":
            return "kube-dns", None
        if ns == "default" and name == "kubernetes":
            return "kube-apiserver", "apiserver"
        return None, None


# ------------------------------------------------------------------------------ Hubble (one pass)
def hubble_scan(app, path):
    """One pass over a Hubble capture. Returns the stored triples (score_<app>.py hubble_edges(),
    exactly), the uniform triples with the relaxation behind each, and diagnostics."""
    stored, uni = set(), defaultdict(set)
    diag = Counter()
    for o in jsonl(path):
        f = o.get("flow", o)
        if f.get("is_reply") or f.get("reply"):
            continue
        src = f.get("source") or {}
        dst = f.get("destination") or {}
        dl = dst.get("labels") or []
        sl = src.get("labels") or []
        l4 = f.get("l4") or {}
        dp = ((l4.get("TCP") or {}).get("destination_port")) or ((l4.get("UDP") or {}).get("destination_port"))
        # ---- STORED, line by line
        s = app.ns_role(src.get("namespace"), src.get("pod_name"))
        if not (s is None or s == "kube-dns"):
            if "reserved:world" in dl:
                d = "world"
            elif "reserved:host" in dl or "reserved:kube-apiserver" in dl:
                d = "kube-apiserver"
            else:
                d = app.ns_role(dst.get("namespace"), dst.get("pod_name"))
            if s and d and s != d and dp:
                stored.add((s, d, int(dp)))
        else:
            if not src.get("namespace"):
                lab = next((x for x in sl if x.startswith("reserved:")), "reserved:?")
                diag["stored_drop_src_" + lab] += 1
            elif src.get("namespace") == "kube-system":
                diag["stored_drop_src_kube-system"] += 1
            elif src.get("namespace") != app.ns:
                diag["stored_drop_src_other_ns"] += 1
            else:
                diag["stored_drop_src_no_role"] += 1
        # ---- UNIFORM (rescore_platform.py load_synth_ankra with synth_api): sources must be
        # workload roles (reserved world, host, remote-node, health sources skipped); destination
        # reserved:kube-apiserver and reserved:host map to kube-apiserver (the platform's
        # resolve_roles maps reserved:host to kube-apiserver too); self pairs kept.
        if not src.get("namespace"):
            continue
        su, tag_s = app.client_role_u(src.get("namespace"), src.get("pod_name"), kube_system_source=True)
        if not su:
            continue
        tag_d = None
        if "reserved:world" in dl:
            du = "world"
        elif "reserved:kube-apiserver" in dl or "reserved:host" in dl:
            du = "kube-apiserver"
        elif "reserved:remote-node" in dl:
            du, tag_d = "remote-node", "remote_node"
        elif dst.get("namespace"):
            du, tag_d = app.peer_role_u(dst.get("namespace"), dst.get("pod_name"))
        else:
            du = None
        if not du or not dp:
            continue
        tags = {t for t in (tag_s, tag_d) if t}
        if su == du:
            tags.add("self")
        uni[(su, du, int(dp))] |= tags
    return stored, dict(uni), diag


# ------------------------------------------------------------------------------ STORED adapters
def stored_otterize(app, path):
    try:
        data = json.load(open(path))["data"]["serviceIntents"]
    except Exception:
        return set()
    e = set()
    for si in data:
        c = si["client"]
        if c["namespace"] != app.ns:
            continue
        cr = app.role(c["name"])
        for it in si.get("intents", []):
            dr = app.role(it["name"]) if it.get("namespace") == app.ns else (
                "kube-dns" if it.get("namespace") == "kube-system" else None)
            if cr and dr and cr != dr:
                e.add((cr, dr))
    return e


def load_ig_tcp(run):
    recs = []
    for o in jsonl(os.path.join(run, "ig_tcp.json")):
        k = o.get("k8s") or {}
        d = o.get("dst") or {}
        s = o.get("src") or {}
        recs.append(dict(type=o.get("type"), ns=k.get("namespace"), pod=k.get("podName", ""),
                         daddr=d.get("addr", ""), dport=d.get("port") or 0, saddr=s.get("addr", ""),
                         sport=s.get("port") or 0, comm=(o.get("proc") or {}).get("comm"),
                         ts=o.get("timestamp")))
    return recs


def stored_ig_tcp(app, recs, ipmap):
    e = set()
    for r in recs:
        if r["type"] != "connect":
            continue
        if r["ns"] != app.ns:
            continue
        s = app.role(r["pod"])
        t = ipmap.get(r["daddr"])
        if not t:
            continue
        d = app.ns_role(t["ns"], t["name"]) if t["ns"] != "kube-system" else "kube-dns"
        if s and d and s != d and r["dport"]:
            e.add((s, d, int(r["dport"])))
    return e


def load_ig_snap(run):
    try:
        arr = json.load(open(os.path.join(run, "ig_snap.json")))
    except Exception:
        return []
    recs = []
    for r in arr if isinstance(arr, list) else [arr]:
        d = r.get("dst") or {}
        k = r.get("k8s") or {}
        recs.append(dict(proto=d.get("proto"), state=r.get("state"), ns=k.get("namespace"),
                         pod=k.get("podName", ""), daddr=d.get("addr", ""), dport=d.get("port") or 0,
                         sport=(r.get("src") or {}).get("port") or 0))
    return recs


def stored_ig_snap(app, recs, ipmap):
    e = set()
    for r in recs:
        if r["proto"] != "TCP" or r["state"] != 1:
            continue
        if r["ns"] != app.ns:
            continue
        pod = app.role(r["pod"])
        t = ipmap.get(r["daddr"])
        if not t:
            continue
        other = app.ns_role(t["ns"], t["name"]) if t["ns"] != "kube-system" else "kube-dns"
        dp = r["dport"]
        if not pod or not other or pod == other:
            continue
        if dp and dp in app.known:
            e.add((pod, other, int(dp)))
        else:
            sp = r["sport"]
            if sp and sp in app.known:
                e.add((other, pod, int(sp)))
    return e


def config_edges(app):
    d = json.load(open(app.p("policies", "config_derived_edges.json")))
    e = set()
    for x in d["needed"]:
        s = x["src"].split("/")[-1]
        dst = x["dst"]
        dn = dst.split("/")[-1] if "/" in dst else dst
        d2 = "kube-dns" if dn == "kube-dns" else (app.role(dn) or dn)
        if app.role(s) and d2:
            e.add((app.role(s), d2, int(x["port"])))
    return e


def pairs(T):
    return {(t[0], t[1]) for t in T}


def stored_score(admit_pairs, L_pairs, A_pairs):
    fd = [x for x in L_pairs if x not in admit_pairs]
    op = [x for x in A_pairs if x in admit_pairs]
    return {"admit": len(admit_pairs),
            "false_deny": round(len(fd) / len(L_pairs), 3) if L_pairs else None,
            "over_privilege": round(len(op) / len(A_pairs), 3) if A_pairs else None,
            "block_rate": round(1 - len(op) / len(A_pairs), 3) if A_pairs else None,
            "missed_legit": sorted(f"{s}->{d}" for s, d in fd),
            "admitted_attacks": sorted(f"{s}->{d}" for s, d in op)}


def stored_live(app):
    """The live_enforcement block exactly as score_<app>.py builds it from enforce/<tool>/."""
    res = {}
    for t in TOOLS:
        f = app.p("enforce", t, "result.json")
        if not os.path.exists(f):
            continue
        r = json.load(open(f))
        pods = app.p("enforce", t, "pods_after_restart.txt")
        nr = (sum(1 for l in open(pods) if l.split() and l.split()[1].split("/")[0] != l.split()[1].split("/")[1])
              if os.path.exists(pods) else None)
        if app.c["live_kind"] == "otel":
            res[STORED_NAME[t]] = {"drops": r.get("drops_total", r.get("total_drops")),
                                   "distinct_dropped_edges": len(r["drops_by_edge"]),
                                   "locust_fails": r.get("locust_fails", "n/a"),
                                   "pods_not_ready_after_restart": nr,
                                   "top_dropped": list(r["drops_by_edge"].items())[:5]}
        else:
            res[STORED_NAME[t]] = {"drops": r["drops_total"], "distinct_dropped_edges": len(r["drops_by_edge"]),
                                   "locust_fails": r["locust_fails"], "pods_not_ready_after_restart": nr,
                                   "top_dropped": list(r["drops_by_edge"].items())[:5]}
    return res


# ------------------------------------------------------------------------------ UNIFORM adapters
def uniform_otterize(app, path):
    """rescore_platform.py otterize_edges() with RELAX_ALL: clients in every namespace (attack
    namespaces dropped) mapped by role() of their name; intents to the app namespace, kube-system
    (DNS) and default/kubernetes (API server); self pairs kept."""
    data = json.load(open(path))["data"]["serviceIntents"]
    e = defaultdict(set)
    diag = Counter()
    for si in data:
        c = si["client"]
        cr, tag_c = app.client_role_u(c.get("namespace"), c.get("name"))
        for it in si.get("intents", []) or []:
            diag["intents"] += 1
            if "namespace" not in it:
                diag["intent_without_namespace"] += 1
            dr, tag_d = app.peer_role_u(it.get("namespace"), it.get("name"))
            if not (cr and dr):
                continue
            tags = {t for t in (tag_c, tag_d) if t}
            if cr == dr:
                tags.add("self")
            e[(cr, dr)] |= tags
    return dict(e), diag


def ig_peer_u(app, ipmap, addr):
    t = ipmap.get(addr)
    if t:
        return app.peer_role_u(t.get("ns"), t.get("name"))
    if is_global(addr):
        return "world", "world"
    return None, None


def uniform_ig_tcp(app, recs, ipmap, keep_close=False, listen=None):
    """rescore_platform.py ig_tcp_edges() with RELAX_ALL: connect events (me -> peer on dst.port)
    and accept events (peer -> me on src.port). keep_close=True is a sensitivity outside the
    uniform rule: a close event is directed by the pod's LISTEN ports (server side if src.port is
    one of them)."""
    e = defaultdict(set)
    for r in recs:
        typ = r["type"]
        if typ not in ("connect", "accept") and not (keep_close and typ == "close"):
            continue
        me, tag_m = app.client_role_u(r["ns"], r["pod"])
        other, tag_o = ig_peer_u(app, ipmap, r["daddr"])
        if not (me and other):
            continue
        tags = {t for t in (tag_m, tag_o) if t}
        if typ == "accept":
            tags.add("accept")
            edge = (other, me, int(r["sport"]) if r["sport"] else None)
        elif typ == "connect":
            edge = (me, other, int(r["dport"]) if r["dport"] else None)
        else:
            tags.add("close")
            server = r["sport"] in (listen or {}).get(me, ()) or (not (r["dport"] and r["dport"] < EPH))
            edge = (other, me, int(r["sport"]) if r["sport"] else None) if server else \
                (me, other, int(r["dport"]) if r["dport"] else None)
        if edge[0] == edge[1]:
            tags.add("self")
        e[edge] |= tags
    return dict(e)


def listen_ports(app, recs):
    """Ports on which each role's pods hold a TCP LISTEN socket (state 10) in the same snapshot."""
    lp = defaultdict(set)
    for r in recs:
        if r["proto"] == "TCP" and r["state"] == 10 and r["sport"]:
            ro = app.role(r["pod"])
            if ro:
                lp[ro].add(int(r["sport"]))
    return {k: v for k, v in lp.items()}


def snap_side(me, other, sport, dport, listen, mode):
    """'client' (me -> other on dport) or 'server' (other -> me on sport).
    mode 'listen' (headline): server side when sport is a LISTEN port of this pod's role and dport
    is not one of the peer's; client side in the converse case; otherwise the platform threshold.
    mode 'eph': the platform's literal rule, client side iff 0 < dport < 32768."""
    if mode == "listen":
        me_srv = sport in listen.get(me, ())
        ot_srv = dport in listen.get(other, ())
        if me_srv and not ot_srv:
            return "server"
        if ot_srv and not me_srv:
            return "client"
    return "client" if (dport and dport < EPH) else "server"


def uniform_ig_snap(app, recs, ipmap, listen, mode="listen", all_states=False):
    """rescore_platform.py ig_snap_edges() with RELAX_ALL: ESTABLISHED TCP sockets and UDP sockets
    with a remote port; both sides kept at port granularity; self pairs kept."""
    e = defaultdict(set)
    for r in recs:
        tags = set()
        if r["proto"] == "TCP":
            if r["state"] != 1:
                if not (all_states and r["state"] != 10 and r["dport"]):
                    continue
                tags.add("non_established")
        elif r["proto"] == "UDP":
            if not r["dport"]:
                continue
            tags.add("udp")
        else:
            continue
        me, tag_m = app.client_role_u(r["ns"], r["pod"])
        other, tag_o = ig_peer_u(app, ipmap, r["daddr"])
        if not (me and other):
            continue
        tags |= {t for t in (tag_m, tag_o) if t}
        side = snap_side(me, other, r["sport"], r["dport"], listen, mode)
        if side == "client":
            edge = (me, other, int(r["dport"]))
        else:
            edge = (other, me, int(r["sport"]) if r["sport"] else None)
        if r["proto"] == "TCP" and r["dport"] not in app.known and r["sport"] not in app.known:
            tags.add("direction_not_in_known_ports")
        if edge[0] == edge[1]:
            tags.add("self")
        e[edge] |= tags
    return dict(e)


# ------------------------------------------------------------------------------ scoring helpers
def score(P, L_ing, A, L_all, egr):
    fd = sorted(x for x in L_ing if x not in P)
    op = sorted(x for x in A if x in P)
    beyond = sorted(x for x in P if x[1] not in egr and x not in L_all)
    return {"P": len(P), "beyond_L_B": len(beyond), "beyond_L_B_pairs": [fe(x) for x in beyond],
            "false_deny": r3(len(fd) / len(L_ing)), "false_deny_n": len(fd),
            "missed": [fe(x) for x in fd],
            "over_privilege": r3(len(op) / len(A)), "over_privilege_n": len(op),
            "admitted_attacks": [fe(x) for x in op]}


def score_ports(PT, LT_ing):
    PT = {t for t in PT if t[2] is not None}
    fd = sorted(x for x in LT_ing if x not in PT)
    return {"false_deny_port": r3(len(fd) / len(LT_ing)), "false_deny_port_n": len(fd),
            "L_B_ingress_triples": len(LT_ing), "missed_triples": [fe(x) for x in fd]}


def isolation_op(P, targets, A):
    adm = sorted(a for a in A if a[1] not in targets or a in P)
    return {"over_privilege_isolation": r3(len(adm) / len(A)), "admitted": [fe(a) for a in adm],
            "targets": sorted(targets)}


# ------------------------------------------------------------------------------ policies
def load_policy(app, tool):
    """Rendered policy: targets and admitted (src, dst, port) triples (port None if the rule has
    no ports), label values mapped to roles with the stored role()."""
    path = app.p("policies", f"netpol_{tool}.yaml")
    targets, T, selectors, other, labelkeys = set(), set(), [], [], set()
    for d in yaml.safe_load_all(open(path)):
        if not d:
            continue
        ml = d["spec"]["podSelector"].get("matchLabels") or {}
        labelkeys |= set(ml)
        tv = next(iter(ml.values())) if ml else None
        tgt = app.role(tv) or tv
        selectors.append(tv)
        targets.add(tgt)
        for rule in d["spec"].get("ingress") or []:
            ports = [p.get("port") for p in (rule.get("ports") or [])] or [None]
            for fr in rule.get("from") or []:
                if set(fr) != {"podSelector"}:
                    other.append(fr)
                    continue
                sml = fr["podSelector"].get("matchLabels") or {}
                labelkeys |= set(sml)
                sv = next(iter(sml.values())) if sml else None
                selectors.append(sv)
                src = app.role(sv) or sv
                for p in ports:
                    T.add((src, tgt, p))
    return {"targets": targets, "triples": T, "selectors": selectors, "other_peers": other,
            "label_keys": sorted(labelkeys)}


def drops_summary(path, app):
    """POLICY_DENIED drops in an enforce/<tool>/hubble_drops.json, by source, destination,
    protocol and port. A source is the pod name without its hash, or its reserved label."""
    c = Counter()
    src_app_labels = Counter()
    for o in jsonl(path):
        f = o.get("flow", o)
        s = f.get("source") or {}
        d = f.get("destination") or {}
        l4 = f.get("l4") or {}
        proto = next(iter(l4), "none")
        dport = (l4.get(proto) or {}).get("destination_port") if proto in ("TCP", "UDP") else None
        sdesc = strip_hash(s.get("pod_name")) if s.get("pod_name") else next(
            (x for x in (s.get("labels") or []) if x.startswith("reserved:")), "unknown")
        ddesc = strip_hash(d.get("pod_name")) if d.get("pod_name") else next(
            (x for x in (d.get("labels") or []) if x.startswith("reserved:")), "unknown")
        key = f"{sdesc}->{ddesc}:{proto}/{dport} {f.get('drop_reason_desc')} {f.get('traffic_direction')}"
        c[key] += 1
        if s.get("pod_name"):
            for lab in s.get("labels") or []:
                if lab.startswith("k8s:app=") or lab.startswith("k8s:app.kubernetes.io/component="):
                    src_app_labels[f"{strip_hash(s.get('pod_name'))} {lab}"] += 1
    return {"total": sum(c.values()), "by_edge": dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))),
            "source_labels": dict(sorted(src_app_labels.items()))}


def template_labels(path):
    for d in yaml.safe_load_all(open(path)):
        if d and d.get("kind") == "Deployment":
            return d["spec"]["template"]["metadata"].get("labels")
    return None


def pod_names(path):
    return [l.split()[0] for l in open(path) if l.split() and l.split()[0] != "NAME"]


# ------------------------------------------------------------------------------ checks
class Checks:
    def __init__(self):
        self.groups = defaultdict(lambda: {"pass": 0, "fail": 0, "failures": []})

    def eq(self, group, label, got, want):
        g = self.groups[group]
        if got == want:
            g["pass"] += 1
            return True
        g["fail"] += 1
        g["failures"].append({"check": label, "got": got, "want": want})
        out(f"  FAIL [{group}] {label}: got {got!r}, want {want!r}")
        return False


def norm(x):
    return json.loads(json.dumps(x))


# ------------------------------------------------------------------------------ inputs
def input_files():
    files = [RULE_REF]
    for k in APP_ORDER:
        a = App(k)
        files.append(a.p(a.c["scorer"]))
        files.append(a.p("scores", "scores.json"))
        files += [os.path.join(a.capA, a.c["hubble"]), os.path.join(a.capB, a.c["hubble"])]
        for n in ("ig_tcp.json", "ig_snap.json", "ipmap.json", "otterize_t1.json", "pods.txt"):
            files.append(os.path.join(a.capA, n))
        files.append(os.path.join(a.capB, "pods.txt"))
        files.append(a.p("attacks", a.c["attacks"]))
        files.append(a.p("policies", "config_derived_edges.json"))
        for t in TOOLS:
            files.append(a.p("policies", f"netpol_{t}.yaml"))
            for n in ("result.json", "pods_after_restart.txt", "hubble_drops.json"):
                f = a.p("enforce", t, n)
                if os.path.exists(f):
                    files.append(f)
        wl = a.p("workloads")
        for n in sorted(os.listdir(wl)):
            if re.match(r"(loadgen|loadgenerator)-[ab]\.yaml$", n):
                files.append(os.path.join(wl, n))
    return files


def manifest(write):
    files = input_files()
    rel = lambda f: os.path.relpath(f, RES)
    if write:
        with open(MANIFEST, "w") as fh:
            for f in files:
                fh.write(f"{sha256(f)}  {rel(f)}\n")
        print(f"wrote {MANIFEST}: {len(files)} files")
        return None
    want = {}
    for line in open(MANIFEST):
        h, p = line.rstrip("\n").split("  ", 1)
        want[p] = h
    ok = bad = 0
    total_bytes = 0
    banner("Input hashes (MANIFEST.sha256, paths relative to contribution/results/)")
    for f in files:
        r = rel(f)
        total_bytes += os.path.getsize(f)
        h = sha256(f)
        good = want.get(r) == h
        ok += good
        bad += not good
        out(f"  {'OK ' if good else 'BAD'} {r}")
    missing = sorted(set(want) - {rel(f) for f in files})
    for m in missing:
        out(f"  BAD {m} (listed in the manifest, not read)")
        bad += 1
    out(f"  {ok} OK, {bad} BAD, {len(files)} files, {total_bytes} bytes")
    return {"files": len(files), "bytes": total_bytes, "ok": ok, "bad": bad}


# ------------------------------------------------------------------------------ per-app rescore
def rescore_app(key, checks):
    app = App(key)
    banner(f"{app.c['title']} ({app.c['dir']})")
    ipmap = json.load(open(os.path.join(app.capA, "ipmap.json")))
    hubA_s, hubA_u, diagA = hubble_scan(app, os.path.join(app.capA, app.c["hubble"]))
    hubB_s, hubB_u, diagB = hubble_scan(app, os.path.join(app.capB, app.c["hubble"]))
    cfg = config_edges(app)
    Aatt = {tuple(x) for x in json.load(open(app.p("attacks", app.c["attacks"])))["edges"]}
    A_p = pairs(Aatt)
    tcp = load_ig_tcp(app.capA)
    snap = load_ig_snap(app.capA)
    listen = listen_ports(app, snap)

    # ---------------- STORED, reproduced
    L_B = pairs(hubB_s)
    L_B_ing = {(s, d) for s, d in L_B if d not in EGR_STORED}
    stored_T = {"synth": hubA_s, "synth_plus_config": hubA_s | cfg,
                "ig_trace_tcp": stored_ig_tcp(app, tcp, ipmap),
                "ig_snapshot_socket": stored_ig_snap(app, snap, ipmap)}
    stored_P = {"synth": pairs(hubA_s), "synth_plus_config": pairs(hubA_s) | pairs(cfg),
                "otterize": stored_otterize(app, os.path.join(app.capA, "otterize_t1.json")),
                "ig_trace_tcp": pairs(stored_T["ig_trace_tcp"]),
                "ig_snapshot_socket": pairs(stored_T["ig_snapshot_socket"])}
    contamination = sorted(A_p & pairs(hubA_s))
    rep = {"evaluation": "journey B traffic only; policies generated from journey A",
           "L_B_pairs": len(L_B), "L_B_ingress_pairs": len(L_B_ing), "A_size": len(A_p),
           "attack_edges_seen_in_A_traffic": contamination,
           "L_B": sorted(f"{s}->{d}" for s, d in L_B), "analytical": {}, "live_enforcement": {}}
    for t in TOOLS:
        rep["analytical"][STORED_NAME[t]] = stored_score(stored_P[t], L_B_ing, A_p)
    rep["live_enforcement"] = stored_live(app)
    rep = norm(rep)
    stored_file = norm(json.load(open(app.p("scores", "scores.json"))))
    grp = f"stored_scores.{key}"
    out(f"\n  Reproduction of {app.c['dir']}/scores/scores.json under the stored tool-specific adapters")
    for k in ("evaluation", "L_B_pairs", "L_B_ingress_pairs", "A_size", "attack_edges_seen_in_A_traffic", "L_B"):
        checks.eq(grp, k, rep[k], stored_file[k])
    checks.eq(grp, "analytical tool names", sorted(rep["analytical"]), sorted(stored_file["analytical"]))
    for t, v in stored_file["analytical"].items():
        for f, want in v.items():
            checks.eq(grp, f"analytical.{t}.{f}", rep["analytical"].get(t, {}).get(f), want)
    live_extra = sorted(set(rep["live_enforcement"]) - set(stored_file["live_enforcement"]))
    for t, v in stored_file["live_enforcement"].items():
        for f, want in v.items():
            checks.eq(grp, f"live_enforcement.{t}.{f}", rep["live_enforcement"].get(t, {}).get(f), want)
    checks.eq(grp, "top-level keys", sorted(rep), sorted(stored_file))
    g = checks.groups[grp]
    out(f"  {g['pass']} PASS, {g['fail']} FAIL")
    if live_extra:
        out(f"  Note: enforce/<tool>/result.json exists for {live_extra}, which the stored scores.json "
            f"does not list under live_enforcement; not compared.")

    # ---------------- policy render check (stored YAML vs stored adapter)
    pol = {t: load_policy(app, t) for t in TOOLS}
    render = {}
    out("\n  Stored policies/netpol_<tool>.yaml against the stored adapter's ingress edges")
    for t in TOOLS:
        yt = pol[t]["triples"]
        if t == "otterize":
            adapter = {(s, d, None) for s, d in stored_P[t] if d not in EGR_STORED}
        else:
            adapter = {x for x in stored_T[t] if x[1] not in EGR_STORED}
        adapter_in_targets = {x for x in adapter if x[1] in pol[t]["targets"]}
        only_adapter = sorted(adapter - yt, key=str)
        only_yaml = sorted(yt - adapter, key=str)
        no_target = sorted(adapter - adapter_in_targets, key=str)
        render[t] = {"policy_triples": len(yt), "policy_pairs": len(pairs(yt)),
                     "adapter_ingress_triples": len(adapter), "targets": sorted(pol[t]["targets"], key=str),
                     "label_keys": pol[t]["label_keys"],
                     "adapter_not_in_policy": [fe(x) for x in only_adapter],
                     "adapter_dst_without_policy": [fe(x) for x in no_target],
                     "policy_not_in_adapter": [fe(x) for x in only_yaml],
                     "other_peer_kinds": len(pol[t]["other_peers"]),
                     "equal": not only_adapter and not only_yaml}
        out(f"    {t:20} policy {len(yt):3} triples, adapter {len(adapter):3}; "
            f"equal={render[t]['equal']}; adapter-only {render[t]['adapter_not_in_policy']}; "
            f"policy-only {render[t]['policy_not_in_adapter']}")

    # ---------------- UNIFORM
    otu, otdiag = uniform_otterize(app, os.path.join(app.capA, "otterize_t1.json"))
    uni_T = {"synth": hubA_u,
             "synth_plus_config": {**{x: set() for x in cfg}, **hubA_u},
             "ig_trace_tcp": uniform_ig_tcp(app, tcp, ipmap),
             "ig_snapshot_socket": uniform_ig_snap(app, snap, ipmap, listen, "listen")}
    uni_P = {t: pairs(uni_T[t]) for t in uni_T}
    uni_P["otterize"] = set(otu)
    uni_tags = {t: defaultdict(set) for t in TOOLS}
    for t in uni_T:
        for x, tg in uni_T[t].items():
            uni_tags[t][(x[0], x[1])] |= tg
    for x, tg in otu.items():
        uni_tags["otterize"][x] |= tg
    L_Bu = pairs(hubB_u)
    L_Bu_ing = {x for x in L_Bu if x[1] not in EGR_UNIFORM}
    L_Bt_s = {x for x in hubB_s if x[1] not in EGR_STORED}
    L_Bt_u = {x for x in hubB_u if x[1] not in EGR_UNIFORM}

    res = {"dir": app.c["dir"], "title": app.c["title"],
           "L_B": {"stored": {"pairs": len(L_B), "ingress_pairs": len(L_B_ing), "ingress_triples": len(L_Bt_s)},
                   "uniform": {"pairs": len(L_Bu), "ingress_pairs": len(L_Bu_ing), "ingress_triples": len(L_Bt_u),
                               "gained_ingress_pairs": [fe(x) for x in sorted(L_Bu_ing - L_B_ing)],
                               "lost_ingress_pairs": [fe(x) for x in sorted(L_B_ing - L_Bu_ing)]}},
           "A_size": len(A_p), "tools": {}, "render_check": render,
           "live_entries_not_in_stored_scores": live_extra,
           "diagnostics": {"hubble_A_stored_dropped_sources": dict(sorted(diagA.items())),
                           "hubble_B_stored_dropped_sources": dict(sorted(diagB.items())),
                           "otterize_intents": dict(otdiag),
                           "snapshot_listen_ports": {k: sorted(v) for k, v in sorted(listen.items())}}}
    out(f"\n  L_B: stored {len(L_B_ing)} ingress pairs ({len(L_B)} in all), uniform {len(L_Bu_ing)} "
        f"({len(L_Bu)} in all); |A| = {len(A_p)}")
    if L_Bu_ing != L_B_ing:
        out(f"    uniform gains {res['L_B']['uniform']['gained_ingress_pairs']}, "
            f"loses {res['L_B']['uniform']['lost_ingress_pairs']}")

    # sensitivities
    sens_T = {
        "snapshot_eph_direction": pairs(uniform_ig_snap(app, snap, ipmap, listen, "eph")),
        "snapshot_all_tcp_states": pairs(uniform_ig_snap(app, snap, ipmap, listen, "listen", all_states=True)),
        "trace_tcp_plus_close": pairs(uniform_ig_tcp(app, tcp, ipmap, keep_close=True, listen=listen)),
    }
    sens_tool = {"snapshot_eph_direction": "ig_snapshot_socket", "snapshot_all_tcp_states": "ig_snapshot_socket",
                 "trace_tcp_plus_close": "ig_trace_tcp"}
    res["sensitivity"] = {}
    for sn, P in sens_T.items():
        sc = score(P, L_Bu_ing, A_p, L_Bu, EGR_UNIFORM)
        base = uni_P[sens_tool[sn]]
        res["sensitivity"][sn] = {"tool": sens_tool[sn], "P": sc["P"], "false_deny": sc["false_deny"],
                                  "over_privilege": sc["over_privilege"], "beyond_L_B": sc["beyond_L_B"],
                                  "pairs_added_over_uniform": [fe(x) for x in sorted(P - base)],
                                  "pairs_removed_from_uniform": [fe(x) for x in sorted(base - P)]}

    out(f"\n  {'tool':20} | {'stored |P|':>10} {'beyond':>6} {'FD':>6} {'OP':>6} | "
        f"{'uniform |P|':>11} {'beyond':>6} {'FD':>6} {'OP':>6} | changed")
    for t in TOOLS:
        s = score(stored_P[t], L_B_ing, A_p, L_B, EGR_STORED)
        u = score(uni_P[t], L_Bu_ing, A_p, L_Bu, EGR_UNIFORM)
        entry = {"stored": s, "uniform": u}
        if t in PORT_TOOLS:
            entry["stored"].update(score_ports(stored_T[t], L_Bt_s))
            entry["uniform"].update(score_ports(set(uni_T[t]), L_Bt_u))
            entry["port_granularity_note"] = ("computed here from the adapter triples; "
                                              "the stored scorer does not report port granularity")
        gained = sorted(uni_P[t] - stored_P[t])
        lost = sorted(stored_P[t] - uni_P[t])
        entry["gained_pairs"] = [{"pair": fe(x), "relaxations": sorted(uni_tags[t].get(x, ())),
                                  "in_L_B_ingress": x in L_Bu_ing, "in_A": x in A_p} for x in gained]
        entry["lost_pairs"] = [fe(x) for x in lost]
        keys = ("P", "beyond_L_B", "false_deny", "over_privilege")
        entry["changed"] = {k: s[k] != u[k] for k in keys}
        entry["any_change"] = any(entry["changed"].values())
        res["tools"][t] = entry
        out(f"  {t:20} | {s['P']:>10} {s['beyond_L_B']:>6} {s['false_deny']:>6.3f} {s['over_privilege']:>6.3f} | "
            f"{u['P']:>11} {u['beyond_L_B']:>6} {u['false_deny']:>6.3f} {u['over_privilege']:>6.3f} | "
            f"{'YES' if entry['any_change'] else 'no'}")
    out("\n  Port granularity (computed here; the stored scorer reports pair granularity only)")
    for t in PORT_TOOLS:
        s, u = res["tools"][t]["stored"], res["tools"][t]["uniform"]
        out(f"    {t:20} stored {s['false_deny_port']:.3f} ({s['false_deny_port_n']}/{s['L_B_ingress_triples']})"
            f"  uniform {u['false_deny_port']:.3f} ({u['false_deny_port_n']}/{u['L_B_ingress_triples']})")
    out("\n  Pairs each tool gains under the uniform rule (relaxation; in L_B ingress; in A)")
    for t in TOOLS:
        for g in res["tools"][t]["gained_pairs"]:
            out(f"    {t:20} + {g['pair']:45} {','.join(g['relaxations']) or '-':28} "
                f"L_B={g['in_L_B_ingress']} A={g['in_A']}")
        for l in res["tools"][t]["lost_pairs"]:
            out(f"    {t:20} - {l}")
    out("\n  Sensitivities outside the uniform rule")
    for sn, v in res["sensitivity"].items():
        out(f"    {sn:26} ({v['tool']}): |P| {v['P']}, FD {v['false_deny']:.3f}, OP {v['over_privilege']:.3f}, "
            f"beyond {v['beyond_L_B']}; added {v['pairs_added_over_uniform']}; "
            f"removed {v['pairs_removed_from_uniform']}")

    # ---------------- isolation rule (Online Boutique: one policy per destination with an edge)
    if key == "boutique":
        iso = {}
        out("\n  Over-privilege under the isolation rule (a target no policy selects admits every source)")
        for t in TOOLS:
            ystored = pol[t]["targets"]
            dst_stored = {d for s, d in stored_P[t] if d not in EGR_STORED}
            dst_uni = {d for s, d in uni_P[t] if d not in EGR_UNIFORM}
            si = isolation_op(stored_P[t], ystored, A_p)
            ui = isolation_op(uni_P[t], dst_uni, A_p)
            iso[t] = {"stored": si, "uniform": ui,
                      "stored_policy_targets_equal_adapter_ingress_destinations": ystored == dst_stored}
            out(f"    {t:20} stored {si['over_privilege_isolation']:.3f} (targets {len(ystored)}), "
                f"uniform {ui['over_privilege_isolation']:.3f} (targets {len(dst_uni)}); "
                f"rendered targets == adapter destinations: {ystored == dst_stored}")
        res["isolation_rule"] = iso

    # isolation rule on the stored rendered policies, every application
    res["isolation_rule_stored_policies"] = {
        t: {**isolation_op(stored_P[t], pol[t]["targets"], A_p),
            "attack_targets_not_selected": sorted({a[1] for a in A_p} - pol[t]["targets"])} for t in TOOLS}
    out("\n  Stored rendered policies under the isolation rule: " + ", ".join(
        f"{t} {v['over_privilege_isolation']:.3f}" for t, v in res["isolation_rule_stored_policies"].items()))

    # thesis table check (values printed 2026-11-05) against the stored-adapter scores
    grp = f"thesis_tab_twojourney.{key}"
    th = THESIS_TWOJOURNEY[key]
    checks.eq(grp, "|L_B|", len(L_B_ing), th["L_B"])
    checks.eq(grp, "|A|", len(A_p), th["A"])
    for t in TOOLS:
        P_, B_, FD_, OP_ = th[t]
        s = res["tools"][t]["stored"]
        op = res["isolation_rule"][t]["stored"]["over_privilege_isolation"] if key == "boutique" else s["over_privilege"]
        checks.eq(grp, f"{t} |P|", s["P"], P_)
        checks.eq(grp, f"{t} beyond L_B", s["beyond_L_B"], B_)
        checks.eq(grp, f"{t} false-deny", s["false_deny"], FD_)
        checks.eq(grp, f"{t} over-privilege", op, OP_)

    ctx = dict(app=app, ipmap=ipmap, tcp=tcp, snap=snap, listen=listen, pol=pol, stored_T=stored_T,
               stored_P=stored_P, uni_T=uni_T, uni_P=uni_P, L_B_ing=L_B_ing, L_B=L_B, L_Bu_ing=L_Bu_ing,
               hubA_s=hubA_s, hubB_s=hubB_s, cfg=cfg, A_p=A_p, rep=rep)
    return res, ctx


# ------------------------------------------------------------------------------ facts
def pair_evidence(app, ctx, pair):
    """How capture A's observers saw one directed pair: Hubble flows kept by the stored adapter,
    snapshot sockets in each state, trace_tcp events of each type."""
    tcp, snap, ipmap, listen = ctx["tcp"], ctx["snap"], ctx["ipmap"], ctx["listen"]
    s, d = pair
    ev = Counter()
    for r in tcp:
        me = app.role(r["pod"]) if r["ns"] == app.ns else None
        t = ipmap.get(r["daddr"])
        other = app.ns_role(t["ns"], t["name"]) if t else None
        if not (me and other):
            continue
        if {me, other} != {s, d}:
            continue
        if r["type"] == "connect":
            edge = (me, other)
        elif r["type"] == "accept":
            edge = (other, me)
        else:
            server = r["sport"] in listen.get(me, ()) or not (r["dport"] and r["dport"] < EPH)
            edge = (other, me) if server else (me, other)
        if edge == (s, d):
            ev[f"trace_tcp_{r['type']}"] += 1
    for r in snap:
        me = app.role(r["pod"]) if r["ns"] == app.ns else None
        t = ipmap.get(r["daddr"])
        other = app.ns_role(t["ns"], t["name"]) if t else None
        if not (me and other) or {me, other} != {s, d}:
            continue
        side = snap_side(me, other, r["sport"], r["dport"], listen, "listen")
        edge = (me, other) if side == "client" else (other, me)
        if edge == (s, d):
            ev[f"snapshot_{r['proto']}_state{r['state']}"] += 1
    return {"in_hubble_A_stored_adapter": pair in pairs(ctx["hubA_s"]),
            "events": dict(sorted(ev.items()))}


def fact_trace_tcp_entry_port(key, ctx):
    """Online Boutique and Bank of Anthos: loadgenerator -> frontend under trace_tcp."""
    app = ctx["app"]
    src, dst = "loadgenerator", "frontend"
    con, acc = Counter(), Counter()
    for r in ctx["tcp"]:
        if r["ns"] != app.ns:
            continue
        me = app.role(r["pod"])
        t = ctx["ipmap"].get(r["daddr"])
        other = app.ns_role(t["ns"], t["name"]) if t else None
        if r["type"] == "connect" and me == src and other == dst:
            con[r["dport"]] += 1
        if r["type"] == "accept" and me == dst and other == src:
            acc[r["sport"]] += 1
    pol_tt = ctx["pol"]["ig_trace_tcp"]
    pol_sn = ctx["pol"]["ig_snapshot_socket"]
    rendered = sorted(p for s, d, p in pol_tt["triples"] if (s, d) == (src, dst))
    rendered_snap = sorted(p for s, d, p in pol_sn["triples"] if (s, d) == (src, dst))
    LBt = sorted(p for s, d, p in ctx["hubB_s"] if (s, d) == (src, dst))
    drops_tt = drops_summary(app.p("enforce", "ig_trace_tcp", "hubble_drops.json"), app)
    drops_sn = drops_summary(app.p("enforce", "ig_snapshot_socket", "hubble_drops.json"), app)
    result_tt = json.load(open(app.p("enforce", "ig_trace_tcp", "result.json")))
    uni_ports = sorted(p for s, d, p in ctx["uni_T"]["ig_trace_tcp"] if (s, d) == (src, dst))
    stored_ports = sorted(p for s, d, p in ctx["stored_T"]["ig_trace_tcp"] if (s, d) == (src, dst))
    lgb = template_labels(app.p("workloads", "loadgenerator-b.yaml"))
    f = {"pair": f"{src}->{dst}",
         "connect_events_by_dst_port": dict(sorted(con.items())),
         "accept_events_by_src_port": dict(sorted(acc.items())),
         "stored_adapter_ports": stored_ports, "uniform_adapter_ports": uni_ports,
         "L_B_ports": LBt,
         "rendered_trace_tcp_policy_ports": rendered,
         "rendered_trace_tcp_policy_targets": sorted(pol_tt["targets"]),
         "rendered_snapshot_policy_ports": rendered_snap,
         "loadgenerator_b_template_labels": lgb,
         "live_trace_tcp_result_drops_by_edge": result_tt["drops_by_edge"],
         "live_trace_tcp_result_locust_fails": result_tt.get("locust_fails"),
         "live_trace_tcp_hubble_drops": drops_tt,
         "live_snapshot_hubble_drops": drops_sn,
         "uniform_ports_equal_rendered_snapshot_ports": uni_ports == rendered_snap}
    # Which destinations the trace_tcp policy leaves unselected, and where its drops landed.
    roles = {app.role(n) for n in pod_names(os.path.join(app.capA, "pods.txt"))} - {None}
    f["roles_without_trace_tcp_policy"] = sorted(roles - pol_tt["targets"])
    misses = [tuple(m.split("->")) for m in ctx["rep"]["analytical"]["ig_trace_tcp"]["missed_legit"]]
    f["trace_tcp_missed_pairs"] = [
        {"pair": "->".join(m), "destination_selected_by_trace_tcp_policy": m[1] in pol_tt["targets"],
         **pair_evidence(app, ctx, m)} for m in misses]
    rows = f["trace_tcp_missed_pairs"]
    no_open = lambda m: not m["events"].get("trace_tcp_connect") and not m["events"].get("trace_tcp_accept")
    f["missed_seen_only_on_preexisting_connections"] = [
        m["pair"] for m in rows if no_open(m) and (m["events"].get("snapshot_TCP_state1") or m["events"].get("trace_tcp_close"))]
    f["missed_absent_from_capture_A"] = [
        m["pair"] for m in rows if not m["in_hubble_A_stored_adapter"] and not m["events"]]
    drop_dsts = set()
    for k, n in drops_tt["by_edge"].items():
        drop_dsts.add(k.split("->", 1)[1].split(":", 1)[0])
    f["trace_tcp_drop_destinations"] = sorted(drop_dsts)
    f["trace_tcp_drops_on_missed_pairs"] = sum(
        n for k, n in drops_tt["by_edge"].items()
        if any(k.startswith(m[0]) and k.split("->", 1)[1].startswith(m[1] + ":") for m in misses))
    return f


def fact_otel(ctx):
    app = ctx["app"]
    f = {}
    # 1. loadgen selectors
    sel = {}
    for t in TOOLS:
        p = ctx["pol"][t]
        vals = [v for v in p["selectors"] if v is not None]
        sel[t] = {"label_keys": p["label_keys"],
                  "selectors_mapping_to_loadgen": sorted({v for v in vals if app.role(v) == "loadgen"}),
                  "stored_adapter_ingress_edges_from_loadgen": sorted(
                      fe(x) for x in (ctx["stored_T"].get(t) or {(s, d, None) for s, d in ctx["stored_P"][t]})
                      if x[0] == "loadgen" and x[1] not in EGR_STORED),
                  "policy_has_loadgen_selector": any(app.role(v) == "loadgen" for v in vals)}
    f["policies"] = sel
    f["no_policy_has_loadgen_selector"] = not any(v["policy_has_loadgen_selector"] for v in sel.values())
    f["loadgen_a_template_labels"] = template_labels(app.p("workloads", "loadgen-a.yaml"))
    f["loadgen_b_template_labels"] = template_labels(app.p("workloads", "loadgen-b.yaml"))
    f["loadgen_a_b_share_component_label"] = (
        f["loadgen_a_template_labels"].get("app.kubernetes.io/component")
        == f["loadgen_b_template_labels"].get("app.kubernetes.io/component"))
    f["load_generator_pods_A"] = [n for n in pod_names(os.path.join(app.capA, "pods.txt")) if n.startswith("loadgen")]
    f["load_generator_pods_B"] = [n for n in pod_names(os.path.join(app.capB, "pods.txt")) if n.startswith("loadgen")]
    live = {}
    for t in TOOLS:
        r = json.load(open(app.p("enforce", t, "result.json")))
        d = drops_summary(app.p("enforce", t, "hubble_drops.json"), app)
        live[t] = {"result_loadgen_b_frontend_8080": r["drops_by_edge"].get("loadgen-b->frontend:8080"),
                   "hubble_drops_loadgen_b": {k: v for k, v in d["by_edge"].items() if k.startswith("loadgen-b->")},
                   "hubble_drops_loadgen_b_source_labels": {k: v for k, v in d["source_labels"].items()
                                                            if k.startswith("loadgen-b")}}
    f["live_loadgen_b_drops"] = live
    # 2. fused pairs beyond L_B
    cfgrecs = json.load(open(app.p("policies", "config_derived_edges.json")))["needed"]
    P = ctx["stored_P"]["synth_plus_config"]
    beyond = sorted(x for x in P if x[1] not in EGR_STORED and x not in ctx["L_B"])
    fused_pol = pairs(ctx["pol"]["synth_plus_config"]["triples"])
    podsAB = pod_names(os.path.join(app.capA, "pods.txt")) + pod_names(os.path.join(app.capB, "pods.txt"))
    rows = []
    for x in beyond:
        decl = []
        for rcd in cfgrecs:
            sname = rcd["src"].split("/")[-1]
            dn = rcd["dst"].split("/")[-1]
            d2 = "kube-dns" if dn == "kube-dns" else (app.role(dn) or dn)
            if app.role(sname) == x[0] and d2 == x[1]:
                base = sname.replace("opentelemetry-demo-", "")
                decl.append({"src": rcd["src"], "dst": rcd["dst"], "port": rcd["port"],
                             "src_name_is_role": base == x[0],
                             "src_has_pod_in_A_or_B": any(n.startswith(sname) or n.startswith(base + "-")
                                                          for n in podsAB)})
        rows.append({"pair": fe(x), "in_hubble_A": x in pairs(ctx["hubA_s"]),
                     "in_declared_set": bool(decl),
                     "declared_for_source_role_itself": any(r_["src_name_is_role"] for r_ in decl),
                     "declared_only_through_prefix_match": bool(decl) and not any(r_["src_name_is_role"] for r_ in decl),
                     "admitted_by_rendered_fused_policy": x in fused_pol,
                     "declared_by": decl})
    f["fused_beyond_L_B"] = {"count": len(rows), "all_in_declared_set": all(r_["in_declared_set"] for r_ in rows),
                             "declared_for_source_role_itself": [r_["pair"] for r_ in rows if r_["declared_for_source_role_itself"]],
                             "prefix_match_only": [r_["pair"] for r_ in rows if r_["declared_only_through_prefix_match"]],
                             "pairs": rows}
    return f


def fact_teastore(ctx):
    app = ctx["app"]
    ipmap = ctx["ipmap"]
    closes, others = [], Counter()
    for r in ctx["tcp"]:
        me = app.role(r["pod"]) if r["ns"] == app.ns else None
        t = ipmap.get(r["daddr"])
        other = app.ns_role(t["ns"], t["name"]) if t else None
        if {me, other} != {"persistence", "db"}:
            continue
        others[f"{r['type']} on {me}"] += 1
        if r["type"] == "close":
            closes.append({"pod": r["pod"], "comm": r["comm"], "src_port": r["sport"],
                           "peer_role": other, "dst_port": r["dport"], "timestamp": r["ts"]})
    snapc = Counter()
    for r in ctx["snap"]:
        me = app.role(r["pod"]) if r["ns"] == app.ns else None
        t = ipmap.get(r["daddr"])
        other = app.ns_role(t["ns"], t["name"]) if t else None
        if {me, other} == {"persistence", "db"}:
            snapc[f"{r['proto']} state {r['state']} on {me}"] += 1
    return {"pair": "persistence->db",
            "trace_tcp_events_between_persistence_and_db": dict(sorted(others.items())),
            "close_events": sorted(closes, key=lambda c: str(c["timestamp"])),
            "snapshot_sockets_between_persistence_and_db": dict(sorted(snapc.items())),
            "in_stored_trace_tcp_policy": ("persistence", "db") in ctx["stored_P"]["ig_trace_tcp"],
            "in_uniform_trace_tcp": ("persistence", "db") in ctx["uni_P"]["ig_trace_tcp"],
            "rendered_trace_tcp_policy_targets_db": "db" in ctx["pol"]["ig_trace_tcp"]["targets"],
            "rendered_trace_tcp_policy_db_sources": sorted(
                s for s, d, p in ctx["pol"]["ig_trace_tcp"]["triples"] if d == "db"),
            "live_trace_tcp_result_drops_by_edge": json.load(
                open(app.p("enforce", "ig_trace_tcp", "result.json")))["drops_by_edge"]}


def fact_dsb(ctx, res):
    app = ctx["app"]
    ipmap = ctx["ipmap"]
    udp = Counter()
    udp_services = defaultdict(set)
    nonest = Counter()
    for r in ctx["snap"]:
        if r["ns"] != app.ns:
            continue
        me = app.role(r["pod"])
        t = ipmap.get(r["daddr"])
        other = (app.ns_role(t["ns"], t["name"]) if t["ns"] != "kube-system" else "kube-dns") if t else None
        if r["proto"] == "UDP" and r["dport"]:
            udp[f"{me}->{other}:{r['dport']}"] += 1
            udp_services[f"{other}:{r['dport']}"].add(me)
        elif r["proto"] == "TCP" and r["state"] not in (1, 10):
            nonest[f"state {r['state']}"] += 1
    t = res["tools"]["ig_snapshot_socket"]
    to_jaeger = {k: v for k, v in udp.items() if k.split("->")[1].startswith("jaeger:")}
    to_dns = {k: v for k, v in udp.items() if k.split("->")[1].startswith("kube-dns:")}
    return {"udp_sockets_with_remote_port": sum(udp.values()),
            "udp_sockets_by_edge": dict(sorted(udp.items())),
            "udp_to_jaeger_6831_sockets": sum(v for k, v in to_jaeger.items() if k.endswith(":6831")),
            "udp_to_jaeger_6831_services": sorted(udp_services.get("jaeger:6831", ())),
            "udp_to_kube_dns_53_sockets": sum(v for k, v in to_dns.items() if k.endswith(":53")),
            "udp_to_kube_dns_53_sources": sorted(udp_services.get("kube-dns:53", ())),
            "tcp_sockets_not_established_or_listen": dict(nonest),
            "stored": {k: t["stored"][k] for k in ("P", "beyond_L_B", "false_deny", "missed")},
            "uniform": {k: t["uniform"][k] for k in ("P", "beyond_L_B", "false_deny", "missed", "beyond_L_B_pairs")},
            "uniform_gains": t["gained_pairs"],
            "L_B_edges_uniform_snapshot_admits_and_synth_does_not": sorted(
                fe(x) for x in (ctx["uni_P"]["ig_snapshot_socket"] & ctx["L_B_ing"]) - ctx["stored_P"]["synth"])}


# ------------------------------------------------------------------------------ main
def main():
    if "--write-manifest" in sys.argv:
        manifest(True)
        return 0
    if not os.path.exists(MANIFEST):
        print("MANIFEST.sha256 missing; run with --write-manifest first")
        return 1
    man = manifest(False)
    checks = Checks()
    doc = {"artifact": "HELDOUT-UNIFORM-20261105",
           "rule_reference": os.path.relpath(RULE_REF, RES),
           "inputs": man, "apps": {}, "facts": {}}
    ctxs = {}
    for key in APP_ORDER:
        res, ctx = rescore_app(key, checks)
        doc["apps"][key] = res
        ctxs[key] = ctx

    banner("Facts behind the text corrections")
    for key in ("boutique", "bank"):
        f = fact_trace_tcp_entry_port(key, ctxs[key])
        doc["facts"][f"{key}_trace_tcp_entry_port"] = f
        out(f"\n  {APPS[key]['title']}, trace_tcp, {f['pair']}")
        out(f"    connect events by dst.port: {f['connect_events_by_dst_port']}; "
            f"accept events by src.port: {f['accept_events_by_src_port']}")
        out(f"    stored adapter ports {f['stored_adapter_ports']}, uniform {f['uniform_adapter_ports']}, "
            f"L_B ports {f['L_B_ports']}")
        out(f"    rendered trace_tcp policy ports {f['rendered_trace_tcp_policy_ports']} "
            f"(targets {f['rendered_trace_tcp_policy_targets']}); rendered snapshot policy ports "
            f"{f['rendered_snapshot_policy_ports']}; loadgenerator-b labels {f['loadgenerator_b_template_labels']}")
        out(f"    live trace_tcp result.json drops_by_edge {f['live_trace_tcp_result_drops_by_edge']}, "
            f"Locust fails {f['live_trace_tcp_result_locust_fails']}")
        out(f"    live trace_tcp hubble_drops ({f['live_trace_tcp_hubble_drops']['total']}): "
            f"{f['live_trace_tcp_hubble_drops']['by_edge']}")
        out(f"    live snapshot hubble_drops ({f['live_snapshot_hubble_drops']['total']}): "
            f"{f['live_snapshot_hubble_drops']['by_edge']}")
        out(f"    roles without a trace_tcp policy: {f['roles_without_trace_tcp_policy']}")
        out(f"    trace_tcp drops on its missed pairs: {f['trace_tcp_drops_on_missed_pairs']}")
        out(f"    missed pairs seen only on connections opened before the window (ESTABLISHED socket or "
            f"close event, no connect or accept): {len(f['missed_seen_only_on_preexisting_connections'])}"
            f" of {len(f['trace_tcp_missed_pairs'])}; absent from capture A: {f['missed_absent_from_capture_A']}")
        for m in f["trace_tcp_missed_pairs"]:
            out(f"      missed {m['pair']:36} dst selected {m['destination_selected_by_trace_tcp_policy']!s:5} "
                f"Hubble A {m['in_hubble_A_stored_adapter']!s:5} {m['events']}")
    f = fact_otel(ctxs["otel"])
    doc["facts"]["otel_loadgen_and_fused"] = f
    out("\n  OpenTelemetry demo")
    out(f"    no stored policy has a loadgen selector: {f['no_policy_has_loadgen_selector']}")
    for t, v in f["policies"].items():
        out(f"      {t:20} label keys {v['label_keys']}; adapter ingress edges from loadgen "
            f"{v['stored_adapter_ingress_edges_from_loadgen']}")
    out(f"    loadgen-a labels {f['loadgen_a_template_labels']}, loadgen-b labels {f['loadgen_b_template_labels']}, "
        f"share component label: {f['loadgen_a_b_share_component_label']}")
    out(f"    load generator pods A {f['load_generator_pods_A']}, B {f['load_generator_pods_B']}")
    for t, v in f["live_loadgen_b_drops"].items():
        out(f"      {t:20} result.json loadgen-b->frontend:8080 = {v['result_loadgen_b_frontend_8080']}; "
            f"hubble {v['hubble_drops_loadgen_b']}")
    fb = f["fused_beyond_L_B"]
    out(f"    fused pairs beyond L_B: {fb['count']}, all declared: {fb['all_in_declared_set']}")
    out(f"      declared for the source role itself: {fb['declared_for_source_role_itself']}")
    out(f"      only through role() prefix matching: {fb['prefix_match_only']}")
    for r_ in fb["pairs"]:
        out(f"        {r_['pair']:42} admitted by rendered policy {r_['admitted_by_rendered_fused_policy']!s:5} "
            f"declared by {[(d['src'], d['port'], d['src_has_pod_in_A_or_B']) for d in r_['declared_by']]}")
    f = fact_teastore(ctxs["teastore"])
    doc["facts"]["teastore_trace_tcp_db_pool"] = f
    out("\n  TeaStore, trace_tcp, persistence->db")
    out(f"    events: {f['trace_tcp_events_between_persistence_and_db']}")
    for c in f["close_events"]:
        out(f"      close {c}")
    out(f"    snapshot sockets: {f['snapshot_sockets_between_persistence_and_db']}")
    out(f"    in stored policy {f['in_stored_trace_tcp_policy']}, in uniform {f['in_uniform_trace_tcp']}; "
        f"db targeted {f['rendered_trace_tcp_policy_targets_db']} with sources {f['rendered_trace_tcp_policy_db_sources']}; "
        f"live {f['live_trace_tcp_result_drops_by_edge']}")
    f = fact_dsb(ctxs["dsb"], doc["apps"]["dsb"])
    doc["facts"]["dsb_snapshot_udp"] = f
    out("\n  DSB, snapshot_socket")
    out(f"    UDP sockets with a remote port: {f['udp_sockets_with_remote_port']}; to jaeger:6831 "
        f"{f['udp_to_jaeger_6831_sockets']} from {len(f['udp_to_jaeger_6831_services'])} services; to kube-dns:53 "
        f"{f['udp_to_kube_dns_53_sockets']} from {f['udp_to_kube_dns_53_sources']}")
    out(f"    stored |P| {f['stored']['P']}, beyond {f['stored']['beyond_L_B']}, FD {f['stored']['false_deny']}; "
        f"uniform |P| {f['uniform']['P']}, beyond {f['uniform']['beyond_L_B']}, FD {f['uniform']['false_deny']}")
    out(f"    still missed under uniform: {f['uniform']['missed']}")
    out(f"    L_B edges uniform snapshot admits and the synthesiser does not: "
        f"{f['L_B_edges_uniform_snapshot_admits_and_synth_does_not']}")

    # summary table
    banner("Stored against uniform, every application and tool (pair granularity)")
    table = []
    out(f"  {'application':20} {'tool':20} | {'|P|':>9} {'beyond':>7} {'FD':>13} {'OP':>13} | changed")
    for key in APP_ORDER:
        for t in TOOLS:
            e = doc["apps"][key]["tools"][t]
            s, u = e["stored"], e["uniform"]
            row = {"app": key, "tool": t,
                   "stored": {k: s[k] for k in ("P", "beyond_L_B", "false_deny", "over_privilege")},
                   "uniform": {k: u[k] for k in ("P", "beyond_L_B", "false_deny", "over_privilege")},
                   "changed": e["any_change"]}
            if key == "boutique":
                iso = doc["apps"][key]["isolation_rule"][t]
                row["stored"]["over_privilege_isolation"] = iso["stored"]["over_privilege_isolation"]
                row["uniform"]["over_privilege_isolation"] = iso["uniform"]["over_privilege_isolation"]
            table.append(row)
            op_s = f"{s['over_privilege']:.3f}" + (f"/{row['stored']['over_privilege_isolation']:.3f}" if key == "boutique" else "")
            op_u = f"{u['over_privilege']:.3f}" + (f"/{row['uniform']['over_privilege_isolation']:.3f}" if key == "boutique" else "")
            out(f"  {APPS[key]['title']:20} {t:20} | {s['P']:>3} -> {u['P']:<3} {s['beyond_L_B']:>2} -> {u['beyond_L_B']:<2} "
                f"{s['false_deny']:.3f} -> {u['false_deny']:.3f} {op_s:>6} -> {op_u:<6} | {'YES' if row['changed'] else 'no'}")
    out("  (Online Boutique over-privilege: allow-list / isolation rule)")
    doc["table"] = table
    doc["cells_changed"] = [f"{r['app']}.{r['tool']}" for r in table if r["changed"]]

    banner("Check summary")
    tot_p = tot_f = 0
    summary = {}
    for g in sorted(checks.groups):
        v = checks.groups[g]
        summary[g] = {"pass": v["pass"], "fail": v["fail"], "failures": v["failures"]}
        tot_p += v["pass"]
        tot_f += v["fail"]
        out(f"  {g:40} {v['pass']:4} PASS {v['fail']:3} FAIL")
    st = {k: v for k, v in summary.items() if k.startswith("stored_scores.")}
    th = {k: v for k, v in summary.items() if k.startswith("thesis_tab_twojourney.")}
    sp, sf = sum(v["pass"] for v in st.values()), sum(v["fail"] for v in st.values())
    tp, tf = sum(v["pass"] for v in th.values()), sum(v["fail"] for v in th.values())
    out(f"  stored scores.json reproduction: {sp} PASS, {sf} FAIL")
    out(f"  thesis tab:twojourney (stored adapters): {tp} PASS, {tf} FAIL")
    out(f"  all checks: {tot_p} PASS, {tot_f} FAIL; input hashes {man['ok']} OK, {man['bad']} BAD")
    doc["checks"] = {"groups": summary,
                     "stored_scores_reproduction": {"pass": sp, "fail": sf},
                     "thesis_tab_twojourney": {"pass": tp, "fail": tf},
                     "total": {"pass": tot_p, "fail": tot_f}}
    with open(os.path.join(HERE, "output.json"), "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, default=sorted)
        fh.write("\n")
    with open(os.path.join(HERE, "output.txt"), "w") as fh:
        fh.write("\n".join(OUT_LINES) + "\n")
    return 1 if (tot_f or man["bad"]) else 0


if __name__ == "__main__":
    sys.exit(main())
