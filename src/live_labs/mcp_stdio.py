"""Live lab: the MCP server as a real process, over stdio.

The MCP course's tests connect to the server in-process. This lab starts
`python -m src.mcp_server.server` as a separate process, the way a desktop
client would, and shows three things across a real process boundary: the
server runs as the identity in its environment, a request claiming another
identity is refused, and the server's spans join the client's trace.

    uv run python -m src.live_labs.mcp_stdio

Cost: none. Credentials: none; the identity is a local role name. Cleanup:
none; the server process exits with the lab, and its span log is a
temporary file.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

from src.observability.telemetry import SPAN_LOG_ENV, configure_telemetry

REPO_ROOT = Path(__file__).resolve().parents[2]
CURVE = {"tenors_years": [1, 2], "rates_pct": [4, 5], "target_tenors_years": [1.5]}
RISK = {"returns": [0.01, 0.02], "portfolio_values": [100, 101]}


async def run(span_log: Path) -> dict:
    from mcp.client import Client
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from opentelemetry import trace

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "src.mcp_server.server"],
        env={
            **os.environ,
            "AGENTIC_PM_LAB_MCP_IDENTITY": "PM_USER",
            SPAN_LOG_ENV: str(span_log),
        },
        cwd=str(REPO_ROOT),
    )
    tracer = trace.get_tracer("live-lab")
    async with Client(stdio_client(params)) as client:
        with tracer.start_as_current_span("live_lab.mcp_client") as span:
            trace_id = f"{span.get_span_context().trace_id:032x}"
            own = await client.call_tool("interpolate_curve", CURVE)
            claimed = await client.call_tool(
                "risk_metrics",
                RISK,
                meta={"identity": "RISK_USER", "portfolio_id": "PORT_B"},
            )
        return {
            "protocol": client.protocol_version,
            "trace_id": trace_id,
            "own": (own.is_error, own.content[0].text),
            "claimed": (claimed.is_error, claimed.content[0].text),
        }


def main() -> int:
    configure_telemetry()
    with tempfile.TemporaryDirectory() as scratch:
        span_log = Path(scratch) / "server-spans.jsonl"
        result = asyncio.run(run(span_log))
        spans = [json.loads(line) for line in span_log.read_text().splitlines()]
    print(f"Protocol negotiated over stdio: {result['protocol']}")
    print(
        f"Server bound to PM_USER, unclaimed call: error={result['own'][0]}, "
        f"result={result['own'][1]}"
    )
    print(f"Claiming RISK_USER: error={result['claimed'][0]}")
    print(f"  {result['claimed'][1]}")
    joined = [s["name"] for s in spans if s["trace_id"] == result["trace_id"]]
    print(f"\nClient trace: {result['trace_id']}")
    print(f"Server spans in that trace ({len(joined)} of {len(spans)}):")
    for name in joined:
        print(f"  {name}")
    print("The rest are the server's own start-up spans, in traces of their own.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
