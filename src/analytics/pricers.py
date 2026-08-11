"""Present-value bond and Black-Scholes option pricers."""

import math
from collections.abc import Sequence
from typing import Literal, TypedDict

from src.analytics.curves import interpolate_curve


class CashFlow(TypedDict):
    time_years: float
    amount: float


class DiscountedCashFlow(CashFlow):
    rate_pct: float
    present_value: float


class BondPriceResult(TypedDict):
    price: float
    discounted_cash_flows: list[DiscountedCashFlow]


class OptionPriceResult(TypedDict):
    option_type: Literal["call", "put"]
    price: float
    d1: float
    d2: float


def price_bond(
    cash_flows: Sequence[CashFlow],
    curve_tenors_years: Sequence[float],
    curve_rates_pct: Sequence[float],
    *,
    compounding_frequency: int = 2,
) -> BondPriceResult:
    """Discount explicit bond cash flows against an interpolated spot curve."""
    if not cash_flows:
        raise ValueError("at least one cash flow is required")
    if compounding_frequency <= 0:
        raise ValueError("compounding_frequency must be positive")
    times = [float(cash_flow["time_years"]) for cash_flow in cash_flows]
    if any(time <= 0 for time in times):
        raise ValueError("cash-flow times must be positive")
    rates = interpolate_curve(curve_tenors_years, curve_rates_pct, times)

    discounted: list[DiscountedCashFlow] = []
    for cash_flow, time_years, rate_pct in zip(cash_flows, times, rates, strict=True):
        amount = float(cash_flow["amount"])
        periodic_rate = rate_pct / 100 / compounding_frequency
        if periodic_rate <= -1:
            raise ValueError("curve rate produces a non-positive discount base")
        present_value = amount / (
            (1 + periodic_rate) ** (compounding_frequency * time_years)
        )
        discounted.append(
            {
                "time_years": time_years,
                "amount": amount,
                "rate_pct": rate_pct,
                "present_value": present_value,
            }
        )
    return {
        "price": sum(item["present_value"] for item in discounted),
        "discounted_cash_flows": discounted,
    }


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def black_scholes_price(
    spot: float,
    strike: float,
    time_to_expiry: float,
    risk_free_rate: float,
    volatility: float,
    option_type: Literal["call", "put"],
) -> OptionPriceResult:
    """Price a European call or put with the Black-Scholes model."""
    if spot <= 0 or strike <= 0:
        raise ValueError("spot and strike must be positive")
    if time_to_expiry <= 0:
        raise ValueError("time_to_expiry must be positive")
    if volatility <= 0:
        raise ValueError("volatility must be positive")
    if option_type not in ("call", "put"):
        raise ValueError("option_type must be 'call' or 'put'")

    volatility_time = volatility * math.sqrt(time_to_expiry)
    d1 = (
        math.log(spot / strike)
        + (risk_free_rate + 0.5 * volatility**2) * time_to_expiry
    ) / volatility_time
    d2 = d1 - volatility_time
    discounted_strike = strike * math.exp(-risk_free_rate * time_to_expiry)
    if option_type == "call":
        price = spot * _normal_cdf(d1) - discounted_strike * _normal_cdf(d2)
    else:
        price = discounted_strike * _normal_cdf(-d2) - spot * _normal_cdf(-d1)
    return {"option_type": option_type, "price": price, "d1": d1, "d2": d2}
