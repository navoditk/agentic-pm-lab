"""FastAPI entry point for governed deterministic Tool Layer functions."""

from collections.abc import Callable
from typing import Annotated, NamedTuple

import duckdb
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from src.analytics.backtest import run_backtest
from src.analytics.curves import interpolate_curve
from src.analytics.econometrics import factor_regression
from src.analytics.portfolio import portfolio_summary
from src.analytics.pricers import CashFlow
from src.analytics.pricers import price_bond as calculate_bond_price
from src.analytics.research import get_research_summary
from src.analytics.risk import risk_metrics
from src.control.audit import record_audit_event
from src.control.authorization import check_tool_permission
from src.control.identity import role_for_identity
from src.ingestion.load_mock_structured_data import DEFAULT_DB_PATH
from src.observability.telemetry import instrument_fastapi

app = FastAPI(title="agentic-pm-lab Tool Layer")
instrument_fastapi(app)


class AuthorizationContext(NamedTuple):
    identity: str
    role: str


class CashFlowInput(BaseModel):
    time_years: float = Field(gt=0)
    amount: float


class BondPriceRequest(BaseModel):
    security_id: str
    cash_flows: list[CashFlowInput] = Field(min_length=1)
    compounding_frequency: int = Field(default=2, ge=1)
    curve_date: str | None = None


class FactorRegressionRequest(BaseModel):
    portfolio_id: str
    portfolio_returns: list[float] = Field(min_length=3)
    factor_returns: dict[str, list[float]]


class BacktestRequest(BaseModel):
    portfolio_id: str
    asset_returns: dict[str, list[float]]
    weights: dict[str, float]
    initial_value: float = Field(default=100.0, gt=0)
    periods_per_year: int = Field(default=252, ge=1)
    risk_free_rate: float = Field(default=0.0, gt=-1)


class RiskRequest(BaseModel):
    portfolio_id: str
    returns: list[float]
    portfolio_values: list[float] = Field(min_length=1)
    window: int = Field(default=20, ge=2)
    periods_per_year: int = Field(default=252, ge=1)


def require_tool(
    tool_name: str,
) -> Callable[[str | None], AuthorizationContext]:
    """Build a FastAPI dependency enforcing and auditing one tool permission."""

    def dependency(
        x_identity: Annotated[str | None, Header(alias="X-Identity")] = None,
    ) -> AuthorizationContext:
        if x_identity is None:
            raise HTTPException(status_code=401, detail="X-Identity header is required")
        role = role_for_identity(x_identity)
        if role is None:
            raise HTTPException(status_code=401, detail="Unknown identity")
        allowed = check_tool_permission(role, tool_name)
        record_audit_event(x_identity, role, tool_name, allowed)
        if not allowed:
            raise HTTPException(status_code=403, detail="Tool access denied")
        return AuthorizationContext(x_identity, role)

    return dependency


