"""Vectorized static-weight portfolio backtest."""

import math
import statistics
from collections.abc import Mapping, Sequence
from typing import TypedDict

from src.analytics.risk import max_drawdown
from src.observability.telemetry import traced_analytics


class BacktestResult(TypedDict):
    equity_curve: list[float]
    period_returns: list[float]
    cagr: float
    sharpe: float | None
    max_drawdown: float


@traced_analytics("run_backtest")
def run_backtest(
    asset_returns: Mapping[str, Sequence[float]],
    weights: Mapping[str, float],
    *,
    initial_value: float = 100.0,
    periods_per_year: int = 252,
    risk_free_rate: float = 0.0,
) -> BacktestResult:
    """Run a periodically rebalanced static-weight walk-forward backtest."""
    if not asset_returns:
        raise ValueError("at least one asset return series is required")
    if set(asset_returns) != set(weights):
        raise ValueError("asset_returns and weights must contain the same assets")
    if initial_value <= 0:
        raise ValueError("initial_value must be positive")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    normalized_weights = {asset: float(weight) for asset, weight in weights.items()}
    if any(weight < 0 for weight in normalized_weights.values()):
        raise ValueError("weights must be non-negative")
    if not math.isclose(sum(normalized_weights.values()), 1.0, abs_tol=1e-9):
        raise ValueError("weights must sum to 1")

    normalized_returns = {
        asset: [float(value) for value in values]
        for asset, values in asset_returns.items()
    }
    lengths = {len(values) for values in normalized_returns.values()}
    if len(lengths) != 1 or not lengths or next(iter(lengths)) == 0:
        raise ValueError("asset return series must be non-empty and equally sized")

    period_returns = [
        sum(
            normalized_weights[asset] * normalized_returns[asset][period]
            for asset in normalized_returns
        )
        for period in range(next(iter(lengths)))
    ]
    equity_curve = [float(initial_value)]
    for period_return in period_returns:
        if period_return <= -1:
            raise ValueError("period returns cannot be less than or equal to -100%")
        equity_curve.append(equity_curve[-1] * (1 + period_return))

    years = len(period_returns) / periods_per_year
    cagr = (equity_curve[-1] / equity_curve[0]) ** (1 / years) - 1
    sharpe: float | None = None
    if len(period_returns) >= 2:
        volatility = statistics.stdev(period_returns)
        if volatility > 0:
            per_period_risk_free = (1 + risk_free_rate) ** (1 / periods_per_year) - 1
            sharpe = (
                statistics.mean(
                    value - per_period_risk_free for value in period_returns
                )
                / volatility
                * math.sqrt(periods_per_year)
            )
    return {
        "equity_curve": equity_curve,
        "period_returns": period_returns,
        "cagr": cagr,
        "sharpe": sharpe,
        "max_drawdown": max_drawdown(equity_curve)["max_drawdown"],
    }
