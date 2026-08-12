---
name: canvas-capability-authoring
description: Design canvas actions so Copilot and UI controls share validated handlers, durable state, explicit errors, and governed backend access.
license: MIT
covers:
  - .github/extensions
  - tests/unit/extensions
last_verified_commit: 907a375
---

# canvas-capability-authoring

Use this skill before adding or changing a GitHub Copilot canvas capability.
A capability is an agent-callable action and a UI interaction contract, not a
second backend.

## Capability checklist

1. Name actions with a verb first: `add_card`, `move_card`, `refresh_issues`,
   `assign_issue`, `approve_run`. Prefer idempotent verbs such as `set_status`
   over ambiguous toggles when retries are possible.
2. Define a precise `inputSchema` with required fields, enums, and
   `additionalProperties: false`. Validate business rules such as nonblank
   titles inside the handler.
3. Put the action handler in `canvas.mjs`. The agent action and matching UI
   control must call this same handler; never maintain parallel mutations.
4. Return a small object for success. Throw a specific error for invalid input
   or missing state so the runtime surfaces `{ ok: false, code, message }`.
   Store transient refresh failures in `state.error` without pretending the
   refresh succeeded.
5. Mutate shared domain state only through functional `set` calls. Keep draft
   text, active tabs, and filters in local Preact state until the user commits.
6. Key durable state by a stable domain identifier, not a canvas instance ID.
   Use `userStore` for one user's durable state and `githubStore` only when
   collaborators need one shared repository-backed document.
7. Keep the Copilot SDK import in `extension.mjs`; keep `canvas.mjs`, handlers,
   and the HTTP runtime SDK-free so they remain directly testable.
8. Fetch external data only in handlers through `safeFetch`. Render fetched
   values as text, treat them as untrusted, and poll with `pollWhileVisible`.
9. Use the vendored canvas kit unchanged, Primer-backed `ck-*` classes, and
   official GitHub Lucide icons. Render with Preact; never repaint with
   `innerHTML`.
10. A capability that reaches this project's portfolio backend must call the
    governed Tool/MCP interface and propagate caller identity. It must never
    call `src/analytics/` directly or bypass Cedar, guardrails, approval, audit,
    or Tool-boundary re-enforcement.
11. Add a plain handler test for success, invalid input, missing state, and any
    upstream failure. Mock GitHub, OTel/LangSmith, or MCP at the handler
    boundary; do not call real services from unit tests.
12. Run the canvas smoke test over real local HTTP. Then invoke one action from
    the UI and the same action through Copilot, confirming both update the open
    panel without losing draft input.

## Completion criteria

The action name, schema, agent description, UI control, shared handler, durable
state, error behavior, backend authorization path, and tests must describe one
consistent capability. A visual canvas is not complete until it has been
opened and inspected in the GitHub Copilot app.
