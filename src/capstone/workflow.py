"""Reproducible institutional PM capstone replay.

This is the local proof-of-concept path for Day 20. It deliberately separates
structured calculations from cited research evidence and records the versions,
authorization, audit, evaluation, and approval state needed for a later live
AgentCore run.
"""

from datetime import date
from pathlib import Path
from time import perf_counter
from typing import Any

from src.agents.devils_advocate import run_committee_challenge
from src.analytics.pricers import CashFlow, price_bond
from src.analytics.scenario import scenario_analysis
from src.control.audit import record_audit_event
from src.control.authorization import check_portfolio_access
from src.control.identity import role_for_identity
from src.ingestion.fixed_income import validate_bond_instrument
from src.ingestion.provenance import eligible_as_of, make_observation
from src.observability.telemetry import observe_operation
from src.research.provider import mocked_thematic_screen

CAPSTONE_VERSIONS = {
    "data_version": "public-fixtures-2026-08-12-v1",
    "model_version": "deterministic-local-replay-v1",
    "prompt_version": "institutional-pm-capstone-v1",
    "policy_version": "cedar-local-v1",
}


def _trace_id() -> str:
    """Return the active OTel trace id when a provider is recording one."""
    from opentelemetry import trace

    context = trace.get_current_span().get_span_context()
    return format(context.trace_id, "032x") if context.is_valid else "0" * 32


def _run_stage(
    events: list[dict[str, Any]],
    name: str,
    component: str,
    operation: Any,
) -> Any:
    """Run one capstone stage and record safe, inspectable execution metadata."""
    started = perf_counter()
    event: dict[str, Any] = {
        "stage": name,
        "component": component,
        "status": "running",
        "trace_id": _trace_id(),
    }
    events.append(event)
    try:
        result = operation()
    except Exception as error:
        event.update(
            {
                "status": "failed",
                "error_type": type(error).__name__,
                "error": str(error),
            }
        )
        raise
    else:
        event["status"] = "completed"
        return result
    finally:
        event["duration_ms"] = round((perf_counter() - started) * 1000, 3)


