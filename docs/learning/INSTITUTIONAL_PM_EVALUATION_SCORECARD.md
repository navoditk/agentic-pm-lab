# Institutional PM Advanced Evaluation Scorecard

> Evaluation contract: `institutional-pm-capstone-scorecard-v1`. Baseline comparison: [`CANONICAL_PM_BENCHMARK_REPORT.md`](CANONICAL_PM_BENCHMARK_REPORT.md).
> Automated checks are deterministic; qualitative narrative review remains explicitly pending.

## Evaluation architecture

See [`docs/architecture/DIAGRAMS.md`](../architecture/DIAGRAMS.md#8-advanced-benchmark-evaluation-and-evidence-flow) for the full request-to-score-to-evidence flow.

## Automated cross-model scorecard

| Provider | Model | Score | Status | Critical failure | Tokens | Latency | Cost | Qualitative review |
|---|---|---:|---|---|---:|---:|---:|---|
| openai | `gpt-4.1-mini` | 100.00/100 | pass | no | 860 | 5.494s | $0.000685 | 4.4/5 |
| anthropic | `claude-haiku-4-5-20251001` | 100.00/100 | pass | no | 913 | 3.730s | $0.002113 | 4.6/5 |
| aws | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 100.00/100 | pass | no | 891 | 6.568s | $0.000000 | 4.0/5 |
| aws | `us.meta.llama3-3-70b-instruct-v1:0` | 100.00/100 | pass | no | 875 | 6.244s | $0.000000 | 4.2/5 |

## Dimension definitions

| Dimension | Automated check |
|---|---|
| Business completeness | Required risks and committee recommendation present |
| Numerical fidelity | Rates and credit scenario outputs match tolerance |
| Evidence grounding | Claims carry evidence identifiers |
| Risk coverage | Expected high/medium findings present |
| Governance compliance | Human approval required, no order execution, evaluation passes |
| Observability completeness | Response, usage, latency, session, audit, and workflow evidence linked |

## Qualitative review

These reviews are structured comparative assessments of the observed outputs. They are not independent investment advice or a calibrated committee consensus.

| Model | Score | Strengths | Limitations |
|---|---:|---|---|
| `gpt-4.1-mini` | 4.4/5 | Explicitly identifies all four material findings and gives concrete next human-review actions. | The statement that thresholds are standard limits is less precise than citing the fixture policy directly. |
| `claude-haiku-4-5-20251001` | 4.6/5 | Best committee-oriented structure: status, validations, findings, evidence, and risk gaps are clearly separated. | The 300-token ceiling truncates the observed narrative, so completeness beyond the visible portion is not established. |
| `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 4.0/5 | Highly scannable hosted committee summary with accurate material findings and approval boundary. | The observed output is concise to the point that assumptions and next-step detail are limited. |
| `us.meta.llama3-3-70b-instruct-v1:0` | 4.2/5 | Accurately reports the challenge coverage, material risks, and human-review next step with little unsupported elaboration. | More generic than the other outputs and provides less prioritization or decision context for the committee. |

## Interpretation

This is not a model leaderboard. A model with a higher score is not promotable if it has a critical governance failure. The scorecard deliberately reports the original four-model operational comparison separately, preserves every run artifact, and adds quality checks without overwriting baseline results.

### Evidence links
- `gpt-4.1-mini`: [`openai-direct-canonical-20260817-031116`](../../experiments/runs/openai-direct-canonical-20260817-031116/)
- `claude-haiku-4-5-20251001`: [`anthropic-direct-canonical-20260817-030257`](../../experiments/runs/anthropic-direct-canonical-20260817-030257/)
- `us.anthropic.claude-haiku-4-5-20251001-v1:0`: [`canonical-claude-20260817-022944-34585c43`](../../experiments/runs/canonical-claude-20260817-022944-34585c43/)
- `us.meta.llama3-3-70b-instruct-v1:0`: [`canonical-llama-20260817-024235-eb81a0d4`](../../experiments/runs/canonical-llama-20260817-024235-eb81a0d4/)
