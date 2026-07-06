"""Entry point for the 'Visualizando lo Incierto' experiment platform.

Single-page state-machine app built with Streamlit. Stages:
welcome -> consent -> demographics -> instructions -> block1 (10 trials)
-> pause -> block2 (10 trials) -> done

Counterbalancing (see docs/02_protocolo_investigacion.md, section 1.1):
- odd participant_id  -> block 1 = Condition A (formulas), block 2 = Condition B (diagrams)
- even participant_id -> block 1 = Condition B (diagrams), block 2 = Condition A (formulas)

Repeated measures: the same 10 questions appear in both blocks. Question
order is shuffled once per participant with seed=participant_id (reproducible)
and reused for both blocks.

Demo mode (query param ?mode=demo or sidebar toggle): walks the exact same
flow but never writes to persistent storage. Used for portfolio visitors.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

import streamlit as st

from src.data import storage

ROOT_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = ROOT_DIR / "data" / "questions.json"
DIAGRAMS_DIR = ROOT_DIR / "assets" / "diagrams"

CONDITION_A = "A"
CONDITION_B = "B"

PAGE_TITLE = "Visualizando lo Incierto"

CONSENT_TEXT = """
**Consentimiento informado**

Este experimento es parte de un proyecto de investigación sobre semiótica y cognición de la probabilidad. Tu participación es voluntaria y anónima.

- No se recolecta tu nombre, email, ni ningún dato que te identifique personalmente.
- Se registran únicamente: tus respuestas, los tiempos de respuesta, y los datos demográficos agregados que completes a continuación (rango etario, perfil de formación, familiaridad con probabilidad).
- Los datos se analizan de forma agregada junto con los de otros participantes; en ningún informe o publicación aparecerán respuestas individuales identificables.
- Podés abandonar la sesión en cualquier momento cerrando la ventana; los datos de sesiones incompletas no se incluyen en el análisis final.
- La sesión toma aproximadamente 10-15 minutos.

