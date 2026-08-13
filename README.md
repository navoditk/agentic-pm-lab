# Agentic AI Learning Journey: Portfolio Management & Optimization

This repository is a 20-day, hands-on roadmap for building an institutional-grade Portfolio Manager (PM) AI platform for the buy side. It combines deterministic portfolio analytics, multi-agent research and risk workflows, governance, evaluations, observability, and an interactive GitHub Copilot Canvas surface.

The project is deliberately company-agnostic and uses only public or clearly labelled mock data. It is a learning and prototyping environment—not an investment adviser, trading system, or production deployment.

## Purpose

The goal is to develop practical proficiency in the full lifecycle of a trusted PM AI platform:

1. Build reliable deterministic tools for market data, portfolio analytics, risk, scenarios, research, and optimization.
2. Compose those tools into LangGraph and Deep Agents workflows with specialist agents and explicit contracts.
3. Add the controls required for financial services: identity, authorization, policy-as-code, guardrails, provenance, human review, auditability, and failure recovery.
4. Deploy and operate the system using AWS Bedrock and AgentCore patterns, with OpenTelemetry traces and evaluation evidence.
5. Expose the workflows through GitHub Copilot Canvas and practice the same repository with Codex CLI, Claude Code, Copilot CLI, and the Copilot app.

The end state is a defensible PM AI proof of concept: every recommendation should be explainable, evidence-linked, reproducible, tested, observable, and subject to appropriate approval—not merely plausible text from an LLM.

## Current status and roadmap

Days 1–14 are complete. They cover the walking skeleton, public-data layer, deterministic tool layer, Deep Agents, multi-agent orchestration, OpenTelemetry/evals, control-layer foundations, Canvas fundamentals through Agent Operations, AgentCore Memory/Evaluations boundaries, and extended Guardrails.

Days 10–20 extend the project into the comprehensive institutional PM track:

- governed portfolio/risk capstone and human approval flows;
- runtime, automation, prompts, and standalone agent runbooks;
- AWS Bedrock AgentCore Runtime, Gateway, Identity, Policy, Memory, Evaluations, and Guardrails;
- point-in-time data, provenance, SEC research, and evidence-linked retrieval;
- an AWS-style multi-agent investment research workflow;
- a Devil’s Advocate / investment committee challenge workflow;
- AgentOps and the final Portfolio/Risk Canvas;
- a final end-to-end capstone with release evidence and an operational handoff.

The authoritative schedule is [docs/PLAN.md](docs/PLAN.md), and current evidence is tracked in [PROGRESS.md](PROGRESS.md).

## Business problems and use cases

The platform is designed around realistic PM and investment-team workflows:

- **Overnight portfolio review:** summarize exposures, performance drivers, factor moves, concentration, liquidity, and exceptions with links to the underlying data.
- **Risk and scenario analysis:** answer questions about duration, spread, volatility, drawdown, factor exposure, and macro or rates/credit shocks using deterministic tools.
- **Research assistant:** retrieve and summarize public filings, macro releases, market data, and news/sentiment while preserving dates, sources, and point-in-time validity.
- **Investment thesis review:** have fundamental, macro, quantitative, and risk specialists collaborate, then ask a Devil’s Advocate agent to identify missing evidence, contradictions, and downside cases.
- **Portfolio construction:** compare constrained allocations, mean-variance, max-Sharpe, risk-parity, and scenario-aware alternatives; present recommendations for human review rather than placing trades.
- **Active-risk and rebalance review:** assess benchmark-relative exposure, tracking-error budgets, turnover, estimated implementation cost, liquidity constraints, and infeasible constraints before a human approves a rebalance.
- **Downside and robustness review:** compare volatility-based allocations with downside-risk, stress, uncertainty-aware, and shrinkage-based alternatives; make estimation uncertainty and out-of-sample evidence visible rather than hiding it behind a single optimizer score.
- **PM committee preparation:** create an evidence-linked investment brief, decision log, dissenting views, open questions, and approval checklist.
- **Model and agent operations:** inspect traces, replay failures, compare evaluations, monitor cost/latency, and triage policy or tool-boundary violations through Canvas.

Explicit non-goals are autonomous order execution, personalized investment advice, use of proprietary company data, and treating an LLM as the source of truth for financial mathematics.

## Portfolio optimization depth

The optimization track is intentionally deep enough to teach the boundary between
deterministic portfolio construction and agentic narration, but not deep enough
to claim a production optimizer. The current implementation covers:

