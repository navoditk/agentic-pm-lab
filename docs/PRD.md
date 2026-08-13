# PRD: Agentic AI Learning Journey — Portfolio Management & Optimization Tooling

A self-directed, company-agnostic path to building fluency with the agentic AI stack (LangChain, LangGraph, LangGraph Deep Agents, AWS Bedrock/Agent Core, OpenTelemetry, GitHub Copilot App canvases, MCP) through the lens of buy-side portfolio management — using only public/mock data and open-source tools.

**This document defines *what* is being built and *why*.** For repo layout, install steps, and the day-by-day implementation plan, see `docs/PLAN.md`. For current status, see `PROGRESS.md`. `AGENTS.md` routes any dev tool (Claude Code, GitHub Copilot, OpenAI Codex CLI) to the right document for a given question.

---

## 1. Vision

Four things inform this project, stitched together instead of treated as separate:

- **A target platform architecture** organized as Data → Control → Tool → Interactive → Runtime layers (with Automation as a governed sub-layer). That's the map for "what good looks like" at a real institution — described here in fully generic terms, with no vendor- or company-specific system names.
- **A public-data investment-intelligence MVP scope** (deterministic analytics + agent layer + a visual UI) that can be built solo, incrementally, with no paid subscriptions required for the core path.
- **A multi-agent orchestration pattern** — a Portfolio Manager agent orchestrating Macro/Fundamental/Quant specialist agents as tools — that translates directly into LangGraph Deep Agents' native sub-agent model. Concretely inspired by OpenAI's own Cookbook example, "Multi-Agent Portfolio Collaboration with OpenAI Agents SDK" (`docs/REFERENCES.md`, Origins & inspiration) — the same Portfolio-Manager-plus-specialists idea, built there on a different framework; this project is one answer to "what does that pattern look like on LangGraph Deep Agents instead."
- **GitHub Copilot Canvas** (canvas extensions in the GitHub Copilot app), a close, real-world match for the target architecture's own vision of agent-built, shareable, dynamic visual artifacts.

The build proceeds as a "walking skeleton" — every layer exists in mocked form from day one, and each subsequent step of `docs/PLAN.md` replaces one layer's mock with a real implementation: public data, a real agent framework, real observability, real governance, a four-project progression through Canvas extensions, and finally a real managed cloud agent runtime. FICC vocabulary (rates, credit, mortgages, curves, spreads) is absorbed naturally because it's the subject matter of the analytics being built, not a separate study track.

**One project, one architecture, one repository, one end-state.** Production-grade concerns — context engineering, end-to-end authorization, a real eval harness, failure engineering, skills as tested software artifacts, and policy/guardrails as code — deepen the existing 12-day progression rather than forming a parallel "enterprise" track. Nothing here creates a second architecture to maintain.

**No company-sensitive information, system names, or internal product names appear anywhere in this project.** Every data source, mock, and folder name is either a real public API/dataset or a plainly descriptive, invented label — never a reference to a proprietary internal platform. This is a hard constraint, not a preference.

---

### 2.1 PM AI platform fundamentals covered by the target

The frameworks and cloud services are means to learn the platform fundamentals
that make an AI system usable by a portfolio-management team:

| Fundamental | Demonstration target |
|---|---|
| Data contracts and provenance | Every value has an identifier, source, observation time, release/vintage time, unit, currency, transformation, freshness, and quality status. |
| Point-in-time correctness | Backtests and agent answers use only information available at decision time; revised macro data and later filings cannot leak into history. |
| Portfolio representation | Positions, prices, accrued interest, cash, benchmark, weights, returns, FX, corporate actions, and instrument metadata have explicit schemas and reconciliation checks. |
| Investment workflow | Research → risk review → scenario/optimization → human review → approved report, with no accidental order execution. |
| Risk and portfolio construction | Constraints, turnover, liquidity, transaction costs, leverage, concentration, benchmark-relative risk, and explainable allocation changes are first-class inputs. |
| Model and agent risk | Model/version, prompt, skill, tool, data vintage, evaluator, and approval state are recorded so an answer can be reproduced and challenged. |
| Reliability and operations | Timeouts, retries, idempotency, checkpointing, cost budgets, freshness checks, and graceful degradation are tested. |
| Privacy and governance | Entitlements are enforced at the resource boundary; sensitive data is minimized and excluded from prompts, logs, traces, and artifacts. |
| Document intelligence | Public model documents can become cited, reviewable skill packages and document-grounded Deep Agents; executable calculators require explicit formulas, source examples, sandboxing, tests, and human review. |

