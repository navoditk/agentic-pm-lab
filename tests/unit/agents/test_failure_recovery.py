import json
from pathlib import Path
from typing import Any

import pytest
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError

from src.agents.multi_agent import (
    create_multi_agent,
    invoke_multi_agent,
    resume_multi_agent,
)
from src.agents.recovery import specialist_recovery_middleware
from tests.unit.agents.fakes import ScriptedToolCallingModel

FAILURES_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "failures"


def sources():
    return {
        "user_role": {"identity": "pm_user", "role": "pm"},
        "portfolio_state": {"portfolio_id": "PORT_A"},
        "market_data": {},
        "retrieved_research": {},
        "memory": [],
        "tool_outputs": [],
        "skills": [],
    }


def test_timeout_retries_and_malformed_response_enters_dead_letter():
    timeout_fixture = json.loads((FAILURES_DIR / "research_timeout.json").read_text())
    malformed_fixture = json.loads(
        (FAILURES_DIR / "pricer_malformed_response.json").read_text()
    )
    attempts = {"research": 0}

    @tool("get_research_summary")
    def timeout_research(query: str) -> dict[str, Any]:
        """Retrieve public research."""
        del query
        attempts["research"] += 1
        raise TimeoutError(timeout_fixture["message"])

    @tool("price_bond")
    def malformed_price_bond(
        cash_flows: list[dict[str, float]],
        curve_tenors_years: list[float],
        curve_rates_pct: list[float],
        compounding_frequency: int = 2,
    ) -> dict[str, Any]:
        """Discount bond cash flows."""
        del cash_flows, curve_tenors_years, curve_rates_pct, compounding_frequency
        return malformed_fixture["response"]

    model = ScriptedToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_research_summary",
                        "args": {"query": "issuer"},
                        "id": "research",
                        "type": "tool_call",
                    },
                    {
                        "name": "price_bond",
                        "args": {
                            "cash_flows": [{"time_years": 1, "amount": 105}],
                            "curve_tenors_years": [1],
                            "curve_rates_pct": [4.5],
                            "compounding_frequency": 1,
                        },
                        "id": "bond",
                        "type": "tool_call",
                    },
                ],
            ),
            AIMessage(content="Both failures were reported."),
        ]
    )
    agent = create_agent(
        model=model,
        tools=[timeout_research, malformed_price_bond],
        middleware=specialist_recovery_middleware(initial_delay=0),
    )

    result = agent.invoke({"messages": [{"role": "user", "content": "Run both."}]})

    errors = [
        message for message in result["messages"] if isinstance(message, ToolMessage)
    ]
    payloads = {message.name: json.loads(message.content) for message in errors}
    assert attempts["research"] == 3
    assert all(message.status == "error" for message in errors)
    assert payloads["get_research_summary"]["status"] == "dead_letter"
    assert payloads["get_research_summary"]["retryable"] is True
    assert payloads["price_bond"]["error_type"] == "ToolContractError"
    assert payloads["price_bond"]["retryable"] is False


def test_resume_does_not_rerun_completed_parallel_specialist():
    counts = {"macro": 0, "quant": 0}

    def macro_run(state):
        del state
        counts["macro"] += 1
        return {"messages": [AIMessage(content="Macro completed.")]}

    def quant_run(state):
        del state
        counts["quant"] += 1
        if counts["quant"] == 1:
            raise RuntimeError("deliberate specialist crash")
        return {"messages": [AIMessage(content="Quant recovered.")]}

    parent_model = ScriptedToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "task",
                        "args": {
                            "description": "rates",
                            "subagent_type": "macro",
                        },
                        "id": "macro-task",
                        "type": "tool_call",
                    },
                    {
                        "name": "task",
                        "args": {
                            "description": "risk",
                            "subagent_type": "quant",
                        },
                        "id": "quant-task",
                        "type": "tool_call",
                    },
                ],
            ),
            AIMessage(content="Combined recovered result."),
        ]
    )
    subagents = [
        {
            "name": "macro",
            "description": "macro",
            "runnable": RunnableLambda(macro_run),
        },
        {
            "name": "quant",
            "description": "quant",
            "runnable": RunnableLambda(quant_run),
        },
    ]
    agent = create_multi_agent(
        model=parent_model,
        subagents=subagents,
        checkpointer=InMemorySaver(),
    )

    with pytest.raises(RuntimeError, match="deliberate specialist crash"):
        invoke_multi_agent(
            "Run both.",
            sources(),
            agent=agent,
            thread_id="resume-proof",
        )

    assert counts == {"macro": 1, "quant": 1}

    result = resume_multi_agent(agent, "resume-proof")

    assert counts == {"macro": 1, "quant": 2}
    assert result["messages"][-1].content == "Combined recovered result."


def test_iteration_limit_stops_looping_orchestrator():
    looping_responses = [
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "task",
                    "args": {
                        "description": "repeat",
                        "subagent_type": "macro",
                    },
                    "id": f"loop-{index}",
                    "type": "tool_call",
                }
            ],
        )
        for index in range(10)
    ]
    parent_model = ScriptedToolCallingModel(responses=looping_responses)
    subagents = [
        {
            "name": "macro",
            "description": "macro",
            "runnable": RunnableLambda(
                lambda state: {"messages": [AIMessage(content="done")]}
            ),
        }
    ]
    agent = create_multi_agent(model=parent_model, subagents=subagents)

    with pytest.raises(GraphRecursionError):
        invoke_multi_agent(
            "Loop forever.",
            sources(),
            agent=agent,
            iteration_limit=4,
        )


def test_resume_requires_nonempty_thread_id():
    with pytest.raises(ValueError, match="thread_id must not be empty"):
        resume_multi_agent(object(), "")
