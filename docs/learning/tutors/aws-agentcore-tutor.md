# AWS Bedrock AgentCore — deep dive

*Companion to [`agents/aws-agentcore-tutor.md`](../../../agents/aws-agentcore-tutor.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz aws-agentcore-tutor`.*

## What this actually is

Amazon Bedrock AgentCore is AWS's managed platform for running agentic
applications in production: a Runtime that hosts your agent code, a Gateway
that fronts your tools with a governed MCP boundary, an Identity service for
delegated credentials, a Policy service for authorization, Guardrails for
content safety, and Observability wired into CloudWatch. The general idea
AgentCore is solving is one every serious agent deployment eventually hits:
your agent's *reasoning* can live in a Python process, but the moment it
touches real data or real actions, you need the same authentication,
authorization, content-safety, and audit machinery a normal production service
needs — AgentCore is AWS's opinionated, managed way to get that machinery
without building it all yourself.

This repository treats AgentCore as a *deployment target* for a system whose
governance already exists locally (Cedar policies, the four-layer security
model, OpenTelemetry traces) — the point isn't to invent new controls in the
cloud, it's to map controls that already work locally onto their managed AWS
equivalents, and to be honest about which of those mappings are proven with a
real deployment versus still just configured intent.

## Core concepts

- **Runtime.** The managed compute layer that actually executes your agent
  code. AgentCore Runtime supports two deployment shapes: direct-code
  (upload Python, AWS runs it) and container-based (build a Docker image,
  push to ECR). Either way, a request comes in, your code runs, a response
  goes out — Runtime is deliberately not opinionated about your agent
  framework.
- **Gateway.** A managed front door that "converts APIs, Lambda functions,
  and existing services into Model Context Protocol (MCP)-compatible tools",
  with OpenAPI, Smithy, and Lambda as tool input types, and passthrough
  targets for other agents and services
  ([Gateway](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)). It handles both inbound authentication,
  "verifying agent identity", and outbound authentication, "connecting to
  tools", and offers semantic tool search so an agent with thousands of
  tools sees only the relevant ones.
- **Identity.** A credential service for agents as workload identities. Its
  token vault stores OAuth 2.0 tokens, client credentials, and API keys,
  encrypted with KMS, and releases them only to an agent presenting
  "verifiable proof of workload identity". It supports machine-to-machine
  (client credentials, 2LO) and user-delegated (authorization code, 3LO)
  OAuth flows ([Identity features](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/key-features-and-benefits.html)). The
  point is that no long-lived secret sits in the agent's code or config.
- **Policy.** Authorization for tool calls, written in Cedar, the language
  this repository already uses. Policy "intercepts all agent traffic through
  Amazon Bedrock AgentCore Gateways and evaluates each request against
  defined policies" before allowing tool access, "at the boundary outside of
  agent's code" ([Policy](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy.html)). Policies can also be drafted in
  natural language, which the service turns into Cedar and checks. A new
  policy can run in `LOG_ONLY` mode, collecting what it would decide, before
  it is switched to `ACTIVE`.
- **Memory.** "Short-term memory captures turn-by-turn interactions within a
  single session"; "long-term memory automatically extracts and stores key
  insights from conversations across multiple sessions"
  ([Memory](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)). Long-term memory is configured as strategies:
  semantic (facts and knowledge), session summaries, user preferences,
  episodic (structured episodes with reflections across them), or a custom
  strategy ([built-in strategies](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/long-term-configuring-built-in-strategies.html)).
  Records are written to namespaces such as `/users/{actorId}/preferences/`,
  and short-term events expire after `eventExpiryDuration` days (3 to 365).
- **Observability.** AgentCore "emits telemetry data in standardized
  OpenTelemetry (OTEL)-compatible format" into CloudWatch, with built-in
  metrics for agents, gateways, and memory; spans beyond those come from
  instrumenting your own code ([Observability](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability.html)).
- **Evaluations.** Traces from instrumented agents "are converted to a
  unified format and scored using LLM-as-a-Judge techniques for both
  built-in and custom evaluators", run online against live traffic, on
  demand, in batches, or against a dataset
  ([Evaluations](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations.html)). The Evaluations course's advice
  applies unchanged: a managed judge still needs calibrating against people.
- **Guardrails.** Amazon Bedrock's managed content-safety layer: configurable
  denied topics, PII redaction, and other checks applied to model input and
  output, independent of whatever prompt engineering the agent itself does.
- **Direct-code vs. container deployment.** The first real decision this
  project had to make (see ADR 0016): package the agent as plain Python, or
  build a container. Direct-code wins when there's no system-level dependency
  that only a custom image could satisfy — which was true here.
- **Cross-region inference profile.** Some Bedrock models aren't available
  for direct on-demand invocation in every region; a cross-region inference
  profile routes the request to wherever the model actually is, rather than
  failing in the region you asked for.

## How this repository implements it

`config/agentcore.yaml` is the single source of local AgentCore intent, and
every field in it maps to one of the concepts above:

- `runtime.deployment_mode: direct_code` with `entrypoint: src.runtime.agentcore_app:app`
  is the ADR 0016 decision made literal — `src/runtime/agentcore_app.py` is
  the actual entrypoint AWS would invoke, and Docker/`docker-compose.yml`
  stay scoped to the *local comparison stack*, not this deployment path.
- `runtime.model: bedrock_converse:us.anthropic.claude-haiku-4-5-20251001-v1:0`
  with `region: us-west-2` is exactly the cross-region-inference-profile case
  above: Haiku 4.5 has no direct on-demand invocation in `us-west-2`, so the
  cross-region profile is required, not optional.
- `gateway.protocol: MCP`, `target: src.mcp_server.server:create_mcp_server`,
  `governed_path_only: true` is ADR 0017 made literal: the same MCP server
  this repo already uses locally (`src/mcp_server/server.py`, which re-checks
  Cedar tool permission and portfolio entitlement on every call, as the
  identity it was started with, for the portfolio named in the request)
  becomes the Gateway target — no deployed code is allowed a second, ungoverned
  path to `src/api/main.py` or `src/analytics/` directly.
- `identity.local_equivalent: config/roles.yaml` and
  `policy.local_equivalent: [governance/policies/tool-permissions.cedar, governance/policies/portfolio-access.cedar]`
  are explicit statements of "this is what AgentCore Identity/Policy would
  replace" — the mapping is documented before it's proven live.
- `guardrails.mode: extended_day_14` points at the same denied-term/topic
  guardrail this project's `src/control/guardrails.py` already enforces
  locally (see the `governance-delivery-tutor` and `opentelemetry-tutor`
  material for how that layer is tested).
- `teardown.required_after_demo: true` is not decoration — every live
  AgentCore evidence entry in `PROGRESS.md`'s extension log ends with an
  explicit teardown step, because AWS resources left running cost money and
  widen the blast radius of anything left misconfigured.

### What each service replaces here

Every AgentCore service does a job this repository already does locally.
`LOCAL_EQUIVALENTS` in `src/runtime/agentcore_lab.py` names the files, and a
test fails if any of them disappears.

| Service | Local equivalent | What changes when it is managed |
|---|---|---|
| Runtime | `src/runtime/agentcore_app.py`, `config/agentcore.yaml` | Session isolation, scaling, and hosting move to AWS |
| Gateway | `src/mcp_server/server.py` | One managed MCP boundary with inbound and outbound authentication |
| Identity | `config/roles.yaml`, `src/control/identity.py` | Real workload identities and a token vault replace three local names |
| Policy | the two Cedar files in `governance/policies/` | The same language, enforced at the Gateway, with `LOG_ONLY` rollout |
| Memory | `src/context/builder.py` | Persisted short-term events and extracted long-term records, per namespace |
| Observability | `src/observability/telemetry.py` | The same OpenTelemetry data, stored in CloudWatch with built-in metrics |
| Evaluations | `scripts/run_eval.py`, `src/evals/agentcore_evaluations.py` | Managed model-graded evaluators over traces, online or on demand |

### Control-plane requests, offline: `agentcore_lab.py`

`src/runtime/agentcore_lab.py` builds two requests and
`tests/unit/runtime/test_agentcore_lab.py` runs them through botocore's
Stubber against the `bedrock-agentcore-control` service model:

| What the test shows | Test |
|---|---|
| A memory with semantic, summary, and user-preference strategies matches the service model | `test_a_memory_with_three_long_term_strategies_matches_the_service_model` |
| A misspelled strategy is rejected before any call | `test_a_misspelled_strategy_is_rejected_before_any_call` |
| The SDK checks the 3-day minimum expiry locally but passes 400 days to the service | `test_offline_validation_checks_the_minimum_expiry_but_not_the_maximum` |
| A new Cedar policy starts in `LOG_ONLY` | `test_a_new_cedar_policy_starts_in_log_only_mode` |
| Every service's local equivalent exists | `test_every_agentcore_service_names_a_local_equivalent_that_exists` |

The expiry test is the honest limit of an offline lab: Stubber proves a
request has the right shape, not that the service will accept it.

## The four threads

| Thread | In AgentCore | Evidence |
|---|---|---|
| **Observability** | The same OpenTelemetry data this repository emits, stored in CloudWatch; the managed service adds built-in metrics, and anything deeper still comes from your own instrumentation. | `LOCAL_EQUIVALENTS["Observability"]` |
| **Traceability** | Policy decisions are logged per request, and Identity logs every credential operation, so a tool call can be traced to the identity and policy that allowed it. | the Policy and Identity pages cited above |
| **Governance** | Authorization stays in Cedar, now enforced at the Gateway outside the agent's code, and ADR 0017 keeps the Gateway the only deployed tool path. A new policy can be observed in `LOG_ONLY` before it enforces. | `test_a_new_cedar_policy_starts_in_log_only_mode` |
| **Evaluation** | Managed evaluators are model graders over traces; they need the same calibration against people, and a READY resource is never evidence that a request succeeded. | `src/evals/agentcore_evaluations.py` |

## Worked walkthrough: a real, documented failure

The most instructive AgentCore evidence in this repository isn't a success —
it's a documented failure, which is worth walking through because it shows
what "deployment-ready versus request-succeeded" actually looks like in
practice. On 2026-08-17, an attempt to stand up the AgentCore Gateway target
(`experiments/2026-08-17-agentcore-gateway/README.md`) hit two distinct,
sequential permission gaps:

1. The first CloudFormation stack attempt failed cleanup because the
   deploying role lacked `iam:DeleteRolePolicy` — a permission needed to tear
   down IAM resources the stack itself had created, not to create them.
2. After that permission was added and a corrected mock-integration stack was
   attempted, it failed on a *different* missing permission:
   `apigateway:POST` — needed to actually create the API Gateway REST
   resources the target depends on.

Neither attempt resulted in an actual API Gateway or AgentCore Gateway
resource existing. Read `experiments/2026-08-17-agentcore-gateway/deployment-attempts.json`
for the exact API error strings. The lesson this repository draws from it —
and states explicitly rather than glossing over — is that a `READY` Runtime
status or a configured `config/agentcore.yaml` is evidence that deployment
*intent* is correctly specified, never evidence that a request actually
succeeded. Contrast this with the temporary AgentCore Runtime request that
*did* reach `READY` and complete a bounded read-only request (also logged in
`PROGRESS.md`) — the same document distinguishes "reached READY" from
"completed a request" as two separate, independently-evidenced claims.

## Common pitfalls

- **Using long-lived, root-level credentials for a demo.** AgentCore Identity
  exists so a deployed agent gets short-lived, scoped credentials instead —
  using root access keys defeats the entire purpose of the Identity layer and
  is explicitly rejected in this tutor's negative examples.
- **Calling the MCP server directly from deployed code "to save a hop."**
  ADR 0017 makes Gateway the *only* accepted deployed tool path precisely
  because a second, ungoverned route reintroduces the authorization gap
  Gateway exists to close — direct local calls are fine in tests, never in a
  deployed path.
- **Treating "teardown is annoying so I'll skip it" as a reasonable
  shortcut.** `teardown.required_after_demo: true` isn't a suggestion; every
  recorded live AgentCore evidence entry in this repository includes an
  explicit teardown step, and skipping it both costs money and leaves
  resources that widen the attack surface.
- **Enforcing a new policy straight away.** Start it in `LOG_ONLY`, read
  what it would have denied, then switch it to `ACTIVE`.
- **Trusting offline validation as proof.** Stubber checks shape and some
  ranges against the service model; a request it accepts can still be
  refused by the service.
- **Treating long-term memory as a transcript.** Strategies extract facts,
  summaries, and preferences into namespaces; what is kept
  is what a strategy chose, so scope namespaces per actor and never store
  what the agent must not recall.

## Further reading

- [`docs/reference/REFERENCES.md#aws-bedrock--agentcore`](../../reference/REFERENCES.md#aws-bedrock--agentcore)
  for the official AgentCore docs, workshops, and sample repositories.
- [`docs/guides/AWS_AGENTCORE_SETUP.md`](../../guides/AWS_AGENTCORE_SETUP.md) for
  the full account-setup-to-teardown runbook, including cost guardrails and
  troubleshooting from the real live setup.
- [`docs/guides/AGENTCORE_GATEWAY_SETUP.md`](../../guides/AGENTCORE_GATEWAY_SETUP.md)
  for the Gateway-specific exercise this walkthrough is drawn from.
- `docs/adr/0016-agentcore-direct-code-deployment.md` and
  `docs/adr/0017-agentcore-gateway-only-tool-path.md` for the two governing
  decisions in full.
- `docs/evidence/EVIDENCE.md` for the running local-versus-live ledger this
  tutor's "never claim a resource was deployed" rule is built to protect.
