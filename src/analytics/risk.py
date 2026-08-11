"""Deterministic volatility and drawdown risk measures."""

import math
import statistics
from collections.abc import Sequence
from typing import TypedDict

from src.observability.telemetry import traced_analytics


class DrawdownResult(TypedDict):
    max_drawdown: float
    peak_index: int
    trough_index: int


class RiskMetrics(TypedDict):
    rolling_volatility: list[float | None]
    max_drawdown: float
    peak_index: int
    trough_index: int


@traced_analytics("rolling_volatility")
def rolling_volatility(
    returns: Sequence[float],
    *,
    window: int = 20,
    periods_per_year: int = 252,
) -> list[float | None]:
    """Return annualized sample volatility for each complete rolling window."""
    if window < 2:
        raise ValueError("window must be at least 2")
    if periods_per_year <= 0:
        raise ValueError("periods_per_year must be positive")
    normalized = [float(value) for value in returns]
    output: list[float | None] = [None] * len(normalized)
    annualizer = math.sqrt(periods_per_year)
    for end_index in range(window - 1, len(normalized)):
        sample = normalized[end_index - window + 1 : end_index + 1]
        output[end_index] = statistics.stdev(sample) * annualizer
    return output


@traced_analytics("max_drawdown")
def max_drawdown(values: Sequence[float]) -> DrawdownResult:
    """Return the worst peak-to-trough percentage decline."""
    if not values:
        raise ValueError("at least one portfolio value is required")
    normalized = [float(value) for value in values]
    if any(value <= 0 for value in normalized):
        raise ValueError("portfolio values must be positive")

    peak_value = normalized[0]
    peak_index = 0
    worst_drawdown = 0.0
    worst_peak_index = 0
    trough_index = 0
    for index, value in enumerate(normalized):
        if value > peak_value:
            peak_value = value
            peak_index = index
        drawdown = value / peak_value - 1
        if drawdown < worst_drawdown:
            worst_drawdown = drawdown
            worst_peak_index = peak_index
            trough_index = index
    return {
        "max_drawdown": worst_drawdown,
        "peak_index": worst_peak_index,
        "trough_index": trough_index,
    }


@traced_analytics("risk_metrics")
def risk_metrics(
    returns: Sequence[float],
    portfolio_values: Sequence[float],
    *,
    window: int = 20,
    periods_per_year: int = 252,
) -> RiskMetrics:
    """Combine rolling volatility and maximum drawdown."""
    drawdown = max_drawdown(portfolio_values)
    return {
        "rolling_volatility": rolling_volatility(
            returns, window=window, periods_per_year=periods_per_year
        ),
        **drawdown,
    }
