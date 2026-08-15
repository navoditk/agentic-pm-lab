# Experiments

Experiments are the repository's neutral comparison surface for answering a
practical question with a fixed input and a declared setup. A setup may be
local, AWS-backed, or another hosted model/provider. The purpose is not to
collect impressive demos; it is to make capability, cost, latency, failure
modes, and operational burden comparable.

## Mandate

Every experiment should make these boundaries explicit:

- What question or hypothesis is being tested?
- What input, prompt, tools, model/version, and configuration were used?
- Which provider/runtime was exercised and which parts were simulated?
- What output and observable evidence were produced?
- What tokens, latency, and pricing basis were observed or estimated?
- For AWS, what infrastructure cost was observed or estimated separately from
  model token cost?
- What worked, what failed, what are the pros/cons, and what remains unclaimed?
- What cleanup was required and was it completed?

An experiment is successful only when its declared outcome is supported by the
recorded output and evidence. A deployed resource reaching `READY` is not
request-execution evidence. A local mock response is not hosted-provider
evidence. A pricing estimate is not an invoice.

## Record format

The normalized record is `manifest.json` plus a human-readable `findings.md`.
The manifest keeps provider-neutral fields while preserving provider-specific
details in evidence files. The accounting model separates:

```text
token estimate = input_tokens * input_rate / 1,000,000
              + output_tokens * output_rate / 1,000,000

total estimate = token estimate
              + AWS observed spend (or AWS estimated spend until observed)
              + other estimated spend
```

The recorder prefers observed AWS spend when both observed and estimated values
exist, so replacing an estimate with settled billing data does not double count.
Do not add AWS Bedrock token charges twice. If Cost Explorer or a provider bill
already includes model invocation charges, record the authoritative billing
amount in the appropriate AWS field and explain the treatment in the manifest.
Keep the pricing source and as-of date beside every token estimate. Rates vary
by model, region, tier, cached tokens, batch mode, and provider terms.

AWS cost records should identify the account, region, resource/run prefix,
budget snapshot, Cost Explorer query period, and whether the number is
estimated or settled. Cost Explorer and budgets can lag; capture the raw JSON
response and update the run later if the settled amount changes.

## Start an experiment on the fly

Create a run without editing a template:

```bash
uv run python scripts/experiment.py init \
  --name "local prompt comparison" \
  --provider local --mode single_request --model mock-v1 \
  --run-id local-prompt-001
```

Record a response, usage, pricing basis, and evidence:

```bash
uv run python scripts/experiment.py record \
  --run-dir experiments/runs/local-prompt-001 \
  --status success --input-tokens 1200 --output-tokens 350 \
  --input-rate 1.00 --output-rate 5.00 \
  --pricing-source "provider pricing page" --pricing-as-of 2026-08-13 \
  --latency-ms 840 --input-path input.json --output-path response.json \
  --evidence trace.json --note "No external network call; mock model."

uv run python scripts/experiment.py finalize \
  --run-dir experiments/runs/local-prompt-001 \
  --status success --decision keep \
  --next-experiment "Repeat with hosted model and same input."
uv run python scripts/experiment.py check --run-dir experiments/runs/local-prompt-001
```

For a non-AWS hosted provider, use `--provider openai`, `anthropic`, `google`,
or `other`, supply the provider's actual token counts and rates, and attach the
raw response/usage object as evidence. For a local model, record token counts
from the serving runtime when available; otherwise state that token usage is
unavailable rather than inventing it.

When the provider response contains a `usage` object, the recorder normalizes
common names automatically:

```bash
uv run python scripts/experiment.py record \
  --run-dir experiments/runs/comparison-001 \
  --usage-json provider-response.json \
  --input-rate 1.00 --output-rate 5.00 \
  --pricing-source "provider pricing page" --pricing-as-of 2026-08-13
```

It recognizes `input_tokens`/`prompt_tokens`/`inputTokens` and
`output_tokens`/`completion_tokens`/`outputTokens`, plus common total-token
fields. Explicit CLI values override the JSON file.

For AWS, use the [AWS AgentCore runbook](../docs/guides/AWS_AGENTCORE_SETUP.md), then
record both token usage and the separate AWS billing snapshot:

```bash
uv run python scripts/experiment.py record \
  --run-dir experiments/runs/agentcore-proof-001 \
  --status success --input-tokens 900 --output-tokens 280 \
  --input-rate 0.80 --output-rate 4.00 \
  --pricing-source "Bedrock pricing reference" --pricing-as-of 2026-08-13 \
  --aws-estimated 0.02 --request-id req-001 \
  --runtime-session-id session-001 --evidence events.json
```

Replace `--aws-estimated` with `--aws-observed` once the billing period has
settled, and retain the original estimate in the run notes. The command never
contacts AWS; it records values already captured by the deployment workflow.

## Directory convention

```text
experiments/
  README.md                         # mandate and common workflow
  templates/                        # optional reusable inputs/prompts
  agentcore-runtime-proof/          # reusable AWS fixture
  2026-08-13-agentcore-pm-review/  # dated run and its evidence
  runs/<run-id>/
    manifest.json                   # normalized machine-readable record
    findings.md                     # pros, cons, limitations, decision
    input.json / response.json      # safe request/response artifacts
    trace.json / events.json        # provider-specific evidence, if any
```

Only public/mock data may be committed. Do not commit credentials, bearer
tokens, proprietary prompts, customer data, or unreviewed raw provider output.
If a run uses sensitive data locally, keep the run outside the repository and
commit only a redacted manifest and findings summary.

## Comparing setups

Use the same input, task definition, output constraints, and evaluation rubric
where possible. Compare at least:

| Dimension | Local model | Non-AWS hosted model | AWS/AgentCore |
|---|---|---|---|
| Control | Highest local control; operational realism is limited | Provider API and terms apply | IAM, roles, runtime, network, and service limits apply |
| Cost | Hardware/electricity or subscription must be stated | Token price and tiers | Token price plus runtime, logs, storage, and other AWS usage |
| Observability | Local logs/traces | Provider response plus client telemetry | Request, runtime, CloudWatch, and billing evidence |
| Reproducibility | Version and hardware pinning matter | Model revisions and pricing can change | Region, account, permissions, packaging, and service state matter |
| Failure surface | Load, memory, model quality | Rate limits, outages, API/schema changes | All provider failures plus IAM, packaging, deployment, and cleanup |
| Learning value | Understand model behavior and orchestration | Compare model capability and economics | Understand production integration and cloud operations |

The findings should explain both the advantages and the limitations of the
chosen setup. A local result may show algorithmic behavior without proving
production latency or identity controls. A hosted result may show model quality
without proving data governance. An AWS result may show deployment and IAM
behavior while still leaving model quality, billing lag, or a failed request
unresolved. These distinctions are the point of the experiment record.

## Existing runs

- [`agentcore-runtime-proof/`](agentcore-runtime-proof/) is the reusable small
  AWS fixture and invocation probe.
- [`2026-08-13-agentcore-pm-review/`](2026-08-13-agentcore-pm-review/) records
  the live deployment trial, including its ARM64 packaging failure, HTTP 500,
  costs, and teardown. It is intentionally not marked as a successful hosted
  inference.

The [evidence ledger](../docs/evidence/EVIDENCE.md) remains the cross-project summary;
this directory is the detailed experiment record.
