# Architecture

Canonical current-state architecture for agentic-pm-lab. Created Day 1, once the walking skeleton exists — updated in place whenever a design decision changes it, not recreated. The current implementation includes the Day 21 Canvas-to-capstone workflow. See `docs/PRD.md` §2 for the target end-state each layer is heading toward, and `docs/PLAN.md` Appendix B for the day-by-day steps that get it there.

---

## Reading guide

This is the canonical current-state design. Start with the layer table, then
trace one request through the logical components, orchestration, recovery,
observability, evaluation, and security sections. Use the implementation paths
as navigation aids; use [`EVIDENCE.md`](EVIDENCE.md) to distinguish local
behavior from hosted or live evidence.

The visual companion is [`DIAGRAMS.md`](DIAGRAMS.md). It contains the platform
layer view, governed request sequence, multi-agent topology, data/evidence
separation, security boundaries, local-versus-AWS comparison, and CI/evaluation
flow.

| If you want to understand... | Read... |
|---|---|
| The platform shape | [The layers](#the-layers-and-what-exists-today-day-20) |
| Request and data flow | [Logical components](#logical-components-through-day-20) |
| Agent delegation and failure handling | [Multi-agent orchestration](#multi-agent-orchestration-day-5) and [Failure and recovery](#failure-and-recovery-day-5) |
| Traces and quality | [Observability and evaluation](#observability-and-evaluation-day-6) |
| Authorization and safety | [Security Model](#security-model) |

---

## The layers, and what exists today (Day 21)

| Layer | Target end-state (`docs/PRD.md` §2) | What exists today |
|---|---|---|
| **Data Layer** | Real yfinance/FRED/SEC EDGAR public ingestion | `src/ingestion/prices.py` loads daily OHLCV for six public ETFs from yfinance; `src/ingestion/macro.py` loads Treasury yields, Fed Funds, and CPI from FRED and derives `curve_points`. `src/ingestion/public_investment.py` adds tested, real-capable normalizers/fetchers for SEC Company Facts/submissions, ALFRED, Treasury auctions, NY Fed SOFR, CFTC COT, and Kenneth French factors. The latter paths are not yet promoted into canonical DuckDB tables or claimed as live experiment evidence. `security_master` and `portfolio_positions` remain invented CSV fixtures and retain their `# MOCK` marker. |
| **Control Layer** | AuthN, AuthZ, Guardrails, and Tool enforcement as four separately-tested concerns (`docs/PRD.md` §3, principle 10) | `config/roles.yaml` assigns three local test identities only. Cedar policies independently govern tools and portfolio resources, agent construction removes unauthorized tools before model binding, portfolio context is checked before model access, a denied-terms guardrail checks input/context/output, and FastAPI re-checks tool plus resource access. Backtests pause for human approval. Every decision records its layer and OTel trace ID. |
| **Tool Layer** | Real deterministic engines, one JSON Schema contract each, wrapped once as MCP | In addition to pricing, curves, exposure, risk, regression, and backtest, `src/analytics/scenario.py` provides first-order rates/credit shocks and `src/analytics/optimizer.py` provides max-Sharpe, minimum-volatility, and risk-parity allocation proposals with turnover/concentration checks. FastAPI and MCP expose both under the same contracts. Research and portfolio classifications intentionally remain mocked. |
| **Interactive Layer** | Four real GitHub Copilot Canvas extensions | Four project canvases now exist: `agentic-kanban`, `issue-triage-canvas`, `agent-ops-canvas`, and the Portfolio/Risk capstone. Day 19 extends Agent Operations with evidence-provider health, committee rebuttal, fixed-income, promotion/SLO, and incident/replay panels. Day 21 adds a bounded PM question runner that invokes the Python capstone in fixture mode and exposes stage, audit, evaluation, provenance, trace, token, cost, and failure evidence. The Canvas remains an interaction surface, not a trust boundary. |
| **Runtime Layer** | Copilot-coding-agent PR through real CI → AWS Bedrock AgentCore Runtime | `src/runtime/agentcore_app.py` is a direct-code AgentCore entrypoint for the same Portfolio Manager, with `config/agentcore.yaml` capturing Runtime/Gateway/Identity/Policy/Guardrails/OTel intent. A temporary Runtime reached `READY`, completed a bounded read-only request, and was torn down; no Gateway target is claimed. |
| **Agent Layer** | LangGraph Deep Agents, single agent then multi-agent orchestration | `src/agents/multi_agent.py` defines a Portfolio Manager orchestrator with native Macro, Quant/Risk, and Fundamental sub-agents. `src/agents/investment_research.py` adds a separate research supervisor with Quantitative Analysis, News/Research, and Smart Summarizer specialists. Each specialist receives only its domain tools, and the orchestrators receive no ungoverned analytics tools directly. `multi_agent_local.py` reproduces the original hierarchy on Ollama/Qwen3 4B for comparison; the Day 5 cross-domain run did not delegate and returned empty. |
| **Observability** | One cost-aware OTel stream with local and agent-specific views | `src/observability/telemetry.py` instruments FastAPI and emits manual analytics, agent, authorization, identity, and audit spans. Agent spans include model, token, tool/retrieval call, retry, latency, success, and estimated-cost attributes. Day 21 adds a structured local execution envelope with stage durations, audit events, trace IDs, explicit token basis, and zero-cost fixture accounting. The same OTLP stream exports to LangSmith; no parallel proprietary tracing path exists. |
| **Evaluation** | Versioned behavioral regression suite across independent dimensions | Eighteen active golden/routing/policy cases run as OTel-native LangSmith experiments. `scripts/run_eval.py` scores routing, tool selection, tool arguments, retrieval context, final-answer criteria, and deterministic policy compliance. AgentCore Memory, standalone Guardrails, batch control-path, and scored on-demand Evaluation evidence are recorded in `docs/EVIDENCE.md`; hosted-runtime span collection remains optional. |
| **Automation** (Runtime sub-layer) | Scheduled pipeline + native platform automation | `.github/workflows/morning-brief.yml` provides an approval-only scheduled review; native Copilot automation remains a platform/browser evidence task. Day 21 provides a learner-triggered Canvas workflow over the local capstone. |

The Data Layer is intentionally mixed: public price/macro data is real and the
high-feasibility public connectors are real-capable, while
portfolio and security metadata remains mock. The target separates a structured
calculation path from an unstructured evidence path. Structured records may feed
deterministic analytics only after point-in-time and quality checks; unstructured
records (filings, narratives, news metadata, and document-derived skills) support
retrieval and explanation, but cannot directly set a risk number or allocation.
The normalized connector shapes and field meanings can be browsed in
`data/samples/public_investment/`; those files are representative fixtures, not
live provider captures.
The optional BigData.com adapter sits behind the evidence path and the governed
MCP/Gateway boundary. Remaining stubs are tracked from their `# MOCK` markers in
`PROGRESS.md` (`docs/PLAN.md` §6).

---

## Logical components, through Day 20

```
data/mock_structured/*.csv          invented portfolio and security metadata
  -> src/ingestion/load_mock_structured_data.py
      -> data/cache/portfolio.duckdb   security_master, portfolio_positions

yfinance                              public ETF daily OHLCV
  -> src/ingestion/prices.py
      -> data/cache/prices.json        24-hour normalized-response cache
      -> portfolio.duckdb/prices

FRED                                  public macro and Treasury observations
  -> src/ingestion/macro.py
      -> data/cache/macro.json         24-hour normalized-response cache
      -> portfolio.duckdb/macro_series
      -> portfolio.duckdb/curve_points (latest complete Treasury curve)

config/roles.yaml                    local identity -> role assignment only
governance/policies/*.cedar         tool and portfolio authorization authority
  -> src/control/identity.py         resolve PM/RISK/ADMIN test identities
  -> src/control/authorization.py    Cedar decisions and agent tool filtering
  -> src/control/guardrails.py       shared denied-term input/context/output check
  -> src/control/audit.py            layered decisions + OTel trace -> audit.jsonl

src/analytics/*.py                   pure deterministic financial engines
src/analytics/scenario.py             rates/credit first-order scenario engine
src/analytics/optimizer.py            constrained allocation proposals
contracts/tools/*.schema.json        input/output contract per engine
src/api/main.py                      governed FastAPI wrappers; research mock
src/mcp_server/server.py              contract-backed MCP adapter; Cedar re-check
src/runtime/agentcore_app.py          direct-code AgentCore Runtime entrypoint

ResearchEvidence provider adapters   src/research/provider.py returns cited,
                                     licensing-aware evidence fixtures; the
                                     optional BigData.com thematic operation is
                                     mocked and cannot create a risk number

Fixed-income data spine               src/research/fixed_income.py partitions
                                     point-in-time structured observations from
                                     cited commentary; Treasury auctions, SOFR,
                                     TRACE, CFTC, and provider connectors remain
                                     fixture/provider-adapter work

scripts/artifacts_host.py            separate FastAPI app, serves artifacts/*
src/ui/app.py                         optional Streamlit comparison surface
Dockerfile/docker-compose.yml         one-command local API/MCP/artifact stack

.github/extensions/agentic-kanban/   shared board canvas for create/assign/move
.github/extensions/issue-triage-canvas/  repository issue triage canvas
.github/extensions/agent-ops-canvas/     agent run / trace / approval canvas
                                         + research/committee AgentOps panels
.github/extensions/portfolio-risk-canvas/ governed PM/risk review canvas

skills/example-echo/                 proves the Agent Skills package mechanism
skills/python-best-practices/        this project's actual coding conventions
skills/mock-to-real-migration/       safe mock replacement checklist
skills/ficc-glossary-maintainer/     consistent learning glossary format
skills/new-tool-onboarding/          end-to-end capability checklist
skills/skill-creator/                complete skill-package scaffolding recipe
skills/skill-tester/                 local static/mock skill validation recipe
skills/portfolio-risk-summary/       exposure/volatility/drawdown synthesis
skills/canvas-capability-authoring/  verb-first, shared-handler canvas standard
.github/agents/risk-narrator-agent.agent.md  evidence-linked PM/risk narration

src/context/builder.py               named full/filtered context composition
src/agents/single_agent.py           OpenAI-configured Deep Agent
src/agents/single_agent_local.py     same agent on local Ollama/Qwen3 4B
src/agents/multi_agent.py            Portfolio Manager -> three native specialist sub-agents
src/agents/multi_agent_local.py      same hierarchy on local Ollama/Qwen3 4B
src/agents/investment_research.py    separate supervisor -> quantitative,
                                     news/research, and smart-summarizer agents
src/agents/devils_advocate.py        independent read-only challenge engine,
                                     critic agent, and human-review workflow
src/capstone/workflow.py             reproducible authenticated PM capstone,
                                     structured/unstructured provenance split,
                                     audit/evaluation/version metadata
src/agents/recovery.py               retry, validation, limits, and dead-letter middleware

src/observability/telemetry.py       shared OTel provider, spans, and LangSmith OTLP export
evals/*.jsonl                        golden, routing, authorization, and guardrail cases
scripts/run_eval.py                  OTel-native LangSmith experiment and scoring runner
config/eval-baseline.json            accepted fast/full scores and regression tolerance
skills/eval-dataset-authoring/       evaluation-case schema and authoring workflow

.github/workflows/ci.yml             lint + test on push/PR
.github/workflows/contract-tests.yml skill schema/static/mock/negative gates
.github/workflows/skills-freshness.yml changed-code/skill synchronization gate
.github/workflows/morning-brief.yml  weekday approval-only review issue
.github/workflows/eval-regression.yml  fast PR/full main behavioral regression gate
.github/workflows/progress-tracker.yml  regenerates PROGRESS.md's status table on push to main
.github/agents/eval-triage-agent.agent.md  read-only regression investigation persona
.github/agents/docs-agent.agent.md    docs maintenance agent for architecture/glossary
.github/agents/pr-reviewer-agent.agent.md    read-only domain PR reviewer
.github/agents/skills-auditor-agent.agent.md  read-only stale-skill reviewer
.github/prompts/                       six PM workflows + one developer workflow
docs/RUNBOOK.md                        local start/test/eval/security/deploy guide
config/agentcore.yaml                  reviewed managed-runtime intent
config/bedrock-guardrail.yaml          minimal Day 12 guardrail intent
```

## Interactive Layer (Days 8–9)

The first two canvases were intentionally low-stakes. `agentic-kanban` proved
the shared-state contract: UI and agent actions create, assign, and move the
same cards through the same handlers. `issue-triage-canvas` raised the bar by
pulling real GitHub issues, filtering and prioritizing them visually, and
calling the GitHub API only from SDK-free handlers with a token acquired at
runtime.

`agent-ops-canvas` is the operational canvas: it surfaces the seeded Day 4/5/6/7
history, selected run traces, guardrail summaries, cost metrics, a paused
approval run, and a side-by-side comparison panel for single-agent versus
multi-agent observations. `approve_run` and `retry_node` both call back into the
main agent via `askAgent`, while `run_evaluation` shells out to
`scripts/run_eval.py` and returns the real LangSmith experiment summary when
`LANGSMITH_API_KEY` is present.

The Portfolio/Risk capstone is the first domain-specific integration boundary.
Its action contract covers portfolio selection, scenario review, trace focus,
provenance, and approval state. The Python MCP adapter is the governed mount
point for deterministic analytics: it loads the existing contract's `input`
schema, resolves the caller's identity from MCP request metadata, checks Cedar
tool permission, and re-checks portfolio entitlement before calling
`src/analytics/`. The Canvas keeps mock holdings and scenario fixtures visibly
separate from public curve data; it is not itself a trust boundary.

## Governed Tool Layer sequence (Day 7)

Public ingestion remains unchanged, while every direct Tool Layer API call
follows the governed boundary:

```
yfinance/FRED
  --> fresh TTL cache? -- yes --> normalized JSON records
          | no                  --> public API --> normalized JSON records
          +---------------------------> DuckDB tables

caller + X-Identity
  --> src/api/main.py OR src/mcp_server/server.py
        --> role_for_identity(identity)
        --> Cedar: check_tool_permission(role, tool)
              |-- denied --> audit(AuthZ, denied) --> HTTP 403
              |-- allowed --> audit(AuthZ, allowed)
                    --> Cedar: check_portfolio_access(identity, portfolio)
                          |-- denied --> audit(Tool, denied) --> HTTP 403
                          |-- allowed --> audit(Tool, allowed)
                    --> validate typed request
                    --> src/analytics/<deterministic function>
                    --> typed JSON response
```

For MCP, identity and (when required) `portfolio_id` travel as request
metadata, not as trusted prompt text. Missing identity is denied, and the
portfolio entitlement is checked again immediately before the analytics call.
The MCP registration uses the shared contract input schema, so FastAPI and MCP
cannot silently drift at the wire boundary.

Deep Agent construction independently resolves the same identity and asks
Cedar which tools may be bound. Invocation rejects unauthorized portfolio
context before it reaches the model, checks content on both sides of model
execution, and pauses `run_backtest` through `interrupt_on`. This is
defense-in-depth, not a replacement for the API re-check. Day 10 makes MCP the
shared governed mount point; Day 12 makes AgentCore Gateway the only deployed
route to it.

---

## Multi-agent orchestration (Day 5)

The Portfolio Manager has only the native Deep Agents `task` delegation tool.
Specialists run in isolated context windows, so the orchestrator must include
the relevant named-source data in each task description.

```
question + context-builder output
  -> Portfolio Manager
       |-- task(macro)       -> interpolate_curve / price_bond
       |-- task(quant)       -> volatility / drawdown / risk
       |                       factor regression / backtest
       `-- task(fundamental) -> portfolio exposure / mocked research
  -> attributed synthesis
```

This is orchestration, not authorization. The specialist tool split reduces
accidental misuse but does not establish caller entitlements; Day 7 adds the
governed boundary checks.

---

## Failure and recovery (Day 5)

Specialist tool calls retry timeout/rate-limit failures twice with exponential
backoff, validate exact-name JSON Schema contracts when available, and convert
exhausted or malformed results into explicit `dead_letter` tool messages.
Per-run ceilings allow at most eight specialist tool calls and six Portfolio
Manager delegations; graph recursion defaults to 50 steps at invocation.

The Portfolio Manager's `task` calls are deliberately not retried wholesale.
With a checkpointer and stable `thread_id`, LangGraph preserves successful
parallel task writes. `resume_multi_agent()` resumes the failed task without
re-running a completed specialist. This was exercised by crashing Quant after
Macro completed: the observed invocation counts changed from
`macro=1, quant=1` at failure to `macro=1, quant=2` after resume. Read-only
specialist tools make that retry idempotent. The built-in
`create_checkpointed_multi_agent()` uses process-local memory for the Day 5
exercise; a durable checkpointer is still required before deployment.

---

## Observability and evaluation (Day 6)

`configure_telemetry()` owns one process-wide tracer provider. FastAPI
auto-instrumentation and manual application spans share that provider, while an
OTLP HTTP exporter sends the same hierarchy to LangSmith's
`/otel/v1/traces` endpoint. Span attributes record counts, sizes, identifiers,
status, timing, and estimated economics; raw analytics inputs are not copied
into operational attributes.

Evaluation wraps each Portfolio Manager invocation in an OTel root span. The
root carries the LangSmith experiment session and reference-example IDs plus
GenAI prompt/completion attributes, so every target trace lands in the
experiment and links back to its dataset case. Evaluator feedback is attached
per dimension rather than reduced to one aggregate score.

The Day 7 `gpt-4.1-mini` baseline extends Day 6 with deterministic policy
cases:

| Subset | Cases | Routing | Tool selection | Tool arguments | Retrieval context | Final answer | Policy | Tokens | Estimated cost | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fast floor | 7 | 100% | 100% | 80% | 100% | 60% | 100% | 57,221 | $0.0269 | 70.4 s |
| Full | 18 | 100% | 86.7% | 93.3% | 100% | 53.3% | 100% | 168,940 | $0.0797 | 204.6 s |

The fast Day 7 probe observed one missed tool call and two argument failures.
Because these were model variability rather than an intentional product
change, `config/eval-baseline.json` records those observed scores separately
and retains Day 6's stronger behavioral floors while adding policy compliance
at 100%. Baselines are not lowered merely to make a run pass.

Guardrail behavior remains `null`, not a passing placeholder, until Day 12.
CI permits at most a 0.10 absolute drop from the matching floor. Operational
totals establish a comparison footprint but are not CI failure thresholds
because hosted-runner latency and generated-token volume vary independently of
behavior.

Detailed trace correlation and experiment links are in
`docs/observability-evaluation.md`.

---

## Context engineering

`src/context/builder.py` is the only prompt-context assembly path for the
single agent. Its seven named sources are user/role, portfolio state, market
data, retrieved research, memory, previous tool outputs, and skills.

- **Full mode** includes all seven sources verbatim. It exists as the measured
  overload baseline, not the desired production default.
- **Filtered mode** requires user/role and an explicit source allowlist chosen
  for the task. Omitted research, memory, or prior outputs never enter the
  model prompt implicitly.
- Token size is measured with the selected model's tiktoken encoding.
- No summarization or tool-history compression exists yet; those remain the
  next controls after source filtering.

The Day 4 experiment is recorded in `docs/comparison-notes.md`. Filtering cut
the representative contexts by 49–96%, but Qwen3 4B still omitted the tool call
for a large 500-return argument in both full and filtered modes. Small-context
volatility and concentration questions did call the correct real tools.

---

## Document intelligence boundary

The document-to-skill capability is a future cross-cutting learning path for
Days 16–20. A supplied PDF or model document is untrusted input. The intended
flow preserves the original artifact and page-level extraction, creates a
structured document manifest, generates a candidate `SKILL.md` and contract,
and only then considers deterministic calculator candidates. Generated code
must pass static inspection, restricted execution, source-derived tests, and
human review before a Deep Agent can call it. The generated skill is a behavior
description, not an authorization control; MCP/Tool policy remains the final
enforcement boundary.

The first useful milestone is document-grounded Q&A with citations. Executable
model calculations are a later milestone because OCR, formula ambiguity, units,
annualization, missing-data conventions, and document-embedded prompt
injection can all change the meaning of a calculation.

## Security Model

### Trust boundaries and identity propagation

The caller supplies `X-Identity` to FastAPI or an identity in the named
`user_role` agent context. Only `src/control/identity.py` maps that value to a
role. A caller-supplied role string is descriptive context and never an
authorization input. Unknown identities receive no tools and HTTP callers
receive 401.

The local identities and effective access are:

| Identity | Role | Tool access | Portfolio access |
|---|---|---|---|
| `PM_USER` | `pm` | Current pricing, curve, research, econometrics, backtest, portfolio, and risk tools | `PORT_A` only |
| `RISK_USER` | `risk` | Curve, econometrics, backtest, portfolio, and risk tools; no pricing or research | `PORT_A` and `PORT_B` |
| `ADMIN_USER` | `admin` | Every explicitly registered current tool | `PORT_A` and `PORT_B` |

Cedar is default-deny: unknown tools, actions, portfolios, roles, and identities
do not inherit access, including for administrators. `config/roles.yaml`
contains no permissions; `governance/policies/` is their sole authority.

### Four independently enforced concerns

| Layer | Local enforcement | Failure behavior | AWS mapping captured Day 12 |
|---|---|---|---|
| AuthN | Exact identity lookup from `config/roles.yaml` | Unknown/missing identity is rejected before authorization | `config/agentcore.yaml` maps to AgentCore Identity; live resource not claimed |
| AuthZ | Cedar tool and portfolio policies; tools filtered before model binding | Tool/resource is absent or denied | `config/agentcore.yaml` maps to AgentCore Policy; Cedar intent remains source for review |
| Guardrails | Shared denied-term and topic check on question, named context, and final output | Content is withheld with `GuardrailViolation` | `config/bedrock-guardrail.yaml` captures extended Day 14 intent; standalone Bedrock Guardrails pass/block evidence is recorded |
| Tool enforcement | FastAPI and MCP repeat tool/resource authorization | HTTP/MCP denial before analytics/data access | ADR 0017 requires Gateway-fronted MCP; no direct deployed bypass |

Authorization does not trust skill contracts or prompt intent. A permitted tool
cannot reach `PORT_B` for `PM_USER`, because resource authorization runs before
agent context assembly and again at the API boundary. A request describing an
unknown write as a read remains denied because Cedar evaluates the actual tool
resource, not the request's wording.

### Threat model and tested negative paths

The deterministic negative suite under `governance/tests/` covers role
spoofing, instruction override attempts, system-instruction retrieval through
an unregistered tool, permitted-tool portfolio bypass, unlisted data export,
and write-shaped operations framed as reads. Content tests verify that the
same denied-term list used by pre-commit blocks generated output at runtime,
while topic tests block unqualified trading directives and prompt/credential
exfiltration without blocking risk narration. These controls reduce
prompt-injection and excessive-agency risk; they do not claim that string
matching detects every semantic attack.

### Human approval, audit, and secrets

`run_backtest` is visible only when Cedar permits it and is configured with
`interrupt_on` by default. Execution pauses before the tool runs, producing an
`interrupted` audit decision until a human approves or rejects it.

Audit records are append-only JSON Lines with timestamp, identity, role, tool,
resource (when applicable), decision (`allowed`, `denied`, or `interrupted`),
enforcement layer, and the active 32-character OTel trace ID. Authorization and
audit spans therefore correlate a denial or interruption with its end-to-end
trace.

Secrets remain outside version control in `.env` or GitHub Actions secrets.
Neither spans nor audit records contain credentials, raw prompts, raw
analytics inputs, or matched denied content. The local identity mechanism is a
learning stand-in, not credential authentication; AgentCore Identity replaces
it for deployment.

### Local controls versus AgentCore

The local stack proves policy separation, Cedar decisions, resource checks,
tool filtering, approval interrupts, guardrail placement, and traced audit
evidence. It does not provide signed identities, managed policy deployment,
semantic content classification, or a network-enforced gateway. Day 12 maps
those gaps respectively to AgentCore Identity, AgentCore Policy, Bedrock
Guardrails, and Gateway; Day 14 expands the content policy beyond simple
terms. The deployed architecture must expose no interactive path that bypasses
Gateway and its tool-boundary entitlement re-check.

---

## Repository layout

See `docs/PLAN.md` §1 for the full target repo tree and its sequencing rule (nothing is pre-stubbed before the day it's actually needed). Day 1 created the subset that today's steps use: `data/mock_structured/`, `src/{ingestion,control,api}/`, `config/roles.yaml`, `tests/unit/{control,ingestion}/`, `skills/{example-echo,python-best-practices}/`, `scripts/artifacts_host.py`, `artifacts/hello.html`, and the CI/progress-tracker/skills-freshness workflow skeletons.