These fundamentals are broader than making an agent call a tool: they are the
minimum mental model for assessing whether a PM AI platform is safe,
reproducible, and useful in an investment workflow.

### 2.2 Public-data realism track

The core path remains small enough to complete, while the following extensions
make the end-to-end use case more realistic:

| Data need | Core path | Recommended extension | Main lesson |
|---|---|---|---|
| Prices and macro | yfinance and FRED | Treasury direct feeds and ALFRED vintages | Calendars, revisions, units, and freshness |
| Fundamentals and filings | Mock security master | SEC EDGAR submissions, XBRL Company Facts, and N-PORT | As-filed data, identifiers, filing dates, point-in-time joins |
| Fixed-income liquidity | Mock holdings and curve | FINRA TRACE aggregates or licensed transaction data | Sparse trades, capped volumes, and licensing |
| Factors and benchmarks | Supplied factor returns | Kenneth French Data Library and public benchmark series | Factor definitions, excess returns, and survivorship controls |
| News and sentiment | Mock research endpoint | SEC filing text plus GDELT event/news metadata | Evidence-linked retrieval and sentiment uncertainty |
| Backtesting | Static toy backtest | Costs, slippage, turnover, liquidity, and rebalance timing | Research validity is separate from model sophistication |

Public data is suitable for learning and prototyping, not automatically for
production investment decisions. Each connector must document access terms,
rate limits, attribution, update cadence, historical coverage, revisions,
identifier quality, and redistribution rights.

## 2. Target Architecture

| Platform Layer | What it means at a real firm | What this project builds, mock-first |
|---|---|---|
| Data Layer | Governed access to structured, unstructured, and enterprise data | An invented mock structured-data layer (synthetic portfolio/security/curve tables) → real yfinance/FRED/SEC EDGAR public ingestion; the security master stays a documented mock unless real fundamentals are added as a stretch |
| Control Layer | Four separate concerns, not one: **AuthN** (who is calling), **AuthZ** (what they may access), **Guardrails** (content/behavior constraints), **Tool enforcement** (the final boundary that actually withholds unauthorized data) — see §3, principle 10 | A local role-based allowlist, audit log, and test-identity authorization matrix → human-in-the-loop approval wired into the agent → AWS Bedrock AgentCore Identity/Policy plus Bedrock Guardrails as the managed equivalents |
| Tool Layer | Callable APIs over data: instrument pricers, curve APIs, portfolio APIs, research APIs, econometrics, backtests, **portfolio optimization** — each with a machine-readable input/output contract | Stub endpoints with canned responses → real deterministic engines (bond/option pricer, curve interpolation, exposure/vol/drawdown, factor regression, walk-forward backtest, scenario shock, **constrained mean-variance/max-Sharpe/risk-parity allocation via PyPortfolioOpt, Day 12**), wrapped once as MCP and mounted everywhere, each with a JSON Schema contract and entitlement check at the boundary; benchmark-relative, downside/robust, liquidity-aware, and multi-period extensions are documented learning targets, not current production claims; the research API stays a documented mock unless EDGAR full-text search is added as a stretch |
| Interactive Layer | Rich, agent-built, shareable visual surfaces for people to work alongside agents — an interaction surface, not a trust boundary | A four-project progression through real GitHub Copilot Canvas extensions, plus a minimal framework-agnostic UI for comparison; every canvas capability calls the same governed Tool/MCP interface everything else does, never a shortcut around it |
| Runtime Layer | Non-production single-file artifact hosting; a production path is a real agentic app tied to a repo with real CI/CD | A hand-built local artifact host as a rough analog → each canvas extension's own persisted-state folder as the real, product-native equivalent → a real Copilot-coding-agent-authored PR merged through real CI (including skill, contract, eval, and authorization regression checks) → AWS Bedrock AgentCore Runtime, reached only through the Gateway-governed path |
| Automation (sub-layer) | Event-triggered pipelines, approval-only | A scheduled pipeline and a native platform automation, both producing a report and executing nothing |

