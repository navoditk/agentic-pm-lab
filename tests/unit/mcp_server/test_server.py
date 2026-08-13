import asyncio
import json
from pathlib import Path

import pytest

from src.mcp_server.server import MCP_TOOL_SPECS, create_mcp_server, invoke_tool

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_registered_mcp_schemas_are_loaded_from_shared_contracts() -> None:
    server = create_mcp_server()
    registered = {tool.name: tool for tool in server._tool_manager.list_tools()}

    assert set(registered) == {spec.name for spec in MCP_TOOL_SPECS}
    for spec in MCP_TOOL_SPECS:
        contract = json.loads(
            (REPO_ROOT / "contracts" / "tools" / spec.contract_file).read_text()
        )
        assert registered[spec.name].parameters == contract["properties"]["input"]


@pytest.mark.parametrize(
    ("tool_name", "arguments", "expected_key"),
    [
        (
            "black_scholes_price",
            {
                "spot": 100,
                "strike": 100,
                "time_to_expiry": 1,
                "risk_free_rate": 0.03,
                "volatility": 0.2,
                "option_type": "call",
            },
            "price",
        ),
        (
            "price_bond",
            {
                "cash_flows": [{"time_years": 1, "amount": 102}],
                "curve_tenors_years": [1, 2],
                "curve_rates_pct": [4, 4.5],
            },
            "price",
        ),
        (
            "interpolate_curve",
            {
                "tenors_years": [1, 2],
                "rates_pct": [4, 5],
                "target_tenors_years": [1.5],
            },
            0,
        ),
        (
            "portfolio_summary",
            {
                "positions": [{"security_id": "A", "market_value": 60}],
                "security_master": [
                    {"security_id": "A", "asset_class": "bond", "sector": "govt"}
                ],
            },
            "total_market_value",
        ),
        (
            "risk_metrics",
            {
                "returns": [0.01, -0.005, 0.002],
                "portfolio_values": [100, 101, 99],
                "window": 2,
            },
            "max_drawdown",
        ),
        (
            "factor_regression",
            {
                "portfolio_returns": [0.01, 0.02, 0.015, 0.03],
                "factor_returns": {"rates": [0.005, 0.01, 0.007, 0.015]},
            },
            "alpha",
        ),
        (
            "run_backtest",
            {
                "asset_returns": {"A": [0.01, -0.005], "B": [0.0, 0.01]},
                "weights": {"A": 0.5, "B": 0.5},
            },
            "equity_curve",
        ),
        ("get_research_summary", {"query": "rates outlook"}, "summary"),
    ],
)
def test_each_mcp_tool_delegates_to_underlying_analytics(
    tool_name: str, arguments: dict, expected_key: str | int
) -> None:
    result = invoke_tool(
        tool_name, arguments, identity="PM_USER", portfolio_id="PORT_A"
    )
    if isinstance(expected_key, int):
        assert isinstance(result, list)
        assert result[expected_key] == 4.5
    else:
        assert expected_key in result


def test_mcp_requires_identity_and_rechecks_portfolio_entitlement() -> None:
    with pytest.raises(PermissionError, match="Unknown identity"):
        invoke_tool(
            "risk_metrics",
            {"returns": [0.01, 0.02], "portfolio_values": [100, 101]},
            identity="UNKNOWN",
            portfolio_id="PORT_A",
        )

    with pytest.raises(PermissionError, match="PORT_B"):
        invoke_tool(
            "risk_metrics",
            {"returns": [0.01, 0.02], "portfolio_values": [100, 101]},
            identity="PM_USER",
            portfolio_id="PORT_B",
        )


def test_mcp_context_handler_requires_identity_metadata() -> None:
    server = create_mcp_server()

    async def call() -> object:
        return await server.call_tool(
            "risk_metrics",
            {"returns": [0.01, 0.02], "portfolio_values": [100, 101]},
        )

    with pytest.raises(Exception, match="Context is not available"):
        asyncio.run(call())
