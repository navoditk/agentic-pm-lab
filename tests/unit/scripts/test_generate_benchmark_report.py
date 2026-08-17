import json
from pathlib import Path

from scripts.generate_benchmark_report import render


def test_report_separates_exact_and_related_runs(tmp_path: Path):
    benchmark = {
        "benchmark_id": "test",
        "title": "Test benchmark",
        "version": "1",
        "status": "partial",
        "business_question": "Test question",
        "business_objective": "Test objective",
        "input_contract": {
            "identity": "PM_USER",
            "portfolio_id": "PORT_A",
            "decision_date": "2026-08-13",
            "data_policy": "mock",
            "required_controls": [],
        },
        "workflow_stages": ["request_received", "response_emitted"],
        "benchmark_modes": [
            {
                "name": "controlled",
                "purpose": "same evidence",
                "model_responsibility": "summary",
            },
            {
                "name": "agentic",
                "purpose": "same tools",
                "model_responsibility": "tools",
            },
        ],
        "evaluation_dimensions": ["latency"],
        "providers": [
            {
                "provider": "x",
                "model": "exact",
                "surface": "api",
                "alignment": "canonical_exact",
                "status": "observed",
                "input_tokens": 1,
                "output_tokens": 2,
                "total_tokens": 3,
                "latency_ms": 1000,
                "estimated_cost_usd": 0.1,
                "observability": ["OTel"],
                "governance": "safe",
                "source": "x",
            },
            {
                "provider": "y",
                "model": "related",
                "surface": "local",
                "alignment": "related_historical_run",
                "status": "observed",
                "input_tokens": None,
                "output_tokens": None,
                "total_tokens": None,
                "latency_ms": None,
                "estimated_cost_usd": 0.0,
                "observability": ["notes"],
                "governance": "not scored",
                "source": "y",
            },
        ],
        "known_gaps": ["rerun related"],
    }
    report = render(benchmark)
    assert "Observed exact-capstone providers: **1**" in report
    assert "canonical_exact" in report
    assert "related_historical_run" in report
    assert "not a quality leaderboard" in report
    assert json.dumps(benchmark["providers"][0]) not in report
