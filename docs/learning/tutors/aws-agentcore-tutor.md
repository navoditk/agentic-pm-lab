# AWS Bedrock AgentCore — deep dive

*Companion to [`.github/agents/aws-agentcore-tutor.agent.md`](../../../.github/agents/aws-agentcore-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py aws-agentcore-tutor --quiz`.*

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
- **Gateway.** A managed API front door that turns existing APIs, Lambda
  functions, or MCP servers into a governed set of tools an agent can call,
  enforcing authorization and observability at that single boundary rather
  than trusting every caller.
- **Identity.** AgentCore's answer to "how does my deployed agent get
  short-lived, scoped credentials instead of a long-lived API key baked into
  its config" — delegated, temporary access rather than static secrets.
- **Policy.** The managed authorization layer that decides whether a given
  identity may take a given action on a given resource — conceptually the
  same job Cedar does locally in this repository, just running as an AWS
  service instead of an embedded library.
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
  Cedar tool permission and portfolio entitlement from MCP request metadata)
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

## Further reading

- [`docs/reference/REFERENCES.md#aws-bedrock--agentcore`](../reference/REFERENCES.md#aws-bedrock--agentcore)
  for the official AgentCore docs, workshops, and sample repositories.
- [`docs/guides/AWS_AGENTCORE_SETUP.md`](../guides/AWS_AGENTCORE_SETUP.md) for
  the full account-setup-to-teardown runbook, including cost guardrails and
  troubleshooting from the real live setup.
- [`docs/guides/AGENTCORE_GATEWAY_SETUP.md`](../guides/AGENTCORE_GATEWAY_SETUP.md)
  for the Gateway-specific exercise this walkthrough is drawn from.
- `docs/adr/0016-agentcore-direct-code-deployment.md` and
  `docs/adr/0017-agentcore-gateway-only-tool-path.md` for the two governing
  decisions in full.
- `docs/evidence/EVIDENCE.md` for the running local-versus-live ledger this
  tutor's "never claim a resource was deployed" rule is built to protect.
