# Documentation

Every document in this repository, grouped by what you are trying to do. If
you are new, read [Start here](learning/START_HERE.md) first; if you only want
the courses, open the [curriculum site](https://navoditk.github.io/agentic-pm-lab/).

## Learn

| Document | What it is for |
|---|---|
| [Start here](learning/START_HERE.md) | The on-ramp: three ways in, and the seven steps of the local course path |
| [Tutor course guide](learning/TUTOR_COURSE_GUIDE.md) | The recommended order, how to work through one course, and the completion rubric |
| [Course deep dives](learning/tutors/) | One document per course: concepts, this repository's implementation, the four threads, a walkthrough, and pitfalls |
| [Depth path](learning/DEPTH_PATH.md) | The orient, trace, break, teach method behind every course, and an optional fixture capstone |
| [Mastery skill](learning/MASTERY_SKILL.md) | The `agentexpert` tutor for Claude Code, Copilot, and Codex |
| [Live labs](learning/LIVE_LABS.md) | Optional runs against real services, each with its cost, credentials, and cleanup |
| [Learner progress](learning/LEARNER_PROGRESS.md) | Your recorded quiz results (generated) |
| [Phase 1 recap](learning/PHASE_1_RECAP.md) | What the 21-day build delivered, day by day, with a self-check list |
| [FICC glossary](learning/ficc-glossary.md) | Plain-language fixed-income terms used across the repository |

## Understand the platform

| Document | What it is for |
|---|---|
| [PRD](architecture/PRD.md) | The problem, goals, success criteria, and non-goals |
| [Architecture](architecture/ARCHITECTURE.md) | The current system, its layers, and the security model |
| [Diagrams](architecture/DIAGRAMS.md) | The visual companion to the architecture |
| [Architecture decisions](adr/) | ADRs 0016 to 0021, from AgentCore deployment to the capstone design |
| [References](reference/REFERENCES.md) | Curated reading by topic, with the sources every course cites |

## Run it

| Document | What it is for |
|---|---|
| [INSTALL](../INSTALL.md) | Rebuilding the platform from an empty directory (not needed to learn) |
| [Runbook](guides/RUNBOOK.md) | Starting, testing, evaluating, and tearing down the local stack |
| [GitHub workflows](guides/GITHUB_WORKFLOWS.md) | Every CI workflow: what it checks, when it runs, and how to run it locally |
| [Tutor runbook](guides/TUTOR_RUNBOOK.md) | Using one tutor persona on its own, from any coding agent |
| [Agent runbook](guides/AGENT_RUNBOOK.md) | Exercising the custom agents and skills standalone |
| [Agents and skills across CLIs](guides/CLI_AGENTS_AND_SKILLS.md) | How one agent or skill source is generated for Claude Code, Copilot, and Codex |
| [Canvas exercises](guides/CANVAS_EXERCISES.md) | One PM question end to end in GitHub Copilot Canvas |
| [AWS AgentCore setup](guides/AWS_AGENTCORE_SETUP.md) | Account setup, budgets, a first Runtime, and teardown |
| [AgentCore Gateway exercise](guides/AGENTCORE_GATEWAY_SETUP.md) | Putting the MCP tools behind a managed Gateway |
| [Direct model runs](guides/DIRECT_MODEL_RUNS.md) | Running the capstone against a hosted model outside AgentCore |

## Build and status

| Document | What it is for |
|---|---|
| [PROGRESS](../PROGRESS.md) | Build status by layer (generated) and the dated narrative log |
| [PLAN](PLAN.md) | The 21-day build plan, day by day; `agentic-pm-lab plan <day>` prints one day |
| [Completion audit](learning/PLAN_REVIEW.md) | An independent review of the plan against what was built |
| [Phase 2 plan](learning/PHASE_2_PLAN.md) | A proposed production-readiness track |
| [No-cost roadmap](learning/NO_COST_ROADMAP.md) | What could be built next without spending anything |
| [Foundations mastery plan](learning/FOUNDATIONS_MASTERY_PLAN.md) | How the curriculum, quizzes, and learner tools were designed |
| [Curriculum freshness plan](learning/CURRICULUM_FRESHNESS_PLAN.md) | How course sources are monitored and reviewed |
| [Learnings](learning/LEARNINGS.md) | A dated retrospective, written as the build went |
| [AGENTS](../AGENTS.md) | Rules and routing for every coding agent working in the repository |

## Evidence and evaluation

| Document | What it is for |
|---|---|
| [Evidence ledger](evidence/EVIDENCE.md) | Local proof separated from live integration evidence |
| [Benchmark report](learning/CANONICAL_PM_BENCHMARK_REPORT.md) | The institutional PM morning-review benchmark |
| [Evaluation scorecard](learning/INSTITUTIONAL_PM_EVALUATION_SCORECARD.md) and [v2](learning/INSTITUTIONAL_PM_SCORECARD_V2.md) | Advanced evaluation results across models and runs |
| [Qualitative review](learning/INSTITUTIONAL_PM_QUALITATIVE_REVIEW.md) | A provisional review of the 38 observed runs |
| [Observability and evaluation evidence](learning/observability-evaluation.md) | The Day 6 baseline and how it was derived |
| [Comparison notes](learning/comparison-notes.md) | Measured comparisons made during the build |
| [Experiments](../experiments/README.md) | Recorded experiments, with their setup and cleanup |
| [Public data](../data/README.md) | The public-data catalog and sample pack |