**Agent framework:** LangGraph Deep Agents (the `deepagents` package) is the framework of choice for the Agent layer — a batteries-included harness on top of LangGraph providing planning, a virtual filesystem, native sub-agent spawning, and a built-in Agent Skills loader using the same `SKILL.md` format shared across every dev tool in use on this project. This is why Deep Agents, not a hand-rolled LangGraph graph, is the default for the multi-agent Portfolio-Manager-plus-specialists pattern.

**Context is engineered, not assumed.** The agent's context window is assembled deliberately from named sources (user/role, portfolio state, market data, retrieved research, memory, tool outputs, skills) rather than accumulating implicitly — see §3, principle 11, and `docs/PLAN.md` §13.

**End state:** the multi-agent Portfolio Manager system runs on AWS Bedrock AgentCore (Runtime, Gateway, Identity, Policy, Observability), reachable only through the Gateway-governed path, as an integration-depth proof of concept — real running code and real captured traces, deliberately not a persistent production service (resources are torn down after the final integration step; see `docs/PLAN.md` for why). The expanded 20-day roadmap makes AgentCore Memory, AWS-native Evaluations, richer Bedrock Guardrails, point-in-time data, SEC research, investment-research collaboration, Devil's Advocate challenge, AgentOps, and the final institutional capstone mainstream milestones in Days 13–20.

---

## 3. Design Principles

1. **Walking skeleton first, then deepen one layer at a time.** The foundation touches every layer badly; each subsequent step makes exactly one layer real.
2. **Deterministic math, AI narration.** The LLM never computes a risk number — it calls a tested Python function and narrates the result. This is also the best FICC-learning device: you have to know what the function should return before you can trust the agent's summary of it.
3. **Public or mock data only, always.** No company-sensitive terminology, tickers-as-proxies, internal system names, or real non-public identifiers anywhere in the repo, commit history, or documentation.
4. **Every mock is labeled and tracked.** A consistent `# MOCK — replace on Day X` marker in code, reflected automatically in a status table (see `docs/PLAN.md` §6) — both a study aid and the fastest way to see what's left before the platform is "real enough."
5. **Skills are software artifacts, not prompt-only files.** A skill expresses *intended* behavior (its `SKILL.md`); a contract (`contract.yaml`) declares *allowed* behavior — inputs, permitted tools, output schema, side effects, approval requirements; examples and tests prove the two match. Policy, not the skill file, is what actually enforces allowed behavior (§15). See `docs/PLAN.md` §8.
6. **Every component ships with a standalone, mocked test — and every skill and tool ships with a contract test too.** No unit test hits a real network call, real API, or real cloud resource. Contract tests validate a tool or skill's declared input/output schema independent of what any particular LLM happens to produce.
7. **Every capability traces back to a stated business question.** A tool, skill, prompt, or canvas capability isn't "done" until there's a named PM question it answers (§4 below) — this keeps the project anchored to decision-support value, not just technical breadth.
8. **One Tool Layer, mounted everywhere — contracts included.** The deterministic analytics functions are built once and wrapped once as MCP; every agent surface (Deep Agents, Canvas, AgentCore Gateway) mounts the same implementation instead of getting a bespoke binding. This extends to the contract, not just the code: one schema per tool, referenced wherever it's needed, never re-authored per consumer.
9. **Commit small, commit often, track automatically.** Progress bookkeeping (status tables, mock→real tracking, and evidence links — PR, tests, eval run, trace, ADR) is derived from repo state wherever possible, not hand-maintained — see `docs/PLAN.md` §6 for the mechanism.
10. **Authentication, authorization, guardrails, and tool enforcement are four separate concerns, tested independently.** Identity answers *who*; policy answers *what they may access*; guardrails constrain *unsafe content or behavior* as defense-in-depth, not a substitute for authorization; the tool/API boundary is the final, non-bypassable enforcement point — unauthorized data must never reach the model, regardless of what the model was asked or tricked into requesting. See `docs/PLAN.md` §15.
11. **Context is assembled deliberately, and its cost is measured.** What enters the model's context window, why, how it's bounded, and what deliberately stays out are all explicit design decisions, not incidental accumulation — and every run's token/latency/cost footprint is recorded alongside its quality score, so architectural choices (e.g., single-agent vs. multi-agent) are justified against both. See `docs/PLAN.md` §13 and §5's OTel extension.
12. **Assume dependencies fail, and prove the system degrades safely.** Timeouts, retries with backoff, iteration ceilings, checkpoint/resume, and idempotency aren't theoretical — they're exercised with deliberate fault injection, not just implemented and hoped about. See `docs/PLAN.md` §14.
13. **Governance lives in Git, next to the code it governs.** Authorization policy and guardrail configuration are versioned, code-reviewed, and regression-tested the same way application code is — not a separately managed, out-of-band configuration. See `docs/PLAN.md` §15.

