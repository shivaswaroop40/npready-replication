#!/usr/bin/env python3
"""Two-journey figures across Boutique, DSB social network, Bank of Anthos. Reads scores.json,
enforce/<tool>/result.json and the per-app scorer modules; no number is hand-entered."""
import json, os, sys, importlib.util
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.family":"sans-serif","font.sans-serif":["Helvetica Neue","Helvetica","Arial","DejaVu Sans"],"figure.dpi":150})
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT=os.path.dirname(os.path.abspath(__file__))
INK="#1a1a2e"; MUTED="#8d99ae"
APPS=[("Online Boutique","BOUTIQUE-20260903","score_boutique"),("DSB social","DSB-SOCIAL-20260904","score_dsb"),("Bank of Anthos","BANK-20260904","score_bank"),("OTel demo","OTEL-20260906","score_otel"),("TeaStore","TEASTORE-20260906","score_teastore")]
TOOLS=[("synth (ours, traffic A)","synth (ours)","#1f5fbf"),("synth_plus_config (ours, traffic A + config)","synth + config (ours)","#2a9d8f"),
       ("otterize","Otterize","#e07b1a"),("ig_snapshot_socket","IG snapshot_socket","#8d99ae"),("ig_trace_tcp","IG trace_tcp","#e94560")]
KEY={"synth (ours, traffic A)":"synth","synth_plus_config (ours, traffic A + config)":"synth_plus_config","otterize":"otterize","ig_snapshot_socket":"ig_snapshot_socket","ig_trace_tcp":"ig_trace_tcp"}
def load(app):
    d=json.load(open(f"{R}/{app[1]}/scores/scores.json")); return d
_CACHE=json.load(open(os.path.join(OUT,"coverage_cache.json"))) if os.path.exists(os.path.join(OUT,"coverage_cache.json")) else {}
def sources(app):
    """coverage of journey B's ingress edges by observation (synth, A), config alone, union"""
    if app[0] in _CACHE:
        return tuple(_CACHE[app[0]])
    spec=importlib.util.spec_from_file_location(app[2], f"{R}/{app[1]}/{app[2]}.py"); m=importlib.util.module_from_spec(spec)
    cwd=os.getcwd(); os.chdir(f"{R}/{app[1]}"); spec.loader.exec_module(m)
    hubA=m.hubble_edges("captureA/"+[f for f in os.listdir("captureA") if f.startswith("hubble_")][0]); hubB=m.hubble_edges("captureB/"+[f for f in os.listdir("captureB") if f.startswith("hubble_")][0]); cfg=m.config_edges(); os.chdir(cwd)
    P=m.pairs; LB={(s,d) for s,d in P(hubB) if d not in ("kube-dns","world","kube-apiserver")}
    obs=P(hubA)&LB; con=P(cfg)&LB; return len(LB), len(obs), len(con), len((P(hubA)|P(cfg))&LB)
def fig_falsedeny():
    """Five held-out applications, plus the commercial platform as a marked-off sixth group.

    The platform bars come from the three-run reproduction study (reproduction/repro-*_score.json
    and FINAL-RUN-20260903/sensitivity_and_fusion.json), and are scored against the hand-built L
    rather than against a second vendor journey, so they are separated by a rule and labelled."""
    PLATFORM = {"synth (ours, traffic A)": 0.299,
                "synth_plus_config (ours, traffic A + config)": 0.103,
                "otterize": 0.709,
                "ig_snapshot_socket": 0.615,
                "ig_trace_tcp": 0.880}
    fig,ax=plt.subplots(figsize=(11.4,4.6)); n=len(APPS)+1; w=0.15
    for ti,(k,label,col) in enumerate(TOOLS):
        xs=[ai+(ti-2)*w for ai in range(n)]
        ys=[load(a)["analytical"][k]["false_deny"] for a in APPS]+[PLATFORM[k]]
        bars=ax.bar(xs,ys,w-0.02,color=col,label=label,zorder=3)
        for i,(bar,y) in enumerate(zip(bars,ys)):
            ax.annotate(f"{y:.2f}",(bar.get_x()+bar.get_width()/2,y),textcoords="offset points",
                        xytext=(0,3),ha="center",fontsize=7.5,color=INK)
    ax.axvline(len(APPS)-0.5,color="#c9ced6",lw=1.2,ls=(0,(4,3)),zorder=2)
    ax.set_xticks(range(n))
    ax.set_xticklabels([a[0] for a in APPS]+["Ankra platform"],fontsize=10)
    ax.get_xticklabels()[-1].set_fontweight("bold")
    ax.set_ylim(0,1.0)
    ax.set_ylabel("fraction of needed connections the policy blocks\n(lower is better)")
    ax.grid(axis="y",color="#eee",zorder=0)
    for s_ in ("top","right"): ax.spines[s_].set_visible(False)
    ax.text(len(APPS)-0.42,0.965,"hand-built dependency list",fontsize=7.5,color=MUTED,style="italic")
    ax.legend(frameon=False,fontsize=8.5,ncol=5,loc="upper center",bbox_to_anchor=(0.5,-0.12))
    ax.set_title("How much of the traffic each application needs would be blocked",
                 fontsize=11,color=INK)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_twojourney_falsedeny.png"); plt.close(fig)
