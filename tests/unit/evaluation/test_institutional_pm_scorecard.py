import json
from pathlib import Path

from src.evaluation.institutional_pm_scorecard import evaluate_response


def test_scorecard_passes_governed_canonical_shape():
    expected = json.loads(
        Path("experiments/canonical-pm-benchmark/expected_results.json").read_text()
    )
    response = {
        "request_id": "req-1",
        "approval_required": True,
        "order_execution": False,
        "usage": {"input_tokens": 10},
        "latency_ms": 100,
        "workflow_stages": [
            {"stage": stage} for stage in expected["required_workflow_stages"]
        ],
        "capstone": {
            "evaluation": {"status": "pass"},
            "committee_artifact": {
                "status": "pending_human_review",
                "challenge": {
                    "recommendation": "revise_or_decline",
                    "findings": expected["required_findings"],
                },
                "thesis": {
                    "calculations": {
                        "rates": {"portfolio_return_impact": -0.01505},
                        "credit": {"portfolio_return_impact": -0.009},
                    },
                    "claims": [{"evidence_ids": ["SOFR-EVIDENCE"]}],
                },
            },
        },
    }
    manifest = {
        "run_id": "req-1",
        "execution": {
            "provider": "local",
            "model": "fixture",
            "runtime_session_id": "s-1",
        },
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "latency_ms": 100,
        },
        "costs": {"total_estimated_usd": 0.0},
    }

    result = evaluate_response(
        response,
        manifest,
        expected,
        {"response.json", "audit.jsonl", "manifest.json"},
    )

    assert result["status"] == "pass"
    assert result["automated_score"] == 100.0
    assert result["critical_failure"] is False
