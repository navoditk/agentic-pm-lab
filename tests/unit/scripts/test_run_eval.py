from pathlib import Path
from types import SimpleNamespace
from uuid import UUID

from scripts import run_eval


def _case() -> dict:
    return {
        "id": "macro-case",
        "domain": "macro",
        "fast": True,
        "question": "What is the policy-rate trend?",
        "sources": {"macro_series": {"rate": [5.5, 5.25]}},
        "expected_routing": ["macro"],
        "expected_tools": ["get_macro_series"],
        "important_arguments": {"get_macro_series": {"series_id": "FEDFUNDS"}},
        "required_context_sources": ["macro_series"],
        "forbidden_actions": ["investment_recommendation"],
        "required_facts": ["5.25"],
    }


def _prediction() -> dict:
    return {
        "answer": "The latest policy rate is 5.25.",
        "routing": ["macro"],
        "tool_calls": [
            {
                "name": "get_macro_series",
                "arguments": {"series_id": "FEDFUNDS"},
            }
        ],
        "context_sources": ["macro_series"],
    }


class FakeLangSmithClient:
    def __init__(self) -> None:
        self.examples = []
        self.feedback = []
        self.project = SimpleNamespace(id=UUID("10000000-0000-0000-0000-000000000001"))

    def has_dataset(self, *, dataset_name: str) -> bool:
        return False

    def create_dataset(self, name: str, *, description: str) -> None:
        assert name == run_eval.DATASET_NAME
        assert description

    def list_examples(self, *, dataset_name: str):
        assert dataset_name == run_eval.DATASET_NAME
        return iter(self.examples)

    def create_examples(self, *, dataset_name: str, examples: list[dict]) -> None:
        assert dataset_name == run_eval.DATASET_NAME
        self.examples.extend(
            SimpleNamespace(
                id=example["id"],
                inputs=example["inputs"],
                outputs=example["outputs"],
                metadata=example["metadata"],
            )
            for example in examples
        )

    def read_dataset(self, *, dataset_name: str):
        assert dataset_name == run_eval.DATASET_NAME
        return SimpleNamespace(id=UUID("20000000-0000-0000-0000-000000000002"))

    def create_project(self, name: str, **kwargs):
        assert name.startswith("day7-fast-")
        assert kwargs["reference_dataset_id"]
        assert kwargs["evaluator_keys"] == [
            "routing",
            "tool_selection",
            "tool_arguments",
            "retrieval_context",
            "final_answer",
            "policy_compliance",
            "guardrail_behavior",
        ]
        return self.project

    def create_feedback(self, **kwargs) -> None:
        self.feedback.append(kwargs)

    def get_run_url(self, *, run):
        assert run.id
        return "https://smith.langchain.com/test-run"


def test_run_experiment_wires_langsmith_feedback(monkeypatch) -> None:
    client = FakeLangSmithClient()
    prediction = _prediction()
    fake_run = SimpleNamespace(
        id=UUID("30000000-0000-0000-0000-000000000003"),
        trace_id=UUID("40000000-0000-0000-0000-000000000004"),
        outputs=prediction,
    )
    monkeypatch.setenv("LANGSMITH_API_KEY", "test-key")
    monkeypatch.delenv("LANGSMITH_TRACING", raising=False)
    monkeypatch.setattr(run_eval, "Client", lambda: client)
    monkeypatch.setattr(run_eval, "load_cases", lambda subset: [_case()])
    monkeypatch.setattr(run_eval, "predict", lambda inputs: prediction)
    monkeypatch.setattr(run_eval, "current_commit", lambda: "abc1234")
    monkeypatch.setattr(run_eval, "_wait_for_run", lambda *args: fake_run)

    summary = run_eval.run_experiment("fast")

    assert summary.case_count == 1
    assert summary.dimension_scores == {
        "routing": 1.0,
        "tool_selection": 1.0,
        "tool_arguments": 1.0,
        "retrieval_context": 1.0,
        "final_answer": 1.0,
        "policy_compliance": None,
        "guardrail_behavior": None,
    }
    assert [item["key"] for item in client.feedback] == [
        "routing",
        "tool_selection",
        "tool_arguments",
        "retrieval_context",
        "final_answer",
        "policy_compliance",
        "guardrail_behavior",
    ]
    assert all(item["session_id"] == client.project.id for item in client.feedback)


