"""Persistence layer for the experiment platform.

Public contract (DO NOT change these signatures — streamlit_app.py depends on
them): `new_participant`, `save_response`, `finalize_session`.

Two backends, selected automatically at import time:

- `SQLiteBackend` — local file `data/results/responses.db`. Used for local
  development and as a safe fallback. WAL mode, foreign keys enforced,
  parameterized queries only.
- `SupabaseBackend` — Postgres via the `supabase-py` client. Used in
  production (Streamlit Community Cloud), whose filesystem is EPHEMERAL: a
  container restart/redeploy wipes any local SQLite file, which would destroy
  experiment data. Supabase persists data outside the container.

Backend selection: if both `SUPABASE_URL` and `SUPABASE_KEY` are present
(checked in `st.secrets` first, then `os.environ`), the Supabase backend is
used. Otherwise SQLite is used and a warning is logged — this is expected for
local dev, but if it happens in a deployed app it means secrets are missing
and data WILL be lost on the next restart.

Schema (both backends, kept equivalent):

    participants(
        participant_id  PK, autoincrement / identity
        age_range       TEXT NOT NULL
        education_profile TEXT NOT NULL
        probability_familiarity INTEGER NOT NULL
        created_at      TEXT/timestamptz NOT NULL, default now
        finalized_at    TEXT/timestamptz NULL  -- NULL until block 2 completes
    )

    responses(
        response_id     PK, autoincrement / identity
        participant_id  FK -> participants
        question_id     TEXT NOT NULL
        condition       TEXT NOT NULL CHECK IN ('A', 'B')
        block           INTEGER NOT NULL CHECK IN (1, 2)
        position        INTEGER NOT NULL
        answer_index    INTEGER NOT NULL
        correct         INTEGER/BOOLEAN NOT NULL
        latency_seconds REAL NOT NULL CHECK (latency_seconds > 0)
        created_at      TEXT/timestamptz NOT NULL, default now
        UNIQUE(participant_id, question_id, block)  -- prevents double-submit
    )

See docs/05_esquema_datos.md for the full field dictionary and the Supabase
setup SQL/secrets format.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional, Protocol

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "results" / "responses.db"

VALID_CONDITIONS = ("A", "B")
VALID_BLOCKS = (1, 2)


# ---------------------------------------------------------------------------
# Backend protocol
# ---------------------------------------------------------------------------


class Backend(Protocol):
    def new_participant(self, demographics: dict) -> int: ...

    def save_response(
        self,
        participant_id: int,
        question_id: str,
        condition: str,
        block: int,
        position: int,
        answer_index: int,
        correct: bool,
        latency_seconds: float,
    ) -> None: ...

    def finalize_session(self, participant_id: int) -> None: ...


def _validate_response_inputs(
    condition: str, block: int, latency_seconds: float
) -> None:
    if condition not in VALID_CONDITIONS:
        raise ValueError(f"condition must be one of {VALID_CONDITIONS}, got {condition!r}")
    if block not in VALID_BLOCKS:
        raise ValueError(f"block must be one of {VALID_BLOCKS}, got {block!r}")
    if not (latency_seconds > 0):
        raise ValueError(f"latency_seconds must be > 0, got {latency_seconds!r}")


# ---------------------------------------------------------------------------
# SQLite backend (local dev / fallback)
# ---------------------------------------------------------------------------


class SQLiteBackend:
    """Local SQLite backend. WAL mode, context-managed connections."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            self._ensure_schema(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    @staticmethod
    def _ensure_schema(conn: sqlite3.Connection) -> None:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS participants (
                participant_id INTEGER PRIMARY KEY AUTOINCREMENT,
                age_range TEXT NOT NULL,
                education_profile TEXT NOT NULL,
                probability_familiarity INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                finalized_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS responses (
                response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                condition TEXT NOT NULL CHECK (condition IN ('A', 'B')),
                block INTEGER NOT NULL CHECK (block IN (1, 2)),
                position INTEGER NOT NULL,
                answer_index INTEGER NOT NULL,
                correct INTEGER NOT NULL CHECK (correct IN (0, 1)),
                latency_seconds REAL NOT NULL CHECK (latency_seconds > 0),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (participant_id) REFERENCES participants (participant_id),
                UNIQUE (participant_id, question_id, block)
            )
            """
        )
        conn.commit()

    def new_participant(self, demographics: dict) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO participants (age_range, education_profile, probability_familiarity)
                VALUES (?, ?, ?)
                """,
                (
                    demographics["age_range"],
                    demographics["education_profile"],
                    demographics["probability_familiarity"],
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def save_response(
        self,
        participant_id: int,
        question_id: str,
        condition: str,
        block: int,
        position: int,
        answer_index: int,
        correct: bool,
        latency_seconds: float,
    ) -> None:
        _validate_response_inputs(condition, block, latency_seconds)
        with self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO responses (
                        participant_id, question_id, condition, block, position,
                        answer_index, correct, latency_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        participant_id,
                        question_id,
                        condition,
                        block,
                        position,
                        answer_index,
                        int(correct),
                        latency_seconds,
                    ),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                logger.warning(
                    "Duplicate/invalid response rejected (participant_id=%s, "
                    "question_id=%s, block=%s): %s",
                    participant_id,
                    question_id,
                    block,
                    exc,
                )
                raise

    def finalize_session(self, participant_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE participants SET finalized_at = datetime('now') WHERE participant_id = ?",
                (participant_id,),
            )
            conn.commit()


# ---------------------------------------------------------------------------
# Supabase backend (production — Streamlit Community Cloud)
# ---------------------------------------------------------------------------


class SupabaseBackend:
    """Supabase (Postgres) backend via supabase-py.

    Requires `SUPABASE_URL` and `SUPABASE_KEY` (service role or a key with
    insert/update rights on `participants`/`responses`) to be set in
    `st.secrets` or environment variables. See docs/05_esquema_datos.md for
    the SQL to create the two tables and the secrets.toml format.
    """

    def __init__(self, url: str, key: str) -> None:
        from supabase import create_client  # imported lazily; optional dep

        self._client = create_client(url, key)

    def new_participant(self, demographics: dict) -> int:
        payload = {
            "age_range": demographics["age_range"],
            "education_profile": demographics["education_profile"],
            "probability_familiarity": demographics["probability_familiarity"],
        }
        result = self._client.table("participants").insert(payload).execute()
        return int(result.data[0]["participant_id"])

    def save_response(
        self,
        participant_id: int,
        question_id: str,
        condition: str,
        block: int,
        position: int,
        answer_index: int,
        correct: bool,
        latency_seconds: float,
    ) -> None:
        _validate_response_inputs(condition, block, latency_seconds)
        payload = {
            "participant_id": participant_id,
            "question_id": question_id,
            "condition": condition,
            "block": block,
            "position": position,
            "answer_index": answer_index,
            "correct": bool(correct),
            "latency_seconds": latency_seconds,
        }
        self._client.table("responses").insert(payload).execute()

    def finalize_session(self, participant_id: int) -> None:
        self._client.table("participants").update(
            {"finalized_at": "now()"}
        ).eq("participant_id", participant_id).execute()


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------


def _get_secret(name: str) -> Optional[str]:
    """Look up a config value in st.secrets first, then environment vars."""
    try:
        import streamlit as st

        if hasattr(st, "secrets") and name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.environ.get(name)


def _select_backend() -> Backend:
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_KEY")
    if url and key:
        try:
            logger.info("Using SupabaseBackend for persistence.")
            return SupabaseBackend(url, key)
        except Exception:
            logger.exception(
                "Failed to initialize SupabaseBackend despite secrets being "
                "present; falling back to SQLite. THIS RISKS DATA LOSS if "
                "deployed on an ephemeral filesystem."
            )
            return SQLiteBackend()
    logger.warning(
        "SUPABASE_URL/SUPABASE_KEY not found; falling back to SQLiteBackend. "
        "If this is a deployed app on an ephemeral filesystem (e.g. Streamlit "
        "Community Cloud), configure Supabase secrets or experiment data WILL "
        "be lost on container restart. See docs/05_esquema_datos.md."
    )
    return SQLiteBackend()


_backend: Optional[Backend] = None


def _get_backend() -> Backend:
    global _backend
    if _backend is None:
        _backend = _select_backend()
    return _backend


# ---------------------------------------------------------------------------
# Public module-level API (contract with streamlit_app.py — DO NOT rename)
# ---------------------------------------------------------------------------


def new_participant(demographics: dict) -> int:
    """Create a new participant record and return the assigned sequential ID.

    `demographics` expects keys: "age_range", "education_profile",
    "probability_familiarity".
    """
    return _get_backend().new_participant(demographics)


def save_response(
    participant_id: int,
    question_id: str,
    condition: str,
    block: int,
    position: int,
    answer_index: int,
    correct: bool,
    latency_seconds: float,
) -> None:
    """Persist a single trial response.

    Raises ValueError if condition/block/latency_seconds are out of the
    allowed domain. Raises on a duplicate (participant_id, question_id,
    block) — that combination is unique to prevent double-submit.
    """
    _get_backend().save_response(
        participant_id,
        question_id,
        condition,
        block,
        position,
        answer_index,
        correct,
        latency_seconds,
    )


def finalize_session(participant_id: int) -> None:
    """Mark a participant's session as finalized (completed both blocks)."""
    _get_backend().finalize_session(participant_id)
