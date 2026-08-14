"""Fixed-income research bundle with separate structured and evidence paths."""

from collections.abc import Iterable, Mapping
from typing import Any

from src.ingestion.provenance import REQUIRED_PROVENANCE_FIELDS, eligible_as_of

STRUCTURED_TOPICS = {
    "treasury_auction_supply",
    "sofr_funding_conditions",
    "curve_shape",
    "trace_liquidity_aggregate",
    "issuer_rating_exposure",
    "cftc_rates_positioning",
}


def build_fixed_income_research_bundle(
    observations: Iterable[Mapping[str, Any]],
    commentary: Iterable[Mapping[str, Any]],
    *,
    decision_date: str,
) -> dict[str, Any]:
    """Partition point-in-time observations from cited unstructured commentary.

    Structured observations are eligible for deterministic tools only after the
    provenance check. Commentary is retained as evidence and cannot contribute
    a numeric risk value.
    """
    structured: list[dict[str, Any]] = []
    for observation in observations:
        record = dict(observation)
        topic = record.get("topic")
        if topic not in STRUCTURED_TOPICS:
            raise ValueError(f"unsupported fixed-income topic: {topic}")
        if not REQUIRED_PROVENANCE_FIELDS.issubset(record):
            raise ValueError("structured observation is missing provenance")
        if eligible_as_of(record, decision_date):
            structured.append(record)

    evidence: list[dict[str, Any]] = []
    for item in commentary:
        record = dict(item)
        required = {
            "provider",
            "query",
            "entity",
            "publication_time",
            "retrieval_time",
            "novelty",
            "licensing",
            "evidence",
        }
        missing = sorted(required.difference(record))
        if missing:
            raise ValueError(f"commentary evidence is missing fields: {missing}")
        record["risk_number_eligible"] = False
        evidence.append(record)

    return {
        "structured_observations": structured,
        "evidence_commentary": evidence,
        "structured_count": len(structured),
        "evidence_count": len(evidence),
        "narrative_cannot_create_risk_number": True,
    }
