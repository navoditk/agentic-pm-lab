# Evidence ledger

This ledger separates repository-local proof from live integration evidence.
Passing local tests do not imply that an AWS resource, hosted model, provider,
or browser session was exercised.

| Area | Local proof | Live evidence | Current state |
|---|---|---|---|
| Institutional PM capstone | `src/capstone/workflow.py`, focused tests, replay artifact script | Full deterministic capstone executed inside temporary AgentCore Runtime; CloudWatch stages/metrics, token usage, cost snapshot, and teardown | Local and full hosted proof captured |
| Hosted model comparison | Same-input Claude Haiku and Meta Llama 3.3 70B AgentCore runs | [Exact-input Llama comparison](../../experiments/runs/agentcore-llama33-exact-20260816-223000/) and Claude baseline | Llama comparison complete; single-run quality/cost conclusions intentionally not generalized |
| OpenTelemetry and evaluation | Local exporters, golden dataset, deterministic evaluators, Day 6/7 records | Scored AgentCore on-demand fixture; hosted-runtime span collection not claimed | Local and on-demand evaluation proof complete; hosted rerun requires instrumentation and credentials |
| LangSmith / paid model | Runner and contracts exist | `OPENAI_API_KEY` and `LANGSMITH_API_KEY` are unset | Blocked pending credentials and explicit spend approval |
| AgentCore Runtime/Gateway | Deployment intent, entrypoint, ADRs, local boundary | Runtime and endpoint reached `READY`; successful read-only invocation and teardown; no Gateway | Runtime live-complete; Gateway remains unclaimed; see [`AWS_AGENTCORE_SETUP.md`](../guides/AWS_AGENTCORE_SETUP.md) |
| AWS observability | Local OTel path and CloudWatch target documented | Successful runtime CloudWatch events plus AgentCore namespace metrics captured; ADOT/hosted OTel span collection remains unclaimed | Runtime logs and metrics live-complete; hosted OTel span export remains optional |
| Managed Bedrock Guardrail attachment | Local/standalone Guardrail cases and runtime configuration path | Temporary Guardrail was passed into hosted `Converse`; blocked message and zero-token intervention were observed, while neutral review prompts exposed a false positive | Attachment path proven; policy/prompt refinement required before claiming an allowed managed attachment |
| Public providers | Fixture adapters and provenance contracts for Treasury, SOFR, SEC, research | [Live ALFRED/Treasury/SEC capture](../../experiments/runs/2026-08-16-live-public-data-004/) | ALFRED, Treasury daily yield curve, and SEC EDGAR live-complete for bounded capture; auctions/TRACE/N-PORT/research remain unclaimed |
| GitHub Projects learning board | Project schema, linked repository, 21 roadmap items, two morning-review issues | [Project views overview](screenshots/github-project/github-project-views-overview.png); [corrected roadmap screenshot](screenshots/github-project/github-project-21-day-roadmap.png) | Views created, roadmap filter corrected and saved, and browser evidence captured |
| Scheduled morning brief | `.github/workflows/morning-brief.yml` and deterministic artifact generator | [Workflow run 31865364150](https://github.com/navoditk/agentic-pm-lab/actions/runs/31865364150); [review issue #3](https://github.com/navoditk/agentic-pm-lab/issues/3); uploaded `morning-portfolio-review-31865364150` artifact | Manual dispatch, artifact upload, and approval-only issue creation verified |
| Native Copilot lifecycle | Prompts, custom agents, PR-review and skills-auditor configuration; local contract/freshness checks | No Copilot CLI/coding-agent run in the current authenticated session | Repository path complete; live Copilot evidence blocked by expired GitHub CLI auth |
| Copilot Canvas | Capability tests and loopback smoke tests | No screenshot or interactive browser evidence; browser connector unavailable on 2026-08-16 | Local complete; hosted visual capture unclaimed |

## Hosted AgentCore full-capstone comparison — 2026-08-16 UTC

The full comparison [`agentcore-full-capstone-20260816-204917`](../../experiments/runs/agentcore-full-capstone-20260816-204917/)
executed the complete deterministic institutional PM workflow inside a
temporary ARM64 AgentCore Runtime. The hosted model was limited to a bounded
committee-review summary after the deterministic workflow completed.

The run produced 1,319 input tokens, 300 output tokens, and 1,619 total
tokens. It recorded eight application stages, 11 runtime log events, one
invocation/session, 7,513 ms duration/latency, and zero errors or throttles.
The committee remained challenged and pending human review; no order was
generated or executed. Private model chain-of-thought was not captured. The
trace exposes stages, policy outcomes, evidence, assumptions, findings,
evaluation dimensions, and outputs.

Cost Explorer returned an estimated `$0.034946236` for the UTC account day;
this is not request-attributed. The budget snapshot was `$0.417` actual and
`$0.839` forecast against a `$50` monthly budget. Runtime, endpoint, package
prefix, and log groups were deleted after evidence capture.

See the [full hosted response](../../experiments/runs/agentcore-full-capstone-20260816-204917/hosted-full-response.json),
[CloudWatch events](../../experiments/runs/agentcore-full-capstone-20260816-204917/events-default.json),
[AgentCore metrics](../../experiments/runs/agentcore-full-capstone-20260816-204917/metrics.json),
and [experiment findings](../../experiments/runs/agentcore-full-capstone-20260816-204917/findings.md).

The earlier bounded counterpart remains useful as a smaller hosted proof:
[`agentcore-capstone-20260816-200245`](../../experiments/runs/agentcore-capstone-20260816-200245/).

## Hosted model comparison — 2026-08-16 UTC

The exact-input comparison [`agentcore-llama33-exact-20260816-223000`](../../experiments/runs/agentcore-llama33-exact-20260816-223000/)
ran the same capstone request with Claude Haiku 4.5 and Meta Llama 3.3 70B.
Claude used 1,619 total tokens and 7,513 ms; Llama used 875 total tokens and
5,915 ms. Both runs completed with zero runtime errors/throttles,
`approval_required=true`, and `order_execution=false`. Llama required the
cross-region inference profile `us.meta.llama3-3-70b-instruct-v1:0` because
direct on-demand invocation is unsupported for this model in the lab region.
The Cost Explorer amount remains account/day scoped, so no model-specific cost
claim is made.

## Managed Guardrail attachment probe — 2026-08-16 UTC

The temporary run [`agentcore-managed-guardrail-20260816-215000`](../../experiments/runs/agentcore-managed-guardrail-20260816-215000/)
passed a managed Bedrock Guardrail through `guardrailConfig` in the hosted
model call. The configured blocked message was returned with zero model
tokens, confirming the attachment and intervention path. The same Guardrail
also blocked a neutral portfolio-review prompt because serialized governance
and review vocabulary produced a false positive. This run therefore proves
the attachment path, but not a production-ready allowed case. The standalone
`ApplyGuardrail` proof remains the allowed-versus-blocked reference. The
temporary Guardrail, runtimes, package prefixes, and log groups were deleted.

## Hosted AgentCore counterpart comparison — 2026-08-16 UTC (superseded scope)

The bounded run [`agentcore-capstone-20260816-200245`](../../experiments/runs/agentcore-capstone-20260816-200245/)
successfully exercised the temporary AgentCore Runtime and hosted Claude Haiku
model. It captured 499 model tokens, all seven runtime workflow stages,
approval-required/order-execution safety fields, an estimated `$0.008064516`
same-day Cost Explorer amount, and a `$0.417` actual / `$0.839` forecast budget
snapshot. The runtime, endpoint, and S3 package prefix were deleted.

This is hosted counterpart evidence, not yet a full hosted reproduction of the
Day 20 deterministic capstone: the local replay runs the full research,
fixed-income, Devil's Advocate, committee, evaluation, and audit workflow,
while the deployed proof application is the smaller read-only AgentCore slice.
The full-capstone follow-up above supersedes this as the authoritative hosted
comparison. This smaller run remains retained to show the incremental path
from a minimal AgentCore proof to the complete hosted workflow.

The same run validated the `AWS/Bedrock-AgentCore` namespace: one
invocation/session, 6,109 ms duration/latency, and zero errors, user errors,
system errors, or throttles. The runtime emitted application log events, but
an ADOT/OTel span export to a hosted tracing backend was not configured.

## Live public-data capture — 2026-08-16 UTC

The bounded experiment [`2026-08-16-live-public-data-004`](../../experiments/runs/2026-08-16-live-public-data-004/)
verified these public endpoints with normalized, provenance-preserving output:

| Provider | Live result | Scope | Cost |
|---|---|---|---:|
| ALFRED public graph CSV | Success | DGS10, 250 observations, explicit vintage `2024-01-02` | $0.00 |
| U.S. Treasury daily yield-curve XML | Success | 2,340 tenor records through `2026-08-14` | $0.00 |
| SEC EDGAR submissions | Success | 1,000 filing metadata records for CIK `0000320193` | $0.00 |
| SEC Company Facts | Success | 25,135 normalized XBRL records, including 699 revenue-related USD records | $0.00 |

The existing Treasury auctions URL returned HTTP 404 during the same work and
is not claimed as live evidence. The official daily yield-curve feed was used
for the Treasury capture instead. Raw provider payloads and credentials were
not committed. The run used zero model tokens, no AWS resources, and no paid
provider service.

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

## Direct Anthropic institutional PM capstone — 2026-08-16 UTC

- The governed institutional PM capstone completed through Anthropic's direct
  Messages API with model `claude-haiku-4-5-20251001`.
- Native usage was 613 input tokens, 300 output tokens, and 913 total tokens;
  measured latency was 3,706 ms. The token estimate was `$0.002113` using the
  run's recorded $1.00/M input and $5.00/M output rates. No AWS resources were
  provisioned.
- Observable stages and audit evidence were retained. The response explicitly
  kept `approval_required: true` and `order_execution: false`; private model
  chain-of-thought was not captured.
- Artifacts: [`run manifest`](../../experiments/runs/anthropic-direct-capstone-20260816-230000/manifest.json),
  [`response`](../../experiments/runs/anthropic-direct-capstone-20260816-230000/response.json),
  [`audit log`](../../experiments/runs/anthropic-direct-capstone-20260816-230000/audit.jsonl),
  and [`findings`](../../experiments/runs/anthropic-direct-capstone-20260816-230000/findings.md).

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
- The gap was then closed for the on-demand API using the documented Strands
  OpenTelemetry span-and-event shape in
  `experiments/agentcore-runtime-proof/evaluation_input.example.json`.
- On-demand `Builtin.Helpfulness` returned one scored result on the final
  redacted fixture: value `0.17`, label `Very Unhelpful`, with 988 evaluator
  tokens. A preceding identical-shape run returned `0.33`/`Somewhat Unhelpful`;
  this variation is a useful reminder that LLM-judge scores should be treated
  as experimental measurements, not deterministic unit-test assertions. Both
  explanations correctly identified that the synthetic response did not
  actually summarize portfolio risks. This is a valid evaluator proof, not a
  production quality claim.

## Canvas validation — 2026-08-14 UTC

- The Agent Operations Canvas loopback smoke test passed all six checks, and the
  capability test passed. This validates the local runtime and action handlers;
  no Copilot-hosted browser session or screenshot is claimed.

## Copilot and Canvas evidence attempt — 2026-08-16 UTC

- The local Portfolio Risk and Agent Operations Canvas capability and smoke
  tests remain passing.
- The browser connector returned no available browser session, so no hosted
  Copilot Canvas interaction or screenshot was claimed.
- `gh auth status` reported that the `navoditk` GitHub CLI token is invalid.
  The installed CLI does not accept the historical `--use-device-code` flag;
  interactive re-authentication requires a browser session outside this
  terminal. No native Copilot CLI or coding-agent run is claimed.

## Gateway status — 2026-08-14 UTC

- `list-gateways` returned no Gateway resources. No Gateway was created because
  the experiment does not yet have a user-supplied HTTPS MCP target and
  authentication/credential-provider configuration. Creating a placeholder
  target would not be a meaningful or safe end-to-end test.

## Gateway target implementation — 2026-08-17 UTC

- Added a disposable CloudFormation-backed regional API Gateway target with
  three read-only public/mock-data operations and a complete AgentCore Gateway
  setup runbook: [`AGENTCORE_GATEWAY_SETUP.md`](../guides/AGENTCORE_GATEWAY_SETUP.md).
- The first live preflight reported AWS CLI `2.36.22`, but the
  `agentic-pm-lab` IAM Identity Center session had expired and refresh failed.
  No Gateway, target, API, Lambda, or IAM resource was created by this attempt.
- The exercise remains `live_preflight_blocked_by_iam_permissions`: after SSO
  renewal, CloudFormation reported missing `apigateway:POST`; the first design
  also exposed missing IAM cleanup permissions. No API Gateway or AgentCore
  Gateway resource was created. See the [`deployment attempts`](../../experiments/2026-08-17-agentcore-gateway/deployment-attempts.json).

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
