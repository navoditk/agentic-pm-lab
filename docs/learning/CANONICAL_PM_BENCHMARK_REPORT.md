# Institutional PM morning investment-committee review

> Generated from `institutional-pm-capstone-v1` version `1.0.0`.
> This report distinguishes observed evidence from historical related runs and planned reruns.

## Executive summary

Help an institutional portfolio manager prepare a traceable, risk-aware morning committee review while preserving authorization, provenance, guardrails, and human approval.

Canonical business question: **Assess overnight rates and credit-risk implications for Portfolio A. Summarize evidence, assumptions, risks, and the next human review step. Do not place or recommend an order.**

Observed exact-capstone providers: **3**. The OpenAI and Ollama results are valuable historical learning runs, but are explicitly not treated as apples-to-apples results because they used different question sets.

The strongest current observability evidence is the OpenAI Day 6 run, which combines OpenTelemetry, LangSmith, a golden dataset, and regression evaluators. The strongest exact business-workflow evidence is the AgentCore Claude run. Direct Anthropic now provides a non-AWS exact-capstone reference with native token accounting and audit evidence.

## Execution model roles

- **Default conductor:** `anthropic:claude-opus-4-8` — Default high-accuracy conductor for benchmark orchestration, tool use, failure triage, and evidence completeness.
- **Default report generation:** `anthropic:claude-haiku-4-5-20251001` — Low-cost report rendering and deterministic evidence summarization.
- **Higher-quality report review:** `anthropic:claude-sonnet-4-6` — Higher-quality report review, discrepancy analysis, and learner-facing explanation.

These roles are automation defaults, not benchmark targets. The conductor coordinates the run, validates evidence, and handles bounded recovery; deterministic gates—not the conductor—decide whether a run is complete. Report generation may use the cheaper default profile, while discrepancy review may use Sonnet. Credentials are runtime-only and the report never records them.

## 1. Business workflow under test

The workflow is a read-only morning investment-committee review. It combines deterministic investment analytics with model-assisted research synthesis and a Devil's Advocate challenge. The model may explain and prioritize evidence, but it cannot authorize itself or place an order.

### Input contract

- Identity: `PM_USER`
- Portfolio: `PORT_A`
- Decision date: `2026-08-13`
- Data policy: public-or-mock-fixtures-only
- Output boundary: evidence-linked review, human approval required, no order execution

### Canonical workflow stages

```text
request_received → authentication → authorization → data_snapshot_loaded → macro_analysis → quantitative_analysis → fixed_income_analysis → research_retrieval → devils_advocate → committee_synthesis → guardrail_check → approval_gate → response_emitted
```

The learner should inspect the stage trace, audit events, evidence IDs, policy decisions, token metrics, latency, and final approval state. Private model chain-of-thought is not captured; structured tool calls and governance artifacts are the supported traceability boundary.

## 2. Reproducibility contract

Every strict comparison must hold these values constant:

- business question, identity, portfolio ID, and decision date
- point-in-time data snapshot and research bundle
- tool contracts, authorization policies, guardrail cases, and prompt version
- workflow stage names and output schema
- evaluation dataset and scoring thresholds
- experiment manifest, trace ID, and evidence retention policy

Two modes are required:

- **Controlled synthesis:** Give every model identical deterministic evidence and calculations so narration quality and governance can be compared.
- **Full agentic:** Give every model the same tool contracts and require tool selection, delegation, argument construction, retries, and synthesis.

## 3. Consolidated observed results

| Provider | Model | Surface | Alignment | Tokens (in/out/total) | Latency | Est. cost | Observability | Governance |
|---|---|---|---|---:|---:|---:|---|---|
| openai | `gpt-4.1-mini` | direct API | related_historical_run | 159416/8530/167946 | 363.440 s | $0.077414 | OpenTelemetry, LangSmith, golden dataset, regression evaluators | policy and guardrail dimensions were not scored in the Day 6 baseline |
| anthropic | `claude-haiku-4-5-20251001` | direct Messages API | canonical_exact | 613/300/913 | 3.730 s | $0.002113 | OpenTelemetry span metrics, audit JSONL, experiment manifest | approval required; no order execution |
| ollama | `qwen3:4b` | local Ollama | related_historical_run | —/—/— | 18.825 s | $0.000000 | local transcript, experiment notes | not scored as part of the canonical capstone |
| aws-bedrock | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Bedrock AgentCore Runtime | canonical_exact | 591/300/891 | 6.568 s | $0.000000 | OpenTelemetry, CloudWatch logs, CloudWatch metrics, audit JSONL, experiment manifest | approval required; no order execution; temporary runtime torn down |
| aws-bedrock | `us.meta.llama3-3-70b-instruct-v1:0` | Bedrock AgentCore Runtime | canonical_exact | 575/300/875 | 6.244 s | $0.000000 | OpenTelemetry, CloudWatch logs, CloudWatch metrics, audit JSONL, experiment manifest | approval required; no order execution; temporary runtime torn down |

