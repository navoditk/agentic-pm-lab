import pytest

from src.analytics.fixed_income import (
    bond_duration_dv01,
    key_rate_dv01,
    reconcile_bond_price,
)


def test_duration_and_dv01_use_discounted_cash_flow_weights():
    result = bond_duration_dv01(
        [{"time_years": 1.0, "amount": 5.0}, {"time_years": 2.0, "amount": 105.0}],
        [1.0, 2.0],
        [5.0, 5.0],
    )

    assert result["price"] == pytest.approx(99.88389, abs=1e-5)
    assert result["macaulay_duration_years"] == pytest.approx(1.952354, abs=1e-5)
    assert result["modified_duration_years"] == pytest.approx(1.904736, abs=1e-5)
    assert result["dv01"] == pytest.approx(0.0190252, abs=1e-6)


def test_key_rate_dv01_is_concentrated_at_relevant_nodes():
    result = key_rate_dv01(
        [{"time_years": 2.0, "amount": 100.0}],
        [1.0, 2.0, 5.0],
        [4.0, 5.0, 6.0],
    )

    assert result["base_price"] == pytest.approx(90.595064, abs=1e-5)
    assert result["key_rate_dv01"]["2.0"] > 0
    assert result["key_rate_dv01"]["1.0"] == pytest.approx(0.0)
    assert result["key_rate_dv01"]["5.0"] == pytest.approx(0.0)


def test_clean_dirty_price_reconciliation_uses_supplied_period_fraction():
    result = reconcile_bond_price(99.5, 100.0, 6.0, 2, 0.5)

    assert result == {
        "clean_price": 99.5,
        "accrued_interest": pytest.approx(1.5),
        "dirty_price": pytest.approx(101.0),
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"bump_bps": 0},
        {"accrued_period_fraction": 1.1},
    ],
)
def test_fixed_income_rejects_invalid_parameters(kwargs):
    if "bump_bps" in kwargs:
        with pytest.raises(ValueError, match="bump_bps"):
            key_rate_dv01(
                [{"time_years": 1.0, "amount": 100.0}],
                [1.0],
                [5.0],
                **kwargs,
            )
    else:
        with pytest.raises(ValueError, match="accrued_period_fraction"):
            reconcile_bond_price(100, 100, 5, 2, **kwargs)
