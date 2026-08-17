# AgentCore Gateway experiment — 2026-08-17

Status: `implementation_ready_live_preflight_blocked`

## Objective

Prove that a real HTTPS API Gateway target can be exposed through AgentCore
Gateway as selected read-only MCP tools, while preserving IAM authentication,
tool filtering, observable evidence, and teardown.

## Scope

- Regional API Gateway REST API.
- Lambda with deterministic public/mock learning payloads.
- Three read-only GET operations: portfolio risk, market curve, research evidence.
- AgentCore Gateway with `AWS_IAM` authorization and stage-scoped
  `execute-api:Invoke` permission.
- No trades, real holdings, secrets, or company-sensitive data.

## Evidence status

The reusable CloudFormation template, OpenAPI source, runbook, and expected
observations are committed. The live run was not started because the AWS SSO
session had expired and could not refresh non-interactively. No AWS resource
was created by this attempt.

## Lessons captured before live execution

1. AgentCore Gateway's API Gateway target uses the REST API ID and stage plus
   tool filters; it is distinct from the MCP-server endpoint target shape.
2. The target's `READY` state is not sufficient evidence of successful calls;
   the Gateway role also needs SigV4 `execute-api:Invoke` on the exact stage.
3. API Gateway operation IDs and descriptions become the learner's MCP tool
   surface, so they are part of the contract and should be reviewed.
4. Authentication, tool authorization, and portfolio entitlement are separate
   controls and should be evidenced independently.
5. The experiment must remain disposable and capture cleanup before completion.

## Next step

After renewing the IAM Identity Center session, follow
[`AGENTCORE_GATEWAY_SETUP.md`](../../docs/guides/AGENTCORE_GATEWAY_SETUP.md).
