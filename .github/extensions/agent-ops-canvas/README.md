# Agent Operations

Agent Operations — a canvas built on the Canvas Kit. Day 19 extends it into the
research and committee operations surface.

A GitHub Copilot App **canvas extension** generated with the `create-canvas-app`
skill (data template). The agent and the user share the same live
state through the same action handlers; the view renders with Preact + htm and a
vendored kit — no build step, no `package.json`.

## Day 19 panels

The shared state and handlers expose evidence-provider health, thesis versus
rebuttal findings, allocation deltas, fixed-income provenance and hedge
assumptions, promotion/SLO checks, and incident/replay controls. A degraded
provider is shown as degraded; the Canvas never fabricates replacement research
and remains an interaction surface rather than a trust boundary.

## Layout

```
extension.mjs   the ONLY file that imports the Copilot SDK (thin adapter)
canvas.mjs      canvas config: state load/save + action handlers (SDK-free)
canvas-kit/     vendored kit (copied verbatim; do not edit)
web/index.html  shell that loads /kit/theme.css and ./app.mjs
web/app.mjs     your Preact view
test/smoke.test.mjs  boots the runtime over HTTP and exercises the actions
```

This is an **external-data** canvas: it fetches from a source URL inside an action handler (always with `AbortSignal.timeout`), captures failures into state, and auto-refreshes on a visibility-gated timer via the kit's `pollWhileVisible` helper.

## Validate

```
node test/smoke.test.mjs
```

## Install

Copy this folder into `.github/extensions/agent-ops-canvas` (in-repo),
`$COPILOT_HOME/extensions/agent-ops-canvas` (personal), or
`$COPILOT_HOME/session-state/<sessionId>/extensions/agent-ops-canvas` (current session
only — disappears with the session), then run `extensions_reload` and open it
with `open_canvas` (`canvasId: "agent-ops-canvas"`).

## Keeping the kit current

`canvas-kit/` is a vendored snapshot of the create-canvas-app `kit/`. Re-sync it
with the skill's `scripts/sync-kit.mjs`, and gate drift in CI with
`scripts/check-kit-freshness.mjs`.
