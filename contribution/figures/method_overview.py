#!/usr/bin/env python3
"""Thesis method figure: three phases as rows; components as blocks; every flow named on its arrow."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os
OUT=os.path.dirname(os.path.abspath(__file__))
BLUE,GREY,GREEN,RED,AMBER="#004791","#5A6472","#1B7F3B","#B00020","#9A6B00"; INK="#1A1A1A"
plt.rcParams.update({"font.family":"DejaVu Sans"})
fig,ax=plt.subplots(figsize=(13.4,6.2)); ax.set_xlim(0,1340); ax.set_ylim(0,620); ax.axis("off"); ax.set_aspect("equal")
def blk(x,y,name,what=None,ec=BLUE,fc="white",w=196,h=60,fs=9.6,sfs=7.6):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=6",fc=fc,ec=ec,lw=1.5,zorder=2))
    ax.text(x+w/2,y+h/2+(9 if what else 0),name,ha="center",va="center",fontsize=fs,fontweight="bold",color=ec,zorder=3)
    if what: ax.text(x+w/2,y+h/2-11,what,ha="center",va="center",fontsize=sfs,color=INK,zorder=3,linespacing=1.3)
    return (x,y,w,h)
def arr(p,q,label=None,color=BLUE,dy=10,dx=0,ls="-"):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle="-|>",mutation_scale=12,lw=1.5,color=color,linestyle=ls,shrinkA=2,shrinkB=2,zorder=4))
    if label: ax.text((p[0]+q[0])/2+dx,(p[1]+q[1])/2+dy,label,ha="center",va="center",fontsize=7.6,color=color,style="italic",zorder=5)
R=lambda b:(b[0]+b[2],b[1]+b[3]/2); L=lambda b:(b[0],b[1]+b[3]/2); T=lambda b:(b[0]+b[2]/2,b[1]+b[3]); B=lambda b:(b[0]+b[2]/2,b[1])
def lane(y,text,col): ax.text(14,y,text,fontsize=8.6,fontweight="bold",color=col,va="bottom"); ax.plot([14,1326],[y-4,y-4],color="#D9E0EA",lw=1,zorder=0)
# phase 1
lane(586,"PHASE 1   derive what the application declares",GREY)
c=blk(30,506,"cluster or manifests","read-only",ec=GREY); i=blk(258,506,"inventory","workloads, Services")
g=blk(486,502,"derivation","S1 config values · S2 Services · S3 Ingress\nS4 DNS · S5 RBAC · S6 headless peers",w=340,h=68,sfs=7.0)
n=blk(920,506,"NEEDED  L*","declared edges",ec=AMBER)
arr(R(c),L(i),color=GREY); arr(R(i),L(g)); arr(R(g),L(n),color=AMBER)
# phase 2
lane(480,"PHASE 2   observe what it does",GREY)
w=blk(30,400,"training workload","one window, every observer",ec=GREY); o=blk(258,400,"observers","Hubble, Otterize, IG")
a=blk(486,400,"adapters","one per observer"); ob=blk(714,400,"OBSERVED  O","(src, dst, port)")
arr(R(w),L(o),color=GREY); arr(R(o),L(a)); arr(R(a),L(ob))
# phase 3
lane(360,"PHASE 3   attack it, score every generator, reconcile before enforcing",AMBER)
p=blk(714,270,"policy  P","O alone, or O ∪ L*  (fusion)",w=400)
rc=blk(1140,270,"reconciler","NEEDED × ADMITTED",ec=AMBER)
gt=blk(590,130,"REFERENCE  L","evaluation workload, or\nthe declared dependency set",ec=AMBER,h=66)
sc=blk(816,130,"scorer","over-privilege, false-deny",ec=AMBER,h=66)
at=blk(1040,130,"ATTACKS  A","six families, executed in\na separate window",ec=RED,w=176,h=66)
o1=blk(816,14,"two numbers","per generator",ec=GREEN); o2=blk(1140,14,"break list + gate","edge, evidence, verdict",ec=GREEN)
arr(B(ob),(812,330),"O",dx=-14,dy=0); arr(B(n),(1018,330),"L*",color=AMBER,dx=14,dy=0)
arr(B(p),T(sc),"P",dx=-14,dy=0); arr(R(gt),L(sc),"L",color=AMBER,dy=12); arr(L(at),R(sc),"A",color=RED,dy=12)
arr(R(p),L(rc),"admitted",color=AMBER,dy=12)
ax.plot([1116,1128,1128],[536,536,342],color=AMBER,lw=1.5,ls=(0,(4,3)),zorder=1); arr((1128,342),(1150,330),color=AMBER,ls=(0,(4,3)))
ax.text(1136,440,"declared",fontsize=7.4,color=AMBER,style="italic",rotation=90,va="center")
arr(B(sc),T(o1),color=GREEN); arr(B(rc),T(o2),color=GREEN)
fig.savefig(f"{OUT}/fig_method_overview.png",dpi=200,bbox_inches="tight",facecolor="white",pad_inches=0.1); print("figure written")
