from langchain_core.messages import AIMessage, ToolMessage

from src.agents.single_agent import create_single_agent, invoke_single_agent
from tests.unit.agents.fakes import ScriptedToolCallingModel


def sources():
    return {
        "user_role": {"identity": "pm_user", "role": "pm"},
        "portfolio_state": {"portfolio_id": "PORT_A"},
        "market_data": {"returns": [0.01, -0.01]},
        "retrieved_research": {"summary": "mock"},
        "memory": [],
        "tool_outputs": [],
        "skills": ["portfolio-risk-summary"],
    }


def test_agent_calls_get_volatility_with_scripted_arguments():
    model = ScriptedToolCallingModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_volatility",
                        "args": {
                            "returns": [0.01, -0.01],
                            "window": 2,
                            "periods_per_year": 1,
                        },
                        "id": "volatility-call",
                        "type": "tool_call",
                    }
                ],
            ),
            AIMessage(content="The tool calculated annualized volatility."),
        ]
    )
    agent = create_single_agent(model=model)

    result = invoke_single_agent(
        "What's my portfolio volatility?",
        sources(),
        agent=agent,
    )

    tool_messages = [
        message for message in result["messages"] if isinstance(message, ToolMessage)
    ]
    assert "get_volatility" in model.bound_tool_names
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "get_volatility"
    assert "0.014142" in tool_messages[0].content


def test_interrupt_policy_can_be_plugged_in_without_changing_agent_callers():
    model = ScriptedToolCallingModel(responses=[AIMessage(content="No tool needed.")])

    agent = create_single_agent(model=model, interrupt_on={"run_backtest": True})

    assert agent is not None


def test_filtered_invocation_excludes_irrelevant_research():
    class PromptCaptureAgent:
        prompt = ""

        def invoke(self, payload, config=None):
            del config
            self.prompt = payload["messages"][0]["content"]
            return {"messages": []}

    agent = PromptCaptureAgent()

    invoke_single_agent(
        "What's my portfolio volatility?",
        sources(),
        agent=agent,
        relevant_sources=["user_role", "market_data", "skills"],
    )

    assert "## market_data" in agent.prompt
    assert "retrieved_research" not in agent.prompt
