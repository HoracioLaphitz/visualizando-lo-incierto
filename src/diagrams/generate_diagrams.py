"""Generate baseline and Gestalt-optimized diagram stimuli for Condition B.

Reads `data/questions.json` and produces two PNG files per question:
    assets/diagrams/{id}_baseline.png   - plain, conventional textbook diagram
    assets/diagrams/{id}_optimized.png  - Gestalt-optimized diagram

Design rationale lives in `docs/03_sistema_diseno.md`. In short:
    - baseline:  grayscale, thin uniform strokes, no color coding, no filled
                 intersections, straight/elbow connectors -> "how a textbook
                 would lazily draw it".
    - optimized: color coding per event (ley de semejanza), filled
                 intersection regions (ley de cierre), smooth continuous
                 branches with width encoding magnitude (ley de buena
                 continuidad + jerarquia visual), direct labeling of
                 probabilities.

All numeric values displayed come exclusively from each question's
`diagram_spec` -- nothing is hardcoded per question. Run as:
    python src/diagrams/generate_diagrams.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from matplotlib_venn import venn2

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_PATH = PROJECT_ROOT / "data" / "questions.json"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "diagrams"

# --------------------------------------------------------------------------
# Canvas
# --------------------------------------------------------------------------
FIG_SIZE = (8.0, 6.0)  # inches -> with DPI=150 approx 1200x900 px
DPI = 150

# --------------------------------------------------------------------------
# Palette -- colorblind-safe subset of the Okabe-Ito palette.
# See docs/03_sistema_diseno.md for the accessibility justification.
# --------------------------------------------------------------------------
COLOR_A = "#0072B2"            # blue        - Event A / first branch
COLOR_B = "#D55E00"            # vermillion  - Event B / second branch
COLOR_INTERSECTION = "#6B3FA0"  # violet      - A ∩ B (perceptual blend of A+B)
COLOR_TARGET = "#009E73"       # bluish green - highlighted "target" leaf path
COLOR_MUTED = "#B0B0B0"        # gray        - non-target leaf path
COLOR_TEXT_DARK = "#1A1A1A"
COLOR_BASELINE = "#000000"     # baseline strokes/text: plain black
COLOR_BASELINE_FILL = "#FFFFFF"

# --------------------------------------------------------------------------
# Label vocabulary -- maps the (limited, known) set of diagram_spec key
# tokens to short human-readable labels. This only affects *text formatting*
# of labels; every numeric value still comes from diagram_spec.
# --------------------------------------------------------------------------
TOKEN_LABELS = {
    "a": "A",
    "b": "B",
    "not_a": "¬A",
    "nota": "¬A",
    "not_b": "¬B",
    "notb": "¬B",
    "enfermedad": "Enf.",
    "sano": "Sano",
    "pos": "Pos.",
    "neg": "Neg.",
}


def humanize_token(token: str) -> str:
    """Translate a diagram_spec key fragment into a short display label."""
    return TOKEN_LABELS.get(token, token.replace("_", " ").capitalize())


def root_child_label(key: str) -> str:
    """Label for a root-level branch, e.g. 'p_not_a' -> '¬A'."""
    body = key[2:] if key.startswith("p_") else key
    return humanize_token(body)


def leaf_child_label(key: str) -> str:
    """Label for a second-level branch, e.g. 'p_notb_given_a' -> '¬B'."""
    body = key[2:] if key.startswith("p_") else key
    child_token = body.split("_given_")[0]
    return humanize_token(child_token)


# --------------------------------------------------------------------------
# Figure helpers
# --------------------------------------------------------------------------
def new_figure() -> tuple[plt.Figure, plt.Axes]:
    fig, ax = plt.subplots(figsize=FIG_SIZE, dpi=DPI)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")
    return fig, ax


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=DPI, facecolor="white", bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)


# --------------------------------------------------------------------------
# Venn: single circle + complement (q03-style spec)
# --------------------------------------------------------------------------
def draw_complement_venn(spec: dict[str, Any], optimized: bool) -> plt.Figure:
    fig, ax = new_figure()
    # Square canvas: a circle inscribed in a square covers up to pi/4 (~0.785)
    # of its area, so any p_a below that threshold fits with visible margin.
    # (A wide rectangle would force the circle to overflow vertically for
    # p_a values above ~H/W * pi/4.)
    width, height = 9.0, 9.0
    p_a = spec["set_a"]
    p_complement = spec["complement"]

    rect_lw = 2.0 if optimized else 1.0
    ax.add_patch(
        Rectangle((0, 0), width, height, fill=False, edgecolor=COLOR_BASELINE, linewidth=rect_lw)
    )

    area_total = width * height
    radius = math.sqrt((p_a * area_total) / math.pi)
    cx, cy = width / 2, height / 2

    if optimized:
        face, alpha, edge_lw = COLOR_A, 0.55, 2.2
        inside_style = dict(fontsize=20, fontweight="bold", color="white", ha="center", va="center")
        outside_style = dict(fontsize=15, fontweight="bold", color=COLOR_TEXT_DARK, ha="left", va="top")
    else:
        face, alpha, edge_lw = COLOR_BASELINE_FILL, 1.0, 1.0
        inside_style = dict(fontsize=14, color="black", ha="center", va="center")
        outside_style = dict(fontsize=13, color="black", ha="left", va="top")

    ax.add_patch(
        Circle((cx, cy), radius, facecolor=face, edgecolor=COLOR_BASELINE, linewidth=edge_lw, alpha=alpha)
    )
    ax.text(cx, cy, f"A\nP(A) = {p_a:.2f}", **inside_style)
    ax.text(0.3, height - 0.3, f"¬A\nP(¬A) = {p_complement:.2f}", **outside_style)

    ax.set_xlim(-0.5, width + 0.5)
    ax.set_ylim(-0.5, height + 0.5)
    ax.set_aspect("equal")
    return fig


# --------------------------------------------------------------------------
# Venn: two circles (q01, q02, q04-style spec)
# --------------------------------------------------------------------------
def draw_two_set_venn(spec: dict[str, Any], optimized: bool) -> plt.Figure:
    fig, ax = new_figure()
    a_only = spec["set_a_only"]
    b_only = spec["set_b_only"]
    inter = spec["intersection"]
    outside = spec.get("outside")

    v = venn2(subsets=(a_only, b_only, inter), set_labels=("A", "B"), ax=ax)

    region_values = {"10": a_only, "01": b_only, "11": inter}
    region_colors = {"10": COLOR_A, "01": COLOR_B, "11": COLOR_INTERSECTION}

    for region_id, value in region_values.items():
        patch = v.get_patch_by_id(region_id)
        if patch is not None:
            if optimized:
                patch.set_facecolor(region_colors[region_id])
                patch.set_alpha(0.9 if region_id == "11" else 0.55)
                patch.set_edgecolor("black")
                patch.set_linewidth(1.5)
            else:
                patch.set_facecolor(COLOR_BASELINE_FILL)
                patch.set_alpha(1.0)
                patch.set_edgecolor("black")
                patch.set_linewidth(1.0)

        label = v.get_label_by_id(region_id)
        if label is not None:
            label.set_text(f"{value:.2f}")
            if optimized:
                label.set_fontsize(18 if region_id == "11" else 15)
                label.set_fontweight("bold")
                label.set_color("white" if region_id == "11" else "white")
            else:
                label.set_fontsize(13)
                label.set_fontweight("normal")
                label.set_color("black")

    for set_label in v.set_labels or []:
        if set_label is None:
            continue
        if optimized:
            set_label.set_fontsize(16)
            set_label.set_fontweight("bold")
        else:
            set_label.set_fontsize(13)

    # sample-space rectangle around the venn layout
    xlim, ylim = ax.get_xlim(), ax.get_ylim()
    pad_x = (xlim[1] - xlim[0]) * 0.15
    pad_y = (ylim[1] - ylim[0]) * 0.20
    rx0, rx1 = xlim[0] - pad_x, xlim[1] + pad_x
    ry0, ry1 = ylim[0] - pad_y, ylim[1] + pad_y
    ax.add_patch(
        Rectangle(
            (rx0, ry0), rx1 - rx0, ry1 - ry0, fill=False,
            edgecolor="black", linewidth=1.5 if optimized else 1.0, zorder=0,
        )
    )
    ax.set_xlim(rx0, rx1)
    ax.set_ylim(ry0, ry1)

    if outside is not None:
        style = dict(fontsize=13, ha="left", va="top", color="black")
        if optimized:
            style.update(fontsize=14, fontweight="bold", color=COLOR_TEXT_DARK)
        ax.text(rx0 + 0.04 * (rx1 - rx0), ry1 - 0.04 * (ry1 - ry0), f"fuera = {outside:.2f}", **style)

    ax.set_aspect("equal")
    return fig


# --------------------------------------------------------------------------
# Tree: two-level probability tree (q05-q10-style spec)
# --------------------------------------------------------------------------
def draw_tree(spec: dict[str, Any], optimized: bool) -> plt.Figure:
    fig, ax = new_figure()

    root_items = list(spec["root"].items())
    branch_keys = [k for k in spec if k.startswith("branch_")]
    b0_items = list(spec[branch_keys[0]].items())
    b1_items = list(spec[branch_keys[1]].items())

    root_pos = (0.5, 4.0)
    l1_top, l1_bot = (5.2, 6.6), (5.2, 1.4)
    leaves = {
        "tt": (11.0, 7.8),
        "tb": (11.0, 5.4),
        "bt": (11.0, 2.6),
        "bb": (11.0, 0.2),
    }

    root_label_top = root_child_label(root_items[0][0])
    root_label_bot = root_child_label(root_items[1][0])
    p_top, p_bot = root_items[0][1], root_items[1][1]

    leaf_label_tt, p_tt = leaf_child_label(b0_items[0][0]), b0_items[0][1]
    leaf_label_tb, p_tb = leaf_child_label(b0_items[1][0]), b0_items[1][1]
    leaf_label_bt, p_bt = leaf_child_label(b1_items[0][0]), b1_items[0][1]
    leaf_label_bb, p_bb = leaf_child_label(b1_items[1][0]), b1_items[1][1]

    joint_tt = p_top * p_tt
    joint_tb = p_top * p_tb
    joint_bt = p_bot * p_bt
    joint_bb = p_bot * p_bb

    def draw_edge(p0, p1, width, color, curved):
        if curved:
            arrow = FancyArrowPatch(
                p0, p1, connectionstyle="arc3,rad=0.12", arrowstyle="-",
                linewidth=width, color=color, shrinkA=0, shrinkB=0, capstyle="round",
            )
            ax.add_patch(arrow)
        else:
            midx = (p0[0] + p1[0]) / 2
            ax.plot(
                [p0[0], midx, midx, p1[0]], [p0[1], p0[1], p1[1], p1[1]],
                color=color, linewidth=width, solid_capstyle="round",
            )

    def draw_node(pos, radius, face, edge):
        ax.add_patch(Circle(pos, radius, facecolor=face, edgecolor=edge, linewidth=1.5, zorder=3))

    if optimized:
        lw_scale, base_lw = 8.0, 1.5
        draw_edge(root_pos, l1_top, base_lw + lw_scale * p_top, COLOR_A, curved=True)
        draw_edge(root_pos, l1_bot, base_lw + lw_scale * p_bot, COLOR_B, curved=True)
        draw_edge(l1_top, leaves["tt"], base_lw + lw_scale * joint_tt, COLOR_TARGET, curved=True)
        draw_edge(l1_top, leaves["tb"], base_lw + lw_scale * joint_tb, COLOR_MUTED, curved=True)
        draw_edge(l1_bot, leaves["bt"], base_lw + lw_scale * joint_bt, COLOR_TARGET, curved=True)
        draw_edge(l1_bot, leaves["bb"], base_lw + lw_scale * joint_bb, COLOR_MUTED, curved=True)

        draw_node(root_pos, 0.28, COLOR_TEXT_DARK, "black")
        draw_node(l1_top, 0.24, COLOR_A, "black")
        draw_node(l1_bot, 0.24, COLOR_B, "black")
        for key, color in (("tt", COLOR_TARGET), ("tb", COLOR_MUTED), ("bt", COLOR_TARGET), ("bb", COLOR_MUTED)):
            draw_node(leaves[key], 0.18, color, "black")

        branch_label_style = dict(fontsize=13, fontweight="bold", color=COLOR_TEXT_DARK, ha="center")
        leaf_label_style = dict(fontsize=12, fontweight="bold", color=COLOR_TEXT_DARK, ha="left", va="center")
        joint_label_style = dict(fontsize=12, fontweight="bold", color=COLOR_TEXT_DARK, ha="left", va="center")
    else:
        uniform_lw = 1.2
        for p0, p1 in (
            (root_pos, l1_top), (root_pos, l1_bot),
            (l1_top, leaves["tt"]), (l1_top, leaves["tb"]),
            (l1_bot, leaves["bt"]), (l1_bot, leaves["bb"]),
        ):
            draw_edge(p0, p1, uniform_lw, COLOR_BASELINE, curved=False)

        draw_node(root_pos, 0.12, "white", "black")
        draw_node(l1_top, 0.12, "white", "black")
        draw_node(l1_bot, 0.12, "white", "black")
        for key in ("tt", "tb", "bt", "bb"):
            draw_node(leaves[key], 0.10, "white", "black")

        branch_label_style = dict(fontsize=12, fontweight="normal", color="black", ha="center")
        leaf_label_style = dict(fontsize=11, fontweight="normal", color="black", ha="left", va="center")
        joint_label_style = dict(fontsize=11, fontweight="normal", color="black", ha="left", va="center")

    # root-level branch labels (name + probability), placed at ~40% of the edge
    def mid(p0, p1, frac=0.42):
        return (p0[0] + (p1[0] - p0[0]) * frac, p0[1] + (p1[1] - p0[1]) * frac)

    mt = mid(root_pos, l1_top)
    mb = mid(root_pos, l1_bot)
    ax.text(mt[0], mt[1] + 0.35, f"{root_label_top}\nP={p_top:.2f}", **branch_label_style)
    ax.text(mb[0], mb[1] - 0.35, f"{root_label_bot}\nP={p_bot:.2f}", **branch_label_style)

    # second-level branch labels; offset away from the sibling edge so the
    # "up" branch label sits above its line and the "down" branch label
    # sits below its line (they never point toward each other).
    for (p0, p1), lbl, p_val in (
        ((l1_top, leaves["tt"]), leaf_label_tt, p_tt),
        ((l1_top, leaves["tb"]), leaf_label_tb, p_tb),
        ((l1_bot, leaves["bt"]), leaf_label_bt, p_bt),
        ((l1_bot, leaves["bb"]), leaf_label_bb, p_bb),
    ):
        m = mid(p0, p1, frac=0.38)
        vertical_sign = 1.0 if p1[1] >= p0[1] else -1.0
        ax.text(m[0], m[1] + vertical_sign * 0.30, f"{lbl} | P={p_val:.2f}", **leaf_label_style)

    # leaf joint-probability labels
    for key, lbl_top, lbl_bot, joint in (
        ("tt", root_label_top, leaf_label_tt, joint_tt),
        ("tb", root_label_top, leaf_label_tb, joint_tb),
        ("bt", root_label_bot, leaf_label_bt, joint_bt),
        ("bb", root_label_bot, leaf_label_bb, joint_bb),
    ):
        lx, ly = leaves[key]
        ax.text(lx + 0.35, ly, f"P({lbl_top}∩{lbl_bot}) = {joint:.3f}", **joint_label_style)

    ax.set_xlim(-0.5, 15.0)
    ax.set_ylim(-0.6, 8.6)
    ax.set_aspect("equal")
    return fig


# --------------------------------------------------------------------------
# Dispatch
# --------------------------------------------------------------------------
def build_figure(question: dict[str, Any], optimized: bool) -> plt.Figure:
    diagram_type = question["diagram_type"]
    spec = question["diagram_spec"]

    if diagram_type == "venn":
        if "set_a" in spec and "complement" in spec:
            return draw_complement_venn(spec, optimized)
        return draw_two_set_venn(spec, optimized)

    if diagram_type == "tree":
        return draw_tree(spec, optimized)

    raise ValueError(f"Unknown diagram_type: {diagram_type!r}")


def main() -> None:
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    questions = data["questions"]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    for question in questions:
        qid = question["id"]
        for variant, optimized in (("baseline", False), ("optimized", True)):
            fig = build_figure(question, optimized)
            out_path = OUTPUT_DIR / f"{qid}_{variant}.png"
            save_figure(fig, out_path)
            generated.append(out_path)

    print(f"Generated {len(generated)} PNG files in {OUTPUT_DIR}")
    for path in generated:
        print(f"  - {path.name}")


if __name__ == "__main__":
    main()
