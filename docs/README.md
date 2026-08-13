# Documentation

Use this page as the documentation map. Repository entry points that benefit
from root-level visibility remain at the root: `README.md`, `AGENTS.md`,
`INSTALL.md`, and `PROGRESS.md`.

## Start here

| Need | Document |
|---|---|
| Set up the repository for the first time | [`../INSTALL.md`](../INSTALL.md) |
| See the current implementation day and evidence | [`../PROGRESS.md`](../PROGRESS.md) |
| Understand why the project exists | [`PRD.md`](PRD.md) |
| Follow the day-by-day build | [`PLAN.md`](PLAN.md) |
| Understand the current system design | [`ARCHITECTURE.md`](ARCHITECTURE.md) |

## Learn and operate

| Need | Document |
|---|---|
| Review daily retrospectives | [`LEARNINGS.md`](LEARNINGS.md) |
| Inspect Day 6 trace and evaluation evidence | [`observability-evaluation.md`](observability-evaluation.md) |
| Find source material by topic | [`REFERENCES.md`](REFERENCES.md) |
| Review model, context, tool, and AWS comparisons | [`comparison-notes.md`](comparison-notes.md) |
| Look up FICC terminology | [`ficc-glossary.md`](ficc-glossary.md) |
| Run, evaluate, deploy, or tear down the system | [`RUNBOOK.md`](RUNBOOK.md) |
| Review architecture decisions | `adr/` *(created as decisions are recorded)* |

| Run custom agents and skills standalone | [`AGENT_RUNBOOK.md`](AGENT_RUNBOOK.md) |
| Review AgentCore deployment intent and decisions | [`../config/agentcore.yaml`](../config/agentcore.yaml), [`adr/0016-agentcore-direct-code-deployment.md`](adr/0016-agentcore-direct-code-deployment.md), [`adr/0017-agentcore-gateway-only-tool-path.md`](adr/adr/0017-agentcore-gateway-only-tool-path.md) |

## Agent and contributor guidance

[`../AGENTS.md`](../AGENTS.md) remains the canonical router for AI coding tools
and repository rules. Skills under `../skills/` contain task-specific reusable
instructions; their contracts and tests live beside each skill.
