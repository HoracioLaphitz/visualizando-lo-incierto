"""Qualitative-analysis agent network (DTR seccion 9).

Automates semiotic deconstruction of diagrams, qualitative coding of think-aloud
transcripts, and insight synthesis, using the Anthropic API. See
``docs/07_arquitectura_agentes.md`` for the architecture and how to run each
pipeline.
"""

from __future__ import annotations

from .base import (
    DEFAULT_ANALYSIS_MODEL,
    DEFAULT_CHEAP_MODEL,
    AgentError,
    BaseAgent,
    MissingAPIKeyError,
)
from .insight_generator import AlternativeDesigner, ReportWriter
from .qualitative_coder import QualitativeCoder
from .semiotist import GestaltAnalyst, PeirceanClassifier

__all__ = [
    "AgentError",
    "MissingAPIKeyError",
    "BaseAgent",
    "DEFAULT_ANALYSIS_MODEL",
    "DEFAULT_CHEAP_MODEL",
    "PeirceanClassifier",
    "GestaltAnalyst",
    "QualitativeCoder",
    "ReportWriter",
    "AlternativeDesigner",
]
