# Documentation map

This directory is organized by reader intent, not by chronology. Use this page to
choose the right entry point for your goal.

The canonical product and architecture documents are:

- [`../README.md`](../README.md) — the repository pitch, scope, and quick start
- [`../INSTALL.md`](../INSTALL.md) — installation and verification
- [`../AGENTS.md`](../AGENTS.md) — AI-tool routing and repo entry points
- [`architecture/PRD.md`](architecture/PRD.md) — problem statement, goals, and success criteria
- [`architecture/ARCHITECTURE.md`](architecture/ARCHITECTURE.md) — current system shape and security boundaries
- [`PLAN.md`](PLAN.md) — the canonical 21-day build plan
- [`../PROGRESS.md`](../PROGRESS.md) — current status and evidence state

## Choose your path

| Goal | Start here |
|---|---|
| Browse the full curriculum without downloading | [GitHub Pages curriculum](https://navoditk.github.io/agentic-pm-lab/) or [standalone artifact](../artifacts/agentic-pm-curriculum.html) |
| Learn with a guided agent | Open a local checkout in Copilot, Claude Code, or Codex and say **`agentexpert`**; see [Mastery skill](learning/MASTERY_SKILL.md) |
| Complete local courses with lab evidence | [Start here](learning/START_HERE.md), then the [recommended order](learning/TUTOR_COURSE_GUIDE.md#recommended-order) and [Depth Path](learning/DEPTH_PATH.md) |
| Understand or build the platform | [Phase 1 recap](learning/PHASE_1_RECAP.md) for what was built, then [PRD](architecture/PRD.md), [Architecture](architecture/ARCHITECTURE.md), [Plan](PLAN.md), and [Progress](../PROGRESS.md) |
| Run or operate it locally | [Install](../INSTALL.md), [Runbook](guides/RUNBOOK.md), and [GitHub workflow guide](guides/GITHUB_WORKFLOWS.md) |
| Review proof and benchmarks | [Evidence ledger](evidence/EVIDENCE.md) and the [benchmark reports](#evidence-and-evaluation) |
| Explore AWS, Canvas, or orchestration | [AWS AgentCore setup](guides/AWS_AGENTCORE_SETUP.md), [Gateway exercise](guides/AGENTCORE_GATEWAY_SETUP.md), [Canvas exercises](guides/CANVAS_EXERCISES.md), and [Agent runbook](guides/AGENT_RUNBOOK.md) |

## Documentation by purpose

### Canonical product and architecture

- [`../README.md`](../README.md)
- [`../INSTALL.md`](../INSTALL.md)
- [`../AGENTS.md`](../AGENTS.md)
- [`../PROGRESS.md`](../PROGRESS.md)
- [`architecture/PRD.md`](architecture/PRD.md)
- [`architecture/ARCHITECTURE.md`](architecture/ARCHITECTURE.md)
- [`architecture/DIAGRAMS.md`](architecture/DIAGRAMS.md)
- [`PLAN.md`](PLAN.md)

### Learning and study materials

- [`learning/START_HERE.md`](learning/START_HERE.md)
- [`learning/MASTERY_SKILL.md`](learning/MASTERY_SKILL.md)
- [`learning/CURRICULUM_FRESHNESS_PLAN.md`](learning/CURRICULUM_FRESHNESS_PLAN.md)
- [`learning/TUTOR_COURSE_GUIDE.md`](learning/TUTOR_COURSE_GUIDE.md)
- [`learning/DEPTH_PATH.md`](learning/DEPTH_PATH.md)
- [`learning/PHASE_1_RECAP.md`](learning/PHASE_1_RECAP.md)
- [`learning/PHASE_2_PLAN.md`](learning/PHASE_2_PLAN.md)
- [`learning/LEARNER_PROGRESS.md`](learning/LEARNER_PROGRESS.md)
- [`learning/LEARNINGS.md`](learning/LEARNINGS.md)
- [`learning/comparison-notes.md`](learning/comparison-notes.md)
- [`learning/observability-evaluation.md`](learning/observability-evaluation.md)
- [`learning/ficc-glossary.md`](learning/ficc-glossary.md)

### Guides and operations

- [`guides/RUNBOOK.md`](guides/RUNBOOK.md)
- [`guides/GITHUB_WORKFLOWS.md`](guides/GITHUB_WORKFLOWS.md)
- [`guides/CANVAS_EXERCISES.md`](guides/CANVAS_EXERCISES.md)
- [`guides/TUTOR_RUNBOOK.md`](guides/TUTOR_RUNBOOK.md)
- [`guides/AGENT_RUNBOOK.md`](guides/AGENT_RUNBOOK.md)
- [`guides/AWS_AGENTCORE_SETUP.md`](guides/AWS_AGENTCORE_SETUP.md)
- [`guides/AGENTCORE_GATEWAY_SETUP.md`](guides/AGENTCORE_GATEWAY_SETUP.md)

### Evidence and evaluation

- [`evidence/EVIDENCE.md`](evidence/EVIDENCE.md)
- [`learning/CANONICAL_PM_BENCHMARK_REPORT.md`](learning/CANONICAL_PM_BENCHMARK_REPORT.md)
- [`learning/INSTITUTIONAL_PM_EVALUATION_SCORECARD.md`](learning/INSTITUTIONAL_PM_EVALUATION_SCORECARD.md)
- [`learning/INSTITUTIONAL_PM_SCORECARD_V2.md`](learning/INSTITUTIONAL_PM_SCORECARD_V2.md)

### Reference and decisions

- [`reference/REFERENCES.md`](reference/REFERENCES.md)
- [`adr/`](adr/)
- [`../experiments/README.md`](../experiments/README.md)
- [`../data/README.md`](../data/README.md)

`AGENTS.md` remains the canonical router for AI coding tools. Reusable
implementation and learning skills live under `../skills/`; the shared
mastery package is [`skills/agentic-pm-mastery/`](../skills/agentic-pm-mastery/)
with discovery loaders for Copilot, Claude Code, and Codex.
