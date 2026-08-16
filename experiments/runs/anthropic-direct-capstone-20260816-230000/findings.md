# Findings: Direct Anthropic institutional PM capstone

Run ID: `anthropic-direct-capstone-20260816-230000`

## Question and hypothesis

- Question: Assess overnight rates and credit-risk implications for Portfolio A;
  summarize evidence, assumptions, risks, and the next human review step.
- Hypothesis: A direct Anthropic Messages API call can narrate the deterministic
  institutional PM capstone without bypassing authorization, provenance, or the
  human-approval boundary.

## Setup

- Provider/runtime: Anthropic direct Messages API
- Model/version: `claude-haiku-4-5-20251001`
- Region or local host: Anthropic API; no AWS resource provisioned
- Input fixture: `input.json` copied from the governed AgentCore proof fixture
- Prompt/configuration: 300-token maximum, temperature 0, concise evidence-linked
  committee summary; private chain-of-thought explicitly excluded from logging

## Result

- Outcome: Success. The model returned a committee summary after the local
  capstone completed its deterministic data, challenge, evaluation, and control
  stages.
- What worked: Direct authentication, response capture, native token accounting,
  OTel span metrics, audit JSONL, and the approval-only/no-order outcome.
- What failed or surprised us: The first local attempt exposed a script import-path
  defect; the second attempt was blocked by sandbox DNS. Both were fixed or
  retried without an API response being produced. The successful response stopped
  at the configured 300-token ceiling.
- Reproducibility notes: Run with `ANTHROPIC_API_KEY` supplied transiently in the
  environment and follow the commands in `docs/guides/DIRECT_MODEL_RUNS.md`.

## Trade-offs

### Advantages

- Simple direct API path, native provider usage fields, and no cloud resources to
  clean up.

### Limitations and risks

- Fixture data is public/mock only; the direct API estimate is not a provider bill;
  the response ceiling may truncate a summary; private chain-of-thought is not
  available or retained.

### Cost and latency interpretation

- 613 input tokens, 300 output tokens, 913 total tokens, 3,706 ms recorded
  latency, and estimated token cost `$0.002113` using $1.00/M input and $5.00/M
  output pricing as of 2026-08-16. No AWS infrastructure cost applies.

## Evidence

- Artifact: [`response.json`](response.json), [`input.json`](input.json)
- Trace/log: [`audit.jsonl`](audit.jsonl); OTel metrics are embedded in the response
  stage metadata and no private chain-of-thought is logged.
- Usage/cost snapshot: `manifest.json` records 613/300 tokens, 3,706 ms, and
  `$0.002113` estimated token cost.

## Decision

- Keep: direct Anthropic is now a supported non-AWS provider path, subject to
  explicit API-key handling and model-access/billing controls.
- Next experiment: compare direct Anthropic with direct OpenAI on identical input.
