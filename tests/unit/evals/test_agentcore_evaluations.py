import pytest

from src.evals.agentcore_evaluations import (
    build_evaluation_plan,
    compare_evaluation_dimensions,
)


def test_plan_reuses_golden_dataset_and_keeps_dimensions_separate() -> None:
    plan = build_evaluation_plan()

    assert plan.dataset == "evals/golden_dataset.jsonl"
    assert "trajectory" in plan.dimensions
    assert plan.trace_search_required is True


def test_comparison_aligns_missing_dimensions_without_aggregate_score() -> None:
    result = compare_evaluation_dimensions(
        {"tool_selection": 1.0, "policy": None},
        {"tool_selection": 0.9, "response_quality": 0.8},
    )

    assert result["tool_selection"] == {"langsmith": 1.0, "agentcore": 0.9}
    assert result["policy"] == {"langsmith": None, "agentcore": None}
    assert result["response_quality"] == {"langsmith": None, "agentcore": 0.8}


def test_plan_rejects_empty_runtime() -> None:
    with pytest.raises(ValueError, match="dataset and runtime"):
        build_evaluation_plan(runtime=" ")