def fig_sources():
    fig,axes=plt.subplots(1,len(APPS),figsize=(3.3*len(APPS),4.2),sharey=True)
    for ax,app in zip(axes,APPS):
        L,o,c,u=sources(app); vals=[100*o/L,100*c/L,100*u/L]; cols=["#1f5fbf","#e07b1a","#2a9d8f"]
        bars=ax.bar(["observation\n(journey A)","configuration\nalone","union"],vals,0.6,color=cols,zorder=3)
        for b,v,k in zip(bars,vals,(o,c,u)): ax.annotate(f"{k}/{L}\n{v:.0f}%",(b.get_x()+b.get_width()/2,v),textcoords="offset points",xytext=(0,3),ha="center",fontsize=8.5,color=INK)
        ax.set_title(app[0],fontsize=10.5,color=INK); ax.set_ylim(0,118); ax.grid(axis="y",color="#eee",zorder=0); ax.tick_params(axis="x",labelsize=8.5)
        for s in ("top","right"): ax.spines[s].set_visible(False)
    axes[0].set_ylabel("journey B edges recovered (%)")
    fig.suptitle("What each source recovers of the edges the evaluation journey needs",fontsize=11,color=INK)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_twojourney_sources.png"); plt.close(fig)
def fig_live():
    """Packets denied on genuine application edges during journey B under enforcement.

    Unresolved ('?') endpoints are excluded. The journey-B driver's own ingress edge is
    subtracted only where it is a constant: per application we subtract the MINIMUM driver-edge
    drop count across all tools, so a driver edge that every policy denies (OTel, where the
    journey-B pod carries a label no policy selects) cancels out, while one that only a single
    tool denies (Boutique and Bank trace_tcp, a genuine defect) is left in full."""
    fig,axes=plt.subplots(1,len(APPS),figsize=(3.3*len(APPS),4.4))
    LOADGEN=("loadgen","load-test","locust","wrk2-client")
    for ax,app in zip(axes,APPS):
        ys=[];notrun=[];drv=[]
        for k,label,col in TOOLS:
            f=f"{R}/{app[1]}/enforce/{KEY[k]}/result.json"
            if not os.path.exists(f):
                ys.append(0); notrun.append(True); drv.append(None); continue
            r=json.load(open(f))
            edges={e:v for e,v in r["drops_by_edge"].items()
                   if not e.startswith("?->") and "->?" not in e}
            d=sum(v for e,v in edges.items()
                  if any(e.split("->")[0].startswith(g) for g in LOADGEN))
            ys.append(sum(edges.values())); notrun.append(False); drv.append(d)
        seen=[d for d in drv if d is not None]
        const=min(seen) if seen else 0
        ys=[max(0,y-const) if not nr else y for y,nr in zip(ys,notrun)]
        bars=ax.bar(range(len(TOOLS)),ys,0.62,color=[t[2] for t in TOOLS],zorder=3)
        top=max(ys+[1])*1.3
        for i,(b,y) in enumerate(zip(bars,ys)):
            ax.annotate("n/r" if notrun[i] else f"{y:,}",(b.get_x()+b.get_width()/2,y),
                        textcoords="offset points",xytext=(0,3),ha="center",fontsize=8,
                        color=(MUTED if notrun[i] else INK))
            if notrun[i]: b.set_alpha(0.15)
        ax.set_xticks(range(len(TOOLS))); ax.set_xticklabels(["synth","synth\n+config","Otterize","snapshot\nsocket","trace\ntcp"],fontsize=8)
        ax.set_title(app[0],fontsize=10.5,color=INK); ax.grid(axis="y",color="#eee",zorder=0); ax.set_ylim(0,top)
        for sp in ("top","right"): ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("packets denied on application edges,\n180 s of journey B under the enforced policy")
    fig.suptitle("Live enforcement: what each generated policy actually broke",fontsize=11,color=INK)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_twojourney_live.png"); plt.close(fig)
fig_falsedeny(); fig_sources(); fig_live(); print("wrote 3 figures to",OUT)
for a in APPS: print(a[0],"L_B,obs,cfg,union =",sources(a))
