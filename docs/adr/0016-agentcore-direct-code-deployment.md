# ADR 0016: AgentCore direct-code deployment

## Status

Accepted for Day 12 learning deployment.

## Decision

Use the Bedrock AgentCore Runtime direct-code Python deployment path for the
Portfolio Manager. Keep the application entrypoint in
`src/runtime/agentcore_app.py` and retain Docker only for the local comparison
stack.

## Rationale

The project is pure Python and has no system dependency requiring a custom
image. Direct code reduces moving parts for the learning milestone and keeps
attention on Runtime, Gateway, Identity, Policy, Guardrails, and OTel. It does
not imply that containers are unsuitable for a later institutional service.

## Consequences

The deployment must validate packaged Python dependencies and supported runtime
versions. A future container path should be a separate experiment, not mixed
into the direct-code evidence.
