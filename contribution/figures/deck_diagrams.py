#!/usr/bin/env python3
"""Diagrams for the four-slide deck.

Block-diagram style: each block carries a short name and at most one short line
saying what it is. Anything that flows is named on the arrow, not inside the box.

Coordinate system: 1 unit = 1/100 inch, so a typographic point is 100/72 units.
That makes font sizes and box heights directly comparable and layout predictable.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import os

OUT = os.path.dirname(os.path.abspath(__file__))
BLUE, GREY, GREEN, RED, AMBER = "#004791", "#5A6472", "#1B7F3B", "#B00020", "#9A6B00"
INK, MUTE = "#1A1A1A", "#6C757D"
plt.rcParams.update({"font.family": "DejaVu Sans"})

BW, BH = 200, 62          # the standard block


def canvas(w_in, h_in):
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    ax.set_xlim(0, w_in * 100); ax.set_ylim(0, h_in * 100)
    ax.axis("off"); ax.set_aspect("equal")
    return fig, ax


def blk(ax, x, y, name, what=None, ec=BLUE, fc="white", w=BW, h=BH, fs=10, sfs=8):
    """A block: bold name, plus at most one short line saying what it is."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6",
                                fc=fc, ec=ec, lw=1.6, zorder=2))
    ax.text(x + w / 2, y + h / 2 + (8 if what else 0), name, ha="center", va="center",
            fontsize=fs, fontweight="bold", color=ec, zorder=3)
    if what:
        ax.text(x + w / 2, y + h / 2 - 11, what, ha="center", va="center",
                fontsize=sfs, color=INK, zorder=3)
    return (x, y, w, h)


def arr(ax, p, q, label=None, color=BLUE, ls="-", lw=1.7, dx=0, dy=10):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=13,
                                 lw=lw, color=color, linestyle=ls,
                                 shrinkA=2, shrinkB=2, zorder=4))
    if label:
        ax.text((p[0] + q[0]) / 2 + dx, (p[1] + q[1]) / 2 + dy, label,
                ha="center", va="center", fontsize=8, color=color,
                style="italic", zorder=5, linespacing=1.4)


def Rm(b): x, y, w, h = b; return (x + w, y + h / 2)
def Lm(b): x, y, w, h = b; return (x, y + h / 2)
def Tm(b): x, y, w, h = b; return (x + w / 2, y + h)
def Bm(b): x, y, w, h = b; return (x + w / 2, y)


# ----------------------------------------------------------------- 1. architecture
def architecture():
    W, H = 13.4, 6.4
    fig, ax = canvas(W, H)

    ax.text(10, 626, "npready", fontsize=15, fontweight="bold", color=BLUE, va="top")
    ax.text(158, 623, "about 1,800 lines of Python, Apache-2.0, v0.2.1",
            fontsize=9, color=MUTE, va="top")

    ax.add_patch(Rectangle((10, 314), 1320, 284, fc="#F7F9FC", ec="#D9E0EA", lw=1, zorder=0))
    ax.add_patch(Rectangle((10, 16), 1320, 274, fc="#FAF7F2", ec="#E6DCCB", lw=1, zorder=0))
    ax.text(22, 590, "WHAT YOU RUN BEFORE ENFORCING", fontsize=9.5, fontweight="bold",
            color=MUTE, va="top")
    ax.text(22, 282, "HOW THE TOOLS ARE COMPARED", fontsize=9.5, fontweight="bold",
            color=AMBER, va="top")

    # ---- lane 1
    cx = [30, 300, 570, 840, 1110]
    cl  = blk(ax, cx[0], 478, "cluster", "or a folder of YAML", ec=GREY, fc="white", w=190)
    iv  = blk(ax, cx[1], 478, "inventory.py", "read the cluster", w=190)
    gr  = blk(ax, cx[2], 478, "graph.py", "config → needed", w=190)
    npo = blk(ax, cx[0], 336, "NetworkPolicy", "what is already there", ec=GREY, fc="white", w=190)
    po  = blk(ax, cx[1], 336, "policy.py", "policy → admitted", w=190)
    blk(ax, cx[3], 407, "reconcile.py", "needed × admitted", w=190)
    o1  = blk(ax, cx[4], 478, "the break list", "edge + evidence", ec=GREEN, w=190)
    o2  = blk(ax, cx[4], 336, "the gate", "enforce / audit / shadow", ec=GREEN, w=190, sfs=7.4)

    arr(ax, Rm(cl), Lm(iv), "read-only", color=GREY)
    arr(ax, Rm(iv), Lm(gr), "workloads,\nServices", dy=17)
    arr(ax, Rm(npo), Lm(po), color=GREY)
    arr(ax, Rm(gr), (cx[3], 453), "NEEDED", dy=13)
    arr(ax, Rm(po), (cx[3], 423), "ADMITTED", dx=60, dy=-13)
    arr(ax, (cx[3] + 190, 453), Lm(o1), "breaks", dy=13)
    arr(ax, (cx[3] + 190, 423), Lm(o2), "verdict", dy=-13)

    ax.text(cx[2], 470, "S1 config values · S2 Services\n"
                        "S3 Ingress · S4 DNS\nS5 RBAC · S6 headless peers",
            fontsize=7.6, color=MUTE, va="top", linespacing=1.5)

    # ---- lane 2
    bw = blk(ax, cx[0], 150, "benign window", "one window, all four tools", ec=GREY, fc="white",
             w=180, sfs=7.6)
    ad = blk(ax, cx[1], 150, "4 adapters", "one per observer", w=180)
    pl = blk(ax, cx[2], 150, "5 policies", "one per generator", w=180)
    sc = blk(ax, cx[3], 150, "score.py", "policy vs truth", ec=AMBER, w=180)
    nm = blk(ax, cx[4], 150, "2 numbers", "per tool", ec=GREEN, w=180)
    gl = blk(ax, cx[3] - 4, 36, "truth L", None, ec=AMBER, fc="white", w=88, h=46, fs=8.6)
    at = blk(ax, cx[3] + 96, 36, "attacks A", None, ec=RED, fc="white", w=88, h=46, fs=8.6)

    arr(ax, Rm(bw), Lm(ad), "flows", color=GREY)
    arr(ax, Rm(ad), Lm(pl), "(src,dst,port)")
    arr(ax, Rm(pl), Lm(sc), "P", color=AMBER)
    arr(ax, Rm(sc), Lm(nm), "scores", color=GREEN)
    arr(ax, Tm(gl), (cx[3] + 40, 150), color=AMBER)
    arr(ax, Tm(at), (cx[3] + 140, 150), color=RED)

    ax.text(cx[1] + 90, 142, "Hubble is my own adapter", fontsize=7.8, color=BLUE,
            va="top", ha="center")
    ax.text(cx[2] + 90, 142, "mine = Hubble plus what config declares", fontsize=7.8, color=BLUE,
            va="top", ha="center")

    ax.plot([cx[2] + 90, cx[2] + 90], [478, 218], color=BLUE, lw=1.5, ls=(0, (5, 3)), zorder=1)
    arr(ax, (cx[2] + 90, 224), (cx[2] + 90, 212), color=BLUE, lw=1.5)
    ax.text(cx[2] + 98, 350, "declared", fontsize=8, color=BLUE, style="italic", va="center")

    fig.savefig(f"{OUT}/deck_architecture.png", dpi=200, bbox_inches="tight",
                facecolor="white", pad_inches=0.12)
    plt.close(fig)


