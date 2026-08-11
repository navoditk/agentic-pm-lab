import pytest

from src.analytics.backtest import run_backtest


def test_builds_static_weight_equity_curve_and_metrics():
    result = run_backtest(
        {"A": [0.10, -0.10], "B": [0.0, 0.0]},
        {"A": 0.5, "B": 0.5},
        periods_per_year=2,
    )

    assert result["period_returns"] == pytest.approx([0.05, -0.05])
    assert result["equity_curve"] == pytest.approx([100, 105, 99.75])
    assert result["cagr"] == pytest.approx(-0.0025)
    assert result["max_drawdown"] == pytest.approx(-0.05)
    assert result["sharpe"] == pytest.approx(0)


def test_rejects_weights_that_do_not_sum_to_one():
    with pytest.raises(ValueError, match="sum to 1"):
        run_backtest({"A": [0.01]}, {"A": 0.9})
