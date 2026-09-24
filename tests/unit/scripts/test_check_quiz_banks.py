"""The quiz-bank checker, tested on the defects it exists to catch.

Each negative case is a way a bank can be passed without understanding, or
can quietly stop matching its sources.
"""

import pytest

from scripts.check_quiz_banks import check, check_bank, check_question

CONCEPTS = {"otel.sampling"}
SOURCES = {"opentelemetry-python"}


def question(i=0, correct=0, **extra):
    return {
        "id": f"t-q{i}",
        "topic": "t",
        "question": f"Question {i}?",
        "choices": ["a", "b", "c", "d"],
        "correct_index": correct,
        "citation": "README.md",
        **extra,
    }


def test_the_committed_banks_are_valid():
    assert check() == []


def test_an_answer_key_that_favours_one_position_is_rejected():
    """The defect that let "always pick B" score 87%."""
    bank = [question(i, correct=1) for i in range(10)]
    [error] = check_bank("t", bank)
    assert "always picks it would score 100%" in error


def test_a_balanced_key_passes():
    assert check_bank("t", [question(i, correct=i % 4) for i in range(12)]) == []


def test_repeated_question_text_across_banks_is_rejected():
    a = question(1, correct=0)
    b = {**question(2, correct=1), "topic": "u", "question": "question 1?  "}
    errors = check({"t": [a], "u": [b]})
    assert any("repeats the question text" in e for e in errors)


def test_a_partly_tiered_bank_is_rejected():
    bank = [question(0, tier="concept")] + [question(i) for i in range(1, 5)]
    assert any("every question" in e for e in check_bank("t", bank))


def test_a_tiered_bank_off_the_mix_is_rejected():
    bank = [question(i, correct=i % 4, tier="implementation") for i in range(10)]
    errors = check_bank("t", bank)
    assert any("concept questions are 0%" in e for e in errors)


def test_a_tiered_bank_on_the_mix_passes():
    tiers = ["concept"] * 4 + ["implementation"] * 4 + ["transfer"] * 2
    bank = [question(i, correct=i % 4, tier=t) for i, t in enumerate(tiers)]
    assert check_bank("t", bank) == []


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (
            {"tier": "concept", "concept": "otel.sampling", "explanation": "x"},
            "registered in source-registry.yaml",
        ),
        (
            {
                "tier": "concept",
                "source_id": "opentelemetry-python",
                "explanation": "x",
            },
            "must name its concept",
        ),
        ({"concept": "otel.nonsense"}, "not in concepts.yaml"),
        ({"tier": "transfer"}, "need an explanation"),
        ({"tier": "sometimes"}, "is not one of"),
        (
            {"verified_by": "tests/unit/test_cli.py::test_that_does_not_exist"},
            "not a test that exists",
        ),
        ({"citation": "src/nowhere.py"}, "does not exist"),
        ({"correct_index": 7}, "is not a choice"),
        ({"choices": ["a", "a", "b"]}, "distinct choices"),
    ],
)
def test_a_malformed_question_is_rejected(extra, message):
    errors = check_question({**question(), **extra}, "t", CONCEPTS, SOURCES)
    assert any(message in e for e in errors), errors


def test_a_well_formed_concept_question_passes():
    q = question(
        tier="concept",
        concept="otel.sampling",
        source_id="opentelemetry-python",
        explanation="Parent-based sampling keeps traces whole.",
        verified_by="tests/unit/test_cli.py::test_every_advertised_command_parses",
    )
    assert check_question(q, "t", CONCEPTS, SOURCES) == []


def test_a_bank_whose_answers_are_usually_the_longest_choice_is_rejected():
    """Always picking the longest choice scored 78% across the banks before
    this rule, passing most of them without reading a question."""

    def q(i, long_correct):
        choices = ["short a", "short b", "short c", "short d"]
        choices[i % 4] = "a much longer correct answer" if long_correct else "short x"
        return question(i, correct=i % 4, choices=choices)

    biased = [q(i, long_correct=True) for i in range(10)]
    errors = check_bank("t", biased)
    assert any("uniquely longest in 10 of 10" in e for e in errors)
    balanced = [q(i, long_correct=i < 3) for i in range(10)]
    assert not any("longest" in e for e in check_bank("t", balanced))