# ----------------------------------------------------------------- 2. capture semantics
def capture():
    W, H = 13.4, 6.8
    fig, ax = canvas(W, H)

    ax.text(14, 666, "What the traffic actually looks like", fontsize=12,
            fontweight="bold", color=INK, va="top")

    cols = [858, 976, 1096, 1222]
    hdr = [("Hubble", "mine"), ("Otterize", ""), ("IG", "trace_tcp"), ("IG", "snapshot")]
    for cx, (a, b_) in zip(cols, hdr):
        ax.text(cx, 668, a, ha="center", fontsize=9.6, fontweight="bold", color=BLUE, va="top")
        if b_:
            ax.text(cx, 652, b_, ha="center", fontsize=8.6, color=BLUE, va="top")
    ax.plot([800, 1300], [630, 630], color=GREY, lw=1)
    ax.text(1050, 620, "does it reach the generated policy?", ha="center",
            fontsize=8.6, style="italic", color=MUTE, va="top")

    w0, w1 = 300, 700
    ax.add_patch(Rectangle((w0, 218), w1 - w0, 362, fc="#E9F0FA", ec=BLUE, lw=1.4, zorder=0))
    ax.text((w0 + w1) / 2, 596, "the 30-minute capture window", ha="center",
            fontsize=10.5, fontweight="bold", color=BLUE, va="top")
    ax.text(w0 - 12, 596, "pods already running", ha="right", fontsize=9, color=MUTE, va="top")

    rows = [
        (548, "1", "a gRPC or JDBC pool, opened when the pod started",
         "carries traffic all window, never reconnects"),
        (460, "2", "a connection opened inside the window",
         "one connect() event, and everybody sees it"),
        (372, "3", "a pool left behind by a job that ran earlier",
         "still ESTABLISHED, but carrying nothing now"),
        (284, "4", "a dependency gated on an event that never fires",
         "nightly reconcile, a failover, a button nobody pressed"),
    ]
    for y, tag, label, note in rows:
        ax.text(14, y, tag + ".   " + label, fontsize=10, fontweight="bold", color=INK, va="top")
        ax.text(32, y - 17, note, fontsize=8.6, color=MUTE, style="italic", va="top")

    bar = lambda y: y - 48
    ax.add_patch(Rectangle((20, bar(548)), 730, 13, fc=GREEN, ec="none", alpha=.9))
    ax.add_patch(Rectangle((430, bar(460)), 190, 13, fc=GREEN, ec="none", alpha=.9))
    ax.add_patch(Rectangle((20, bar(372)), 280, 13, fc=AMBER, ec="none", alpha=.9))
    ax.add_patch(Rectangle((300, bar(372)), 450, 13, fc=AMBER, ec=AMBER, alpha=.22, hatch="////", lw=0))
    ax.plot([320, 690], [bar(284) + 6, bar(284) + 6], ls=(0, (5, 5)), color=RED, lw=2.2)

    ax.annotate("", xy=(770, 196), xytext=(14, 196),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2))
    ax.text(770, 182, "time", ha="right", fontsize=9, color=INK, va="top")

    marks = [["yes", "yes", "NO", "yes"],
             ["yes", "yes", "yes", "yes"],
             ["no", "no", "no", "YES"],
             ["no", "no", "no", "no"]]
    for (y, *_), row in zip(rows, marks):
        for cx, m in zip(cols, row):
            loud = m.isupper()
            col = RED if m == "NO" else (AMBER if m == "YES" else (GREEN if m == "yes" else "#A9B0B8"))
            ax.text(cx, y - 26, m, ha="center", va="center",
                    fontsize=11 if loud else 9.4,
                    fontweight="bold" if loud else "normal", color=col)

    ax.plot([14, 1300], [166, 166], color=GREY, lw=1)
    ax.text(14, 152, "Two mistakes you cannot see from the tool's own output",
            fontsize=11, fontweight="bold", color=INK, va="top")
    ax.text(32, 122,
            "trace_tcp misses row 1. It watches connect(), and row 1 never reconnects. Online Boutique\n"
            "is entirely row 1, so trace_tcp emitted a single rule and took the application off the air.",
            fontsize=9.2, color=RED, va="top", linespacing=1.55)
    ax.text(32, 62,
            "snapshot_socket counts row 3. It lists established sockets, whoever opened them. On DeathStarBench\n"
            "that handed it the best score of any observer, earned from a data-loading job's leftovers.",
            fontsize=9.2, color=AMBER, va="top", linespacing=1.55)

    fig.savefig(f"{OUT}/deck_capture.png", dpi=200, bbox_inches="tight",
                facecolor="white", pad_inches=0.12)
    plt.close(fig)


