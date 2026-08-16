# Findings: hosted AgentCore counterpart comparison

Run ID: `agentcore-capstone-20260816-200245`

## Question

Can the bounded institutional PM read-only request run through a temporary
AgentCore Runtime with hosted model usage, safety fields, CloudWatch workflow
events, and AWS cost evidence, while the local full capstone remains the
reference implementation?

## Result

The hosted AgentCore counterpart succeeded:

- Runtime and `default` endpoint reached `READY`.
- Claude Haiku 4.5 returned a response with 199 input tokens, 300 output
  tokens, and 499 total tokens.
- The response included `approval_required=true` and `order_execution=false`.
- CloudWatch contained all seven runtime stages:
  `request_received`, `input_validated`, `authorization_checked`,
  `orchestration_started`, `bedrock_completed`, `guardrail_checked`, and
  `response_emitted`.
- Cost Explorer reported an estimated `$0.008064516` for the UTC day. The
  account budget snapshot was `$0.417` actual and `$0.839` forecast against a
  `$50` monthly budget.
- Temporary runtime, endpoint, and S3 package prefix were deleted.

AgentCore namespace metrics were also present: one invocation and one session,
6,109 ms duration/latency, and zero errors, user errors, system errors, or
throttles.

## Local versus hosted interpretation

The local reference replay completed the full deterministic Day 20 workflow:
authentication, freshness, research evidence, fixed-income scenarios, Devil's
Advocate challenge, committee artifact, evaluation, and audit. The hosted
runtime used in this run is the smaller reusable AgentCore proof application;
it validates the hosted request, model, approval boundary, and observable
runtime stages but does not execute every local capstone stage.

Therefore this run proves hosted integration and operational evidence, but it
does not yet claim a full hosted reproduction of the Day 20 capstone. The
remaining implementation is to package the capstone workflow behind the
AgentCore entrypoint and repeat the same comparison without weakening the
authorization, provenance, evaluation, or human-review boundaries.

## Observability limitation resolved

The initial unsuffixed log-group query returned `ResourceNotFoundException`.
AgentCore creates endpoint-suffixed groups. The `-default` group contained the
runtime events; the `-DEFAULT` group contained streams without events. The
correct group and complete event transcript are retained in
[`events-default.json`](events-default.json).

## Evidence

- [Hosted response](hosted-response.json)
- [Local full replay](local-response.json)
- [Runtime metadata](runtime.json)
- [CloudWatch events](events-default.json)
- [Budget snapshot](budget.json)
- [Cost Explorer estimate](cost.json)
- [AgentCore metrics](metrics.json)

The two endpoint-suffixed CloudWatch log groups were deleted after the event
transcripts were saved locally.
