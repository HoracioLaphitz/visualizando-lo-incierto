"""Thin agent base for the qualitative-analysis agent network.

Implements the shared machinery every specialized agent in this package needs:

- Anthropic client construction from the ``ANTHROPIC_API_KEY`` environment
  variable (never hardcoded), with a clear error when it is missing.
- A single ``BaseAgent.run`` entry point that turns a system prompt plus user
  content (optionally including base64 PNG images, for the vision agents) into
  a model response.
- Retry with exponential backoff on rate limits and transient 5xx errors.
- Helpers for extracting text and parsing JSON out of model responses.

Model selection follows the project contract:

- Analysis agents default to ``claude-sonnet-5``.
- The cheap router / labeler defaults to ``claude-haiku-4-5-20251001``.
- Both can be overridden globally via the ``ANTHROPIC_MODEL`` environment
  variable (useful for cost sweeps or pinning a specific snapshot).

The ``anthropic`` SDK is imported lazily inside :func:`get_client` so that the
orchestrator CLI (``--help``, argument parsing) works even when the dependency
is not installed and without ever requiring an API key.

All code, comments, and identifiers are in English. The *agent prompts* live in
the specialized modules and are written in Spanish, because they analyze
Spanish research material and must emit Spanish artifacts.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Any, Sequence

logger = logging.getLogger(__name__)

# --- Model configuration ---------------------------------------------------

#: Default model for the analysis agents (semiotist, insight generator).
DEFAULT_ANALYSIS_MODEL = "claude-sonnet-5"
#: Default model for the cheap router / qualitative labeler.
DEFAULT_CHEAP_MODEL = "claude-haiku-4-5-20251001"

ENV_API_KEY = "ANTHROPIC_API_KEY"
ENV_MODEL_OVERRIDE = "ANTHROPIC_MODEL"

#: Conservative non-streaming default. Kept under the SDK's ~16k streaming
#: guard so plain ``messages.create`` calls do not risk HTTP timeouts.
DEFAULT_MAX_TOKENS = 8000

#: Rough characters-per-token ratio, only for the orchestrator cost preview.
#: Not a substitute for the token-counting endpoint.
APPROX_CHARS_PER_TOKEN = 4


class AgentError(RuntimeError):
    """Base error for the agent package."""


class MissingAPIKeyError(AgentError):
    """Raised when ``ANTHROPIC_API_KEY`` is not present in the environment."""


# --- Model resolution ------------------------------------------------------


def resolve_model(default: str) -> str:
    """Return the ``ANTHROPIC_MODEL`` override if set, else ``default``."""
    override = os.environ.get(ENV_MODEL_OVERRIDE)
    return override.strip() if override and override.strip() else default


def get_client() -> Any:
    """Build an Anthropic client from the environment.

    Raises :class:`MissingAPIKeyError` with an actionable message when the API
    key is absent, and :class:`AgentError` when the ``anthropic`` SDK is not
    installed. The SDK import is deferred to here so argument parsing does not
    depend on it.
    """
    api_key = os.environ.get(ENV_API_KEY)
    if not api_key or not api_key.strip():
        raise MissingAPIKeyError(
            "La variable de entorno ANTHROPIC_API_KEY no esta definida. "
            "Exporta tu clave antes de ejecutar los agentes, por ejemplo:\n"
            "  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "La clave nunca se guarda en el codigo."
        )
    try:
        import anthropic  # noqa: PLC0415 (deliberate lazy import)
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise AgentError(
            "El paquete 'anthropic' no esta instalado. Instala las dependencias "
            "con 'pip install -r requirements.txt'."
        ) from exc
    return anthropic.Anthropic(api_key=api_key)


# --- Content helpers -------------------------------------------------------


def encode_image_block(image_path: Path) -> dict:
    """Read a PNG file and return an Anthropic base64 image content block."""
    image_path = Path(image_path)
    if not image_path.exists():
        raise AgentError(f"No se encontro la imagen del diagrama: {image_path}")
    data = base64.standard_b64encode(image_path.read_bytes()).decode("utf-8")
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": data},
    }


def extract_text(response: Any) -> str:
    """Concatenate the text blocks of a Messages API response."""
    parts = [
        block.text
        for block in getattr(response, "content", [])
        if getattr(block, "type", None) == "text"
    ]
    return "".join(parts).strip()


def parse_json(text: str) -> Any:
    """Parse JSON from a model response, tolerating Markdown code fences.

    Raises :class:`AgentError` with the offending text when parsing fails, so
    callers get a debuggable message instead of a bare ``JSONDecodeError``.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        # Drop the opening fence (``` or ```json) and the closing fence.
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise AgentError(
            f"La respuesta del modelo no es JSON valido: {exc}\n---\n{text[:2000]}"
        ) from exc


