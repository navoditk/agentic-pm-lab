# Agentic AI Learning Journey: Portfolio Management & Optimization

This repository is a hands-on learning laboratory for building a trusted,
fixed-income-first Portfolio Manager (PM) AI proof of concept. It combines
deterministic financial analytics with LangGraph/Deep Agents, governance,
evaluation, observability, public-data provenance, AWS Bedrock AgentCore
patterns, MCP, and GitHub Copilot Canvas.

It is deliberately company-agnostic and uses only public or clearly labelled
mock data. It is not an investment adviser, trading system, autonomous order
executor, or production deployment.

## Start here

Three routes in, depending on what you have. All three teach the same
courses from the same canonical sources.

**1. Nothing installed, or you cannot clone the repository.** Read the full
interactive curriculum in a browser — every course, quiz, and reference,
with no download:

> **[Open the curriculum on GitHub Pages](https://navoditk.github.io/agentic-pm-lab/)**

**2. You have a coding agent.** Open this checkout in **Claude Code, GitHub
Copilot, or Codex** and say:

```
agentexpert
```

That loads the [Agentic PM Lab Mastery skill](docs/learning/MASTERY_SKILL.md)
— a source-grounded tutor that runs lessons, quizzes, failure scenarios,
build labs, teach-backs, and a cross-topic assessment, tracking XP and level
as you go. It is read-only and offline by default: no credentials, no live
providers, no investment actions. The same skill is wired for all three
agents, so the experience does not depend on which one you use.

**3. You prefer a terminal.** You need `git` and
[`uv`](https://docs.astral.sh/uv/getting-started/installation/); `uv` fetches
the right Python itself. One command is then the front door:

```bash
git clone https://github.com/navoditk/agentic-pm-lab.git && cd agentic-pm-lab
uv sync
uv run agentic-pm-lab            # all commands, grouped by audience
uv run agentic-pm-lab learn      # every course, in order
uv run agentic-pm-lab quiz agent-architecture-tutor
```

No model, network, or API key is needed for any of the learning commands.
You do **not** need [INSTALL.md](INSTALL.md) to learn — that guide rebuilds
the repository from an empty directory.

The worked example throughout is a fixed-income portfolio manager, but you do
not need finance to learn the agent core. Only the optional Finance domain
module assumes fixed income and portfolio theory; for the math itself, see
[pm-mechanics](https://github.com/navoditk/pm-mechanics).

## Related repositories

This repo is the **agent layer**: how to put deterministic financial analytics
behind an LLM without letting plausible language become an unaudited investment
decision.

[**pm-mechanics**](https://github.com/navoditk/pm-mechanics) is the **math
layer** underneath it — a build-first trainer for the PM/FICC and equity
analytics themselves, where you derive, code, and test each formula by hand.
Its coverage of the finance domain is substantially deeper than this repo's:
37 fixed-income reference pages, 37 notebooks, and tested implementations of
duration, DV01, convexity, Z-spread, CDS, MBS prepayment, Black-Scholes, and
Black-Litterman, among others.

If you take the optional Finance domain module and its fixed-income or
portfolio-theory concepts are unfamiliar, learn them there first. This repo
assumes the math and focuses on governing it; its FICC and
portfolio-construction courses are scoped to what these tools need, and point
at pm-mechanics for the full treatment.

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

## What was built

The 21-day build plan is complete for local, fixture-based verification. For
a guided tour, read the [Phase 1 recap](docs/learning/PHASE_1_RECAP.md): what
each day delivered, a self-check list, and the questions the build should let
you answer. It is also on the
[curriculum site](https://navoditk.github.io/agentic-pm-lab/#roadmap). The
repository currently provides:

| Area | Current state |
|---|---|
| Analytics | Bond/option pricing, curves, risk, factor regression, backtesting, scenarios, and portfolio optimization |
| Data | Real-capable yfinance/FRED paths; governed ALFRED, Treasury, SEC, SOFR, CFTC, and Kenneth French connectors; mock holdings/security master |
| Agents | Single-agent and specialist-based Deep Agents; a separate research supervisor; local-model comparison path |
| Governance | Local identities, Cedar tool/resource policy, guardrails, repeated enforcement at FastAPI/MCP boundaries, approval interrupts, audit records |
| Evaluation | Golden, routing, policy, and guardrail cases; versioned baselines; deterministic evaluators; local regression gates |
| Observability | OpenTelemetry traces *and* metrics as separate signals: spans carrying token, latency, retry, tool and estimated-cost attributes, plus counters and histograms for agent runs, tool calls, tokens, cost, retries and authorization denials; W3C context propagation across process boundaries; parent-based head sampling; structured fixture execution envelopes |
| Interfaces | Four Canvas projects, MCP adapter, FastAPI API, Streamlit tutor UI, and approval-only scheduled review workflow |
| AWS | AgentCore Runtime entrypoint and runbooks; live temporary Runtime, Memory, standalone Guardrails, and on-demand Evaluation evidence |
| Learning | Tutor courses in three modules, deep-dive companions, 20–35-question quizzes with concept, implementation, and transfer tiers, learner-progress tracking, source catalog, and no-cost exercises |

Run the local verification yourself — this is the same gate set CI runs, so a
green result here means a green pull request:

```bash
uv run agentic-pm-lab check
```

The test result is local verification evidence, not proof of a successful
cloud request, live provider response, or hosted Canvas session.

## What is not complete, and why that matters

This is a learning-scale proof of concept, not an institutional production
platform. The remaining boundaries are intentional and documented:

- portfolio positions, security-master classifications, and the research
  endpoint remain mock or fixture-backed;
- the 23-question PM catalog is broader than the active 22-case golden dataset;
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

## The learning path

The courses come in three modules. **Agent core** is the required path through
agentic AI; **Finance domain** applies it to investing and is optional, as are
the **Platforms** courses, which you pick by stack. `agentic-pm-lab learn`
prints the same list.

<!-- LEARNING_PATH:START -->
<!-- Generated from docs/learning/tutor-courses.json by
     scripts/build_learning_path.py. Edit the JSON, not this table. -->

| Step | Module | Course | Topic id | Est. hours |
|---|---|---|---|---|
| 1 | Agent core | [Agent foundations](docs/learning/tutors/agent-foundations-tutor.md) | `agent-foundations-tutor` | ~6 |
| 2 | Agent core | [Agent architecture](docs/learning/tutors/agent-architecture-tutor.md) | `agent-architecture-tutor` | ~3 |
| 3 | Agent core | [LangGraph and Deep Agents](docs/learning/tutors/langgraph-deep-agents-tutor.md) | `langgraph-deep-agents-tutor` | ~5 |
| 4 | Agent core | [Model Context Protocol](docs/learning/tutors/mcp-tutor.md) | `mcp-tutor` | ~4 |
| 5 | Agent core | [OpenTelemetry](docs/learning/tutors/opentelemetry-tutor.md) | `opentelemetry-tutor` | ~5 |
| 6 | Agent core | [Evaluations and AgentOps](docs/learning/tutors/evaluation-agentops-tutor.md) | `evaluation-agentops-tutor` | ~5 |
| 7 | Agent core | [Governance and delivery](docs/learning/tutors/governance-delivery-tutor.md) | `governance-delivery-tutor` | ~4 |
| 8 | Finance domain (optional) | [FICC fundamentals](docs/learning/tutors/ficc-tutor-agent.md) | `ficc-tutor-agent` | ~3 |
| 9 | Finance domain (optional) | [Portfolio construction](docs/learning/tutors/portfolio-construction-tutor.md) | `portfolio-construction-tutor` | ~4 |
| 10 | Finance domain (optional) | [Data provenance and research quality](docs/learning/tutors/data-provenance-research-tutor.md) | `data-provenance-research-tutor` | ~3 |
| 11 | Finance domain (optional) | [Public investment data](docs/learning/tutors/investment-data-tutor.md) | `investment-data-tutor` | ~3 |
| 12 | Finance domain (optional) | [Investment committee challenge](docs/learning/tutors/investment-committee-tutor.md) | `investment-committee-tutor` | ~3 |
| 13 | Platforms (optional) | [AWS Bedrock AgentCore](docs/learning/tutors/aws-agentcore-tutor.md) | `aws-agentcore-tutor` | ~4 |
| 14 | Platforms (optional) | [Copilot Canvas](docs/learning/tutors/copilot-canvas-mcp-tutor.md) | `copilot-canvas-mcp-tutor` | ~3 |
| 15 | Platforms (optional) | [Agent development lifecycle](docs/learning/tutors/agent-development-lifecycle-tutor.md) | `agent-development-lifecycle-tutor` | ~4 |
| 16 | Platforms (optional) | [Document-to-skill pipeline](docs/learning/tutors/document-to-skill-tutor.md) | `document-to-skill-tutor` | ~4 |

Only the Agent core module is required: about 32 hours. The other
modules are optional; take Finance domain to apply the core to investing, and
the Platforms courses for the tools you use. About 63 hours for everything.
Hours are rough estimates covering the deep dive, the three labs, the quiz,
and the teach-back. Each course lists its own prerequisites, so an
experienced learner can start anywhere.

<!-- LEARNING_PATH:END -->

Every course carries the same structure, whichever route you took above:

| Element | What it is |
|---|---|
| Persona and deep dive | A compact orientation, then a repository-grounded walkthrough of the real code |
| Objectives and lessons | What you should be able to do, and the sequence to get there |
| Quiz | 20–35 deterministic questions, each citing a repository file or a registered external source |
| Local lab | Trace working code and perturb it |
| Failure lab | Break it deliberately and explain the safe result |
| Build lab | Write code yourself; the tutor reviews but never writes it for you |
| Teach-back | Explain it back against a rubric |

This supports complete self-paced courses. It does not claim production
certification or expert mastery.

Deeper references: [START_HERE](docs/learning/START_HERE.md) for a zero-context
on-ramp, the [Tutor Course Guide](docs/learning/TUTOR_COURSE_GUIDE.md) for
working through one course and the completion rubric, the
[Depth Path](docs/learning/DEPTH_PATH.md) for the four-pass study method, and
the [Tutor Runbook](docs/guides/TUTOR_RUNBOOK.md) for
invoking a tutor from any agent surface. Understanding is tracked separately
from implementation status in
[LEARNER_PROGRESS](docs/learning/LEARNER_PROGRESS.md).

## Repository map

| Need | Start here |
|---|---|
| Install and verify | [INSTALL.md](INSTALL.md) |
| What was built, day by day | [Phase 1 recap](docs/learning/PHASE_1_RECAP.md) |
| Current status and evidence | [PROGRESS.md](PROGRESS.md), [EVIDENCE.md](docs/evidence/EVIDENCE.md) |
| Goals and acceptance criteria | [PRD.md](docs/architecture/PRD.md) |
| Current architecture and security | [ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md), [DIAGRAMS.md](docs/architecture/DIAGRAMS.md) |
| Day-by-day build plan | [PLAN.md](docs/PLAN.md) |
| Local operation | [RUNBOOK.md](docs/guides/RUNBOOK.md) |
| AWS AgentCore path | [AWS AgentCore setup](docs/guides/AWS_AGENTCORE_SETUP.md), [Gateway exercise](docs/guides/AGENTCORE_GATEWAY_SETUP.md) |
| Guided learning | [GitHub Pages curriculum](https://navoditk.github.io/agentic-pm-lab/), [standalone artifact](artifacts/agentic-pm-curriculum.html), or say **`agentexpert`** in a Copilot, Claude Code, or Codex checkout |
| Curriculum maintenance | [Freshness plan](docs/learning/CURRICULUM_FRESHNESS_PLAN.md), [Mastery skill](docs/learning/MASTERY_SKILL.md), [Tutor Course Guide](docs/learning/TUTOR_COURSE_GUIDE.md) |
| What to build next, at no cost | [No-cost roadmap](docs/learning/NO_COST_ROADMAP.md) |
| References | [REFERENCES.md](docs/reference/REFERENCES.md) |
| Experiments and comparisons | [experiments README](experiments/README.md), [benchmark report](docs/learning/CANONICAL_PM_BENCHMARK_REPORT.md) |
| Public-data catalog | [data README](data/README.md), [sample pack](data/samples/public_investment/README.md) |

## Building on it

The learning commands are above. Two developer commands sit beside them.
`check` runs the same gates CI runs, so a green local run means a green pull
request. `plan` prints one day's implementation steps — roughly 1,800 tokens
against 51,000 for the whole plan, which matters when you are pasting context
into an agent that cannot read your filesystem:

```bash
uv run agentic-pm-lab check --fast
uv run agentic-pm-lab plan 7 --quiet | pbcopy
```

Setup is in [INSTALL.md](INSTALL.md); the day-by-day path is in
[PLAN.md](docs/PLAN.md). All unit tests mock external dependencies. Never add
credentials, proprietary data, or claims of live evidence without recording
the corresponding experiment and cleanup state.

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
