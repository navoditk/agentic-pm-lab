"""Grader calibration and repeated trials, as the Evaluations course teaches.

Quiz questions in evals/tutor_quizzes/evaluation-agentops-tutor.jsonl cite
these tests by name (`verified_by`). Every judge here is a scripted function.
"""

import pytest

from src.evaluation.judge_lab import (
    cohens_kappa,
    consistency,
    judge_both_orders,
    pass_at_k,
    pass_hat_k,
    percent_agreement,
    suite_scores,
)

# 20 labelled answers: 18 a person passed, 2 they failed.
HUMAN = ["pass"] * 18 + ["fail"] * 2


def always_first(question, first, second):
    return "first"


def prefers_the_cited_answer(question, first, second):
    return "first" if "[source]" in first else "second"


PAIRS = [
    ("Duration of the 5y?", "4.6 years [source]", "about 5"),
    ("Is PORT_B in limit?", "yes", "no, 3% over [source]"),
]


def test_raw_agreement_flatters_a_judge_that_always_says_pass():
    judge = ["pass"] * 20
    assert percent_agreement(judge, HUMAN) == 0.9
    assert cohens_kappa(judge, HUMAN) == 0.0  # no better than chance


def test_kappa_credits_agreement_beyond_chance():
    # Catches one of the two failures and wrongly fails one good answer.
    judge = ["pass"] * 17 + ["fail"] + ["fail", "pass"]
    assert percent_agreement(judge, HUMAN) == 0.9
    assert cohens_kappa(judge, HUMAN) == pytest.approx(0.444, abs=0.001)


def test_swapping_the_order_exposes_a_position_biased_judge():
    assert [judge_both_orders(always_first, *pair) for pair in PAIRS] == ["tie", "tie"]
    assert consistency(always_first, PAIRS) == 0.0


def test_a_judge_that_reads_the_answers_wins_in_both_orders():
    assert [judge_both_orders(prefers_the_cited_answer, *p) for p in PAIRS] == [
        "A",
        "B",
    ]
    assert consistency(prefers_the_cited_answer, PAIRS) == 1.0


def test_pass_at_k_and_pass_hat_k_agree_at_one_and_diverge_after():
    assert pass_at_k(0.8, 1) == pass_hat_k(0.8, 1) == 0.8
    assert pass_at_k(0.8, 3) == pytest.approx(0.992)
    assert pass_hat_k(0.8, 3) == pytest.approx(0.512)


def test_the_same_mean_success_rate_can_hide_opposite_reliability():
    steady = [0.8] * 10  # every task works four times in five
    split = [1.0] * 8 + [0.0] * 2  # most tasks always work, two never do
    steady_scores, split_scores = suite_scores(steady, 3), suite_scores(split, 3)
    assert steady_scores["pass@1"] == pytest.approx(split_scores["pass@1"])
    # Retries rescue the steady agent; they cannot rescue a task that never works.
    assert steady_scores["pass@3"] > split_scores["pass@3"]
    # Needing every run to succeed punishes the steady agent's flakiness.
    assert steady_scores["pass^3"] < split_scores["pass^3"]