def run_institutional_pm_capstone(
    *,
    identity: str,
    portfolio_id: str,
    decision_date: str,
    audit_log_path: Path,
    human_reviewer: str | None = None,
    approval: str | None = None,
) -> dict[str, Any]:
    """Run the full local PM/research/committee workflow."""
    execution_trace: list[dict[str, Any]] = []
    _validate_date(decision_date)

    with observe_operation(
        "capstone.institutional_pm_review",
        "workflow",
        {"app.auth.identity": identity, "app.portfolio.id": portfolio_id},
    ):
        _run_stage(
            execution_trace,
            "authenticate_and_authorize",
            "control",
            lambda: _authenticate_and_authorize(identity, portfolio_id, audit_log_path),
        )
        observations = _run_stage(
            execution_trace,
            "load_structured_observations",
            "data",
            _structured_observations,
        )
        freshness = _run_stage(
            execution_trace,
            "point_in_time_freshness",
            "provenance",
            lambda: _check_freshness(observations, decision_date),
        )
        evidence = _run_stage(
            execution_trace,
            "retrieve_cited_research",
            "research",
            lambda: mocked_thematic_screen(
                "funding pressure and credit outlook",
                entity="Issuer A",
                publication_time="2026-08-12T08:00:00Z",
                retrieval_time="2026-08-13T08:00:00Z",
                novelty=0.8,
            ),
        )
        bond = _run_stage(
            execution_trace, "fixed_income_validation", "quant", _fixed_income_review
        )
        rates_scenario = _run_stage(
            execution_trace,
            "rates_scenario",
            "quant",
            lambda: scenario_analysis(
                [
                    {"security_id": "BOND_A", "weight": 0.40, "duration": 5.2},
                    {"security_id": "CREDIT_A", "weight": 0.30, "duration": 3.1},
                ],
                "rates",
                50,
                horizon="overnight",
            ),
        )
        credit_scenario = _run_stage(
            execution_trace,
            "credit_scenario",
            "quant",
            lambda: scenario_analysis(
                [
                    {"security_id": "CREDIT_A", "weight": 0.30, "spread_duration": 4.0},
                ],
                "credit",
                75,
                horizon="overnight",
            ),
        )
        hedge = _run_stage(
            execution_trace,
            "human_review_only_hedge",
            "portfolio",
            lambda: _duration_hedge_proposal(
                target_duration=0.40 * 5.2 + 0.30 * 3.1, hedge_duration=7.0
            ),
        )
        thesis = _run_stage(
            execution_trace,
            "draft_evidence_linked_thesis",
            "supervisor",
            lambda: _draft_thesis(
                rates_scenario, credit_scenario, evidence, bond, hedge
            ),
        )
        committee = _run_stage(
            execution_trace,
            "devils_advocate_committee_challenge",
            "governance",
            lambda: run_committee_challenge(
                thesis,
                decision_date=decision_date,
                human_reviewer=human_reviewer,
                approval=approval,
            ),
        )
        evaluation = _run_stage(
            execution_trace,
            "evaluate_and_prepare_review",
            "evaluation",
            lambda: _evaluate_capstone(
                freshness=freshness,
                evidence=evidence,
                bond=bond,
                rates_scenario=rates_scenario,
                committee=committee,
            ),
        )
        _run_stage(
            execution_trace,
            "write_audit_event",
            "audit",
            lambda: record_audit_event(
                identity,
                role_for_identity(identity) or "unknown",
                "institutional_pm_capstone",
                "allowed",
                "Tool",
                resource_id=portfolio_id,
                log_path=audit_log_path,
            ),
        )
        return {
            "workflow": [
                "authenticated_pm_request",
                "freshness_check",
                "macro_quant_fundamental_research_evidence",
                "deterministic_fixed_income_scenarios",
                "devils_advocate_challenge",
                "cited_committee_artifact",
                "human_review",
                "otel_audit_evaluation_metadata",
            ],
            "identity": identity,
            "portfolio_id": portfolio_id,
            "decision_date": decision_date,
            "freshness": freshness,
            "provenance_paths": {
                "structured_calculations": {
                    "observations": observations,
                    "rates_scenario": rates_scenario,
                    "credit_scenario": credit_scenario,
                    "fixed_income": bond,
                    "hedge": hedge,
                },
                "unstructured_evidence": [evidence],
            },
            "committee_artifact": committee,
            "evaluation": evaluation,
            "versions": dict(CAPSTONE_VERSIONS),
            "production_oriented_poc": True,
            "order_execution": False,
            "live_provider_evidence": False,
            "execution_trace": execution_trace,
            "trace_id": _trace_id(),
            "reasoning_artifact": {
                "type": "structured_execution_trace",
                "private_chain_of_thought_captured": False,
                "note": "The trace exposes stages, tools, policy outcomes, evidence, failures, and outputs without exposing private model chain-of-thought.",
            },
        }


def _authenticate_and_authorize(
    identity: str, portfolio_id: str, audit_path: Path
) -> None:
    role = role_for_identity(identity)
    if role is None:
        record_audit_event(
            identity,
            "unknown",
            "institutional_pm_capstone",
            "denied",
            "AuthN",
            log_path=audit_path,
        )
        raise PermissionError("identity is not recognized")
    if not check_portfolio_access(identity, portfolio_id):
        record_audit_event(
            identity,
            role,
            "institutional_pm_capstone",
            "denied",
            "AuthZ",
            resource_id=portfolio_id,
            log_path=audit_path,
        )
        raise PermissionError(f"{identity} is not authorized for {portfolio_id}")


def _structured_observations() -> list[dict[str, Any]]:
    return [
        make_observation(
            source="public-fixture-treasury",
            series_id="TREASURY_CURVE",
            observation_date="2026-08-12",
            release_date="2026-08-12",
            value=4.2,
            unit="percent",
            vintage="2026-08-12",
            source_url="https://home.treasury.gov/",
        ),
        make_observation(
            source="public-fixture-sofr",
            series_id="SOFR",
            observation_date="2026-08-12",
            release_date="2026-08-12",
            value=5.3,
            unit="percent",
            vintage="2026-08-12",
            source_url="https://www.newyorkfed.org/markets/reference-rates/sofr",
        ),
    ]


def _check_freshness(
    observations: list[dict[str, Any]], decision_date: str
) -> dict[str, Any]:
    results = []
    for observation in observations:
        results.append(
            {
                "series_id": observation["series_id"],
                "eligible": eligible_as_of(observation, decision_date),
                "release_date": observation["release_date"],
                "vintage": observation["vintage"],
            }
        )
    return {
        "status": "pass"
        if all(item["eligible"] for item in results)
        else "needs_review",
        "observations": results,
    }


