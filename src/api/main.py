"""FastAPI entry point — the Tool Layer's HTTP surface.

Every endpoint below is a stub today; each one is replaced with a real
implementation on the day noted in its own docstring (PLAN.md Appendix B).
"""

from fastapi import FastAPI

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
    """# MOCK — replace on Day 3 with real curve interpolation over Day 2's FRED-derived tenors."""
    return {"curve_date": curve_date, "points": [], "mock": True}


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