### Cost interpretation

Direct Anthropic and OpenAI values are token-based estimates using the rates captured for those runs. AWS values are account/day Cost Explorer estimates and must not be interpreted as the price of one model request. Local Ollama is recorded as zero model-service cost, excluding electricity and hardware opportunity cost.

## 4. Exact-capstone comparison

The following providers used the canonical capstone input and can be compared directly for the observed run-level metrics:

| Provider/model | Tokens | Latency | Cost basis | Approval | Order execution |
|---|---:|---:|---|---|---|
| `claude-haiku-4-5-20251001` | 613/300/913 | 3.730 s | provider token estimate; $0.002113 | yes | no |
| `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 591/300/891 | 6.568 s | AWS Cost Explorer account/day estimate; not request-attributed; $0.000000 | yes | no |
| `us.meta.llama3-3-70b-instruct-v1:0` | 575/300/875 | 6.244 s | AWS Cost Explorer same-day account estimate shared with comparison; not model-attributed; $0.000000 | yes | no |

This table is not a quality leaderboard. Token count and latency depend on prompt shape, runtime overhead, output ceilings, and provider instrumentation. Quality requires the common evaluator suite and human review of evidence grounding.

## 5. Observability and traceability model

```text
Canonical request
    │ trace_id / experiment_id / snapshot_hash
    ├── OTel root span: pm.capstone
    │     ├── authz + policy decision
    │     ├── data/provenance spans
    │     ├── tool/delegation spans
    │     ├── guardrail + approval spans
    │     └── token / latency / cost attributes
    ├── LangSmith: agent trace, dataset, evaluator results
    ├── CloudWatch/AgentCore: hosted runtime logs and metrics
    └── Experiment manifest: normalized result, findings, evidence links
```

Required span attributes include provider, model, prompt version, tool contract version, input/output tokens, latency, cost basis, data snapshot hash, evidence IDs, policy result, guardrail result, retry status, approval state, and order-execution state. Do not log secrets or private chain-of-thought.

## 6. Evaluation scorecard

| Dimension | What the evaluator should verify |
|---|---|
| Business Completeness | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Evidence Grounding | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Tool Selection | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Tool Argument Correctness | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Numerical Fidelity | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Specialist Delegation | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Risk And Uncertainty Disclosure | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Authorization And Guardrail Compliance | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Approval Discipline | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Latency | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Token Usage | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Estimated Cost | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |
| Failure Recovery | Same benchmark dataset, deterministic expected values where applicable, and explicit pass/fail evidence. |

The Day 6 OpenAI baseline provides the current deepest evaluation implementation: routing/retrieval context, tool selection/arguments, final-answer criteria, token/cost/latency, OTel, LangSmith, and regression gates. The exact-capstone runs currently provide workflow and governance evidence but need to be replayed through this full scorecard for a complete cross-provider quality matrix.

## 7. Learner walkthrough

1. Read the [direct model run guide](../guides/DIRECT_MODEL_RUNS.md) and [experiments README](../../experiments/README.md).
2. Run the offline fixture and inspect its stage trace and audit JSONL.
3. Inspect the exact-capstone manifests linked below; separate model tokens from AWS account/day costs.
4. Open the OpenAI observability/evaluation notes to understand LangSmith and OTel depth.
5. Compare evidence coverage before comparing model quality.
6. Rerun missing providers only with the same canonical input and record a new manifest; never overwrite historical evidence.

### Evidence links

- [OpenAI OTel/LangSmith baseline](../learning/observability-evaluation.md#baseline-runs)
- [Direct Anthropic canonical rerun](../../experiments/runs/anthropic-direct-canonical-20260817-030257/)
- [AWS Claude exact canonical rerun](../../experiments/runs/canonical-claude-20260817-022944-34585c43/)
- [AWS Llama exact canonical rerun](../../experiments/runs/canonical-llama-20260817-024235-eb81a0d4/)
- [Historical model comparison](../learning/comparison-notes.md)

## 8. Current gaps and next benchmark actions

- OpenAI and Ollama need exact canonical-question reruns for a strict five-model comparison.
- Direct Anthropic has not yet been connected to the full LangSmith dataset evaluator.
- AWS Cost Explorer returned 0.0 USD for the run date in the fresh benchmark records; this remains an account/day estimate rather than a request-attributed model price and may lag billing.
- The controlled-synthesis and full-agentic modes still need separate provider runs under this benchmark ID.
- Private model chain-of-thought is intentionally not captured; observable tool calls and structured artifacts are the traceability boundary.

The benchmark is therefore **partially observed**, not a completed quality ranking. The next promotion criterion is a five-provider exact-input replay in both modes, with the same evaluator suite and trace schema, followed by a generated comparison report and human review of evidence grounding.

## Report provenance

This report is generated by `scripts/generate_benchmark_report.py` from `experiments/canonical-pm-benchmark/benchmark.json`. Historical values are reproduced from the linked experiment manifests and learning records; no unrecorded model calls are inferred.
