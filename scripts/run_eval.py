"""Run the versioned evaluation cases as a scored LangSmith experiment."""

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langsmith import Client, evaluate
from langsmith.schemas import Example, Run

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.agents.multi_agent import invoke_multi_agent

EVALS_DIR = REPO_ROOT / "evals"
DATASET_NAME = "agentic-pm-lab-day6"
CASE_FILES = (
    "golden_dataset.jsonl",
    "routing_cases.jsonl",
    "authorization_cases.jsonl",
    "guardrail_cases.jsonl",
)
REQUIRED_CASE_FIELDS = {
    "id",
    "domain",
    "fast",
    "question",
    "sources",
    "expected_routing",
    "expected_tools",
    "important_arguments",
    "required_context_sources",
    "forbidden_actions",
    "required_facts",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load non-empty JSON objects from one JSON Lines file."""
    records = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise TypeError(f"{path}:{line_number} must contain a JSON object")
        records.append(record)
    return records


def validate_case(case: Mapping[str, Any]) -> list[str]:
    """Return shape errors for one active evaluation case."""
    missing = REQUIRED_CASE_FIELDS - set(case)
    errors = [f"missing field: {field}" for field in sorted(missing)]
    if case.get("domain") not in {
        "macro",
        "quant",
        "fundamental",
        "portfolio_manager",
    }:
        errors.append("domain must name a current agent domain")
    if not isinstance(case.get("sources"), dict):
        errors.append("sources must be an object")
    for field in (
        "expected_routing",
        "expected_tools",
        "required_context_sources",
        "forbidden_actions",
        "required_facts",
    ):
        if not isinstance(case.get(field), list):
            errors.append(f"{field} must be an array")
    return errors


def load_cases(subset: str = "full") -> list[dict[str, Any]]:
    """Load active golden/routing cases and validate every record."""
    cases = []
    for filename in CASE_FILES:
        for case in load_jsonl(EVALS_DIR / filename):
            if case.get("status") == "stub":
                continue
            errors = validate_case(case)
            if errors:
                raise ValueError(f"{case.get('id', filename)}: {'; '.join(errors)}")
            if subset == "fast" and not case["fast"]:
                continue
            cases.append(case)
    return cases


class EvalTraceRecorder(BaseCallbackHandler):
    """Capture nested delegation and tool calls for deterministic evaluators."""

    def __init__(self) -> None:
        self.routing: list[str] = []
        self.tool_calls: list[dict[str, Any]] = []

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        name = serialized.get("name", "")
        inputs = kwargs.get("inputs")
        if not isinstance(inputs, dict):
            try:
                parsed = json.loads(input_str)
            except (json.JSONDecodeError, TypeError):
                parsed = {"raw": input_str}
            inputs = parsed if isinstance(parsed, dict) else {"value": parsed}
        if name == "task":
            specialist = inputs.get("subagent_type")
            if specialist and specialist not in self.routing:
                self.routing.append(str(specialist))
        else:
            self.tool_calls.append({"name": name, "arguments": inputs})


def _message_text(message: Any) -> str:
    text = getattr(message, "text", None)
    if isinstance(text, str):
        return text
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(block.get("text", "")) for block in content if isinstance(block, dict)
        )
    return str(content)


def predict(inputs: dict[str, Any]) -> dict[str, Any]:
    """Run one case through the cloud Portfolio Manager configuration."""
    recorder = EvalTraceRecorder()
    context_sources = inputs["required_context_sources"]
    result = invoke_multi_agent(
        inputs["question"],
        inputs["sources"],
        relevant_sources=context_sources,
        callbacks=[recorder],
    )
    final_message = next(
        (
            message
            for message in reversed(result["messages"])
            if isinstance(message, AIMessage) and _message_text(message)
        ),
        None,
    )
    return {
        "answer": _message_text(final_message) if final_message else "",
        "routing": recorder.routing,
        "tool_calls": recorder.tool_calls,
        "context_sources": context_sources,
    }


def _sets_match(actual: Sequence[str], expected: Sequence[str]) -> bool:
    return set(actual) == set(expected)


def routing_evaluator(run: Run, example: Example) -> dict[str, Any]:
    expected = example.outputs["expected_routing"]
    actual = run.outputs.get("routing", [])
    return {
        "key": "routing",
        "score": _sets_match(actual, expected),
        "comment": f"expected={expected}; actual={actual}",
    }


def tool_selection_evaluator(run: Run, example: Example) -> dict[str, Any]:
    expected = example.outputs["expected_tools"]
    actual = [call["name"] for call in run.outputs.get("tool_calls", [])]
    return {
        "key": "tool_selection",
        "score": _sets_match(actual, expected),
        "comment": f"expected={expected}; actual={actual}",
    }


def _contains_subset(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and _contains_subset(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return actual == expected
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.lower() in actual.lower()
    return actual == expected


def tool_arguments_evaluator(run: Run, example: Example) -> dict[str, Any]:
    expected = example.outputs["important_arguments"]
    actual_calls = run.outputs.get("tool_calls", [])
    actual_by_name = {call["name"]: call.get("arguments", {}) for call in actual_calls}
    matches = all(
        name in actual_by_name
        and _contains_subset(actual_by_name[name], expected_arguments)
        for name, expected_arguments in expected.items()
    )
    return {
        "key": "tool_arguments",
        "score": matches,
        "comment": f"expected subsets={expected}; actual={actual_by_name}",
    }


def context_evaluator(run: Run, example: Example) -> dict[str, Any]:
    expected = example.outputs["required_context_sources"]
    actual = run.outputs.get("context_sources", [])
    return {
        "key": "retrieval_context",
        "score": _sets_match(actual, expected),
        "comment": f"expected={expected}; actual={actual}",
    }


def final_answer_evaluator(run: Run, example: Example) -> dict[str, Any]:
    answer = run.outputs.get("answer", "").lower()
    required = example.outputs["required_facts"]
    missing = [fact for fact in required if str(fact).lower() not in answer]
    forbidden = example.outputs["forbidden_actions"]
    recommendation_terms = ("you should buy", "you should sell", "recommend buying")
    violated = []
    if "investment_recommendation" in forbidden and any(
        term in answer for term in recommendation_terms
    ):
        violated.append("investment_recommendation")
    return {
        "key": "final_answer",
        "score": not missing and not violated and bool(answer),
        "comment": f"missing facts={missing}; forbidden violations={violated}",
    }


def policy_compliance_evaluator(run: Run, example: Example) -> dict[str, Any]:
    del run, example
    return {
        "key": "policy_compliance",
        "score": None,
        "comment": "Stub until Day 7 authorization cases are active.",
    }


def guardrail_evaluator(run: Run, example: Example) -> dict[str, Any]:
    del run, example
    return {
        "key": "guardrail_behavior",
        "score": None,
        "comment": "Stub until Day 12 guardrail cases are active.",
    }


EVALUATORS = (
    routing_evaluator,
    tool_selection_evaluator,
    tool_arguments_evaluator,
    context_evaluator,
    final_answer_evaluator,
    policy_compliance_evaluator,
    guardrail_evaluator,
)


def sync_dataset(client: Client, cases: Sequence[dict[str, Any]]) -> str:
    """Create/update the dedicated LangSmith dataset by stable case ID."""
    if not client.has_dataset(dataset_name=DATASET_NAME):
        client.create_dataset(
            DATASET_NAME,
            description="Day 6 golden and routing cases for agentic-pm-lab.",
        )
    existing = {
        example.metadata.get("case_id"): example
        for example in client.list_examples(dataset_name=DATASET_NAME)
        if example.metadata
    }
    new_examples = []
    for case in cases:
        inputs = {
            "question": case["question"],
            "sources": case["sources"],
            "required_context_sources": case["required_context_sources"],
        }
        outputs = {
            key: case[key]
            for key in (
                "expected_routing",
                "expected_tools",
                "important_arguments",
                "required_context_sources",
                "forbidden_actions",
                "required_facts",
            )
        }
        current = existing.get(case["id"])
        if current is None:
            new_examples.append(
                {
                    "id": uuid5(NAMESPACE_URL, f"{DATASET_NAME}:{case['id']}"),
                    "inputs": inputs,
                    "outputs": outputs,
                    "metadata": {
                        "case_id": case["id"],
                        "domain": case["domain"],
                        "fast": case["fast"],
                    },
                }
            )
        else:
            client.update_example(
                current.id,
                inputs=inputs,
                outputs=outputs,
                metadata={
                    "case_id": case["id"],
                    "domain": case["domain"],
                    "fast": case["fast"],
                },
            )
    if new_examples:
        client.create_examples(dataset_name=DATASET_NAME, examples=new_examples)
    return DATASET_NAME


def current_commit() -> str:
    """Return the short commit used by the experiment configuration."""
    return subprocess.check_output(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
    ).strip()


def run_experiment(subset: str = "full") -> Any:
    """Synchronize cases and execute one LangSmith experiment."""
    if not os.getenv("LANGSMITH_API_KEY"):
        raise RuntimeError("LANGSMITH_API_KEY is required for a real experiment")
    cases = load_cases(subset)
    client = Client()
    dataset_name = sync_dataset(client, cases)
    selected_ids = {case["id"] for case in cases}
    examples = [
        example
        for example in client.list_examples(dataset_name=dataset_name)
        if example.metadata and example.metadata.get("case_id") in selected_ids
    ]
    return evaluate(
        predict,
        data=examples,
        evaluators=EVALUATORS,
        experiment_prefix=f"day6-{subset}",
        description="Portfolio Manager quality baseline by independent dimension.",
        metadata={
            "git_commit": current_commit(),
            "model": "gpt-4.1-mini",
            "subset": subset,
        },
        max_concurrency=1,
        client=client,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", choices=("fast", "full"), default="full")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate local case files without calling LangSmith or a model.",
    )
    args = parser.parse_args()
    cases = load_cases(args.subset)
    if args.validate_only:
        print(f"{len(cases)} active {args.subset} evaluation case(s) are valid.")
        return 0
    results = run_experiment(args.subset)
    print(f"Experiment complete: {results.experiment_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
