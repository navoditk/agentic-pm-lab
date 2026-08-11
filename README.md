# Agentic AI Learning Journey: Portfolio Management & Optimization Tooling

A hands-on, production-grade learning project: build a multi-agent AI system for buy-side portfolio management — real deterministic analytics, real governance, real cloud deployment — using only public and mock data. Company-agnostic by design; nothing here references a specific employer or proprietary system.

## What this is

A 12-day (+2 optional) build, not a tutorial you passively read. Each day replaces one mocked piece of a "walking skeleton" with something real: public market data, a multi-agent LangGraph system, observability, authorization, a governed cloud deployment. By the end, a Portfolio Manager agent orchestrating Macro/Quant/Fundamental specialists answers real portfolio-risk questions *and* proposes real reallocations — backed by tested tools, a real security model, and a scored evaluation harness — deployed once to AWS Bedrock AgentCore as a proof of concept, then torn down.

**Where the core idea comes from:** the Portfolio-Manager-orchestrates-specialists pattern isn't invented here — it's translated from OpenAI's own Cookbook example, ["Multi-Agent Portfolio Collaboration with OpenAI Agents SDK"](https://developers.openai.com/cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration) (Raj Pathak, Chelsea Hu), which uses a Portfolio Manager agent calling Macro/Fundamental/Quant specialist agents as tools to solve an investment research problem. This project asks the same question on a different stack: what does that pattern look like built on LangGraph Deep Agents' native sub-agent model instead of the OpenAI Agents SDK, deepened with production concerns (contracts, evals, security, observability) the original didn't need to cover.

## Tech stack

- **Agents:** LangGraph / LangGraph Deep Agents, multi-agent orchestration with native sub-agents
- **Cloud deployment:** AWS Bedrock AgentCore (Runtime, Gateway, Identity, Policy, Observability; optional Memory/Evaluations/deeper Guardrails)
- **Observability & eval:** OpenTelemetry (extended with cost/token telemetry) + LangSmith (golden-dataset experiments across seven scored dimensions)
- **Interactive surfaces:** GitHub Copilot Canvas (four progressively richer apps), MCP (one Tool Layer, mounted everywhere)
- **Governance:** Cedar policy-as-code, a four-layer AuthN → AuthZ → Guardrails → Tool-enforcement security model
- **Dev tooling:** Claude Code, GitHub Copilot (Desktop/CLI/App), OpenAI Codex CLI — interchangeable, compared empirically as you go
- **App layer:** FastAPI, DuckDB, `uv`, pytest, pre-commit

## What you'll find here

- A deterministic Tool Layer (pricers, curve construction, exposure/vol/drawdown, factor regression, backtesting, scenario shocks, **and real portfolio optimization — mean-variance, max-Sharpe, risk parity, via PyPortfolioOpt**) — every function contract-tested, no LLM ever computes a risk number or an allocation
- Twelve Agent Skills as tested software artifacts (contract, examples, tests — not prompt files), including two meta-skills that build and test the others
- A golden evaluation dataset scored across routing, tool selection, arguments, retrieval quality, final answer, policy compliance, and guardrail behavior
- Four GitHub Copilot Canvas apps, from a warm-up kanban board to a capstone Portfolio/Risk Operations console
- A real security model: test identities with deliberately different entitlements, adversarial/prompt-injection tests, policy and guardrails versioned as code

## Learning goals

Working proficiency with the full stack above, demonstrated end to end rather than in isolated exercises — and specifically: context engineering as a deliberate layer (not incidental prompt stuffing), failure/recovery engineering with real fault injection, a security model that survives adversarial testing, and an honest empirical record (not just published benchmarks) of which dev tools and which model backends actually perform best on this project's own task mix.

## Find your way around

| Document | What it's for |
|---|---|
| [`docs/README.md`](docs/README.md) | Documentation index — the complete map by intent |
| `docs/PRD.md` | The *why* — vision, architecture, principles, the business questions this platform answers, tiered success criteria |
| `docs/PLAN.md` | The *how* — repo layout, all 14 days' step-by-step, the skills/prompts/security/context-engineering detail |
| `docs/ARCHITECTURE.md` | Canonical current-state architecture and security boundaries |
| `PROGRESS.md` | Current status — mostly auto-generated, plus a daily log |
| `INSTALL.md` | One-time setup — start here |
| `docs/REFERENCES.md` | Curated reading, by topic |
| `AGENTS.md` | Routes Claude Code / GitHub Copilot / Codex CLI to the right document — read automatically by those tools |

## Getting started

Read `INSTALL.md` start to finish, then use `PROGRESS.md` to find the current
day in `docs/PLAN.md`.

## A note on data

Public APIs (yfinance, FRED, SEC EDGAR) and clearly-labeled invented mock data only. No company-sensitive information, real non-public data, or proprietary system names appear anywhere in this repo — by design, not by omission.
