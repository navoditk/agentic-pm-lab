# Architecture

Canonical current-state architecture for agentic-pm-lab. Created Day 1, once the walking skeleton exists — updated in place whenever a design decision changes it, not recreated. See `docs/PRD.md` §2 for the target end-state each layer is heading toward, and `docs/PLAN.md` Appendix B for the day-by-day steps that get it there.

---

## The layers, and what exists today (Day 7)

| Layer | Target end-state (`docs/PRD.md` §2) | What exists today |
|---|---|---|
| **Data Layer** | Real yfinance/FRED/SEC EDGAR public ingestion | `src/ingestion/prices.py` loads daily OHLCV for six public ETFs from yfinance; `src/ingestion/macro.py` loads Treasury yields, Fed Funds, and CPI from FRED and derives `curve_points`. Both use a 24-hour JSON-file cache before replacing their DuckDB tables. `security_master` and `portfolio_positions` remain invented CSV fixtures and retain their `# MOCK` marker. |
| **Control Layer** | AuthN, AuthZ, Guardrails, and Tool enforcement as four separately-tested concerns (`docs/PRD.md` §3, principle 10) | `config/roles.yaml` assigns three local test identities only. Cedar policies independently govern tools and portfolio resources, agent construction removes unauthorized tools before model binding, portfolio context is checked before model access, a denied-terms guardrail checks input/context/output, and FastAPI re-checks tool plus resource access. Backtests pause for human approval. Every decision records its layer and OTel trace ID. |
| **Tool Layer** | Real deterministic engines, one JSON Schema contract each, wrapped once as MCP | `src/analytics/` contains deterministic bond/option pricing, curve interpolation, portfolio exposure/concentration, volatility/drawdown, OLS factor regression, and static-weight backtesting. `contracts/tools/` fixes each input/output shape, and `src/api/main.py` exposes the governed routes. Research intentionally remains mocked; MCP wrapping starts Day 10. |
| **Interactive Layer** | Four real GitHub Copilot Canvas extensions | Doesn't exist yet — starts Day 8. Today's only artifact is `.github/copilot-instructions.md`, a pointer to `AGENTS.md` so every harness reads the same routing rules. |
| **Runtime Layer** | Copilot-coding-agent PR through real CI → AWS Bedrock AgentCore Runtime | `scripts/artifacts_host.py`, a hand-built local FastAPI host serving anything dropped into `artifacts/` — a rough non-prod analog of a real artifact/report host. `.github/workflows/ci.yml` is the production-path skeleton (lint + test on push/PR); nothing deploys yet. |
| **Agent Layer** | LangGraph Deep Agents, single agent then multi-agent orchestration | `src/agents/multi_agent.py` defines a Portfolio Manager orchestrator with native Macro, Quant/Risk, and Fundamental sub-agents. Each specialist receives only its domain tools, and the orchestrator receives no analytics tools directly. `multi_agent_local.py` reproduces the hierarchy on Ollama/Qwen3 4B for comparison; the Day 5 cross-domain run did not delegate and returned empty. |
| **Observability** | One cost-aware OTel stream with local and agent-specific views | `src/observability/telemetry.py` instruments FastAPI and emits manual analytics, agent, authorization, identity, and audit spans. Agent spans include model, token, tool/retrieval call, retry, latency, success, and estimated-cost attributes. The same OTLP stream exports to LangSmith; no parallel proprietary tracing path exists. |
| **Evaluation** | Versioned behavioral regression suite across independent dimensions | Fifteen active golden/routing cases run as OTel-native LangSmith experiments. `scripts/run_eval.py` scores routing, tool selection, tool arguments, retrieval context, and final-answer criteria; policy and guardrail evaluators remain explicit stubs until their implementation days. `config/eval-baseline.json` and `eval-regression.yml` enforce subset-specific score floors. |
| **Automation** (Runtime sub-layer) | Scheduled pipeline + native platform automation | Doesn't exist yet — starts Day 11. |

The Data Layer is intentionally mixed: public price/macro data is real, while
portfolio and security metadata remains mock. Remaining stubs are tracked from
their `# MOCK` markers in `PROGRESS.md` (`docs/PLAN.md` §6).

---

