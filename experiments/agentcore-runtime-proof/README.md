# AgentCore Runtime proof experiment

This directory is the smallest repeatable AWS experiment for the lab. It keeps
the deployment fixture separate from the full local application so a new user
can validate identity, packaging, AgentCore Runtime, Bedrock, logs, and cleanup
without deploying the entire repository.

The authoritative runbook is [`docs/AWS_AGENTCORE_SETUP.md`](../../docs/AWS_AGENTCORE_SETUP.md).
Use this directory's `agentcore_app.py`, `requirements.txt`, and `input.json`
when following the direct CodeZip path in that runbook.

The fixture is intentionally read-only. It returns an assessment and explicit
approval boundary; it cannot place orders or call portfolio-management tools.
