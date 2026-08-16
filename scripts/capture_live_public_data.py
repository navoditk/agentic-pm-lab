"""Capture bounded, normalized samples from approved public data sources."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ingestion.public_investment import (
    PublicDataError,
    fetch_alfred_graph,
    fetch_sec_company_facts,
    fetch_sec_submissions,
    fetch_treasury_yield_curve,
)


def now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def latest(rows: list[dict[str, Any]], field: str, limit: int) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row.get(field) or ""), reverse=True)[:limit]


def run(output_dir: Path, sec_user_agent: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=False)
    captured_at = now()
    alfred = fetch_alfred_graph(
        "DGS10",
        vintage_date="2024-01-02",
        observation_start="2023-01-01",
        observation_end="2024-01-02",
    )
    treasury = fetch_treasury_yield_curve(year=2026)
    submissions = fetch_sec_submissions("320193", user_agent=sec_user_agent)
    facts = fetch_sec_company_facts("320193", user_agent=sec_user_agent)
    revenue = [
        row
        for row in facts
        if row.get("unit") == "USD" and "revenue" in str(row.get("concept")).lower()
    ]
    treasury_date = max(row["observation_date"] for row in treasury)
    treasury_sample = [
        row
        for row in treasury
        if row["observation_date"] == treasury_date
        and row["series_id"] in {"BC_2YEAR", "BC_10YEAR", "BC_30YEAR"}
    ]
    response = {
        "captured_at": captured_at,
        "sources": {
            "alfred": {
                "status": "success",
                "record_count": len(alfred),
                "sample": [alfred[0], alfred[-1]],
            },
            "treasury_yield_curve": {
                "status": "success",
                "record_count": len(treasury),
                "latest_observation_date": treasury_date,
                "sample": treasury_sample,
            },
            "sec_submissions": {
                "status": "success",
                "cik": "0000320193",
                "record_count": len(submissions),
                "sample": latest(submissions, "filing_date", 3),
            },
            "sec_companyfacts": {
                "status": "success",
                "cik": "0000320193",
                "record_count": len(facts),
                "revenue_record_count": len(revenue),
                "sample": latest(revenue, "filing_date", 3),
            },
        },
    }
    (output_dir / "response.json").write_text(
        json.dumps(response, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    manifest = {
        "schema_version": 1,
        "run_id": output_dir.name,
        "created_at": captured_at,
        "updated_at": now(),
        "experiment": {
            "name": "live public investment data capture",
            "status": "success",
        },
        "execution": {
            "provider": "other",
            "mode": "bounded_public_data_capture",
            "model": "none",
            "region": "none",
        },
        "input": {
            "path": "fixed public queries",
            "descriptor": "ALFRED DGS10 vintage 2024-01-02; Treasury 2026; SEC CIK 0000320193",
            "sha256": "",
        },
        "output": {
            "path": "response.json",
            "summary": "Normalized samples and counts; raw payloads excluded.",
        },
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "latency_ms": None,
        },
        "pricing": {
            "currency": "USD",
            "input_per_1m_tokens": 0,
            "output_per_1m_tokens": 0,
            "source": "No model invocation; public endpoints",
            "as_of": captured_at[:10],
        },
        "costs": {
            "token_estimate_usd": 0,
            "aws_observed_usd": 0,
            "aws_estimated_usd": 0,
            "other_estimated_usd": 0,
            "total_estimated_usd": 0,
            "accounting_note": "No AWS or model service was used.",
        },
        "evidence": ["response.json", "findings.md"],
        "findings": {
            "decision": "keep",
            "next_experiment": "Review provider snapshots before canonical promotion.",
        },
        "cleanup": {
            "required": False,
            "status": "not_required",
            "notes": "No cloud resources created.",
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    findings = f"""# Findings: live public investment data capture

Run ID: `{output_dir.name}`

## Question and hypothesis

Can approved public-data connectors retrieve bounded live responses and
normalize them into provenance-preserving records before canonical promotion?

## Result

- ALFRED DGS10: `{len(alfred)}` observations from vintage `2024-01-02`.
- U.S. Treasury daily yield curve: `{len(treasury)}` tenor records; latest observation `{treasury_date}`.
- SEC EDGAR submissions: `{len(submissions)}` normalized filing records for CIK `0000320193`.
- SEC Company Facts: `{len(facts)}` normalized records, including `{len(revenue)}` revenue-related USD records.
- Model tokens: `0`; AWS cost: `$0.00`; public endpoint cost: `$0.00`.

## What worked

Normalized output preserves source URLs, observation dates, release/vintage
semantics, units, CIK, accession numbers, and concept names. Only small
normalized samples and counts are committed; raw provider payloads are not.

## Limitations

The legacy Treasury Fiscal Data auctions path returned HTTP 404 during this
work, so it is not claimed as live evidence. The official Treasury daily
yield-curve XML feed was used instead. ALFRED's public graph CSV exposes the
requested vintage but not every release-history field available through the
keyed FRED API. SEC evidence is metadata and XBRL facts; full filing-text
extraction remains a separate controlled exercise.

## Evidence

- [Normalized response](response.json)
- [Machine-readable manifest](manifest.json)
- [Public data source catalog](../../../data/README.md)
"""
    (output_dir / "findings.md").write_text(findings, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sec-user-agent", required=True)
    args = parser.parse_args()
    try:
        run(args.output_dir, args.sec_user_agent)
    except (OSError, PublicDataError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
