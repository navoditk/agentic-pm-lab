import pytest

from src.analytics.scenario import scenario_analysis


def test_rates_scenario_uses_duration_and_weight() -> None:
    result = scenario_analysis(
        [
            {"security_id": "bond", "weight": 0.6, "duration": 5.0},
            {"security_id": "cash", "weight": 0.4, "duration": 0.0},
        ],
        "rates",
        50,
    )
    assert result["portfolio_return_impact"] == pytest.approx(-0.015)
    assert result["mock"] is True


def test_credit_scenario_uses_spread_duration() -> None:
    result = scenario_analysis(
        [{"security_id": "credit", "weight": 1.0, "spread_duration": 4.0}],
        "credit",
        75,
        horizon="one_day",
    )
    assert result["portfolio_return_impact"] == pytest.approx(-0.03)
    assert result["horizon"] == "one_day"


def test_scenario_rejects_invalid_units() -> None:
    with pytest.raises(ValueError, match="scenario_type"):
        scenario_analysis([{"weight": 1.0}], "equity", 50)  # type: ignore[arg-type]
