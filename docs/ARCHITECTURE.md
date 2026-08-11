# Architecture

Canonical current-state architecture for agentic-pm-lab. Created Day 1, once the walking skeleton exists — updated in place whenever a design decision changes it, not recreated. See `docs/PRD.md` §2 for the target end-state each layer is heading toward, and `docs/PLAN.md` Appendix B for the day-by-day steps that get it there.

---

## The layers, and what exists today (Day 4)

| Layer | Target end-state (`docs/PRD.md` §2) | What exists today |
|---|---|---|
| **Data Layer** | Real yfinance/FRED/SEC EDGAR public ingestion | `src/ingestion/prices.py` loads daily OHLCV for six public ETFs from yfinance; `src/ingestion/macro.py` loads Treasury yields, Fed Funds, and CPI from FRED and derives `curve_points`. Both use a 24-hour JSON-file cache before replacing their DuckDB tables. `security_master` and `portfolio_positions` remain invented CSV fixtures and retain their `# MOCK` marker. |
| **Control Layer** | AuthN, AuthZ, Guardrails, and Tool enforcement as four separately-tested concerns (`docs/PRD.md` §3, principle 10) | Every `/tools/*` route now requires an `X-Identity`, resolves its temporary role from `config/roles.yaml`, re-checks `check_permission()` at the boundary, and appends the allow/deny decision to the audit log. The combined allowlist remains a `# MOCK` until Cedar splits identity from authorization on Day 7. |
| **Tool Layer** | Real deterministic engines, one JSON Schema contract each, wrapped once as MCP | `src/analytics/` contains deterministic bond/option pricing, curve interpolation, portfolio exposure/concentration, volatility/drawdown, OLS factor regression, and static-weight backtesting. `contracts/tools/` fixes each input/output shape, and `src/api/main.py` exposes the governed routes. Research intentionally remains mocked; MCP wrapping starts Day 10. |
| **Interactive Layer** | Four real GitHub Copilot Canvas extensions | Doesn't exist yet — starts Day 8. Today's only artifact is `.github/copilot-instructions.md`, a pointer to `AGENTS.md` so every harness reads the same routing rules. |
| **Runtime Layer** | Copilot-coding-agent PR through real CI → AWS Bedrock AgentCore Runtime | `scripts/artifacts_host.py`, a hand-built local FastAPI host serving anything dropped into `artifacts/` — a rough non-prod analog of a real artifact/report host. `.github/workflows/ci.yml` is the production-path skeleton (lint + test on push/PR); nothing deploys yet. |
| **Agent Layer** | LangGraph Deep Agents, single agent then multi-agent orchestration | `src/agents/single_agent.py` constructs one Deep Agent with nine deterministic analytics tools, shared skills, an explicit context builder, and an empty `interrupt_on` seam for Day 7. OpenAI is configured and a `gpt-4.1-mini` smoke test succeeds; `single_agent_local.py` runs the same harness on Ollama/Qwen3 4B and has completed real tool calls. |
| **Automation** (Runtime sub-layer) | Scheduled pipeline + native platform automation | Doesn't exist yet — starts Day 11. |

The Data Layer is intentionally mixed: public price/macro data is real, while
portfolio and security metadata remains mock. Remaining stubs are tracked from
their `# MOCK` markers in `PROGRESS.md` (`docs/PLAN.md` §6).

---

## Logical components, Day 3

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

config/roles.yaml                    role->tool permission + identity->role (temporary, combined)
  -> src/control/allowlist.py         check_permission(role, tool_name)
  -> src/control/audit.py             record_audit_event(...) -> data/cache/audit.jsonl

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

.github/workflows/ci.yml             lint + test on push/PR
.github/workflows/progress-tracker.yml  regenerates PROGRESS.md's status table on push to main
.github/workflows/skills-freshness.yml  placeholder, built out Day 11
```

## Request/tool sequence (Day 3 shape)

No runtime agent exists yet (Day 4). Public ingestion remains unchanged, while
every Tool Layer call now follows the governed boundary:

```
yfinance/FRED
  --> fresh TTL cache? -- yes --> normalized JSON records
          | no                  --> public API --> normalized JSON records
          +---------------------------> DuckDB tables

caller + X-Identity
  --> src/api/main.py
        --> role_for_identity(identity)
        --> check_permission(role, tool)
              |-- denied --> audit(allowed=false) --> HTTP 403
              |-- allowed --> audit(allowed=true)
                    --> validate typed request
                    --> src/analytics/<deterministic function>
                    --> typed JSON response
```

Day 4's LangChain tool wrappers currently call `src/analytics/` directly, as
the day's Deep Agents exercise specifies. They are not yet a governed
production path and must not be treated as authorization enforcement. Day 7
plugs identity/authorization and human approval into this tool seam; Day 10
then makes MCP the shared governed mount point.

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

## Security Boundaries

The FastAPI boundary is load-bearing for HTTP callers: missing or unknown identities receive
401, denied tools receive 403, and both allowed and denied known-identity
decisions are audited. This is still a learning-scale combined AuthN/AuthZ stub,
not the final security model. Day 7 separates identity lookup, Cedar policy,
guardrails, and parameter-level Tool enforcement and expands this section.
Until Day 7, the new direct LangChain analytics wrappers sit outside that HTTP
boundary and are explicitly non-governed learning code.

---

## Repository layout

See `docs/PLAN.md` §1 for the full target repo tree and its sequencing rule (nothing is pre-stubbed before the day it's actually needed). Day 1 created the subset that today's steps use: `data/mock_structured/`, `src/{ingestion,control,api}/`, `config/roles.yaml`, `tests/unit/{control,ingestion}/`, `skills/{example-echo,python-best-practices}/`, `scripts/artifacts_host.py`, `artifacts/hello.html`, and the CI/progress-tracker/skills-freshness workflow skeletons.
