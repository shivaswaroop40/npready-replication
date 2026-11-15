#!/usr/bin/env python3
"""Score generated policies for Online Boutique.
Generation traffic = captureA (shipped Locust). Evaluation traffic = captureB (purchase journey).
Tools: our synth (Hubble A), synth+config (fusion), Otterize (t1 of A), IG trace_tcp (A), IG snapshot_socket (A).
Metrics: false-deny vs the evaluation journey's legitimate edges (L_B), over-privilege vs A_boutique,
coverage vs the config-declared set. Pair granularity for every tool; port granularity where the tool carries ports."""
import json, os, glob, sys
ART=os.path.dirname(os.path.abspath(__file__))
NS="otel"
SVCS=['adservice', 'cartservice', 'checkoutservice', 'currencyservice', 'emailservice', 'flagd', 'frauddetectionservice', 'frontend', 'imageprovider', 'kafka', 'paymentservice', 'productcatalogservice', 'quoteservice', 'recommendationservice', 'shippingservice', 'valkey', 'accountingservice', 'loadgen']
def role(pod):
    pod=pod or ""
    pod=pod.replace("opentelemetry-demo-","")
    import re as _re; pod=_re.sub(r"-[a-z0-9]{6,10}(-[a-z0-9]{4,5})?$","",pod)
    for s in sorted(SVCS,key=len,reverse=True):
        if pod.startswith(s): return s
    return None
def ns_role(ns,pod):
    if ns==NS: return role(pod)
    if ns=="kube-system": return "kube-dns"
    return None
def hubble_edges(path):
    e=set()
    for line in open(path):
        line=line.strip()
        if not line: continue
        try: o=json.loads(line)
        except: continue
        f=o.get("flow",o)
        if f.get("is_reply") or f.get("reply"): continue
        src=f.get("source") or {}; dst=f.get("destination") or {}
        s=ns_role(src.get("namespace"),src.get("pod_name"))
        if s is None or s=="kube-dns": continue
        dl=dst.get("labels") or []
        if "reserved:world" in dl: d="world"
        elif "reserved:host" in dl or "reserved:kube-apiserver" in dl: d="kube-apiserver"
        else: d=ns_role(dst.get("namespace"),dst.get("pod_name"))
        l4=f.get("l4") or {}; dp=((l4.get("TCP") or {}).get("destination_port")) or ((l4.get("UDP") or {}).get("destination_port"))
        if s and d and s!=d and dp: e.add((s,d,int(dp)))
    return e
def otterize_edges(path):
    try: data=json.load(open(path))["data"]["serviceIntents"]
    except Exception: return set()
    e=set()
    for si in data:
        c=si["client"]
        if c["namespace"]!=NS: continue
        cr=role(c["name"])
        for it in si.get("intents",[]):
            dr=role(it["name"]) if it.get("namespace")==NS else ("kube-dns" if it.get("namespace")=="kube-system" else None)
            if cr and dr and cr!=dr: e.add((cr,dr))
    return e
def ig_tcp_edges(run):
    ipmap=json.load(open(os.path.join(run,"ipmap.json"))); e=set()
    for line in open(os.path.join(run,"ig_tcp.json")):
        line=line.strip()
        if not line: continue
        try: o=json.loads(line)
        except: continue
        if o.get("type")!="connect": continue
        k=o.get("k8s") or {}
        if k.get("namespace")!=NS: continue
        s=role(k.get("podName","")); dst=o.get("dst") or {}
        t=ipmap.get(dst.get("addr","")); 
        if not t: continue
        d=ns_role(t["ns"],t["name"]) if t["ns"]!="kube-system" else "kube-dns"
        if s and d and s!=d and dst.get("port"): e.add((s,d,int(dst["port"])))
    return e
KNOWN_PORTS={8080,6379,9092,8013,53,8081}
def ig_snap_edges(run):
    ipmap=json.load(open(os.path.join(run,"ipmap.json"))); e=set(); EPH=32768
    try: arr=json.load(open(os.path.join(run,"ig_snap.json")))
    except Exception: return e
    for r in arr if isinstance(arr,list) else [arr]:
        dst=r.get("dst") or {}
        if dst.get("proto")!="TCP" or r.get("state")!=1: continue
        k=r.get("k8s") or {}
        if k.get("namespace")!=NS: continue
        pod=role(k.get("podName","")); t=ipmap.get(dst.get("addr",""))
        if not t: continue
        other=ns_role(t["ns"],t["name"]) if t["ns"]!="kube-system" else "kube-dns"
        dp=dst.get("port") or 0
        if not pod or not other or pod==other: continue
        # direction by known service port, not by an ephemeral threshold (gRPC 50051 sits above 32768)
        if dp and dp in KNOWN_PORTS: e.add((pod,other,int(dp)))
        else:
            sp=(r.get("src") or {}).get("port") or 0
            if sp and sp in KNOWN_PORTS: e.add((other,pod,int(sp)))
    return e
