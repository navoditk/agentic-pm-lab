"""Constrained portfolio allocation helpers backed by PyPortfolioOpt."""

from collections.abc import Mapping
from typing import Literal, TypedDict

import numpy as np
import pandas as pd
from pypfopt import EfficientFrontier, HRPOpt

from src.observability.telemetry import traced_analytics


class OptimizationResult(TypedDict):
    method: str
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe: float | None
    turnover: float
    transaction_cost: float
    constraints: dict[str, float]
    mock: bool


def _validate_inputs(
    expected_returns: Mapping[str, float],
    covariance: Mapping[str, Mapping[str, float]],
    current_weights: Mapping[str, float],
    bounds: tuple[float, float],
) -> list[str]:
    assets = list(expected_returns)
    if len(assets) < 2:
        raise ValueError("at least two assets are required")
    if set(covariance) != set(assets) or set(current_weights) != set(assets):
        raise ValueError(
            "expected_returns, covariance, and current_weights must share assets"
        )
    if bounds[0] < 0 or bounds[1] > 1 or bounds[0] > bounds[1]:
        raise ValueError("bounds must be within [0, 1] and ordered")
    if not np.isclose(sum(float(value) for value in current_weights.values()), 1.0):
        raise ValueError("current_weights must sum to 1")
    if any(float(value) < 0 for value in current_weights.values()):
        raise ValueError("current_weights must be non-negative")
    matrix = np.array([[float(covariance[a][b]) for b in assets] for a in assets])
    if not np.allclose(matrix, matrix.T) or np.any(np.linalg.eigvalsh(matrix) < -1e-10):
        raise ValueError("covariance must be symmetric and positive semidefinite")
    return assets


def compare_to_current(
    weights: Mapping[str, float], current_weights: Mapping[str, float]
) -> tuple[dict[str, float], float]:
    """Return per-asset deltas and one-way turnover versus current weights."""
    if set(weights) != set(current_weights):
        raise ValueError("weights and current_weights must share assets")
    deltas = {
        asset: float(weights[asset]) - float(current_weights[asset])
        for asset in weights
    }
    return deltas, 0.5 * sum(abs(delta) for delta in deltas.values())


def _result(
    method: str,
    weights: Mapping[str, float],
    expected_returns: Mapping[str, float],
    covariance: Mapping[str, Mapping[str, float]],
    current_weights: Mapping[str, float],
    transaction_cost_bps: float,
    constraints: dict[str, float],
) -> OptimizationResult:
    assets = list(expected_returns)
    vector = np.array([float(weights[asset]) for asset in assets])
    returns = np.array([float(expected_returns[asset]) for asset in assets])
    matrix = np.array([[float(covariance[a][b]) for b in assets] for a in assets])
    expected_return = float(vector @ returns)
    volatility = float(np.sqrt(vector @ matrix @ vector))
    sharpe = expected_return / volatility if volatility > 0 else None
    _, turnover = compare_to_current(weights, current_weights)
    return {
        "method": method,
        "weights": {asset: float(value) for asset, value in weights.items()},
        "expected_return": expected_return,
        "volatility": volatility,
        "sharpe": sharpe,
        "turnover": turnover,
        "transaction_cost": turnover * transaction_cost_bps / 10_000,
        "constraints": constraints,
        "mock": True,
    }


@traced_analytics("portfolio_optimization")
def optimize_portfolio(
    method: Literal["max_sharpe", "min_volatility", "risk_parity"],
    expected_returns: Mapping[str, float],
    covariance: Mapping[str, Mapping[str, float]],
    current_weights: Mapping[str, float],
    *,
    weight_bounds: tuple[float, float] = (0.0, 1.0),
    max_turnover: float = 1.0,
    max_concentration: float = 1.0,
    transaction_cost_bps: float = 0.0,
    risk_free_rate: float = 0.0,
) -> OptimizationResult:
    """Optimize a long-only allocation and reject infeasible institutional limits."""
    if method not in ("max_sharpe", "min_volatility", "risk_parity"):
        raise ValueError("method must be max_sharpe, min_volatility, or risk_parity")
    if max_turnover < 0 or max_concentration <= 0 or transaction_cost_bps < 0:
        raise ValueError("institutional constraints must be non-negative")
    assets = _validate_inputs(
        expected_returns, covariance, current_weights, weight_bounds
    )
    means = np.array([float(expected_returns[asset]) for asset in assets])
    matrix = np.array([[float(covariance[a][b]) for b in assets] for a in assets])

    if method == "risk_parity":
        optimizer = HRPOpt(
            returns=None,
            cov_matrix=pd.DataFrame(matrix, index=assets, columns=assets),
        )
        try:
            weights = optimizer.optimize()
        except AttributeError as error:
            # PyPortfolioOpt releases before the SciPy 1.16 compatibility fix
            # reference a removed private SciPy constant. Keep the learning
            # path deterministic and explicit rather than hiding the failure.
            if "_LINKAGE_METHODS" not in str(error):
                raise
            inverse_volatility = 1 / np.sqrt(np.diag(matrix))
            weights = {
                asset: float(value)
                for asset, value in zip(assets, inverse_volatility, strict=True)
            }
        weights = {asset: float(weights.get(asset, 0.0)) for asset in assets}
    else:
        frontier = EfficientFrontier(
            pd.Series(means, index=assets),
            pd.DataFrame(matrix, index=assets, columns=assets),
            weight_bounds=weight_bounds,
        )
        if method == "max_sharpe":
            frontier.max_sharpe(risk_free_rate=risk_free_rate)
        else:
            frontier.min_volatility()
        weights = {
            asset: float(value) for asset, value in frontier.clean_weights().items()
        }

    weights = {asset: max(0.0, float(weights.get(asset, 0.0))) for asset in assets}
    normalizer = sum(weights.values())
    if normalizer <= 0:
        raise ValueError("optimizer returned no investable weights")
    weights = {asset: value / normalizer for asset, value in weights.items()}
    _deltas, turnover = compare_to_current(weights, current_weights)
    if turnover > max_turnover + 1e-8:
        raise ValueError(f"optimization exceeds max_turnover: {turnover:.6f}")
    if max(weights.values()) > max_concentration + 1e-8:
        raise ValueError("optimization exceeds max_concentration")
    return _result(
        method,
        weights,
        expected_returns,
        covariance,
        current_weights,
        transaction_cost_bps,
        {"max_turnover": max_turnover, "max_concentration": max_concentration},
    )
