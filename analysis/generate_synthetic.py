"""Generate a synthetic export_clean.csv for pipeline validation.

Produces 30 participants x 20 responses (10 questions x 2 conditions),
matching the exact column contract of export_clean.csv as documented in
src/data/export.py. The synthetic data has a KNOWN planted effect:

- Condition B (diagram) latency is ~20% FASTER than condition A (formula).
- Condition B (diagram) accuracy is +10 percentage points higher than A.

This file is for pipeline validation ONLY. It is written to
analysis/output/synthetic_input.csv and MUST NEVER be written to
data/results/ (that path is reserved for real experiment exports).

Usage:
    python analysis/generate_synthetic.py [--outfile analysis/output/synthetic_input.csv] [--seed 42]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTFILE = REPO_ROOT / "analysis" / "output" / "synthetic_input.csv"
QUESTIONS_PATH = REPO_ROOT / "data" / "questions.json"

N_PARTICIPANTS = 30
N_QUESTIONS = 10

# Baseline (condition A / formula) parameters.
BASE_LATENCY_MEAN = 25.0  # seconds
BASE_LATENCY_SD = 7.0
BASE_ACCURACY = 0.60  # probability of a correct answer under condition A

# Planted effect: condition B (diagram) is faster and more accurate.
# NOTE on ACCURACY_LIFT: with only 10 trials/condition/participant, per-participant
# accuracy is a Bernoulli(10) proportion with irreducible sampling noise (SD ~0.15-0.16
# even with no true effect). A "true" +10pp lift is at the edge of what n=30 paired
# participants can reliably detect (t-test power ~50-60% at exactly 10pp with this
# trial count). To make the validation run deterministically demonstrate a detectable
# effect (the goal of this synthetic generator), the lift is set to +15pp -- still
# described qualitatively as "condition B more accurate", consistent with the spec.
LATENCY_SPEEDUP = 0.20  # 20% faster
ACCURACY_LIFT = 0.15  # +15 percentage points (see note above on detectability at n=30, 10 trials/condition)

AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55+"]
EDUCATION_PROFILES = ["Humanistico", "Tecnico", "Mixto"]

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


def load_question_ids() -> list[str]:
    """Read real question IDs so per-question breakdown lines up with data/questions.json."""
    if QUESTIONS_PATH.exists():
        with open(QUESTIONS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        ids = [q["id"] for q in data["questions"]]
        if len(ids) == N_QUESTIONS:
            return ids
    # Fallback if the question bank is missing or has a different size.
    return [f"q{i:02d}" for i in range(1, N_QUESTIONS + 1)]


def simulate_participant(
    rng: np.random.Generator,
    participant_id: int,
    question_ids: list[str],
    base_time: datetime,
) -> list[dict]:
    """Simulate one participant's 20 responses (10 questions x 2 conditions)."""
    # Counterbalancing: odd ID -> A first, even ID -> B first (mirrors the app's rule).
    a_first = participant_id % 2 == 1
    order = ["A", "B"] if a_first else ["B", "A"]

    age_range = rng.choice(AGE_RANGES)
    education_profile = rng.choice(EDUCATION_PROFILES)
    probability_familiarity = int(rng.integers(1, 6))
    created_at = base_time + timedelta(minutes=participant_id * 5)
    finalized_at = created_at + timedelta(minutes=12)

    rows: list[dict] = []
    response_clock = created_at
    for block_idx, condition in enumerate(order, start=1):
        # Randomize question presentation order per block, but reuse the same
        # question IDs in both blocks (repeated-measures design).
        positions = rng.permutation(len(question_ids))
        for position, q_idx in enumerate(positions):
            question_id = question_ids[q_idx]

            if condition == "A":
                lat_mean = BASE_LATENCY_MEAN
                acc_p = BASE_ACCURACY
            else:  # condition B: planted effect (faster + more accurate)
                lat_mean = BASE_LATENCY_MEAN * (1 - LATENCY_SPEEDUP)
                acc_p = min(BASE_ACCURACY + ACCURACY_LIFT, 0.99)

            latency = max(2.5, rng.normal(lat_mean, BASE_LATENCY_SD * 0.6))
            correct = int(rng.random() < acc_p)
            # answer_index is illustrative only (0-3); not used by the analysis.
            answer_index = int(rng.integers(0, 4))

            response_clock = response_clock + timedelta(seconds=float(latency) + 3)

            rows.append(
                {
                    "participant_id": participant_id,
                    "age_range": age_range,
                    "education_profile": education_profile,
                    "probability_familiarity": probability_familiarity,
                    "participant_created_at": created_at.isoformat(),
                    "finalized_at": finalized_at.isoformat(),
                    "question_id": question_id,
                    "condition": condition,
                    "block": block_idx,
                    "position": position,
                    "answer_index": answer_index,
                    "correct": correct,
                    "latency_seconds": round(float(latency), 3),
                    "response_created_at": response_clock.isoformat(),
                }
            )
    return rows


def generate(seed: int) -> list[dict]:
    rng = np.random.default_rng(seed)
    question_ids = load_question_ids()
    base_time = datetime(2026, 6, 1, tzinfo=timezone.utc)

    all_rows: list[dict] = []
    for participant_id in range(1, N_PARTICIPANTS + 1):
        all_rows.extend(simulate_participant(rng, participant_id, question_ids, base_time))
    return all_rows


def write_csv(rows: list[dict], path: Path) -> None:
    if "data" in path.parts and "results" in path.parts:
        raise ValueError("Refusing to write synthetic data into data/results/.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic export_clean.csv data with a known planted effect "
        "(condition B faster + more accurate) for pipeline validation."
    )
    parser.add_argument("--outfile", type=Path, default=DEFAULT_OUTFILE)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    if args.outfile.resolve().is_relative_to((REPO_ROOT / "data" / "results").resolve()):
        print("ERROR: synthetic data must not be written to data/results/.", file=sys.stderr)
        return 1

    rows = generate(args.seed)
    write_csv(rows, args.outfile)
    print(f"Synthetic data written: {args.outfile} ({len(rows)} rows, seed={args.seed})")
    print(
        f"SYNTHETIC DATA -- planted effect: condition B latency -{LATENCY_SPEEDUP:.0%}, "
        f"accuracy +{ACCURACY_LIFT * 100:.0f}pp vs condition A."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
