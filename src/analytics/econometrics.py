"""OLS factor regression for portfolio and public-proxy returns."""

from collections.abc import Mapping, Sequence
from typing import TypedDict

import numpy as np
import statsmodels.api as sm


class FactorRegressionResult(TypedDict):
    alpha: float
    betas: dict[str, float]
    r_squared: float
    observations: int


def factor_regression(
    portfolio_returns: Sequence[float],
    factor_returns: Mapping[str, Sequence[float]],
) -> FactorRegressionResult:
    """Regress portfolio returns on one or more aligned factor-return series."""
    portfolio = np.asarray(portfolio_returns, dtype=float)
    if portfolio.ndim != 1 or len(portfolio) < 3:
        raise ValueError("portfolio_returns must contain at least three observations")
    if not factor_returns:
        raise ValueError("at least one factor series is required")
    factor_names = list(factor_returns)
    factors = np.column_stack(
        [np.asarray(factor_returns[name], dtype=float) for name in factor_names]
    )
    if factors.shape[0] != portfolio.shape[0]:
        raise ValueError("portfolio and factor series must have the same length")
    if not np.isfinite(portfolio).all() or not np.isfinite(factors).all():
        raise ValueError("return series must contain only finite values")
    if portfolio.shape[0] <= factors.shape[1] + 1:
        raise ValueError("more observations than regression parameters are required")

    model = sm.OLS(portfolio, sm.add_constant(factors, has_constant="add")).fit()
    return {
        "alpha": float(model.params[0]),
        "betas": {
            name: float(model.params[index + 1])
            for index, name in enumerate(factor_names)
        },
        "r_squared": float(model.rsquared),
        "observations": int(model.nobs),
    }