# ----------------------------------------------------------------- 3. two-journey protocol
def protocol():
    W, H = 13.4, 4.3
    fig, ax = canvas(W, H)

    ax.add_patch(Rectangle((10, 44), 510, 316, fc="#F6F8FC", ec=GREY, lw=1.2, ls=(0, (5, 4)), zorder=0))
    ax.add_patch(Rectangle((550, 44), 730, 316, fc="#F5FBF7", ec=GREEN, lw=1.2, ls=(0, (5, 4)), zorder=0))
    ax.text(265, 400, "Generate the policy", ha="center", fontsize=11.5, fontweight="bold", color=MUTE, va="top")
    ax.text(915, 400, "Test it on traffic it has never seen", ha="center", fontsize=11.5,
            fontweight="bold", color=GREEN, va="top")

    ja = blk(ax, 36, 268, "journey A", "the vendor's own", ec=GREY, fc="white", w=186)
    ob = blk(ax, 36, 166, "4 observers", "all at once", w=186)
    cf = blk(ax, 36, 64, "config", "S1 to S6, mine", ec=AMBER, w=186)
    pp = blk(ax, 300, 166, "5 policies", "one per generator", w=186)

    jb = blk(ax, 578, 268, "journey B", "a different one", ec=GREEN, fc="white", w=186)
    sp = blk(ax, 578, 166, "score", "on paper", ec=GREEN, w=186)
    lv = blk(ax, 856, 166, "enforce it", "restart, run B", ec=GREEN, w=186)
    dr = blk(ax, 1094, 166, "drops", "POLICY_DENIED", ec=GREEN, w=186, sfs=7.6)

    arr(ax, Bm(ja), Tm(ob), "traffic", color=GREY, dx=32, dy=0)
    arr(ax, Rm(ob), Lm(pp), "observed", dy=11)
    arr(ax, Rm(cf), (300, 180), "declared", color=AMBER, dx=6, dy=-12)
    arr(ax, Rm(pp), Lm(sp), "P", color=BLUE, dy=11)
    arr(ax, Bm(jb), Tm(sp), "the edges B needs", color=GREEN, dx=54, dy=0)
    arr(ax, Rm(sp), Lm(lv), "false-deny", color=GREEN, dy=11)
    arr(ax, Rm(lv), Lm(dr), color=GREEN)

    ax.text(645, 16, "Journey A and journey B are different. I wrote neither of them. All five policies are scored the same way.",
            ha="center", fontsize=10.5, fontweight="bold", color=INK, va="bottom")

    fig.savefig(f"{OUT}/deck_protocol.png", dpi=200, bbox_inches="tight",
                facecolor="white", pad_inches=0.12)
    plt.close(fig)


architecture(); capture(); protocol()
print("wrote deck_architecture.png, deck_capture.png, deck_protocol.png")
