import pytest

from src.analytics.optimizer import compare_to_current, optimize_portfolio

EXPECTED = {"A": 0.10, "B": 0.08, "C": 0.06}
COVARIANCE = {
    "A": {"A": 0.04, "B": 0.01, "C": 0.00},
    "B": {"A": 0.01, "B": 0.0225, "C": 0.0025},
    "C": {"A": 0.00, "B": 0.0025, "C": 0.01},
}
CURRENT = {"A": 1 / 3, "B": 1 / 3, "C": 1 / 3}


def test_compare_to_current_returns_deltas_and_one_way_turnover() -> None:
    deltas, turnover = compare_to_current({"A": 0.5, "B": 0.3, "C": 0.2}, CURRENT)
    assert sum(deltas.values()) == pytest.approx(0)
    assert turnover == pytest.approx((1 / 6 + 1 / 30 + 2 / 15) / 2)


@pytest.mark.parametrize("method", ["max_sharpe", "min_volatility", "risk_parity"])
def test_optimizer_returns_normalized_weights_and_constraints(method: str) -> None:
    result = optimize_portfolio(
        method,
        EXPECTED,
        COVARIANCE,
        CURRENT,
        max_turnover=1,
        max_concentration=0.9,
        transaction_cost_bps=10,
    )
    assert set(result["weights"]) == set(EXPECTED)
    assert sum(result["weights"].values()) == pytest.approx(1.0)
    assert max(result["weights"].values()) <= 0.9
    assert result["transaction_cost"] == pytest.approx(result["turnover"] * 0.001)
    assert result["mock"] is True


def test_optimizer_rejects_turnover_limit() -> None:
    with pytest.raises(ValueError, match="max_turnover"):
        optimize_portfolio(
            "max_sharpe",
            EXPECTED,
            COVARIANCE,
            {"A": 0.0, "B": 0.0, "C": 1.0},
            max_turnover=0.01,
        )
