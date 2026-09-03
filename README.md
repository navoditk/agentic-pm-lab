# Agentic AI Learning Journey: Portfolio Management & Optimization

This repository is a hands-on learning laboratory for building a trusted,
fixed-income-first Portfolio Manager (PM) AI proof of concept. It combines
deterministic financial analytics with LangGraph/Deep Agents, governance,
evaluation, observability, public-data provenance, AWS Bedrock AgentCore
patterns, MCP, and GitHub Copilot Canvas.

It is deliberately company-agnostic and uses only public or clearly labelled
mock data. It is not an investment adviser, trading system, autonomous order
executor, or production deployment.

## The gist in five minutes

The central design question is: **how can an AI assist a PM without turning
plausible language into an unaudited investment decision?** The repository's
answer is a layered workflow:

```text
public/mock data -> deterministic tools -> governed agent workflow
                  -> evidence, evaluation, audit, human review
                  -> report or allocation proposal, never an order
```

The LLM reasons, delegates, retrieves, and narrates. Python functions perform
pricing, risk, scenarios, backtests, and portfolio optimization. Authorization
is enforced outside prompts. Every result should expose assumptions, data
vintage, evidence, limitations, approval state, and reproducibility metadata.

The repository is both a completed 21-day local implementation path and a
deliberately bounded platform-shaped proof of concept whose hosted and
production gaps remain visible.

## Goals

The project set out to:

1. Build deterministic bond, curve, portfolio, risk, scenario, research, and
   constrained-optimization tools with machine-readable contracts.
2. Compose those tools into single-agent and multi-agent LangGraph/Deep Agents
   workflows with Macro, Quant/Risk, and Fundamental specialists.
3. Add financial-services controls: identity, Cedar authorization, guardrails,
   tool-boundary enforcement, human approval, audit, provenance, and safe
   failure recovery.
4. Instrument the workflow with OpenTelemetry and evaluate routing, tool use,
   arguments, retrieval, answers, policy, and guardrail behavior separately.
5. Expose the governed workflow through MCP, four Canvas projects, scheduled
   automation, and an AWS Bedrock AgentCore deployment path.
6. Make the repository teachable through tutors, quizzes, worked examples,
   architecture documents, references, and reproducible local exercises.

The authoritative business questions, success tiers, and non-goals are in the
[PRD](docs/architecture/PRD.md). The current implementation and evidence are
in [ARCHITECTURE](docs/architecture/ARCHITECTURE.md), [PROGRESS](PROGRESS.md),
and the [evidence ledger](docs/evidence/EVIDENCE.md).

## What is complete today

The local 21-day learning path is complete. The repository currently provides:

| Area | Current state |
|---|---|
| Analytics | Bond/option pricing, curves, risk, factor regression, backtesting, scenarios, and portfolio optimization |
| Data | Real-capable yfinance/FRED paths; governed ALFRED, Treasury, SEC, SOFR, CFTC, and Kenneth French connectors; mock holdings/security master |
| Agents | Single-agent and specialist-based Deep Agents; a separate research supervisor; local-model comparison path |
| Governance | Local identities, Cedar tool/resource policy, guardrails, repeated enforcement at FastAPI/MCP boundaries, approval interrupts, audit records |
| Evaluation | Golden, routing, policy, and guardrail cases; versioned baselines; deterministic evaluators; local regression gates |
| Observability | OpenTelemetry traces and metrics with token, latency, retry, tool, and estimated-cost attributes; structured fixture execution envelopes |
| Interfaces | Four Canvas projects, MCP adapter, FastAPI API, Streamlit tutor UI, and approval-only scheduled review workflow |
| AWS | AgentCore Runtime entrypoint and runbooks; live temporary Runtime, Memory, standalone Guardrails, and on-demand Evaluation evidence |
| Learning | Fourteen tutor topics, deep-dive companions, 20–30-question quizzes, learner-progress tracking, source catalog, and no-cost exercises |