---

## 4. Business Problems & Trading Decisions Addressed

Every capability in this platform traces back to a specific question a portfolio manager might actually ask (Principle 7). This is the canonical list, grouped by which sub-agent answers each question — the Portfolio Manager orchestrator handles the two cross-cutting questions that need more than one sub-agent. `docs/PLAN.md` Appendix C gives the machine-checkable version (expected tool calls, expected answer criteria, and — for the golden dataset — routing, argument, authorization, and guardrail dimensions) used for evaluation.

**Reminder throughout:** answers are only as good as the underlying data. Anything sourced from the mocked security master or the mocked research tool is illustrative of the mechanism, not investment-grade, until those items move off the non-goals list (§6). **Reminder on scope:** several of these questions are portfolio-scoped — a real deployment would restrict which portfolios a given caller may query at all, which is exactly what the authorization work in `docs/PLAN.md` §15 exercises using test identities with deliberately different entitlements.

### 4.1 Macro sub-agent — rates, regime, and liquidity questions

| # | PM Question | Business Problem / Trading Decision |
|---|---|---|
| 2 | What happens if rates rise 50bps? | Stress-test rate sensitivity — is current duration positioning appropriate given a plausible rate move? |
| 6 | How exposed are we to recession risk? | Macro regime read — should the book tilt more defensive? |
| 7 | Are funding conditions deteriorating? | Liquidity/funding stress — should leverage or less-liquid exposure be reduced? |
| 12 | Is the market currently risk-on or risk-off? | Tactical regime classification informing near-term tilts |
| 14 | How exposed are we to tightening liquidity? | Sizing an appropriate liquidity buffer |
| 16 | Are we exposed to yield-curve steepening risk? | Curve positioning — barbell vs. bullet duration structure |
| 17 | How much did rates contribute to returns? | Macro attribution — validating whether P&L matches the rates thesis |

### 4.2 Quant/Risk sub-agent — exposure, concentration, factor, and optimization questions

| # | PM Question | Business Problem / Trading Decision |
|---|---|---|
| 3 | Which positions contribute most to spread risk? | Credit risk concentration — which positions to trim to reduce spread duration |
| 9 | How correlated is the portfolio to SPY? | Equity beta/correlation — does the book actually diversify equity risk? |
| 10 | Compare rates shock vs. credit shock. | Relative stress magnitude — which risk factor to hedge first |
| 11 | What are the largest portfolio concentrations? | Concentration risk — whether to trim oversized single-name/sector exposure |
| 15 | How does mortgage convexity affect the portfolio? | MBS negative convexity — hedging needs in a rally or selloff |
| 18 | What are our dominant factor exposures? | Factor risk — surfacing unintended factor bets |
| 19 | How diversified is the portfolio? | Diversification measurement — whether to add uncorrelated positions |
| 21 | What's the minimum-variance reweighting of the current holdings, holding expected return roughly constant? | Rebalancing decision — can risk be reduced without giving up return? (`docs/PLAN.md` Day 12 — the first genuinely prescriptive question in this catalog, not just descriptive) |
| 22 | What would a maximum-Sharpe-ratio allocation look like, given current expected returns and covariances? | Rebalancing decision — is the current allocation risk-efficient, or could the same risk buy more expected return elsewhere? |
| 23 | How would a risk-parity allocation differ from our current, concentration-heavy weights? | Diversification decision — is risk being contributed disproportionately by a few positions, independent of their nominal weight? |

