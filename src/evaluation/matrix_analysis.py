"""Statistics and promotion-gate analysis for repeated PM evaluation runs."""

from __future__ import annotations

from math import ceil
from statistics import mean, median, stdev
from typing import Any


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, ceil(quantile * len(ordered)) - 1)]


def summarize_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [
        float(run["automated_score"])
        for run in runs
        if run.get("automated_score") is not None
    ]
    latencies = [
        float(run["metrics"]["latency_ms"])
        for run in runs
        if run.get("metrics", {}).get("latency_ms") is not None
    ]
    costs = [
        float(run["metrics"]["estimated_cost_usd"])
        for run in runs
        if run.get("metrics", {}).get("estimated_cost_usd") is not None
    ]
    tokens = [
        float(run["metrics"]["total_tokens"])
        for run in runs
        if run.get("metrics", {}).get("total_tokens") is not None
    ]
    successful = sum(run.get("status") == "pass" for run in runs)
    summary = {
        "run_count": len(runs),
        "success_rate": successful / len(runs) if runs else 0.0,
        "critical_failure_count": sum(
            bool(run.get("critical_failure")) for run in runs
        ),
        "automated_score": {
            "mean": mean(scores) if scores else None,
            "median": median(scores) if scores else None,
            "p95": percentile(scores, 0.95),
            "stdev": stdev(scores) if len(scores) > 1 else 0.0,
        },
        "latency_ms": {
            "mean": mean(latencies) if latencies else None,
            "median": median(latencies) if latencies else None,
            "p95": percentile(latencies, 0.95),
        },
        "total_tokens": {
            "mean": mean(tokens) if tokens else None,
            "median": median(tokens) if tokens else None,
        },
        "estimated_cost_usd": {
            "mean": mean(costs) if costs else None,
            "total": sum(costs) if costs else None,
        },
    }
    total_cost = summary["estimated_cost_usd"]["total"]
    summary["cost_per_successful_run_usd"] = (
        round(total_cost / successful, 10)
        if successful and total_cost is not None
        else None
    )
    return summary


def apply_gates(summary: dict[str, Any], gates: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "minimum_repetitions_for_promotion": summary["run_count"]
        >= gates["minimum_repetitions_for_promotion"],
        "critical_governance_failures": summary["critical_failure_count"]
        <= gates["critical_governance_failures"],
        "minimum_success_rate": summary["success_rate"]
        >= gates["minimum_success_rate"],
        "minimum_automated_score": (summary["automated_score"]["mean"] or 0)
        >= gates["minimum_automated_score"],
        "maximum_p95_latency_ms": (summary["latency_ms"]["p95"] or float("inf"))
        <= gates["maximum_p95_latency_ms"],
    }
    return {"status": "pass" if all(checks.values()) else "fail", "checks": checks}
