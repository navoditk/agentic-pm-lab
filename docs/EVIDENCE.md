# Evidence ledger

This ledger separates repository-local proof from live integration evidence.
Passing local tests do not imply that an AWS resource, hosted model, provider,
or browser session was exercised.

| Area | Local proof | Live evidence | Current state |
|---|---|---|---|
| Institutional PM capstone | `src/capstone/workflow.py`, focused tests, replay artifact script | Successful AgentCore runtime invocation, CloudWatch stages, token usage, and teardown | Local and live proof captured |
| OpenTelemetry and evaluation | Local exporters, golden dataset, deterministic evaluators, Day 6/7 records | No new hosted run in this session | Local complete; hosted rerun requires credentials |
| LangSmith / paid model | Runner and contracts exist | `OPENAI_API_KEY` and `LANGSMITH_API_KEY` are unset | Blocked pending credentials and explicit spend approval |
| AgentCore Runtime/Gateway | Deployment intent, entrypoint, ADRs, local boundary | Runtime and endpoint reached `READY`; successful read-only invocation and teardown; no Gateway | Runtime live-complete; Gateway remains unclaimed; see [`AWS_AGENTCORE_SETUP.md`](AWS_AGENTCORE_SETUP.md) |
| AWS observability | Local OTel path and CloudWatch target documented | Successful runtime CloudWatch trace captured; AgentCore namespace metrics remain unclaimed | Partial live proof |
| Public providers | Fixture adapters and provenance contracts for Treasury, SOFR, SEC, research | No new live provider capture | Unclaimed; must preserve terms and point-in-time metadata |
| Copilot Canvas | Capability tests and loopback smoke tests | No screenshot or interactive browser evidence | Local complete; visual capture unclaimed |

## AWS identity setup — 2026-08-13

- AWS Organization `o-1q9a561nov` was created with all features enabled.
- IAM Identity Center organization instance is active in `us-west-2` and
  replicated to `us-east-1`.
- User `navodit.kaushik` was assigned the one-hour
  `AgenticPMLabDeveloper` permission set for account `463802498849`.
- Runtime and Gateway execution roles were created with separate trust and
  minimal inline policies; `iam:PassRole` is limited to those two role ARNs.
- Named CLI profile `agentic-pm-lab` authenticated as an
  `AWSReservedSSO_AgenticPMLabDeveloper_*` role.
- `bedrock-agentcore-control:ListAgentRuntimes` succeeded after the permission
  set was refreshed and returned zero current runtimes. The later temporary
  runtime/endpoint trial is recorded below and was fully torn down.

## AgentCore deployment experiment — 2026-08-13

- Named SSO identity and `agentcore` CLI `0.26.0` are usable.
- The local entrypoint imports successfully as `BedrockAgentCoreApp`.
- Bedrock model metadata is available in `us-west-2`.
- Runtime `agentic_pm_lab_20260813-aAl0i15vuk` and endpoint `default` reached
  `READY`, then were deleted after the run.
- Version 1 CloudWatch evidence captured a macOS-native `pydantic_core` import
  failure; a Linux ARM64 rebuild was deployed as version 3.
- The bounded version-3 invocation returned AgentCore HTTP 500 without a new
  delayed CloudWatch traceback. No successful answer, trace, or model output is
  claimed.
- Budget `agentic-pm-lab-monthly` is `$50`; final observed actual `$0.179`,
  forecast `$0.464`; same-day Cost Explorer estimate was `$0.00`.
- Temporary runtime, endpoints, S3 package bucket, and empty log groups were
  removed. Organization, Identity Center, roles, and budget remain.

## AgentCore retry — 2026-08-14 UTC

- A fresh Linux ARM64 CodeZip was built and verified with
  `pydantic_core/_pydantic_core.cpython-313-aarch64-linux-gnu.so`.
- Runtime `agentic_pm_agentcore_proof_20260813_175047-f6d71VAxMz` and endpoint
  `default` both reached `READY` in `us-west-2`.
- The invocation reached request receipt, input validation, authorization
  (`read_only_research: allow`), orchestration start, and execution-role
  credential discovery. CloudWatch then recorded:
  `ResourceNotFoundException: Model use case details have not been submitted
  for this account` from the Bedrock `Converse` call.
- This is the definitive cause of the HTTP 500 for this retry. It requires an
  account administrator to complete Anthropic's Bedrock model use-case form,
  followed by the documented propagation wait, before rerunning the request.
- The temporary runtime, endpoint, and S3 object were deleted. The current SSO
  role lacks `logs:DeleteLogGroup`, so two empty AgentCore log groups remain
  for administrator cleanup. The role also lacks `bedrock:ListGuardrails`,
  preventing an independent live Guardrails proof in this session.

