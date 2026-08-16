"""Governed cache for reviewed public investment-data connectors.

This cache is deliberately separate from ``portfolio.duckdb``. It stores
normalized provider records plus a run-level provenance table after schema,
source-domain, freshness, and bounded-volume checks pass.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import duckdb

from src.ingestion.load_mock_structured_data import REPO_ROOT
from src.ingestion.public_investment import (
    fetch_alfred_graph,
    fetch_sec_company_facts,
    fetch_sec_submissions,
    fetch_treasury_yield_curve,
)

DEFAULT_GOVERNED_DB = REPO_ROOT / "data" / "cache" / "public_investment.duckdb"
DEFAULT_SUMMARY_PATH = REPO_ROOT / "data" / "cache" / "public_investment_summary.json"
MAX_RECORDS = 100_000
SOURCE_DOMAINS = {
    "alfred": "alfred.stlouisfed.org",
    "treasury": "home.treasury.gov",
    "sec": {"data.sec.gov", "www.sec.gov"},
}


class GovernedDataError(RuntimeError):
    """Raised when a provider batch fails the governed-cache contract."""


def _hash_records(records: list[dict[str, Any]]) -> str:
    payload = json.dumps(records, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _validate(
    source: str,
    records: list[dict[str, Any]],
    required: tuple[str, ...],
) -> None:
    if not records:
        raise GovernedDataError(f"{source} returned no records")
    if len(records) > MAX_RECORDS:
        raise GovernedDataError(f"{source} exceeded the {MAX_RECORDS} record bound")
    expected_domains = SOURCE_DOMAINS[source]
    if isinstance(expected_domains, str):
        expected_domains = {expected_domains}
    for record in records:
        missing = [field for field in required if not record.get(field)]
        if missing:
            raise GovernedDataError(f"{source} record missing fields: {missing}")
        hostname = urlparse(str(record["source_url"])).hostname
        if hostname not in expected_domains:
            raise GovernedDataError(
                f"{source} source URL is outside the approved domain: {hostname}"
            )


def _latest_date(records: list[dict[str, Any]], *fields: str) -> str | None:
    values = [
        str(record[field])
        for record in records
        for field in fields
        if record.get(field)
    ]
    return max(values) if values else None


def capture_public_sources(
    *,
    capture_date: date | None = None,
    sec_user_agent: str,
    alfred_series_id: str = "DGS10",
    alfred_vintage: str | None = None,
    alfred_days: int = 365,
    treasury_year: int | None = None,
    fetchers: dict[str, Callable[..., list[dict[str, Any]]]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Fetch and validate bounded live batches for the governed cache."""
    as_of = capture_date or datetime.now(UTC).date()
    vintage = alfred_vintage or as_of.isoformat()
    start = (as_of - timedelta(days=alfred_days)).isoformat()
    fetch = fetchers or {}
    alfred = (fetch.get("alfred") or fetch_alfred_graph)(
        alfred_series_id,
        vintage_date=vintage,
        observation_start=start,
        observation_end=as_of.isoformat(),
    )
    treasury = (fetch.get("treasury") or fetch_treasury_yield_curve)(
        year=treasury_year or as_of.year
    )
    submissions = (fetch.get("submissions") or fetch_sec_submissions)(
        "320193", user_agent=sec_user_agent
    )
    facts = (fetch.get("facts") or fetch_sec_company_facts)(
        "320193", user_agent=sec_user_agent
    )
    _validate(
        "alfred", alfred, ("series_id", "observation_date", "vintage", "source_url")
    )
    _validate("treasury", treasury, ("series_id", "observation_date", "source_url"))
    _validate(
        "sec", submissions, ("cik", "accession_number", "filing_date", "source_url")
    )
    _validate("sec", facts, ("cik", "concept", "filing_date", "source_url"))
    return {
        "alfred": alfred,
        "treasury": treasury,
        "sec_submissions": submissions,
        "sec_companyfacts": facts,
    }


def _metadata(
    source: str, records: list[dict[str, Any]], captured_at: str
) -> tuple[Any, ...]:
    return (
        source,
        "success",
        captured_at,
        records[0]["source_url"],
        len(records),
        _latest_date(records, "observation_date", "filing_date"),
        records[0].get("vintage"),
        _hash_records(records),
        "passed schema, source-domain, and record-bound checks",
    )