def config_edges():
    d=json.load(open(os.path.join(ART,"policies","config_derived_edges.json")))
    e=set()
    for x in d["needed"]:
        s=x["src"].split("/")[-1]; dst=x["dst"]; dn=dst.split("/")[-1] if "/" in dst else dst
        if dn=="kube-dns": d2="kube-dns"
        else: d2=role(dn) or dn
        if role(s) and d2: e.add((role(s),d2,int(x["port"])))
    return e
pairs=lambda T:{(s,d) for s,d,_ in T}
def score(admit_pairs,L_pairs,A_pairs):
    fd=[x for x in L_pairs if x not in admit_pairs]; op=[x for x in A_pairs if x in admit_pairs]
    return {"admit":len(admit_pairs),"false_deny":round(len(fd)/len(L_pairs),3) if L_pairs else None,
            "over_privilege":round(len(op)/len(A_pairs),3) if A_pairs else None,
            "block_rate":round(1-len(op)/len(A_pairs),3) if A_pairs else None,
            "missed_legit":sorted(f"{s}->{d}" for s,d in fd),"admitted_attacks":sorted(f"{s}->{d}" for s,d in op)}
def main():
    """Evaluation is journey B only. Configuration is an INPUT to our tool (synth_plus_config), never a reference."""
    A=os.path.join(ART,"captureA"); B=os.path.join(ART,"captureB")
    hubA=hubble_edges(os.path.join(A,"hubble_otel.json")); hubB=hubble_edges(os.path.join(B,"hubble_otel.json"))
    cfg=config_edges()
    Aatt={tuple(x) for x in json.load(open(os.path.join(ART,"attacks","A_otel.json")))["edges"]}
    L_B=pairs(hubB); A_p=pairs(Aatt)
    # ingress policies cannot deny egress to DNS; drop egress-only edges from the evaluation set so the
    # analytical number matches what enforcement can actually break
    L_B_ing={(s,d) for s,d in L_B if d not in ("kube-dns","world","kube-apiserver")}
    contamination=sorted(A_p & pairs(hubA))
    tools={"synth (ours, traffic A)":pairs(hubA),"synth_plus_config (ours, traffic A + config)":pairs(hubA)|pairs(cfg),
           "otterize":otterize_edges(os.path.join(A,"otterize_t1.json")),
           "ig_trace_tcp":pairs(ig_tcp_edges(A)),"ig_snapshot_socket":pairs(ig_snap_edges(A))}
    out={"evaluation":"journey B traffic only; policies generated from journey A",
         "L_B_pairs":len(L_B),"L_B_ingress_pairs":len(L_B_ing),"A_size":len(A_p),"attack_edges_seen_in_A_traffic":contamination,
         "L_B":sorted(f"{s}->{d}" for s,d in L_B),"analytical":{},"live_enforcement":{}}
    for t,adm in tools.items():
        r=score(adm,L_B_ing,A_p); out["analytical"][t]=r
    # live enforcement results, if the loop has run
    key={"synth (ours, traffic A)":"synth","synth_plus_config (ours, traffic A + config)":"synth_plus_config","otterize":"otterize","ig_trace_tcp":"ig_trace_tcp","ig_snapshot_socket":"ig_snapshot_socket"}
    for t,k in key.items():
        f=os.path.join(ART,"enforce",k,"result.json")
        if os.path.exists(f):
            r=json.load(open(f)); pods=os.path.join(ART,"enforce",k,"pods_after_restart.txt")
            nr=sum(1 for l in open(pods) if l.split() and l.split()[1].split("/")[0]!=l.split()[1].split("/")[1]) if os.path.exists(pods) else None
            out["live_enforcement"][t]={"drops":r.get("drops_total",r.get("total_drops")),"distinct_dropped_edges":len(r["drops_by_edge"]),"locust_fails":r.get("locust_fails","n/a"),"pods_not_ready_after_restart":nr,"top_dropped":list(r["drops_by_edge"].items())[:5]}
    json.dump(out,open(os.path.join(ART,"scores","scores.json"),"w"),indent=1)
    print(f"evaluation set: journey B, {len(L_B_ing)} ingress pairs ({len(L_B)} incl. DNS egress); attacks |A|={len(A_p)}; attack-in-A-traffic={contamination}")
    print(f"\n{'tool':46} {'admit':>5} {'false_deny_B':>12} {'over_priv':>9} | {'drops':>6} {'dropped_edges':>13} {'locust_fails':>12} {'not_ready':>9}")
    for t in tools:
        a=out["analytical"][t]; l=out["live_enforcement"].get(t,{})
        print(f"{t:46} {a['admit']:>5} {a['false_deny']:>12} {a['over_privilege']:>9} | {str(l.get('drops','-')):>6} {l.get('distinct_dropped_edges','-'):>13} {l.get('locust_fails','-'):>12} {str(l.get('pods_not_ready_after_restart','-')):>9}")
if __name__=="__main__": main()