- expected returns and covariance supplied as explicit, auditable inputs;
- long-only weight bounds and feasibility checks;
- maximum-Sharpe and minimum-volatility mean-variance allocations;
- hierarchical risk-parity allocation, with a documented deterministic fallback
  for the current PyPortfolioOpt/SciPy compatibility issue;
- current-versus-proposed weight deltas, one-way turnover, concentration limits,
  and estimated transaction costs;
- rates/credit scenario analysis, JSON contracts, FastAPI/MCP exposure, agent
  narration, human approval, and regression tests.

The roadmap treats the following as the next institutional layer: benchmark-relative
tracking error and active risk, group and factor constraints, downside/CVaR risk,
shrinkage and Black-Litterman inputs, liquidity/market-impact costs, walk-forward
out-of-sample validation, robust/uncertainty-aware allocations, and multi-period
rebalance planning. Cardinality/integer allocation, tax-aware optimization,
derivatives margin, liability-driven investing, and live order generation remain
outside this learning project. See the dedicated [portfolio optimization reading
path](docs/REFERENCES.md#portfolio-optimization-and-portfolio-construction) for
the recommended progression.

## Target technology stack

| Capability | Target technologies and project role |
|---|---|
| Agent orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/), [Deep Agents](https://docs.langchain.com/oss/python/deepagents/), specialist sub-agents, structured handoffs, resumable workflows |
| Models and cloud runtime | [Amazon Bedrock](https://aws.amazon.com/bedrock/), [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/), Runtime, Gateway, Identity, Policy, Memory, Evaluations, and Guardrails |
| Data and analytics | Public market data, FRED macro data, SEC EDGAR filings, news/sentiment adapters, DuckDB, pandas, deterministic risk/portfolio engines, backtesting, and constrained optimization with PyPortfolioOpt; CVXPY is the current transitive solver layer, while Cvxportfolio, Riskfolio-Lib, and skfolio are comparison references rather than core dependencies |
| Tool boundary | Typed tool contracts, JSON Schema/YAML contracts, MCP-compatible access patterns, validation, timeouts, retries, and authorization re-checks at execution time |
| Governance and security | Cedar policy-as-code, AuthN → AuthZ → guardrails → tool-enforcement layers, human approval, audit records, provenance, prompt-injection and adversarial tests |
| Observability and evaluation | [OpenTelemetry](https://opentelemetry.io/), traces and metrics, LangSmith experiments, golden datasets, cost/token/latency telemetry, failure replay, regression gates |
| User experience | GitHub Copilot Canvas, MCP, progressively richer operational and portfolio/risk surfaces |
| Application foundation | FastAPI, `uv`, pytest, pre-commit, GitHub Actions, reproducible local mock fixtures |
| Development tools | [GitHub Copilot](https://github.com/features/copilot) CLI/Desktop/App, [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview), and [OpenAI Codex](https://developers.openai.com/codex) CLI; interchangeable where practical and compared through project evidence |

The stack is intentionally layered. Deterministic analytics sit below the agent layer; controls sit at the tool boundary and are not inferred from prompts or skill descriptions; traces and evals span the workflow; Canvas is a review and operations surface, not a replacement for governance.

## Learning outcomes

By the end of the roadmap, the learner should be able to:

- design a production-oriented multi-agent architecture for investment research and portfolio decisions;
- write agent skills, prompts, tool contracts, custom agents, and runbooks that another engineer can execute and test independently;
- apply context engineering, memory, retrieval, source freshness, provenance, and point-in-time correctness to financial workflows;
- separate LLM reasoning from deterministic pricing, risk, optimization, and backtesting code;
- distinguish an allocation proposal from an executable order: every optimization result carries assumptions, constraints, turnover/cost estimates, feasibility state, and human-approval requirements;
- build eval datasets and failure-injection tests for routing, tool choice, arguments, retrieval, answer quality, policy compliance, and guardrails;
- instrument agent workflows with OpenTelemetry and operate them using traces, metrics, cost, latency, and replay evidence;
- understand how Bedrock AgentCore services line up end to end with application, tool, identity, policy, memory, evaluation, and observability concerns;
- create a Copilot Canvas that communicates portfolio state and approvals clearly; and
- document trade-offs, limitations, release criteria, and operational ownership for an institutional audience.

## Key inspirations and reference implementations

The core multi-agent PM pattern is adapted from OpenAI’s [Multi-Agent Portfolio Collaboration](https://developers.openai.com/cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration) cookbook: a Portfolio Manager coordinates macro, fundamental, and quantitative specialists. This repository translates the idea to LangGraph/Deep Agents and adds governance, evaluations, observability, data provenance, AWS deployment patterns, and a human approval path.

The forward roadmap also studies and adapts these public examples:

- AWS’s [AI-powered investment research assistant with multi-agent collaboration](https://aws.amazon.com/blogs/machine-learning/part-3-building-an-ai-powered-assistant-for-investment-research-with-multi-agent-collaboration-in-amazon-bedrock-and-amazon-bedrock-data-automation/).
- AWS’s [Investment Analysis using Amazon Bedrock](https://docs.aws.amazon.com/solutions/investment-analysis-using-amazon-bedrock/) solution guidance.
- AWS’s [multi-agent orchestration solution](https://docs.aws.amazon.com/solutions/multi-agent-orchestration-on-aws/) and [Bedrock AgentCore samples](https://github.com/awslabs/amazon-bedrock-agent-samples).
- AWS’s [context-rich research agents with Deep Agents and AgentCore](https://aws.amazon.com/blogs/machine-learning/build-context-rich-research-agents-with-deep-agents-and-bedrock-agentcore/) and [AgentOps at scale](https://aws.amazon.com/blogs/machine-learning/agentops-operationalize-agentic-ai-at-scale-with-amazon-bedrock-agentcore/).
- LinqAlpha’s [Devil’s Advocate investment-thesis workflow on Amazon Bedrock](https://aws.amazon.com/blogs/machine-learning/how-linqalpha-assesses-investment-theses-using-devils-advocate-on-amazon-bedrock/). This is the intended reference for the committee challenge and dissenting-view track. “LinqDQA” is treated here as the LinqAlpha/Devil’s Advocate example.
- Portfolio-construction references are organized in the [optimization reading path](docs/REFERENCES.md#portfolio-optimization-and-portfolio-construction), covering PyPortfolioOpt, CVXPY, Cvxportfolio, Riskfolio-Lib, skfolio, and vectorbt examples. These resources extend the learning scope without implying that the current repo implements every method they expose.

Additional background on agent harnesses, skills, context engineering, tools, and evals is curated in [docs/REFERENCES.md](docs/REFERENCES.md), including relevant OpenAI and Anthropic engineering articles, talks, and videos.

## Repository guide

| Document | Use it for |
|---|---|
| [INSTALL.md](INSTALL.md) | One-time environment setup and verification |
| [AGENTS.md](AGENTS.md) | Routing instructions for Codex, Claude Code, and GitHub Copilot |
| [PROGRESS.md](PROGRESS.md) | Current day, completed work, pending work, and evidence |
| [docs/README.md](docs/README.md) | Documentation index by intent |
| [docs/PRD.md](docs/PRD.md) | Vision, business problems, architecture, principles, success criteria, and non-goals |
| [docs/PLAN.md](docs/PLAN.md) | Day-by-day implementation plan, contracts, skills, security, context engineering, and Days 10–20 extension |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Canonical architecture and security boundaries |
| [docs/REFERENCES.md](docs/REFERENCES.md) | Curated documentation, cookbooks, projects, talks, videos, and podcasts by topic |
| [docs/AGENT_RUNBOOK.md](docs/AGENT_RUNBOOK.md) | Standalone custom-agent and skill examples, test cases, expected outputs, and troubleshooting |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | One-command local stack, tests, traces, evaluations, security checks, automation, and AWS teardown guidance |
| [data/README.md](data/README.md) | Data-source cards, freshness, licensing, provenance, and mock-data rules |

## Getting started

Read [INSTALL.md](INSTALL.md) from start to finish, then read [PROGRESS.md](PROGRESS.md) to identify the current day and evidence. Use [docs/PLAN.md](docs/PLAN.md) for the implementation task, [docs/AGENT_RUNBOOK.md](docs/AGENT_RUNBOOK.md) to run a custom agent or skill standalone, and [docs/REFERENCES.md](docs/REFERENCES.md) when a topic needs deeper study.

All unit tests must mock external dependencies and must not call real APIs or cloud resources. Unfinished endpoints are explicitly marked as mocks, and no public or mock data in this repository should be interpreted as investment advice.
