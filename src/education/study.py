"""Placement, spaced review, and the mastery matrix, from the quiz banks and
the recorded attempts. Nothing here records an attempt.

- **Placement.** Twelve concept questions spread across the required
  courses. A course whose placement questions are all answered correctly
  can be skipped ahead: straight to its quiz, which still has to be passed.
  Placement tests concepts only, so it never marks a course complete.
- **Spaced review.** Every recorded attempt lists the concept ids it missed.
  A concept is due for review while the latest attempt of a course that
  assesses it still misses it; the oldest misses come first, because they
  have had longest to fade.
- **Mastery matrix.** For each course, the best recorded score in each
  question tier, so a learner can see whether they know the ideas
  (concept), this implementation (implementation), or can apply them
  (transfer).

See docs/learning/FOUNDATIONS_MASTERY_PLAN.md section 6.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

from src.education.tutor import (
    COURSE_CATALOG,
    LEARNER_PROGRESS_DIR,
    TOPIC_CATALOG,
    load_quiz,
)

TIERS = ("concept", "implementation", "transfer")

# (course, question id): concept questions only, across the required path.
PLACEMENT: tuple[tuple[str, str], ...] = (
    ("agent-foundations-tutor", "agent-foundations-tutor-q1"),
    ("agent-foundations-tutor", "agent-foundations-tutor-q5"),
    ("agent-architecture-tutor", "agent-architecture-tutor-q35"),
    ("langgraph-deep-agents-tutor", "langgraph-deep-agents-tutor-q32"),
    ("langgraph-deep-agents-tutor", "langgraph-deep-agents-tutor-q39"),
    ("mcp-tutor", "mcp-tutor-q7"),
    ("mcp-tutor", "mcp-tutor-q11"),
    ("opentelemetry-tutor", "opentelemetry-tutor-q26"),
    ("opentelemetry-tutor", "opentelemetry-tutor-q30"),
    ("evaluation-agentops-tutor", "evaluation-agentops-tutor-q31"),
    ("governance-delivery-tutor", "governance-delivery-tutor-q27"),
    ("traceability-capstone-tutor", "traceability-capstone-tutor-q4"),
)


def _question(topic: str, question_id: str) -> dict[str, Any]:
    for question in load_quiz(topic):
        if question["id"] == question_id:
            return question
    raise ValueError(f"{question_id} is not in {topic}'s bank")


def placement_questions() -> list[dict[str, Any]]:
    return [_question(topic, qid) for topic, qid in PLACEMENT]


def grade_placement(answers: Sequence[int]) -> dict[str, Any]:
    """Score a placement run and say which courses can be skipped ahead."""
    questions = placement_questions()
    if len(answers) != len(questions):
        raise ValueError(f"expected {len(questions)} answers, got {len(answers)}")
    by_course: dict[str, list[bool]] = {}
    missed = []
    for (topic, _), question, answer in zip(PLACEMENT, questions, answers, strict=True):
        right = answer == question["correct_index"]
        by_course.setdefault(topic, []).append(right)
        if not right:
            missed.append(question["id"])
    skip_ahead = [topic for topic, marks in by_course.items() if all(marks)]
    take = [topic for topic in by_course if topic not in skip_ahead]
    return {
        "score": len(questions) - len(missed),
        "total": len(questions),
        "skip_ahead": skip_ahead,
        "take": take,
        "missed": missed,
    }


# --- recorded attempts ---------------------------------------------------------


def load_attempts(log_dir: Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Every recorded attempt, per course, oldest first."""
    log_dir = log_dir or LEARNER_PROGRESS_DIR
    attempts: dict[str, list[dict[str, Any]]] = {}
    for topic in TOPIC_CATALOG:
        path = log_dir / f"{topic}.jsonl"
        if path.exists():
            records = [
                json.loads(line) for line in path.read_text().splitlines() if line
            ]
            attempts[topic] = sorted(records, key=lambda r: r["timestamp"])
    return attempts


def due_concepts(
    attempts: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Concepts the latest attempt of some course still misses, oldest first.

    A concept's age is taken from the first attempt in its current run of
    misses for that course, so a concept that was missed, then answered
    correctly, then missed again counts from the second miss.
    """
    since: dict[str, str] = {}
    for records in attempts.values():
        still_missed = set(records[-1].get("missed_concepts", []))
        for concept in still_missed:
            start = records[-1]["timestamp"]
            for record in reversed(records):
                if concept not in record.get("missed_concepts", []):
                    break
                start = record["timestamp"]
            if concept not in since or start < since[concept]:
                since[concept] = start
    return [
        {"concept": concept, "since": when}
        for concept, when in sorted(since.items(), key=lambda item: (item[1], item[0]))
    ]


def review_questions(
    concept: str, *, per_concept: int = 2, tiers: Iterable[str] = TIERS
) -> list[dict[str, Any]]:
    """Practice questions for one concept, preferring concept then transfer."""
    order = {
        tier: rank
        for rank, tier in enumerate(("concept", "transfer", "implementation"))
    }
    wanted = set(tiers)
    matches = [
        question
        for topic in TOPIC_CATALOG
        for question in load_quiz(topic)
        if question.get("concept") == concept and question["tier"] in wanted
    ]
    matches.sort(key=lambda q: (order[q["tier"]], q["id"]))
    return matches[:per_concept]


def review_queue(
    log_dir: Path | None = None, *, limit: int = 5, per_concept: int = 2
) -> list[dict[str, Any]]:
    """The oldest due concepts, each with questions to practise."""
    queue = []
    for item in due_concepts(load_attempts(log_dir))[:limit]:
        queue.append(
            {
                **item,
                "questions": review_questions(item["concept"], per_concept=per_concept),
            }
        )
    return queue


def mastery_matrix(
    attempts: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Best recorded fraction per tier, per course, in the recommended order.

    A tier with no recorded attempt is None, not 0: not measured is not the
    same as not known.
    """
    rows = []
    for topic in TOPIC_CATALOG:
        best: dict[str, float | None] = dict.fromkeys(TIERS)
        for record in attempts.get(topic, []):
            for tier, score in (record.get("tiers") or {}).items():
                if score.get("total"):
                    fraction = score["score"] / score["total"]
                    if best.get(tier) is None or fraction > best[tier]:
                        best[tier] = fraction
        rows.append(
            {
                "topic": topic,
                "module": COURSE_CATALOG[topic]["stage"],
                "required": COURSE_CATALOG[topic]["required"],
                **best,
            }
        )
    return rows


def age_in_days(timestamp: str, now: datetime) -> int:
    return max(0, (now - datetime.fromisoformat(timestamp)).days)