Al continuar, confirmás que sos mayor de 18 años y que aceptás participar bajo estas condiciones.
"""

AGE_RANGES = ["18-24", "25-34", "35-44", "45-54", "55+"]
EDUCATION_PROFILES = ["Humanístico", "Técnico", "Mixto"]


@st.cache_data
def load_questions() -> list[dict]:
    with open(QUESTIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["questions"]


def is_demo_mode() -> bool:
    """Demo mode is active via ?mode=demo query param or the sidebar toggle."""
    query_flag = st.query_params.get("mode") == "demo"
    sidebar_flag = st.session_state.get("demo_toggle", False)
    return query_flag or sidebar_flag


def init_session_state() -> None:
    defaults = {
        "stage": "welcome",
        "participant_id": None,
        "consent_given": False,
        "demographics": None,
        "block_order": None,  # e.g. [CONDITION_A, CONDITION_B]
        "question_order": None,  # list of question ids, shuffled once
        "current_block": 1,
        "trial_start_times": {},  # (block, position) -> timestamp
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_sidebar() -> None:
    with st.sidebar:
        st.toggle("Modo demo (no se registran datos)", key="demo_toggle")
        if is_demo_mode():
            st.info("MODO DEMO activo. Ningún dato se guarda.")


def render_demo_banner() -> None:
    if is_demo_mode():
        st.warning("MODO DEMO — los datos NO se registran.", icon="⚠️")


def block_condition_for(order_position: int) -> str:
    """order_position is 1 for block1, 2 for block2."""
    block_order = st.session_state.block_order
    return block_order[order_position - 1]


def assign_participant(demographics: dict) -> int:
    """Create the participant record (or a throwaway id in demo mode)."""
    if is_demo_mode():
        # Not persisted; parity only needs to be internally consistent for
        # this session, so a random id is fine.
        return random.randint(1, 1_000_000)
    return storage.new_participant(demographics)


def build_block_order(participant_id: int) -> list[str]:
    if participant_id % 2 == 1:
        return [CONDITION_A, CONDITION_B]
    return [CONDITION_B, CONDITION_A]


def build_question_order(participant_id: int, questions: list[dict]) -> list[str]:
    ids = [q["id"] for q in questions]
    rng = random.Random(participant_id)
    shuffled = ids[:]
    rng.shuffle(shuffled)
    return shuffled


def get_question_by_id(questions: list[dict], question_id: str) -> dict:
    for q in questions:
        if q["id"] == question_id:
            return q
    raise KeyError(f"Unknown question id: {question_id}")


# ---------------------------------------------------------------------------
# Stage renderers
# ---------------------------------------------------------------------------


def render_welcome() -> None:
    st.title(PAGE_TITLE)
    st.write(
        "Bienvenido/a a este experimento sobre cómo comprendemos la probabilidad "
        "cuando se presenta con fórmulas o con diagramas. La sesión dura entre "
        "10 y 15 minutos."
    )
    if st.button("Comenzar", type="primary"):
        st.session_state.stage = "consent"
        st.rerun()


def render_consent() -> None:
    st.title("Consentimiento informado")
    st.markdown(CONSENT_TEXT)
    accepted = st.checkbox("Acepto participar", key="consent_checkbox")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Continuar", type="primary", disabled=not accepted):
            st.session_state.consent_given = True
            st.session_state.stage = "demographics"
            st.rerun()
    with col2:
        render_exit_button()


def render_demographics() -> None:
    st.title("Datos demográficos")
    st.write("Estos datos se usan únicamente como covariables de control.")

    age_range = st.selectbox("Rango etario", AGE_RANGES)
    education_profile = st.selectbox("Perfil de formación", EDUCATION_PROFILES)
    familiarity = st.slider(
        "Familiaridad autopercibida con probabilidad "
        "(1 = nunca estudié probabilidad, 5 = la uso regularmente)",
        min_value=1,
        max_value=5,
        value=3,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Continuar", type="primary"):
            demographics = {
                "age_range": age_range,
                "education_profile": education_profile,
                "probability_familiarity": familiarity,
            }
            participant_id = assign_participant(demographics)
            questions = load_questions()

            st.session_state.demographics = demographics
            st.session_state.participant_id = participant_id
            st.session_state.block_order = build_block_order(participant_id)
            st.session_state.question_order = build_question_order(participant_id, questions)
            st.session_state.stage = "instructions"
            st.rerun()
    with col2:
        render_exit_button()


def render_instructions() -> None:
    st.title("Instrucciones")
    st.write(
        """
        A continuación vas a resolver dos bloques de 10 preguntas de probabilidad.

        - Se medirá el tiempo que tardás en responder cada pregunta.
        - No hay penalización por responder rápido o lento.
        - Respondé con la mayor precisión posible, sin usar calculadora ni notas externas.
        - No vas a poder volver a una pregunta anterior una vez enviada la respuesta.
        """
    )
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Comenzar bloque 1", type="primary"):
            st.session_state.stage = "block1"
            st.rerun()
    with col2:
        render_exit_button()


def render_exit_button() -> None:
    if st.button("Salir"):
        st.session_state.stage = "welcome"
        for key in list(st.session_state.keys()):
            if key not in ("demo_toggle",):
                del st.session_state[key]
        st.rerun()


def render_trial(block: int) -> None:
    questions = load_questions()
    order_position = 1 if block == 1 else 2
    condition = block_condition_for(order_position)
    question_ids = st.session_state.question_order
    position = st.session_state.get(f"block{block}_position", 0)

    if position >= len(question_ids):
        # Block complete.
        st.session_state.stage = "pause" if block == 1 else "done"
        if block == 2 and not is_demo_mode():
            storage.finalize_session(st.session_state.participant_id)
        st.rerun()
        return

    question_id = question_ids[position]
    question = get_question_by_id(questions, question_id)

    timer_key = (block, position)
    if timer_key not in st.session_state.trial_start_times:
        st.session_state.trial_start_times[timer_key] = time.time()

    st.title(f"Bloque {block} — Pregunta {position + 1} de {len(question_ids)}")
    st.progress(position / len(question_ids))

    if condition == CONDITION_A:
        st.latex(question["formula_latex"])
        st.write(question["statement_a"])
    else:
        image_path = DIAGRAMS_DIR / f"{question['id']}_optimized.png"
        st.image(str(image_path))
        st.write(question["statement_b"])

    answer = st.radio(
        "Elegí una opción:",
        options=list(range(len(question["options"]))),
        format_func=lambda i: question["options"][i],
        key=f"answer_block{block}_pos{position}",
        index=None,
    )

    if st.button("Enviar respuesta", type="primary", disabled=answer is None):
        submit_time = time.time()
        latency_seconds = submit_time - st.session_state.trial_start_times[timer_key]
        correct = answer == question["correct_index"]

        if not is_demo_mode():
            storage.save_response(
                participant_id=st.session_state.participant_id,
                question_id=question["id"],
                condition=condition,
                block=block,
                position=position,
                answer_index=answer,
                correct=correct,
                latency_seconds=latency_seconds,
            )

        st.session_state[f"block{block}_position"] = position + 1
        st.rerun()


def render_pause() -> None:
    st.title("Pausa")
    st.write("Tomate 30 segundos antes de continuar.")
    if st.button("Continuar", type="primary"):
        st.session_state.stage = "block2"
        st.rerun()


def render_done() -> None:
    st.title("¡Gracias por participar!")
    st.write(
        """
        Tu sesión terminó. Los datos ya fueron guardados de forma anónima y se
        analizarán junto con los de otros participantes.

        No se muestra puntaje ni respuestas correctas para no influir en
        futuros participantes que puedan compartir esta experiencia.
        """
    )


def main() -> None:
    st.set_page_config(page_title=PAGE_TITLE, page_icon="🎲", layout="centered")
    init_session_state()
    render_sidebar()
    render_demo_banner()

    stage = st.session_state.stage
    if stage == "welcome":
        render_welcome()
    elif stage == "consent":
        render_consent()
    elif stage == "demographics":
        render_demographics()
    elif stage == "instructions":
        render_instructions()
    elif stage == "block1":
        render_trial(block=1)
    elif stage == "pause":
        render_pause()
    elif stage == "block2":
        render_trial(block=2)
    elif stage == "done":
        render_done()
    else:
        st.error(f"Unknown stage: {stage}")


if __name__ == "__main__":
    main()
