from src.evaluation.matrix_analysis import apply_gates, summarize_runs


def test_matrix_summary_reports_percentiles_and_cost_per_success():
    runs = [
        {
            "status": "pass",
            "critical_failure": False,
            "automated_score": 100,
            "metrics": {
                "latency_ms": 100,
                "total_tokens": 10,
                "estimated_cost_usd": 0.1,
            },
        },
        {
            "status": "pass",
            "critical_failure": False,
            "automated_score": 90,
            "metrics": {
                "latency_ms": 200,
                "total_tokens": 20,
                "estimated_cost_usd": 0.2,
            },
        },
    ]

    summary = summarize_runs(runs)

    assert summary["success_rate"] == 1.0
    assert summary["automated_score"]["mean"] == 95
    assert summary["latency_ms"]["p95"] == 200
    assert summary["cost_per_successful_run_usd"] == 0.15


def test_promotion_gate_requires_repeated_runs():
    summary = summarize_runs(
        [
            {
                "status": "pass",
                "critical_failure": False,
                "automated_score": 100,
                "metrics": {"latency_ms": 100},
            }
        ]
    )
    result = apply_gates(
        summary,
        {
            "critical_governance_failures": 0,
            "minimum_success_rate": 0.95,
            "minimum_automated_score": 90,
            "maximum_p95_latency_ms": 15000,
            "minimum_repetitions_for_promotion": 5,
        },
    )

    assert result["status"] == "fail"
    assert result["checks"]["minimum_repetitions_for_promotion"] is False
