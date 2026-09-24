"""Recording a quiz answered outside the terminal.

`--quiz --answers` lets the agentexpert skill record an attempt the learner
completed in a conversation. It writes the same log a terminal attempt does,
so the things worth pinning are the ones that would make that log lie: a
partial round recorded as a full one, an out-of-range answer recorded as a
wrong one, or a smoke test writing into the real learner log.
"""

import json
from collections import Counter

import pytest

import src.education.tutor as tutor_module
from scripts.tutor import parse_answers, record_answers
from src.education.tutor import load_quiz

TOPIC = "opentelemetry-tutor"


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    """Never touch data/learner_progress/ -- a test run is not a learner."""
    monkeypatch.setattr(tutor_module, "LEARNER_PROGRESS_DIR", tmp_path)
    return tmp_path


def correct_answers(topic=TOPIC):
    return [question["correct_index"] for question in load_quiz(topic)]


def as_raw(answers):
    return ",".join(str(answer) for answer in answers)


def test_a_full_correct_set_is_recorded_as_a_pass(isolated_log):
    result = record_answers(TOPIC, as_raw(correct_answers()))
    assert result["score"] == result["total"] == len(load_quiz(TOPIC))
    assert result["passed"] is True
    assert result["missed"] == []
    [line] = (isolated_log / f"{TOPIC}.jsonl").read_text().splitlines()
    assert json.loads(line)["score"] == result["score"]


def test_missed_questions_come_back_with_their_citations():
    answers = correct_answers()
    first_choices = len(load_quiz(TOPIC)[0]["choices"])
    answers[0] = (answers[0] + 1) % first_choices
    result = record_answers(TOPIC, as_raw(answers))
    assert result["score"] == result["total"] - 1
    [missed] = result["missed"]
    assert missed["id"] == load_quiz(TOPIC)[0]["id"]
    assert missed["citation"]


def test_a_partial_round_is_refused_not_recorded(isolated_log):
    """Five correct practice answers must not become a passed topic."""
    with pytest.raises(ValueError, match="full bank"):
        record_answers(TOPIC, as_raw(correct_answers()[:5]))
    assert not (isolated_log / f"{TOPIC}.jsonl").exists()


@pytest.mark.parametrize("bad", ["9", "-1", "b", ""])
def test_an_out_of_range_answer_is_a_transcription_error(bad):
    questions = load_quiz(TOPIC)
    raw = as_raw(correct_answers()[:-1]) + f",{bad}"
    with pytest.raises(ValueError):
        parse_answers(raw, questions)


def test_whitespace_around_answers_is_tolerated():
    questions = load_quiz(TOPIC)
    spaced = ", ".join(str(answer) for answer in correct_answers())
    assert parse_answers(spaced, questions) == correct_answers()


# --- tiers ------------------------------------------------------------------


def test_a_recorded_attempt_carries_its_tier_breakdown(isolated_log):
    result = record_answers(TOPIC, as_raw(correct_answers()))
    per_tier = Counter(q["tier"] for q in load_quiz(TOPIC))
    assert result["tiers"] == {
        tier: {"score": count, "total": count} for tier, count in per_tier.items()
    }
    line = (isolated_log / f"{TOPIC}.jsonl").read_text().splitlines()[0]
    assert json.loads(line)["tiers"] == result["tiers"]


def test_tier_practice_is_scored_but_never_recorded(isolated_log, monkeypatch, capsys):
    from scripts import tutor as runner

    answers = iter(str(a) for a in correct_answers())
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    runner._run_quiz(TOPIC, "implementation")
    assert "not recorded" in capsys.readouterr().out
    assert not (isolated_log / f"{TOPIC}.jsonl").exists()


def test_recording_refuses_a_tier_filter(monkeypatch):
    from scripts import tutor as runner

    monkeypatch.setattr(
        "sys.argv", ["tutor.py", TOPIC, "--quiz", "--tier", "concept", "--answers", "0"]
    )
    with pytest.raises(SystemExit):
        runner.main()
