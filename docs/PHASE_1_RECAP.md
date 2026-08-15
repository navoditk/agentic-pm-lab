# Phase 1 Recap and Learning Path

**Status:** Completed foundation track  
**Scope:** Original 20-day agentic PM AI learning plan  
**Posture:** Public/mock data and reversible experiments; not a production adviser or execution system

## Purpose

Phase 1 establishes the technical, investment, governance, and operating
foundation for the repository. Use this document to review what was completed,
check what a learner should understand, and traverse the repository in a
progressive order before starting the Phase 2 production-readiness track.

The completion rule is:

    local implementation + deterministic tests != live provider/cloud evidence

A completed Phase 1 day means the repository-local learning slice is implemented
and tested. It does not mean that every hosted model, AWS service, licensed
provider, or browser surface was exercised live.

## Navigation

- [Phase 1 outcome](#phase-1-outcome)
- [Day-by-day recap](#day-by-day-recap)
- [Completion checklist](#completion-checklist)
- [Questions Phase 1 should enable you to answer](#questions-phase-1-should-enable-you-to-answer)
- [Recommended learning path](#recommended-learning-path)
- [Using references and experiments](#using-references-and-experiments)
- [Transition to Phase 2](#transition-to-phase-2)

> **How to use this guide:** read the outcome first, use the checklist as a
> self-assessment, then follow the ten stages in order. Each stage names the
> files to read, commands to run, and tutor questions to ask.

## Phase 1 outcome

Phase 1 delivered:

- deterministic bond, curve, risk, scenario, backtest, econometrics, and optimization tools;
- single-agent and multi-agent Deep Agent workflows;
- Macro, Quant/Risk, and Fundamental specialist delegation;
- retry, backoff, dead-letter, checkpoint, and resume patterns;
- MCP-wrapped tools with contracts and authorization checks;
- local identity mapping and Cedar authorization;
- input, context, and output guardrails;
- human approval and audit logging;
- OpenTelemetry traces with token, cost, latency, retry, and tool metadata;
- LangSmith-compatible evaluation and regression workflows;
- GitHub Copilot skills, prompts, custom agents, and Canvas extensions;
- AgentCore Runtime, Memory, Evaluations, and Guardrail proofs;
- point-in-time provenance and SEC evidence normalization;
- research, Devil's Advocate, committee, AgentOps, and capstone workflows;
- public-data connectors, sample catalog, and investment-data tutor.

## Day-by-day recap

| Day | Completed and resolved |
|---|---|
| 1 | Walking skeleton, FastAPI, DuckDB fixtures, local artifact host, CI, progress generation, pre-commit, initial contracts, skills, architecture, and explicit mock markers. |
| 2 | yfinance and FRED ingestion, TTL caching, DuckDB price/macro/curve tables, public-data normalization, and FICC tutor foundation. |
| 3 | Bond and option pricing, curve interpolation, portfolio exposure, volatility, drawdown, factor regression, backtest, scenarios, optimization, contracts, API, MCP, and tool audit instrumentation. |
| 4 | Single Deep Agent, named/filtered context, skills, fake-model routing tests, token measurements, and the local Ollama/Qwen comparison. |
| 5 | Portfolio Manager supervisor, Macro/Quant/Fundamental specialists, restricted tool sets, retry/backoff, dead letters, failure injection, checkpoint/resume, and parameter-preservation hardening. |
| 6 | OpenTelemetry across the stack, LangSmith-compatible export, token/cost/latency fields, golden dataset, dimensional evaluators, baseline experiment, regression workflow, and eval-triage agent. |
| 7 | Identity-to-role mapping, Cedar tool/portfolio policies, boundary re-checks, guardrails, human approval interrupts, audit traces, and adversarial authorization tests. |
| 8 | Agentic Kanban and Issue Triage Canvases, shared handlers, GitHub issue filtering, capability tests, and docs agent. |
| 9 | Agent Operations Canvas with run history, traces, guardrails, costs, evaluations, approval/retry controls, evidence health, degradation, and replay. |
| 10 | Contract-backed MCP server, repeated entitlement checks, Portfolio/Risk Canvas, risk narrator, provenance, trace, scenario, and approval capabilities. |
| 11 | Docker/Compose local path, artifact reports, prompt library, PR reviewer, skills auditor, freshness checks, morning brief, and delivery runbooks. |
| 12 | Scenario engine, constrained optimization, optimization skill/prompt/tests, AgentCore Runtime configuration, direct-code and Gateway ADRs, temporary Runtime deployment, successful read-only invocation, and teardown. |
| 13 | AgentCore short/long-term Memory boundaries, cross-session preference proof, Evaluation manifest, comparison structure, on-demand score, and instrumentation-gap diagnosis. |
| 14 | Expanded local guardrails, trading-directive and prompt-exfiltration blocking, AWS standalone Guardrail proof, guardrail cases, and four-layer governance documentation. Optional fine-tuning, multi-region, and Cost Explorer stretch work was explicitly skipped. |
| 15 | Observation/release dates, vintages, as-of eligibility, bond instrument validation, needs-review behavior, and provenance tutor examples. |
| 16 | SEC filing metadata, CIK/accession normalization, source URLs, filing timestamps, excerpts, as-of filtering, and document-to-skill evidence foundations. |
| 17 | Investment research supervisor, quantitative/news/summarizer specialists, fixed-income evidence separation, mocked provider evidence, licensing/novelty metadata, and supervisor-pattern ADR. |
| 18 | Independent Devil's Advocate engine, contradiction/staleness/concentration/liquidity challenges, unsupported-causality checks, invalidation conditions, committee workflow, and human-review requirement. |
| 19 | Research/committee evidence health, thesis-versus-rebuttal findings, allocation deltas, promotion/SLO checks, degraded-provider exercise, dead-letter replay, and AgentOps Canvas integration. |
| 20 | Authenticated PM request, entitlement, freshness, macro/quant/FICC calculations, cited research, challenge, committee review, OTel/audit/evaluation metadata, fixed-income scenarios, human-review hedge, replayable capstone, and AWS cleanup evidence. |

## Completion checklist

### Architecture and investment domain

- [ ] I can explain the five architecture layers and their trust boundaries.
- [ ] I can distinguish deterministic calculations from model reasoning.
- [ ] I can explain structured data versus unstructured evidence.
- [ ] I can load the mock security master and portfolio positions.
- [ ] I can explain observation date, release date, vintage, and as-of eligibility.
- [ ] I can explain clean price, dirty price, accrued interest, duration, DV01, and curve assumptions.
- [ ] I can calculate exposure, concentration, volatility, drawdown, factor exposure, and scenario impact.
- [ ] I can compare max-Sharpe, minimum-volatility, and risk-parity proposals.
- [ ] I can explain why an optimization result is not an approved trade.

### Agents and harness

- [ ] I can explain single-agent versus specialist-supervisor designs.
- [ ] I can describe Macro, Quant/Risk, and Fundamental responsibilities.
- [ ] I can trace context assembly, delegation, tool use, and synthesis.
- [ ] I can explain restricted specialist tool sets.
- [ ] I can explain retry, backoff, dead-letter, checkpoint, and resume.
- [ ] I can identify the human approval interrupt.
- [ ] I can explain why a model must use deterministic tools for numerical claims.
- [ ] I can explain the local-model delegation limitation recorded in the experiments.
- [ ] I can compare LangGraph, Deep Agents, Runtime, and the intended Gateway path.

### Security and governance

- [ ] I can distinguish authentication, authorization, guardrails, and tool enforcement.
- [ ] I can explain the Cedar tool and portfolio policies.
- [ ] I can explain why prompts and skills cannot grant authority.
- [ ] I can describe input, context, and output guardrail checks.
- [ ] I can explain prompt-injection and cross-portfolio negative tests.
- [ ] I can identify what is audited and how trace IDs connect decisions.
- [ ] I can explain why human approval is required for sensitive actions.
- [ ] I can explain why order execution is disabled.

### Evaluation and operations

- [ ] I can explain routing, tool-selection, argument, retrieval, final-answer, policy, and guardrail dimensions.
- [ ] I can interpret a baseline's model, cases, scores, tokens, cost, and latency.
- [ ] I can explain why one evaluator score is not a production-quality claim.
- [ ] I can find OTel token, cost, latency, retry, retrieval, and tool fields.
- [ ] I can run tests, contract checks, Cedar checks, and freshness checks.
- [ ] I can distinguish local proof, fixture evidence, connector capability, and live evidence.
- [ ] I can use the experiment framework to record a new run.
- [ ] I can explain AWS budget, teardown, and cleanup discipline.

## Questions Phase 1 should enable you to answer

### Architecture

1. Why should deterministic portfolio calculations be separate from LLM reasoning?
2. When does a single agent outperform a multi-agent workflow?
3. What does a skill add beyond a prompt?
4. What does MCP add to the platform?
5. Why should Canvas use governed handlers instead of duplicate business logic?
6. When is local Deep Agents preferable to AgentCore Runtime?
7. What evidence is required before calling a deployment successful?
8. Why is READY status not proof of a successful application request?

### Investment and data

9. What does each source in the public-data catalog represent?
10. How does look-ahead bias enter a backtest?
11. Why can a revised macro value be invalid historically?
12. What bond terms are required before valuation?
13. Why can narrative evidence support a thesis but not directly create a risk number?
14. What can Treasury auctions, SOFR, CFTC positioning, and factors support?
15. What can each source not prove?
16. How do stale, conflicting, incomplete, or unlicensed sources affect a decision?
17. Why is a security master a risk dependency?
18. Why can an optimizer proposal be infeasible or non-implementable?

### Agent behavior

19. How does the supervisor choose a specialist?
20. How are tool arguments, units, and annualization preserved?
21. What happens when a specialist times out?
22. How does checkpoint/resume avoid duplicate work?
23. What is the difference between model failure and tool failure?
24. When should the agent abstain?
25. How does context filtering affect tokens and reliability?
26. How are cost and latency recorded?

### Governance

27. Can a prompt override Cedar?
28. Can a caller change identity in the request payload?
29. How are retrieved documents and tool results treated?
30. What belongs in an audit event?
31. What is the difference between denied and needs_review?
32. Why is human approval different from generated approval language?
33. What should be captured before a provider or model change?
34. Why is live evidence tracked separately from local tests?

## Recommended learning path

Use progressive disclosure rather than reading every file linearly.

### Stage 1 — Orient

Read:

1. README.md
2. AGENTS.md
3. PROGRESS.md
4. docs/PRD.md
5. docs/ARCHITECTURE.md
6. docs/DIAGRAMS.md
7. docs/PLAN.md
7. docs/PLAN_REVIEW.md

Ask agent-architecture-tutor:

    Explain the five architecture layers. For each, identify its trust boundary,
    current implementation, main failure mode, and the next file to read.

Then use [`DIAGRAMS.md`](DIAGRAMS.md) to trace the same architecture visually
before moving to the detailed implementation files.

### Stage 2 — Learn the investment data and analytics

Read:

1. data/README.md
2. data/samples/public_investment/README.md
3. docs/ficc-glossary.md
4. src/analytics/
5. src/ingestion/provenance.py
6. tests/unit/analytics/

Ask ficc-tutor-agent:

    Explain clean price, dirty price, accrued interest, duration, DV01,
    convexity, spread duration, carry, and rolldown. State what is implemented,
    simplified, or deferred.

Ask investment-data-tutor:

    Browse the ALFRED, Treasury, SOFR, SEC, CFTC, and Kenneth French samples.
    Explain one row, time semantics, decision use, limitation, and status.

### Stage 3 — Learn tools before agents

Read:

1. contracts/tools/
2. src/api/main.py
3. src/mcp_server/server.py
4. tests/unit/analytics/
5. tests/unit/api/
6. tests/unit/mcp_server/

Run:

    uv run pytest tests/unit/analytics tests/unit/api tests/unit/mcp_server -q

Ask portfolio-construction-tutor:

    Compare the three optimizer methods, their assumptions, current-versus-
    proposed weights, constraints, and reasons for human review.

### Stage 4 — Learn orchestration

Read:

1. src/agents/single_agent.py
2. src/agents/multi_agent.py
3. src/agents/recovery.py
4. src/context/builder.py
5. tests/unit/agents/
6. tests/unit/context/

Run:

    uv run pytest tests/unit/agents tests/unit/context -q

Ask langgraph-deep-agents-tutor:

    Trace a three-domain portfolio question through delegation, tool
    restrictions, parameter preservation, retry, dead-letter, checkpoint,
    resume, and synthesis.

### Stage 5 — Learn skills, prompts, and agents

Read skills/, docs/AGENT_RUNBOOK.md, docs/TUTOR_RUNBOOK.md,
.github/agents/, and .github/prompts/.

Run:

    uv run python scripts/check_skill_contracts.py
    uv run python scripts/check_skills_freshness.py --base HEAD~1 --head HEAD

Ask agent-development-lifecycle-tutor:

    Explain the difference between a skill, prompt, custom agent, tool contract,
    and evaluator. Show the required tests when one changes.

Ask document-to-skill-tutor:

    Use a public model document to demonstrate document mapping, citations,
    ambiguity, candidate skill generation, and human review.

### Stage 6 — Learn controls and approval

Read src/control/, governance/policies/, governance/tests/,
config/security/banned-terms.txt, and the Security Model in
docs/ARCHITECTURE.md.

Run:

    uv run python scripts/check_cedar_policies.py
    uv run pytest governance/tests tests/unit/control -q

Ask governance-delivery-tutor:

    Walk through allowed, denied, interrupted, and guardrail-blocked requests.
    Explain which layer decides, what is audited, and why prompts cannot grant
    authority.

Ask investment-committee-tutor:

    Challenge a mock duration thesis. Identify missing evidence, contradictions,
    stale sources, unsupported causality, invalidation conditions, and the
    human-approval point.

### Stage 7 — Learn evaluation and observability

Read src/observability/telemetry.py, src/evals/, scripts/run_eval.py,
evals/, config/eval-baseline.json, docs/observability-evaluation.md,
and experiments/README.md.

Run:

    uv run pytest tests/unit/observability tests/unit/evals tests/unit/scripts/test_run_eval.py -q

Ask evaluation-agentops-tutor:

    Explain every evaluation dimension. Interpret perfect routing with weak final
    answers. Design cases for citation correctness, point-in-time eligibility,
    and abstention.

Ask opentelemetry-tutor:

    Map one request to spans and attributes. Explain what to record for tokens,
    cost, latency, retries, tools, policy, and sensitive-content protection.

### Stage 8 — Learn Canvas and operations

Read src/ui/app.py, .github/extensions/, docs/RUNBOOK.md,
docs/GITHUB_WORKFLOWS.md,
docs/CANVAS_EXERCISES.md, docs/EVIDENCE.md, and docs/comparison-notes.md.

Ask copilot-canvas-mcp-tutor:

    Explain shared state, governed handlers, trust boundaries, approval, retry,
    trace, and evaluation behavior in the Canvas surfaces.

Run [`CANVAS_EXERCISES.md`](CANVAS_EXERCISES.md) and compare the question answer,
scenario result, entitlement outcome, provenance, and trace evidence.

Ask production-readiness-agent:

    Audit the local runbook and Canvas path for deployment, rollback, SLO,
    alerting, retention, and browser-evidence gaps.

### Stage 9 — Learn AWS and runtime operations

Read docs/AWS_AGENTCORE_SETUP.md, config/agentcore.yaml,
src/runtime/agentcore_app.py, the AgentCore ADRs,
experiments/agentcore-runtime-proof/, and docs/EVIDENCE.md.

Ask aws-agentcore-tutor:

    Explain Runtime, Gateway, Identity, Policy, Guardrails, Memory, and
    Evaluations. Separate intended architecture from live evidence and identify
    remaining Gateway and observability gaps.

Only run AWS commands when authenticated, budgeted, scoped, and ready to clean
up. Treat READY status as deployment state, not application success.

### Stage 10 — Run the capstone and transition

Read scripts/run_capstone_replay.py, src/capstone/workflow.py,
experiments/2026-08-13-agentcore-pm-review/, docs/EVIDENCE.md, and PROGRESS.md.

Run:

    uv run python scripts/run_capstone_replay.py
    uv run pytest

Ask investment-committee-tutor:

    Review the capstone as a committee member. State whether it is ready for
    human review, what evidence supports it, what remains mock, which assumptions
    are material, and what Phase 2 work is required.

Then read docs/PHASE_2_PLAN.md and select the next track based on the gaps found.

## Using references and experiments

docs/REFERENCES.md is a study map, not a bibliography to read linearly. Use it
before a topic, during implementation, and after the exercise to record one
finding in docs/LEARNINGS.md with a supporting test or experiment.

Use experiments/README.md for local, hosted, and AWS comparisons. Each run
should record the question, inputs, setup, model/version, output, evidence,
latency, tokens, cost basis, limitations, decision, and cleanup state.

Useful reference paths include:

- LangGraph, Deep Agents, MCP, OpenTelemetry, and agent harnesses.
- FICC, portfolio construction, curves, risk, data provenance, and backtesting.
- Cedar, NIST AI RMF, prompt injection, guardrails, and secure tool use.
- Bedrock, AgentCore Runtime, Gateway, Identity, Memory, Policy, Evaluations, and teardown.
- PDF extraction, document-to-skill workflows, citations, and source-derived tests.

Do not treat a vendor blog, model demo, or paper as evidence that the repository
implements a capability. Record what was actually tested.

## Transition to Phase 2

Start Phase 2 when:

- this checklist is complete;
- the Phase 1 capstone can be replayed;
- local, fixture, connector-capable, and live evidence are distinguishable;
- remaining gaps are documented;
- the learner is ready to add mandate, data-governance, model-risk, production,
  and resilience controls.

The recommended first Phase 2 task is Day 1: select one institutional workflow
and define its decision rights before adding new agents or providers.

Before beginning Phase 2, run the Day 21 Canvas bridge exercise in
[`docs/CANVAS_EXERCISES.md`](CANVAS_EXERCISES.md). It is the recommended final
Phase 1 checkpoint because it lets a new learner replay the governed PM
workflow from the Canvas or terminal, inspect structured execution evidence,
and distinguish fixture token accounting from provider-backed usage without
exposing private chain-of-thought.
