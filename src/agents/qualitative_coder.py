"""Subagente 3.2 "Etiquetador Cualitativo (NLP)" (DTR seccion 9).

Codes think-aloud transcript segments into the categories defined by the DTR
(seccion 6): ``carga_cognitiva_alta``, ``reconocimiento_de_patrones``,
``frustracion``, ``momento_eureka``, and a catch-all ``otro``. Each coded
segment carries the supporting quote and a confidence score.

This is the "cheap labeler" of the network: it defaults to the Haiku model,
because segment classification is a high-volume, low-complexity task. Input is a
plain-text transcript; output is a JSON list of coded segments. Prompts are in
Spanish (the transcripts are Spanish audio transcriptions).
"""

from __future__ import annotations

from typing import Any

from .base import DEFAULT_CHEAP_MODEL, BaseAgent, resolve_model

CATEGORIES = [
    "carga_cognitiva_alta",
    "reconocimiento_de_patrones",
    "frustracion",
    "momento_eureka",
    "otro",
]

CODER_SYSTEM = """\
Eres el "Etiquetador Cualitativo", un subagente del Cientifico de Datos
Cognitivos. Procesas transcripciones del protocolo de "pensar en voz alta":
grabaciones de participantes que explican su razonamiento mientras resuelven
problemas de probabilidad (con formula o con diagrama).

Tu tarea: segmentar la transcripcion en fragmentos con significado y asignar a
cada fragmento UNA de estas categorias:

- carga_cognitiva_alta: el participante expresa esfuerzo mental elevado, se
  pierde, relee, o verbaliza que le cuesta seguir los pasos.
- reconocimiento_de_patrones: identifica una estructura, relacion espacial o
  regularidad (ej. "las dos ramas llevan a lo mismo", "esta parte es la
  interseccion").
- frustracion: expresa enojo, rendicion, o afecto negativo hacia la tarea.
- momento_eureka: expresa comprension subita ("ah, ya entendi", "claro").
- otro: cualquier fragmento relevante que no encaje en las anteriores.

No inventes contenido: cada fragmento codificado debe citar texto que este
literalmente en la transcripcion. Asigna una confianza entre 0.0 y 1.0.

Devuelve UNICAMENTE JSON valido, sin texto adicional ni cercas de codigo:
{
  "segments": [
    {
      "category": "carga_cognitiva_alta|reconocimiento_de_patrones|frustracion|momento_eureka|otro",
      "quote": "<cita textual del fragmento>",
      "confidence": 0.0
    }
  ]
}
"""


class QualitativeCoder(BaseAgent):
    """Codes think-aloud transcripts into cognitive-load categories."""

    def __init__(self, *, model: str | None = None, client: Any | None = None) -> None:
        super().__init__(
            name="EtiquetadorCualitativo",
            model=model or resolve_model(DEFAULT_CHEAP_MODEL),
            system_prompt=CODER_SYSTEM,
            client=client,
        )

    def _build_prompt(self, transcript: str) -> str:
        return (
            "Codifica la siguiente transcripcion de pensar en voz alta. "
            "Devuelve la lista de fragmentos codificados.\n\n"
            "--- TRANSCRIPCION ---\n"
            f"{transcript.strip()}\n"
            "--- FIN TRANSCRIPCION ---\n"
        )

    def code_transcript(self, transcript: str) -> list[dict]:
        """Return the list of coded segments for a transcript."""
        result = self.run_json(self._build_prompt(transcript))
        segments = result.get("segments", []) if isinstance(result, dict) else result
        return segments if isinstance(segments, list) else []

    def preview(self, transcript: str) -> dict:
        return self.preview_size(self._build_prompt(transcript))