Run the local verification yourself:

```bash
UV_CACHE_DIR=/tmp/agentic-pm-lab-uv-cache uv run pytest -q
UV_CACHE_DIR=/tmp/agentic-pm-lab-uv-cache uv run python scripts/check_progress.py
UV_CACHE_DIR=/tmp/agentic-pm-lab-uv-cache uv run python scripts/check_skill_contracts.py
```

The current suite is expected to report **203 passing tests**. The progress
table is intentionally local: a green local check does not imply a successful
cloud request, live provider response, or hosted Canvas session.

## What is not complete, and why that matters

This is a learning-scale proof of concept, not an institutional production
platform. The remaining boundaries are intentional and documented:

- portfolio positions, security-master classifications, and the research
  endpoint remain mock or fixture-backed;
- the 23-question PM catalog is broader than the active 15-case golden dataset;
  deferred questions include production liquidity, benchmark-relative risk,
  mortgage analytics, sentiment, and multi-period optimization;
- AgentCore Gateway live evidence and Copilot-hosted browser evidence remain
  unclaimed, although the implementation paths exist;
- hosted AgentCore evidence proves bounded integrations and a full deterministic
  capstone execution, not high availability, production operations, or every
  research-provider path;
- optimization remains learning-scale: supplied estimates, long-only
  constraints, turnover/concentration checks, and documented fallbacks are not
  a production risk model;
- the system proposes and explains; it does not place or execute trades.

See [EVIDENCE](docs/evidence/EVIDENCE.md) for local versus live proof and
[PLAN_REVIEW](docs/learning/PLAN_REVIEW.md) for the independent completion audit.

## The architecture in one view

| Layer | Repository implementation | Trust boundary |
|---|---|---|
| Data | DuckDB, public connectors, provenance, point-in-time checks, fixture catalog | Structured data feeds calculations; narrative evidence cannot silently become a risk input |
| Control | Identity, Cedar policy, guardrails, audit, human approval | Authorization is enforced before model access and again at the tool boundary |
| Tool | Deterministic analytics with JSON Schema contracts, FastAPI, MCP | Tools validate inputs and re-check identity/resource entitlement |
| Agent | LangGraph/Deep Agents, specialist delegation, context assembly, recovery | LLM output is interpretation, not financial truth |
| Interactive | Canvas, Streamlit, scheduled review, AgentOps surfaces | UI is not a security boundary |
| Runtime | Local fixture host and AgentCore Runtime/Gateway intent | Hosted deployment is temporary evidence, not an always-on service |
| Observability/evaluation | OTel, LangSmith-compatible experiments, baselines, replay, cost accounting | Logs and traces minimize prompts, holdings, secrets, and denied content |

The important pattern is not any single vendor. It is the separation of
calculation, reasoning, policy, evidence, and human decision-making.

## Learning path and depth

For a first pass, use [START_HERE](docs/learning/START_HERE.md). For complete
course instructions, use the [Tutor Course Guide](docs/learning/TUTOR_COURSE_GUIDE.md).
The [Depth Path](docs/learning/DEPTH_PATH.md) supplies the cross-topic study
method. Each tutor now has a machine-readable course outline containing
prerequisites, objectives, lessons, a local lab, a failure lab, and a
teach-back assessment.

The fourteen tutor topics cover FICC, portfolio construction, agent
architecture, LangGraph/Deep Agents, AWS AgentCore, data/provenance, evaluation
and AgentOps, OpenTelemetry, investment committees, Canvas/MCP, development
lifecycle, governance/delivery, document-to-skill workflows, and public
investment data. Each course has a compact persona, a repository-grounded
deep dive, explicit lessons and objectives, worked and adversarial examples,
a deterministic 25-question quiz, a local lab, a failure lab, and a teach-back
assessment. This supports complete self-paced learning courses, but does not
claim production certification or expert mastery.

