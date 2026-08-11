import math

import pytest

from src.analytics.pricers import black_scholes_price, price_bond


def test_prices_single_cash_flow_by_hand():
    result = price_bond(
        [{"time_years": 1, "amount": 105}],
        [0.5, 1, 2],
        [5, 5, 5],
        compounding_frequency=1,
    )

    assert result["price"] == pytest.approx(100)
    assert result["discounted_cash_flows"][0]["present_value"] == pytest.approx(100)


def test_black_scholes_matches_reference_call_value():
    result = black_scholes_price(100, 100, 1, 0.05, 0.2, "call")

    assert result["price"] == pytest.approx(10.450584, abs=1e-6)


def test_black_scholes_call_put_parity():
    call = black_scholes_price(100, 105, 0.5, 0.03, 0.25, "call")["price"]
    put = black_scholes_price(100, 105, 0.5, 0.03, 0.25, "put")["price"]

    assert call - put == pytest.approx(100 - 105 * math.exp(-0.03 * 0.5))


def test_bond_rejects_cash_flow_outside_curve():
    with pytest.raises(ValueError, match="outside"):
        price_bond([{"time_years": 3, "amount": 100}], [1, 2], [4, 5])
