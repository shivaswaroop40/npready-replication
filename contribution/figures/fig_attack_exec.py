import json, glob, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
HERE=os.path.dirname(os.path.abspath(__file__))
R=os.path.join(HERE,"..","results","ATTACK-EXEC-K3S-20261109","per-app")
APPS=[("boutique","Online\nBoutique"),("bank","Bank of\nAnthos"),("dsb","DSB social"),("otel","OpenTelemetry\ndemo"),("teastore","TeaStore")]
TOOLS=[("unprotected","no policy"),("synth","flow synth\n(this work)"),("synth_plus_config","fused\n(this work)"),("otterize","Otterize"),("ig_snapshot_socket","IG snapshot"),("ig_trace_tcp","IG trace_tcp")]
data={}; A={}
for key,_ in APPS:
    d=json.load(open(os.path.join(R,f"{key}.json"))); A[key]=d["attack_edges"]
    for tk,_ in TOOLS:
        if tk=="unprotected":
            data[(key,tk)]=sum(1 for r in d["rounds"]["unprotected"] if r["reachable"] is True)
        else:
            data[(key,tk)]=d["rounds"][tk]["attack_reachable"]
GREEN="#2a9d8f"; RED="#e63946"; INK="#1a1a2e"; GREY="#8d99ae"
fig,ax=plt.subplots(figsize=(9.2,4.0))
nx,ny=len(APPS),len(TOOLS)
for j,(tk,tl) in enumerate(TOOLS):
    for i,(ak,al) in enumerate(APPS):
        n=data[(ak,tk)]; tot=A[ak]
        reachable=n>0
        # unprotected: all reachable = "attack lands" (expected, grey-ish); policy: red if any reachable else green
        if tk=="unprotected":
            fc="#d9d9d9"; tc=INK
        else:
            fc=RED if reachable else GREEN; tc="white"
        y=ny-1-j
        ax.add_patch(Rectangle((i,y),0.96,0.92,facecolor=fc,edgecolor="white",lw=2))
        ax.text(i+0.48,y+0.46,f"{n}/{tot}",ha="center",va="center",color=tc,fontsize=10,fontweight="bold")
ax.set_xlim(0,nx); ax.set_ylim(0,ny)
ax.set_xticks([i+0.48 for i in range(nx)]); ax.set_xticklabels([l for _,l in APPS],fontsize=9)
ax.set_yticks([ny-1-j+0.46 for j in range(ny)]); ax.set_yticklabels([l for _,l in TOOLS],fontsize=9)
ax.xaxis.set_ticks_position("top"); ax.xaxis.set_label_position("top")
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(length=0)
ax.set_title("Attack edges that connected, executed on a Cilium cluster\n(green = all blocked, red = reachable; numbers are reachable / total attack edges)",
             fontsize=10.5, pad=26)
fig.tight_layout()
fig.savefig(os.path.join(HERE,"fig_attack_exec.png"),dpi=220,bbox_inches="tight",facecolor="white",pad_inches=0.1)
print("wrote fig_attack_exec.png")
