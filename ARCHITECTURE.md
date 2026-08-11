# Architecture

Canonical current-state architecture for agentic-pm-lab. Created Day 1, once the walking skeleton exists — updated in place whenever a design decision changes it, not recreated. See `PRD.md` §2 for the target end-state each layer is heading toward, and `PLAN.md` Appendix B for the day-by-day steps that get it there.

---

## The layers, and what exists today (Day 2)

| Layer | Target end-state (`PRD.md` §2) | What exists today |
|---|---|---|
| **Data Layer** | Real yfinance/FRED/SEC EDGAR public ingestion | `src/ingestion/prices.py` loads daily OHLCV for six public ETFs from yfinance; `src/ingestion/macro.py` loads Treasury yields, Fed Funds, and CPI from FRED and derives `curve_points`. Both use a 24-hour JSON-file cache before replacing their DuckDB tables. `security_master` and `portfolio_positions` remain invented CSV fixtures and retain their `# MOCK` marker. |
| **Control Layer** | AuthN, AuthZ, Guardrails, and Tool enforcement as four separately-tested concerns (`PRD.md` §3, principle 10) | A single combined stub: `src/control/allowlist.py` (`check_permission(role, tool_name)`, backed by `config/roles.yaml`) and `src/control/audit.py` (append-only JSON Lines log). AuthN/AuthZ aren't split yet, Guardrails and real Tool enforcement don't exist yet. `# MOCK — replace on Day 7` with `governance/policies/*.cedar`. |
| **Tool Layer** | Real deterministic engines, one JSON Schema contract each, wrapped once as MCP | `src/api/main.py` — `/tools/curve` now reads raw FRED-derived points from DuckDB. The other five endpoints remain stubs; interpolation, analytics contracts, and Control Layer enforcement arrive on Day 3. |
| **Interactive Layer** | Four real GitHub Copilot Canvas extensions | Doesn't exist yet — starts Day 8. Today's only artifact is `.github/copilot-instructions.md`, a pointer to `AGENTS.md` so every harness reads the same routing rules. |
| **Runtime Layer** | Copilot-coding-agent PR through real CI → AWS Bedrock AgentCore Runtime | `scripts/artifacts_host.py`, a hand-built local FastAPI host serving anything dropped into `artifacts/` — a rough non-prod analog of a real artifact/report host. `.github/workflows/ci.yml` is the production-path skeleton (lint + test on push/PR); nothing deploys yet. |
| **Agent Layer** | LangGraph Deep Agents, single agent then multi-agent orchestration | Doesn't exist yet — starts Day 4. |
| **Automation** (Runtime sub-layer) | Scheduled pipeline + native platform automation | Doesn't exist yet — starts Day 11. |

The Data Layer is intentionally mixed: public price/macro data is real, while
portfolio and security metadata remains mock. Remaining stubs are tracked from
their `# MOCK` markers in `PROGRESS.md` (`PLAN.md` §6).

---

## Logical components, Day 2

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

src/api/main.py                      FastAPI app; real raw-curve read, 5 stubs
  (not yet calling allowlist.check_permission -- wired Day 3)

scripts/artifacts_host.py            separate FastAPI app, serves artifacts/*

skills/example-echo/                 proves the Agent Skills package mechanism
skills/python-best-practices/        this project's actual coding conventions
skills/mock-to-real-migration/       safe mock replacement checklist
skills/ficc-glossary-maintainer/     consistent learning glossary format

.github/workflows/ci.yml             lint + test on push/PR
.github/workflows/progress-tracker.yml  regenerates PROGRESS.md's status table on push to main
.github/workflows/skills-freshness.yml  placeholder, built out Day 11
```

## Request/tool sequence (Day 2 shape)

No runtime agent exists yet (Day 4). Public data ingestion and the raw curve
read now follow these paths:

```
yfinance/FRED
  --> fresh TTL cache? -- yes --> normalized JSON records
          | no                  --> public API --> normalized JSON records
          +---------------------------> DuckDB tables

caller --> GET /tools/curve --> DuckDB curve_points --> raw tenor/rate response
```

By Day 3, this becomes:

```
caller --> src/api/main.py --> src/control/allowlist.check_permission(role, tool)
             |-- denied --> 403, audit.record_audit_event(..., allowed=False)
             |-- allowed --> src/analytics/<real function> --> response, audit.record_audit_event(..., allowed=True)
```

---

## Security Boundaries

*Placeholder — filled in properly on Day 7, when the Control Layer splits into real AuthN, AuthZ, Guardrails, and Tool enforcement (`PLAN.md` §15). Today's "boundary" is just `check_permission()`, called nowhere yet — it becomes load-bearing once Day 3 wires it into `src/api/main.py`, and gets replaced by real Cedar policy on Day 7.*

---

## Repository layout

See `PLAN.md` §1 for the full target repo tree and its sequencing rule (nothing is pre-stubbed before the day it's actually needed). Day 1 created the subset that today's steps use: `data/mock_structured/`, `src/{ingestion,control,api}/`, `config/roles.yaml`, `tests/unit/{control,ingestion}/`, `skills/{example-echo,python-best-practices}/`, `scripts/artifacts_host.py`, `artifacts/hello.html`, and the CI/progress-tracker/skills-freshness workflow skeletons.
