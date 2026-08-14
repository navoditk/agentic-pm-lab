import pytest

from src.research.fixed_income import build_fixed_income_research_bundle
from src.research.provider import mocked_thematic_screen


def test_provider_returns_cited_metadata_not_free_form_summary():
    result = mocked_thematic_screen(
        "credit outlook",
        entity="Issuer A",
        publication_time="2026-08-12T08:00:00Z",
        retrieval_time="2026-08-12T09:00:00Z",
        novelty=0.8,
    )

    assert result["provider"] == "mock-bigdata-thematic-screen"
    assert result["entity"] == "Issuer A"
    assert result["evidence"]["source_url"].startswith("https://")
    assert result["licensing"]["redistribution"] == "not_permitted"
    assert result["mock"] is True


def test_provider_rejects_invalid_novelty():
    with pytest.raises(ValueError, match="novelty"):
        mocked_thematic_screen(
            "credit outlook",
            entity="Issuer A",
            publication_time="2026-08-12T08:00:00Z",
            novelty=1.1,
        )


def test_fixed_income_bundle_keeps_commentary_off_risk_path():
    evidence = mocked_thematic_screen(
        "funding pressure",
        entity="Issuer A",
        publication_time="2026-08-11T08:00:00Z",
        retrieval_time="2026-08-12T09:00:00Z",
    )
    bundle = build_fixed_income_research_bundle(
        [
            {
                "topic": "sofr_funding_conditions",
                "source": "public-fixture",
                "series_id": "SOFR",
                "observation_date": "2026-08-11",
                "release_date": "2026-08-11",
                "unit": "percent",
                "vintage": "2026-08-11",
                "value": 5.3,
            }
        ],
        [evidence],
        decision_date="2026-08-12",
    )

    assert bundle["structured_count"] == 1
    assert bundle["evidence_count"] == 1
    assert bundle["evidence_commentary"][0]["risk_number_eligible"] is False
    assert bundle["narrative_cannot_create_risk_number"] is True
