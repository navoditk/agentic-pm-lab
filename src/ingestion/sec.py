"""Normalize SEC filing metadata into point-in-time research evidence."""

from collections.abc import Iterable
from typing import Any

from src.ingestion.provenance import eligible_as_of


def normalize_filing(filing: dict[str, Any]) -> dict[str, Any]:
    """Normalize the small filing envelope used by the research layer."""
    required = {
        "accession_number",
        "cik",
        "form",
        "filing_date",
        "period_of_report",
        "primary_document",
    }
    missing = sorted(required.difference(filing))
    if missing:
        raise ValueError(f"filing is missing fields: {missing}")
    accession = str(filing["accession_number"]).replace("-", "")
    cik = str(filing["cik"]).zfill(10)
    return {
        "source": "sec-edgar",
        "accession_number": str(filing["accession_number"]),
        "cik": cik,
        "form": str(filing["form"]),
        "filing_date": str(filing["filing_date"]),
        "period_of_report": str(filing["period_of_report"]),
        "primary_document": str(filing["primary_document"]),
        "source_url": (
            f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/"
            f"{filing['primary_document']}"
        ),
    }


def filing_evidence(
    filing: dict[str, Any],
    *,
    excerpt: str,
    retrieved_at: str,
) -> dict[str, Any]:
    """Create an attributable, time-stamped evidence object from a filing."""
    normalized = normalize_filing(filing)
    if not excerpt.strip():
        raise ValueError("excerpt must not be empty")
    normalized.update(
        {
            "evidence_type": "sec_filing_excerpt",
            "excerpt": excerpt,
            "retrieved_at": retrieved_at,
            "publication_date": normalized["filing_date"],
            "point_in_time_eligible": True,
        }
    )
    return normalized


def filings_as_of(
    filings: Iterable[dict[str, Any]], *, decision_date: str
) -> list[dict[str, Any]]:
    """Keep filings whose filing/publication date was known at decision time."""
    results = []
    for filing in filings:
        normalized = normalize_filing(filing)
        observation = {
            "source": "sec-edgar",
            "series_id": normalized["accession_number"],
            "observation_date": normalized["period_of_report"],
            "release_date": normalized["filing_date"],
            "unit": "document",
            "vintage": normalized["filing_date"],
        }
        if eligible_as_of(observation, decision_date):
            results.append(normalized)
    return sorted(results, key=lambda item: item["filing_date"])
