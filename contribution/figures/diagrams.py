#!/usr/bin/env python3
"""Hand-drawn (excalidraw-style) architecture diagrams for the thesis.

Uses matplotlib's xkcd sketch filter so the figures read as diagrams rather than
as generated charts. Each figure makes exactly one claim; arrows are labelled.
Outputs PNG at 200 dpi for LaTeX inclusion.
"""
import matplotlib

matplotlib.use("Agg")
import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, PathPatch
from matplotlib.path import Path
from matplotlib.text import Text

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = ["Chalkboard", "Comic Sans MS", "Bradley Hand", "DejaVu Sans"]

INK = "#1b1b2f"
RED = "#c1121f"
GREEN = "#2a9d8f"
AMBER = "#e09f3e"
GREY = "#8d99ae"


def box(ax, x, y, w, h, label, sub=None, color=INK, fill="none", lw=2, fs=11):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                linewidth=lw, edgecolor=color, facecolor=fill, zorder=3))
    # Each extra subtitle line moves the title up and the subtitle down, so the
    # stack stays centred and the title's descenders clear the subtitle.
    extra = sub.count("\n") if sub else 0
    k = fs / 11  # offsets scale with the font so larger text keeps the same spacing
    ax.text(x + w / 2, y + h / 2 + (k * (0.09 + 0.07 * extra) if sub else 0), label,
            ha="center", va="center", fontsize=fs, color=INK, zorder=4)
    if sub:
        ax.text(x + w / 2, y + h / 2 + k * (-0.13 + 0.02 * extra) - (k - 1) * 0.12 * extra, sub,
                ha="center", va="center", fontsize=fs - 3, color=GREY, zorder=4)


def arrow(ax, p1, p2, label=None, color=INK, style="-|>", lw=1.8, off=0.0, fs=9, shrink_a=3):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=14,
                                 linewidth=lw, color=color, zorder=2,
                                 shrinkA=shrink_a, shrinkB=3))
    if label:
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax.text(mx, my + 0.1 + off, label, ha="center", va="bottom",
                fontsize=fs, color=color, zorder=5)


def brace(ax, x, y0, y1, depth=0.25, hook=0.15, color=INK, lw=1.8):
    """Right-facing curly brace from y0 to y1 with its back at x. Returns the tip."""
    ym, xm, xt = (y0 + y1) / 2, x + depth / 2, x + depth
    verts = [(x, y1), (xm, y1), (xm, y1 - hook), (xm, ym + hook), (xm, ym), (xt, ym),
             (xm, ym), (xm, ym - hook), (xm, y0 + hook), (xm, y0), (x, y0)]
    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3, Path.CURVE3,
             Path.CURVE3, Path.CURVE3, Path.LINETO, Path.CURVE3, Path.CURVE3]
    ax.add_patch(PathPatch(Path(verts, codes), facecolor="none", edgecolor=color,
                           linewidth=lw, capstyle="round", zorder=2))
    return xt, ym


def no_text_halo(fig):
    """xkcd mode gives every artist a white stroke, which reads as a glow on text.
    Remove it from text only: boxes and arrows keep it, so fills render as before."""
    for t in fig.findobj(Text):
        t.set_path_effects([])


def canvas(w=12, h=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis("off")
    return fig, ax


# ------------------------------------------------------------------ Fig 1
def fig_quadrants():
    """The enforcement-readiness model: what each quadrant means operationally."""
    with plt.xkcd(scale=0.6, length=110, randomness=2):
        plt.rcParams["font.family"] = FONT
        # Limits hug the content; the figure size keeps the original scale
        # (0.778 in per x unit, 0.598 in per y unit) so cells keep their shape.
        fig, ax = plt.subplots(figsize=(7.24, 5.54))
        ax.set_xlim(0.58, 9.35); ax.set_ylim(0.912, 9.475); ax.axis("off")

        cells = [
            (1.4, 5.2, GREEN, "CORRECT", "admitted and needed", "keep"),
            (5.7, 5.2, AMBER, "UNUSED", "admitted, not needed", "safe to remove"),
            (1.4, 1.1, RED, "WOULD BREAK", "needed, not admitted", "fix before enforcing"),
            (5.7, 1.1, GREY, "DENIED", "neither", "attacks land here"),
        ]
        for x, y, col, title, sub, act in cells:
            ax.add_patch(FancyBboxPatch((x, y), 3.5, 3.3,
                                        boxstyle="round,pad=0.03,rounding_size=0.1",
                                        linewidth=2.4, edgecolor=col,
                                        facecolor=col, alpha=0.13, zorder=2))
            ax.text(x + 1.75, y + 2.35, title, ha="center", fontsize=13, color=INK)
            ax.text(x + 1.75, y + 1.65, sub, ha="center", fontsize=9.5, color=GREY)
            ax.text(x + 1.75, y + 0.75, act, ha="center", fontsize=10, color=col)

        ax.text(3.15, 9.15, "NEEDED", ha="center", fontsize=12, color=INK)
        ax.text(3.15, 8.80, "(declared by config)", ha="center", fontsize=8.5, color=GREY)
        ax.text(7.45, 9.15, "NOT NEEDED", ha="center", fontsize=12, color=GREY)
        ax.text(0.75, 6.85, "ADMITTED", rotation=90, va="center", ha="center",
                fontsize=12, color=INK)
        ax.text(0.75, 2.75, "DENIED", rotation=90, va="center", ha="center",
                fontsize=12, color=GREY)
        no_text_halo(fig)
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, "diag_quadrants.png"), dpi=200,
                    bbox_inches="tight", facecolor="white")
        plt.close(fig)


