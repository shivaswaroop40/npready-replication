#!/usr/bin/env python3
"""Generate the thesis figures from the REAL reproduced data.

fig_reproducibility, fig_two_axes and fig_ceiling plot the platform scores under the
UNIFORM adapter rule, read from ../results/RESCORE-20261104/output.json (written by
rescore_platform.py in that directory). load() still reads the stored per-run score
files under ../results/reproduction/ (the AS_WRITTEN adapters) for reference.
No hand-entered numbers: everything is read from those files.
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Professional, neutral sans across every figure. Helvetica Neue first (present on
# macOS), then portable fallbacks so the figures render the same on a CI box.
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
    "axes.titleweight": "medium",
    "svg.fonttype": "none",
    "figure.dpi": 150,
})

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results", "reproduction")
RESCORE = os.path.join(HERE, "..", "results", "RESCORE-20261104", "output.json")
RESCORE_RUNS = ["run1", "run2", "run3"]   # the three repetitions, in the order of RUNS
RUNS = ["repro-20260824-161956", "repro-20260824-165159", "repro-20260824-172334"]
GENS = [
    ("our_synth_hubble", "flow synth\n(this work)"),
    ("ig_snapshot_socket", "IG snapshot\nsocket"),
    ("otterize_fresh30", "Otterize\nfresh-30"),
    ("otterize_20day", "Otterize\ncarried-over"),
    ("ig_trace_tcp", "IG trace_tcp"),
]
INK = "#1a1a2e"
ACCENT = "#e94560"
MUTED = "#8d99ae"
GOOD = "#2a9d8f"


def load():
    out = []
    for r in RUNS:
        p = os.path.join(RES, f"{r}_score.json")
        out.append(json.load(open(p)))
    return out


def load_rescore(path=RESCORE):
    """The UNIFORM-rule results of rescore_platform.py.

    Returns the parsed output.json. The figures read
      doc["uniform"]["platform"]["falsedeny"][gen]["per_run"][run] / ["mean"],
      doc["uniform"]["platform"]["security"][gen]["over_privilege"],
      doc["uniform"]["platform"]["fusion"] and doc["uniform"]["sock-shop"]["fusion"].
    Every mean there is the mean of exact fractions over run1 to run3, rounded once."""
    doc = json.load(open(path))
    if doc.get("headline_rule") != "UNIFORM":
        raise ValueError(f"{path}: headline rule is {doc.get('headline_rule')!r}, expected 'UNIFORM'")
    return doc


def fig_reproducibility(rs=None):
    """False-deny per tool across 3 runs (platform, UNIFORM rule): three lines, one per run.

    Runs frequently have identical values (e.g. snapshot_socket is the same in all
    three), so drawn on top of each other the earlier lines vanish. Each run is
    offset horizontally by a small amount so all three are always visible."""
    rs = load_rescore() if rs is None else rs
    fd = rs["uniform"]["platform"]["falsedeny"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    n = len(GENS)
    offsets = [-0.12, 0.0, 0.12]
    styles = [("#1f5fbf", "o", "Run 1"), ("#e07b1a", "s", "Run 2"), ("#2a9d8f", "^", "Run 3")]
    for ri, run in enumerate(RESCORE_RUNS):
        vals = [fd[key]["per_run"][run] for key, _ in GENS]
        xs = [gi + offsets[ri] for gi in range(n)]
        col, mk, lab = styles[ri]
        ax.plot(xs, vals, color=col, marker=mk, markersize=7, markerfacecolor="white",
                markeredgewidth=1.8, lw=1.6, label=lab, zorder=3 + ri)
    for gi, (key, _) in enumerate(GENS):
        vals = [fd[key]["per_run"][run] for run in RESCORE_RUNS]
        mean = fd[key]["mean"]          # mean of exact fractions, rounded once
        ax.annotate(f"{mean:.3f}", (gi, max(vals)), textcoords="offset points",
                    xytext=(0, 12), ha="center", color=INK, fontsize=9, fontweight="bold")
    ax.set_xticks(list(range(n)))
    ax.set_xticklabels([lbl for _, lbl in GENS], fontsize=9)
    ax.set_ylabel("false-deny (legitimate connections denied)")
    ax.set_ylim(0, 1)
    ax.set_xlim(-0.5, n - 0.5)
    ax.legend(frameon=False, fontsize=9, loc="upper left")
    ax.set_title("False-deny across three runs (Ankra platform, |L| = 39)\n"
                 "runs are offset sideways so identical values do not hide each other; label = mean",
                 fontsize=10, color=INK)
    ax.grid(axis="y", color="#eee", zorder=0)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_reproducibility.png"), dpi=150)
    plt.close(fig)


def fig_two_axes(rs=None):
    """Security axis vs deployability axis (platform, UNIFORM rule, mean of three runs)."""
    from matplotlib.patches import Patch
    rs = load_rescore() if rs is None else rs
    plat = rs["uniform"]["platform"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4.9))
    xs = range(len(GENS))
    labels = [lbl for _, lbl in GENS]

    # Plot the two error rates on ONE shared scale. Block-rate is not plotted:
    # it is 1 - over-privilege by definition, so charting both would spend a
    # whole panel restating the same number.
    op = [plat["security"][k]["over_privilege"] for k, _ in GENS]
    fd = [plat["falsedeny"][k]["mean"] for k, _ in GENS]

    for ax, vals, colour, title in (
        (a1, op, GOOD, "Security axis: attacks the policy lets through"),
        (a2, fd, ACCENT, "Deployability axis: legitimate traffic it blocks"),
    ):
        bars = ax.bar(xs, vals, 0.62, color=colour, zorder=3)
        for r, v in zip(bars, vals):
            ax.annotate(f"{v:.3f}", (r.get_x() + r.get_width() / 2, v),
                        textcoords="offset points", xytext=(0, 4), ha="center",
                        fontsize=9, fontweight="bold", color=INK)
        ax.set_title(title, fontsize=10, color=INK)
        ax.set_ylim(0, 1.0)
        ax.set_xticks(list(xs))
        ax.set_xticklabels(labels, fontsize=8)
        # both panels carry the y-axis and the "lower is better" direction
        ax.set_ylabel("fraction of edges  (lower is better)", fontsize=9.5)
        ax.grid(axis="y", color="#eeeeee", zorder=0)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)

    handles = [Patch(facecolor=GOOD, label="over-privilege  (attack edges admitted)"),
               Patch(facecolor=ACCENT, label="false-deny  (legitimate traffic blocked)")]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False,
               fontsize=9, bbox_to_anchor=(0.5, 0.0))

    fig.suptitle("Over-privilege and false-deny on the platform, mean of three runs",
                 fontsize=11.5, color=INK)
    fig.tight_layout(rect=[0, 0.07, 1, 1])
    fig.savefig(os.path.join(HERE, "fig_two_axes.png"), dpi=150)
    plt.close(fig)


def fig_ceiling(rs=None):
    """Coverage by source, per application, under the UNIFORM rule.

    Reads ../results/RESCORE-20261104/output.json: configuration alone and the
    best single observer (per run, mean of run1 to run3) for the platform and
    Sock Shop. The story is the reversal between the two apps, so no number is
    hand-entered."""
    rs = load_rescore() if rs is None else rs
    pf = rs["uniform"]["platform"]["fusion"]
    sf = rs["uniform"]["sock-shop"]["fusion"]

    # platform: configuration recall vs the hand-assembled L, best observer (mean of three runs)
    plat_cfg = pf["config"]["pct"]
    plat_obs = pf["best_observer"]["pct"]

    # sock shop: configuration recall, best observer per run (mean of three runs)
    ss_cfg = sf["config"]["pct"]
    ss_obs = sf["best_observer_per_run"]["pct"]

    # A slope chart: two sources on the x-axis, one line per application. The
    # lines cross, and the crossing IS the finding — whichever source you pick,
    # there is an application where it is the wrong one.
    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    x0, x1 = 0.0, 1.0
    series = [
        ("Platform", plat_cfg, plat_obs, GOOD,
         "declares its dependencies in\nenvironment variables, Ingress, RBAC"),
        ("Sock Shop", ss_cfg, ss_obs, ACCENT,
         "hard-codes its dependencies\nin application source"),
    ]
    # name label position and right-value nudge, per series, chosen so nothing
    # collides: the two right-hand endpoints sit only 3 points apart.
    place = {"Platform": ((10, 20), "left", 10), "Sock Shop": ((14, -62), "left", -8)}
    for name, cfg, obs, col, sub in series:
        ax.plot([x0, x1], [cfg, obs], color=col, lw=2.6, zorder=3,
                marker="o", markersize=10, markerfacecolor="white",
                markeredgewidth=2.6, markeredgecolor=col)
        ax.annotate(f"{cfg:.1f}%", (x0, cfg), textcoords="offset points",
                    xytext=(-14, -4), ha="right", fontsize=11,
                    fontweight="bold", color=col)
        (nx, ny), nha, dy = place[name]
        ax.annotate(f"{obs:.1f}%", (x1, obs), textcoords="offset points",
                    xytext=(14, dy), ha="left", fontsize=11,
                    fontweight="bold", color=col)
        anchor = (x0, cfg) if name == "Platform" else (x1, obs)
        ax.annotate(f"{name}\n{sub}", anchor, textcoords="offset points",
                    xytext=(nx, ny), ha=nha, fontsize=8.5, color=col,
                    linespacing=1.4)

    ax.set_xlim(-0.28, 1.62)
    ax.set_ylim(-6, 116)
    ax.set_xticks([x0, x1])
    ax.set_xticklabels(["configuration alone\n(declared edges)",
                        "observation alone\n(best of five observers)"], fontsize=10)
    ax.set_ylabel("legitimate connections recovered (%)")
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_title("Coverage of the reference set by source", fontsize=10.5, color=INK)
    ax.grid(axis="y", color="#eeeeee", zorder=0)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "fig_ceiling.png"), dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    rs = load_rescore()
    fig_reproducibility(rs)
    fig_two_axes(rs)
    fig_ceiling(rs)
    print("wrote fig_reproducibility.png, fig_two_axes.png, fig_ceiling.png")
