# Copilot Canvas and MCP — deep dive

*Companion to [`.github/agents/copilot-canvas-mcp-tutor.agent.md`](../../../.github/agents/copilot-canvas-mcp-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py copilot-canvas-mcp-tutor --quiz`.*

## What this actually is

Two separate ideas get bundled under this tutor because they solve the same
underlying problem from opposite ends: **MCP (Model Context Protocol)** is a
standard way for an AI system to call external tools with a shared, typed
contract, and **GitHub Copilot Canvas** is a rich, stateful UI surface an
agent (and a human) can both act on. The connecting question is: when a
button on a screen and a model's tool call both need to reach the same
governed backend, how do you make sure neither path can quietly bypass the
authorization checks the other one goes through?

The naive answer — "the UI is internal, so it can call the backend directly"
— is exactly the failure mode this repository's design rejects. A Canvas
panel is an *interaction surface*: a place to see state and trigger an
action. It is never itself a *trust boundary*. Every real check happens one
layer down, in the same governed tool boundary a model-driven MCP call would
also have to pass through.

## Core concepts

- **MCP (Model Context Protocol).** A protocol for exposing tools to a model
  with a declared input/output schema, so the model (or any MCP client) can
  discover and call them without bespoke integration code per tool.
- **Shared handler pattern.** The same backend function that answers a UI
  click also answers an agent's tool call — there is one implementation, not
  a UI copy and an agent copy that can drift apart.
- **Identity propagation.** A Canvas action or an MCP call carries an
  identity, which the backend resolves to a role and checks *again*, even if
  the caller already believes it's authorized — never trust a caller's claim
  about its own permissions.
- **Provenance display.** Any exposure/scenario/optimization number shown on
  a Canvas panel should be traceable back to its inputs' vintage and
  assumptions, not presented as an unqualified fact.
- **Trust boundary vs. interaction surface.** The distinction this whole
  tutor exists to teach: a Canvas is where you *see* and *trigger* things; the
  governed MCP/tool boundary is where access is actually *decided*.
- **Approval controls.** An action that requires human sign-off (like
  `run_backtest`, per `DEFAULT_INTERRUPT_ON` in `src/agents/multi_agent.py`)
  needs the same interrupt/approval semantics whether it was triggered from a
  Canvas button or a model's tool call.

## How this repository implements it

`src/mcp_server/server.py` is explicit about its own role in its module
docstring: "The MCP server is an adapter, not a second analytics
implementation. Every handler delegates to `src.analytics`... Identity and
portfolio metadata travel in the MCP request context so callers cannot bypass
the Day 7 Cedar checks by calling the MCP server directly." That sentence is
the whole design in one line — read it before anything else in this file.

Concretely: `MCP_TOOL_SPECS` is a tuple of `MCPToolSpec` entries, each pairing
an MCP-facing tool name (like `"scenario_analysis"`) with a
`permission_name` (the Cedar resource identifier), a real analytics handler
(`scenario_analysis` from `src/analytics/scenario.py`), and an optional
`portfolio_field`. `invoke_tool()` is the single choke point every call goes
through: it calls `_identity_allowed()`, which resolves the caller's role via
`role_for_identity()` and checks `check_tool_permission()` — the exact same
Cedar functions the FastAPI layer and the Deep Agent tool-filtering layer
both use (see the `governance-delivery-tutor` and `agent-architecture-tutor`
deep dives). If the spec declares a `portfolio_field`, `_enforce_resource()`
also re-checks `check_portfolio_access()` before the analytics function is
ever called. Note where identity comes from: `_metadata_from_context()` reads
it out of the MCP request's metadata (or, as a fallback, an `x-identity`
header) — never out of the arguments dict the caller supplies, and never out
of anything a model could have written into a prompt. `dispatch()` explicitly
raises `PermissionError("MCP request metadata must include identity")` if
it's missing, rather than defaulting to some permissive identity.

The Canvas side of this repository (`.github/extensions/`) follows the
parallel discipline: `docs/architecture/ARCHITECTURE.md`'s "Interactive
Layer" section describes the Portfolio/Risk Canvas's action contract
(portfolio selection, scenario review, trace focus, provenance, approval
state) and states plainly: "The Canvas keeps mock holdings and scenario
fixtures visibly separate from public curve data; it is not itself a trust
boundary." The same document's "Governed Tool Layer sequence" section traces
the identical enforcement order this MCP server implements —
`check_tool_permission` before `check_portfolio_access`, audited at each
step — showing that the FastAPI path and the MCP path are two adapters over
one governed core, not two independently-trusted systems.

## Worked walkthrough

1. Read `src/mcp_server/server.py`'s module docstring, then
   `MCPToolSpec` and the `MCP_TOOL_SPECS` tuple — pick one entry (e.g.
   `scenario_analysis`) and note its `permission_name` and `portfolio_field`.
2. Trace `invoke_tool()` line by line for that entry: `_identity_allowed()`
   first, then (because `portfolio_field` is set) `_enforce_resource()`,
   then finally `_call_analytics()`.
3. Read `_metadata_from_context()` and confirm identity is read from request
   metadata/headers, never from the tool arguments.
4. Compare this to `src/agents/multi_agent.py`'s `tools_for_identity()` call
   in `specialist_subagents()` — a Deep Agent never even gets an unauthorized
   tool bound to it in the first place, which is defense-in-depth *before*
   the MCP-level re-check, not a replacement for it.
5. Find a Canvas capability test under `.github/extensions/` (per
   `docs/guides/TUTOR_RUNBOOK.md`'s "Local evidence loop", e.g.
   `node --test .github/extensions/portfolio-risk-canvas/tests/*.test.mjs`)
   and read one mocked "denied cross-portfolio request" test case to see this
   same boundary exercised from the UI side.

## Common pitfalls

- **"The UI already checked, so the backend doesn't need to."** Backwards.
  The UI check (if any) is a convenience for the user; the backend re-check
  via `invoke_tool()`/`_identity_allowed()` is the actual control. A UI-only
  check is not a security boundary, it's a typo-preventer.
- **Showing a number without its provenance.** An optimization result,
  scenario impact, or exposure figure rendered on a Canvas panel without its
  data vintage, constraints, and approval state is not more useful for being
  simpler — it's less trustworthy, because the viewer can't tell if it's
  live, mock, stale, or pending review.
- **Persisting credentials in Canvas state so "the agent can just reuse
  them."** Identity should be acquired at runtime and propagated per-request
  (as `_metadata_from_context()` does), never stored as long-lived state a
  Canvas session carries around.

## Further reading

- [`docs/reference/REFERENCES.md#github-copilot-app-canvas-prompts-skills-custom-agents`](../reference/REFERENCES.md#github-copilot-app-canvas-prompts-skills-custom-agents)
  and the adjacent
  [`#model-context-protocol-mcp`](../reference/REFERENCES.md#model-context-protocol-mcp)
  section.
- `docs/architecture/ARCHITECTURE.md`'s "Interactive Layer (Days 8–9)" and
  "Governed Tool Layer sequence (Day 7)" sections for the full request-flow
  diagrams.
- `docs/guides/CANVAS_EXERCISES.md` for hands-on Canvas walkthroughs, and
  `docs/guides/TUTOR_RUNBOOK.md`'s "Local evidence loop" for how to run the
  Canvas capability tests locally.
