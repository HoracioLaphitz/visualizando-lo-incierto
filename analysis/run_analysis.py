"""Statistical analysis pipeline for the "Visualizando lo Incierto" experiment.

Reads export_clean.csv (see src/data/export.py for the column contract),
aggregates to the participant level (mean latency and accuracy rate per
condition, per participant -- the correct unit of analysis for the paired
t-test, since raw trial-level rows are not independent observations), and
runs the analyses specified in lineamiento_del_proyecto.md (DTR sections 6-7):

- Descriptive statistics per condition (latency, accuracy).
- Paired-samples t-test (scipy.stats.ttest_rel), condition A vs B, for both
  latency and accuracy, with Cohen's d for paired samples and a 95% CI of
  the mean difference.
- Shapiro-Wilk normality check on the difference scores; if violated
  (p < .05), a Wilcoxon signed-rank test is also reported as a robustness
  check.
- Per-question breakdown (accuracy, median latency, per condition) to spot
  which diagrams helped or hurt comprehension.
- Order-effect / counterbalancing check: independent-samples t-test
  comparing the A-first vs B-first groups on the within-subject A-B
  difference.

All console/report text is in Spanish (research artifact for a
Spanish-speaking audience); code, comments, and identifiers are in English.

Usage:
    python analysis/run_analysis.py [--input data/results/export_clean.csv] [--outdir analysis/output]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "data" / "results" / "export_clean.csv"
DEFAULT_OUTDIR = REPO_ROOT / "analysis" / "output"

ALPHA = 0.05
MIN_N_FOR_INFERENCE = 5

# Contract columns, per src/data/export.py module docstring.
REQUIRED_COLUMNS = [
    "participant_id",
    "question_id",
    "condition",
    "block",
    "correct",
    "latency_seconds",
]

COLOR_A = "#0072B2"  # condition A / formula
COLOR_B = "#D55E00"  # condition B / diagram


# ---------------------------------------------------------------------------
# Data loading and contract checks
# ---------------------------------------------------------------------------


def load_data(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """Load export_clean.csv and check it against the documented column contract.

    Returns (dataframe, list_of_contract_warnings). Does not raise on
    contract deviations -- callers decide how to proceed, and deviations are
    surfaced in the final report.
    """
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    df = pd.read_csv(path)
    warnings: list[str] = []

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"export_clean.csv is missing required columns: {missing}. "
            "See src/data/export.py for the expected contract."
        )

    if df.empty:
        warnings.append("El archivo de entrada no contiene filas.")
        return df, warnings

    valid_conditions = {"A", "B"}
    seen_conditions = set(df["condition"].dropna().unique())
    unexpected = seen_conditions - valid_conditions
    if unexpected:
        warnings.append(
            f"Valores inesperados en 'condition' (se esperaba 'A'/'B'): {sorted(unexpected)}. "
            "Nota: docs/02b_operacionalizacion.md documenta la variable como "
            "'formula'/'diagrama', pero src/data/export.py (el contrato real de "
            "export_clean.csv) usa 'A'/'B'. Este script sigue el contrato de export.py."
        )

    if df["latency_seconds"].isna().any():
        warnings.append("Hay valores nulos en 'latency_seconds'; se excluyen de los calculos de latencia.")

    if df["correct"].isna().any():
        warnings.append("Hay valores nulos en 'correct'; se excluyen de los calculos de exactitud.")

    out_of_range = df[(df["latency_seconds"] < 2) | (df["latency_seconds"] > 300)]
    if not out_of_range.empty:
        warnings.append(
            f"{len(out_of_range)} filas con 'latency_seconds' fuera del rango valido [2, 300] "
            "segun docs/02b_operacionalizacion.md, a pesar de que export_clean.csv deberia "
            "tener el filtro ya aplicado (ver src/data/export.py, apply_exclusions)."
        )

    return df, warnings


def derive_order_block(df: pd.DataFrame) -> pd.Series:
    """Derive orden_bloque (A_primero / B_primero) per participant from block 1's condition.

    docs/02b_operacionalizacion.md documents 'orden_bloque' as a column that
    should exist alongside the data, but it is NOT part of the export.py
    column contract. We derive it directly from the observed data (which
    condition appears in block == 1 for each participant) rather than
    trusting participant_id parity, since the data itself is the ground
    truth of what the participant actually saw.
    """
    block1 = df[df["block"] == 1]
    first_condition = block1.groupby("participant_id")["condition"].agg(lambda s: s.mode().iat[0] if not s.mode().empty else None)
    order = first_condition.map({"A": "A_primero", "B": "B_primero"})
    order.name = "orden_bloque"
    return order


# ---------------------------------------------------------------------------
# Participant-level aggregation (the correct unit of analysis for the paired t-test)
# ---------------------------------------------------------------------------


def build_participant_aggregates(df: pd.DataFrame, contract_warnings: list[str]) -> pd.DataFrame:
    """Aggregate trial-level rows to one row per participant, with mean latency
    and accuracy rate per condition (A and B).

    Participants missing one of the two conditions are dropped (a paired
    design requires both conditions per participant); this is reported as a
    warning, not silently discarded.
    """
    valid = df[df["condition"].isin(["A", "B"])].copy()
    valid = valid.dropna(subset=["latency_seconds", "correct"])

    agg = (
        valid.groupby(["participant_id", "condition"])
        .agg(mean_latency=("latency_seconds", "mean"), accuracy=("correct", "mean"), n_trials=("correct", "size"))
        .unstack("condition")
    )

    # Flatten the MultiIndex columns: (mean_latency, A) -> latency_A, etc.
    agg.columns = [f"{metric}_{cond}" for metric, cond in agg.columns]

    required_cols = ["mean_latency_A", "mean_latency_B", "accuracy_A", "accuracy_B"]
    missing_cols = [c for c in required_cols if c not in agg.columns]
    if missing_cols:
        contract_warnings.append(
            f"No hay datos suficientes para construir columnas {missing_cols}: "
            "falta la condicion A o B por completo en el dataset."
        )
        for c in missing_cols:
            agg[c] = np.nan

    incomplete_mask = agg[required_cols].isna().any(axis=1)
    n_incomplete = int(incomplete_mask.sum())
    if n_incomplete:
        contract_warnings.append(
            f"{n_incomplete} participante(s) excluido(s) del analisis pareado por no tener "
            f"datos completos en ambas condiciones: {sorted(agg.index[incomplete_mask].tolist())}."
        )

    agg = agg.loc[~incomplete_mask].copy()
    agg = agg.rename(
        columns={
            "mean_latency_A": "latency_A",
            "mean_latency_B": "latency_B",
        }
    )

    order = derive_order_block(df)
    agg = agg.join(order, how="left")

    agg["diff_latency"] = agg["latency_A"] - agg["latency_B"]
    agg["diff_accuracy"] = agg["accuracy_A"] - agg["accuracy_B"]

    return agg.reset_index()


# ---------------------------------------------------------------------------
# Descriptive statistics
# ---------------------------------------------------------------------------


def describe_metric(series: pd.Series) -> dict:
    series = series.dropna()
    return {
        "n": int(series.shape[0]),
        "mean": float(series.mean()) if series.shape[0] else float("nan"),
        "sd": float(series.std(ddof=1)) if series.shape[0] > 1 else float("nan"),
        "median": float(series.median()) if series.shape[0] else float("nan"),
    }


def compute_descriptives(agg: pd.DataFrame) -> dict:
    return {
        "latency_A": describe_metric(agg["latency_A"]),
        "latency_B": describe_metric(agg["latency_B"]),
        "accuracy_A": describe_metric(agg["accuracy_A"]),
        "accuracy_B": describe_metric(agg["accuracy_B"]),
    }


# ---------------------------------------------------------------------------
# Inferential statistics
# ---------------------------------------------------------------------------


def paired_test_with_ci(x: pd.Series, y: pd.Series, alpha: float = ALPHA) -> dict:
    """Paired t-test of x vs y (x - y), with Cohen's dz and a 95% CI of the mean difference.

    Also runs Shapiro-Wilk on the difference scores; if normality is
    violated (p < alpha), also runs Wilcoxon signed-rank as a robustness
    check.
    """
    diff = (x - y).dropna()
    n = diff.shape[0]

    t_stat, p_value = stats.ttest_rel(x, y, nan_policy="omit")
    df_ = n - 1
    mean_diff = float(diff.mean())
    sd_diff = float(diff.std(ddof=1))
    se_diff = sd_diff / np.sqrt(n)
    t_crit = stats.t.ppf(1 - alpha / 2, df_)
    ci_low = mean_diff - t_crit * se_diff
    ci_high = mean_diff + t_crit * se_diff
    cohens_dz = mean_diff / sd_diff if sd_diff > 0 else float("nan")

    result = {
        "n": n,
        "t": float(t_stat),
        "df": df_,
        "p": float(p_value),
        "mean_diff": mean_diff,
        "sd_diff": sd_diff,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "cohens_dz": cohens_dz,
        "shapiro_w": None,
        "shapiro_p": None,
        "normality_violated": None,
        "wilcoxon_w": None,
        "wilcoxon_p": None,
    }

    if n >= 3:
        shapiro_w, shapiro_p = stats.shapiro(diff)
        result["shapiro_w"] = float(shapiro_w)
        result["shapiro_p"] = float(shapiro_p)
        result["normality_violated"] = bool(shapiro_p < alpha)

        if result["normality_violated"]:
            try:
                wilcoxon_w, wilcoxon_p = stats.wilcoxon(diff)
                result["wilcoxon_w"] = float(wilcoxon_w)
                result["wilcoxon_p"] = float(wilcoxon_p)
            except ValueError as exc:
                # e.g. all differences are zero
                logger.warning("No se pudo calcular Wilcoxon: %s", exc)

    return result


def order_effect_check(agg: pd.DataFrame, diff_col: str, alpha: float = ALPHA) -> dict | None:
    """Independent-samples t-test comparing A-first vs B-first groups on a
    within-subject difference (diff_latency or diff_accuracy), to validate
    that counterbalancing neutralized order/learning effects.
    """
    groups = agg.dropna(subset=[diff_col, "orden_bloque"])
    a_first = groups.loc[groups["orden_bloque"] == "A_primero", diff_col]
    b_first = groups.loc[groups["orden_bloque"] == "B_primero", diff_col]

    if a_first.shape[0] < 2 or b_first.shape[0] < 2:
        return None

    t_stat, p_value = stats.ttest_ind(a_first, b_first, equal_var=False, nan_policy="omit")
    return {
        "n_a_first": int(a_first.shape[0]),
        "n_b_first": int(b_first.shape[0]),
        "mean_a_first": float(a_first.mean()),
        "mean_b_first": float(b_first.mean()),
        "t": float(t_stat),
        "p": float(p_value),
    }


# ---------------------------------------------------------------------------
# Per-question breakdown
# ---------------------------------------------------------------------------


def per_question_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    valid = df[df["condition"].isin(["A", "B"])].dropna(subset=["latency_seconds", "correct"])
    breakdown = (
        valid.groupby(["question_id", "condition"])
        .agg(accuracy=("correct", "mean"), median_latency=("latency_seconds", "median"), n=("correct", "size"))
        .reset_index()
    )
    pivot = breakdown.pivot(index="question_id", columns="condition", values=["accuracy", "median_latency", "n"])
    pivot.columns = [f"{metric}_{cond}" for metric, cond in pivot.columns]
    pivot = pivot.reset_index().sort_values("question_id")
    if "accuracy_A" in pivot.columns and "accuracy_B" in pivot.columns:
        pivot["accuracy_diff_B_minus_A"] = pivot["accuracy_B"] - pivot["accuracy_A"]
    if "median_latency_A" in pivot.columns and "median_latency_B" in pivot.columns:
        pivot["latency_diff_B_minus_A"] = pivot["median_latency_B"] - pivot["median_latency_A"]
    return pivot


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------


def plot_boxplots(agg: pd.DataFrame, outdir: Path) -> list[Path]:
    paths = []

    fig, ax = plt.subplots(figsize=(5, 5))
    data = [agg["latency_A"].dropna(), agg["latency_B"].dropna()]
    bp = ax.boxplot(data, labels=["A (formula)", "B (diagrama)"], patch_artist=True)
    for patch, color in zip(bp["boxes"], [COLOR_A, COLOR_B]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_ylabel("Latencia media por participante (segundos)")
    ax.set_title("Latencia por condicion")
    fig.tight_layout()
    path = outdir / "boxplot_latencia.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(path)

    fig, ax = plt.subplots(figsize=(5, 5))
    data = [agg["accuracy_A"].dropna(), agg["accuracy_B"].dropna()]
    bp = ax.boxplot(data, labels=["A (formula)", "B (diagrama)"], patch_artist=True)
    for patch, color in zip(bp["boxes"], [COLOR_A, COLOR_B]):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.set_ylabel("Tasa de exactitud por participante")
    ax.set_title("Exactitud por condicion")
    fig.tight_layout()
    path = outdir / "boxplot_exactitud.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    paths.append(path)

    return paths


def plot_per_question(breakdown: pd.DataFrame, outdir: Path) -> Path | None:
    if "accuracy_A" not in breakdown.columns or "accuracy_B" not in breakdown.columns:
        return None

    fig, axes = plt.subplots(2, 1, figsize=(8, 8), sharex=True)

    x = np.arange(len(breakdown))
    axes[0].scatter(x, breakdown["accuracy_A"], color=COLOR_A, label="A (formula)", zorder=3)
    axes[0].scatter(x, breakdown["accuracy_B"], color=COLOR_B, label="B (diagrama)", zorder=3)
    for xi, row in zip(x, breakdown.itertuples()):
        axes[0].plot([xi, xi], [row.accuracy_A, row.accuracy_B], color="gray", alpha=0.4, zorder=1)
    axes[0].set_ylabel("Exactitud")
    axes[0].set_title("Exactitud por pregunta y condicion")
    axes[0].legend()
    axes[0].set_ylim(-0.05, 1.05)

    if "median_latency_A" in breakdown.columns and "median_latency_B" in breakdown.columns:
        axes[1].scatter(x, breakdown["median_latency_A"], color=COLOR_A, label="A (formula)", zorder=3)
        axes[1].scatter(x, breakdown["median_latency_B"], color=COLOR_B, label="B (diagrama)", zorder=3)
        for xi, row in zip(x, breakdown.itertuples()):
            axes[1].plot([xi, xi], [row.median_latency_A, row.median_latency_B], color="gray", alpha=0.4, zorder=1)
        axes[1].set_ylabel("Latencia mediana (s)")
        axes[1].set_title("Latencia mediana por pregunta y condicion")

    axes[1].set_xticks(x)
    axes[1].set_xticklabels(breakdown["question_id"], rotation=45, ha="right")
    fig.tight_layout()
    path = outdir / "dotplot_por_pregunta.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Report rendering (Spanish)
# ---------------------------------------------------------------------------


def fmt(value, decimals=3) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/D"
    return f"{value:.{decimals}f}"


def render_report(
    *,
    is_synthetic: bool,
    n_raw_rows: int,
    n_participants_total: int,
    n_participants_analyzed: int,
    contract_warnings: list[str],
    descriptives: dict,
    latency_test: dict | None,
    accuracy_test: dict | None,
    order_latency: dict | None,
    order_accuracy: dict | None,
    breakdown: pd.DataFrame,
    figure_paths: dict[str, Path],
    outdir: Path,
) -> str:
    lines: list[str] = []

    if is_synthetic:
        lines.append("# DATOS SINTETICOS DE VALIDACION -- Reporte de Analisis")
        lines.append("")
        lines.append(
            "**ADVERTENCIA: este reporte fue generado con `analysis/generate_synthetic.py` "
            "sobre datos SINTETICOS, no con datos reales del experimento.** Su unico proposito "
            "es validar que el pipeline de analisis funciona de punta a punta y detecta un "
            "efecto plantado conocido (condicion B mas rapida y mas exacta que condicion A; "
            "ver `analysis/generate_synthetic.py` para los valores exactos)."
        )
    else:
        lines.append("# Reporte de Analisis -- Visualizando lo Incierto")

    lines.append("")
    lines.append(f"Filas leidas: {n_raw_rows}. Participantes con datos: {n_participants_total}. "
                 f"Participantes incluidos en el analisis pareado (ambas condiciones completas): {n_participants_analyzed}.")
    lines.append("")
    lines.append(
        "**Regla de interpretacion:** se usa alfa = 0.05, dos colas, en todas las pruebas de hipotesis."
    )
    lines.append("")

    if contract_warnings:
        lines.append("## Advertencias sobre el contrato de datos")
        lines.append("")
        for w in contract_warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("## Estadistica descriptiva (nivel participante, n = medias por condicion)")
    lines.append("")
    lines.append("| Metrica | Condicion | n | Media | DE | Mediana |")
    lines.append("|---|---|---|---|---|---|")
    lines.append(
        f"| Latencia (s) | A (formula) | {descriptives['latency_A']['n']} | "
        f"{fmt(descriptives['latency_A']['mean'])} | {fmt(descriptives['latency_A']['sd'])} | "
        f"{fmt(descriptives['latency_A']['median'])} |"
    )
    lines.append(
        f"| Latencia (s) | B (diagrama) | {descriptives['latency_B']['n']} | "
        f"{fmt(descriptives['latency_B']['mean'])} | {fmt(descriptives['latency_B']['sd'])} | "
        f"{fmt(descriptives['latency_B']['median'])} |"
    )
    lines.append(
        f"| Exactitud | A (formula) | {descriptives['accuracy_A']['n']} | "
        f"{fmt(descriptives['accuracy_A']['mean'])} | {fmt(descriptives['accuracy_A']['sd'])} | "
        f"{fmt(descriptives['accuracy_A']['median'])} |"
    )
    lines.append(
        f"| Exactitud | B (diagrama) | {descriptives['accuracy_B']['n']} | "
        f"{fmt(descriptives['accuracy_B']['mean'])} | {fmt(descriptives['accuracy_B']['sd'])} | "
        f"{fmt(descriptives['accuracy_B']['median'])} |"
    )
    lines.append("")

    if n_participants_analyzed < MIN_N_FOR_INFERENCE:
        lines.append(
            f"## Estadistica inferencial: OMITIDA\n\n"
            f"Solo hay {n_participants_analyzed} participante(s) con datos completos en ambas "
            f"condiciones (minimo requerido: {MIN_N_FOR_INFERENCE}). Con una muestra tan chica, "
            "un t-test pareado no tiene sentido interpretativo (poder estadistico virtualmente nulo "
            "y alta sensibilidad a outliers). Se reportan unicamente los descriptivos de arriba."
        )
        lines.append("")
    else:
        lines.append("## Prueba T pareada -- Latencia (H2: latencia_B < latencia_A)")
        lines.append("")
        lines.append(_render_ttest_block(latency_test, "latencia_seg"))
        lines.append("")

        lines.append("## Prueba T pareada -- Exactitud (H2: exactitud_B > exactitud_A)")
        lines.append("")
        lines.append(_render_ttest_block(accuracy_test, "tasa de exactitud"))
        lines.append("")

        lines.append("## Chequeo de efecto de orden (validacion del contrabalanceo)")
        lines.append("")
        lines.append(_render_order_block(order_latency, "diferencia de latencia (A - B)"))
        lines.append("")
        lines.append(_render_order_block(order_accuracy, "diferencia de exactitud (A - B)"))
        lines.append("")

    lines.append("## Desglose por pregunta (accion: identificar diagramas que ayudaron o perjudicaron)")
    lines.append("")
    if breakdown.empty:
        lines.append("No hay datos suficientes para el desglose por pregunta.")
    else:
        cols = ["question_id"]
        header = ["Pregunta"]
        if "accuracy_A" in breakdown.columns:
            cols += ["accuracy_A", "accuracy_B", "accuracy_diff_B_minus_A"]
            header += ["Exactitud A", "Exactitud B", "Diff (B-A)"]
        if "median_latency_A" in breakdown.columns:
            cols += ["median_latency_A", "median_latency_B", "latency_diff_B_minus_A"]
            header += ["Latencia mediana A (s)", "Latencia mediana B (s)", "Diff (B-A)"]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "---|" * len(header))
        for row in breakdown.itertuples(index=False):
            values = []
            for c in cols:
                v = getattr(row, c)
                if c == "question_id":
                    values.append(str(v))
                else:
                    values.append(fmt(v))
            lines.append("| " + " | ".join(values) + " |")
    lines.append("")

    if figure_paths:
        lines.append("## Figuras")
        lines.append("")
        for name, path in figure_paths.items():
            rel = path.name
            lines.append(f"- {name}: `{rel}`")
            lines.append(f"  ![{name}]({rel})")
        lines.append("")

    lines.append("## Notas de interpretacion")
    lines.append("")
    lines.append(
        "- El t-test pareado se calcula sobre agregados a nivel participante (media de latencia y "
        "tasa de exactitud por condicion), no sobre filas individuales de ensayo, porque los ensayos "
        "de un mismo participante no son observaciones independientes."
    )
    lines.append(
        "- Si Shapiro-Wilk sobre las diferencias arroja p < 0.05, se reporta ademas Wilcoxon como "
        "prueba de robustez no parametrica; si ambas coinciden en direccion y significancia, la "
        "conclusion es mas solida."
    )
    lines.append(
        "- El chequeo de efecto de orden compara, entre el grupo A-primero y B-primero, la diferencia "
        "intra-sujeto (A - B). Si no hay diferencia significativa entre grupos, el contrabalanceo "
        "neutralizo el efecto de orden/aprendizaje como se esperaba."
    )
    lines.append("")

    return "\n".join(lines)


def _render_ttest_block(test: dict | None, metric_label: str) -> str:
    if test is None:
        return "No se pudo calcular (datos insuficientes)."

    lines = [
        f"- n = {test['n']}, t({test['df']}) = {fmt(test['t'])}, p = {fmt(test['p'], 4)}",
        f"- Diferencia media (A - B) = {fmt(test['mean_diff'])}, DE de la diferencia = {fmt(test['sd_diff'])}",
        f"- IC 95% de la diferencia: [{fmt(test['ci_low'])}, {fmt(test['ci_high'])}]",
        f"- Cohen's d (pareado, dz) = {fmt(test['cohens_dz'])}",
        f"- Significativo a alfa=0.05: {'SI' if test['p'] < ALPHA else 'NO'}",
    ]

    if test["shapiro_p"] is not None:
        lines.append(
            f"- Shapiro-Wilk sobre diferencias: W = {fmt(test['shapiro_w'])}, p = {fmt(test['shapiro_p'], 4)} "
            f"({'normalidad violada' if test['normality_violated'] else 'no se rechaza normalidad'})"
        )
        if test["normality_violated"] and test["wilcoxon_p"] is not None:
            lines.append(
                f"- Robustez (Wilcoxon signed-rank): W = {fmt(test['wilcoxon_w'])}, p = {fmt(test['wilcoxon_p'], 4)} "
                f"({'SI' if test['wilcoxon_p'] < ALPHA else 'NO'} significativo a alfa=0.05)"
            )

    return "\n".join(f"{line}" for line in lines)


def _render_order_block(test: dict | None, label: str) -> str:
    if test is None:
        return f"No se pudo calcular el chequeo de orden para {label} (datos insuficientes en algun grupo)."
    return (
        f"**{label}**: A-primero (n={test['n_a_first']}, media={fmt(test['mean_a_first'])}) vs "
        f"B-primero (n={test['n_b_first']}, media={fmt(test['mean_b_first'])}) -- "
        f"t = {fmt(test['t'])}, p = {fmt(test['p'], 4)} "
        f"({'HAY efecto de orden detectable' if test['p'] < ALPHA else 'sin evidencia de efecto de orden'})."
    )


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def run(input_path: Path, outdir: Path) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)

    df, contract_warnings = load_data(input_path)
    n_raw_rows = len(df)
    n_participants_total = df["participant_id"].nunique() if not df.empty else 0

    is_synthetic = "synthetic" in input_path.name.lower() or "sintetic" in input_path.name.lower()

    if df.empty:
        report = render_report(
            is_synthetic=is_synthetic,
            n_raw_rows=0,
            n_participants_total=0,
            n_participants_analyzed=0,
            contract_warnings=contract_warnings,
            descriptives=compute_descriptives(pd.DataFrame(columns=["latency_A", "latency_B", "accuracy_A", "accuracy_B"])),
            latency_test=None,
            accuracy_test=None,
            order_latency=None,
            order_accuracy=None,
            breakdown=pd.DataFrame(),
            figure_paths={},
            outdir=outdir,
        )
        report_path = outdir / "report.md"
        report_path.write_text(report, encoding="utf-8")
        logger.warning("Input vacio; se escribio un reporte minimo en %s", report_path)
        return report_path

    agg = build_participant_aggregates(df, contract_warnings)
    n_participants_analyzed = len(agg)

    descriptives = compute_descriptives(agg)

    latency_test = None
    accuracy_test = None
    order_latency = None
    order_accuracy = None

    if n_participants_analyzed >= MIN_N_FOR_INFERENCE:
        latency_test = paired_test_with_ci(agg["latency_A"], agg["latency_B"])
        accuracy_test = paired_test_with_ci(agg["accuracy_A"], agg["accuracy_B"])
        order_latency = order_effect_check(agg, "diff_latency")
        order_accuracy = order_effect_check(agg, "diff_accuracy")
    else:
        contract_warnings.append(
            f"n={n_participants_analyzed} participante(s) con datos completos; se omite estadistica "
            f"inferencial (minimo requerido: {MIN_N_FOR_INFERENCE}). Ver seccion de estadistica inferencial."
        )

    breakdown = per_question_breakdown(df)

    figure_paths: dict[str, Path] = {}
    if n_participants_analyzed > 0:
        box_paths = plot_boxplots(agg, outdir)
        figure_paths["Latencia por condicion (boxplot)"] = box_paths[0]
        figure_paths["Exactitud por condicion (boxplot)"] = box_paths[1]
    dot_path = plot_per_question(breakdown, outdir)
    if dot_path is not None:
        figure_paths["Desglose por pregunta (dot plot)"] = dot_path

    report = render_report(
        is_synthetic=is_synthetic,
        n_raw_rows=n_raw_rows,
        n_participants_total=n_participants_total,
        n_participants_analyzed=n_participants_analyzed,
        contract_warnings=contract_warnings,
        descriptives=descriptives,
        latency_test=latency_test,
        accuracy_test=accuracy_test,
        order_latency=order_latency,
        order_accuracy=order_accuracy,
        breakdown=breakdown,
        figure_paths=figure_paths,
        outdir=outdir,
    )
    report_path = outdir / "report.md"
    report_path.write_text(report, encoding="utf-8")

    return report_path


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Run the paired-design statistical analysis.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Path to export_clean.csv")
    parser.add_argument("--outdir", type=Path, default=DEFAULT_OUTDIR, help="Output directory for report + figures")
    args = parser.parse_args(argv)

    try:
        report_path = run(args.input, args.outdir)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    except ValueError as exc:
        logger.error("%s", exc)
        return 1

    print(f"Reporte generado: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
