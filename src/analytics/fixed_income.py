"""Learning-scale fixed-income risk and price-reconciliation calculations."""

from collections.abc import Sequence
from typing import TypedDict

from src.analytics.pricers import CashFlow, price_bond
from src.observability.telemetry import traced_analytics


class DurationResult(TypedDict):
    price: float
    macaulay_duration_years: float
    modified_duration_years: float
    dv01: float


class KeyRateResult(TypedDict):
    base_price: float
    key_rate_dv01: dict[str, float]
    bump_bps: float


class PriceReconciliation(TypedDict):
    clean_price: float
    accrued_interest: float
    dirty_price: float


@traced_analytics("bond_duration_dv01")
def bond_duration_dv01(
    cash_flows: Sequence[CashFlow],
    curve_tenors_years: Sequence[float],
    curve_rates_pct: Sequence[float],
    *,
    compounding_frequency: int = 2,
) -> DurationResult:
    """Return price, duration, and first-order DV01 for explicit cash flows.

    Duration is calculated from the discounted cash-flow weights. The result is
    a learning approximation for a supplied spot curve; it does not model
    callable features, settlement calendars, or spread curves.
    """
    if not cash_flows:
        raise ValueError("at least one cash flow is required")
    if compounding_frequency <= 0:
        raise ValueError("compounding_frequency must be positive")
    priced = price_bond(
        cash_flows,
        curve_tenors_years,
        curve_rates_pct,
        compounding_frequency=compounding_frequency,
    )
    price = float(priced["price"])
    macaulay = (
        sum(
            float(item["time_years"]) * float(item["present_value"])
            for item in priced["discounted_cash_flows"]
        )
        / price
    )
    weighted_rate = (
        sum(
            float(item["rate_pct"]) * float(item["present_value"])
            for item in priced["discounted_cash_flows"]
        )
        / price
    )
    modified = macaulay / (1 + weighted_rate / 100 / compounding_frequency)
    return {
        "price": price,
        "macaulay_duration_years": macaulay,
        "modified_duration_years": modified,
        "dv01": price * modified * 0.0001,
    }


@traced_analytics("key_rate_dv01")
def key_rate_dv01(
    cash_flows: Sequence[CashFlow],
    curve_tenors_years: Sequence[float],
    curve_rates_pct: Sequence[float],
    *,
    compounding_frequency: int = 2,
    bump_bps: float = 1.0,
) -> KeyRateResult:
    """Estimate node-level DV01 by repricing one curve node at a time."""
    if bump_bps <= 0:
        raise ValueError("bump_bps must be positive")
    if len(curve_tenors_years) != len(curve_rates_pct):
        raise ValueError("curve tenors and rates must have the same length")
    if len({float(tenor) for tenor in curve_tenors_years}) != len(curve_tenors_years):
        raise ValueError("curve tenors must be unique")
    base = price_bond(
        cash_flows,
        curve_tenors_years,
        curve_rates_pct,
        compounding_frequency=compounding_frequency,
    )["price"]
    bump_rate_pct = bump_bps / 100
    result: dict[str, float] = {}
    for index, tenor in enumerate(curve_tenors_years):
        bumped = [float(rate) for rate in curve_rates_pct]
        bumped[index] += bump_rate_pct
        bumped_price = price_bond(
            cash_flows,
            curve_tenors_years,
            bumped,
            compounding_frequency=compounding_frequency,
        )["price"]
        result[str(float(tenor))] = float(base) - float(bumped_price)
    return {
        "base_price": float(base),
        "key_rate_dv01": result,
        "bump_bps": float(bump_bps),
    }


@traced_analytics("reconcile_bond_price")
def reconcile_bond_price(
    clean_price: float,
    par_value: float,
    coupon_rate_pct: float,
    coupon_frequency: int,
    accrued_period_fraction: float,
) -> PriceReconciliation:
    """Reconcile clean price, accrued interest, and dirty price.

    ``accrued_period_fraction`` is the fraction of the coupon period elapsed,
    supplied by the caller because day-count and settlement calendars vary by
    instrument. This intentionally does not infer calendar conventions.
    """
    if clean_price < 0 or par_value <= 0 or coupon_rate_pct < 0:
        raise ValueError(
            "price and par_value must be positive; coupon cannot be negative"
        )
    if coupon_frequency <= 0:
        raise ValueError("coupon_frequency must be positive")
    if not 0 <= accrued_period_fraction <= 1:
        raise ValueError("accrued_period_fraction must be between 0 and 1")
    accrued = (
        par_value * coupon_rate_pct / 100 / coupon_frequency * accrued_period_fraction
    )
    return {
        "clean_price": float(clean_price),
        "accrued_interest": accrued,
        "dirty_price": float(clean_price) + accrued,
    }
