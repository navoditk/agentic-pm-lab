# AGENTS.md — Agent & Tool Routing

This file is read automatically by Claude Code, by GitHub Copilot (coding agent, CLI, and the Copilot app), and by OpenAI Codex CLI at the start of a session in this repo. Its only job is to route: point each tool at the right document for the right question, so the project doesn't need re-explaining every session regardless of which tool picked it up.

`.github/copilot-instructions.md` exists only as a thin pointer back to this file, for Copilot surfaces that specifically look in `.github/` first.

## The documents, and when to read which

- **`INSTALL.md`** — one-time environment and repo setup, done before Day 1. Self-contained; read this first if the repo has no `pyproject.toml` yet or the verification checklist at its end hasn't been completed.
- **`PRD.md`** — the *why*. Vision, target architecture, design principles, the business problems this platform answers, tiered success criteria, acceptance tests, explicit non-goals. Read this when you need to understand intent, not steps.
- **`PLAN.md`** — the *how*. Repo layout, the full day-by-day implementation steps (Appendix B), the skills/contracts/prompts/custom-agents/pre-commit-hooks catalogs, context engineering (§13), failure engineering (§14), the security model (§15), references. Read this to actually do the work for a given day.
- **`PROGRESS.md`** — the *where we are*. Current day, the auto-generated mock→real status table, completed vs. pending checklist, evidence links. Read this first among the others, to know what's already done.
- **`ARCHITECTURE.md`** — canonical current-state architecture (created Day 1, updated whenever a design decision changes it), including a dedicated Security Model section (AuthN/AuthZ/Guardrails/Tool-enforcement) added Day 7 — merged in rather than a separate `SECURITY.md`, since one doc is easier to keep current than two that need to agree with each other. **`RUNBOOK.md`** — how to start/test/eval/deploy/teardown (created Day 11). Neither exists until its creation day — check `PROGRESS.md` if unsure whether it's there yet.
- **`REFERENCES.md`** — curated reading by topic, pre-written from Day 1 and updated in place as you learn. `PLAN.md`'s day-by-day steps each point at a specific subsection of this file rather than repeating it.

## Repo rules (non-negotiable, apply regardless of which day or tool)

- No company-sensitive information, internal system names, or proprietary data anywhere — in code, commits, docs, comments, or generated output. Public and mock data only (PRD.md §1 and §3, principle 3).
- Every unfinished endpoint carries a `# MOCK — replace on Day X` docstring.
- No test in `tests/unit/` may hit a real network call, API, or cloud resource — mock external dependencies (PLAN.md §4).
- Every skill's frontmatter (`covers`, `last_verified_commit`) must stay in sync with the code it documents, or the PR needs a `skills-unaffected` label (PLAN.md §8.4).
- Every skill and tool has a `contract.yaml`/JSON Schema contract; a change to allowed tools, inputs, or output shape updates the contract in the same PR (PLAN.md §8.2, §8.3).
- Authorization is never inferred from a skill's stated intent — only `governance/policies/` (Cedar) and the tool-boundary re-check actually enforce what's allowed (PLAN.md §15). Never write code that trusts a skill's `contract.yaml` as a security control.
- No PR that touches `governance/`, `config/roles.yaml`, or `src/control/` merges without `authorization-tests.yml` passing, including its negative/adversarial cases (PLAN.md §15.2).
- Commit small, commit often, push after every commit — see the git workflow at the top of PLAN.md's Appendix B, and the commit checkpoints listed in each day's section.

## How to onboard onto today's work

**First time in this repo, or `pyproject.toml` doesn't exist yet?** Do `INSTALL.md` first, start to finish, including its verification checklist — it's self-contained and covers repo bootstrap plus every tool the whole plan needs. Only come back here once that's done.

1. Read `PROGRESS.md` — confirms the current day and what's already done.
2. Read `PLAN.md`'s Appendix B section for that day in full — goal, install/account setup (if any), recommended tool, numbered steps, commit checkpoints, track-progress line.
3. If a step references a design decision you don't have context for, check `PRD.md` (architecture layers, principles, business problems) rather than guessing.
4. Do the work.
5. Update `PROGRESS.md`'s narrative line — including evidence links (PR, test run, eval run, trace, screenshot, ADR — whichever apply) — and `LEARNINGS.md`. The status table itself is regenerated automatically by `progress-tracker.yml`, so don't hand-edit that part.
6. Commit and push at each checkpoint listed in that day's PLAN.md section, not just once at the end.

## Day → PLAN.md quick reference

| Day | Focus | Where |
|---|---|---|
| *(before Day 1)* | Environment & repo setup | `INSTALL.md`, start to finish |
| 1 | Foundation: walking skeleton | PLAN.md Appendix B, Day 1 |
| 2 | Data Layer: real public data | PLAN.md Appendix B, Day 2 |
| 3 | Tool Layer: real deterministic engines | PLAN.md Appendix B, Day 3 |
| 4 | Deep Agents: single agent | PLAN.md Appendix B, Day 4 |
| 5 | Deep Agents: multi-agent orchestration | PLAN.md Appendix B, Day 5 |
| 6 | OpenTelemetry, LangSmith, eval dataset | PLAN.md Appendix B, Day 6 |
| 7 | Control Layer for real | PLAN.md Appendix B, Day 7 |
| 8 | Canvas fundamentals (Kanban + Issue Triage) | PLAN.md Appendix B, Day 8 |
| 9 | Canvas: Agent Operations | PLAN.md Appendix B, Day 9 |
| 10 | Canvas: Portfolio/Risk capstone | PLAN.md Appendix B, Day 10 |
| 11 | Runtime & Automation, prompts, PR path | PLAN.md Appendix B, Day 11 |
| 12 | AWS Bedrock AgentCore, portfolio optimization, wrap-up | PLAN.md Appendix B, Day 12 |
| 13 *(optional)* | AgentCore Memory & Evaluations | PLAN.md, Optional AWS Deep-Dive Extension, Day 13 |
| 14 *(optional)* | Bedrock Guardrails + stretch | PLAN.md, Optional AWS Deep-Dive Extension, Day 14 |

## Tool-specific notes

- **Claude Code** reads this file automatically at session start. Best fit for architecture decisions, multi-file reasoning, and framework/cloud debugging — Days 1, 3, 4, 5, 7, 12, and the optional 13–14 lean on it most.
- **GitHub Copilot CLI, Desktop, and the Copilot app** read this file (via the `.github/copilot-instructions.md` pointer for surfaces that need it explicitly). Best fit for repetitive scaffolding, canvas building, and GitHub-platform work — Days 2, 6, 8, 9, 10, and 11 lean on it most.
- **OpenAI Codex CLI** reads this file automatically too (its own `/init` command exists to create one, but this repo already has it). A reasonable substitute wherever Claude Code is the default — deep reasoning, debugging, architecture work — if you'd rather use it or want to compare the two on the same task. Doesn't substitute for the Copilot app on the canvas days (8–10) or the Day 11 PR exercise; those stay Copilot-specific regardless of which CLI tool handles everything else.
- Any of the three CLI tools can be used any day; PLAN.md's per-day "Recommended dev tool" line is a default, not a restriction. `INSTALL.md` §8 has exact launch commands for all three.