The following additional optimization cases are part of the institutional extension
backlog. They make the business scope more complete without implying that the
current Day 12 optimizer already implements them:

| Additional PM question | Business problem / decision |
|---|---|
| Can we improve active return while staying within a benchmark tracking-error budget? | Benchmark-relative portfolio construction and active-risk governance |
| Which proposed rebalance is feasible after liquidity, turnover, spread, and market-impact costs? | Implementation planning; reject allocations that look attractive but cannot be traded responsibly |
| How stable is the allocation across covariance/return estimation windows and market regimes? | Model-risk review; prefer robust decisions over fragile in-sample optima |
| What allocation minimizes downside risk or CVaR rather than total volatility? | Tail-risk and drawdown-aware construction for portfolios where symmetric volatility is insufficient |
| How should factor, sector, duration, spread, and issuer risk contributions be budgeted? | Translate investment guidelines into explicit risk budgets and explainable constraints |
| How should the portfolio rebalance over multiple periods under a target risk path? | Reduce unnecessary turnover while keeping risk within a monitored corridor |

### 4.3 Fundamental sub-agent — benchmark, attribution, and research questions

| # | PM Question | Business Problem / Trading Decision |
|---|---|---|
| 4 | Where are we overweight relative to benchmark? | Active risk vs. benchmark — rebalancing toward or away from the benchmark |
| 5 | What drove underperformance this month? | Attribution — is underperformance thesis-related, or a mistake to correct? |
| 8 | Which assets hedge equity selloffs? | Hedge construction — what to add as a tail-risk hedge |
| 13 | Which holdings have deteriorating sentiment? | Early-warning signal — whether to review or trim a position before fundamentals confirm (mock-sourced today; see §6) |

### 4.4 Portfolio Manager orchestrator — cross-cutting questions

| # | PM Question | Business Problem / Trading Decision |
|---|---|---|
| 1 | What changed in portfolio risk overnight? | Morning triage — does anything need PM attention before the broader market opens? |
| 20 | Generate a portfolio risk summary for the committee. | Investment committee prep — what to present and be ready to defend |

---

## 5. Success Criteria

Success is tiered on purpose — **one working vertical slice matters more than nominal completion of every optional feature.** Tier 1 is the bar for "the project works." Tier 2 is strongly desirable and is what most of this document's new depth targets. Tier 3 is explicitly time-permitting.

### Tier 1 — must demonstrate
- Deterministic Tool Layer (with contracts, including real portfolio optimization, not just risk description) + LangGraph/Deep Agents (single and multi-agent) + MCP + OpenTelemetry + a golden-dataset eval suite + basic skills with contracts and tests, all working together end to end.
- All five architecture layers (§2) have moved from mock to real, per the mock→real status table (`PROGRESS.md`), except the items explicitly excluded in §6.
- A multi-agent Portfolio Manager system (Macro, Quant, Fundamental sub-agents) answers all 23 questions in §4, end to end, using real tool calls rather than hallucinated numbers.
- A CI pipeline exists that would catch, automatically: a stale skill, a broken skill/tool contract, a regression in agent behavior or eval score across a model change, and a broken test — without a person having to remember to check.

### Tier 2 — strongly desirable
- Identity and authorization (test identities with deliberately different entitlements) plus negative security tests (prompt injection, tool-bypass attempts) pass, per the security acceptance test below.
- Four working GitHub Copilot Canvas extensions exist, including one capstone (Portfolio/Risk Operations) that stands on its own as a demonstrable artifact, calling only governed interfaces.
- The same agent runs successfully on AWS Bedrock AgentCore Runtime and Gateway at least once, with a captured trace and a passing evaluation run against the golden dataset, reachable only through the Gateway-governed path.
- Every business question in §4 has a named prompt, skill, or agent-callable capability that answers it, traceable in `docs/PLAN.md` Appendix C, each with a contract and test.
- The document-to-skill learning deliverable can take a public model document through a cited document map and candidate `SKILL.md`/contract package, with explicit ambiguity and human-review status; executable calculators are only accepted when source-derived tests pass.

