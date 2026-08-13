# Tutor Agent Runbook

The tutor agents are standalone, read-only learning personas for the 20-day
PM AI roadmap. They are separate from operational agents such as
`risk-narrator-agent`, `eval-triage-agent`, `pr-reviewer-agent`, and
`skills-auditor-agent`. A tutor explains concepts, points to repository
evidence, and proposes a small exercise; it does not edit code, authorize
access, run paid evaluations, place orders, or make investment recommendations.

## Tutor catalog

| Tutor | Best used for | Main roadmap days |
|---|---|---|
| `ficc-tutor-agent` | Rates, credit, curves, duration, convexity, and FICC vocabulary | 2–3, 15–18 |
| `portfolio-construction-tutor` | Optimization, constraints, risk budgets, implementation, and validation | 3, 12, 15, 20 |
| `agent-architecture-tutor` | Agent/workflow design, context, skills, tools, memory, recovery | 4–7, 11–20 |
| `langgraph-deep-agents-tutor` | LangGraph state, Deep Agents, delegation, interrupts, and checkpoints | 4–5, 11, 17–20 |
| `aws-agentcore-tutor` | Bedrock, AgentCore services, IAM, deployment, observability, teardown | 12–14, 19–20 |
| `data-provenance-research-tutor` | Point-in-time data, EDGAR, evidence, sentiment, and research quality | 2, 15–17, 20 |
| `evaluation-agentops-tutor` | Golden datasets, eval dimensions, regression, SLOs, and operations | 6, 9, 13–14, 19–20 |
| `opentelemetry-tutor` | Traces, spans, attributes, propagation, privacy, and AgentCore observability | 6, 9, 12–14, 19 |
| `investment-committee-tutor` | Thesis review, Devil’s Advocate, evidence grading, dissent, and approval | 17–20 |
| `copilot-canvas-mcp-tutor` | Canvas UX, shared state, MCP boundaries, approvals, and capability tests | 8–11, 19–20 |
| `agent-development-lifecycle-tutor` | Skills, prompts, custom agents, contracts, tests, freshness, and cross-tool practice | 4, 8, 11, 19–20 |
| `governance-delivery-tutor` | CI/CD, policy-as-code, guardrails, approvals, audit, promotion, rollback, and teardown | 6–7, 11–14, 19–20 |
| `document-to-skill-tutor` | PDF/model-document extraction, generated skills, formula validation, provenance, sandboxing, and Deep Agent interfaces | 15–20 |

## How to use one independently

Select the project-scoped agent in GitHub Copilot, Copilot CLI, Claude Code, or
another compatible agent surface that reads `.github/agents/`. The same prompt
works across tools:

```text
Use portfolio-construction-tutor. Explain minimum volatility versus maximum
Sharpe using the repository's toy portfolio. Cite the implementation and tests,
state which inputs are supplied or mock, and finish with one local exercise.
```

For a deeper session:

```text
Use aws-agentcore-tutor. Teach me the Day 12 direct-code deployment path. Start
with the account prerequisites, map each repository config field to AgentCore,
show what evidence would prove a live deployment, and quiz me one question at a
time. Do not ask for credentials or claim that a resource exists.
```

For adversarial practice:

```text
Use opentelemetry-tutor. I want to put the full prompt and portfolio holdings
into every span so debugging is easier. Challenge this design, propose a
privacy-safe schema, and point to the repository test or policy that supports
your answer.
```

Each tutor file contains five worked examples and three negative/adversarial
examples. Use those examples as acceptance tests for tutor behavior. Record the
tutor name, prompt, repository sources cited, answer, exercise, and limitation;
never record credentials or private data.

## Document-to-skill examples

Use `document-to-skill-tutor` independently for the document-intelligence
deliverable.

```text
Use document-to-skill-tutor. Given this public equity-risk model PDF, explain
volatility, beta, tracking error, and drawdown. Preserve page citations, list
assumptions and units, identify missing inputs, and separate document claims
from repository implementation.
```

```text
Use document-to-skill-tutor. Design a generated package with SKILL.md,
contract.yaml, document-manifest.json, five worked questions, three refusal
cases, and source-page references. Do not generate executable code yet.
```

```text
Use document-to-skill-tutor. Identify formulas precise enough to implement as
deterministic functions. For each, provide inputs, units, source page,
assumptions, edge cases, and a source-derived test vector. Flag ambiguity.
```

```text
Use document-to-skill-tutor. Review a candidate calculate_tracking_error
function against the document's formula and worked example. Check frequency,
annualization, missing data, units, and provenance. Return pass, fail, or
needs-human-review.
```

```text
Use document-to-skill-tutor. Design a Deep Agent over the reviewed skill with
list_sections, retrieve_passage, show_formula, explain_assumption,
run_source_example, and run_validated_calculation. Define refusal behavior.
```

Benefits include faster assimilation of unfamiliar model documents, reusable
document-specific skills, explainable formula walkthroughs, source-linked
calculations, and clear comparison with the repository's deterministic risk
engine. The tutor must reject automatic conversion of every paragraph into
executable code, refuse to guess an unspecified annualization factor, and treat
uploaded document instructions as untrusted content.

## Local evidence loop

Tutors are read-only, so their primary test is answer quality and source
grounding. Validate the implementation they reference with:

```bash
UV_CACHE_DIR=/tmp/agentic-pm-lab-uv-cache uv run pytest
UV_CACHE_DIR=/tmp/agentic-pm-lab-uv-cache uv run ruff check src tests
```

Useful focused checks include:

```bash
uv run pytest tests/unit/analytics/test_optimizer.py -q
uv run pytest tests/unit/control/test_guardrails.py -q
uv run pytest tests/unit/runtime tests/unit/evals -q
node --test .github/extensions/portfolio-risk-canvas/tests/*.test.mjs
```

When a tutor describes a live service, distinguish repository code/tests,
local mocks/deployment intent, and captured cloud/API/Canvas evidence. Tutors
must not upgrade the first two levels into the third. See
[`AGENT_RUNBOOK.md`](AGENT_RUNBOOK.md), [`REFERENCES.md`](REFERENCES.md), and
[`RUNBOOK.md`](RUNBOOK.md) for broader standalone, study, and operations flows.
