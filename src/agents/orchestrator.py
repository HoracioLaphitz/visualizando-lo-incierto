"""Agente Maestro "Orquestador de Investigacion Visual" (DTR seccion 9).

Pipeline runner and CLI for the qualitative-analysis agent network. Each step is
independently runnable, because research workflows are iterative:

    python -m src.agents.orchestrator semiotic --question q01
    python -m src.agents.orchestrator semiotic --all            # cost-guarded
    python -m src.agents.orchestrator code-transcript path.txt
    python -m src.agents.orchestrator insights
    python -m src.agents.orchestrator alternatives --question q09
    python -m src.agents.orchestrator route --input "clasifica este arbol"

The orchestrator resolves the right agent (Subagente 1.1 "Router" uses the cheap
model), runs it, and saves every output under ``analysis/output/agents/`` as
JSON or Markdown with a UTC timestamp and deterministic file naming.

Cost guard: batch runs over all 10 questions print an estimated input size and
ask for confirmation before spending tokens; ``--yes`` skips the prompt.

The ``anthropic`` SDK is only touched when an agent actually runs, so ``--help``
and argument parsing work without the dependency or an API key.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import (
    DEFAULT_CHEAP_MODEL,
    AgentError,
    BaseAgent,
    MissingAPIKeyError,
    approx_tokens,
    resolve_model,
)
from .insight_generator import AlternativeDesigner, ReportWriter
from .qualitative_coder import QualitativeCoder
from .semiotist import GestaltAnalyst, PeirceanClassifier

logger = logging.getLogger(__name__)

# --- Paths -----------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
QUESTIONS_PATH = REPO_ROOT / "data" / "questions.json"
ASSETS_DIR = REPO_ROOT / "assets" / "diagrams"
STAT_REPORT_PATH = REPO_ROOT / "analysis" / "output" / "report.md"
OUTPUT_DIR = REPO_ROOT / "analysis" / "output" / "agents"

#: Condition B stimulus variant used as the vision input (see docs/03).
STIMULUS_VARIANT = "optimized"


# --- Shared helpers --------------------------------------------------------


def _timestamp() -> str:
    """UTC timestamp for deterministic, sortable file names."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_questions() -> list[dict]:
    if not QUESTIONS_PATH.exists():
        raise AgentError(f"No se encontro el banco de preguntas: {QUESTIONS_PATH}")
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return data["questions"]


def get_question(qid: str) -> dict:
    for question in load_questions():
        if question["id"] == qid:
            return question
    raise AgentError(f"Pregunta desconocida: {qid!r}. Usa un id como 'q01'..'q10'.")


def diagram_path(qid: str) -> Path:
    path = ASSETS_DIR / f"{qid}_{STIMULUS_VARIANT}.png"
    if not path.exists():
        raise AgentError(
            f"No se encontro el diagrama {path}. Genera los assets con "
            "'python src/diagrams/generate_diagrams.py'."
        )
    return path


def _ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def save_json(payload: Any, filename: str) -> Path:
    path = _ensure_output_dir() / filename
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return path


def save_text(text: str, filename: str) -> Path:
    path = _ensure_output_dir() / filename
    path.write_text(text, encoding="utf-8")
    return path


def _wrap(agent_name: str, payload: Any) -> dict:
    """Attach provenance metadata to any saved artifact."""
    return {
        "agent": agent_name,
        "generated_at": _timestamp(),
        "result": payload,
    }


def _confirm(prompt: str) -> bool:
    try:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
    except EOFError:
        return False
    return answer in {"y", "yes", "s", "si", "sí"}


# --- Router (cheap model, DTR Subagente 1.1) -------------------------------

ROUTER_SYSTEM = """\
Eres el "Router" del Orquestador de Investigacion Visual. Clasificas la peticion
del usuario y la enrutas al agente especializado correspondiente. Responde
UNICAMENTE con JSON valido, sin texto adicional:
{
  "pipeline": "semiotic|code-transcript|insights|alternatives|unknown",
  "reason": "<por que ese pipeline>"
}

Guia:
- semiotic: analizar/clasificar un diagrama (Peirce, Gestalt, fijacion ocular).
- code-transcript: codificar una transcripcion de pensar en voz alta.
- insights: redactar hallazgos/informe integrando teoria + estadistica.
- alternatives: proponer rediseños para un diagrama que genero confusion.
- unknown: si no encaja en ninguno.
"""


