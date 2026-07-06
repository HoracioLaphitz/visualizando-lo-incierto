# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **research project**, not a software codebase (yet). Title: *"Visualizando lo Incierto: Semiótica y Cognición de la Probabilidad en la Era Algorítmica"* — a quasi-experimental study on whether probability diagrams (Venn, tree) reduce cognitive load compared to algebraic formulas, grounded in Peircean semiotics, Gestalt psychology, Flusser's technical image theory, and Sweller's cognitive load theory.

The authoritative source is `lineamiento_del_proyecto.md` (Documento Técnico de Requerimientos, in Spanish). Read it before any substantive work. All project documents are written in Spanish; keep new research artifacts in Spanish unless asked otherwise.

## Commands

```bash
pip install -r requirements.txt                 # Python deps (Streamlit, matplotlib-venn, scipy, supabase, anthropic)
streamlit run streamlit_app.py                  # run the experiment platform locally
python src/diagrams/generate_diagrams.py        # regenerate all 20 stimulus PNGs from data/questions.json
python -m src.data.export                       # export responses.db -> export_raw.csv + export_clean.csv (applies exclusions)
python analysis/generate_synthetic.py           # synthetic dataset with planted effect (pipeline validation)
python analysis/run_analysis.py --input <csv>   # descriptives + paired t-tests + figures -> analysis/output/
python -m src.agents.orchestrator --help        # AI agent network CLI (needs ANTHROPIC_API_KEY)
```

No test suite; verification is `python -m py_compile <files>` plus running the pipelines above (synthetic data validates the analysis end-to-end).

## Architecture

Pipeline: `data/questions.json` (single source of truth for stimuli — never hardcode question values) → `src/diagrams/generate_diagrams.py` renders `assets/diagrams/{qid}_{baseline|optimized}.png` → `streamlit_app.py` runs the session state-machine (welcome → consent → demographics → block1 → pause → block2) → `src/data/storage.py` persists → `src/data/export.py` extracts → `analysis/run_analysis.py` tests hypotheses → `src/agents/` (Anthropic API network) automates qualitative/semiotic analysis → `docs/08_sintaxis_visual.md` accumulates validated rules.

Key invariants:
- **Storage contract**: `new_participant`, `save_response`, `finalize_session` in `src/data/storage.py` are a frozen interface used by `streamlit_app.py`. Dual backend: Supabase when `SUPABASE_URL`/`SUPABASE_KEY` secrets exist (production — Streamlit Cloud's filesystem is ephemeral), SQLite fallback otherwise.
- **Condition isolation**: Condition A renders only `formula_latex`/`statement_a`; Condition B only the `_optimized.png` + `statement_b`. Never leak one into the other.
- **Counterbalancing**: odd participant ID → A-first; even → B-first. Question order shuffled with `seed=participant_id`.
- **Exclusions live in export, not the DB**: raw records are kept for audit; `export.py` drops latency <2s/>300s and unfinalized participants.
- **Paired analysis on participant-level aggregates**, never trial-level rows (independence violation).
- **Demo mode** (`?mode=demo`) never persists — it exists so portfolio visitors don't contaminate the n=30 sample.
- Mathematical content is ground truth: visual analysis must never drift from statistical exactness (DTR section 4).
- Data contract reference: `src/data/export.py` docstring defines column names; docs must match it (condition values are "A"/"B").

## Deployment

GitHub: HoracioLaphitz. Production: Streamlit Community Cloud (entry point `streamlit_app.py`), linked from the owner's Vercel portfolio via demo mode URL. Supabase setup SQL and secrets format: `docs/05_esquema_datos.md`.

## Experimental Design Constraints

- Repeated-measures design: Condition A (formulas only) vs. Condition B (diagrams only), same 10 questions, 30 participants.
- Metrics: response latency, accuracy rate, eye-tracking (or cursor recording), think-aloud audio.
- Analysis: descriptive stats + paired t-test (p < 0.05), qualitative coding, gaze plot analysis.
- Final deliverable: "Reglas de Sintaxis Visual para la Probabilidad" — a normative document on visual syntax for probability.
