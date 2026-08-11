import pytest
from langchain_core.messages import AIMessage, ToolMessage

from src.agents import multi_agent_local
from src.agents.multi_agent import (
    create_multi_agent,
    invoke_multi_agent,
    specialist_subagents,
)
from tests.unit.agents.fakes import ScriptedToolCallingModel


def sources():
    return {
        "user_role": {"identity": "pm_user", "role": "pm"},
        "portfolio_state": {"portfolio_id": "PORT_A"},
        "market_data": {"returns": [0.01, -0.01]},
        "retrieved_research": {"summary": "mock"},
        "memory": [],
        "tool_outputs": [],
        "skills": ["scenario-analysis"],
    }


ROUTING_CASES = [
    (
        "macro",
        "interpolate_curve",
        {
            "tenors_years": [1, 2],
            "rates_pct": [4, 5],
            "target_tenors_years": [1.5],
        },
        "Are we exposed to yield-curve steepening?",
    ),
    (
        "quant",
        "get_volatility",
        {
            "returns": [0.01, -0.01],
            "window": 2,
            "periods_per_year": 12,
        },
        "What is driving current volatility?",
    ),
    (
        "fundamental",
        "get_research_summary",
        {"query": "Issuer A sentiment"},
        "Which holdings have deteriorating sentiment?",
    ),
]


@pytest.mark.parametrize(
    ("specialist_name", "tool_name", "tool_args", "question"),
    ROUTING_CASES,
)
def test_portfolio_manager_routes_each_domain_to_its_specialist(
    specialist_name,
    tool_name,
    tool_args,
    question,
):
    parent_model = ScriptedToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "task",
                        "args": {
                            "description": f"Use {tool_name} with {tool_args}.",
                            "subagent_type": specialist_name,
                        },
                        "id": f"{specialist_name}-task",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content=f"Synthesized {specialist_name} result."),
        ]
    )
    specialist_models = {
        name: ScriptedToolCallingModel(responses=[AIMessage(content="Unused.")])
        for name in ("macro", "quant", "fundamental")
    }
    routed_model = ScriptedToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": tool_name,
                        "args": tool_args,
                        "id": f"{tool_name}-call",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content=f"{specialist_name} completed."),
        ]
    )
    specialist_models[specialist_name] = routed_model
    agent = create_multi_agent(
        model=parent_model,
        specialist_models=specialist_models,
    )

    result = invoke_multi_agent(question, sources(), agent=agent)

    task_messages = [
        message for message in result["messages"] if isinstance(message, ToolMessage)
    ]
    assert len(task_messages) == 1
    assert task_messages[0].name == "task"
    assert routed_model.response_index == 2
    assert tool_name in routed_model.bound_tool_names
    assert all(
        model.response_index == 0
        for name, model in specialist_models.items()
        if name != specialist_name
    )


def test_specialists_have_domain_specific_tool_boundaries():
    specs = {spec["name"]: spec for spec in specialist_subagents()}

    assert {tool.name for tool in specs["macro"]["tools"]} == {
        "interpolate_curve",
        "price_bond",
    }
    assert {tool.name for tool in specs["quant"]["tools"]} == {
        "get_volatility",
        "get_max_drawdown",
        "get_risk_metrics",
        "run_factor_regression",
        "run_backtest",
    }
    assert {tool.name for tool in specs["fundamental"]["tools"]} == {
        "get_portfolio_exposure",
        "get_research_summary",
    }
    assert specs["quant"]["skills"] == ["./skills/scenario-analysis/"]


def test_local_variant_creates_separate_models_for_the_hierarchy(monkeypatch):
    created_models = []

    def fake_local_model(model_name):
        model = ScriptedToolCallingModel(responses=[AIMessage(content=model_name)])
        created_models.append(model)
        return model

    monkeypatch.setattr(multi_agent_local, "_local_model", fake_local_model)

    agent = multi_agent_local.create_local_multi_agent("local-test")

    assert agent.name == "portfolio-manager"
    assert len(created_models) == 4
