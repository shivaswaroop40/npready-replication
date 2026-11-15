import json,re,os
W=os.path.dirname(os.path.abspath(__file__)); d=json.load(open(f'{W}/scores/scores.json')); r=open(f'{W}/README.md').read()
rows={"synth (ours, traffic A)":"synth (ours, traffic A)","synth_plus_config (ours, traffic A + config)":"synth + config (ours)","otterize":"Otterize","ig_trace_tcp":"IG trace_tcp","ig_snapshot_socket":"IG snapshot_socket"}
for k,label in rows.items():
    a=d['analytical'][k]; l=d['live_enforcement'].get(k,{})
    line=f"| {label} | {a['admit']} | **{a['false_deny']:.3f}** | {a['over_privilege']:.3f} | {l.get('drops','n/a')} | {l.get('locust_fails','n/a')} | {l.get('pods_not_ready_after_restart','n/a')} |"
    r=re.sub(r'\| '+re.escape(label)+r' \| ADMIT[^\n]*', line, r)
rec=open(f'{W}/attacks/recon_result.txt').read() if os.path.exists(f'{W}/attacks/recon_result.txt') else ''
r=r.replace('RECON targets', f"{rec.count('OPEN')} of {rec.count('RESULT ')} targets")
open(f'{W}/README.md','w').write(r); print("README filled (RESULT_PARAGRAPH left for the author's sentence)")