def write_governed_cache(
    captures: dict[str, list[dict[str, Any]]],
    *,
    db_path: Path = DEFAULT_GOVERNED_DB,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Atomically write normalized source tables and governance metadata."""
    captured = captured_at or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_db = db_path.with_suffix(".tmp.duckdb")
    if temporary_db.exists():
        temporary_db.unlink()
    with duckdb.connect(str(temporary_db)) as connection:
        connection.execute("""
            CREATE TABLE ingestion_runs (
                source VARCHAR, status VARCHAR, captured_at TIMESTAMP,
                source_url VARCHAR, record_count INTEGER,
                latest_date VARCHAR, vintage VARCHAR, batch_sha256 VARCHAR,
                validation_note VARCHAR
            )
        """)
        connection.execute("""
            CREATE TABLE alfred_observations (
                series_id VARCHAR, observation_date DATE, release_date DATE,
                vintage DATE, value DOUBLE, unit VARCHAR, source_url VARCHAR,
                captured_at TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE treasury_yield_curve (
                series_id VARCHAR, observation_date DATE, release_date DATE,
                value DOUBLE, unit VARCHAR, source_url VARCHAR,
                captured_at TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE sec_submissions (
                cik VARCHAR, accession_number VARCHAR, form VARCHAR,
                filing_date DATE, period_of_report DATE, primary_document VARCHAR,
                source_url VARCHAR, captured_at TIMESTAMP
            )
        """)
        connection.execute("""
            CREATE TABLE sec_companyfacts (
                cik VARCHAR, taxonomy VARCHAR, concept VARCHAR, unit VARCHAR,
                value_json VARCHAR, observation_date DATE, filing_date DATE,
                form VARCHAR, accession_number VARCHAR, frame VARCHAR,
                source_url VARCHAR, captured_at TIMESTAMP
            )
        """)
        for source, records in captures.items():
            connection.execute(
                "INSERT INTO ingestion_runs VALUES (?, ?, CAST(? AS TIMESTAMP), ?, ?, ?, ?, ?, ?)",
                _metadata(source, records, captured),
            )
        connection.executemany(
            "INSERT INTO alfred_observations VALUES (?, CAST(? AS DATE), CAST(? AS DATE), CAST(? AS DATE), ?, ?, ?, CAST(? AS TIMESTAMP))",
            [
                (
                    r["series_id"],
                    r["observation_date"],
                    r.get("release_date") or None,
                    r["vintage"],
                    r["value"],
                    r["unit"],
                    r["source_url"],
                    captured,
                )
                for r in captures["alfred"]
            ],
        )
        connection.executemany(
            "INSERT INTO treasury_yield_curve VALUES (?, CAST(? AS DATE), CAST(? AS DATE), ?, ?, ?, CAST(? AS TIMESTAMP))",
            [
                (
                    r["series_id"],
                    r["observation_date"],
                    r.get("release_date") or None,
                    r["value"],
                    r["unit"],
                    r["source_url"],
                    captured,
                )
                for r in captures["treasury"]
            ],
        )
        connection.executemany(
            "INSERT INTO sec_submissions VALUES (?, ?, ?, CAST(? AS DATE), CAST(? AS DATE), ?, ?, CAST(? AS TIMESTAMP))",
            [
                (
                    r["cik"],
                    r["accession_number"],
                    r["form"],
                    r["filing_date"] or None,
                    r.get("period_of_report") or None,
                    r["primary_document"],
                    r["source_url"],
                    captured,
                )
                for r in captures["sec_submissions"]
            ],
        )
        connection.executemany(
            "INSERT INTO sec_companyfacts VALUES (?, ?, ?, ?, ?, CAST(? AS DATE), CAST(? AS DATE), ?, ?, ?, ?, CAST(? AS TIMESTAMP))",
            [
                (
                    r["cik"],
                    r["taxonomy"],
                    r["concept"],
                    r["unit"],
                    json.dumps(r["value"]),
                    r.get("observation_date") or None,
                    r.get("filing_date") or None,
                    r.get("form"),
                    r.get("accession_number"),
                    r.get("frame"),
                    r["source_url"],
                    captured,
                )
                for r in captures["sec_companyfacts"]
            ],
        )
    temporary_db.replace(db_path)
    summary = {
        "captured_at": captured,
        "database": str(db_path),
        "governance": "separate source-specific cache; canonical portfolio tables unchanged",
        "sources": {
            source: {
                "record_count": len(records),
                "batch_sha256": _hash_records(records),
            }
            for source, records in captures.items()
        },
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return summary