## Logical components, through Day 7

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
contracts/tools/*.schema.json        input/output contract per engine
src/api/main.py                      governed FastAPI wrappers; research mock

scripts/artifacts_host.py            separate FastAPI app, serves artifacts/*

skills/example-echo/                 proves the Agent Skills package mechanism
skills/python-best-practices/        this project's actual coding conventions
skills/mock-to-real-migration/       safe mock replacement checklist
skills/ficc-glossary-maintainer/     consistent learning glossary format
skills/new-tool-onboarding/          end-to-end capability checklist
skills/skill-creator/                complete skill-package scaffolding recipe
skills/skill-tester/                 local static/mock skill validation recipe
skills/portfolio-risk-summary/       exposure/volatility/drawdown synthesis

src/context/builder.py               named full/filtered context composition
src/agents/single_agent.py           OpenAI-configured Deep Agent
src/agents/single_agent_local.py     same agent on local Ollama/Qwen3 4B
src/agents/multi_agent.py            Portfolio Manager -> three native specialist sub-agents
src/agents/multi_agent_local.py      same hierarchy on local Ollama/Qwen3 4B
src/agents/recovery.py               retry, validation, limits, and dead-letter middleware

src/observability/telemetry.py       shared OTel provider, spans, and LangSmith OTLP export
evals/*.jsonl                        golden, routing, authorization, and guardrail cases
scripts/run_eval.py                  OTel-native LangSmith experiment and scoring runner
config/eval-baseline.json            accepted fast/full scores and regression tolerance
skills/eval-dataset-authoring/       evaluation-case schema and authoring workflow

.github/workflows/ci.yml             lint + test on push/PR
.github/workflows/eval-regression.yml  fast PR/full main behavioral regression gate
.github/workflows/progress-tracker.yml  regenerates PROGRESS.md's status table on push to main
.github/workflows/skills-freshness.yml  placeholder, built out Day 11
.github/agents/eval-triage-agent.agent.md  read-only regression investigation persona
```

## Governed Tool Layer sequence (Day 7)

Public ingestion remains unchanged, while every direct Tool Layer API call
follows the governed boundary:

```
yfinance/FRED
  --> fresh TTL cache? -- yes --> normalized JSON records
          | no                  --> public API --> normalized JSON records
          +---------------------------> DuckDB tables

caller + X-Identity
  --> src/api/main.py
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

The accepted `gpt-4.1-mini` baseline is versioned in
`config/eval-baseline.json`:

| Subset | Cases | Routing | Tool selection | Tool arguments | Retrieval context | Final answer | Tokens | Estimated cost | Latency |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Fast | 5 | 100% | 100% | 80% | 100% | 60% | 51,710 | $0.0239 | 78.4 s |
| Full | 15 | 100% | 86.7% | 86.7% | 100% | 46.7% | 167,946 | $0.0774 | 363.4 s |

Policy-compliance and guardrail-behavior scores are `null`, not passing
placeholders; Days 7 and 12 activate those dimensions. CI permits at most a
0.10 absolute drop from the matching subset baseline, which means one failed
case in the five-case PR subset fails the gate. Operational totals establish a
comparison footprint but are not CI failure thresholds because hosted-runner
latency and generated-token volume vary independently of behavior.

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

| Layer | Local enforcement | Failure behavior | AWS target (Day 12) |
|---|---|---|---|
| AuthN | Exact identity lookup from `config/roles.yaml` | Unknown/missing identity is rejected before authorization | AgentCore Identity |
| AuthZ | Cedar tool and portfolio policies; tools filtered before model binding | Tool/resource is absent or denied | AgentCore Policy using equivalent Cedar rules |
| Guardrails | Shared denied-term check on question, named context, and final output | Content is withheld with `GuardrailViolation` | Bedrock Guardrails; local check remains defense-in-depth |
| Tool enforcement | FastAPI repeats tool authorization and portfolio-resource authorization | HTTP 403 before analytics/data access | Gateway-fronted MCP re-check; no direct deployed bypass |

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
same denied-term list used by pre-commit blocks generated output at runtime.
These controls reduce prompt-injection and excessive-agency risk; they do not
claim that string matching detects every semantic attack.

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
Guardrails, and Gateway. The deployed architecture must expose no interactive
path that bypasses Gateway and its tool-boundary entitlement re-check.

---

## Repository layout

See `docs/PLAN.md` §1 for the full target repo tree and its sequencing rule (nothing is pre-stubbed before the day it's actually needed). Day 1 created the subset that today's steps use: `data/mock_structured/`, `src/{ingestion,control,api}/`, `config/roles.yaml`, `tests/unit/{control,ingestion}/`, `skills/{example-echo,python-best-practices}/`, `scripts/artifacts_host.py`, `artifacts/hello.html`, and the CI/progress-tracker/skills-freshness workflow skeletons.
