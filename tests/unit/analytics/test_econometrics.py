import pytest

from src.analytics.econometrics import factor_regression


def test_recovers_exact_alpha_and_factor_beta():
    result = factor_regression(
        [0.011, 0.021, 0.031, 0.041],
        {"SPY": [0.005, 0.01, 0.015, 0.02]},
    )

    assert result["alpha"] == pytest.approx(0.001)
    assert result["betas"]["SPY"] == pytest.approx(2)
    assert result["r_squared"] == pytest.approx(1)
    assert result["observations"] == 4


def test_rejects_misaligned_factor_series():
    with pytest.raises(ValueError, match="same length"):
        factor_regression([0.01, 0.02, 0.03], {"SPY": [0.01, 0.02]})
