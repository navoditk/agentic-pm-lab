import pytest

from src.analytics.portfolio import portfolio_summary

SECURITIES = [
    {"security_id": "A", "asset_class": "rates", "sector": "government"},
    {"security_id": "B", "asset_class": "credit", "sector": "industrials"},
]


def test_calculates_weights_exposure_and_concentration():
    result = portfolio_summary(
        [
            {"security_id": "A", "market_value": 60},
            {"security_id": "B", "market_value": 40},
        ],
        SECURITIES,
    )

    assert result["total_market_value"] == 100
    assert result["exposure_by_asset_class"] == {"credit": 0.4, "rates": 0.6}
    assert result["largest_position_weight"] == 0.6
    assert result["concentration_hhi"] == pytest.approx(0.52)
    assert result["security_master_is_mock"] is True


def test_rejects_position_missing_from_security_master():
    with pytest.raises(ValueError, match="missing: C"):
        portfolio_summary([{"security_id": "C", "market_value": 100}], SECURITIES)
