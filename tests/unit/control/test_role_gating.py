from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from opentelemetry import trace

from src.agents import single_agent
from src.control import guardrails
from src.control.audit import read_audit_log, record_audit_event
from src.control.authorization import (
    check_portfolio_access,
    check_tool_permission,
)
from src.control.identity import role_for_identity
from tests.unit.agents.fakes import ScriptedToolCallingModel

IDENTITY_CASES = [
    ("PM_USER", "pm", "price-bond", "delete_portfolio", "PORT_A", "PORT_B"),
    ("RISK_USER", "risk", "risk", "price-bond", "PORT_B", "PORT_UNKNOWN"),
    ("ADMIN_USER", "admin", "research", "delete_portfolio", "PORT_B", "PORT_UNKNOWN"),
]


@pytest.mark.parametrize(
    (
        "identity",
        "role",
        "allowed_tool",
        "denied_tool",
        "allowed_portfolio",
        "denied_portfolio",
    ),
    IDENTITY_CASES,
)
def test_each_identity_has_allowed_and_denied_paths(
    identity,
    role,
    allowed_tool,
    denied_tool,
    allowed_portfolio,
    denied_portfolio,
):
    assert role_for_identity(identity) == role
    assert check_tool_permission(role, allowed_tool)
    assert not check_tool_permission(role, denied_tool)
    assert check_portfolio_access(identity, allowed_portfolio)
    assert not check_portfolio_access(identity, denied_portfolio)


def test_each_identity_decision_has_an_audit_trace_id(tmp_path):
    log_path = tmp_path / "role-decisions.jsonl"
    tracer = trace.get_tracer("tests.role_gating")

    for identity, role, allowed_tool, denied_tool, _, _ in IDENTITY_CASES:
        for tool_name, decision in (
            (allowed_tool, "allowed"),
            (denied_tool, "denied"),
        ):
            with tracer.start_as_current_span(f"{identity}.{decision}"):
                record_audit_event(
                    identity,
                    role,
                    tool_name,
                    decision,
                    "AuthZ",
                    log_path=log_path,
                )

    records = read_audit_log(log_path)
    assert len(records) == 6
    assert {record["identity"] for record in records} == {
        "PM_USER",
        "RISK_USER",
        "ADMIN_USER",
    }
    assert {record["decision"] for record in records} == {"allowed", "denied"}
    assert all(
        len(record["trace_id"]) == 32 and int(record["trace_id"], 16) > 0
        for record in records
    )


def test_backtest_pauses_and_audits_before_execution(monkeypatch):
    events = []
    monkeypatch.setattr(guardrails, "record_audit_event", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        single_agent,
        "record_audit_event",
        lambda *args, **kwargs: events.append((args, kwargs)),
    )
    model = ScriptedToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "run_backtest",
                        "args": {
                            "asset_returns": {"A": [0.01, -0.01]},
                            "weights": {"A": 1.0},
                        },
                        "id": "backtest-call",
                        "type": "tool_call",
                    }
                ],
            )
        ]
    )
    agent = single_agent.create_single_agent(
        "PM_USER",
        model=model,
        checkpointer=InMemorySaver(),
    )
    sources = {
        "user_role": {"identity": "PM_USER", "role": "pm"},
        "portfolio_state": {"portfolio_id": "PORT_A"},
        "market_data": {},
        "retrieved_research": {},
        "memory": [],
        "tool_outputs": [],
        "skills": [],
    }

    result = single_agent.invoke_single_agent(
        "Run a backtest.",
        sources,
        agent=agent,
        thread_id=f"approval-{uuid4()}",
    )

    assert result["__interrupt__"]
    assert not any(
        isinstance(message, ToolMessage) and message.name == "run_backtest"
        for message in result["messages"]
    )
    assert events == [(("PM_USER", "pm", "run_backtest", "interrupted", "Tool"), {})]
