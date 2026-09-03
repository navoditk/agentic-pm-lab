"""Offline evidence-quality checks for authored PM fixtures."""

from collections.abc import Iterable, Mapping
from typing import Any


def citation_completeness(
    claims: Iterable[Mapping[str, Any]], valid_evidence_ids: set[str]
) -> dict[str, Any]:
    """Check that every claim has at least one known evidence identifier."""
    missing: list[str] = []
    invalid: list[str] = []
    for index, claim in enumerate(claims):
        claim_id = str(claim.get("id", index))
        evidence_ids = claim.get("evidence_ids", [])
        if not isinstance(evidence_ids, list) or not evidence_ids:
            missing.append(claim_id)
            continue
        invalid.extend(
            f"{claim_id}:{evidence_id}"
            for evidence_id in evidence_ids
            if str(evidence_id) not in valid_evidence_ids
        )
    passed = not missing and not invalid
    return {
        "status": "pass" if passed else "fail",
        "score": 1.0 if passed else 0.0,
        "missing_claims": missing,
        "invalid_evidence_ids": invalid,
    }


def abstention_check(
    answer: str, *, required_disclosures: Iterable[str]
) -> dict[str, Any]:
    """Check that a bounded answer states its required limitations."""
    normalized = answer.casefold()
    missing = [
        disclosure
        for disclosure in required_disclosures
        if disclosure.casefold() not in normalized
    ]
    return {
        "status": "pass" if not missing else "fail",
        "score": 1.0 if not missing else 0.0,
        "missing_disclosures": missing,
    }


def contradiction_check(claims: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Find conflicting values for the same explicitly named subject."""
    values: dict[str, set[str]] = {}
    for claim in claims:
        subject = claim.get("subject")
        value = claim.get("value")
        if subject is None or value is None:
            continue
        values.setdefault(str(subject), set()).add(str(value))
    conflicts = sorted(
        subject for subject, observed in values.items() if len(observed) > 1
    )
    return {
        "status": "pass" if not conflicts else "fail",
        "score": 1.0 if not conflicts else 0.0,
        "conflicting_subjects": conflicts,
    }


def evaluate_evidence_bundle(
    *,
    claims: Iterable[Mapping[str, Any]],
    valid_evidence_ids: set[str],
    answer: str,
    required_disclosures: Iterable[str],
) -> dict[str, Any]:
    """Run the independent offline evidence checks as one result envelope."""
    materialized = list(claims)
    dimensions = {
        "citation_completeness": citation_completeness(
            materialized, valid_evidence_ids
        ),
        "abstention": abstention_check(
            answer, required_disclosures=required_disclosures
        ),
        "contradiction": contradiction_check(materialized),
    }
    return {
        "status": "pass"
        if all(item["status"] == "pass" for item in dimensions.values())
        else "fail",
        "dimensions": dimensions,
    }
