# Agent Runbook: Standalone Custom Agents and Skills

This runbook shows how to exercise the repository's custom agents and skills
without running the full AWS or Canvas stack. It is a learning and validation
guide, not a production operating procedure. The full system runbook remains
planned for Day 11 in docs/PLAN.md.

## 1. Choose the right abstraction

| Abstraction | Use it for | Examples |
|---|---|---|
| Skill | Reusable background knowledge or a bounded workflow | portfolio-risk-summary, scenario-analysis, ficc-glossary-maintainer |
| Custom agent | A deliberately selected persona with a narrow job | docs-agent, eval-triage-agent, personal ficc-tutor-agent |
| Prompt file | A repeatable task with a fixed input/output shape | Planned Day 11 review and attribution prompts |
| Canvas capability | A stateful visual interaction shared by UI and agent | Kanban, issue triage, agent operations |

Custom agents are not authorization boundaries. Any capability that reaches
portfolio data must use the governed Tool/MCP path and propagate identity.

## 2. Local prerequisites

From the repository root:

    uv sync
    UV_CACHE_DIR=/tmp/agentic-pm-lab-uv-cache uv run pytest -q tests governance skills

For one skill:

    uv run python scripts/validate_skill.py skills/portfolio-risk-summary
    uv run pytest skills/portfolio-risk-summary/tests -q

These tests are deterministic and do not call a live model, cloud service, or
network endpoint.

## 3. docs-agent

Use this agent when a code or policy change affects the current architecture or
FICC vocabulary.

    Review changes to src/analytics/risk.py and src/control/authorization.py.
    Update docs/ARCHITECTURE.md only if the current-state data flow or security
    boundary changed. If a new fixed-income term was introduced, update
    docs/ficc-glossary.md using the glossary-maintainer format. Report files
    changed and unresolved mismatches.

Expected behavior: inspect implementation before editing, keep architecture
claims factual, preserve security boundaries, and report when no change is
justified.

## 4. eval-triage-agent

Use this read-only agent after .github/workflows/eval-regression.yml fails.

    Investigate the attached evaluation regression. Compare baseline and
    candidate per dimension, identify changed case IDs, inspect traces and the
    source diff, and return the smallest confirming test. Do not edit code,
    evals, workflows, or config/eval-baseline.json.

Expected output: a baseline/current/delta table, regressed case IDs and
evidence, classification as product regression, evaluator drift, dataset drift,
infrastructure failure, or model nondeterminism, and one confirming test.

## 5. Personal ficc-tutor-agent

The FICC tutor is deliberately a personal-scope learning agent, not part of the
runtime system. A reference template is in
docs/agent-templates/ficc-tutor-agent.agent.md. Copy it to the user-scope agent
directory supported by the selected Copilot surface, then reload the session.

Example requests:

    Explain key rate duration as if I understand bond pricing but not curve
    risk. Use the repo glossary, give one toy numerical example, and point to
    the analytics or test that makes the concept concrete.

    I saw negative convexity in the MBS scenario question. Explain it, contrast
    it with ordinary bond convexity, state the data required for an MBS impact,
    and identify which parts of this repo remain mocked.

    Quiz me on duration, spread duration, OAS, convexity, and drawdown. Ask one
    question at a time and reveal the solution only after I try.

The tutor should cite the glossary or a public source, expand acronyms, label
mock data, avoid investment recommendations, and suggest a relevant tool/test.

## 6. Skills as standalone exercises

    uv run python scripts/validate_skill.py skills/portfolio-risk-summary
    uv run pytest skills/portfolio-risk-summary/tests -q

Use this test prompt with a local Deep Agent or scripted fake model:

    Using only the supplied positions, security master, returns, and portfolio
    values, produce a concise risk summary. Call exposure, volatility, and
    drawdown tools. State the volatility window and annualization, label mock
    classifications, and do not recommend a trade.

For scenario-analysis, expected Day 5 behavior is a normalized request with
missing inputs and unavailable execution status. It must not invent a stress
result before the Day 12 deterministic engine exists.

## 7. Troubleshooting

| Symptom | Likely cause | Check |
|---|---|---|
| Agent unavailable | Personal-scope agent is not installed in this client | Confirm the client-specific agent directory and reload |
| Skill ignored | Invalid frontmatter or contract mismatch | Run validate_skill.py and inspect covers |
| Unsupported numeric answer | Model narrated without a tool result | Inspect the trace and add a golden case |
| Unauthorized portfolio appears | Resource check happened only before construction | Test direct tools and enforce the governed boundary |
| Final-answer eval fails | Missing facts, weak criteria, or nondeterminism | Inspect the case and trace; do not lower the baseline first |

## 8. Evidence to record

Record agent/skill name, model, prompt, inputs, tool calls, output, test
command, trace or screenshot, data provenance, and limitations. Keep real
credentials and private data out of transcripts.