def estimate_input_chars(system_prompt: str, user_text: str) -> int:
    """Character count of the textual prompt payload (images excluded)."""
    return len(system_prompt) + len(user_text)


def approx_tokens(char_count: int) -> int:
    """Very rough token estimate from a character count (preview only)."""
    return char_count // APPROX_CHARS_PER_TOKEN


# --- Base agent ------------------------------------------------------------


class BaseAgent:
    """Minimal agent: system prompt + user content -> response.

    Subclasses set ``name``, ``model``, and ``system_prompt`` and expose
    task-specific methods that build the user content and post-process the
    response via :meth:`run` / :meth:`run_json`.
    """

    def __init__(
        self,
        *,
        name: str,
        model: str,
        system_prompt: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        max_retries: int = 4,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        client: Any | None = None,
    ) -> None:
        self.name = name
        self.model = model
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._client = client

    # -- internals ---------------------------------------------------------

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = get_client()
        return self._client

    def _build_messages(
        self, user_text: str, images: Sequence[Path] | None
    ) -> list[dict]:
        content: list[dict] = []
        for image in images or []:
            content.append(encode_image_block(Path(image)))
        content.append({"type": "text", "text": user_text})
        return [{"role": "user", "content": content}]

    def _call_with_retry(self, messages: list[dict], max_tokens: int) -> Any:
        import anthropic  # lazy; SDK already importable if we reached here

        client = self._get_client()
        last_exc: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                return client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=self.system_prompt,
                    messages=messages,
                )
            except anthropic.RateLimitError as exc:
                last_exc = exc
                retry_after = _retry_after_seconds(exc)
                delay = retry_after if retry_after is not None else self._backoff(attempt)
                logger.warning(
                    "[%s] Rate limit (intento %d/%d); reintento en %.1fs",
                    self.name, attempt + 1, self.max_retries + 1, delay,
                )
            except anthropic.APIStatusError as exc:
                # Retry only transient server-side failures; surface 4xx.
                if exc.status_code >= 500:
                    last_exc = exc
                    delay = self._backoff(attempt)
                    logger.warning(
                        "[%s] Error de servidor %s (intento %d/%d); reintento en %.1fs",
                        self.name, exc.status_code, attempt + 1,
                        self.max_retries + 1, delay,
                    )
                else:
                    raise
            except anthropic.APIConnectionError as exc:
                last_exc = exc
                delay = self._backoff(attempt)
                logger.warning(
                    "[%s] Error de conexion (intento %d/%d); reintento en %.1fs",
                    self.name, attempt + 1, self.max_retries + 1, delay,
                )

            if attempt < self.max_retries:
                time.sleep(delay)

        assert last_exc is not None
        raise AgentError(
            f"[{self.name}] Se agotaron los reintentos ({self.max_retries + 1})."
        ) from last_exc

    def _backoff(self, attempt: int) -> float:
        return min(
            self.base_delay * (2 ** attempt) + random.uniform(0, 1),
            self.max_delay,
        )

    # -- public API --------------------------------------------------------

    def run(
        self,
        user_text: str,
        *,
        images: Sequence[Path] | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Send one request and return the response text."""
        messages = self._build_messages(user_text, images)
        response = self._call_with_retry(messages, max_tokens or self.max_tokens)
        return extract_text(response)

    def run_json(
        self,
        user_text: str,
        *,
        images: Sequence[Path] | None = None,
        max_tokens: int | None = None,
    ) -> Any:
        """Send one request and parse the response as JSON."""
        return parse_json(self.run(user_text, images=images, max_tokens=max_tokens))

    def preview_size(self, user_text: str, n_images: int = 0) -> dict:
        """Return a rough input-size preview for the cost guard."""
        chars = estimate_input_chars(self.system_prompt, user_text)
        return {
            "chars": chars,
            "approx_tokens": approx_tokens(chars),
            "images": n_images,
        }


def _retry_after_seconds(exc: Any) -> float | None:
    """Best-effort read of the ``retry-after`` header from an SDK error."""
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    value = headers.get("retry-after")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
