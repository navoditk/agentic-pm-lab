import pytest

from src.education.tutor import (
    TOPIC_CATALOG,
    grade_answers,
    list_topics,
    load_quiz,
    record_attempt,
    teach_topic,
)


def test_list_topics_covers_all_fourteen_tutors():
    topics = list_topics()
    assert len(topics) == 14
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


def test_teach_topic_rejects_unknown_topic():
    with pytest.raises(ValueError, match="unknown topic"):
        teach_topic("not-a-real-topic")


def test_every_topic_has_a_twenty_to_thirty_question_quiz_with_valid_answer_keys():
    for topic_id in TOPIC_CATALOG:
        questions = load_quiz(topic_id)
        assert 20 <= len(questions) <= 30, (
            f"{topic_id} quiz should have 20-30 questions, has {len(questions)}"
        )
        ids = [question["id"] for question in questions]
        assert len(ids) == len(set(ids)), f"{topic_id} quiz has duplicate ids"
        for question in questions:
            assert len(question["choices"]) == 4
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
