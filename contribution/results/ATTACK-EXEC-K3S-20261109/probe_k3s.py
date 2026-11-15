#!/usr/bin/env python3
"""Execute the attack edges of one application on the k3s+Cilium cluster.
For each edge (src_role, dst_role, port): launch a pod carrying the SOURCE workload's
exact pod-template labels (Cilium gives it that workload's identity) and open one TCP
connection to a destination pod's IP on `port`. Record connected/denied.
Runs once unprotected, then once per generated policy. No exploit payload: a bare TCP connect."""
import json, glob, os, subprocess, sys, importlib.util, time, yaml
APP_DIR, MANIFEST, NS = sys.argv[1], sys.argv[2], sys.argv[3]
KC = ["kubectl", "-n", NS]
def sh(args, **k): return subprocess.run(args, capture_output=True, text=True, **k)
def load_role(d):
    f = glob.glob(os.path.join(d, "score_*.py"))[0]
    spec = importlib.util.spec_from_file_location("sc", f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m.role
role = load_role(APP_DIR)
docs = [x for x in yaml.safe_load_all(open(os.path.join(APP_DIR, MANIFEST))) if x]
wl = {x["metadata"]["name"]: x for x in docs if x.get("kind") in ("Deployment","StatefulSet","DaemonSet")}
# map role -> a workload name and its pod-template labels
role_to_wl = {}
for n, x in wl.items():
    try: r = role(n)
    except Exception: r = None
    if r and r not in role_to_wl:
        role_to_wl[r] = (n, x["spec"]["template"]["metadata"].get("labels", {}))
A = json.load(open(glob.glob(os.path.join(APP_DIR, "attacks", "A_*.json"))[0]))["edges"]

def dst_pod_ip(dst_role):
    # find a running pod whose workload maps to dst_role
    out = sh(KC + ["get","pods","-o","json"]).stdout
    pods = json.loads(out)["items"]
    for p in pods:
        name = p["metadata"].get("generateName","") or p["metadata"]["name"]
        owner = p["metadata"].get("labels",{})
        # match by role of the pod's app label set
        for key in ("app","app.kubernetes.io/name","service","run","app.kubernetes.io/component"):
            v = owner.get(key)
            if not v: continue
            try: r = role(v)
            except Exception: r = None
            if r == dst_role and p["status"].get("phase")=="Running" and p["status"].get("podIP"):
                return p["status"]["podIP"]
    return None

def probe(src_role, dst_ip, port, tag):
    name = f"probe-{tag}".lower().replace("_","-").replace(".","-")[:60]
    labels = role_to_wl.get(src_role, (None,{}))[1]
    label_args = []
    for k,v in labels.items(): label_args += ["--labels" if False else None]  # placeholder
    # build overrides JSON so we can set arbitrary labels + command
    ov = {"apiVersion":"v1","metadata":{"labels":labels},
          "spec":{"containers":[{"name":"p","image":"busybox:1.36",
                 "command":["sh","-c",f"nc -z -w 4 {dst_ip} {port}; echo RC=$?"]}],
                 "restartPolicy":"Never"}}
    sh(KC + ["delete","pod",name,"--ignore-not-found","--wait=false"])
    r = sh(KC + ["run",name,"--image=busybox:1.36","--restart=Never",
                 f"--overrides={json.dumps(ov)}","--command","--","sh","-c",
                 f"nc -z -w 4 {dst_ip} {port}; echo RC=$?"])
    # wait for completion
    for _ in range(20):
        ph = sh(KC+["get","pod",name,"-o","jsonpath={.status.phase}"]).stdout
        if ph in ("Succeeded","Failed"): break
        time.sleep(1)
    logs = sh(KC+["logs",name]).stdout.strip()
    sh(KC + ["delete","pod",name,"--ignore-not-found","--wait=false"])
    reachable = "RC=0" in logs
    return reachable, logs

def run_round(tag):
    res = []
    for src,dst,port in A:
        ip = dst_pod_ip(dst)
        if not ip:
            res.append({"edge":f"{src}->{dst}:{port}","reachable":None,"note":"no dst pod"}); continue
        reach, logs = probe(src, ip, port, f"{tag}-{src}-{dst}-{port}")
        res.append({"edge":f"{src}->{dst}:{port}","dst_ip":ip,"reachable":reach,"log":logs})
        print(f"  [{tag}] {src}->{dst}:{port}  reachable={reach}")
    return res

OUT = {"app":NS,"attack_edges":len(A),"rounds":{}}
print(f"=== {NS}: {len(A)} attack edges ===")
print("--- unprotected ---")
OUT["rounds"]["unprotected"] = run_round("unprot")
for pol in ["synth","synth_plus_config","otterize","ig_snapshot_socket","ig_trace_tcp"]:
    pf = os.path.join(APP_DIR,"policies",f"netpol_{pol}.yaml")
    if not os.path.exists(pf): continue
    sh(KC+["delete","networkpolicy","--all","--wait=true"])
    ap = sh(KC+["apply","-f",pf])
    time.sleep(6)
    print(f"--- {pol} ({ap.stdout.strip().count('created')+ap.stdout.strip().count('configured')} policies) ---")
    rnd = run_round(pol)
    reachable_n = sum(1 for r in rnd if r["reachable"] is True)
    OUT["rounds"][pol] = {"edges":rnd,"attack_reachable":reachable_n,"over_privilege":round(reachable_n/len(A),3)}
    print(f"    => over_privilege(executed) = {reachable_n}/{len(A)} = {round(reachable_n/len(A),3)}")
sh(KC+["delete","networkpolicy","--all","--wait=false"])
json.dump(OUT, open(sys.argv[4],"w"), indent=2)
print("written", sys.argv[4])
