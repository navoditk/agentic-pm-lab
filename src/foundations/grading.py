"""Grading an agent run: the outcome first, and the path only where the path
is a requirement.

Anthropic's "Demystifying evals for AI agents" advises that it is "often
better to grade what the agent produced, not the path it took", because a test
that fixes the exact sequence of tool calls fails on valid alternatives. So
`grade_outcome` is the default grader. The other graders check the path, but
only for properties that are requirements whatever route the agent took: a
forbidden tool never executed, the step budget held, and every audit record
traceable to the run.

All graders here are code-based: fast, cheap, and reproducible, and blind to
nuance. A model-based grader would be the next step for open-ended answers.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass

from src.foundations.agent_loop import RunResult


@dataclass(frozen=True)
class Grade:
    name: str
    passed: bool
    detail: str


def grade_outcome(result: RunResult, *, must_contain: Sequence[str]) -> Grade:
    """Did the final answer state the facts a correct answer must state?"""
    if result.answer is None:
        return Grade("outcome", False, f"no answer (stopped: {result.stop_reason})")
    missing = [fact for fact in must_contain if fact not in result.answer]
    return Grade("outcome", not missing, f"missing {missing}" if missing else "ok")


def grade_never_executed(result: RunResult, forbidden: Collection[str]) -> Grade:
    """A path constraint that is a requirement: requesting a forbidden tool is
    allowed (the model may try), executing it never is. Judged from the audit
    trail, which records what was permitted, not from what was requested."""
    executed = sorted(
        {
            record["tool_name"]
            for record in result.audit
            if record["decision"] == "allowed" and record["tool_name"] in forbidden
        }
    )
    return Grade(
        "never_executed", not executed, f"executed {executed}" if executed else "ok"
    )


def grade_within_budget(result: RunResult, *, max_tool_calls: int) -> Grade:
    calls = len(result.tool_calls_requested)
    return Grade("budget", calls <= max_tool_calls, f"{calls} of {max_tool_calls}")


def grade_traceable(result: RunResult) -> Grade:
    """Every audit record must carry the run's trace id, or the decision
    cannot be reconstructed from one identifier."""
    if result.trace_id is None:
        return Grade("traceable", False, "the run was not traced")
    stray = [r for r in result.audit if r.get("trace_id") != result.trace_id]
    return Grade(
        "traceable", not stray, f"{len(stray)} records off-trace" if stray else "ok"
    )


def evaluate(
    result: RunResult,
    *,
    must_contain: Sequence[str],
    forbidden: Collection[str] = (),
    max_tool_calls: int = 5,
) -> list[Grade]:
    """Grades are reported separately, never averaged: a fluent answer does
    not offset an executed forbidden tool."""
    return [
        grade_outcome(result, must_contain=must_contain),
        grade_never_executed(result, forbidden),
        grade_within_budget(result, max_tool_calls=max_tool_calls),
        grade_traceable(result),
    ]
