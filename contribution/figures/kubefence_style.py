#!/usr/bin/env python3
"""Two architecture figures in the visual grammar of KubeFence's Fig. 6 (Cesarano and Natella, DSN 2025):
catalogue strip, grey rounded panels with a dark header, sub-steps as white boxes with artifact icons,
a dashed Offline/Runtime divider, tick and cross markers at the enforcement point. Units: 1/100 inch.
Run `python3 kubefence_style.py operator --check` to redraw only Figure 3.3 (fig_arch_operator.png)
and check its geometry; with no argument both figures are written."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Polygon, Circle
from matplotlib.path import Path
import os, sys
OUT=os.path.dirname(os.path.abspath(__file__))
INK="#1A1A1A"; MUTE="#6C757D"; PANEL="#ECEFF3"; HDR="#3D4650"; BLUE="#004791"; GREEN="#1B7F3B"; RED="#B00020"; AMBER="#9A6B00"
plt.rcParams.update({"font.family":"DejaVu Sans"})
CH=5.3   # approx width of one character at 6.9 pt, in units (DejaVu is wide)

def panel(ax,x,y,w,h,title):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=10",fc=PANEL,ec="#C9CFD8",lw=1,zorder=1))
    ax.add_patch(FancyBboxPatch((x,y+h-26),w,26,boxstyle="round,pad=0,rounding_size=10",fc=HDR,ec=HDR,zorder=2))
    ax.add_patch(Rectangle((x,y+h-26),w,12,fc=HDR,ec=HDR,zorder=2))
    ax.text(x+12,y+h-13,title,fontsize=8.6,fontweight="bold",color="white",va="center",zorder=3)
def box(ax,x,y,name,sub=None,ec=BLUE,fs=8.4,w=None,h=None):
    lines=(sub or "").split("\n"); need=max([len(name)*CH*1.62]+[len(l)*CH for l in lines])+24
    w=w or max(need,110); h=h or (30+16*len(lines) if sub else 34)
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=5",fc="white",ec=ec,lw=1.2,zorder=3))
    ax.text(x+w/2,y+h-13,name,ha="center",va="center",fontsize=fs,fontweight="bold",color=ec,zorder=4)
    if sub: ax.text(x+w/2,y+(h-26)/2,sub,ha="center",va="center",fontsize=6.9,color=INK,zorder=4,linespacing=1.3)
    return (x,y,w,h)
def doc(ax,x,y,label,tag=None,ec=MUTE,w=32,h=40):
    f=8
    ax.add_patch(Polygon([(x,y),(x+w-f,y),(x+w,y+f),(x+w,y+h),(x,y+h)],closed=True,fc="white",ec=ec,lw=1,zorder=4))
    ax.add_patch(Polygon([(x+w-f,y),(x+w-f,y+f),(x+w,y+f)],closed=True,fc="#DDE2E8",ec=ec,lw=0.8,zorder=5))
    for i in range(3): ax.plot([x+6,x+w-8],[y+h-11-i*7]*2,color="#B9C0CA",lw=1,zorder=5)
    if tag: ax.text(x+w/2,y+8,tag,ha="center",va="center",fontsize=5.4,color=ec,fontweight="bold",zorder=6)
    ax.text(x+w/2,y-6,label,ha="center",va="top",fontsize=6.6,color=INK,zorder=6,linespacing=1.2)
    return (x,y,w,h)
def arr(ax,p,q,label=None,color=MUTE,ls="-",lw=1.2,dy=8,dx=0):
    ax.add_patch(FancyArrowPatch(p,q,arrowstyle="-|>",mutation_scale=9,lw=lw,color=color,linestyle=ls,shrinkA=1,shrinkB=1,zorder=6))
    if label: ax.text((p[0]+q[0])/2+dx,(p[1]+q[1])/2+dy,label,ha="center",va="center",fontsize=6.6,color=color,style="italic",zorder=7)
def elbow(ax,pts,color,ls=(0,(3,2))):
    xs,ys=zip(*pts); ax.plot(xs,ys,color=color,lw=1.1,ls=ls,zorder=5); arr(ax,pts[-2],pts[-1],color=color,ls=ls)
def mark(ax,x,y,ok,label):
    ax.add_patch(Circle((x,y),8,fc=GREEN if ok else RED,ec="white",lw=1,zorder=8))
    ax.text(x,y,"✓" if ok else "✗",ha="center",va="center",fontsize=8,color="white",fontweight="bold",zorder=9)
    ax.text(x+13,y,label,fontsize=6.6,color=GREEN if ok else RED,va="center",zorder=9,linespacing=1.2)
def tile(ax,x,y,label,ec,w=82):
    ax.add_patch(FancyBboxPatch((x,y),w,44,boxstyle="round,pad=0,rounding_size=7",fc="white",ec=ec,lw=1.4,zorder=3))
    ax.text(x+w/2,y+22,label,ha="center",va="center",fontsize=6.8,color=ec,fontweight="bold",zorder=4,linespacing=1.15)
R=lambda b:(b[0]+b[2],b[1]+b[3]/2); L=lambda b:(b[0],b[1]+b[3]/2); T=lambda b:(b[0]+b[2]/2,b[1]+b[3]); B=lambda b:(b[0]+b[2]/2,b[1])


# ============================================================== Figure A: evaluation overview
def fig_evaluation():
    fig,ax=plt.subplots(figsize=(9.6,9.6)); ax.set_xlim(0,960); ax.set_ylim(0,960); ax.axis("off"); ax.set_aspect("equal")
    ax.add_patch(FancyBboxPatch((40,884),880,62,boxstyle="round,pad=0,rounding_size=8",fc="white",ec="#C9CFD8",lw=1,ls=(0,(3,2)),zorder=1))
    for i,(lab,ec) in enumerate([("Online\nBoutique",BLUE),("Bank of\nAnthos",BLUE),("OTel\ndemo",BLUE),("TeaStore",BLUE),("DeathStar\nBench",BLUE),("Sock\nShop",BLUE),("commercial\nplatform",AMBER)]):
        tile(ax,54+i*106,893,lab,ec,w=96)
    ax.text(912,915,"target\napplications",ha="right",va="center",fontsize=6.6,color=MUTE,linespacing=1.2)
    arr(ax,(460,884),(460,862),color=MUTE)
    panel(ax,40,412,880,450,"Enforcement-readiness evaluation   (policy generation and scoring)")
    # column 1: derive
    doc(ax,58,762,"manifests",tag="YAML"); doc(ax,124,762,"Ingress,\nRBAC",tag="YAML")
    b1=box(ax,58,660,"derivation","six sources, S1 to S6",w=146); arr(ax,(107,752),(107,b1[1]+b1[3]),color=MUTE)
    d1=doc(ax,88,560,"declared\nedges  L*",tag="JSON",ec=AMBER); arr(ax,B(b1),T(d1),color=AMBER)
    # column 2: observe
    b2=box(ax,236,752,"training workload","author-written (single-window)\nor journey A (held-out)",ec=MUTE,w=210)
    b3=box(ax,236,660,"observers","Hubble, Otterize, IG",w=210); arr(ax,B(b2),T(b3))
    b4=box(ax,236,558,"adapters","one per observer,\nto (src, dst, port)",w=210); arr(ax,B(b3),T(b4))
    d2=doc(ax,b4[0]+b4[2]/2-16,470,"observed\nedges  O",tag="JSON",ec=BLUE); arr(ax,B(b4),T(d2),color=BLUE)
    # column 3: attacks, reference
    b5=box(ax,470,752,"attack roster","one set per application;\nsix ATT&CK families (platform)",ec=RED,w=210)
    d3=doc(ax,b5[0]+b5[2]/2-16,690,"attack\nedges  A",tag="JSON",ec=RED); arr(ax,B(b5),T(d3),color=RED)
    b6=box(ax,470,530,"reference set  L","hand-assembled set\n(single-window) or\njourney B (held-out)",ec=AMBER,w=210)
    # column 4: policies, scorer
    b7=box(ax,700,752,"candidate policies","one per observer,\nplus fusion O ∪ L*")
    elbow(ax,[(T(b2)[0],T(b2)[1]),(T(b2)[0],830),(T(b7)[0],830),(T(b7)[0],T(b7)[1])],MUTE,ls="-"); ax.text((T(b2)[0]+T(b7)[0])/2,827,"traffic",fontsize=6.4,color=MUTE,ha="center",va="top",style="italic")
    b8=box(ax,700,660,"scorer","over-privilege,\nfalse-deny",ec=AMBER); arr(ax,B(b7),T(b8),color=BLUE)
    arr(ax,R(d3),L(b8),color=RED); arr(ax,R(b6),(b8[0],b8[1]+6),color=AMBER)
    d4=doc(ax,b8[0]+b8[2]/2-16,560,"scores per\ngenerator",tag="JSON",ec=GREEN); arr(ax,B(b8),T(d4),color=GREEN)
    # the fused policy takes L*: route under column 1, up between columns 3 and 4
    elbow(ax,[(R(d1)[0],R(d1)[1]),(160,R(d1)[1]),(160,640),(690,640),(690,b7[1]+8),(b7[0],b7[1]+8)],AMBER)
    ax.text(560,632,"L* into the fused policy",fontsize=6.4,color=AMBER,ha="center",va="top",style="italic")
    # divider
    ax.plot([40,920],[392,392],color=MUTE,lw=1.2,ls=(0,(6,4)),zorder=3)
    ax.text(46,398,"Offline",fontsize=7.6,color=MUTE,va="bottom",fontweight="bold"); ax.text(46,386,"Runtime",fontsize=7.6,color=RED,va="top",fontweight="bold")
    # runtime panel
    panel(ax,40,40,880,332,"Live enforcement on the cluster   (held-out applications)")
    ax.add_patch(FancyBboxPatch((392,62),510,262,boxstyle="round,pad=0,rounding_size=8",fc="white",ec="#C9CFD8",lw=1,zorder=2))
    ax.text(647,308,"Kubernetes cluster, Cilium CNI",ha="center",fontsize=7.6,color=INK,fontweight="bold",zorder=4)
    for i,lab in enumerate(["frontend","checkout","payment","database"]): box(ax,412+i*122,240,lab,ec=BLUE,fs=7.4,w=108)
    box(ax,412,150,"generated NetworkPolicy, enforced by the CNI","workloads restarted, so their connections re-open under it",ec=INK,fs=7.6,w=474)
    mark(ax,428,116,True,"needed edge admitted")
    mark(ax,650,116,False,"needed edge denied: POLICY_DENIED,")
    ax.text(663,100,"one count per edge",fontsize=6.6,color=RED,va="center")
    doc(ax,856,70,"drops per\nedge",tag="JSON",ec=RED,w=28,h=34)
    b9=box(ax,60,240,"evaluation workload","journey B, 180 s,\nsame maintainers",ec=MUTE)
    arr(ax,R(b9),(392,R(b9)[1]),color=MUTE)
    ax.text(60,150,"Each attack edge is also executed against\neach enforced policy, on a separate\nCilium cluster.",fontsize=6.6,color=RED,va="center",linespacing=1.25)
    fig.savefig(f"{OUT}/fig_arch_evaluation.png",dpi=220,bbox_inches="tight",facecolor="white",pad_inches=0.08); plt.close(fig)

# ============================================================== Figure B: the operator path (Figure 3.3)
# Every text is measured and every box is sized from its text, on one grid with one gap (G).
# Top tier: inputs -> inventory -> derivation / policy expansion -> reconciler -> quadrants.
# Bottom tier: what the operator receives. The quadrants copy Figure 3.2 (diagrams.py,
# fig_quadrants): same axes, cell names and rendered colours. `operator --check` verifies that
# every text sits inside its box and that no line crosses a text or a box it does not join.
Q_INK="#1B1B2F"; Q_GREY="#8D99AE"                                              # Figure 3.2 text colours
QCELL={"CORRECT":("#CBE7E3","#B7DDD9"),"UNUSED":("#F6E7D0","#F3DEBE"),
       "WOULD BREAK":("#EFC5C8","#E9B0B4"),"DENIED":("#E3E5EA","#D8DCE3")}      # Figure 3.2 fill, border
FS=dict(hdr=9.0,title=8.4,body=7.4,doc=7.2,tag=5.6,axis=7.0,cell=7.2,mono=6.6,div=7.6,foot=7.2)
SANS,MONO,LSP="DejaVu Sans","DejaVu Sans Mono",1.3

class Sheet:
    """A canvas in 1/100 inch that measures text and records every box, text and line it draws."""
    def __init__(s,W,H,dpi=400):
        s.fig=plt.figure(figsize=(W/100,H/100),dpi=dpi)
        s.ax=s.fig.add_axes((0,0,1,1)); s.ax.set_xlim(0,W); s.ax.set_ylim(0,H); s.ax.axis("off")
        s.R=s.fig.canvas.get_renderer(); s.boxes,s.parent,s.texts,s.lines,s.m={},{},[],[],{}
    def ext(s,t):
        bb=t.get_window_extent(s.R); (x0,y0),(x1,y1)=s.ax.transData.inverted().transform([(bb.x0,bb.y0),(bb.x1,bb.y1)])
        return x0,y0,x1,y1
    def _probe(s,txt,fs,weight,family):
        t=s.ax.text(0,0,txt,va="baseline",fontsize=fs,fontweight=weight,family=family); e=s.ext(t); t.remove(); return e
    def metrics(s,fs,weight="normal",family=SANS):          # ascent of "l", descent of "p", cap height
        if (fs,weight,family) not in s.m:
            _,y0,_,y1=s._probe("lp",fs,weight,family); s.m[fs,weight,family]=(y1,-y0,s._probe("H",fs,weight,family)[3])
        return s.m[fs,weight,family]
    def width(s,txt,fs,weight="normal",family=SANS):
        return max(e[2]-e[0] for e in (s._probe(l,fs,weight,family) for l in txt.split("\n")))
    def height(s,txt,fs,weight="normal",family=SANS):
        a,d,_=s.metrics(fs,weight,family); return a+d+txt.count("\n")*LSP*(a+d)
    def text(s,x,top,txt,owner,fs,ha="center",color=INK,weight="normal",family=SANS,style="normal",z=4):
        """Lines on evenly spaced baselines from `top` down; returns the bottom of the block.
        (matplotlib centres each line in its own line box, which spaces baselines unevenly.)"""
        a,d,_=s.metrics(fs,weight,family)
        for i,l in enumerate(txt.split("\n")):
            s.texts.append((s.ax.text(x,top-a-i*LSP*(a+d),l,ha=ha,va="baseline",fontsize=fs,fontweight=weight,
                                      family=family,style=style,color=color,zorder=z),owner))
        return top-s.height(txt,fs,weight,family)
    def caps(s,x,ymid,txt,owner,fs,color,weight="bold",z=4):  # one line of capitals, centred on ymid
        s.texts.append((s.ax.text(x,ymid-s.metrics(fs,weight)[2]/2,txt,ha="center",va="baseline",fontsize=fs,
                                  fontweight=weight,color=color,zorder=z),owner))
    def box(s,name,x0,y0,x1,y1,kind,parent="panel"):
        s.boxes[name]=(x0,y0,x1,y1,kind); s.parent[name]=parent
    def line(s,pts,color,src,dst,head=True):
        s.ax.add_patch(FancyArrowPatch(path=Path(pts),arrowstyle="-|>" if head else "-",mutation_scale=10,lw=1.2,
                                       color=color,zorder=6,joinstyle="miter",capstyle="butt"))
        s.lines.append((pts,src,dst))

PADX,PADT,GAPTB,PADB=10,7,6,8          # inside a box: side, top, title-to-body and bottom padding
def need(S,title,body):                # smallest box that holds a title and a body
    return (max(S.width(title,FS["title"],"bold"),S.width(body,FS["body"]))+2*PADX,
            PADT+S.height(title,FS["title"],"bold")+GAPTB+S.height(body,FS["body"])+PADB)
def op_box(S,name,x,y,w,h,title,body,ec,align="top"):
    S.ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0,rounding_size=5",fc="white",ec=ec,lw=1.2,zorder=3))
    S.box(name,x,y,x+w,y+h,"box")
    block=S.height(title,FS["title"],"bold")+GAPTB+S.height(body,FS["body"])
    top=y+h-PADT if align=="top" else y+h/2+block/2
    return S.text(x+w/2,S.text(x+w/2,top,title,name,FS["title"],color=ec,weight="bold")-GAPTB,body,name,FS["body"])
def op_doc(S,name,cx,cy,label,tag,ec=MUTE,w=36,h=40,f=9):
    x,y=cx-w/2,cy-h/2
    S.ax.add_patch(Polygon([(x,y),(x+w,y),(x+w,y+h-f),(x+w-f,y+h),(x,y+h)],closed=True,fc="white",ec=ec,lw=1,zorder=4))
    S.ax.add_patch(Polygon([(x+w-f,y+h),(x+w-f,y+h-f),(x+w,y+h-f)],closed=True,fc="#DDE2E8",ec=ec,lw=0.8,zorder=5))
    for i,x1 in enumerate((x+w-f-3,x+w-6,x+w-6)): S.ax.plot([x+6,x1],[y+h-9-i*6]*2,color="#B9C0CA",lw=1,zorder=5)
    S.box(name,x,y,x+w,y+h,"doc"); S.caps(cx,y+8,tag,name,FS["tag"],ec)
    S.text(cx,y+h+5+S.height(label,FS["doc"]),label,None,FS["doc"])           # label above the icon

def fig_operator(check=False):
    T_INV=("inventory","workloads,\nServices")
    T_DER=("derivation","needed edges from\nsix sources")
    T_EXP=("policy expansion","admitted edges of\nevery NetworkPolicy")
    T_REC=("reconciler","needed ×\nadmitted")
    T_GATE=("gate verdict","ENFORCE, AUDIT or SHADOW\nSHADOW if any edge would break\nnon-zero exit code on SHADOW,\nso it can gate a merge")
    T_BRK=("break list, with evidence","needed edges no policy admits,\nto a destination a policy protects")
    EX="shop/orders-api →\n  shop/orders-cache :6379\n[s1] REDIS_ADDR=orders-cache:6379"     # the thesis listing's example
    T_UNP=("unprotected list","needed edges whose destination\nno policy selects: they flow under\ndefault-allow, so a policy should\nbe written for them")
    DOCS=(("manifests or\nlive cluster","YAML"),("existing\npolicies","YAML"))
    W,G=760,22; X0,X1=26,W-26
    M=Sheet(W,100)                                        # measuring sheet
    # ---- horizontal grid: docs | inventory | derivation, policy expansion | reconciler | quadrants
    docw=max(M.width(l,FS["doc"]) for l,_ in DOCS)
    wT=round(max(need(M,*T_INV)[0],need(M,*T_REC)[0])); wD=round(max(need(M,*T_DER)[0],need(M,*T_EXP)[0]))
    hs=max(need(M,*t)[1] for t in (T_INV,T_DER,T_EXP,T_REC))+8       # one row; the tall boxes span two rows
    xi=X0+docw+G; xd=xi+wT+G; xr=xd+wD+G; xp=xr+wT+G
    a_h=M.metrics(FS["axis"])[0]+M.metrics(FS["axis"])[1]           # height of an axis label line
    pl,pr=6,8; cx0=xp+pl+a_h+6; cw=(X1-pr-cx0-G)/2                  # quadrant cells, gap G like everything else
    dy=(hs+G)/2; hT=2*hs+G                                          # rows: c+dy and c-dy, gap G
    # ---- bottom tier
    bw=(X1-X0-2*G)/3; ex_w,ex_h=M.width(EX,FS["mono"],family=MONO),M.height(EX,FS["mono"],family=MONO)
    hb=max(need(M,*T_BRK)[1]+6+ex_h+8,need(M,*T_UNP)[1],need(M,*T_GATE)[1])
    # ---- vertical offsets from the centre line c of the top tier
    p_top=hT/2+6+a_h+6; p_bot=hT/2+8                                # quadrant plate
    y_div=p_bot+18; y_bus=y_div+14; b_top=y_bus+20; foot=b_top+hb+16; P_bot=foot+14; P_top=p_top+12+26
    H=round(P_top+P_bot+16); c=8+P_bot
    plt.close(M.fig)

    S=Sheet(W,H); ax=S.ax
    # panel and header
    PX0,PX1,py0,py1=10,W-10,c-P_bot,c+P_top
    ax.add_patch(FancyBboxPatch((PX0,py0),PX1-PX0,py1-py0,boxstyle="round,pad=0,rounding_size=10",fc=PANEL,ec="#C9CFD8",lw=1,zorder=1))
    ax.add_patch(FancyBboxPatch((PX0,py1-26),PX1-PX0,26,boxstyle="round,pad=0,rounding_size=10",fc=HDR,ec=HDR,zorder=2))
    ax.add_patch(Rectangle((PX0,py1-26),PX1-PX0,12,fc=HDR,ec=HDR,zorder=2))
    S.box("panel",PX0,py0,PX1,py1,"panel",parent=None); S.box("header",PX0,py1-26,PX1,py1,"header")
    a,d,_=S.metrics(FS["hdr"],"bold")
    S.text(PX0+14,py1-13+(a+d)/2,"npready readiness   (run before enforcing: what would break, and where)","header",
           FS["hdr"],ha="left",color="white",weight="bold")
    # inputs -> inventory -> derivation / policy expansion -> reconciler
    dcx=X0+docw/2
    for (lab,tag),yy,nm in zip(DOCS,(c+dy,c-dy),("doc1","doc2")):
        op_doc(S,nm,dcx,yy,lab,tag)
        S.line([(dcx+18,yy),(xi-1,yy)],MUTE,nm,"inv")
    op_box(S,"inv",xi,c-hT/2,wT,hT,*T_INV,ec=BLUE,align="center")
    op_box(S,"der",xd,c+dy-hs/2,wD,hs,*T_DER,ec=BLUE,align="center")
    op_box(S,"exp",xd,c-dy-hs/2,wD,hs,*T_EXP,ec=BLUE,align="center")
    op_box(S,"rec",xr,c-hT/2,wT,hT,*T_REC,ec=AMBER,align="center")
    for yy,nm in ((c+dy,"der"),(c-dy,"exp")):
        S.line([(xi+wT,yy),(xd-1,yy)],BLUE,"inv",nm); S.line([(xd+wD,yy),(xr-1,yy)],BLUE,nm,"rec")
    # the quadrants, as in Figure 3.2: columns needed | not needed, rows admitted | denied
    ax.add_patch(FancyBboxPatch((xp,c-p_bot),X1-xp,p_top+p_bot,boxstyle="round,pad=0,rounding_size=7",fc="white",ec="#C9CFD8",lw=1,zorder=2))
    S.box("plate",xp,c-p_bot,X1,c+p_top,"plate")
    S.line([(xr+wT,c),(xp-1,c)],AMBER,"rec","plate")
    cells={}
    for col,row,nm in ((0,1,"CORRECT"),(1,1,"UNUSED"),(0,0,"WOULD BREAK"),(1,0,"DENIED")):
        x=cx0+col*(cw+G); y=(c+dy if row else c-dy)-hs/2
        ax.add_patch(FancyBboxPatch((x,y),cw,hs,boxstyle="round,pad=0,rounding_size=5",fc=QCELL[nm][0],ec=QCELL[nm][1],lw=1.8,zorder=3))
        S.box(nm,x,y,x+cw,y+hs,"cell",parent="plate"); S.caps(x+cw/2,y+hs/2,nm,nm,FS["cell"],Q_INK); cells[nm]=(x,y)
    for col,lab,colr in ((0,"needed",Q_INK),(1,"not needed",Q_GREY)):
        S.text(cx0+col*(cw+G)+cw/2,c+hT/2+6+a_h,lab,"plate",FS["axis"],color=colr)
    for yy,lab,colr in ((c+dy,"admitted",Q_INK),(c-dy,"denied",Q_GREY)):
        S.texts.append((ax.text(xp+pl+a_h/2,yy,lab,rotation=90,ha="center",va="center",fontsize=FS["axis"],color=colr,zorder=4),"plate"))
    # divider between the analysis and what the operator receives
    yd=c-y_div
    ax.plot([PX0+8,PX1-8],[yd,yd],color=MUTE,lw=1.1,ls=(0,(6,4)),zorder=2)
    a,d,_=S.metrics(FS["div"],"bold")
    S.text(X0,yd+4+a+d,"Analysis, read-only",None,FS["div"],ha="left",color=MUTE,weight="bold")
    S.text(X0,yd-4,"Output to the operator",None,FS["div"],ha="left",color=RED,weight="bold")
    # outputs: gate verdict <- break list <- WOULD BREAK -> unprotected list
    yt=c-b_top; yb=yt-hb; xs=[X0+i*(bw+G) for i in range(3)]
    op_box(S,"gate",xs[0],yb,bw,hb,*T_GATE,ec=INK)
    op_box(S,"unp",xs[2],yb,bw,hb,*T_UNP,ec=MUTE)
    tb=op_box(S,"brk",xs[1],yb,bw,hb,*T_BRK,ec=RED)
    sx=xs[1]+(bw-ex_w)/2-6
    ax.add_patch(FancyBboxPatch((sx,tb-6-ex_h-8),ex_w+12,ex_h+8,boxstyle="round,pad=0,rounding_size=3",fc="#F3F4F6",ec="#D5D9DF",lw=0.8,zorder=4))
    S.box("evidence",sx,tb-6-ex_h-8,sx+ex_w+12,tb-6,"snippet",parent="brk")
    S.text(sx+6,tb-10,EX,"evidence",FS["mono"],ha="left",family=MONO,z=5)
    # a needed edge no policy admits: break list if a policy protects its destination, else unprotected list
    wx=cells["WOULD BREAK"][0]+cw/2; yy=c-y_bus; bx,ux=xs[1]+bw/2,xs[2]+bw/2
    S.line([(wx,c-dy-hs/2),(wx,yy)],RED,"WOULD BREAK","fork",head=False)
    S.line([(wx,yy),(bx,yy),(bx,yt+1)],RED,"fork","brk")
    S.line([(wx,yy),(ux,yy),(ux,yt+1)],MUTE,"fork","unp")
    ax.add_patch(Circle((wx,yy),2.6,fc=RED,ec=RED,zorder=7))
    S.line([(xs[1],yb+hb/2),(xs[0]+bw+1,yb+hb/2)],RED,"brk","gate")     # SHADOW if the break list is not empty
    a,d,_=S.metrics(FS["foot"])
    S.text(W/2,yb-16+(a+d)/2,"The analysis never mutates the cluster. Enforcing remains a separate, explicit act by the operator.",
           None,FS["foot"],color=MUTE,style="italic")
    S.fig.savefig(f"{OUT}/fig_arch_operator.png",dpi=220,bbox_inches="tight",facecolor="white",pad_inches=0.08)
    problems=sheet_problems(S) if check else []
    plt.close(S.fig)
    return problems

def sheet_problems(S,pad=(5,3)):
    """Geometry check: text inside its owner box with padding, no overlapping texts, no text on a foreign
    box, no line through a text or through a box it does not start or end at, boxes kept apart."""
    grow=lambda r,g:(r[0]-g,r[1]-g,r[2]+g,r[3]+g)
    hit=lambda a,b:a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
    def cuts(p,q,r):                                       # segment p-q meets rectangle r (Liang-Barsky)
        t0,t1=0.0,1.0
        for pk,qk in ((p[0]-q[0],p[0]-r[0]),(q[0]-p[0],r[2]-p[0]),(p[1]-q[1],p[1]-r[1]),(q[1]-p[1],r[3]-p[1])):
            if pk==0:
                if qk<0: return False
            elif pk<0: t0=max(t0,qk/pk)
            else: t1=min(t1,qk/pk)
            if t0>t1: return False
        return True
    def up(n):
        out=[]
        while S.parent.get(n): n=S.parent[n]; out.append(n)
        return out
    T=[(t,o,S.ext(t)) for t,o in S.texts]; bad=[]
    for t,o,e in T:
        if o in S.boxes and S.boxes[o][4] not in ("plate","header"):
            r=S.boxes[o]; m=(e[0]-r[0],r[2]-e[2],e[1]-r[1],r[3]-e[3])
            if min(m[:2])<pad[0] or min(m[2:])<pad[1]: bad.append(f"text {t.get_text()!r} tight in {o}: {[round(v,1) for v in m]}")
        for n,r in S.boxes.items():
            if n!=o and n not in up(o) and r[4]!="panel" and hit(grow(e,2),r): bad.append(f"text {t.get_text()!r} on box {n}")
    for i in range(len(T)):
        for j in range(i+1,len(T)):
            if hit(grow(T[i][2],1),T[j][2]): bad.append(f"texts overlap: {T[i][0].get_text()!r} / {T[j][0].get_text()!r}")
    for pts,a,b in S.lines:
        for p,q in zip(pts,pts[1:]):
            bad+=[f"line {a}->{b} through text {t.get_text()!r}" for t,o,e in T if cuts(p,q,grow(e,3))]
            bad+=[f"line {a}->{b} through box {n}" for n,r in S.boxes.items() if n not in (a,b) and r[4]!="panel"
                  and not (r[4]=="plate" and (a in QCELL or b=="plate")) and cuts(p,q,r)]
    solid=[n for n in S.boxes if S.boxes[n][4] in ("box","doc","plate")]
    bad+=[f"boxes closer than 6: {m} / {n}" for i,m in enumerate(solid) for n in solid[i+1:] if hit(grow(S.boxes[m],6),S.boxes[n])]
    return bad

if __name__=="__main__":
    # python3 kubefence_style.py                      both figures
    # python3 kubefence_style.py operator [--check]   Figure 3.3 only (fig_arch_operator.png)
    args=sys.argv[1:]; which=[a for a in args if not a.startswith("--")] or ["evaluation","operator"]
    if "evaluation" in which: fig_evaluation()
    if "operator" in which:
        problems=fig_operator(check="--check" in args)
        if "--check" in args: print("\n".join(problems) or "geometry check: no problems")
    print("figures written:",", ".join(which))
