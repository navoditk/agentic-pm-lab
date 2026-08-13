"""MCP wrapper for the shared, deterministic Tool Layer.

The MCP server is an adapter, not a second analytics implementation. Every
handler delegates to ``src.analytics`` and loads the corresponding input
contract from ``contracts/tools``. Identity and portfolio metadata travel in
the MCP request context so callers cannot bypass the Day 7 Cedar checks by
calling the MCP server directly.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.context import Context
from mcp.server.mcpserver.tools.base import Tool as RegisteredTool

from src.analytics.backtest import run_backtest
from src.analytics.curves import interpolate_curve
from src.analytics.econometrics import factor_regression
from src.analytics.portfolio import portfolio_summary
from src.analytics.pricers import CashFlow, black_scholes_price, price_bond
from src.analytics.research import get_research_summary
from src.analytics.risk import risk_metrics
from src.control.authorization import check_portfolio_access, check_tool_permission
from src.control.identity import role_for_identity

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPO_ROOT / "contracts" / "tools"


@dataclass(frozen=True)
class MCPToolSpec:
    """One MCP registration and its governed Tool Layer implementation."""

    name: str
    contract_file: str
    permission_name: str
    handler: Any
    portfolio_field: str | None = None

    @property
    def contract(self) -> dict[str, Any]:
        return json.loads((CONTRACTS_DIR / self.contract_file).read_text())

    @property
    def input_schema(self) -> dict[str, Any]:
        # The repository contract is the authoritative wire schema. Its
        # ``output`` section remains available to contract/eval tooling; MCP's
        # inputSchema is the contract's input section.
        return self.contract["properties"]["input"]


def _identity_allowed(identity: str, permission_name: str) -> str:
    role = role_for_identity(identity)
    if role is None:
        raise PermissionError(f"Unknown identity: {identity}")
    if not check_tool_permission(role, permission_name):
        raise PermissionError(f"{identity} is not authorized for {permission_name}")
    return role


def _enforce_resource(identity: str, portfolio_id: str | None) -> None:
    if portfolio_id is None:
        return
    if not check_portfolio_access(identity, portfolio_id):
        raise PermissionError(
            f"{identity} is not authorized for portfolio {portfolio_id}"
        )


def _call_analytics(
    spec: MCPToolSpec, arguments: dict[str, Any]
) -> dict[str, Any] | list[float]:
    if spec.name == "black_scholes_price":
        return black_scholes_price(**arguments)
    if spec.name == "interpolate_curve":
        return interpolate_curve(**arguments)
    if spec.name == "price_bond":
        cash_flows = [CashFlow(**item) for item in arguments["cash_flows"]]
        return price_bond(
            cash_flows,
            arguments["curve_tenors_years"],
            arguments["curve_rates_pct"],
            compounding_frequency=arguments.get("compounding_frequency", 2),
        )
    if spec.name == "portfolio_summary":
        return portfolio_summary(**arguments)
    if spec.name == "risk_metrics":
        return risk_metrics(**arguments)
    if spec.name == "factor_regression":
        return factor_regression(**arguments)
    if spec.name == "run_backtest":
        return run_backtest(**arguments)
    if spec.name == "get_research_summary":
        return get_research_summary(arguments["query"])
    raise KeyError(f"No analytics handler registered for {spec.name}")


MCP_TOOL_SPECS: tuple[MCPToolSpec, ...] = (
    MCPToolSpec(
        "black_scholes_price",
        "black_scholes_price.schema.json",
        "price_option",
        black_scholes_price,
    ),
    MCPToolSpec(
        "price_bond",
        "price_bond.schema.json",
        "price-bond",
        price_bond,
    ),
    MCPToolSpec(
        "interpolate_curve",
        "interpolate_curve.schema.json",
        "interpolate_curve",
        interpolate_curve,
    ),
    MCPToolSpec(
        "portfolio_summary",
        "portfolio_summary.schema.json",
        "get_portfolio_exposure",
        portfolio_summary,
        portfolio_field="portfolio_id",
    ),
    MCPToolSpec(
        "risk_metrics",
        "risk_metrics.schema.json",
        "get_risk_metrics",
        risk_metrics,
        portfolio_field="portfolio_id",
    ),
    MCPToolSpec(
        "factor_regression",
        "factor_regression.schema.json",
        "run_factor_regression",
        factor_regression,
        portfolio_field="portfolio_id",
    ),
    MCPToolSpec(
        "run_backtest",
        "run_backtest.schema.json",
        "run_backtest",
        run_backtest,
        portfolio_field="portfolio_id",
    ),
    MCPToolSpec(
        "get_research_summary",
        "get_research_summary.schema.json",
        "get_research_summary",
        get_research_summary,
    ),
)

_SPEC_BY_NAME = {spec.name: spec for spec in MCP_TOOL_SPECS}


def invoke_tool(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    identity: str,
    portfolio_id: str | None = None,
) -> dict[str, Any] | list[float]:
    """Invoke one MCP capability through the identity and resource boundary.

    ``portfolio_id`` is deliberately metadata rather than an analytics input:
    it is authorization context and must not be allowed to alter calculations.
    """

    spec = _SPEC_BY_NAME.get(tool_name)
    if spec is None:
        raise KeyError(f"Unknown MCP tool: {tool_name}")
    _identity_allowed(identity, spec.permission_name)
    if spec.portfolio_field:
        if not isinstance(portfolio_id, str) or not portfolio_id:
            raise PermissionError(
                f"{tool_name} requires portfolio_id in MCP request metadata"
            )
        _enforce_resource(identity, portfolio_id)
    return _call_analytics(spec, arguments)


def _metadata_from_context(context: Any) -> dict[str, Any]:
    request_context = getattr(context, "request_context", None)
    metadata = getattr(request_context, "meta", None)
    if isinstance(metadata, dict):
        return metadata
    request = getattr(request_context, "request", None)
    headers = getattr(request, "headers", None)
    if headers is not None:
        return {
            "identity": headers.get("x-identity"),
            "portfolio_id": headers.get("x-portfolio-id"),
        }
    return {}


def _mcp_handler(spec: MCPToolSpec):
    """Build a typed MCP callable whose generated schema has the right fields.

    The SDK validates arguments against the callable before executing it. A
    dynamic, explicit signature keeps that validation active while the
    registration below still replaces the generated schema with the shared
    contract object.
    """

    field_names = list(spec.input_schema.get("properties", {}))

    async def dispatch(arguments: dict[str, Any], context: Context) -> Any:
        arguments = {
            key: value for key, value in arguments.items() if value is not None
        }
        metadata = _metadata_from_context(context)
        identity = metadata.get("identity")
        if not isinstance(identity, str):
            raise PermissionError("MCP request metadata must include identity")
        return invoke_tool(
            spec.name,
            arguments,
            identity=identity,
            portfolio_id=metadata.get("portfolio_id"),
        )

    required = set(spec.input_schema.get("required", []))
    required_fields = [name for name in field_names if name in required]
    optional_fields = [name for name in field_names if name not in required]
    parameters = ["context: Context"]
    parameters.extend(f"{name}: Any" for name in required_fields)
    parameters.extend(f"{name}: Any = None" for name in optional_fields)
    argument_items = ", ".join(f"{name!r}: {name}" for name in field_names)
    source = (
        f"async def handler({', '.join(parameters)}):\n"
        f"    return await dispatch({{{argument_items}}}, context)"
    )
    namespace = {"Any": Any, "Context": Context, "dispatch": dispatch}
    exec(source, namespace)  # noqa: S102 - names originate in checked-in JSON contracts.
    handler = namespace["handler"]
    handler.__name__ = spec.name
    handler.__doc__ = f"Governed MCP capability for {spec.name}; identity comes from request metadata."
    return handler


def create_mcp_server() -> MCPServer:
    """Create the MCP server with contract-backed input schemas."""

    server = MCPServer(
        name="agentic-pm-lab-tool-layer",
        version="0.1.0",
        description="Governed MCP adapter for deterministic PM analytics.",
    )
    for spec in MCP_TOOL_SPECS:
        server.add_tool(_mcp_handler(spec), name=spec.name, description=spec.name)
        # MCP SDK 2.x generates schemas from Python annotations. The project
        # contracts are stricter and already validated by FastAPI, so replace
        # the generated schema at registration with the exact shared contract.
        registered = server._tool_manager.get_tool(spec.name)  # SDK registration seam
        if not isinstance(registered, RegisteredTool):  # pragma: no cover
            raise TypeError(f"Unexpected MCP registration for {spec.name}")
        registered.parameters = spec.input_schema
    return server


def main() -> None:
    """Run the server over stdio for local MCP clients."""

    create_mcp_server().run(transport="stdio")


if __name__ == "__main__":  # pragma: no cover
    main()
