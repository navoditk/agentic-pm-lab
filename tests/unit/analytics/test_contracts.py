import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from src.analytics.backtest import run_backtest
from src.analytics.curves import interpolate_curve
from src.analytics.econometrics import factor_regression
from src.analytics.optimizer import optimize_portfolio
from src.analytics.portfolio import portfolio_summary
from src.analytics.pricers import black_scholes_price, price_bond
from src.analytics.research import get_research_summary
from src.analytics.risk import risk_metrics
from src.analytics.scenario import scenario_analysis

CONTRACTS_DIR = Path(__file__).resolve().parents[3] / "contracts" / "tools"


def contract_case(name):
    if name == "price_bond":
        function_input = {
            "cash_flows": [{"time_years": 1, "amount": 105}],
            "curve_tenors_years": [0.5, 1, 2],
            "curve_rates_pct": [5, 5, 5],
            "compounding_frequency": 1,
        }
        output = price_bond(**function_input)
    elif name == "black_scholes_price":
        function_input = {
            "spot": 100,
            "strike": 100,
            "time_to_expiry": 1,
            "risk_free_rate": 0.05,
            "volatility": 0.2,
            "option_type": "call",
        }
        output = black_scholes_price(**function_input)
    elif name == "interpolate_curve":
        function_input = {
            "tenors_years": [1, 2],
            "rates_pct": [4, 5],
            "target_tenors_years": [1.5],
        }
        output = interpolate_curve(**function_input)
    elif name == "portfolio_summary":
        function_input = {
            "positions": [{"security_id": "A", "market_value": 100}],
            "security_master": [
                {"security_id": "A", "asset_class": "rates", "sector": "government"}
            ],
        }
        output = portfolio_summary(**function_input)
    elif name == "risk_metrics":
        function_input = {
            "returns": [0.01, -0.01],
            "portfolio_values": [100, 90],
            "window": 2,
            "periods_per_year": 1,
        }
        output = risk_metrics(**function_input)
    elif name == "factor_regression":
        function_input = {
            "portfolio_returns": [0.01, 0.02, 0.03, 0.04],
            "factor_returns": {"SPY": [0.005, 0.01, 0.015, 0.02]},
        }
        output = factor_regression(**function_input)
    elif name == "run_backtest":
        function_input = {
            "asset_returns": {"A": [0.01, -0.01]},
            "weights": {"A": 1.0},
            "periods_per_year": 2,
        }
        output = run_backtest(**function_input)
    elif name == "get_research_summary":
        function_input = {"query": "latest issuer developments"}
        output = get_research_summary(**function_input)
    elif name == "scenario_analysis":
        function_input = {
            "positions": [{"security_id": "A", "weight": 1.0, "duration": 5.0}],
            "scenario_type": "rates",
            "shock_bps": 50,
        }
        output = scenario_analysis(**function_input)
    elif name == "optimize_portfolio":
        function_input = {
            "method": "min_volatility",
            "expected_returns": {"A": 0.1, "B": 0.08},
            "covariance": {"A": {"A": 0.04, "B": 0.01}, "B": {"A": 0.01, "B": 0.0225}},
            "current_weights": {"A": 0.5, "B": 0.5},
        }
        output = optimize_portfolio(**function_input)
    else:
        raise AssertionError(f"Unknown contract case: {name}")
    return function_input, output


@pytest.mark.parametrize(
    "name",
    [
        "price_bond",
        "black_scholes_price",
        "interpolate_curve",
        "portfolio_summary",
        "risk_metrics",
        "factor_regression",
        "run_backtest",
        "get_research_summary",
        "scenario_analysis",
        "optimize_portfolio",
    ],
)
def test_actual_input_and_output_match_contract(name):
    schema = json.loads((CONTRACTS_DIR / f"{name}.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    function_input, output = contract_case(name)

    Draft202012Validator(schema).validate({"input": function_input, "output": output})
