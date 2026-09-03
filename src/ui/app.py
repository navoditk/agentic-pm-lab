"""Optional framework-neutral Streamlit comparison surface for Day 11, plus the
read-only tutor face added by the post-Day-21 interactive-tutor extension."""

import sys
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.education.tutor import (
    grade_answers,
    list_topics,
    load_quiz,
    record_attempt,
    teach_topic,
)

st.set_page_config(page_title="Agentic PM Lab", layout="wide")
st.title("Agentic PM Lab — local comparison view")
st.warning(
    "Learning surface using mock portfolio data; no trades or investment advice."
)
st.subheader("Portfolio risk snapshot")
st.metric("Market value", "$1.25m")
st.metric("Volatility", "12.3%")
st.metric("Maximum drawdown", "-7.4%")
st.caption(
    "Canvas and API remain the primary integration paths. This Streamlit view exists only to compare UI frameworks."
)

st.divider()
st.subheader("Tutor")
st.caption(
    "Deterministic, read-only content — no model calls. Same 14 topics as "
    "`.github/agents/*.agent.md` and `uv run python scripts/tutor.py`."
)

_topic_labels = {topic["id"]: topic["label"] for topic in list_topics()}
selected_id = st.sidebar.selectbox(
    "Tutor topic",
    options=list(_topic_labels),
    format_func=lambda topic_id: _topic_labels[topic_id],
)

taught = teach_topic(selected_id)
st.markdown(f"#### {taught['label']}")
st.write(taught["scope_text"])
st.caption(f"Source: `{taught['agent_file']}` · Reference: `{taught['reference']}`")

st.markdown("**Quiz**")
_questions = load_quiz(selected_id)
_answers = []
for _position, _question in enumerate(_questions, start=1):
    _choice = st.radio(
        f"Q{_position}. {_question['question']}",
        options=list(range(len(_question["choices"]))),
        format_func=lambda i, q=_question: q["choices"][i],
        key=f"{selected_id}-q{_position}",
        index=None,
    )
    _answers.append(_choice)

if st.button("Grade quiz", key=f"grade-{selected_id}"):
    if any(answer is None for answer in _answers):
        st.error("Answer every question before grading.")
    else:
        _result = grade_answers(selected_id, _answers)
        record_attempt(selected_id, _result["score"], _result["total"])
        st.success(f"Score: {_result['score']}/{_result['total']}")
        for _item in _result["results"]:
            _mark = "correct" if _item["correct"] else "incorrect"
            st.write(f"`{_item['id']}`: {_mark} — cited: `{_item['citation']}`")