def _curve_points(curve_date: str | None = None) -> tuple[str, list[tuple]]:
    if not DEFAULT_DB_PATH.exists():
        raise HTTPException(status_code=503, detail="Curve data has not been ingested")
    with duckdb.connect(str(DEFAULT_DB_PATH), read_only=True) as connection:
        table_exists = connection.execute(
            """
            SELECT count(*)
            FROM information_schema.tables
            WHERE table_name = 'curve_points'
            """
        ).fetchone()[0]
        if not table_exists:
            raise HTTPException(
                status_code=503, detail="Curve data has not been ingested"
            )
        selected_date = curve_date
        if selected_date is None:
            selected_date = str(
                connection.execute(
                    "SELECT max(curve_date) FROM curve_points"
                ).fetchone()[0]
            )
        rows = connection.execute(
            """
            SELECT tenor, tenor_years, rate_pct, series_id
            FROM curve_points
            WHERE curve_date = CAST(? AS DATE)
            ORDER BY tenor_years
            """,
            [selected_date],
        ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No curve found for that date")
    return selected_date, rows


def _unprocessable(error: ValueError) -> HTTPException:
    return HTTPException(status_code=422, detail=str(error))


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tools/price-bond")
def price_bond(
    request: BondPriceRequest,
    _authorization: Annotated[
        AuthorizationContext, Depends(require_tool("price-bond"))
    ],
) -> dict:
    """Price explicit bond cash flows against the FRED-derived curve."""
    _, rows = _curve_points(request.curve_date)
    try:
        result = calculate_bond_price(
            [
                CashFlow(time_years=item.time_years, amount=item.amount)
                for item in request.cash_flows
            ],
            [row[1] for row in rows],
            [row[2] for row in rows],
            compounding_frequency=request.compounding_frequency,
        )
    except ValueError as error:
        raise _unprocessable(error) from error
    return {"security_id": request.security_id, **result, "mock": False}


@app.get("/tools/curve")
def curve(
    _authorization: Annotated[AuthorizationContext, Depends(require_tool("curve"))],
    curve_date: str | None = None,
    target_tenors_years: Annotated[list[float] | None, Query()] = None,
) -> dict:
    """Interpolate the FRED-derived Treasury curve at requested tenors."""
    selected_date, rows = _curve_points(curve_date)
    observed_tenors = [row[1] for row in rows]
    targets = target_tenors_years or observed_tenors
    try:
        rates = interpolate_curve(
            observed_tenors,
            [row[2] for row in rows],
            targets,
        )
    except ValueError as error:
        raise _unprocessable(error) from error
    return {
        "curve_date": selected_date,
        "points": [
            {"tenor_years": tenor, "rate_pct": rate}
            for tenor, rate in zip(targets, rates, strict=True)
        ],
        "mock": False,
    }


@app.post("/tools/research")
def research(
    query: str,
    _authorization: Annotated[AuthorizationContext, Depends(require_tool("research"))],
) -> dict:
    """# MOCK — stays mocked; real research is a deferred non-goal (docs/PRD.md §6)."""
    return get_research_summary(query)


@app.post("/tools/econometrics")
def econometrics(
    request: FactorRegressionRequest,
    _authorization: Annotated[
        AuthorizationContext, Depends(require_tool("econometrics"))
    ],
) -> dict:
    """Run an OLS factor regression over caller-supplied aligned returns."""
    try:
        result = factor_regression(request.portfolio_returns, request.factor_returns)
    except ValueError as error:
        raise _unprocessable(error) from error
    return {"portfolio_id": request.portfolio_id, **result, "mock": False}


@app.post("/tools/backtest")
def backtest(
    request: BacktestRequest,
    _authorization: Annotated[AuthorizationContext, Depends(require_tool("backtest"))],
) -> dict:
    """Run a static-weight walk-forward backtest."""
    try:
        result = run_backtest(
            request.asset_returns,
            request.weights,
            initial_value=request.initial_value,
            periods_per_year=request.periods_per_year,
            risk_free_rate=request.risk_free_rate,
        )
    except ValueError as error:
        raise _unprocessable(error) from error
    return {"portfolio_id": request.portfolio_id, **result, "mock": False}


@app.get("/tools/portfolio")
def portfolio(
    portfolio_id: str,
    _authorization: Annotated[AuthorizationContext, Depends(require_tool("portfolio"))],
) -> dict:
    """Return weights and exposures using the explicitly mocked security master."""
    if not DEFAULT_DB_PATH.exists():
        raise HTTPException(
            status_code=503, detail="Portfolio data has not been loaded"
        )
    with duckdb.connect(str(DEFAULT_DB_PATH), read_only=True) as connection:
        positions = connection.execute(
            """
            SELECT security_id, market_value
            FROM portfolio_positions
            WHERE portfolio_id = ?
            """,
            [portfolio_id],
        ).fetchall()
        securities = connection.execute(
            "SELECT security_id, asset_class, sector FROM security_master"
        ).fetchall()
    if not positions:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    result = portfolio_summary(
        [
            {"security_id": security_id, "market_value": market_value}
            for security_id, market_value in positions
        ],
        [
            {
                "security_id": security_id,
                "asset_class": asset_class,
                "sector": sector,
            }
            for security_id, asset_class, sector in securities
        ],
    )
    return {"portfolio_id": portfolio_id, **result, "mock": False}


@app.post("/tools/risk")
def risk(
    request: RiskRequest,
    _authorization: Annotated[AuthorizationContext, Depends(require_tool("risk"))],
) -> dict:
    """Calculate rolling volatility and maximum drawdown."""
    try:
        result = risk_metrics(
            request.returns,
            request.portfolio_values,
            window=request.window,
            periods_per_year=request.periods_per_year,
        )
    except ValueError as error:
        raise _unprocessable(error) from error
    return {"portfolio_id": request.portfolio_id, **result, "mock": False}
