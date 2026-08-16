import duckdb
import pytest

from src.ingestion.governed_public import (
    GovernedDataError,
    capture_public_sources,
    write_governed_cache,
)


def _fixtures():
    return {
        "alfred": lambda *_args, **_kwargs: [
            {
                "source": "alfred",
                "series_id": "DGS10",
                "observation_date": "2026-08-14",
                "release_date": "2026-08-16",
                "vintage": "2026-08-16",
                "value": 4.2,
                "unit": "provider-defined",
                "source_url": "https://alfred.stlouisfed.org/graph/alfredgraph.csv",
            }
        ],
        "treasury": lambda **_kwargs: [
            {
                "source": "us-treasury-daily-yield-curve",
                "series_id": "BC_10YEAR",
                "observation_date": "2026-08-14",
                "release_date": "2026-08-14",
                "value": 4.2,
                "unit": "percent",
                "source_url": "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml",
            }
        ],
        "submissions": lambda *_args, **_kwargs: [
            {
                "source": "sec-edgar-submissions",
                "cik": "0000320193",
                "accession_number": "0000320193-26-000020",
                "form": "10-Q",
                "filing_date": "2026-07-31",
                "period_of_report": "2026-06-27",
                "primary_document": "quarterly.htm",
                "source_url": "https://data.sec.gov/submissions/CIK0000320193.json",
            }
        ],
        "facts": lambda *_args, **_kwargs: [
            {
                "source": "sec-edgar-companyfacts",
                "cik": "0000320193",
                "taxonomy": "us-gaap",
                "concept": "Revenues",
                "unit": "USD",
                "value": 100,
                "observation_date": "2026-06-27",
                "filing_date": "2026-07-31",
                "form": "10-Q",
                "accession_number": "0000320193-26-000020",
                "frame": "CY2026Q2",
                "source_url": "https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json",
            }
        ],
    }


def test_capture_validates_and_returns_all_source_batches():
    captures = capture_public_sources(
        capture_date=__import__("datetime").date(2026, 8, 16),
        sec_user_agent="agentic-pm-lab/1.0 contact test@example.com",
        fetchers=_fixtures(),
    )
    assert set(captures) == {
        "alfred",
        "treasury",
        "sec_submissions",
        "sec_companyfacts",
    }
    assert all(len(records) == 1 for records in captures.values())


def test_capture_rejects_unapproved_source_domain():
    fixtures = _fixtures()
    fixtures["alfred"] = lambda *_args, **_kwargs: [
        {
            **_fixtures()["alfred"]()[0],
            "source_url": "https://example.com/not-alfred",
        }
    ]
    with pytest.raises(GovernedDataError, match="outside the approved domain"):
        capture_public_sources(
            capture_date=__import__("datetime").date(2026, 8, 16),
            sec_user_agent="agentic-pm-lab/1.0 contact test@example.com",
            fetchers=fixtures,
        )


def test_write_governed_cache_creates_separate_tables_and_summary(tmp_path):
    captures = capture_public_sources(
        capture_date=__import__("datetime").date(2026, 8, 16),
        sec_user_agent="agentic-pm-lab/1.0 contact test@example.com",
        fetchers=_fixtures(),
    )
    db_path = tmp_path / "public_investment.duckdb"
    summary_path = tmp_path / "summary.json"
    summary = write_governed_cache(
        captures,
        db_path=db_path,
        summary_path=summary_path,
        captured_at="2026-08-16T00:00:00Z",
    )
    assert summary["sources"]["alfred"]["record_count"] == 1
    with duckdb.connect(str(db_path), read_only=True) as connection:
        assert (
            connection.execute("SELECT count(*) FROM ingestion_runs").fetchone()[0] == 4
        )
        assert (
            connection.execute("SELECT count(*) FROM sec_companyfacts").fetchone()[0]
            == 1
        )
    assert summary_path.exists()
