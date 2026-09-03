# Governance and delivery — deep dive

*Companion to [`.github/agents/governance-delivery-tutor.agent.md`](../../../.github/agents/governance-delivery-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py governance-delivery-tutor --quiz`.*

## What this actually is

"Governance" in an agentic system means answering, for every request: who is
this, what are they allowed to do, is the content safe, and did the tool
actually check before acting? "Delivery" means the CI/CD machinery that
decides whether a change is allowed to reach `main` at all. Neither is a
single check — real production agent systems separate identity
(authentication), permission (authorization), content safety (guardrails),
and enforcement (the tool boundary re-checking at execution time) into
independently testable concerns, because conflating them creates a single
point of failure: if "is this allowed" and "is this safe" are the same check,
a content-safety bypass becomes an authorization bypass too.

This repository implements that separation for real, not just as a diagram.
Understanding it means being able to answer, for any given decision, exactly
which of the four layers made it — and knowing that none of the other three
are a substitute if one is missing.

## Core concepts

- **AuthN (authentication).** Resolving *who* is calling. Here: an identity
  string mapped to a role via `config/roles.yaml`, checked by
  `src/control/identity.py`. Three local test identities only — this is a
  learning stand-in, not credential authentication.
- **AuthZ (authorization).** Deciding *what* an authenticated identity may
  do. Here: Cedar policy evaluation (`governance/policies/*.cedar`),
  default-deny, evaluated separately for tool invocation
  (`tool-permissions.cedar`) and portfolio resource access
  (`portfolio-access.cedar`).
- **Guardrails.** Content-level safety, independent of who is asking or what
  they're authorized to do. Here: `src/control/guardrails.py`'s shared
  denied-term/topic check, applied to input, context, and output.
- **Tool enforcement.** The re-check that happens at the moment a tool
  actually executes, regardless of what upstream layers already decided.
  Defense in depth: even a correctly-authorized request gets checked again at
  the boundary.
- **Default-deny.** The posture where an unknown identity, tool, or resource
  has *no* access by default — access must be explicitly granted, never
  inferred from absence of a denial.
- **Policy-as-code.** Expressing authorization rules (here, in Cedar) as
  version-controlled, testable files rather than scattered `if` statements or
  database rows a developer could edit without review.
- **Release gate.** A CI check that must pass before a change can merge or
  deploy — the mechanism that turns "we intend this to be true" into "this is
  actually enforced before anyone can bypass it by accident."

## How this repository implements it

`docs/architecture/ARCHITECTURE.md`'s "Four independently enforced concerns"
table is the canonical reference. Each row names the local mechanism, the
failure behavior, and (where relevant) the AWS mapping captured for Day 12:

- **AuthN** → `config/roles.yaml` + `src/control/identity.py`. Unknown or
  missing identity is rejected before authorization is even attempted.
- **AuthZ** → `governance/policies/*.cedar`, evaluated via
  `check_tool_permission()`/`check_portfolio_access()` in
  `src/control/authorization.py`. Tools are filtered from an agent's toolset
  *before* model binding — an unauthorized tool isn't just refused at call
  time, it's never offered to the model in the first place.
- **Guardrails** → `src/control/guardrails.py`'s `enforce_content()`, a pure
  denied-term/topic-pattern function (no model call) applied at input,
  context, and output stages via `enforce_agent_input()`/
  `enforce_agent_output()`.
- **Tool enforcement** → FastAPI (`src/api/main.py`) and MCP
  (`src/mcp_server/server.py`) both independently re-check tool and resource
  access immediately before calling into `src/analytics/`, per ADR 0017's
  requirement that Gateway (or its local equivalent) is the *only* accepted
  path to deterministic tools.

None of these four consult a skill's `contract.yaml` or a prompt's stated
intent — that's a documentation artifact, not a decision-maker (see the
agent-development-lifecycle deep dive for the companion half of this
distinction).

CI mirrors this separation. `.github/workflows/authorization-tests.yml` runs
on every push/PR touching `governance/**`, `config/roles.yaml`, or
`src/control/**`: it validates Cedar policy syntax
(`scripts/check_cedar_policies.py`) and then runs
`governance/tests/` (which includes `test_authorization.py`,
`test_prompt_injection.py`, and `test_sensitive_output.py` — the adversarial
negative cases, not just happy-path checks) alongside
`tests/unit/control` and `tests/unit/agents`. No PR touching those paths
merges without this passing — it is not advisory. The other release gates
(`ci.yml` for lint+test, `contract-tests.yml` for skill schema/static/mock/
negative checks, `skills-freshness.yml`, `eval-regression.yml`) are the
remaining pieces of what a release actually depends on; a governance change
that only passes `ci.yml` but not `authorization-tests.yml` is not releasable.

Human approval and audit are release evidence, not an afterthought:
`run_backtest` is configured with `interrupt_on` by default, pausing
execution for a human decision; every authorization/guardrail decision is
recorded to an append-only `audit.jsonl` with identity, role, tool, resource,
decision, enforcement layer, and OTel trace ID. AWS teardown sequences
(`docs/guides/AWS_AGENTCORE_SETUP.md`, `docs/guides/AGENTCORE_GATEWAY_SETUP.md`)
are the same idea applied to infrastructure: a release checklist for anything
touching AWS points at an explicit, documented teardown step, not "someone
will remember to clean it up."

## Worked walkthrough

Trace one denied request through all four layers:

1. Read `governance/policies/tool-permissions.cedar` and note which tools
   each role (`pm`, `risk`, `admin`) may invoke.
2. Read `governance/tests/test_authorization.py` for a concrete
   denied-request test case, and run it:
   ```bash
   uv run pytest governance/tests/test_authorization.py -q
   ```
3. Trace the same boundary through `src/control/authorization.py`'s
   `tools_for_identity()` — note it *filters* the toolset before an agent is
   even constructed, rather than constructing the agent with every tool and
   hoping the model declines to call the wrong one.
4. Read `governance/tests/test_prompt_injection.py` and
   `test_sensitive_output.py` — these are the guardrail layer's adversarial
   coverage, independent of the authorization layer you just traced.
5. Confirm CI wiring: read `.github/workflows/authorization-tests.yml`'s
   `paths` filters and note exactly which changed files would trigger it —
   this is the difference between "we have tests" and "the tests are a gate."

## Common pitfalls

- **Using a guardrail to solve an authorization problem, or vice versa.**
  "Block PORT_B access with a content guardrail" conflates two different
  questions: guardrails answer "is this content safe," Cedar answers "is this
  identity allowed to touch this resource." A content filter cannot express
  "this specific identity may not see this specific portfolio," and trying to
  make it do so either fails silently or over-blocks unrelated content.
- **Treating a passing `ci.yml` as sufficient to merge.** `ci.yml` (lint and
  unit tests) passing says nothing about whether a change to
  `governance/**` or `src/control/**` preserves the authorization boundary —
  that's specifically what `authorization-tests.yml` exists to check, and it
  runs as a separate, mandatory gate for exactly that reason.
- **Skipping human approval because the model seems confident.** `run_backtest`'s
  `interrupt_on` pause is a property of the tool's configuration, not a
  judgment call the model or the caller gets to override based on how
  confident an answer looks. Confidence is not evidence of correctness, and
  the approval boundary doesn't have a confidence-based bypass.

## Further reading

- [`docs/reference/REFERENCES.md#security-authnauthz-policy-as-code-prompt-injection`](../reference/REFERENCES.md#security-authnauthz-policy-as-code-prompt-injection)
- `docs/architecture/ARCHITECTURE.md`'s full "Security Model" section
  (trust boundaries, the four-concern table, threat model, human approval/
  audit/secrets, local-versus-AgentCore mapping)
- `docs/adr/0017-agentcore-gateway-only-tool-path.md`
- `docs/guides/GITHUB_WORKFLOWS.md` for the complete CI workflow map
