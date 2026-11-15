#!/usr/bin/env python3
"""Thesis diagrams: the capture mechanism, the single-window harness and the two-journey
protocol. The draft platform-by-role figure is in thesis_diagrams_platform.py.

Same block style as deck_diagrams.py. 1 unit = 1/100 inch.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

OUT = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(OUT, "..", "results", "reproduction")
BLUE, GREY, GREEN, RED, AMBER, PURPLE = "#004791", "#5A6472", "#1B7F3B", "#B00020", "#9A6B00", "#6A3D9A"
INK, MUTE = "#1A1A1A", "#6C757D"
plt.rcParams.update({"font.family": "DejaVu Sans"})
BW, BH = 200, 62


def canvas(w_in, h_in):
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    ax.set_xlim(0, w_in * 100); ax.set_ylim(0, h_in * 100)
    ax.axis("off"); ax.set_aspect("equal")
    return fig, ax


def blk(ax, x, y, name, what=None, ec=BLUE, fc="white", w=BW, h=BH, fs=10, sfs=8):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6",
                                fc=fc, ec=ec, lw=1.6, zorder=2))
    ax.text(x + w / 2, y + h / 2 + (8 if what else 0), name, ha="center", va="center",
            fontsize=fs, fontweight="bold", color=ec, zorder=3)
    if what:
        ax.text(x + w / 2, y + h / 2 - 11, what, ha="center", va="center",
                fontsize=sfs, color=INK, zorder=3, linespacing=1.2)
    return (x, y, w, h)


def arr(ax, p, q, label=None, color=BLUE, ls="-", lw=1.7, dx=0, dy=10):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=lw,
                                 color=color, linestyle=ls, shrinkA=0, shrinkB=0, zorder=4))
    if label:
        ax.text((p[0] + q[0]) / 2 + dx, (p[1] + q[1]) / 2 + dy, label, ha="center",
                va="center", fontsize=8.4, color=color, style="italic", zorder=5)


def Rm(b): x, y, w, h = b; return (x + w, y + h / 2)
def Lm(b): x, y, w, h = b; return (x, y + h / 2)
def Tm(b): x, y, w, h = b; return (x + w / 2, y + h)
def Bm(b): x, y, w, h = b; return (x + w / 2, y)


# ------------------------------------------------------------------ 1. capture mechanism
def capture_mechanism():
    fig, ax = canvas(13.4, 5.6)
    cols = [858, 990, 1110, 1236]
    hdr = [("flow synth.", "(Hubble)"), ("Otterize", ""), ("IG", "trace_tcp"), ("IG", "snapshot")]
    for cx, (a, b_) in zip(cols, hdr):
        ax.text(cx, 548, a, ha="center", fontsize=9.6, fontweight="bold", color=BLUE, va="top")
        if b_:
            ax.text(cx, 532, b_, ha="center", fontsize=8.6, color=BLUE, va="top")
    ax.plot([790, 1300], [510, 510], color=GREY, lw=1)
    ax.text(1045, 500, "is the connection in the generated policy?", ha="center",
            fontsize=8.6, style="italic", color=MUTE, va="top")

    w0, w1 = 300, 700
    ax.add_patch(Rectangle((w0, 98), w1 - w0, 362, fc="#E9F0FA", ec="none", zorder=0))
    for wx in (w0, w1):                  # window edges as short ticks clear of the row text
        for y0, y1 in ((98, 110), (446, 460)):
            ax.plot([wx, wx], [y0, y1], color=BLUE, lw=1.4, zorder=1)
    ax.text((w0 + w1) / 2, 476, "the benign window", ha="center",
            fontsize=10.5, fontweight="bold", color=BLUE, va="top")
    ax.text(w0 - 12, 476, "pods already running", ha="right", fontsize=9, color=MUTE, va="top")

    rows = [
        (428, "1", "a connection pool opened when the pod started",
         "database, message bus, cache, gRPC or JDBC; carries traffic, never reconnects"),
        (340, "2", "a connection opened inside the window",
         "one connect() event; every observer records it"),
        (252, "3", "an idle connection left behind by an earlier job",
         "still established, but carries no traffic during the window"),
        (164, "4", "a dependency that fires only on an event outside the window",
         "a reconciliation, a failover, an operation nobody performed"),
    ]
    for y, tag, label, note in rows:
        ax.text(14, y, tag + ".   " + label, fontsize=10, fontweight="bold", color=INK, va="top")
        ax.text(32, y - 17, note, fontsize=8.4, color=MUTE, style="italic", va="top")
    bar = lambda y: y - 48
    ax.add_patch(Rectangle((20, bar(428)), 730, 13, fc=GREEN, ec="none", alpha=.9))
    ax.add_patch(Rectangle((430, bar(340)), 190, 13, fc=GREEN, ec="none", alpha=.9))
    ax.add_patch(Rectangle((20, bar(252)), 280, 13, fc=AMBER, ec="none", alpha=.9))
    ax.add_patch(Rectangle((300, bar(252)), 450, 13, fc=AMBER, ec=AMBER, alpha=.22, hatch="////", lw=0))
    ax.plot([320, 690], [bar(164) + 6, bar(164) + 6], ls=(0, (5, 5)), color=RED, lw=2.2)
    ax.annotate("", xy=(770, 76), xytext=(14, 76), arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2))
    ax.text(770, 62, "time", ha="right", fontsize=9, color=INK, va="top")

    marks = [["yes", "yes", "NO", "yes"],
             ["yes", "yes", "yes", "yes"],
             ["no", "no", "no", "YES"],
             ["no", "no", "no", "no"]]
    for (y, *_), row in zip(rows, marks):
        for cx, m in zip(cols, row):
            loud = m.isupper()
            col = RED if m == "NO" else (AMBER if m == "YES" else (GREEN if m == "yes" else "#A9B0B8"))
            ax.text(cx, y - 26, m, ha="center", va="center", fontsize=11 if loud else 9.4,
                    fontweight="bold" if loud else "normal", color=col)
    fig.savefig(f"{OUT}/fig_capture_mechanism.png", dpi=200, bbox_inches="tight",
                facecolor="white", pad_inches=0.12)
    plt.close(fig)


# ------------------------------------------------------------------ 2. single-window harness
def blk2(ax, x, y, name, what, ec=BLUE, w=170, h=96, sfs=7.8):
    """Name at the top, a multi-line description under it."""
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=6",
                                fc="white", ec=ec, lw=1.6, zorder=2))
    ax.text(x + w / 2, y + h - 18, name, ha="center", va="center", fontsize=9.6,
            fontweight="bold", color=ec, zorder=3)
    ax.text(x + w / 2, y + (h - 30) / 2, what, ha="center", va="center", fontsize=sfs,
            color=INK, zorder=3, linespacing=1.3)
    return (x, y, w, h)


def harness():
    fig, ax = canvas(13.4, 4.0)
    ax.add_patch(Rectangle((10, 352), 1310, 34, fc="#FBEFF1", ec=RED, lw=1.1, zorder=0))
    ax.text(665, 369, "Guards: targets and context must match a lab allow-list  ·  production endpoints refused  ·  "
            "platform health checked first  ·  probes removed on exit",
            ha="center", va="center", fontsize=8.2, color=RED)
    st = blk2(ax, 10, 200, "start", "reset Otterize;\nstart Hubble and\ntrace_tcp", ec=GREY, w=140)
    ax.add_patch(Rectangle((172, 60), 560, 270, fc="#E9F0FA", ec=BLUE, lw=1.4, zorder=0))
    ax.text(452, 318, "30-minute benign window", ha="center", fontsize=10.5, fontweight="bold",
            color=BLUE, va="top")
    blk2(ax, 186, 186, "API driver", "187 endpoints a pass;\n184 reads + 3 calls\nthat change no state", ec=GREY, w=172)
    blk2(ax, 368, 186, "Sock Shop", "register, log in,\nbrowse, cart, orders", ec=GREY, w=166)
    blk2(ax, 544, 186, "the platform", "its own reconciliation,\nmonitoring, DNS,\nexternal calls", ec=GREY, w=174)
    obs = ["Hubble flows: whole window", "IG trace_tcp: whole window",
           "Otterize map: reset at start, read at end", "IG snapshot_socket: sampled at end"]
    for i, t in enumerate(obs):
        ax.text(192 + (i // 2) * 238, 150 - (i % 2) * 24, t, fontsize=8.2, color=BLUE, va="center")
    ax.text(192, 92, "observed traffic \u2192 adapters \u2192 edges (src, dst, port)", fontsize=8.2,
            color=INK, style="italic", va="center")
    sn = blk2(ax, 754, 200, "snapshots", "Otterize map,\nsockets,\nflow records", ec=GREY, w=140)
    at = blk2(ax, 916, 200, "attack window", "six families in a\nlabelled, disposable\nnamespace; no policy", ec=RED, w=176)
    sc = blk2(ax, 1114, 200, "score", "each policy against\nhand-assembled L and A", ec=AMBER, w=196)
    pol = blk2(ax, 916, 56, "policies", "one per observer,\nplus the fused policy", ec=BLUE, w=176, h=86)
    arr(ax, Rm(st), (172, Rm(st)[1]), color=GREY)
    arr(ax, (732, Rm(st)[1]), Lm(sn), color=GREY)
    arr(ax, Rm(sn), Lm(at), color=GREY)
    arr(ax, Rm(at), Lm(sc), "A", color=RED, dy=12)
    arr(ax, Bm(sn), (Bm(sn)[0], 99), color=BLUE)
    arr(ax, (Bm(sn)[0], 99), Lm(pol), color=BLUE)
    arr(ax, Rm(pol), Bm(sc), "P", color=BLUE, dx=16, dy=0)
    fig.savefig(f"{OUT}/fig_harness.png", dpi=200, bbox_inches="tight", facecolor="white", pad_inches=0.12)
    plt.close(fig)


# ------------------------------------------------------------------ 3. two-journey protocol
def two_journey(cfg_what="derivation, S1 to S6", out="fig_two_journey.png"):
    fig, ax = canvas(13.4, 4.3)
    ax.add_patch(Rectangle((10, 44), 510, 316, fc="#F6F8FC", ec=GREY, lw=1.2, ls=(0, (5, 4)), zorder=0))
    ax.add_patch(Rectangle((550, 44), 730, 316, fc="#F5FBF7", ec=GREEN, lw=1.2, ls=(0, (5, 4)), zorder=0))
    ax.text(265, 400, "Generate the policy", ha="center", fontsize=11.5, fontweight="bold", color=MUTE, va="top")
    ax.text(915, 400, "Score it and enforce it on a different workload", ha="center", fontsize=11.5,
            fontweight="bold", color=GREEN, va="top")
    ja = blk(ax, 36, 268, "journey A", "maintainers' load script", ec=GREY, w=186)
    ob = blk(ax, 36, 166, "observers", "Hubble, Otterize, IG x2", w=186)
    cf = blk(ax, 36, 64, "configuration", cfg_what, ec=AMBER, w=186)
    pp = blk(ax, 300, 166, "five policies", "four observed + fused", w=186)
    jb = blk(ax, 578, 268, "journey B", "a different journey", ec=GREEN, w=186)
    sp = blk(ax, 578, 166, "score", "against L_B, analytically", ec=GREEN, w=186)
    lv = blk(ax, 856, 166, "enforce", "apply, restart, run B", ec=GREEN, w=186)
    dr = blk(ax, 1094, 166, "drops", "POLICY_DENIED, 180 s", ec=GREEN, w=186, sfs=7.6)
    arr(ax, Bm(ja), Tm(ob), "traffic", color=GREY, dx=32, dy=0)
    arr(ax, Rm(ob), Lm(pp), "observed", dy=11)
    arr(ax, Rm(cf), (300, 180), "declared", color=AMBER, dx=30, dy=-22)
    arr(ax, Rm(pp), Lm(sp), "P", color=BLUE, dy=11)
    arr(ax, Bm(jb), Tm(sp), "ingress edges = L_B", color=GREEN, dx=90, dy=0)
    arr(ax, Rm(sp), Lm(lv), "false-deny", color=GREEN, dy=11)
    arr(ax, Rm(lv), Lm(dr), color=GREEN)
    fig.savefig(f"{OUT}/{out}", dpi=200, bbox_inches="tight", facecolor="white", pad_inches=0.12)
    plt.close(fig)


if __name__ == "__main__":
    capture_mechanism(); harness(); two_journey()
    print("wrote fig_capture_mechanism.png, fig_harness.png, fig_two_journey.png")
