---
name: new-tool-onboarding
description: Add a new deterministic Tool Layer capability end to end, including analytics, contract, governed API exposure, tests, and documentation.
license: MIT
covers:
  - contracts/tools
  - src/analytics
  - src/api/main.py
last_verified_commit: 21e2ec3
---

# new-tool-onboarding

Use this skill when adding a capability that does not already exist. If a
function or endpoint already carries a `# MOCK` marker, use
`mock-to-real-migration` instead.

## Checklist

1. Define the deterministic analytics function in `src/analytics/` with fully
   typed inputs and outputs. Keep network and framework concerns outside it.
2. Validate caller-fixable input errors with specific `ValueError` messages;
   never return a success-shaped placeholder.
3. Derive `contracts/tools/<function>.schema.json` from the implemented
   signature and output. Validate the schema itself before using it.
4. Add or extend the FastAPI route in `src/api/main.py`. Translate input errors
   at this boundary and re-check authorization using the canonical tool name.
5. Update the role configuration only when the new tool requires a deliberate
   permission change. Add allowed and denied authorization tests together.
6. Add hand-calculable unit tests for the function and contract tests that
   validate actual function input/output against its schema.
7. Check whether the tool also needs MCP or Canvas exposure. Those surfaces
   must call the same governed implementation rather than bypassing it.
8. Update `ARCHITECTURE.md`, progress checks, relevant skills' `covers` and
   `last_verified_commit`, and any glossary term introduced by the tool.

## Completion criteria

The capability is complete only when its pure function, schema, governed
boundary, positive and negative tests, audit decision, and documentation agree
on the same name and observable behavior.
