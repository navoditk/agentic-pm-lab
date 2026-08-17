# Institutional PM Scorecard v2

> This report extends the [baseline four-model comparison](CANONICAL_PM_BENCHMARK_REPORT.md) without replacing it.
> Current observed repetitions are one per model; promotion requires the configured minimum repetition count.

## Repeated-run analysis

| Model | Runs | Success rate | Mean score | Score stdev | p95 latency | Cost/run | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `gpt-4.1-mini` | 1 | 100.0% | 100.00 | 0.00 | 5494 ms | $0.000685 | fail |
| `claude-haiku-4-5-20251001` | 1 | 100.0% | 100.00 | 0.00 | 3730 ms | $0.002113 | fail |
| `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 1 | 100.0% | 100.00 | 0.00 | 6568 ms | $0.000000 | fail |
| `us.meta.llama3-3-70b-instruct-v1:0` | 1 | 100.0% | 100.00 | 0.00 | 6244 ms | $0.000000 | fail |

## Scenario coverage

| Scenario | Status | Purpose |
|---|---|---|
| `baseline` | observed | Canonical point-in-time capstone comparison. |
| `missing-liquidity` | planned | Verify abstention and explicit uncertainty when liquidity data is absent. |
| `stale-evidence` | planned | Reject or qualify evidence outside the decision-date freshness window. |
| `conflicting-sources` | planned | Surface contradiction instead of silently selecting a preferred source. |
| `unauthorized-portfolio` | planned | Deny access before model invocation and record an authorization trace. |
| `prompt-injection-research` | planned | Treat hostile research text as untrusted evidence and preserve tool boundaries. |
| `malformed-tool-response` | planned | Validate, retry, and dead-letter malformed deterministic tool output. |

## Promotion interpretation

The current baseline passes the quality and latency gates but does not satisfy the five-repetition promotion requirement. Adversarial scenarios remain planned until provider adapters execute them and append immutable run records.
