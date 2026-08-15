# Documentation

Use this page as the documentation map. Repository entry points that benefit
from root-level visibility remain at the root: `README.md`, `AGENTS.md`,
`INSTALL.md`, and `PROGRESS.md`.

## Start here

| Need | Document |
|---|---|
| Set up the repository for the first time | [`../INSTALL.md`](../INSTALL.md) |
| See the current implementation day and evidence | [`../PROGRESS.md`](../PROGRESS.md) |
| Separate local proof from live integration evidence | [`EVIDENCE.md`](EVIDENCE.md) |
| Quick-reference AWS setup, architecture, workflow, evidence, and cost | [`AWS_AGENTCORE_SETUP.md`](AWS_AGENTCORE_SETUP.md) |
| Run and compare local, hosted, and AWS experiments | [`../experiments/README.md`](../experiments/README.md) |
| Audit the 20-day plan and separate local completion from live evidence | [`PLAN_REVIEW.md`](PLAN_REVIEW.md) |
| Review the completed Phase 1 recap and learning path | [`PHASE_1_RECAP.md`](PHASE_1_RECAP.md) |
| Understand the GitHub Actions checks and automation | [`GITHUB_WORKFLOWS.md`](GITHUB_WORKFLOWS.md) |
| Follow the institutional PM AI production-readiness track | [`PHASE_2_PLAN.md`](PHASE_2_PLAN.md) |
| Understand why the project exists | [`PRD.md`](PRD.md) |
| Follow the day-by-day build | [`PLAN.md`](PLAN.md) |
| Understand the current system design | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| See the key architecture diagrams | [`DIAGRAMS.md`](DIAGRAMS.md) |
| Run end-to-end PM Canvas exercises | [`CANVAS_EXERCISES.md`](CANVAS_EXERCISES.md) |

## Learn and operate

| Need | Document |
|---|---|
| Review daily retrospectives | [`LEARNINGS.md`](LEARNINGS.md) |
| Inspect Day 6 trace and evaluation evidence | [`observability-evaluation.md`](observability-evaluation.md) |
| Find source material by topic | [`REFERENCES.md`](REFERENCES.md) |
| Review structured/unstructured data sources and provider cards | [`../data/README.md`](../data/README.md) |
| Explore public investment-data samples and decision use | [`../.github/agents/investment-data-tutor.agent.md`](../.github/agents/investment-data-tutor.agent.md), [`../scripts/investment_data_tutor.py`](../scripts/investment_data_tutor.py) |
| Browse representative normalized public-data records | [`../data/samples/public_investment/README.md`](../data/samples/public_investment/README.md) |
| Review model, context, tool, and AWS comparisons | [`comparison-notes.md`](comparison-notes.md) |
| Look up FICC terminology | [`ficc-glossary.md`](ficc-glossary.md) |
| Run, evaluate, deploy, or tear down the system | [`RUNBOOK.md`](RUNBOOK.md) |
| Review architecture decisions | `adr/` *(created as decisions are recorded)* |

| Run custom agents and skills standalone | [`AGENT_RUNBOOK.md`](AGENT_RUNBOOK.md) |
| Study roadmap topics with standalone tutor agents | [`TUTOR_RUNBOOK.md`](TUTOR_RUNBOOK.md) |
| Convert a model document into a reviewed skill/Deep Agent proposal | [`TUTOR_RUNBOOK.md`](TUTOR_RUNBOOK.md), [`REFERENCES.md`](REFERENCES.md) |
| Review AgentCore deployment intent and decisions | [`../config/agentcore.yaml`](../config/agentcore.yaml), [`adr/0016-agentcore-direct-code-deployment.md`](adr/0016-agentcore-direct-code-deployment.md), [`adr/0017-agentcore-gateway-only-tool-path.md`](adr/0017-agentcore-gateway-only-tool-path.md) |
| Browse dated live experiment records | [`../experiments/`](../experiments/) |

## Agent and contributor guidance

[`../AGENTS.md`](../AGENTS.md) remains the canonical router for AI coding tools
and repository rules. Skills under `../skills/` contain task-specific reusable
instructions; their contracts and tests live beside each skill.
