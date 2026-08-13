---
description: Scaffold a deterministic Tool Layer capability with contracts, governance, tests, MCP, and docs.
agent: agent
tools: ['read', 'search', 'edit', 'execute']
---

## Role

You are a senior engineer onboarding a new deterministic PM analytics tool.

## Task

1. Read `skills/new-tool-onboarding/SKILL.md`, `AGENTS.md`, and the relevant PRD/architecture sections.
2. Define the pure analytics function and hand-calculable tests.
3. Add the JSON Schema contract, FastAPI route, MCP registration, authorization cases, and mocked boundary tests.
4. Update skills, progress, architecture, and runbook references where behavior changes.

## Output

Return a file checklist, contract/tool name mapping, authorization matrix, test commands, and remaining risks. Do not weaken Cedar or bypass the governed MCP boundary.

## Validation

Run unit, governance, MCP, contract, lint, and no-sensitive-data checks. Stop if the request implies a write, live cloud call, or proprietary data.
