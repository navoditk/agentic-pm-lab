# Agentic PM Lab Runbook

This is the operational entry point for the Day 11 local stack and the later
AWS/AgentCore exercises. It is explicit about what is real, what is mock, and
where human approval is required.

## Safety boundary

This repository uses public data and labelled mock holdings/security metadata.
It does not place orders, provide personalized investment advice, or contain
company-sensitive information. `run_backtest` and other high-impact actions
remain approval-gated. A Canvas, prompt, skill, or agent description never
grants authorization; Cedar and the final tool boundary do.

## One-time setup

Read [INSTALL.md](../INSTALL.md) first. Then verify:

```bash
uv sync
uv run pytest
uv run pre-commit run --all-files
```

Set public-data/model credentials only in `.env` or the shell. Never commit
them. Network and cloud access are not permitted in `tests/unit/`; use mocks.

## Start the local stack

The full comparison stack is:

```bash
docker compose up
```

Services:

- API: `http://localhost:8000/docs`
- Artifact host: `http://localhost:8765/`
- MCP server: stdio process for a compatible local MCP client
- Optional Streamlit comparison view: `docker compose --profile ui up`

## Record an experiment

Use the provider-neutral recorder for a quick local, hosted, or AWS-backed run:

```bash
uv run python scripts/experiment.py init \
  --name "local smoke" --provider local --model mock-v1 --run-id smoke-001
```

Record the response, token usage, pricing basis, evidence, and result with
`record`, then close the run with `finalize`. See
[`experiments/README.md`](../experiments/README.md) for the common manifest,
AWS cost fields, comparison rubric, and a complete example. Use
[`AWS_AGENTCORE_SETUP.md`](AWS_AGENTCORE_SETUP.md) for deployment-specific
credentials, packaging, logs, billing snapshots, and teardown.

If Docker is unavailable, start individual services:

```bash
uv run uvicorn src.api.main:app --reload
uv run python scripts/artifacts_host.py
uv run python -m src.mcp_server.server
uv run streamlit run src/ui/app.py
```

Generate the sample report with:

```bash
curl -X POST http://localhost:8765/generate/risk-summary
open http://localhost:8765/files/portfolio-risk-summary.html
```

The report is a single-file HTML artifact and explicitly labels mock holdings
and deterministic fixtures. It complements the Canvas surfaces; it is not a
second trust boundary or a replacement for trace/provenance review.

## Test commands

Fast local checks:

```bash
uv run pytest
uv run pytest governance/tests -q
uv run pytest tests/unit/mcp_server -q
uv run python scripts/check_skill_contracts.py
uv run python scripts/check_skills_freshness.py --base HEAD~1 --head HEAD
uv run ruff check .
```

Canvas checks:

```bash
node .github/extensions/agentic-kanban/test/smoke.test.mjs
node .github/extensions/issue-triage-canvas/test/smoke.test.mjs
node .github/extensions/agent-ops-canvas/test/smoke.test.mjs
node .github/extensions/portfolio-risk-canvas/test/smoke.test.mjs
node .github/extensions/portfolio-risk-canvas/tests/canvas-capabilities.test.mjs
```

The smoke tests bind a loopback server and may require local execution
permission in a restricted sandbox.

## Run a workflow or custom agent standalone

Prompts live in `.github/prompts/` and are invoked as slash commands in a
supported Copilot surface. Start with `/morning-portfolio-review` or
`/investment-committee-brief`. Each output must include sources, dates,
provenance, authorization state, and limitations.

Custom agents:

- `risk-narrator-agent`: narrates approved analytics and refuses unauthorized or order-like requests.
- `pr-reviewer-agent`: read-only review for security, contracts, tests, provenance, and eval impact.
- `skills-auditor-agent`: read-only diagnosis of stale skill documentation.
- `eval-triage-agent`: read-only diagnosis of evaluation regressions.
- `docs-agent`: maintains architecture/glossary alignment.
- `ficc-tutor-agent`: personal learning tutor; not part of runtime authorization.

