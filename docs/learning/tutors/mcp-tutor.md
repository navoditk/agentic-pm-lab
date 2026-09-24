# Model Context Protocol — deep dive

*Companion to [`.github/agents/mcp-tutor.agent.md`](../../../.github/agents/mcp-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz mcp-tutor`.*

This Agent core course assumes [Agent foundations](agent-foundations-tutor.md):
the agent loop, tool calling, and the allowlist in `governed_call`. It teaches
MCP from the specification, [version 2026-07-28](https://modelcontextprotocol.io/specification/latest),
and from a real session against this repository's server. Everything runs
in-process and offline.

## What this actually is

In Agent foundations, the tools lived in the same process as the loop. MCP is
what you use when they do not: a standard way for an application to discover
and call tools, read context, and use prompt templates served by something
else. The specification calls the application the **host**, its connector the
**client**, and the provider the **server**; messages are JSON-RPC 2.0.

The protocol does not decide who may do what. It carries the request; your
client and your server each still have to govern it. That is the thread
through this course: an MCP boundary adds a second place where observability,
traceability, governance, and evaluation must hold, not a place where they
stop.

## Core concepts

- **Primitives.** Servers offer **tools** ("functions for the AI model to
  execute", model-controlled), **resources** (context and data), and
  **prompts** (templated messages and workflows for users). The tools page
  adds that there **SHOULD** always be a human able to deny a tool invocation.
- **Stateless requests.** In 2026-07-28, "all the information needed to
  process a request is contained in the request itself." Every request
  carries `io.modelcontextprotocol/protocolVersion` and `clientCapabilities`
  in `_meta`, and "an open connection, such as a STDIO process, is not a
  conversation or session." Earlier revisions negotiated once per connection
  with an `initialize` handshake; the pinned SDK still speaks that with
  `mode="legacy"` (2025-11-25).
- **Transports.** Two are standard: **stdio** (newline-delimited JSON-RPC over
  a client-launched subprocess's standard streams) and **Streamable HTTP**
  (each message an HTTP POST to one endpoint).
- **Two kinds of error.** *Protocol errors* are for problems with the request
  itself, such as an unknown tool or a malformed request, and are JSON-RPC
  errors. *Tool execution errors* (input validation, API failures, business
  rules) are results with `isError: true`, so the model "can use to
  self-correct". Clients **SHOULD** pass execution errors to the model.
- **Untrusted descriptions.** "Descriptions of tool behavior such as
  annotations should be considered untrusted, unless obtained from a trusted
  server." A description is text the model reads, and it can carry
  instructions.
- **Identity.** On HTTP, the [Authorization framework](https://modelcontextprotocol.io/specification/latest/basic/authorization)
  applies; on stdio, credentials come "from the environment". `clientInfo` and
  `serverInfo` are "self-reported" and should not be relied on "for security
  decisions". The [security best practices](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices)
  forbid **token passthrough**: servers "MUST NOT accept any tokens that were
  not explicitly issued for the MCP server".
- **Trace context.** `traceparent`, `tracestate`, and `baggage` are reserved
  in `_meta` for W3C trace context, so a trace can continue across the
  boundary.

## How this repository implements it

`src/mcp_server/server.py` is the server. `create_mcp_server()` registers each
tool and replaces the schema the SDK generated from Python annotations with
the shared contract from `contracts/tools/`, so FastAPI, MCP, and the tests
agree on one wire schema. Every call goes through `invoke_tool()`, which maps
the identity to a role, checks the tool with Cedar, and checks the portfolio
when the tool has one.

`src/mcp_server/client_lab.py` is the client. `connect()` opens a real,
in-process session with the SDK's `Client`; `call()` returns whether the
result had `isError`; and `mcp_tools_for_loop()` discovers the server's tools
and wraps each as an Agent foundations `Tool`. Each wrapped call opens its own
short session. That is safe because nothing carries over between calls:
the stateless protocol forbids relying on earlier requests, and under the
legacy handshake each new session initializes itself, so it works in both
modes.

The result is **two layers of governance on one call**:

| Layer | Decides | Where | Refusal looks like |
|---|---|---|---|
| Client | Which tools *this agent* may use | `governed_call` in the loop | "not permitted", audited as denied |
| Server | What *this caller* may do, on which portfolio | `invoke_tool` with Cedar | An `isError` result the model reads |

`test_the_agent_loop_governs_mcp_tools_on_both_sides` runs both at once: the
loop refuses a tool it was never allowed, the server refuses a portfolio the
caller is not entitled to, and a third call passes both. The client's audit
records its own decision ("allowed" for the call the server then refused),
because each boundary audits the decision it made.

### Where the SDK and the specification differ

The pinned SDK (mcp 2.0.0) returns a call to an unknown tool as a result with
`isError`, where the specification lists an unknown tool as a protocol error.
`test_this_sdk_reports_an_unknown_tool_as_a_tool_result` pins the SDK's actual
behaviour. The lesson generalises: read the specification, then test what
your implementation does.

### A limitation, taught rather than hidden

This learning server reads the caller's identity from `_meta`, where the
caller puts it. Cedar authorizes that identity correctly: `PM_USER` is refused
`PORT_B`. But nothing verifies who the caller is, so a caller who *claims*
`RISK_USER` can read `PORT_B`.
`test_identity_in_request_metadata_is_asserted_not_authenticated` proves it.
Authorization is enforced; authentication is only asserted. The build lab
fixes it for stdio, the way the specification describes: take identity from
the environment the server was started with.

## The four threads across the boundary

| Thread | At the MCP boundary | Evidence |
|---|---|---|
| **Observability** | The SDK's server span, `tools/call {tool}`, carries `gen_ai.tool.name`, the same convention as the loop's `execute_tool` span. | `test_trace_context_crosses_the_mcp_boundary` |
| **Traceability** | The SDK carries `traceparent` in `_meta`, so the server's authorization and analytics spans join the caller's trace; the client audit record carries the same id. | `test_trace_context_crosses_the_mcp_boundary`, `test_the_agent_loop_governs_mcp_tools_on_both_sides` |
| **Governance** | Client allowlist and server Cedar check, independently; untrusted descriptions grant nothing; missing identity fails closed; claimed identity is not authentication. | `test_a_poisoned_tool_description_grants_nothing`, `test_a_request_with_no_identity_is_refused` |
| **Evaluation** | Grade the outcome of an MCP-backed run as in Agent foundations, and require the one path property that matters here: a refusal reached the model as an `isError` result. | `src/foundations/grading.py` |

## Worked walkthrough

1. Run the course's tests:
   ```bash
   uv run pytest tests/unit/mcp_server -q
   ```
2. Read `test_the_client_negotiates_the_stateless_or_the_handshake_protocol`.
   Explain what the server learns, and when, in each mode.
3. Read the three error tests. For each, say whether the specification calls
   it a protocol error or a tool execution error, and what the model sees.
4. Read `test_identity_in_request_metadata_is_asserted_not_authenticated`.
   Write down the one line in `server.py` that makes the spoof possible.
5. Read `test_the_agent_loop_governs_mcp_tools_on_both_sides` and draw both
   governance layers, marking which one refused each call.
6. Read `test_a_poisoned_tool_description_grants_nothing`. Rewrite the
   poisoned description so the model sends holdings as an argument instead of
   calling a tool, and say which control would have to stop that.

## Common pitfalls

- **Trusting what the caller says about itself.** Identity in `_meta`,
  `clientInfo`, or a role string is a claim. Authenticate it, or do not use it
  for authorization.
- **Trusting what the server says about itself.** Tool descriptions and
  annotations are untrusted unless the server is trusted; they must never
  decide what is allowed.
- **Treating every normal result as success.** Execution errors arrive as
  results with `isError`. Check it on every result.
- **Connection state.** Under 2026-07-28 a connection is not a session. Pass
  an explicit handle for state that spans requests, and authorize it every
  time.
- **Token passthrough.** Accepting a token issued for another service and
  forwarding it downstream is forbidden by the specification.
- **Assuming the SDK follows the spec exactly.** Test the behaviour you depend
  on.

## Further reading

- [`docs/reference/REFERENCES.md#model-context-protocol-mcp`](../../reference/REFERENCES.md#model-context-protocol-mcp)
  — the specification pages this course cites.
- [OpenTelemetry](opentelemetry-tutor.md), the next course: the spans and
  trace context used here, in depth.
- [Copilot Canvas](copilot-canvas-mcp-tutor.md), in Platforms: a Canvas
  action carried through this same MCP boundary.