class Router(BaseAgent):
    """Cheap-model classifier that maps free text to a pipeline name."""

    def __init__(self, *, model: str | None = None, client: Any | None = None) -> None:
        super().__init__(
            name="Router",
            model=model or resolve_model(DEFAULT_CHEAP_MODEL),
            system_prompt=ROUTER_SYSTEM,
            max_tokens=512,
            client=client,
        )

    def route(self, user_input: str) -> dict:
        return self.run_json(f"Peticion del usuario:\n{user_input}")


# --- Pipelines -------------------------------------------------------------


def run_semiotic_for_question(qid: str) -> Path:
    """Run both semiotist subagents on one question and save a combined JSON."""
    question = get_question(qid)
    image = diagram_path(qid)

    peircean = PeirceanClassifier()
    gestalt = GestaltAnalyst()

    logger.info("[semiotic] %s: Clasificador Peirceano...", qid)
    peircean_result = peircean.classify(question, image)
    logger.info("[semiotic] %s: Analista Gestaltico...", qid)
    gestalt_result = gestalt.analyze(question, image)

    payload = _wrap(
        "SemiotistaVisual",
        {
            "question_id": qid,
            "stimulus": image.name,
            "peircean_classification": peircean_result,
            "gestalt_analysis": gestalt_result,
        },
    )
    path = save_json(payload, f"{qid}_semiotic_{_timestamp()}.json")
    logger.info("[semiotic] %s guardado en %s", qid, path)
    return path


def preview_semiotic_batch(qids: list[str]) -> dict:
    """Estimate the input size of a full semiotic batch for the cost guard."""
    peircean = PeirceanClassifier()
    gestalt = GestaltAnalyst()
    total_chars = 0
    for qid in qids:
        question = get_question(qid)
        total_chars += peircean.preview(question)["chars"]
        total_chars += gestalt.preview(question)["chars"]
    return {
        "questions": len(qids),
        "requests": len(qids) * 2,
        "images": len(qids) * 2,
        "prompt_chars": total_chars,
        "approx_prompt_tokens": approx_tokens(total_chars),
        "note": (
            "Estimacion solo de texto; cada request incluye ademas 1 imagen PNG "
            "que consume tokens de vision adicionales."
        ),
    }


def cmd_semiotic(args: argparse.Namespace) -> int:
    if args.all:
        qids = [q["id"] for q in load_questions()]
        preview = preview_semiotic_batch(qids)
        print("Prevision de costo (batch semiotico sobre todas las preguntas):")
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        if not args.yes and not _confirm(
            f"Se ejecutaran {preview['requests']} requests con {preview['images']} "
            "imagenes. Continuar?"
        ):
            print("Cancelado.")
            return 0
        for qid in qids:
            run_semiotic_for_question(qid)
        return 0

    if not args.question:
        print("Especifica --question <id> o --all.", file=sys.stderr)
        return 2
    run_semiotic_for_question(args.question)
    return 0