Use the [Tutor Runbook](docs/guides/TUTOR_RUNBOOK.md) to invoke a tutor from a
CLI or compatible coding-agent surface. Understanding is recorded separately
from implementation status in `docs/learning/LEARNER_PROGRESS.md`.

## No-cost ways to make the platform more comprehensive

The next improvements do not require live model or AWS spending:

- expand the golden dataset from 15 cases to cover every currently supported
  business question, with explicit `deferred` cases for unsupported questions;
- add deterministic synthetic fixed-income fixtures for key-rate DV01,
  spread duration, carry/rolldown, benchmark-relative risk, liquidity, and
  mortgage-style negative convexity;
- add walk-forward, look-ahead, stale-price, survivorship, corporate-action,
  slippage, and infeasible-constraint tests;
- add synthetic multi-session Memory fixtures and local Gateway contract tests
  without deploying AWS resources;
- add citation completeness, grounding, abstention, uncertainty, and
  contradiction evaluators over authored fixtures;
- add local fault-injection scenarios for stale, unavailable, duplicated,
  conflicting, unlicensed, and prompt-injected evidence;
- add a link checker, reference freshness metadata, and a per-topic study
  matrix; and
- add a fully local browser/Canvas replay harness that checks state transitions
  and evidence presentation without claiming Copilot-hosted behavior.

These improvements increase coverage and teaching value while preserving the
repo's evidence boundary.

## Repository map

| Need | Start here |
|---|---|
| Install and verify | [INSTALL.md](INSTALL.md) |
| Current status and evidence | [PROGRESS.md](PROGRESS.md), [EVIDENCE.md](docs/evidence/EVIDENCE.md) |
| Goals and acceptance criteria | [PRD.md](docs/architecture/PRD.md) |
| Current architecture and security | [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md), [DIAGRAMS.md](docs/architecture/DIAGRAMS.md) |
| Day-by-day build plan | [PLAN.md](docs/PLAN.md) |
| Local operation | [RUNBOOK.md](docs/guides/RUNBOOK.md) |
| AWS AgentCore path | [AWS AgentCore setup](docs/guides/AWS_AGENTCORE_SETUP.md), [Gateway exercise](docs/guides/AGENTCORE_GATEWAY_SETUP.md) |
| Tutors and courses | [START_HERE.md](docs/learning/START_HERE.md), [Tutor Course Guide](docs/learning/TUTOR_COURSE_GUIDE.md), [Depth Path](docs/learning/DEPTH_PATH.md), [Tutor Runbook](docs/guides/TUTOR_RUNBOOK.md) |
| References | [REFERENCES.md](docs/reference/REFERENCES.md) |
| Experiments and comparisons | [experiments README](experiments/README.md), [benchmark report](docs/learning/CANONICAL_PM_BENCHMARK_REPORT.md) |
| Public-data catalog | [data README](data/README.md), [sample pack](data/samples/public_investment/README.md) |

## Getting started

```bash
uv sync
uv run pytest -q
uv run python scripts/tutor.py
uv run python scripts/tutor.py langgraph-deep-agents-tutor --quiz
```

Then follow [START_HERE](docs/learning/START_HERE.md). All unit tests mock
external dependencies. Never add credentials, proprietary data, or claims of
live evidence without recording the corresponding experiment and cleanup
state.

## Influences and durable takeaways

The multi-agent PM shape is adapted from OpenAI's [Multi-Agent Portfolio
Collaboration](https://developers.openai.com/cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration)
example and reimplemented with LangGraph/Deep Agents. The complete,
topic-organized bibliography is in [REFERENCES.md](docs/reference/REFERENCES.md).

The durable takeaways are:

- deterministic math should remain outside the LLM;
- policy must be enforced at the boundary, not inferred from prompts;
- evidence, timestamps, provenance, and uncertainty matter as much as answers;
- evaluation must measure routing, tools, policy, safety, and answer quality
  separately; and
- a deployment, a model response, and a production-ready system are three
  different claims.

License: [MIT](LICENSE).
