# GitHub Workflows

This document explains the GitHub Actions workflows used by the repository.
They are separate gates because passing unit tests alone does not prove that
authorization, contracts, evaluation quality, documentation freshness, and
operational automation are correct.

All workflows use public/mock learning data unless explicitly documented
otherwise. None of them places trades or approves an investment decision.

## Quick start

1. Run the local equivalents in [Local equivalents](#local-equivalents).
2. Open the failed job, if any, and identify whether it is a code, contract,
   authorization, freshness, evaluation, or configuration failure.
3. Read the matching workflow section below.
4. Reproduce the narrowest check locally before changing the code.

The broad `CI` workflow is the baseline. The other workflows are focused gates
that activate only for relevant paths or events.

## GitHub Projects learning board

The repository uses a GitHub Projects v2 board as the human-facing control
plane for the 21-day learning journey. It tracks learning work and evidence;
it does not replace `PROGRESS.md`, which remains the machine-checked source of
repository-local completion.

Recommended project name: **Agentic PM Lab Learning**.

The configured board is [Agentic PM Lab Learning](https://github.com/users/navoditk/projects/2).
It is linked to the [`navodit/agentic-pm-lab`](https://github.com/navoditk/agentic-pm-lab)
repository and currently contains one roadmap item for each day plus the two
existing morning-review issues.

Configure these fields:

| Field | Type | Values or purpose |
|---|---|---|
| Status | Built-in board status | Todo, In Progress, Done; use linked PRs and evidence for review state |
| Day | Number | 1–21; use 0 for cross-cutting work |
| Workstream | Single select | Foundation, Data, Agents, Governance, Evaluation, Canvas, AWS, Documentation |
| Evidence | Single select | Local test, Screenshot, Workflow run, Live provider, AWS, Not claimed |
| Priority | Single select | P0, P1, P2 |
| Learner outcome | Text | The question or capability the learner should understand |

Create these views:

1. **21-day roadmap** — table grouped by `Day`, sorted ascending; expose
   `Status`, `Workstream`, `Evidence`, and `Learner outcome`.
2. **Active learning** — board grouped by `Status`, filtered to items not
   `Done`.
3. **Evidence backlog** — table filtered to `Evidence` = `Not claimed`,
   grouped by `Workstream`.
4. **Canvas and Copilot** — board filtered to `Workstream` = `Canvas` or
   `Documentation`, grouped by `Status`.

For each day or evidence task, create or link one issue with this structure:

```text
## Learner question
What should a learner be able to explain after completing this item?

## Acceptance evidence
- [ ] Local test or workflow URL
- [ ] Screenshot or trace, where applicable
- [ ] Limitation and mock/live status recorded

## Tutor follow-up
Name the tutor and one challenge question that checks understanding.
```

Use labels such as `day-01`, `day-19`, `day-21`, `canvas`, `copilot`,
`evidence-live`, `evidence-local`, `learner`, and `tutor`. Link merged pull
requests to the issue and move the item to **Done** only when the acceptance
evidence is attached. A Project item marked Done does not by itself change the
generated `PROGRESS.md` status.

### Learner workflow

1. Open the **21-day roadmap** and select the current day from `PROGRESS.md`.
2. Read the linked plan section and the relevant guide/reference.
3. Run the local test or Canvas exercise.
4. Ask the named tutor the issue's challenge question.
5. Attach the test result, screenshot, trace, or workflow URL.
6. Record limitations and move the issue from Todo through In Progress to Done
   once the acceptance evidence is attached. Review is represented by the
   linked pull request and evidence fields because the configured board uses
   GitHub's default three Status options.

### Tutor-agent workflow

Tutors should use the Project as an evidence-aware learning queue, not as an
authority source. They may explain an item, point to the plan and references,
and propose a challenge question. They must not mark an item Done, approve a
portfolio action, or infer live evidence from a Project status. Suggested
prompts are documented in the [Tutor Runbook](TUTOR_RUNBOOK.md).

## Workflow map

| Workflow | Main question | Trigger | Write access |
|---|---|---|---|
| [`ci.yml`](../../.github/workflows/ci.yml) | Does the code lint and test? | Push and pull request to `main` | None |
| [`authorization-tests.yml`](../../.github/workflows/authorization-tests.yml) | Are authorization boundaries and negative cases intact? | Relevant security/control changes | None |
| [`contract-tests.yml`](../../.github/workflows/contract-tests.yml) | Do skills, tools, schemas, and governance contracts agree? | Relevant contract/skill changes | None |
| [`skills-freshness.yml`](../../.github/workflows/skills-freshness.yml) | Are skills still aligned with changed code? | Pull requests to `main` | None |
| [`eval-regression.yml`](../../.github/workflows/eval-regression.yml) | Did agent behavior regress? | Relevant agent/eval changes | None |
| [`progress-tracker.yml`](../../.github/workflows/progress-tracker.yml) | Does generated progress match the repository? | Push to `main` | Commits `PROGRESS.md` |
| [`morning-brief.yml`](../../.github/workflows/morning-brief.yml) | Can a scheduled review produce a human-review artifact? | Weekday schedule or manual dispatch | Creates GitHub issues |
| [`public-data-ingestion.yml`](../../.github/workflows/public-data-ingestion.yml) | Can approved public sources be refreshed into a governed cache? | Weekday schedule or manual dispatch | Uploads a 14-day cache artifact; no repository writes |

### Morning-brief evidence exercise

The scheduled workflow is intentionally approval-only. It generates a
deterministic public/mock HTML artifact, uploads it as a short-lived workflow
artifact, and opens a GitHub issue containing the run URL. It does not approve
an investment action or place a trade.

Run it manually from the repository's **Actions** tab:

1. Open **Morning Portfolio Review**.
2. Choose **Run workflow**, select `main`, and confirm **Run workflow**.
3. Open the completed run and verify the `Upload review artifact` step.
4. Download the artifact and confirm the issue links back to the same run.
5. Add the workflow URL and issue URL to the relevant Project item or evidence
   record. Do not attach private data to the issue.

Equivalent CLI command:

```bash
gh workflow run morning-brief.yml --ref main
gh run list --workflow morning-brief.yml --limit 1
```

The first successful manual run is workflow evidence; scheduled execution is
still account-dependent because GitHub may delay or disable scheduled jobs in
inactive repositories.

## 1. CI

File: [`ci.yml`](../../.github/workflows/ci.yml)

CI is the broad baseline gate. It runs on every push to `main` and every pull
request targeting `main`.

It checks out the repository, installs dependencies with `uv`, runs Ruff, and
runs the complete pytest suite. A failure usually means that a code change has
broken formatting/lint rules or a deterministic test.

This is necessary but not sufficient: CI does not replace the authorization,
contract, freshness, or behavioral-evaluation workflows.

## 2. Authorization Tests

File: [`authorization-tests.yml`](../../.github/workflows/authorization-tests.yml)

This focused gate runs when changes touch `governance/`, role configuration,
the control layer, agents, Cedar validation, or the workflow itself. It:

1. Validates Cedar policy syntax.
2. Runs governance tests.
3. Runs control-layer tests.
4. Runs agent authorization and negative/adversarial tests.

The negative cases are as important as the positive cases. A request that must
be denied, interrupted, or blocked by a guardrail must remain denied after a
change. Prompts, skills, or contracts never grant authority.

## 3. Skill Contracts

File: [`contract-tests.yml`](../../.github/workflows/contract-tests.yml)

This gate runs when skills, contracts, governance, scripts, or the workflow
change. It performs:

- static skill and contract validation;
- mocked skill execution;
- skill negative tests;
- governance negative tests;
- MCP contract tests; and
- analytics contract tests.

Use it when changing an allowed tool, input schema, output shape, skill
frontmatter, or governance-related contract. The implementation and its
contract must change together.

## 4. Skills Freshness

File: [`skills-freshness.yml`](../../.github/workflows/skills-freshness.yml)

This pull-request gate compares the base and head commits and runs
`scripts/check_skills_freshness.py`. It detects when implementation changes may
have made a skill's documented coverage or `last_verified_commit` stale.

When it fails, inspect the changed code and either update the affected skill or
record the repository's explicit `skills-unaffected` decision according to the
project rules. Use the read-only
[`skills-auditor-agent`](../../.github/agents/skills-auditor-agent.agent.md) for
investigation and drafting.

## 5. Evaluation Regression

File: [`eval-regression.yml`](../../.github/workflows/eval-regression.yml)

This gate checks behavioral quality rather than only code correctness. It runs
when agents, observability, roles, evaluation configuration, governance,
evaluation cases, or the runner changes.

- Pull requests run the fast evaluation subset.
- Pushes to `main` and version tags run the full evaluation set.
- Evaluation summaries are uploaded as workflow artifacts.
- The configured baseline is used to detect meaningful score regressions.

The workflow can use `OPENAI_API_KEY` and `LANGSMITH_API_KEY` repository
secrets. Secrets must remain in GitHub's secret store and must never be placed
in source files, logs, fixtures, or documentation.

When this gate fails, start with the failed examples and use the read-only
[`eval-triage-agent`](../../.github/agents/eval-triage-agent.agent.md) to compare
the changed behavior with the baseline.

## 6. Progress Tracker

File: [`progress-tracker.yml`](../../.github/workflows/progress-tracker.yml)

This workflow runs after pushes to `main`. It runs
`scripts/check_progress.py`, which regenerates the machine-checked status table
in `PROGRESS.md` from repository state and `config/progress.yaml`.

If the generated table changes, the workflow commits the update as
`github-actions[bot]` using `[skip ci]`. The daily narrative remains manually
maintained because it contains context, deviations, and evidence links.

Do not hand-edit the generated table. Update the progress configuration or the
implementation evidence that the checker evaluates.

## 7. Morning Portfolio Review

File: [`morning-brief.yml`](../../.github/workflows/morning-brief.yml)

This workflow demonstrates scheduled automation. It can be started manually
or runs on weekdays using the configured cron expression. It generates a
deterministic mock risk-summary artifact and opens a GitHub issue containing:

- the artifact reference;
- the workflow-run link;
- the approval-only disclaimer; and
- the prompt used for the review.

It has `contents: read` and `issues: write` permissions. The issue is a review
request, not an execution approval. No trade execution, investment approval,
or production portfolio access is part of this workflow.

## How a pull request is checked

The workflows are intentionally overlapping but independently scoped:

1. `ci.yml` checks general code quality and tests.
2. `contract-tests.yml` checks schemas and mocked contract behavior when relevant.
3. `authorization-tests.yml` checks policy and security boundaries when relevant.
4. `skills-freshness.yml` checks skill-to-code synchronization on pull requests.
5. `eval-regression.yml` checks agent behavior when relevant.
6. `progress-tracker.yml` refreshes the status table after a merge to `main`.

The relevant path filters prevent every specialized check from running for an
unrelated documentation or analytics change, while the broad CI workflow still
provides a general safety net.

## Local equivalents

Before pushing, run the same classes of checks locally where possible:

```text
uv run ruff check .
uv run pytest
uv run python scripts/check_skill_contracts.py
uv run python scripts/check_cedar_policies.py
uv run python scripts/check_skills_freshness.py --base HEAD~1 --head HEAD
```

For behavioral evaluation, use the commands in [`RUNBOOK.md`](RUNBOOK.md) and
[`experiments/README.md`](../../experiments/README.md). For AWS or hosted-model
work, confirm credentials, budget, scope, evidence capture, and teardown first.

## Troubleshooting order

1. Read the failing job's exact step and download any evaluation artifact.
2. Reproduce the narrowest local equivalent.
3. Check whether the failure is code, contract, authorization, freshness,
   evaluation, credentials, or workflow configuration.
4. Inspect the relevant runbook or tutor.
5. Make the smallest correction and rerun the focused check before the full
   suite.

Workflow success is evidence for the checks that actually ran. It is not proof
of live AWS deployment, licensed-data quality, production readiness, or an
approved investment recommendation.
