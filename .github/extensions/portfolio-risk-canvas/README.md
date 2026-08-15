# Portfolio Risk

Portfolio Risk — a canvas built on the Canvas Kit.

A GitHub Copilot App **canvas extension** generated with the `create-canvas-app`
skill (data template). The agent and the user share the same live
state through the same action handlers; the view renders with Preact + htm and a
vendored kit — no build step, no `package.json`.

## Layout

```
extension.mjs   the ONLY file that imports the Copilot SDK (thin adapter)
canvas.mjs      canvas config: state load/save + action handlers (SDK-free)
canvas-kit/     vendored kit (copied verbatim; do not edit)
web/index.html  shell that loads /kit/theme.css and ./app.mjs
web/app.mjs     your Preact view
test/smoke.test.mjs  boots the runtime over HTTP and exercises the actions
```

This is a **governed analytics** canvas: its production integration boundary is
the contract-backed MCP adapter in `src/mcp_server/`, while standalone tests
use deterministic fixtures. Identity and portfolio entitlement are rechecked
at the MCP boundary; the Canvas state is not an authorization source of truth.

The current portfolio and security-master fixtures are explicitly marked mock.
Public FRED/Treasury inputs are shown separately in the provenance panel. A
scenario result therefore cannot be read as a live valuation or trading signal.

## End-to-end PM exercises

The Canvas includes a bounded **PM question exercise** panel with three
questions: a risk snapshot, a +50 bps rates stress, and a PORT_B entitlement
check. Each question uses the same action handler for agent and UI callers and
returns an answer, route, evidence status, and trace identifier. The exercise
runner is deterministic and fixture-backed so it can be used without model
credentials.

See [`docs/CANVAS_EXERCISES.md`](../../../docs/CANVAS_EXERCISES.md) for the
step-by-step exercises and the real-versus-fixture evidence boundary.

## Validate

```
node test/smoke.test.mjs
```

## Install

Copy this folder into `.github/extensions/portfolio-risk-canvas` (in-repo),
`$COPILOT_HOME/extensions/portfolio-risk-canvas` (personal), or
`$COPILOT_HOME/session-state/<sessionId>/extensions/portfolio-risk-canvas` (current session
only — disappears with the session), then run `extensions_reload` and open it
with `open_canvas` (`canvasId: "portfolio-risk-canvas"`).

## Keeping the kit current

`canvas-kit/` is a vendored snapshot of the create-canvas-app `kit/`. Re-sync it
with the skill's `scripts/sync-kit.mjs`, and gate drift in CI with
`scripts/check-kit-freshness.mjs`.
