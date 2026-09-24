"""Placement, spaced review, and the mastery matrix. No test writes to
data/learner_progress: every log lives in a temporary directory."""

import json
from datetime import UTC, datetime

import pytest

from src.education.study import (
    PLACEMENT,
    due_concepts,
    grade_placement,
    load_attempts,
    mastery_matrix,
    placement_questions,
    review_queue,
)
from src.education.tutor import COURSE_CATALOG, TOPIC_CATALOG


def write_attempts(log_dir, topic, records):
    path = log_dir / f"{topic}.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def attempt(day, missed=(), tiers=None):
    record = {
        "timestamp": datetime(2026, 9, day, tzinfo=UTC).isoformat(),
        "score": 20,
        "total": 30,
        "missed_concepts": list(missed),
    }
    if tiers:
        record["tiers"] = tiers
    return record


# --- placement -------------------------------------------------------------------


def test_placement_is_twelve_concept_questions_across_the_required_path():
    questions = placement_questions()
    assert len(questions) == 12
    assert {q["tier"] for q in questions} == {"concept"}
    required = {t for t, c in COURSE_CATALOG.items() if c["required"]}
    assert {topic for topic, _ in PLACEMENT} == required


def test_a_course_is_skipped_ahead_only_when_all_its_questions_are_right():
    questions = placement_questions()
    answers = [q["correct_index"] for q in questions]
    # Miss one of the two LangGraph questions.
    langgraph = next(
        i for i, (topic, _) in enumerate(PLACEMENT) if topic.startswith("langgraph")
    )
    answers[langgraph] = (answers[langgraph] + 1) % len(questions[langgraph]["choices"])
    result = grade_placement(answers)
    assert result["score"] == 11
    assert "langgraph-deep-agents-tutor" in result["take"]
    assert "langgraph-deep-agents-tutor" not in result["skip_ahead"]
    assert "mcp-tutor" in result["skip_ahead"]


def test_placement_rejects_the_wrong_number_of_answers():
    with pytest.raises(ValueError, match="expected 12"):
        grade_placement([0, 1])


def test_placement_records_nothing(tmp_path, monkeypatch):
    from src.education import tutor

    monkeypatch.setattr(tutor, "LEARNER_PROGRESS_DIR", tmp_path)
    grade_placement([q["correct_index"] for q in placement_questions()])
    assert list(tmp_path.iterdir()) == []


# --- spaced review -------------------------------------------------------------------


def test_a_concept_is_due_until_the_latest_attempt_gets_it_right(tmp_path):
    write_attempts(
        tmp_path,
        "opentelemetry-tutor",
        [
            attempt(1, ["otel.sampling", "otel.collector"]),
            attempt(5, ["otel.sampling"]),  # collector now right
        ],
    )
    assert [d["concept"] for d in due_concepts(load_attempts(tmp_path))] == [
        "otel.sampling"
    ]


def test_older_misses_come_first(tmp_path):
    write_attempts(tmp_path, "mcp-tutor", [attempt(10, ["mcp.authorization"])])
    write_attempts(tmp_path, "opentelemetry-tutor", [attempt(2, ["otel.sampling"])])
    due = due_concepts(load_attempts(tmp_path))
    assert [d["concept"] for d in due] == ["otel.sampling", "mcp.authorization"]


def test_a_relapse_counts_from_the_new_miss(tmp_path):
    write_attempts(
        tmp_path,
        "opentelemetry-tutor",
        [attempt(1, ["otel.sampling"]), attempt(3), attempt(7, ["otel.sampling"])],
    )
    [due] = due_concepts(load_attempts(tmp_path))
    assert due["since"].startswith("2026-09-07")


def test_the_review_queue_offers_questions_on_each_due_concept(tmp_path):
    write_attempts(tmp_path, "opentelemetry-tutor", [attempt(1, ["otel.sampling"])])
    [item] = review_queue(tmp_path)
    assert item["questions"]
    assert {q["concept"] for q in item["questions"]} == {"otel.sampling"}
    assert item["questions"][0]["tier"] == "concept"


# --- mastery matrix -------------------------------------------------------------------


def test_the_matrix_keeps_the_best_score_per_tier(tmp_path):
    write_attempts(
        tmp_path,
        "mcp-tutor",
        [
            attempt(1, tiers={"concept": {"score": 6, "total": 12}}),
            attempt(2, tiers={"concept": {"score": 10, "total": 12}}),
        ],
    )
    rows = {row["topic"]: row for row in mastery_matrix(load_attempts(tmp_path))}
    assert rows["mcp-tutor"]["concept"] == pytest.approx(10 / 12)
    # Not measured is None, not zero.
    assert rows["mcp-tutor"]["transfer"] is None
    assert list(rows) == list(TOPIC_CATALOG)
