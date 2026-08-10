"""FastAPI entry point — the Tool Layer's HTTP surface.

Most endpoints below remain stubs until Day 3. The curve endpoint reads the
real FRED-derived curve populated on Day 2.
"""

import duckdb
from fastapi import FastAPI, HTTPException

from src.ingestion.load_mock_structured_data import DEFAULT_DB_PATH

app = FastAPI(title="agentic-pm-lab Tool Layer")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/tools/price-bond")
def price_bond(security_id: str) -> dict:
    """# MOCK — replace on Day 3 with a real present-value bond pricer."""
    return {"security_id": security_id, "price": 100.0, "mock": True}


@app.get("/tools/curve")
def curve(curve_date: str | None = None) -> dict:
    """Return raw Treasury curve points populated from FRED."""
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
    return {
        "curve_date": selected_date,
        "points": [
            {
                "tenor": tenor,
                "tenor_years": tenor_years,
                "rate_pct": rate_pct,
                "series_id": series_id,
            }
            for tenor, tenor_years, rate_pct, series_id in rows
        ],
        "mock": False,
    }


@app.post("/tools/research")
def research(query: str) -> dict:
    """# MOCK — stays mocked; a real research/sentiment tool is a deferred non-goal (PRD.md §6)."""
    return {"query": query, "summary": "mock research summary", "mock": True}


@app.post("/tools/econometrics")
def econometrics(portfolio_id: str) -> dict:
    """# MOCK — replace on Day 3 with a real OLS factor regression (statsmodels)."""
    return {"portfolio_id": portfolio_id, "beta": {}, "mock": True}


@app.post("/tools/backtest")
def backtest(portfolio_id: str) -> dict:
    """# MOCK — replace on Day 3 with a real vectorized walk-forward backtest."""
    return {"portfolio_id": portfolio_id, "cagr": None, "sharpe": None, "mock": True}


@app.get("/tools/portfolio")
def portfolio(portfolio_id: str) -> dict:
    """# MOCK — replace on Day 3 with real exposure/weights/concentration analytics."""
    return {"portfolio_id": portfolio_id, "exposure": {}, "mock": True}
