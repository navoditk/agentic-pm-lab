# Institutional PM Scorecard v2

> This report extends the [baseline four-model comparison](CANONICAL_PM_BENCHMARK_REPORT.md) without replacing it.
> The matrix contains 5 observed repetition(s) per model at most; the configured promotion threshold is 5.

## Repeated-run analysis

| Model | Runs | Success rate | Mean score | Score stdev | Mean tokens | p95 latency | Cost/run | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `gpt-4.1-mini` | 5 | 100.0% | 100.00 | 0.00 | 817 | 9176 ms | $0.000616 | pass |
| `claude-haiku-4-5-20251001` | 5 | 100.0% | 100.00 | 0.00 | 913 | 6931 ms | $0.002113 | pass |
| `us.anthropic.claude-haiku-4-5-20251001-v1:0` | 5 | 100.0% | 100.00 | 0.00 | 891 | 8187 ms | $0.002091 | pass |
| `us.meta.llama3-3-70b-instruct-v1:0` | 5 | 100.0% | 100.00 | 0.00 | 875 | 11309 ms | $0.000630 | pass |

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

The matrix contains 5 observed repetition(s) per model at most; the configured promotion threshold is 5. Adversarial scenarios remain planned until provider adapters execute them and append immutable run records.

AWS cost/run is a token estimate using standard on-demand Bedrock rates; the temporary AgentCore runtime, logging, and storage components are recorded separately and are not included when their asynchronous cost lookup returns zero or unavailable.
