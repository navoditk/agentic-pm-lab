import math

import pytest

from src.analytics.risk import max_drawdown, risk_metrics, rolling_volatility


def test_calculates_annualized_rolling_sample_volatility():
    result = rolling_volatility(
        [0.01, -0.01, 0.01],
        window=2,
        periods_per_year=2,
    )

    assert result[0] is None
    assert result[1] == pytest.approx(0.02)
    assert result[2] == pytest.approx(0.02)


def test_finds_worst_peak_to_trough_drawdown():
    result = max_drawdown([100, 120, 90, 110])

    assert result == {"max_drawdown": -0.25, "peak_index": 1, "trough_index": 2}


def test_combines_risk_metrics():
    result = risk_metrics(
        [0.01, -0.01],
        [100, 90],
        window=2,
        periods_per_year=1,
    )

    assert result["rolling_volatility"][-1] == pytest.approx(math.sqrt(2) * 0.01)
    assert result["max_drawdown"] == pytest.approx(-0.1)
