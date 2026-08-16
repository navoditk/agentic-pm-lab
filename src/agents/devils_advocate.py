"""Independent thesis challenge and investment-committee workflow."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langgraph.graph.state import CompiledStateGraph

from src.control.identity import role_for_identity

CHALLENGE_CATEGORIES = (
    "missing_evidence",
    "contradictory_data",
    "stale_sources",
    "concentration_risk",
    "liquidity_risk",
    "unsupported_causality",
    "invalidation_conditions",
)

DEVILS_ADVOCATE_PROMPT = """You are an independent Devil's Advocate.
You receive a draft investment thesis, proposed allocation, calculations, and
evidence bundle. Attempt to disprove the thesis. Identify missing evidence,
contradictory data, stale sources, concentration or liquidity risks,
unsupported causal claims, and conditions that would invalidate it. Preserve
uncertainty and cite the supplied evidence IDs. You are read-only: never change
the allocation, approve the committee artifact, or present your critique as an
investment recommendation. A separate human reviewer owns approval.
"""


def challenge_thesis(
    thesis: dict[str, Any],
    *,
    decision_date: str,
    max_source_age_days: int = 30,
    max_position_weight: float = 0.25,
) -> dict[str, Any]:
    """Produce a deterministic, evidence-linked challenge report."""
    _validate_date(decision_date)
    if max_source_age_days < 0:
        raise ValueError("max_source_age_days must be non-negative")
    if not 0 < max_position_weight <= 1:
        raise ValueError("max_position_weight must be between 0 and 1")

    claims = thesis.get("claims", [])
    evidence = thesis.get("evidence", [])
    allocation = thesis.get("allocation", [])
    if not isinstance(claims, list) or not isinstance(evidence, list):
        raise TypeError("claims and evidence must be lists")

    evidence_by_id = {
        item.get("evidence_id"): item
        for item in evidence
        if isinstance(item, dict) and item.get("evidence_id")
    }
    findings: list[dict[str, Any]] = []
    covered: set[str] = set()

    for claim in claims:
        if not isinstance(claim, dict):
            continue
        claim_id = str(claim.get("claim_id", "unknown"))
        linked = [
            evidence_by_id[item]
            for item in claim.get("evidence_ids", [])
            if item in evidence_by_id
        ]
        if not linked:
            covered.add("missing_evidence")
            findings.append(
                _finding(
                    "missing_evidence",
                    "high",
                    claim_id,
                    "Claim has no linked evidence.",
                )
            )
        if any(item.get("contradicts_claim") is True for item in linked):
            covered.add("contradictory_data")
            findings.append(
                _finding(
                    "contradictory_data",
                    "high",
                    claim_id,
                    "Linked evidence contradicts the claim.",
                )
            )
        if claim.get("causal") is True and not any(
            item.get("supports_causality") is True for item in linked
        ):
            covered.add("unsupported_causality")
            findings.append(
                _finding(
                    "unsupported_causality",
                    "high",
                    claim_id,
                    "Causal claim lacks explicit causal evidence.",
                )
            )

    decision = date.fromisoformat(decision_date)
    for item in evidence:
        if not isinstance(item, dict):
            continue
        published = item.get("publication_date")
        if published:
            age = (decision - date.fromisoformat(str(published))).days
            if age > max_source_age_days:
                covered.add("stale_sources")
                findings.append(
                    _finding(
                        "stale_sources",
                        "medium",
                        item.get("evidence_id", "unknown"),
                        f"Source is {age} days old.",
                    )
                )

    for position in allocation:
        if not isinstance(position, dict):
            continue
        weight = float(position.get("weight", 0))
        if weight > max_position_weight:
            covered.add("concentration_risk")
            findings.append(
                _finding(
                    "concentration_risk",
                    "high",
                    position.get("security_id", "unknown"),
                    f"Weight {weight:.2%} exceeds {max_position_weight:.2%}.",
                )
            )
        liquidity = str(position.get("liquidity_status", "unknown")).lower()
        if liquidity in {"illiquid", "unknown", "restricted"}:
            covered.add("liquidity_risk")
            findings.append(
                _finding(
                    "liquidity_risk",
                    "medium",
                    position.get("security_id", "unknown"),
                    f"Liquidity status is {liquidity}.",
                )
            )

    invalidation = thesis.get("invalidation_conditions", [])
    if not invalidation:
        covered.add("invalidation_conditions")
        findings.append(
            _finding(
                "invalidation_conditions",
                "high",
                "thesis",
                "No condition would invalidate the thesis.",
            )
        )

    uncovered = [
        category for category in CHALLENGE_CATEGORIES if category not in covered
    ]
    return {
        "thesis_id": thesis.get("thesis_id", "unidentified"),
        "status": "challenged" if findings else "no_findings",
        "findings": findings,
        "coverage": {
            "categories": list(CHALLENGE_CATEGORIES),
            "covered": sorted(covered),
            "uncovered": uncovered,
            "coverage_ratio": len(covered) / len(CHALLENGE_CATEGORIES),
        },
        "recommendation": "revise_or_decline",
        "approved": False,
        "critic_may_approve": False,
        "decision_date": decision_date,
    }


def run_committee_challenge(
    thesis: dict[str, Any],
    *,
    decision_date: str,
    human_reviewer: str | None = None,
    approval: str | None = None,
) -> dict[str, Any]:
    """Run challenge and require a distinct human decision for approval."""
    challenge = challenge_thesis(thesis, decision_date=decision_date)
    result = {
        "workflow": ["draft", "evidence_attached", "devils_advocate_challenge"],
        "thesis": thesis,
        "challenge": challenge,
        "status": "pending_human_review",
        "approved": False,
    }
    if human_reviewer is None or approval is None:
        return result
    if human_reviewer == "DEVILS_ADVOCATE":
        raise PermissionError("the Devil's Advocate cannot approve its own challenge")
    if role_for_identity(human_reviewer) is None:
        raise PermissionError("human reviewer identity is not recognized")
    if approval not in {"approve", "reject"}:
        raise ValueError("approval must be 'approve' or 'reject'")
    result["workflow"].append("human_review")
    result["status"] = "approved" if approval == "approve" else "rejected"
    result["approved"] = approval == "approve"
    result["reviewer"] = human_reviewer
    return result


def create_devils_advocate_agent(
    model: str | BaseChatModel,
) -> CompiledStateGraph:
    """Create a read-only critic with no bound tools or approval capability."""
    from deepagents import create_deep_agent

    return create_deep_agent(
        model=model,
        tools=(),
        system_prompt=DEVILS_ADVOCATE_PROMPT,
        name="devils-advocate",
    )


def _finding(
    category: str, severity: str, subject: Any, message: str
) -> dict[str, Any]:
    return {
        "category": category,
        "severity": severity,
        "subject": str(subject),
        "message": message,
        "evidence_ids": [str(subject)]
        if category
        not in {"concentration_risk", "liquidity_risk", "invalidation_conditions"}
        else [],
    }


def _validate_date(value: str) -> None:
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO decision_date: {value}") from exc
