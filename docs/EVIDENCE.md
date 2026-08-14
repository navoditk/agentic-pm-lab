# Evidence ledger

This ledger separates repository-local proof from live integration evidence.
Passing local tests do not imply that an AWS resource, hosted model, provider,
or browser session was exercised.

| Area | Local proof | Live evidence | Current state |
|---|---|---|---|
| Institutional PM capstone | `src/capstone/workflow.py`, focused tests, replay artifact script | AgentCore infrastructure deployment and teardown; request execution failed | Local complete; live deployment evidence captured, live answer unclaimed |
| OpenTelemetry and evaluation | Local exporters, golden dataset, deterministic evaluators, Day 6/7 records | No new hosted run in this session | Local complete; hosted rerun requires credentials |
| LangSmith / paid model | Runner and contracts exist | `OPENAI_API_KEY` and `LANGSMITH_API_KEY` are unset | Blocked pending credentials and explicit spend approval |
| AgentCore Runtime/Gateway | Deployment intent, entrypoint, ADRs, local boundary | Runtime and endpoint reached `READY`; invocation failed; no Gateway | Deployment proof captured; request execution remains blocked; see [`AWS_AGENTCORE_SETUP.md`](AWS_AGENTCORE_SETUP.md) |
| AWS observability | Local OTel path and CloudWatch target documented | AgentCore namespace currently has no metrics; control-plane listing is denied | Unclaimed |
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
