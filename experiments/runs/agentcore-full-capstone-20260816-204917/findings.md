# Findings: full hosted AgentCore institutional PM capstone

Run ID: `agentcore-full-capstone-20260816-204917`

## Question

Can the complete deterministic institutional PM capstone run inside a
temporary AWS Bedrock AgentCore Runtime, use a hosted model only for bounded
summarization, preserve the local governance boundaries, and produce enough
evidence to compare local and hosted execution?

## Result

Yes. The full hosted comparison succeeded.

- A temporary ARM64 AgentCore Runtime and `default` endpoint reached `READY`.
- The runtime executed authentication, Cedar authorization delegation,
  point-in-time freshness, macro/quant/fundamental research evidence,
  deterministic fixed-income calculations, Devil's Advocate challenge,
  committee artifact generation, human-review gating, evaluation metadata, and
  audit output before calling the hosted model.
- Claude Haiku returned a bounded committee-review summary with 1,319 input
  tokens, 300 output tokens, and 1,619 total tokens.
- The structured result preserved `approval_required=true` and
  `order_execution=false`; no order was generated or sent.
- The capstone evaluation passed, while the committee remained challenged and
  pending human review because of unsupported causality, concentration, and
  liquidity findings.
- CloudWatch retained the eight application workflow stages plus runtime
  completion events. AgentCore metrics recorded one invocation/session,
  7,513 ms duration/latency, and zero errors or throttles.

## Local versus hosted interpretation

The local replay and hosted result agree on the decision boundary and the
deterministic evidence. The hosted model provides a bounded natural-language
summary; it does not replace the deterministic calculations, authorization,
provenance, evaluation, Devil's Advocate, or human-review controls.

Private model chain-of-thought is not captured. The retained reasoning
artifact is the structured execution trace: stages, tool/policy outcomes,
evidence, assumptions, findings, evaluation dimensions, token usage, and final
approval state.

## Cost and cleanup

Cost Explorer returned an estimated `$0.034946236` for the UTC account day.
This is an account/day estimate rather than a request-attributed charge. The
budget snapshot was `$0.417` actual and `$0.839` forecast against the `$50`
monthly budget. Token pricing was not inferred from the account bill.

The temporary runtime, endpoint, package prefix, and endpoint-suffixed log
groups were deleted after evidence capture. The repository retains the raw
JSON evidence for reproducibility and review.

## Evidence

- [Hosted full response](hosted-full-response.json)
- [Local reference replay](local-response.json)
- [CloudWatch workflow events](events-default.json)
- [AgentCore metrics](metrics.json)
- [Runtime metadata](runtime.json)
- [Budget snapshot](budget.json)
- [Cost Explorer estimate](cost.json)
