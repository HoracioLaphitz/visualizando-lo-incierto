"""Agente 4 "Generador de Insights" (DTR seccion 9).

- :class:`ReportWriter` (Subagente 4.1 "Creador de Informes") — synthesizes the
  semiotic analyses (Agente 1), the statistical report (Agente 3, i.e.
  ``analysis/output/report.md``) and the coded transcripts into a Spanish
  academic findings section (APA-style prose).
- :class:`AlternativeDesigner` (Subagente 4.2 "Diseñador de Alternativas") —
  given a question's ``diagram_spec`` plus evidence of confusion, proposes three
  design variations as structured JSON changes to visual parameters, grounded in
  Gestalt principles.

Prompts and output artifacts are in Spanish; code and identifiers are English.
"""

from __future__ import annotations

import json
from typing import Any

from .base import DEFAULT_ANALYSIS_MODEL, BaseAgent, resolve_model

REPORT_WRITER_SYSTEM = """\
Eres el "Creador de Informes", subagente del Generador de Insights en un proyecto
de investigacion academica sobre semiotica y cognicion de la probabilidad
(hipotesis H1: los diagramas traducen el signo simbolico a signo espacial; H2:
la Gestalt reduce la carga cognitiva frente a la formula).

Tu tarea: integrar tres fuentes —(1) analisis semiotico de los diagramas, (2) el
reporte estadistico cuantitativo (t-test pareado latencia/exactitud), y (3) la
codificacion cualitativa de transcripciones— y redactar una SECCION DE HALLAZGOS
en prosa academica en español, estilo APA.

Reglas:
- El contenido matematico y estadistico es la verdad de referencia: no exageres
  ni contradigas los valores p, medias o tamaños de efecto del reporte.
- Distingue claramente evidencia (datos) de interpretacion (teoria).
- Cruza las tres fuentes: relaciona un elemento visual concreto con su efecto
  estadistico y con lo que verbalizaron los participantes.
- Si una fuente falta o es sintetica/preliminar, dilo explicitamente y modera
  las afirmaciones.
- Devuelve Markdown en español (encabezados, parrafos). No devuelvas JSON.
"""

ALTERNATIVE_DESIGNER_SYSTEM = """\
Eres el "Diseñador de Alternativas", subagente del Generador de Insights. Cuando
un diagrama genera confusion (alta latencia o baja exactitud), propones
variaciones de diseño para una segunda iteracion del experimento, fundamentadas
en principios de la Gestalt (semejanza, cierre, buena continuidad, proximidad,
figura/fondo) y en la semiotica de Peirce.

Recibes la especificacion estructural del diagrama (diagram_spec) y evidencia de
confusion. Propones EXACTAMENTE 3 variaciones. Cada variacion es un conjunto de
cambios concretos a parametros visuales (color, opacidad, grosor de trazo,
jerarquia tipografica, layout, etiquetado), no una descripcion vaga.

Devuelve UNICAMENTE JSON valido, sin texto adicional ni cercas de codigo:
{
  "question_id": "<id>",
  "diagnosis": "<que problema perceptual explicaria la confusion observada>",
  "variations": [
    {
      "name": "<nombre corto de la variacion>",
      "gestalt_principle": "semejanza|cierre|buena_continuidad|proximidad|figura_fondo",
      "peirce_rationale": "<como cambia la carga icono/indice/simbolo>",
      "changes": [
        {
          "parameter": "<parametro visual concreto, ej. opacidad_interseccion>",
          "from": "<valor/estado actual>",
          "to": "<valor/estado propuesto>",
          "why": "<efecto cognitivo esperado (H2)>"
        }
      ],
      "expected_effect": "<hipotesis sobre latencia/exactitud si se aplica>"
    }
  ]
}
"""


class ReportWriter(BaseAgent):
    """Subagente 4.1 — drafts the Spanish academic findings section."""

    def __init__(self, *, model: str | None = None, client: Any | None = None) -> None:
        super().__init__(
            name="CreadorDeInformes",
            model=model or resolve_model(DEFAULT_ANALYSIS_MODEL),
            system_prompt=REPORT_WRITER_SYSTEM,
            # Findings prose can run long; give it room but stay non-streaming.
            max_tokens=12000,
            client=client,
        )

    def _build_prompt(
        self,
        semiotic_analyses: list[dict] | dict,
        statistical_report_md: str,
        coded_transcripts: list[dict] | dict | None,
    ) -> str:
        semiotic_json = json.dumps(semiotic_analyses, ensure_ascii=False, indent=2)
        transcripts_json = json.dumps(
            coded_transcripts or [], ensure_ascii=False, indent=2
        )
        return (
            "Redacta la seccion de hallazgos integrando las tres fuentes.\n\n"
            "=== 1. ANALISIS SEMIOTICO (Agente 1) ===\n"
            f"{semiotic_json}\n\n"
            "=== 2. REPORTE ESTADISTICO (Agente 3, report.md) ===\n"
            f"{statistical_report_md.strip() or '(sin reporte estadistico disponible)'}\n\n"
            "=== 3. CODIFICACION CUALITATIVA (Subagente 3.2) ===\n"
            f"{transcripts_json}\n"
        )

    def draft_findings(
        self,
        semiotic_analyses: list[dict] | dict,
        statistical_report_md: str,
        coded_transcripts: list[dict] | dict | None = None,
    ) -> str:
        """Return the drafted Spanish findings section (Markdown)."""
        return self.run(
            self._build_prompt(
                semiotic_analyses, statistical_report_md, coded_transcripts
            )
        )

    def preview(
        self,
        semiotic_analyses: list[dict] | dict,
        statistical_report_md: str,
        coded_transcripts: list[dict] | dict | None = None,
    ) -> dict:
        return self.preview_size(
            self._build_prompt(
                semiotic_analyses, statistical_report_md, coded_transcripts
            )
        )


class AlternativeDesigner(BaseAgent):
    """Subagente 4.2 — proposes 3 Gestalt-grounded design variations."""

    def __init__(self, *, model: str | None = None, client: Any | None = None) -> None:
        super().__init__(
            name="DiseñadorDeAlternativas",
            model=model or resolve_model(DEFAULT_ANALYSIS_MODEL),
            system_prompt=ALTERNATIVE_DESIGNER_SYSTEM,
            client=client,
        )

    def _build_prompt(self, question: dict, confusion_evidence: dict | str) -> str:
        spec = question.get("diagram_spec", {})
        if isinstance(confusion_evidence, dict):
            evidence_text = json.dumps(confusion_evidence, ensure_ascii=False, indent=2)
        else:
            evidence_text = str(confusion_evidence)
        return (
            "Propon 3 variaciones de diseño para el siguiente diagrama, que mostro "
            "confusion en el experimento.\n\n"
            f"question_id: {question.get('id')}\n"
            f"diagram_type: {question.get('diagram_type')}\n"
            f"concept: {question.get('concept')}\n"
            f"diagram_spec (JSON):\n{json.dumps(spec, ensure_ascii=False, indent=2)}\n\n"
            "=== EVIDENCIA DE CONFUSION ===\n"
            f"{evidence_text}\n"
        )

    def propose_alternatives(
        self, question: dict, confusion_evidence: dict | str
    ) -> dict:
        """Return the parsed JSON with 3 design variations."""
        return self.run_json(self._build_prompt(question, confusion_evidence))

    def preview(self, question: dict, confusion_evidence: dict | str) -> dict:
        return self.preview_size(self._build_prompt(question, confusion_evidence))
