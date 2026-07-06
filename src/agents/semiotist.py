"""Agente 1 "Semiotista Visual" (DTR seccion 9).

Two vision agents that deconstruct a probability diagram:

- :class:`PeirceanClassifier` (Subagente 1.1) — labels each visual element as
  icon / index / symbol, with a justification, grounded in Peirce.
- :class:`GestaltAnalyst` (Subagente 1.2) — reports which Gestalt laws apply,
  the predicted first-fixation zone, and potential perceptual biases.

Both take the diagram PNG (base64) plus its ``diagram_spec`` and return
structured JSON. Prompts are in Spanish because the analyzed material and the
required output artifacts are in Spanish; code and identifiers stay English.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import DEFAULT_ANALYSIS_MODEL, BaseAgent, resolve_model

# --- System prompts (Spanish) ----------------------------------------------

PEIRCEAN_SYSTEM = """\
Eres el "Clasificador Peirceano", un subagente del Semiotista Visual en un
proyecto de investigacion sobre semiotica y cognicion de la probabilidad.

Tu tarea: recibir un diagrama de probabilidad (Venn o arbol) junto con su
especificacion estructural y clasificar CADA elemento visual relevante segun la
tricotomia de Charles Sanders Peirce:

- ICONO: representa por semejanza (ej. el area de un circulo proporcional a una
  probabilidad; la superposicion espacial que refleja la interseccion logica).
- INDICE: representa por conexion directa/causal o direccional (ej. una flecha o
  rama de arbol que apunta a una consecuencia; una secuencia temporal).
- SIMBOLO: representa por convencion arbitraria aprendida (ej. la notacion
  P(A), el color azul asignado al evento A, un signo tipografico).

El contenido matematico es la verdad de referencia: tu analisis semiotico nunca
debe contradecir la exactitud estadistica del diagrama.

Devuelve UNICAMENTE JSON valido, sin texto adicional ni cercas de codigo, con
esta forma exacta:
{
  "question_id": "<id>",
  "diagram_type": "venn|tree",
  "elements": [
    {
      "element": "<descripcion breve del elemento visual>",
      "peirce_category": "icono|indice|simbolo",
      "justification": "<por que pertenece a esa categoria, citando a Peirce>",
      "math_referent": "<que concepto/valor matematico codifica, si aplica>"
    }
  ],
  "summary": "<sintesis de 1-2 frases sobre la mezcla semiotica del diagrama>"
}
"""

GESTALT_SYSTEM = """\
Eres el "Analista Gestaltico", un subagente del Semiotista Visual en un proyecto
sobre semiotica y cognicion de la probabilidad.

Tu tarea: evaluar la composicion perceptual del diagrama (peso visual, contraste,
figura/fondo) aplicando las leyes de la Gestalt, y anticipar como lo procesara el
ojo humano ANTES del razonamiento consciente.

Considera especialmente: semejanza (color por evento), cierre (regiones rellenas
como unidad figural), buena continuidad (ramas curvas, grosor proporcional a la
probabilidad), proximidad y figura/fondo.

Devuelve UNICAMENTE JSON valido, sin texto adicional ni cercas de codigo, con
esta forma exacta:
{
  "question_id": "<id>",
  "diagram_type": "venn|tree",
  "gestalt_laws": [
    {
      "law": "semejanza|cierre|buena_continuidad|proximidad|figura_fondo|otra",
      "applies": true,
      "where": "<en que parte del diagrama se manifiesta>",
      "cognitive_effect": "<efecto esperado sobre la carga cognitiva (H2)>"
    }
  ],
  "predicted_first_fixation": {
    "zone": "<descripcion de la zona donde caeria la primera fijacion ocular>",
    "reason": "<por que esa zona atrae la atencion primero>"
  },
  "potential_biases": [
    {
      "bias": "<sesgo perceptual posible>",
      "risk": "bajo|medio|alto",
      "explanation": "<como el diseño visual podria inducir un error de lectura>"
    }
  ],
  "summary": "<sintesis de 1-2 frases>"
}
"""


def _diagram_context(question: dict) -> str:
    """Render the question's diagram spec into prompt text."""
    spec = question.get("diagram_spec", {})
    return (
        f"question_id: {question.get('id')}\n"
        f"diagram_type: {question.get('diagram_type')}\n"
        f"concept: {question.get('concept')}\n"
        f"enunciado_condicion_B: {question.get('statement_b', '')}\n"
        f"diagram_spec (JSON):\n{json.dumps(spec, ensure_ascii=False, indent=2)}\n"
    )


class PeirceanClassifier(BaseAgent):
    """Subagente 1.1 — icon/index/symbol classification of a diagram."""

    def __init__(self, *, model: str | None = None, client: Any | None = None) -> None:
        super().__init__(
            name="ClasificadorPeirceano",
            model=model or resolve_model(DEFAULT_ANALYSIS_MODEL),
            system_prompt=PEIRCEAN_SYSTEM,
            client=client,
        )

    def _build_prompt(self, question: dict) -> str:
        return (
            "Clasifica semioticamente el siguiente diagrama. La imagen adjunta es "
            "el estimulo visual real (variante 'optimized').\n\n"
            + _diagram_context(question)
        )

    def classify(self, question: dict, image_path: Path) -> dict:
        """Classify one diagram; returns the parsed JSON labeling."""
        return self.run_json(self._build_prompt(question), images=[image_path])

    def preview(self, question: dict) -> dict:
        return self.preview_size(self._build_prompt(question), n_images=1)


class GestaltAnalyst(BaseAgent):
    """Subagente 1.2 — Gestalt / first-fixation / bias analysis of a diagram."""

    def __init__(self, *, model: str | None = None, client: Any | None = None) -> None:
        super().__init__(
            name="AnalistaGestaltico",
            model=model or resolve_model(DEFAULT_ANALYSIS_MODEL),
            system_prompt=GESTALT_SYSTEM,
            client=client,
        )

    def _build_prompt(self, question: dict) -> str:
        return (
            "Analiza la composicion perceptual del siguiente diagrama. La imagen "
            "adjunta es el estimulo visual real (variante 'optimized').\n\n"
            + _diagram_context(question)
        )

    def analyze(self, question: dict, image_path: Path) -> dict:
        """Analyze one diagram; returns the parsed JSON Gestalt report."""
        return self.run_json(self._build_prompt(question), images=[image_path])

    def preview(self, question: dict) -> dict:
        return self.preview_size(self._build_prompt(question), n_images=1)