def _fixed_income_review() -> dict[str, Any]:
    instrument = {
        "security_id": "BOND_A",
        "issuer": "Issuer A",
        "currency": "USD",
        "issue_date": "2024-01-01",
        "maturity_date": "2034-01-01",
        "coupon_rate": 0.05,
        "coupon_frequency": 2,
        "day_count": "30/360",
        "settlement_lag_days": 2,
    }
    validation = validate_bond_instrument(instrument)
    if validation["status"] != "valid":
        raise ValueError("bond instrument requires review before valuation")
    clean = price_bond(
        [CashFlow(time_years=0.5, amount=2.5), CashFlow(time_years=1.0, amount=102.5)],
        [0.5, 1.0],
        [4.0, 4.2],
        compounding_frequency=2,
    )
    accrued_interest = 2.5 * 30 / 180
    return {
        "instrument": instrument,
        "validation": validation,
        "clean_price": clean["price"],
        "accrued_interest": accrued_interest,
        "dirty_price": clean["price"] + accrued_interest,
        "price_assumptions": [
            "Par 100; semiannual 5% coupon; 30/360 accrual; 30 days since coupon."
        ],
        "liquidity_review": "needs_review",
        "rating_exposure": "mock security master",
    }


def _duration_hedge_proposal(
    *, target_duration: float, hedge_duration: float
) -> dict[str, Any]:
    if hedge_duration <= 0:
        raise ValueError("hedge_duration must be positive")
    return {
        "instrument": "Treasury hedge fixture",
        "target_duration": target_duration,
        "hedge_duration": hedge_duration,
        "proposed_weight": target_duration / hedge_duration,
        "action": "human_review_only",
        "order_generated": False,
        "assumptions": [
            "Linear duration matching; basis, convexity, roll, margin, and liquidity require review."
        ],
    }


def _draft_thesis(
    rates: dict[str, Any],
    credit: dict[str, Any],
    evidence: dict[str, Any],
    bond: dict[str, Any],
    hedge: dict[str, Any],
) -> dict[str, Any]:
    return {
        "thesis_id": "CAPSTONE-THESIS-001",
        "claims": [
            {
                "claim_id": "rates",
                "text": "A 50 bps rates shock is material but duration matching may reduce exposure.",
                "evidence_ids": ["SOFR-EVIDENCE"],
                "causal": False,
            },
            {
                "claim_id": "credit",
                "text": "Credit funding pressure supports reducing the credit sleeve.",
                "evidence_ids": ["THEMATIC-EVIDENCE"],
                "causal": True,
            },
        ],
        "evidence": [
            {
                "evidence_id": "SOFR-EVIDENCE",
                "publication_date": "2026-08-12",
                "contradicts_claim": False,
                "supports_causality": False,
            },
            {
                "evidence_id": "THEMATIC-EVIDENCE",
                "publication_date": "2026-08-12",
                "contradicts_claim": False,
                "supports_causality": False,
                "provider": evidence["provider"],
            },
        ],
        "allocation": [
            {
                "security_id": "BOND_A",
                "weight": 0.40,
                "liquidity_status": bond["liquidity_review"],
            },
            {"security_id": "CREDIT_A", "weight": 0.30, "liquidity_status": "unknown"},
        ],
        "invalidation_conditions": [
            "Funding conditions normalize and credit spreads tighten."
        ],
        "calculations": {"rates": rates, "credit": credit, "hedge": hedge},
    }


def _evaluate_capstone(
    *,
    freshness: dict[str, Any],
    evidence: dict[str, Any],
    bond: dict[str, Any],
    rates_scenario: dict[str, Any],
    committee: dict[str, Any],
) -> dict[str, Any]:
    dimensions = {
        "authorization": True,
        "freshness": freshness["status"] == "pass",
        "structured_calculation": bool(rates_scenario["position_impacts"]),
        "unstructured_citation": bool(evidence["evidence"]["source_url"]),
        "bond_validation": bond["validation"]["status"] == "valid",
        "committee_challenge": committee["challenge"]["status"]
        in {"challenged", "no_findings"},
        "human_review_required": committee["status"] == "pending_human_review",
    }
    return {
        "status": "pass" if all(dimensions.values()) else "needs_review",
        "dimensions": dimensions,
        "unresolved": [name for name, passed in dimensions.items() if not passed],
    }


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO decision_date: {value}") from exc