def cmd_code_transcript(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.exists():
        print(f"No existe el archivo de transcripcion: {path}", file=sys.stderr)
        return 2
    transcript = path.read_text(encoding="utf-8")

    coder = QualitativeCoder()
    logger.info("[code-transcript] Codificando %s...", path.name)
    segments = coder.code_transcript(transcript)

    payload = _wrap(
        "EtiquetadorCualitativo",
        {"source": path.name, "n_segments": len(segments), "segments": segments},
    )
    out = save_json(payload, f"transcript_coding_{path.stem}_{_timestamp()}.json")
    logger.info("[code-transcript] guardado en %s", out)
    print(f"Codificados {len(segments)} fragmentos -> {out}")
    return 0


def _load_latest_semiotic() -> list[dict]:
    """Collect the most recent semiotic artifact per question, if any exist."""
    if not OUTPUT_DIR.exists():
        return []
    latest: dict[str, Path] = {}
    for path in sorted(OUTPUT_DIR.glob("*_semiotic_*.json")):
        qid = path.name.split("_semiotic_")[0]
        latest[qid] = path  # sorted ascending -> last write wins (newest)
    analyses = []
    for path in latest.values():
        try:
            analyses.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            logger.warning("Ignorando artefacto ilegible: %s", path)
    return analyses


def _load_coded_transcripts() -> list[dict]:
    if not OUTPUT_DIR.exists():
        return []
    coded = []
    for path in sorted(OUTPUT_DIR.glob("transcript_coding_*.json")):
        try:
            coded.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            logger.warning("Ignorando transcripcion ilegible: %s", path)
    return coded


def cmd_insights(args: argparse.Namespace) -> int:
    semiotic_analyses = _load_latest_semiotic()
    coded_transcripts = _load_coded_transcripts()
    report_md = (
        STAT_REPORT_PATH.read_text(encoding="utf-8")
        if STAT_REPORT_PATH.exists()
        else ""
    )
    if not report_md:
        logger.warning(
            "No se encontro %s; el informe se redactara sin estadistica.",
            STAT_REPORT_PATH,
        )

    writer = ReportWriter()
    logger.info("[insights] Redactando seccion de hallazgos...")
    findings = writer.draft_findings(semiotic_analyses, report_md, coded_transcripts)

    out = save_text(findings, f"findings_{_timestamp()}.md")
    logger.info("[insights] guardado en %s", out)
    print(f"Hallazgos redactados -> {out}")
    return 0


def cmd_alternatives(args: argparse.Namespace) -> int:
    question = get_question(args.question)
    if args.evidence:
        evidence: dict | str = args.evidence
    else:
        evidence = {
            "note": (
                "Sin evidencia estadistica explicita; se usa metadata de la "
                "pregunta como marcador. Pasa --evidence para datos reales."
            ),
            "difficulty": question.get("difficulty"),
            "concept": question.get("concept"),
            "rationale": question.get("rationale"),
        }

    designer = AlternativeDesigner()
    logger.info("[alternatives] Proponiendo rediseños para %s...", args.question)
    result = designer.propose_alternatives(question, evidence)

    payload = _wrap("DiseñadorDeAlternativas", result)
    out = save_json(payload, f"{args.question}_alternatives_{_timestamp()}.json")
    logger.info("[alternatives] guardado en %s", out)
    print(f"Alternativas propuestas -> {out}")
    return 0


def cmd_route(args: argparse.Namespace) -> int:
    router = Router()
    result = router.route(args.input)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


# --- CLI -------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.agents.orchestrator",
        description=(
            "Orquestador de la red de agentes de analisis cualitativo "
            "(DTR seccion 9). Cada paso es ejecutable de forma independiente."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_sem = sub.add_parser(
        "semiotic",
        help="Deconstruccion semiotica de un diagrama (Peirce + Gestalt).",
    )
    p_sem.add_argument("--question", help="Id de la pregunta, ej. q01.")
    p_sem.add_argument(
        "--all", action="store_true", help="Procesar las 10 preguntas (con guarda de costo)."
    )
    p_sem.add_argument(
        "--yes", action="store_true", help="Omitir la confirmacion en corridas batch."
    )
    p_sem.set_defaults(func=cmd_semiotic)

    p_code = sub.add_parser(
        "code-transcript",
        help="Codificar cualitativamente una transcripcion de pensar en voz alta.",
    )
    p_code.add_argument("path", help="Ruta al archivo de transcripcion (.txt).")
    p_code.set_defaults(func=cmd_code_transcript)

    p_ins = sub.add_parser(
        "insights",
        help="Redactar la seccion de hallazgos (integra semiotica + estadistica + transcripciones).",
    )
    p_ins.set_defaults(func=cmd_insights)

    p_alt = sub.add_parser(
        "alternatives",
        help="Proponer 3 rediseños para un diagrama que genero confusion.",
    )
    p_alt.add_argument("--question", required=True, help="Id de la pregunta, ej. q09.")
    p_alt.add_argument(
        "--evidence",
        help="Evidencia de confusion (texto libre). Si se omite, se usa metadata de la pregunta.",
    )
    p_alt.set_defaults(func=cmd_alternatives)

    p_route = sub.add_parser(
        "route",
        help="Clasificar una peticion libre y devolver el pipeline sugerido (modelo barato).",
    )
    p_route.add_argument("--input", required=True, help="Texto de la peticion a enrutar.")
    p_route.set_defaults(func=cmd_route)

    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except MissingAPIKeyError as exc:
        logger.error("%s", exc)
        return 1
    except AgentError as exc:
        logger.error("%s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
