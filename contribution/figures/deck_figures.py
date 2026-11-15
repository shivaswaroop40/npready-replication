#!/usr/bin/env python3
"""Deck-only variants of three thesis figures, for the defence talk (presentation/build_talk.py).

The thesis figures are left unchanged. Same data sources as the thesis figures:
- deck_attack_exec_rq1.png: fig_attack_exec without the fused-policy row (RQ1 block),
  from ../results/ATTACK-EXEC-K3S-20261109/per-app/*.json.
- deck_falsedeny_rq1.png: the deployability panel of fig_two_axes alone,
  from ../results/RESCORE-20261104/output.json.
- deck_two_journey.png: fig_two_journey with the configuration box labelled "our technique (RQ2)".
- deck_fusion.png: diag_fusion with larger text and "allow + review (observed only)".
- deck_twojourney_sources.png: fig_twojourney_sources with larger text, from
  ../results/TWO-JOURNEY-figures/coverage_cache.json (the cache that figure reads).
Run: cd contribution/figures && python3 deck_figures.py
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

import diagrams as dg
import generate_figures as gf
import thesis_diagrams as td

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "..", "results", "ATTACK-EXEC-K3S-20261109", "per-app")
APPS = [("boutique", "Online\nBoutique"), ("bank", "Bank of\nAnthos"), ("dsb", "DSB social"),
        ("otel", "OpenTelemetry\ndemo"), ("teastore", "TeaStore")]
TOOLS = [("unprotected", "no policy"), ("synth", "flow synth\n(this work)"), ("otterize", "Otterize"),
         ("ig_snapshot_socket", "IG snapshot"), ("ig_trace_tcp", "IG trace_tcp")]


def attack_exec_rq1():
    data, A = {}, {}
    for key, _ in APPS:
        d = json.load(open(os.path.join(R, f"{key}.json")))
        A[key] = d["attack_edges"]
        for tk, _ in TOOLS:
            if tk == "unprotected":
                data[(key, tk)] = sum(1 for r in d["rounds"]["unprotected"] if r["reachable"] is True)
            else:
                data[(key, tk)] = d["rounds"][tk]["attack_reachable"]
    GREEN, RED, INK = "#2a9d8f", "#e63946", "#1a1a2e"
    fig, ax = plt.subplots(figsize=(9.2, 3.5))
    nx, ny = len(APPS), len(TOOLS)
    for j, (tk, _) in enumerate(TOOLS):
        for i, (ak, _) in enumerate(APPS):
            n, tot = data[(ak, tk)], A[ak]
            if tk == "unprotected":
                fc, tc = "#d9d9d9", INK
            else:
                fc, tc = (RED if n > 0 else GREEN), "white"
            y = ny - 1 - j
            ax.add_patch(Rectangle((i, y), 0.96, 0.92, facecolor=fc, edgecolor="white", lw=2))
            ax.text(i + 0.48, y + 0.46, f"{n}/{tot}", ha="center", va="center", color=tc,
                    fontsize=10, fontweight="bold")
    ax.set_xlim(0, nx)
    ax.set_ylim(0, ny)
    ax.set_xticks([i + 0.48 for i in range(nx)])
    ax.set_xticklabels([l for _, l in APPS], fontsize=9)
    ax.set_yticks([ny - 1 - j + 0.46 for j in range(ny)])
    ax.set_yticklabels([l for _, l in TOOLS], fontsize=9)
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    ax.set_title("Attack edges that connected, executed on a Cilium cluster\n"
                 "(green = all blocked, red = reachable; reachable / total attack edges)",
                 fontsize=10.5, pad=26)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "deck_attack_exec_rq1.png"), dpi=220, bbox_inches="tight",
                facecolor="white", pad_inches=0.1)
    plt.close(fig)


def falsedeny_rq1():
    plat = gf.load_rescore()["uniform"]["platform"]
    fd = [plat["falsedeny"][k]["mean"] for k, _ in gf.GENS]
    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    xs = range(len(gf.GENS))
    bars = ax.bar(xs, fd, 0.62, color=gf.ACCENT, zorder=3)
    for r, v in zip(bars, fd):
        ax.annotate(f"{v:.3f}", (r.get_x() + r.get_width() / 2, v), textcoords="offset points",
                    xytext=(0, 4), ha="center", fontsize=9, fontweight="bold", color=gf.INK)
    ax.set_title("False-deny on the platform: legitimate edges each policy blocks\n"
                 "(39-edge reference set, mean of three runs)", fontsize=10, color=gf.INK)
    ax.set_ylim(0, 1.0)
    ax.set_xticks(list(xs))
    ax.set_xticklabels([lbl for _, lbl in gf.GENS], fontsize=8)
    ax.set_ylabel("false-deny  (lower is better)", fontsize=9.5)
    ax.grid(axis="y", color="#eeeeee", zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "deck_falsedeny_rq1.png"), dpi=150)
    plt.close(fig)


def twojourney_sources():
    cov = json.load(open(os.path.join(HERE, "..", "results", "TWO-JOURNEY-figures", "coverage_cache.json")))
    apps = ["Online Boutique", "DSB social", "Bank of Anthos", "OTel demo", "TeaStore"]
    fig, axes = plt.subplots(1, len(apps), figsize=(3.3 * len(apps), 4.4), sharey=True)
    for ax, app in zip(axes, apps):
        L, o, c, u = cov[app]
        vals = [100 * o / L, 100 * c / L, 100 * u / L]
        bars = ax.bar(["observation\n(journey A)", "config\nalone", "union"], vals, 0.62,
                      color=["#1f5fbf", "#e07b1a", "#2a9d8f"], zorder=3)
        for b, v, k in zip(bars, vals, (o, c, u)):
            ax.annotate(f"{k}/{L}\n{v:.0f}%", (b.get_x() + b.get_width() / 2, v), textcoords="offset points",
                        xytext=(0, 3), ha="center", fontsize=12, color=gf.INK)
        ax.set_title(app, fontsize=15, color=gf.INK)
        ax.set_ylim(0, 125)
        ax.grid(axis="y", color="#eee", zorder=0)
        ax.tick_params(axis="x", labelsize=11.5)
        ax.tick_params(axis="y", labelsize=11)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axes[0].set_ylabel("journey B edges recovered (%)", fontsize=12)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "deck_twojourney_sources.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    attack_exec_rq1()
    falsedeny_rq1()
    td.two_journey(cfg_what="our technique (RQ2)", out="deck_two_journey.png")
    dg.fig_fusion(out="deck_fusion.png", review="allow + review (observed only)", k=1.8)
    twojourney_sources()
    print("wrote deck_attack_exec_rq1.png, deck_falsedeny_rq1.png, deck_two_journey.png, "
          "deck_fusion.png, deck_twojourney_sources.png")
