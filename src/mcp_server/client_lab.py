"""The client side of MCP, for the Model Context Protocol course.

`server.py` is the repository's MCP server. This module is what talks to it:
a real MCP session, in-process, so every lab runs offline with no subprocess
or network and still exercises the SDK's request handling end to end.

It also connects MCP to the agent loop from Agent foundations.
`mcp_tools_for_loop()` discovers tools over MCP and wraps each as a
`src.foundations.agent_loop.Tool`, so the same loop now governs a remote tool
set. That makes the two layers of governance visible side by side:

- **Client side** (the loop's `governed_call`): which tools this agent may use.
- **Server side** (`server.py`): which caller may use a tool, and on which
  portfolio, enforced by Cedar on every call whatever the client decided.

Facts this module relies on were checked against the pinned SDK (mcp 2.0.0)
and the MCP specification 2026-07-28, and each is pinned by a test in
tests/unit/mcp_server/test_client_lab.py:

- `Client(server, mode="auto")` negotiates protocol 2026-07-28, which is
  stateless: no initialize handshake, version and capabilities on every
  request. `mode="legacy"` forces the earlier initialize handshake (2025-11-25).
- A tool execution error (bad arguments, an authorization refusal) returns a
  result with `isError` set, which the model can see and act on.
- W3C trace context crosses the boundary in `_meta` (`traceparent`), so the
  server's spans join the caller's trace.
- Identity is bound when the server is created, the way the specification
  says a stdio server takes credentials from its environment. A request that
  claims a different identity in `_meta` is refused, because self-reported
  metadata should not be relied on for security decisions; see
  `test_a_claimed_identity_cannot_override_the_authenticated_one`.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Literal

from mcp.client import Client
from mcp.server.mcpserver import MCPServer

from src.foundations.agent_loop import Tool
from src.mcp_server.server import create_mcp_server

Mode = Literal["auto", "legacy"]


class ToolExecutionError(RuntimeError):
    """An MCP tool result with `isError` set, raised so the agent loop's
    `governed_call` turns it into a tool message the model can see."""


@dataclass(frozen=True)
class ToolOutcome:
    is_error: bool
    text: str


@asynccontextmanager
async def connect(
    server: MCPServer | None = None,
    *,
    identity: str | None = None,
    mode: Mode = "auto",
) -> AsyncIterator[Client]:
    """Open an in-process MCP session to the repository's server.

    `identity` is who the server runs as, fixed when it is created: the
    in-process stand-in for starting a stdio server with its identity in the
    environment. It is not something the client can change per request.
    """
    async with Client(server or create_mcp_server(identity), mode=mode) as client:
        yield client


def request_meta(
    portfolio_id: str | None = None, *, claimed_identity: str | None = None
) -> dict[str, Any]:
    """Request metadata: the portfolio, and optionally an identity claim.

    A claim grants nothing. The server compares it with the identity it was
    started as and refuses a mismatch.
    """
    meta: dict[str, Any] = {}
    if portfolio_id is not None:
        meta["portfolio_id"] = portfolio_id
    if claimed_identity is not None:
        meta["identity"] = claimed_identity
    return meta


async def call(
    client: Client,
    tool: str,
    arguments: dict[str, Any],
    *,
    portfolio_id: str | None = None,
    claimed_identity: str | None = None,
) -> ToolOutcome:
    result = await client.call_tool(
        tool,
        arguments,
        meta=request_meta(portfolio_id, claimed_identity=claimed_identity),
    )
    text = "\n".join(getattr(item, "text", "") for item in result.content)
    return ToolOutcome(bool(result.is_error), text)


def mcp_tools_for_loop(
    identity: str,
    portfolio_id: str | None = None,
    *,
    server_factory: Any = create_mcp_server,
    mode: Mode = "auto",
) -> list[Tool]:
    """Discover tools over MCP and wrap each for the Agent foundations loop.

    `server_factory(identity)` builds a server bound to `identity`. The loop
    is synchronous, so each call opens its own short session. That is safe
    because nothing carries over between calls: under 2026-07-28 no request
    may rely on earlier ones over the same connection, and under the legacy
    handshake each new session initializes itself. It works in both modes;
    see `test_a_fresh_session_per_call_works_in_either_protocol_mode`.
    """

    async def discover() -> list[Any]:
        async with connect(server_factory(identity), mode=mode) as client:
            return list((await client.list_tools()).tools)

    def make_function(name: str):
        def invoke(**arguments: Any) -> str:
            async def run() -> ToolOutcome:
                async with connect(server_factory(identity), mode=mode) as client:
                    return await call(
                        client, name, arguments, portfolio_id=portfolio_id
                    )

            outcome = asyncio.run(run())
            if outcome.is_error:
                raise ToolExecutionError(outcome.text)
            return outcome.text

        return invoke

    return [
        Tool(
            name=tool.name,
            # Descriptions come from the server. The specification treats tool
            # descriptions and annotations as untrusted unless the server is
            # trusted; the model reads them, but they grant nothing.
            description=tool.description or "",
            parameters=tool.input_schema,
            function=make_function(tool.name),
        )
        for tool in asyncio.run(discover())
    ]
