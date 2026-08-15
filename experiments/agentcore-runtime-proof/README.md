# AgentCore Runtime proof experiment

This directory is the smallest repeatable AWS experiment for the lab. It keeps
the deployment fixture separate from the full local application so a new user
can validate identity, packaging, AgentCore Runtime, Bedrock, logs, and cleanup
without deploying the entire repository.

The authoritative runbook is [`docs/guides/AWS_AGENTCORE_SETUP.md`](../../docs/guides/AWS_AGENTCORE_SETUP.md).
Use this directory's `agentcore_app.py`, `requirements.txt`, and `input.json`
when following the direct CodeZip path in that runbook.

The fixture is intentionally read-only. It returns an assessment and explicit
approval boundary; it cannot place orders or call portfolio-management tools.

## Evaluation fixture

`evaluation_input.example.json` is a public, synthetic OpenTelemetry fixture
for the AgentCore on-demand `Builtin.Helpfulness` evaluator. It includes the
Strands-supported `invoke_agent` span, its correlated event, and a trace-level
reference input. The latest run produced `0.17` (`Very Unhelpful`) on
2026-08-14 UTC; an earlier identical-shape run produced `0.33`, demonstrating
normal LLM-judge variation. It is kept separate from the runtime package because a minimal runtime that only
emits application logs does not automatically produce evaluation-compatible
spans.
