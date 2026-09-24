"""Calibrating a model grader, and reading repeated trials, offline.

For the Evaluations and AgentOps course. Nothing here calls a model: a
"judge" is any function, so a test can script a biased one and show the
check that catches it.

- **Agreement with people.** Anthropic's agent-evals guide says model graders
  "should be frequently calibrated against expert human judgment". Raw
  agreement flatters a judge when one label dominates: a judge that always
  says "pass" agrees 90% of the time on a set that is 90% passes. Cohen's
  kappa, (p_o - p_e) / (1 - p_e), subtracts the agreement expected by chance.
- **Position bias.** Zheng et al., "Judging LLM-as-a-Judge", found judges
  favour an answer for its position. Their conservative fix: "call a judge
  twice by swapping the order of two answers and only declare a win when an
  answer is preferred in both orders", otherwise a tie. `consistency()` is
  their measure: the share of pairs judged the same both ways.
- **Repeated trials.** Agents are non-deterministic, so one run per task
  measures luck as well as skill. pass@k "measures the likelihood that an
  agent gets at least one correct solution in k attempts"; pass^k "measures
  the probability that all k trials succeed". They agree at k=1 and diverge
  after, and the same mean success rate can hide opposite reliability.

Each is pinned by a test in tests/unit/evaluation/test_judge_lab.py.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Sequence

# A judge sees (question, first answer, second answer) and returns which it
# prefers: "first" or "second".
Judge = Callable[[str, str, str], str]


def percent_agreement(judge: Sequence[str], human: Sequence[str]) -> float:
    if len(judge) != len(human) or not judge:
        raise ValueError("need two equal-length, non-empty label lists")
    return sum(j == h for j, h in zip(judge, human, strict=True)) / len(judge)


def cohens_kappa(judge: Sequence[str], human: Sequence[str]) -> float:
    """Agreement beyond chance: 1 is perfect, 0 is what chance alone gives."""
    observed = percent_agreement(judge, human)
    n = len(judge)
    judge_counts, human_counts = Counter(judge), Counter(human)
    expected = sum(
        (judge_counts[label] / n) * (human_counts[label] / n)
        for label in set(judge) | set(human)
    )
    if expected == 1:
        # Both raters used one identical label throughout: nothing to measure.
        return 1.0 if observed == 1 else 0.0
    return (observed - expected) / (1 - expected)


def judge_both_orders(judge: Judge, question: str, a: str, b: str) -> str:
    """Return A, B, or tie: a win only when the judge prefers it in both orders."""
    first_pass = judge(question, a, b)  # a shown first
    second_pass = judge(question, b, a)  # b shown first
    if first_pass == "first" and second_pass == "second":
        return "A"
    if first_pass == "second" and second_pass == "first":
        return "B"
    return "tie"


def consistency(judge: Judge, pairs: Sequence[tuple[str, str, str]]) -> float:
    """Share of (question, a, b) pairs the judge decides the same way both
    orders round, which Zheng et al. use to measure position bias."""
    decided = [judge_both_orders(judge, *pair) != "tie" for pair in pairs]
    return sum(decided) / len(decided)


def pass_at_k(success_rate: float, k: int) -> float:
    """Chance that at least one of k independent trials succeeds."""
    return 1 - (1 - success_rate) ** k


def pass_hat_k(success_rate: float, k: int) -> float:
    """Chance that all k independent trials succeed."""
    return success_rate**k


def suite_scores(task_rates: Sequence[float], k: int) -> dict[str, float]:
    """Mean pass@1, pass@k, and pass^k over a suite of per-task success rates."""
    n = len(task_rates)
    return {
        "pass@1": sum(task_rates) / n,
        f"pass@{k}": sum(pass_at_k(p, k) for p in task_rates) / n,
        f"pass^{k}": sum(pass_hat_k(p, k) for p in task_rates) / n,
    }
