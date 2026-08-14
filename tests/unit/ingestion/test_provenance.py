import pytest

from src.ingestion.fixed_income import validate_bond_instrument
from src.ingestion.provenance import (
    eligible_as_of,
    make_observation,
    select_point_in_time,
)


def observation(release_date: str, value: float) -> dict:
    return make_observation(
        source="alfred-fixture",
        series_id="DGS10",
        observation_date="2020-01-02",
        release_date=release_date,
        value=value,
        unit="percent",
        vintage=release_date,
    )


def test_point_in_time_selection_uses_latest_known_vintage():
    records = [observation("2020-01-03", 1.80), observation("2020-02-03", 1.85)]

    historical = select_point_in_time(records, decision_date="2020-01-31")
    revised = select_point_in_time(records, decision_date="2020-02-10")

    assert historical[0]["value"] == 1.80
    assert revised[0]["value"] == 1.85


def test_future_release_is_not_eligible_even_for_past_observation():
    record = observation("2020-02-03", 1.85)

    assert not eligible_as_of(record, "2020-01-31")


def test_invalid_provenance_date_is_rejected():
    with pytest.raises(ValueError, match="release_date cannot precede"):
        make_observation(
            source="fixture",
            series_id="CPI",
            observation_date="2020-02-02",
            release_date="2020-02-01",
            value=1,
            unit="index",
            vintage="2020-02-01",
        )


def test_bond_master_requires_terms_before_valuation():
    result = validate_bond_instrument(
        {
            "security_id": "BOND-1",
            "issuer": "Public Fixture Issuer",
            "currency": "USD",
        }
    )

    assert result["status"] == "needs_review"
    assert "coupon_rate" in result["missing_fields"]


def test_valid_bond_master_record_is_accepted():
    result = validate_bond_instrument(
        {
            "security_id": "BOND-1",
            "issuer": "Public Fixture Issuer",
            "currency": "USD",
            "issue_date": "2020-01-01",
            "maturity_date": "2030-01-01",
            "coupon_rate": 0.04,
            "coupon_frequency": 2,
            "day_count": "30/360",
            "settlement_lag_days": 1,
        }
    )

    assert result == {"status": "valid", "security_id": "BOND-1"}
