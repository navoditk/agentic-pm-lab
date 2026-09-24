import json

import pytest

from src.education import tutor as tutor_module
from src.education.tutor import (
    TIER_PASS,
    TOPIC_CATALOG,
    attempt_passes,
    grade_answers,
    list_topics,
    load_quiz,
    record_attempt,
    teach_topic,
)


def test_list_topics_covers_every_tutor():
    topics = list_topics()
    assert len(topics) == len(TOPIC_CATALOG)
    assert {topic["id"] for topic in topics} == set(TOPIC_CATALOG)


def test_teach_topic_is_read_only_and_grounded_in_the_agent_file():
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[3]
    for topic_id in TOPIC_CATALOG:
        taught = teach_topic(topic_id)
        assert taught["read_only"] is True
        assert taught["investment_advice"] is False
        assert taught["scope_text"], f"{topic_id} has no scope text"
        assert taught["agent_file"].endswith(f"{topic_id}.agent.md")
        assert taught["reference"].startswith("docs/reference/REFERENCES.md#"), (
            f"{topic_id} has no specific reference anchor"
        )
        assert (repo_root / taught["deep_dive"]).is_file(), (
            f"{topic_id}'s deep_dive path does not exist: {taught['deep_dive']}"
        )


def _github_heading_slugs(markdown: str) -> set[str]:
    """Slugify every heading the way GitHub does, to resolve `#fragment` links.

    Two details are what make this match the real renderer, and getting either
    wrong turns the test below into one that passes on broken anchors:
    inline markdown renders first (a link becomes its text, a code span its
    contents), and each space becomes one hyphen rather than runs collapsing,
    which is why a heading containing `&` yields a doubled hyphen.
    """
    import re

    slugs = set()
    for line in markdown.splitlines():
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip()
        heading = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading).replace("`", "")
        slugs.add(re.sub(r"[^\w\s-]", "", heading.lower()).replace(" ", "-"))
    return slugs


def test_every_reference_anchor_resolves_to_a_real_heading():
    """A learner clicking the reference must land on the section, not page top.

    The prior assertion only checked the anchor was *present*, which a
    truncated fragment passes: `governance-delivery-tutor` pointed at
    `#security-authnauthz-policy-as-code-prompt-injection` while the heading
    carried a `(Day 7, ... §15)` suffix that GitHub folds into the slug, so
    three learner-facing links silently landed at the top of a long file.
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[3]
    references = repo_root / "docs/reference/REFERENCES.md"
    slugs = _github_heading_slugs(references.read_text(encoding="utf-8"))

    for topic_id in TOPIC_CATALOG:
        fragment = teach_topic(topic_id)["reference"].split("#", 1)[1]
        assert fragment in slugs, (
            f"{topic_id}'s reference anchor #{fragment} matches no heading in "
            f"REFERENCES.md; a learner following it lands at the top of the file"
        )


def test_teach_topic_rejects_unknown_topic():
    with pytest.raises(ValueError, match="unknown topic"):
        teach_topic("not-a-real-topic")


def test_every_topic_has_a_twenty_to_thirty_five_question_quiz_with_valid_keys():
    # Up to 35 so a course can hold its 40/40/20 tier mix; the full format
    # rules live in scripts/check_quiz_banks.py.
    for topic_id in TOPIC_CATALOG:
        questions = load_quiz(topic_id)
        assert 20 <= len(questions) <= 35, (
            f"{topic_id} quiz should have 20-35 questions, has {len(questions)}"
        )
        ids = [question["id"] for question in questions]
        assert len(ids) == len(set(ids)), f"{topic_id} quiz has duplicate ids"
        for question in questions:
            assert 3 <= len(question["choices"]) <= 5
            assert 0 <= question["correct_index"] < len(question["choices"])
            assert question["citation"]


def test_grade_answers_scores_all_correct_and_all_wrong():
    topic_id = "investment-data-tutor"
    questions = load_quiz(topic_id)
    correct_answers = [q["correct_index"] for q in questions]
    result = grade_answers(topic_id, correct_answers)
    assert result["score"] == result["total"] == len(questions)
    assert all(item["correct"] for item in result["results"])

    wrong_answers = [(q["correct_index"] + 1) % len(q["choices"]) for q in questions]
    result = grade_answers(topic_id, wrong_answers)
    assert result["score"] == 0
    assert not any(item["correct"] for item in result["results"])


def test_grade_answers_rejects_mismatched_answer_count():
    with pytest.raises(ValueError, match="expected"):
        grade_answers("investment-data-tutor", [0])


def test_record_attempt_writes_one_jsonl_line(tmp_path):
    log_path = record_attempt("investment-data-tutor", 4, 5, log_dir=tmp_path)
    assert log_path.parent == tmp_path
    lines = log_path.read_text().splitlines()
    assert len(lines) == 1
    import json

    record = json.loads(lines[0])
    assert record["topic"] == "investment-data-tutor"
    assert record["score"] == 4
    assert record["total"] == 5
    assert "timestamp" in record


def test_record_attempt_appends_across_calls(tmp_path):
    record_attempt("investment-data-tutor", 3, 5, log_dir=tmp_path)
    log_path = record_attempt("investment-data-tutor", 5, 5, log_dir=tmp_path)
    assert len(log_path.read_text().splitlines()) == 2


# --- tiers and the pass rule --------------------------------------------------


def test_a_question_without_a_tier_is_an_implementation_question():
    assert {q["tier"] for q in load_quiz("investment-data-tutor")} == {"implementation"}


@pytest.mark.parametrize(
    ("score", "total", "tiers", "expected"),
    [
        (8, 10, None, True),  # a record from before tiers: overall only
        (7, 10, None, False),
        (9, 10, {"concept": {"score": 4, "total": 5}}, True),
        # 90% overall cannot hide a weak tier
        (18, 20, {"concept": {"score": 3, "total": 5}}, False),
        (0, 0, None, False),
    ],
)
def test_attempt_passes_applies_overall_and_per_tier_thresholds(
    score, total, tiers, expected
):
    assert attempt_passes(score, total, tiers) is expected


def test_grading_reports_each_tier_and_the_concepts_missed(monkeypatch):
    bank = [
        {
            "id": f"q{i}",
            "question": "?",
            "choices": ["a", "b", "c", "d"],
            "correct_index": 0,
            "citation": "README.md",
            "tier": tier,
            "concept": concept,
        }
        for i, (tier, concept) in enumerate(
            [("concept", "otel.sampling")] * 4 + [("implementation", None)] * 6
        )
    ]
    monkeypatch.setattr(tutor_module, "load_quiz", lambda _topic: bank)
    # All implementation right; 2 of 4 concept right: 80% overall, 50% concept.
    answers = [0, 0, 1, 1] + [0] * 6
    result = tutor_module.grade_answers("any", answers)
    assert result["score"] == 8
    assert result["tiers"] == {
        "concept": {"score": 2, "total": 4},
        "implementation": {"score": 6, "total": 6},
    }
    assert result["missed_concepts"] == ["otel.sampling"]
    assert 2 / 4 < TIER_PASS and result["passed"] is False


def test_record_attempt_keeps_tiers_so_the_rule_can_be_reapplied(tmp_path):
    path = tutor_module.record_attempt(
        "t",
        8,
        10,
        tiers={"concept": {"score": 2, "total": 4}},
        missed_concepts=["otel.sampling"],
        log_dir=tmp_path,
    )
    record = json.loads(path.read_text())
    assert record["tiers"] == {"concept": {"score": 2, "total": 4}}
    assert record["missed_concepts"] == ["otel.sampling"]
