import pytest

from src.ingestion.sec import filing_evidence, filings_as_of, normalize_filing

FILING = {
    "accession_number": "0000000001-20-000001",
    "cik": "1",
    "form": "10-K",
    "filing_date": "2020-02-15",
    "period_of_report": "2019-12-31",
    "primary_document": "annual-report.htm",
}


def test_normalize_filing_builds_canonical_sec_url():
    result = normalize_filing(FILING)

    assert result["cik"] == "0000000001"
    assert result["source_url"].endswith("/annual-report.htm")
    assert "000000000120000001" in result["source_url"]


def test_filing_evidence_preserves_source_and_retrieval_metadata():
    result = filing_evidence(
        FILING,
        excerpt="The issuer reports a change in funding conditions.",
        retrieved_at="2020-02-16T12:00:00Z",
    )

    assert result["evidence_type"] == "sec_filing_excerpt"
    assert result["publication_date"] == "2020-02-15"
    assert result["point_in_time_eligible"] is True


def test_filings_as_of_excludes_later_filing():
    later = {
        **FILING,
        "accession_number": "0000000001-20-000002",
        "filing_date": "2020-03-15",
    }

    result = filings_as_of([FILING, later], decision_date="2020-02-20")

    assert [item["accession_number"] for item in result] == [FILING["accession_number"]]


def test_normalize_filing_requires_accession_number():
    with pytest.raises(ValueError, match="accession_number"):
        normalize_filing(
            {key: value for key, value in FILING.items() if key != "accession_number"}
        )
