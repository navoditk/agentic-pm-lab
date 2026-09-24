"""Indirect prompt injection, as the Governance course teaches it.

Quiz questions in evals/tutor_quizzes/governance-delivery-tutor.jsonl cite
these tests by name (`verified_by`). The model is scripted to obey the
injected instruction, the worst case.
"""

import json

import pytest

from src.control.guardrails import GuardrailViolation, enforce_content
from src.foundations.agent_loop import ModelTurn, ScriptedModel, ToolCall, run_agent
from src.foundations.injection_lab import (
    LITERAL_INJECTION,
    PARAPHRASED_INJECTION,
    research_tools,
)

ORDER = json.dumps({"ticker": "ACME", "quantity": 1000})


def obeying_model():
    """Reads the note, then does what the note says."""
    return ScriptedModel(
        [
            ModelTurn(
                tool_calls=(ToolCall("c1", "read_research_note", '{"issuer": "ACME"}'),)
            ),
            ModelTurn(tool_calls=(ToolCall("c2", "place_order", ORDER),)),
            ModelTurn(text="Spreads are stable."),
        ]
    )


def run(note, allowed, tmp_path):
    orders: list[dict] = []
    result = run_agent(
        "Summarise the ACME note.",
        obeying_model(),
        research_tools(note, orders),
        allowed_tools=allowed,
        audit_log=tmp_path / "audit.jsonl",
    )
    return result, orders


def test_the_context_guardrail_catches_phrasing_it_knows():
    with pytest.raises(GuardrailViolation):
        enforce_content(LITERAL_INJECTION, "context")


def test_a_paraphrased_injection_passes_the_same_guardrail():
    enforce_content(PARAPHRASED_INJECTION, "context")  # no exception


def test_an_obeyed_injection_is_refused_by_the_allowlist(tmp_path):
    result, orders = run(PARAPHRASED_INJECTION, {"read_research_note"}, tmp_path)
    assert orders == []
    assert [(r["tool_name"], r["decision"]) for r in result.audit] == [
        ("read_research_note", "allowed"),
        ("place_order", "denied"),
    ]
    assert result.answer == "Spreads are stable."


def test_with_the_order_tool_allowed_the_same_injection_trades(tmp_path):
    """Excessive functionality: the agent only needed to read notes."""
    _, orders = run(
        PARAPHRASED_INJECTION, {"read_research_note", "place_order"}, tmp_path
    )
    assert orders == [{"ticker": "ACME", "quantity": 1000}]