# ------------------------------------------------------------------ Fig 2
def fig_eval_framework():
    """C1: how any generator is scored on the same footing, without circularity."""
    with plt.xkcd(scale=0.6, length=110, randomness=2):
        plt.rcParams["font.family"] = FONT
        fig, ax = canvas(12.8, 6.8)

        # --- learning path (top): driver -> observers -> adapter -> scorer ---
        box(ax, 0.3, 4.5, 2.4, 1.1, "workload driver", "one shared window")
        for nm, yy in [("observer A", 5.55), ("observer B", 4.75), ("observer C", 3.95)]:
            box(ax, 3.6, yy - 0.32, 2.0, 0.68, nm, fs=9.5, color=GREY)
            arrow(ax, (2.7, 5.05), (3.6, yy))
        box(ax, 6.5, 4.0, 2.0, 1.6, "adapter", "-> (src,dst,port)")
        for yy in (5.55, 4.75, 3.95):
            arrow(ax, (5.6, yy), (6.5, 4.8))

        sx, sw = 9.3, 2.5
        ax.add_patch(FancyBboxPatch((sx, 3.6), sw, 2.0,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    linewidth=2, edgecolor=INK, facecolor="none", zorder=3))
        ax.text(sx + sw / 2, 5.28, "scorer", ha="center", fontsize=11, color=INK, zorder=4)
        arrow(ax, (8.5, 4.8), (sx, 4.8))
        for lbl, col, yy in [("over-privilege", RED, 4.76),
                             ("false-deny", AMBER, 4.36),
                             ("decomposition", GREY, 3.96)]:
            ax.text(sx + sw / 2, yy, lbl, ha="center", fontsize=9.5, color=col, zorder=4)

        # --- the two inputs that BYPASS the learning path entirely (routed below) ---
        box(ax, 0.3, 2.15, 2.4, 1.0, "attack executor", "separate window", color=RED)
        box(ax, 0.3, 0.45, 2.4, 1.0, "ground truth", "from deployment cfg", color=GREEN)
        ax.add_patch(FancyArrowPatch((2.7, 2.65), (9.55, 3.6),
                                     connectionstyle="arc3,rad=-0.16", arrowstyle="-|>",
                                     mutation_scale=14, lw=1.8, color=RED, zorder=2))
        ax.add_patch(FancyArrowPatch((2.7, 0.95), (9.95, 3.6),
                                     connectionstyle="arc3,rad=-0.14", arrowstyle="-|>",
                                     mutation_scale=14, lw=1.8, color=GREEN, zorder=2))
        ax.text(5.9, 2.72, "attacks A  (never seen by the observers)",
                fontsize=9.5, color=RED, ha="center")
        ax.text(6.2, 1.15, "legitimate set L  (never derived from the traffic)",
                fontsize=9.5, color=GREEN, ha="center")
        ax.text(0.3, 0.05, "both inputs bypass the learning path - that is what makes the\n"
                           "evaluation non-circular and un-gameable by the generator",
                fontsize=9.5, color=INK, ha="left")
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, "diag_eval_framework.png"), dpi=200,
                    bbox_inches="tight", facecolor="white")
        plt.close(fig)


# ------------------------------------------------------------------ Fig 3
def fig_fusion(out="diag_fusion.png", review="allow + review (observed only)", k=1.0):
    """C2: the two planes and the reconciler's four edge classes."""
    with plt.xkcd(scale=0.6, length=110, randomness=2):
        plt.rcParams["font.family"] = FONT
        # Limits hug the content; the figure size keeps the original scale
        # (about 1 in per unit) so boxes keep their shape.
        fig, ax = canvas(9.9, 4.67)
        ax.set_xlim(0.18, 10.05)
        ax.set_ylim(1.12, 5.38)
        yc = 3.25  # every column is centred on this line

        box(ax, 0.3, yc + 0.6, 2.9, 1.4, "OBSERVED flows", "eBPF / CNI logs", color=GREY, fs=11 * k)
        box(ax, 0.3, yc - 2.0, 2.9, 1.4, "DECLARED config",
            "env, Ingress, RBAC,\nDNS, headless peers", color=GREEN, fs=11 * k)

        box(ax, 4.3, yc - 0.8, 2.3, 1.6, "reconciler", "identity + port", fs=11 * k)
        arrow(ax, (3.2, yc + 1.1), (4.3, yc + 0.35))
        arrow(ax, (3.2, yc - 1.1), (4.3, yc - 0.35), color=GREEN)
        # arrow labels sit outside the two converging arrows, clear of the lines
        ax.text(3.88, yc + 0.92, "seen", ha="center", va="center", fontsize=9 * k, color=INK)
        ax.text(3.81, yc - 1.05, "declared", ha="center", va="center", fontsize=9 * k,
                color=GREEN)

        outcomes = [("allow (both)", GREEN), ("allow (declared only)", GREEN),
                    (review, AMBER), ("deny (neither)", RED)]
        for (lbl, col), yy in zip(outcomes, (yc + 1.35, yc + 0.45, yc - 0.45, yc - 1.35)):
            ax.text(7.45, yy, lbl, fontsize=10 * k, color=col, va="center")
            arrow(ax, (6.6, yc), (7.3, yy), lw=1.2, color=col)

        no_text_halo(fig)
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, out), dpi=200,
                    bbox_inches="tight", facecolor="white")
        plt.close(fig)


if __name__ == "__main__":
    fig_quadrants()
    fig_eval_framework()
    fig_fusion()
    print("wrote diag_quadrants.png, diag_eval_framework.png, diag_fusion.png")
