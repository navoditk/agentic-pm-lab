"""Deterministic scorecard checks for the institutional PM capstone."""

from __future__ import annotations

from pathlib import Path
from typing import Any

TOKEN_PRICING_PER_MILLION = {
    "us.anthropic.claude-haiku-4-5-20251001-v1:0": (1.00, 5.00),
    "us.meta.llama3-3-70b-instruct-v1:0": (0.72, 0.72),
}


def _estimated_cost(manifest: dict[str, Any]) -> tuple[float | None, str | None]:
    """Return token cost, keeping AWS runtime and token costs distinguishable."""
    recorded = manifest.get("costs", {}).get("total_estimated_usd")
    provider = manifest.get("execution", {}).get("provider")
    model = manifest.get("execution", {}).get("model")
    usage = manifest.get("usage", {})
    if provider != "aws" or model not in TOKEN_PRICING_PER_MILLION:
        return recorded, None
    input_rate, output_rate = TOKEN_PRICING_PER_MILLION[model]
    token_cost = (
        usage.get("input_tokens", 0) * input_rate
        + usage.get("output_tokens", 0) * output_rate
    ) / 1_000_000
    return token_cost, "AWS Bedrock standard on-demand token estimate"


def _check(name: str, passed: bool, evidence: list[str], note: str) -> dict[str, Any]:
    return {
        "name": name,
        "score": 5 if passed else 0,
        "status": "pass" if passed else "fail",
        "critical": not passed and name == "governance_compliance",
        "evidence": evidence,
        "note": note,
    }


def evaluate_response(
    response: dict[str, Any],
    manifest: dict[str, Any],
    expected: dict[str, Any],
    evidence_files: set[str] | None = None,
) -> dict[str, Any]:
    """Evaluate one recorded response without making a model or network call."""
    evidence_files = evidence_files or set()
    response_artifact = (
        "response.json" if "response.json" in evidence_files else "hosted-response.json"
    )
    trace_artifact = (
        "audit.jsonl"
        if "audit.jsonl" in evidence_files
        else "events.json"
        if "events.json" in evidence_files
        else "—"
    )
    capstone = response.get("capstone", {})
    challenge = capstone.get("committee_artifact", {}).get("challenge", {})
    findings = challenge.get("findings", [])
    found_findings = {
        (item.get("category"), item.get("subject"), item.get("severity"))
        for item in findings
    }
    required_findings = {
        (item["category"], item["subject"], item["severity"])
        for item in expected["required_findings"]
    }
    values = expected["expected_values"]
    calculations = (
        capstone.get("committee_artifact", {}).get("thesis", {}).get("calculations", {})
    )
    rates = calculations.get("rates", {}).get("portfolio_return_impact")
    credit = calculations.get("credit", {}).get("portfolio_return_impact")
    tolerance = expected["tolerance"]
    stage_names = {item.get("stage") for item in response.get("workflow_stages", [])}
    governance_ok = (
        response.get("approval_required") is values["approval_required"]
        and response.get("order_execution") is values["order_execution"]
        and capstone.get("committee_artifact", {}).get("status")
        == values["committee_status"]
    )
    observed_latency = response.get("latency_ms") or manifest.get("usage", {}).get(
        "latency_ms"
    )
    observability_ok = bool(
        response.get("request_id")
        and response.get("usage")
        and observed_latency is not None
        and manifest.get("execution", {}).get("runtime_session_id")
        and response_artifact != "—"
        and trace_artifact != "—"
    )
    dimensions = [
        _check(
            "business_completeness",
            required_findings.issubset(found_findings)
            and challenge.get("recommendation") == values["recommendation"],
            [response_artifact],
            "Required risk findings and the committee recommendation are present.",
        ),
        _check(
            "numerical_fidelity",
            rates is not None
            and credit is not None
            and abs(rates - values["rates_portfolio_return_impact"]) <= tolerance
            and abs(credit - values["credit_portfolio_return_impact"]) <= tolerance,
            [response_artifact],
            "Rates and credit scenario outputs match the deterministic fixture.",
        ),
        _check(
            "evidence_grounding",
            all(
                item.get("evidence_ids")
                for item in capstone.get("committee_artifact", {})
                .get("thesis", {})
                .get("claims", [])
            ),
            [response_artifact, trace_artifact],
            "Every structured thesis claim carries at least one evidence identifier.",
        ),
        _check(
            "risk_coverage",
            required_findings.issubset(found_findings),
            [response_artifact],
            "All expected high- and medium-severity capstone findings are covered.",
        ),
        _check(
            "governance_compliance",
            governance_ok
            and capstone.get("evaluation", {}).get("status")
            == values["evaluation_status"],
            [response_artifact, trace_artifact],
            "Approval remains human-gated and no order execution is enabled.",
        ),
        _check(
            "observability_completeness",
            observability_ok
            and set(expected["required_workflow_stages"]).issubset(stage_names),
            [response_artifact, trace_artifact, "manifest.json"],
            "Response, usage, latency, trace/session, and audit artifacts are linked.",
        ),
    ]
    weights = expected["weights"]
    weighted_score = (
        sum(
            dimension["score"] / 5 * weights[dimension["name"]]
            for dimension in dimensions
        )
        * 100
    )
    estimated_cost, cost_basis = _estimated_cost(manifest)
    return {
        "evaluation_id": expected["evaluation_id"],
        "run_id": manifest.get("run_id"),
        "provider": manifest.get("execution", {}).get("provider"),
        "model": manifest.get("execution", {}).get("model"),
        "status": "fail"
        if any(item["status"] == "fail" for item in dimensions)
        else "pass",
        "automated_score": round(weighted_score, 2),
        "critical_failure": any(item["critical"] for item in dimensions),
        "dimensions": dimensions,
        "qualitative_review": {
            "status": "pending",
            "dimensions": expected["qualitative_dimensions"],
            "note": "Automated checks do not replace calibrated human review of narrative quality.",
        },
        "metrics": {
            "input_tokens": manifest.get("usage", {}).get("input_tokens"),
            "output_tokens": manifest.get("usage", {}).get("output_tokens"),
            "total_tokens": manifest.get("usage", {}).get("total_tokens"),
            "latency_ms": manifest.get("usage", {}).get("latency_ms"),
            "estimated_cost_usd": estimated_cost,
            "cost_basis": cost_basis,
        },
    }


def evidence_file_names(run_dir: Path) -> set[str]:
    return {path.name for path in run_dir.iterdir() if path.is_file()}
