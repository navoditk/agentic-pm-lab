"""The same loop in LangChain: what the framework generates, and what it
does not take over."""

import json

import pytest
from langchain_core.messages import AIMessage

from src.foundations.langchain_loop import (
    CallCounter,
    ScriptedToolModel,
    YieldAnswer,
    interpolate_yield,
    place_order,
    run_langchain_agent,
    structured_answer,
)


def scripted(*messages):
    return ScriptedToolModel(messages=iter(messages))


def tool_call(name, args, call_id="c1"):
    return AIMessage(
        content="", tool_calls=[{"name": name, "args": args, "id": call_id}]
    )


def test_the_tool_decorator_generates_schema_from_type_hints_and_docstring():
    schema = interpolate_yield.args_schema.model_json_schema()
    assert schema["properties"]["target_tenor_years"]["type"] == "number"
    assert schema["required"] == ["target_tenor_years"]
    assert interpolate_yield.description.startswith("Interpolate the demo yield")


def test_the_generated_schema_rejects_arguments_that_do_not_fit():
    with pytest.raises(Exception, match="validation error"):
        interpolate_yield.invoke({"target_tenor_years": "three"})


def test_the_langchain_loop_uses_tool_messages_linked_by_call_id(tmp_path):
    result = run_langchain_agent(
        "3-year yield?",
        scripted(
            tool_call("interpolate_yield", {"target_tenor_years": 3}),
            AIMessage(content="4.3%"),
        ),
        [interpolate_yield, place_order],
        allowed_tools={"interpolate_yield"},
        audit_log=tmp_path / "audit.jsonl",
    )
    tool_entry = result.transcript[2]
    assert tool_entry["role"] == "tool"
    assert json.loads(tool_entry["content"]) == {"result": pytest.approx(4.3)}
    assert result.answer == "4.3%"


def test_governance_stays_in_your_code_under_a_framework(tmp_path):
    result = run_langchain_agent(
        "Buy it.",
        scripted(
            tool_call("place_order", {"ticker": "X", "quantity": 1}),
            AIMessage(content="I cannot place orders."),
        ),
        [interpolate_yield, place_order],
        allowed_tools={"interpolate_yield"},
        audit_log=tmp_path / "audit.jsonl",
    )
    assert [(r["tool_name"], r["decision"]) for r in result.audit] == [
        ("place_order", "denied")
    ]
    assert result.audit[0]["trace_id"] == result.trace_id


def test_callbacks_fire_once_per_model_call(tmp_path):
    counter = CallCounter()
    run_langchain_agent(
        "3-year yield?",
        scripted(
            tool_call("interpolate_yield", {"target_tenor_years": 3}),
            AIMessage(content="4.3%"),
        ),
        [interpolate_yield],
        allowed_tools={"interpolate_yield"},
        audit_log=tmp_path / "audit.jsonl",
        callbacks=[counter],
    )
    assert counter.model_starts == counter.model_ends == 2


def test_structured_output_returns_a_validated_object_not_prose():
    answer = structured_answer(
        scripted(
            tool_call(
                "YieldAnswer",
                {"tenor_years": 3, "yield_pct": 4.3, "source": "demo curve"},
            )
        ),
        "3-year yield?",
    )
    assert answer == YieldAnswer(tenor_years=3, yield_pct=4.3, source="demo curve")


def test_the_stock_fake_model_cannot_bind_tools():
    """Why ScriptedToolModel exists: checked, not assumed."""
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

    with pytest.raises(NotImplementedError):
        GenericFakeChatModel(messages=iter([])).bind_tools([interpolate_yield])