## AgentCore retry after Anthropic form submission — 2026-08-14 UTC

- A second temporary runtime `agentic_pm_agentcore_proof_20260814_182136-vKN7Z4CbKT`
  and endpoint both reached `READY`.
- The first invocation and a retry roughly one minute later both returned HTTP
  500. The delayed CloudWatch trace again states:
  `Model use case details have not been submitted for this account` and advises
  retrying after 15 minutes.
- Runtime, endpoint, and S3 artifact were deleted and the runtime listing is
  empty. The Anthropic form still needs account/region verification, and the
  full AWS-recommended 15-minute propagation window must be allowed before a
  conclusive retry.

## AgentCore retry after Anthropic access — 2026-08-14 UTC

- The final retry runtime and endpoint reached `READY`.
- CloudWatch confirmed Anthropic access had progressed past the use-case-form
  error. The remaining error was an AWS Marketplace authorization failure on
  the runtime execution role: `aws-marketplace:ViewSubscriptions` and
  `aws-marketplace:Subscribe` were required to complete model access.
- The runtime, endpoint, and S3 artifact were deleted; the runtime listing is
  empty. The next retry requires the runtime role policy update and a short
  subscription-propagation wait.

## Successful AgentCore end-to-end run — 2026-08-14 UTC

- Runtime `agentic_pm_agentcore_proof_20260814_185208-QU9geM6P3S` and endpoint
  `default` reached `READY` in `us-west-2`.
- The read-only Portfolio A request completed successfully using Anthropic
  Claude Haiku through the cross-region inference profile.
- Returned stages: `request_received`, `input_validated`,
  `authorization_checked`, `orchestration_started`, `bedrock_completed`,
  `guardrail_checked`, and `response_emitted`.
- Usage: 199 input tokens, 300 output tokens, 499 total tokens. The response
  included `approval_required: true` and `order_execution: false`.
- The temporary runtime, endpoint, and S3 package were deleted; the runtime
  listing is empty. Budget snapshot: `$0.179` actual, `$0.449` forecast, `$50`
  monthly limit. The response and final runtime metadata were retained in the
  local temporary evidence directory for this session.

## Bedrock Guardrails proof — 2026-08-14 UTC

- Created a temporary topic-policy Guardrail in `us-west-2` with a denied
  `TradeExecution` topic.
- A normal read-only portfolio question returned `action=NONE`.
- `Buy 100 shares now.` returned `action=GUARDRAIL_INTERVENED`, with the
  detected topic marked `BLOCKED` and the configured blocked-input message.
- The Guardrail was deleted and `ListGuardrails` confirmed no resource remains.
- This validates the standalone `ApplyGuardrail` path. The successful
  AgentCore runtime proof used the local `guardrail_checked` workflow stage,
  not a managed Guardrail attachment.

## AgentCore Memory proof — 2026-08-14 UTC

- Created temporary Memory `agentic_pm_optional_memory_194451-lPwSTeHdng` with
  a seven-day event expiry and waited for `ACTIVE`.
- Wrote one synthetic preference in namespace `user/PM_USER` and retrieved it
  semantically with score `0.604`.
- Deleted the Memory resource and verified `ListMemories` returned empty.

## AgentCore Evaluation proof — 2026-08-14 UTC

- Started batch evaluation
  `agentic_pm_optional_eval_205228-562067e7db` using built-in
  `Builtin.Helpfulness` against the successful runtime log group.
- The job reached `COMPLETED` and was deleted. It reported zero sessions
  because the minimal fixture emits application workflow logs but does not yet
  emit the ADOT/OTel trace attributes required for AgentCore session
  extraction. This proves the AWS Evaluation control path and records the
  instrumentation gap; it is not a quality score.

## AWS preflight — 2026-08-13

- AWS CLI: `2.36.22`.
- Configured CLI region: `us-west-1`.
- Bedrock model metadata was readable in `us-west-1`; active model access was
  visible, but this did not invoke a model.
- `bedrock-agentcore-control:ListAgentRuntimes` was denied for the active
  identity.
- The active identity resolved to the account root principal. No resource
  creation is authorized from this state; the next AWS step requires a
  named, least-privilege role or profile.
- `config/agentcore.yaml` currently targets `us-west-2`; this remains an
  explicit deployment target until region and role selection are confirmed.

## Completion rule

An item moves to live-complete only when the evidence includes the relevant
trace, report, screenshot, provider response, or teardown confirmation. Until
then, keep the local implementation and the live claim separate.
