"""AWS-native evaluation planning and comparison helpers.

This module does not call AWS.  It creates a reviewable manifest for an
AgentCore Evaluations run and keeps the local LangSmith evaluator as the
deterministic baseline until a live AgentCore Runtime is deployed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AgentCoreEvaluationPlan:
    dataset: str
    runtime: str
    evaluator_model: str
    dimensions: tuple[str, ...]
    trace_search_required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_evaluation_plan(
    *,
    dataset: str = "evals/golden_dataset.jsonl",
    runtime: str = "config/agentcore.yaml",
    evaluator_model: str = "amazon.nova-lite-v1:0",
) -> AgentCoreEvaluationPlan:
    """Build the same-dataset evaluation manifest used for AWS comparison."""
    if not dataset.strip() or not runtime.strip():
        raise ValueError("dataset and runtime must not be empty")
    if not evaluator_model.strip():
        raise ValueError("evaluator_model must not be empty")
    return AgentCoreEvaluationPlan(
        dataset=dataset,
        runtime=runtime,
        evaluator_model=evaluator_model,
        dimensions=("trajectory", "tool_selection", "response_quality", "policy"),
    )


def compare_evaluation_dimensions(
    langsmith: dict[str, float | None],
    agentcore: dict[str, float | None],
) -> dict[str, dict[str, float | None]]:
    """Align two reports without collapsing distinct quality dimensions."""
    dimensions = sorted(set(langsmith) | set(agentcore))
    return {
        dimension: {
            "langsmith": langsmith.get(dimension),
            "agentcore": agentcore.get(dimension),
        }
        for dimension in dimensions
    }