See [AGENT_RUNBOOK.md](AGENT_RUNBOOK.md) for input examples, negative cases,
expected behavior, and troubleshooting.

## Evaluation and traces

Run a deterministic subset without a paid model call using the unit tests. For
the full hosted evaluation, configure `OPENAI_API_KEY` and
`LANGSMITH_API_KEY`, then use the GitHub `eval-regression.yml` workflow or:

```bash
uv run python scripts/run_eval.py --subset fast --baseline config/eval-baseline.json
```

Do not run a paid full evaluation without explicit approval. Inspect traces in
LangSmith using the experiment URL printed by the runner; local OTel spans are
also emitted by the shared telemetry provider. The Agent Operations Canvas
surfaces seeded history, traces, guardrails, evaluation results, approvals,
and cost metrics.

## Security validation

```bash
uv run pytest governance/tests -q
uv run pytest tests/unit/control tests/unit/mcp_server -q
```

Exercise these paths before accepting a change:

1. `PM_USER` can inspect `PORT_A` but cannot access `PORT_B`.
2. `RISK_USER` can inspect `PORT_B` but cannot invoke pricing/research tools.
3. `ADMIN_USER` can approve the paused backtest; other identities cannot.
4. MCP calls without identity metadata or with an unauthorized portfolio fail.
5. Prompt intent, skill contracts, and Canvas state cannot bypass Cedar.

## GitHub automation

`morning-brief.yml` runs on weekdays and manually. It generates a clearly
labelled mock/public report and opens an issue for human review. It has no
execution capability. Configure the optional `portfolio-review` label if the
repository uses labels; the workflow falls back to creating the issue without
it.

For the Copilot app native automation equivalent, create a weekday scheduled
automation with the same prompt and repository scope, set its output to a new
issue or draft comment, and require approval before any write. Do not grant
order-entry, portfolio-write, or unrestricted network tools. Record the
automation name and first issue URL in `PROGRESS.md`.

## AgentCore deployment preview and evidence boundary

The repository contains the local AgentCore-shaped entrypoint and deployment
intent. A temporary Runtime and endpoint reached `READY` during the
2026-08-13 trial and were then deleted; the controlled request returned HTTP
500, so no successful hosted answer is claimed. Before another deployment:

1. Review AWS account, region, budget alert, IAM, and Bedrock model access.
2. Build/package the same agent entry point; keep deterministic analytics and
   MCP contracts unchanged.
3. Configure AgentCore Runtime, Gateway, Identity, Policy, and OTel export.
4. Confirm deployed traffic reaches tools only through governed Gateway.
5. Run smoke, authorization, guardrail, and evaluation checks; capture trace IDs.

Do not deploy from a dirty worktree, with the account root principal, or with
proprietary data. Record live results in [EVIDENCE.md](EVIDENCE.md), and use
the AWS teardown checklist immediately after the learning exercise:

```bash
# Commands are intentionally placeholders until Day 12 creates the resources.
# Delete AgentCore Runtime/Gateway resources, IAM test roles, logs, and buckets.
# Re-check the AWS console and billing dashboard for leftover resources.
```

## Troubleshooting

- **MCP identity error:** supply identity metadata and, for resource-scoped tools, `portfolio_id`; do not put entitlements in prompt text.
- **Canvas state appears stale:** reload the extension and inspect the domain/session state; durable Canvas state is separate from MCP authorization.
- **LangSmith evaluation refuses to run:** check `LANGSMITH_API_KEY`; do not replace the failure with a fabricated success.
- **Freshness check fails:** update the affected skill and contract/frontmatter, then run `scripts/check_skill_contracts.py`; use a documented `skills-unaffected` review exception only when the change truly does not alter skill behavior.
- **Scheduled issue is missing:** inspect Actions permissions, the workflow run, and the repository `issues: write` setting.

## Teardown

```bash
docker compose down --remove-orphans
```

Remove generated local artifacts only when they are disposable and not needed
as evidence. Stop any local model, close Canvas sessions, revoke temporary
tokens, and complete the AWS teardown checklist after cloud exercises.
