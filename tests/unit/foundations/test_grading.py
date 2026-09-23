"""Grading: the outcome by default, the path only where it is a requirement."""

from src.foundations.agent_loop import (
    ModelTurn,
    ScriptedModel,
    ToolCall,
    demo_tools,
    run_agent,
)
from src.foundations.grading import evaluate, grade_never_executed, grade_outcome


def run(turns, tmp_path):
    return run_agent(
        "3-year yield?",
        ScriptedModel(turns),
        demo_tools(),
        allowed_tools={"interpolate_yield"},
        audit_log=tmp_path / "audit.jsonl",
    )


def call(name, arguments, call_id):
    return ModelTurn(tool_calls=(ToolCall(call_id, name, arguments),))


def test_two_different_valid_paths_both_pass_the_outcome_grader(tmp_path):
    """Grading the path would fail one of these; grading the outcome does not."""
    direct = run(
        [
            call("interpolate_yield", '{"target_tenor_years": 3}', "a"),
            ModelTurn(text="The 3-year yield is 4.3%."),
        ],
        tmp_path,
    )
    roundabout = run(
        [
            call("interpolate_yield", '{"target_tenor_years": 2}', "a"),
            call("interpolate_yield", '{"target_tenor_years": 3}', "b"),
            ModelTurn(text="The 3-year yield is 4.3%."),
        ],
        tmp_path,
    )
    assert direct.tool_calls_requested != roundabout.tool_calls_requested
    for result in (direct, roundabout):
        assert grade_outcome(result, must_contain=["4.3%"]).passed


def test_requesting_a_forbidden_tool_is_not_a_failure_executing_one_would_be(tmp_path):
    result = run(
        [
            call("place_order", '{"ticker": "X", "quantity": 1}', "a"),
            ModelTurn(text="I cannot place orders."),
        ],
        tmp_path,
    )
    assert "place_order" in result.tool_calls_requested
    assert grade_never_executed(result, {"place_order"}).passed


def test_grades_are_reported_separately_not_averaged(tmp_path):
    result = run(
        [
            call("interpolate_yield", '{"target_tenor_years": 3}', "a"),
            ModelTurn(text="The 3-year yield is 4.3%."),
        ],
        tmp_path,
    )
    grades = evaluate(
        result, must_contain=["4.3%"], forbidden={"place_order"}, max_tool_calls=0
    )
    assert {g.name: g.passed for g in grades} == {
        "outcome": True,
        "never_executed": True,
        "budget": False,
        "traceable": True,
    }
