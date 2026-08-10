# Architecture

Canonical current-state architecture for agentic-pm-lab. Created Day 1, once the walking skeleton exists — updated in place whenever a design decision changes it, not recreated. See `PRD.md` §2 for the target end-state each layer is heading toward, and `PLAN.md` Appendix B for the day-by-day steps that get it there.

---

## The layers, and what exists today (Day 1)

| Layer | Target end-state (`PRD.md` §2) | What exists today |
|---|---|---|
| **Data Layer** | Real yfinance/FRED/SEC EDGAR public ingestion | `data/mock_structured/*.csv` (invented portfolio/security/curve data) loaded into a local DuckDB file by `src/ingestion/load_mock_structured_data.py`. `# MOCK — replace on Day 2` (prices/curve) and later (security master). |
| **Control Layer** | AuthN, AuthZ, Guardrails, and Tool enforcement as four separately-tested concerns (`PRD.md` §3, principle 10) | A single combined stub: `src/control/allowlist.py` (`check_permission(role, tool_name)`, backed by `config/roles.yaml`) and `src/control/audit.py` (append-only JSON Lines log). AuthN/AuthZ aren't split yet, Guardrails and real Tool enforcement don't exist yet. `# MOCK — replace on Day 7` with `governance/policies/*.cedar`. |
| **Tool Layer** | Real deterministic engines, one JSON Schema contract each, wrapped once as MCP | `src/api/main.py` — six FastAPI stub endpoints (`price-bond`, `curve`, `research`, `econometrics`, `backtest`, `portfolio`), each returning a canned response. No contracts yet (Day 3). Not yet wired to the Control Layer's entitlement check (also Day 3). |
| **Interactive Layer** | Four real GitHub Copilot Canvas extensions | Doesn't exist yet — starts Day 8. Today's only artifact is `.github/copilot-instructions.md`, a pointer to `AGENTS.md` so every harness reads the same routing rules. |
| **Runtime Layer** | Copilot-coding-agent PR through real CI → AWS Bedrock AgentCore Runtime | `scripts/artifacts_host.py`, a hand-built local FastAPI host serving anything dropped into `artifacts/` — a rough non-prod analog of a real artifact/report host. `.github/workflows/ci.yml` is the production-path skeleton (lint + test on push/PR); nothing deploys yet. |
| **Agent Layer** | LangGraph Deep Agents, single agent then multi-agent orchestration | Doesn't exist yet — starts Day 4. |
| **Automation** (Runtime sub-layer) | Scheduled pipeline + native platform automation | Doesn't exist yet — starts Day 11. |

Everything above (except the Interactive Layer's pointer file and the CI skeleton) is deliberately mocked or stubbed — see each layer's own `# MOCK` markers, tracked automatically in `PROGRESS.md`'s mock→real table (`PLAN.md` §6).

---

## Logical components, Day 1

```
data/mock_structured/*.csv          invented seed data (portfolio, security, curve)
  -> src/ingestion/load_mock_structured_data.py
      -> data/cache/portfolio.duckdb   (gitignored, regenerated on demand)

config/roles.yaml                    role->tool permission + identity->role (temporary, combined)
  -> src/control/allowlist.py         check_permission(role, tool_name)
  -> src/control/audit.py             record_audit_event(...) -> data/cache/audit.jsonl

src/api/main.py                      FastAPI app, 6 stub Tool Layer endpoints
  (not yet calling allowlist.check_permission -- wired Day 3)

scripts/artifacts_host.py            separate FastAPI app, serves artifacts/*

skills/example-echo/                 proves the Agent Skills package mechanism
skills/python-best-practices/        this project's actual coding conventions

.github/workflows/ci.yml             lint + test on push/PR
.github/workflows/progress-tracker.yml  regenerates PROGRESS.md's status table on push to main
.github/workflows/skills-freshness.yml  placeholder, built out Day 11
```

## First-pass request/tool sequence (Day 1 shape)

No agent exists yet (Day 4), so today's "sequence" is just the Tool Layer's own request path — this grows a Control Layer check (Day 3), then an agent in front of it (Day 4), then multi-agent routing (Day 5):

```
caller (curl / Streamlit / test)
  --> src/api/main.py  (e.g. GET /tools/curve)
        --> returns canned mock response, tagged "mock": true
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
