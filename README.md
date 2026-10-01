# Agentic PM Lab

**Learn to build and govern agentic AI, through a fixed-income portfolio-management platform built from scratch.**

[![CI](https://github.com/navoditk/agentic-pm-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/navoditk/agentic-pm-lab/actions/workflows/ci.yml)
[![Curriculum](https://github.com/navoditk/agentic-pm-lab/actions/workflows/learning-curriculum.yml/badge.svg)](https://navoditk.github.io/agentic-pm-lab/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Agentic PM Lab is a hands-on learning lab and a working proof of concept. It
puts deterministic financial analytics behind LangGraph agents, then adds what
a regulated setting needs: authorization outside the prompt, guardrails,
human approval, audit, OpenTelemetry, evaluation, MCP, and an AWS Bedrock
AgentCore path. Eighteen courses teach it, from the agent loop to rebuilding a
decision from one trace id.

It uses only public or clearly labelled mock data. It is not investment
advice, a trading system, or a production deployment.

## Start here

| If you have… | Do this |
|---|---|
| **Just a browser** | Open the **[curriculum site](https://navoditk.github.io/agentic-pm-lab/)**: every course, deep dive, and quiz, nothing to install. |
| **A coding agent** | Open this repository in Claude Code, GitHub Copilot, or Codex and say `agentexpert`. The [mastery skill](docs/learning/MASTERY_SKILL.md) runs lessons, quizzes, labs, and assessments, offline and read-only. |
| **A terminal** | Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/), then run the commands below. |

```bash
git clone https://github.com/navoditk/agentic-pm-lab.git && cd agentic-pm-lab
uv sync
uv run agentic-pm-lab learn       # every course, in order
uv run agentic-pm-lab placement   # 12 questions: which courses you can skip ahead
uv run agentic-pm-lab quiz agent-foundations-tutor
```

No model, network, or API key is needed to learn. [INSTALL.md](INSTALL.md) is
only for rebuilding the platform from an empty directory. New here? Read
[START_HERE](docs/learning/START_HERE.md) first.

## The curriculum

Four modules. **Agent core** and the **Capstone** are required; **Finance
domain** and **Platforms** are optional, taken by goal and by stack. You do
not need a finance background for the required path; for the underlying math,
see [pm-mechanics](https://github.com/navoditk/pm-mechanics).

<!-- LEARNING_PATH:START -->
<!-- Generated from docs/learning/tutor-courses.json by
     scripts/build_learning_path.py. Edit the JSON, not this table. -->

| # | Course and topic id | Module | Hours |
|---|---|---|---|
| 1 | [Agent foundations](docs/learning/tutors/agent-foundations-tutor.md)<br>`agent-foundations-tutor` | Agent core | ~6 |
| 2 | [Agent architecture](docs/learning/tutors/agent-architecture-tutor.md)<br>`agent-architecture-tutor` | Agent core | ~4 |
| 3 | [LangGraph and Deep Agents](docs/learning/tutors/langgraph-deep-agents-tutor.md)<br>`langgraph-deep-agents-tutor` | Agent core | ~6 |
| 4 | [Model Context Protocol](docs/learning/tutors/mcp-tutor.md)<br>`mcp-tutor` | Agent core | ~4 |
| 5 | [OpenTelemetry](docs/learning/tutors/opentelemetry-tutor.md)<br>`opentelemetry-tutor` | Agent core | ~6 |
| 6 | [Evaluations and AgentOps](docs/learning/tutors/evaluation-agentops-tutor.md)<br>`evaluation-agentops-tutor` | Agent core | ~6 |
| 7 | [Governance and delivery](docs/learning/tutors/governance-delivery-tutor.md)<br>`governance-delivery-tutor` | Agent core | ~5 |
| 8 | [Capstone: traceability end to end](docs/learning/tutors/traceability-capstone-tutor.md)<br>`traceability-capstone-tutor` | Capstone | ~5 |
| 9 | [FICC fundamentals](docs/learning/tutors/ficc-tutor-agent.md)<br>`ficc-tutor-agent` | Finance domain (optional) | ~3 |
| 10 | [Portfolio construction](docs/learning/tutors/portfolio-construction-tutor.md)<br>`portfolio-construction-tutor` | Finance domain (optional) | ~4 |
| 11 | [Data provenance and research quality](docs/learning/tutors/data-provenance-research-tutor.md)<br>`data-provenance-research-tutor` | Finance domain (optional) | ~3 |
| 12 | [Public investment data](docs/learning/tutors/investment-data-tutor.md)<br>`investment-data-tutor` | Finance domain (optional) | ~3 |
| 13 | [Investment committee challenge](docs/learning/tutors/investment-committee-tutor.md)<br>`investment-committee-tutor` | Finance domain (optional) | ~3 |
| 14 | [AWS Bedrock](docs/learning/tutors/aws-bedrock-tutor.md)<br>`aws-bedrock-tutor` | Platforms (optional) | ~4 |
| 15 | [AWS Bedrock AgentCore](docs/learning/tutors/aws-agentcore-tutor.md)<br>`aws-agentcore-tutor` | Platforms (optional) | ~5 |
| 16 | [Copilot Canvas](docs/learning/tutors/copilot-canvas-mcp-tutor.md)<br>`copilot-canvas-mcp-tutor` | Platforms (optional) | ~3 |
| 17 | [Agent development lifecycle](docs/learning/tutors/agent-development-lifecycle-tutor.md)<br>`agent-development-lifecycle-tutor` | Platforms (optional) | ~4 |
| 18 | [Document-to-skill pipeline](docs/learning/tutors/document-to-skill-tutor.md)<br>`document-to-skill-tutor` | Platforms (optional) | ~4 |

Agent core and the Capstone are required: about 42 hours. The other
modules are optional; take Finance domain to apply the core to investing, and
the Platforms courses for the tools you use. About 78 hours for everything.
Hours are rough estimates covering the deep dive, the three labs, the quiz,
and the teach-back. Each course lists its own prerequisites, so an
experienced learner can start anywhere.

<!-- LEARNING_PATH:END -->

Every course has the same shape:

| Part | What you do |
|---|---|
| Deep dive | Read the concepts, quoted from primary sources, and how this repository implements them |
| Labs | Trace working code (local lab), break it deliberately (failure lab), and write something new (build lab) |
| Quiz | 20–35 questions in three tiers (concept, implementation, transfer), each citing its source; pass at 80% overall and 70% per tier |
| Teach-back | Explain it back against a rubric |

Your quiz results are recorded locally and summarised in
[LEARNER_PROGRESS](docs/learning/LEARNER_PROGRESS.md);
`uv run agentic-pm-lab review` brings back the concepts you missed. Optional
[live labs](docs/learning/LIVE_LABS.md) run the same code against real
services; none is required.

## The design in one view

The central question: **how can AI assist a portfolio manager without turning
plausible language into an unaudited investment decision?**

```text
public/mock data → deterministic tools → governed agent workflow
                 → evidence, evaluation, audit, human review
                 → report or allocation proposal, never an order
```

The model reasons, delegates, and narrates. Python computes every number.
Policy is enforced at the tool boundary, not inferred from prompts.

| Layer | Implementation | Trust boundary |
|---|---|---|
| Data | DuckDB, public connectors, provenance, point-in-time checks | Narrative evidence never silently becomes a risk input |
| Control | Identity, Cedar policy, guardrails, audit, human approval | Authorization runs before model access and again at the tool |
| Tool | Deterministic analytics with JSON Schema contracts, FastAPI, MCP | Tools re-check identity and resource entitlement |
| Agent | LangGraph and Deep Agents, specialist delegation, recovery | Model output is interpretation, not financial truth |
| Interactive | Canvas, Streamlit, scheduled review | The UI is not a security boundary |
| Runtime | Local host and AgentCore Runtime and Gateway | Hosted runs are temporary evidence, not an always-on service |
| Observability and evaluation | OpenTelemetry, LangSmith-compatible experiments, baselines, replay | Telemetry records counts and ids, not prompts, holdings, or secrets |

The full picture is in [ARCHITECTURE](docs/architecture/ARCHITECTURE.md) and
[DIAGRAMS](docs/architecture/DIAGRAMS.md); the goals and non-goals are in the
[PRD](docs/architecture/PRD.md).

## Status

The 21-day build is complete for local, fixture-based verification; the
[Phase 1 recap](docs/learning/PHASE_1_RECAP.md) walks through it day by day.

| Area | What exists |
|---|---|
| Analytics | Bond and option pricing, curves, risk, factor regression, backtesting, scenarios, portfolio optimization |
| Data | yfinance and FRED paths; governed ALFRED, Treasury, SEC, SOFR, CFTC, and Kenneth French connectors; mock holdings and security master |
| Agents | Single-agent and specialist Deep Agents, a separate research supervisor, a local-model comparison |
| Governance | Local identities, Cedar policy, guardrails, enforcement at the FastAPI and MCP boundaries, approval interrupts, audit |
| Evaluation | Golden, routing, policy, and guardrail cases; versioned baselines; regression gates |
| Observability | Traces and metrics as separate signals, W3C context propagation, parent-based sampling |
| AWS | AgentCore Runtime entrypoint and runbooks; live evidence for a temporary Runtime, Memory, Guardrails, and Evaluations |

What is deliberately not done: positions, the security master, and the
research endpoint stay mock or fixture-backed; the optimizer is learning-scale
(supplied estimates, long-only); AgentCore Gateway and Copilot-hosted runs have
no live evidence yet; and the system proposes, it never trades. The
[evidence ledger](docs/evidence/EVIDENCE.md) separates local from live proof,
and the [completion audit](docs/learning/PLAN_REVIEW.md) reviews the plan.

To run the same gates CI runs:

```bash
uv run agentic-pm-lab check
```

A green run is local evidence, not proof of a live cloud or provider call.

## Find your way around

| You want | Go to |
|---|---|
| A zero-context on-ramp | [START_HERE](docs/learning/START_HERE.md) |
| How to work through a course | [Tutor course guide](docs/learning/TUTOR_COURSE_GUIDE.md), [Depth path](docs/learning/DEPTH_PATH.md) |
| A tutor in your coding agent | [Tutor runbook](docs/guides/TUTOR_RUNBOOK.md), [Mastery skill](docs/learning/MASTERY_SKILL.md) |
| Live labs against real services | [LIVE_LABS](docs/learning/LIVE_LABS.md) |
| Build status and evidence | [PROGRESS](PROGRESS.md), [EVIDENCE](docs/evidence/EVIDENCE.md) |
| The day-by-day build plan | [PLAN](docs/PLAN.md) |
| Running it locally | [RUNBOOK](docs/guides/RUNBOOK.md), [INSTALL](INSTALL.md) |
| The AWS AgentCore path | [AgentCore setup](docs/guides/AWS_AGENTCORE_SETUP.md), [Gateway exercise](docs/guides/AGENTCORE_GATEWAY_SETUP.md) |
| CI and automation | [GitHub workflows](docs/guides/GITHUB_WORKFLOWS.md) |
| Reading lists | [REFERENCES](docs/reference/REFERENCES.md) |
| Experiments and benchmarks | [experiments](experiments/README.md), [benchmark report](docs/learning/CANONICAL_PM_BENCHMARK_REPORT.md) |
| Public data | [data catalog](data/README.md), [sample pack](data/samples/public_investment/README.md) |
| What to build next | [No-cost roadmap](docs/learning/NO_COST_ROADMAP.md) |

## Contributing

Agent and tool rules live in [AGENTS.md](AGENTS.md), which Claude Code,
Copilot, and Codex all read. Two developer commands help: `check` runs every
CI gate, and `plan` prints one day of the build plan, about 1,800 tokens
rather than 51,000, for pasting into an agent that cannot read your files.

```bash
uv run agentic-pm-lab check --fast
uv run agentic-pm-lab plan 7 --quiet
```

Unit tests never touch the network. Never commit credentials, proprietary
data, or a claim of live evidence without recording the experiment and its
cleanup.

## Credits and takeaways

The multi-agent PM shape is adapted from OpenAI's
[Multi-Agent Portfolio Collaboration](https://developers.openai.com/cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration)
example and rebuilt with LangGraph and Deep Agents. The math layer beneath it
is [pm-mechanics](https://github.com/navoditk/pm-mechanics).

What carries over to any agent system:

- deterministic math stays outside the model;
- policy is enforced at the boundary, never inferred from prompts;
- evidence, timestamps, and provenance matter as much as answers;
- evaluation measures routing, tools, policy, safety, and quality separately;
- a deployment, a model response, and a production-ready system are three
  different claims.

Licensed under [MIT](LICENSE).