### Tier 3 — time permitting
- Local-model (Ollama) comparison against the cloud model, run against the same golden dataset.
- The extended AWS and institutional track: AgentCore Memory across sessions, AgentCore Evaluations compared against LangSmith, and a deeper Bedrock Guardrails configuration beyond Day 12's minimal deployment intent, followed by provenance, research, committee, AgentOps, and capstone acceptance evidence.
- Additional custom agents, canvases, ADRs, and general operational polish beyond what Tier 1/2 required.

### Core end-state acceptance test
A user request enters through the interactive surface, reaches a LangGraph/Deep Agent, selects a reusable skill/tool path, invokes governed MCP-backed deterministic portfolio/risk tools, returns an answer, emits an OpenTelemetry trace and eval result, records control/audit decisions, and can be deployed through the Bedrock/AgentCore target path — without changing the fundamental business/tool architecture.

### Security acceptance test
An authenticated but unauthorized user cannot retrieve restricted portfolio data even if the model is successfully prompt-injected or attempts an alternate tool path. (`docs/PLAN.md` §15 has the concrete test-identity scenarios this is checked against.)

### CI acceptance test
A change that breaks a skill contract, a tool contract, a golden-eval threshold, an authorization rule, or a guardrail regression is blocked before merge.

**Extended success criteria, if the optional AWS extension (`docs/PLAN.md` Days 13–14) is done:**
- The agent demonstrably recalls a stated preference across two separate sessions via AgentCore Memory, not just within one conversation.
- The same evaluation dataset has been run through both LangSmith and AgentCore's native Evaluations, with a written comparison of what each surfaces.
- The Day 12 minimal Bedrock Guardrail is extended and demonstrated blocking additional deliberately-triggering prompts while passing normal ones through untouched.

---

## 6. Non-Goals / Deferred for This Iteration

- **Real security-master fundamentals (SEC EDGAR-backed).** The mocked security master stays a documented stub; wiring real EDGAR fundamentals is a clean next-iteration task.
- **A real research/sentiment tool.** The research endpoint stays mocked; EDGAR full-text search or GDELT-based sentiment are natural next steps.
- **Deep hallucination-detection metrics beyond dataset-experiment pass/fail scores.** A real, scored regression-testing loop exists (`docs/PLAN.md` §5), separated across routing/tool-selection/argument/retrieval/final-answer/policy/guardrail dimensions, but richer grounding/faithfulness metrics beyond LLM-as-judge and criteria evaluators are out of scope for this iteration.
- **A fifth canvas** beyond the four in the progression.
- **A persistent, always-on AWS deployment.** The AgentCore integration (and the optional Memory/Guardrails extension) is captured as a proof of concept and torn down afterward — not a running service.
- **Unreviewed arbitrary PDF-to-code conversion.** The document-to-skill capability is staged: document-grounded Q&A comes before executable calculators, and generated code requires provenance, sandboxing, source-derived tests, and human review.
- **Full production hardening of fine-tuning, multi-region/HA, and cost optimization.** The optional AWS extension (`docs/PLAN.md` Day 14) gives each a light, hands-on-if-you-want-it touch, but genuine production engineering on any of these stays out of scope, since it's a different skill from agent-building and would be disproportionate to a learning project.
- **A formal policy-as-code engine beyond a learning-scale Cedar setup.** `docs/PLAN.md` §15 uses Cedar for policy-as-code as a real, hands-on exercise; production-scale policy infrastructure (a managed policy service, multi-tenant policy stores) is out of scope.
- **Real production incident response.** Failure engineering (`docs/PLAN.md` §14) deliberately injects faults to observe and harden behavior; it does not stand up on-call rotations, paging, or incident-management tooling.
