"""Export pipeline: SQLite -> CSV (raw + clean).

Usage:
    python -m src.data.export [--db PATH] [--out DIR]

Writes two files (default: data/results/):

- export_raw.csv   — every response joined with participant demographics,
                     no filtering. Kept for audit (see
                     docs/02_protocolo_investigacion.md, section 4).
- export_clean.csv — exclusion criteria applied:
                     1. rows with latency_seconds < 2 or > 300 are dropped
                        (invalid latency per protocol section 4.1);
                     2. all rows from participants without finalized_at are
                        dropped (incomplete sessions, section 4.2);
                     3. all rows from participants with fewer than 20
                        responses are dropped (incomplete paired design).

Columns (both files):
    participant_id          INTEGER — sequential participant ID
    age_range               TEXT    — 18-24 | 25-34 | 35-44 | 45-54 | 55+
    education_profile       TEXT    — Humanistico | Tecnico | Mixto
    probability_familiarity INTEGER — Likert 1-5
    participant_created_at  TEXT    — UTC timestamp of enrollment
    finalized_at            TEXT    — UTC timestamp of session completion (may be empty in raw)
    question_id             TEXT    — question bank ID (data/questions.json)
    condition               TEXT    — A (formula) | B (diagram)
    block                   INTEGER — 1 | 2
    position                INTEGER — 0-based position within the block
    answer_index            INTEGER — selected option index
    correct                 INTEGER — 1 correct / 0 incorrect
    latency_seconds         REAL    — render-to-submit latency
    response_created_at     TEXT    — UTC timestamp of the response

This module intentionally reads from the SQLite file only. For production
data living in Supabase, download the tables as CSV from the Supabase
dashboard, or point --db at a local SQLite copy. (A direct Supabase export
can be added later without touching the CSV format.)
"""

from __future__ import annotations

import argparse
import csv
import logging
import sqlite3
import sys
from pathlib import Path

from .storage import DB_PATH

logger = logging.getLogger(__name__)

RESULTS_DIR = DB_PATH.parent

LATENCY_MIN = 2.0
LATENCY_MAX = 300.0
EXPECTED_RESPONSES = 20  # 10 questions x 2 blocks

COLUMNS = [
    "participant_id",
    "age_range",
    "education_profile",
    "probability_familiarity",
    "participant_created_at",
    "finalized_at",
    "question_id",
    "condition",
    "block",
    "position",
    "answer_index",
    "correct",
    "latency_seconds",
    "response_created_at",
]

_JOIN_QUERY = """
    SELECT
        p.participant_id,
        p.age_range,
        p.education_profile,
        p.probability_familiarity,
        p.created_at AS participant_created_at,
        p.finalized_at,
        r.question_id,
        r.condition,
        r.block,
        r.position,
        r.answer_index,
        r.correct,
        r.latency_seconds,
        r.created_at AS response_created_at
    FROM responses r
    JOIN participants p ON p.participant_id = r.participant_id
    ORDER BY p.participant_id, r.block, r.position
"""


def fetch_rows(db_path: Path) -> list[dict]:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(_JOIN_QUERY)]
    finally:
        conn.close()


def apply_exclusions(rows: list[dict]) -> list[dict]:
    """Apply protocol exclusion criteria; log counts of what was dropped."""
    # Criterion 2: incomplete sessions (no finalized_at).
    unfinalized = {r["participant_id"] for r in rows if not r["finalized_at"]}
    # Criterion 3: fewer than the expected 20 responses (paired design).
    counts: dict[int, int] = {}
    for r in rows:
        counts[r["participant_id"]] = counts.get(r["participant_id"], 0) + 1
    short_sessions = {pid for pid, n in counts.items() if n < EXPECTED_RESPONSES}

    excluded_participants = unfinalized | short_sessions

    clean: list[dict] = []
    dropped_latency = 0
    dropped_participant_rows = 0
    for r in rows:
        if r["participant_id"] in excluded_participants:
            dropped_participant_rows += 1
            continue
        if r["latency_seconds"] < LATENCY_MIN or r["latency_seconds"] > LATENCY_MAX:
            dropped_latency += 1
            continue
        clean.append(r)

    logger.info("Exclusion report:")
    logger.info(
        "  - Participants excluded (not finalized): %d %s",
        len(unfinalized),
        sorted(unfinalized) if unfinalized else "",
    )
    logger.info(
        "  - Participants excluded (< %d responses): %d %s",
        EXPECTED_RESPONSES,
        len(short_sessions - unfinalized),
        sorted(short_sessions - unfinalized) if (short_sessions - unfinalized) else "",
    )
    logger.info("  - Rows dropped with excluded participants: %d", dropped_participant_rows)
    logger.info(
        "  - Rows dropped for invalid latency (<%.0fs or >%.0fs): %d",
        LATENCY_MIN,
        LATENCY_MAX,
        dropped_latency,
    )
    logger.info("  - Rows kept: %d of %d", len(clean), len(rows))
    return clean


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    logger.info("Wrote %d rows -> %s", len(rows), path)


def run_export(db_path: Path, out_dir: Path) -> tuple[Path, Path]:
    rows = fetch_rows(db_path)
    raw_path = out_dir / "export_raw.csv"
    clean_path = out_dir / "export_clean.csv"
    write_csv(rows, raw_path)
    write_csv(apply_exclusions(rows), clean_path)
    return raw_path, clean_path


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description="Export experiment data to CSV.")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="SQLite database path")
    parser.add_argument("--out", type=Path, default=RESULTS_DIR, help="Output directory")
    args = parser.parse_args(argv)
    try:
        run_export(args.db, args.out)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