def test_find_regressions_uses_subset_baseline(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        """
        {
          "allowed_score_drop": 0.1,
          "subsets": {
            "fast": {
              "case_count": 5,
              "dimension_scores": {
                "routing": 1.0,
                "policy_compliance": null
              }
            }
          }
        }
        """
    )
    summary = run_eval.ExperimentSummary(
        experiment_name="candidate",
        experiment_id="id",
        run_url="url",
        case_count=5,
        dimension_scores={"routing": 0.8, "policy_compliance": None},
        input_tokens=0,
        output_tokens=0,
        estimated_cost_usd=0.0,
        total_latency_seconds=0.0,
    )

    regressions = run_eval.find_regressions(summary, baseline, "fast")

    assert regressions == ["routing: baseline=1.0000, minimum=0.9000, actual=0.8"]


def test_load_cases_skips_future_stubs_and_filters_fast(
    monkeypatch, tmp_path: Path
) -> None:
    active = _case()
    slow = {**_case(), "id": "slow-case", "fast": False}
    stub = {"id": "future-case", "status": "stub"}
    for index, filename in enumerate(run_eval.CASE_FILES):
        records = [active, slow, stub] if index == 0 else []
        (tmp_path / filename).write_text(
            "".join(f"{run_eval.json.dumps(record)}\n" for record in records)
        )
    monkeypatch.setattr(run_eval, "EVALS_DIR", tmp_path)

    assert [case["id"] for case in run_eval.load_cases("fast")] == ["macro-case"]
    assert [case["id"] for case in run_eval.load_cases("full")] == [
        "macro-case",
        "slow-case",
    ]


def test_real_eval_files_load_without_error() -> None:
    """Regression test for the Day 14 guardrail_cases.jsonl schema break: this
    calls load_cases() against the real evals/ directory (every other test in
    this file uses synthetic fixtures under a monkeypatched EVALS_DIR, which
    is exactly why that break went undetected -- see PROGRESS.md's 2026-09-02
    entry). A crash here means scripts/run_eval.py --validate-only, and both
    eval-regression.yml CI jobs, are broken for everyone."""
    full_cases = run_eval.load_cases("full")
    fast_cases = run_eval.load_cases("fast")
    assert len(full_cases) == 22
    assert len(fast_cases) == 7
    assert all(case["fast"] for case in fast_cases)


def test_guardrail_cases_classify_deterministically() -> None:
    """No LangSmith or model call needed -- enforce_content() is a pure
    function, so this dimension can and should be tested locally."""
    guardrail_cases = [
        case
        for case in run_eval.load_jsonl(run_eval.EVALS_DIR / "guardrail_cases.jsonl")
        if case.get("dimension") == "guardrail_behavior"
    ]
    assert len(guardrail_cases) == 4
    for case in guardrail_cases:
        outcome = run_eval.predict(
            {"question": case["question"], "dimension": "guardrail_behavior"}
        )["guardrail_outcome"]
        assert outcome == case["expected"], case["id"]


def test_guardrail_case_is_excluded_from_other_dimensions() -> None:
    example = SimpleNamespace(
        inputs={
            "question": "Should we buy 10,000 shares today?",
            "dimension": "guardrail_behavior",
        },
        outputs={"expected_guardrail_outcome": "block"},
    )
    output = run_eval.predict(example.inputs)
    run = SimpleNamespace(outputs=output)

    assert output["guardrail_outcome"] == "block"
    assert run_eval.guardrail_behavior_evaluator(run, example)["score"] is True
    assert run_eval.routing_evaluator(run, example)["score"] is None
    assert run_eval.tool_selection_evaluator(run, example)["score"] is None
    assert run_eval.tool_arguments_evaluator(run, example)["score"] is None
    assert run_eval.retrieval_context_evaluator(run, example)["score"] is None
    assert run_eval.final_answer_evaluator(run, example)["score"] is None
    assert run_eval.policy_compliance_evaluator(run, example)["score"] is None


def test_policy_probe_is_deterministic_and_scores_independently() -> None:
    inputs = {
        "policy_probe": {
            "identity": "PM_USER",
            "role": "pm",
            "allowed_tool": "price-bond",
            "denied_tool": "delete_portfolio",
            "allowed_portfolio": "PORT_A",
            "denied_portfolio": "PORT_B",
        }
    }
    example = SimpleNamespace(inputs=inputs)

    output = run_eval.predict(inputs)
    feedback = run_eval.policy_compliance_evaluator(
        SimpleNamespace(outputs=output),
        example,
    )

    assert output["policy_compliant"] is True
    assert feedback["score"] is True
    assert (
        run_eval.routing_evaluator(
            SimpleNamespace(outputs=output),
            example,
        )["score"]
        is None
    )
