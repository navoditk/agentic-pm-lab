# Comparison Notes

Empirical comparisons recorded while building agentic-pm-lab. Measurements use
public or mock project data only.

## Context engineering

### 2026-08-10 — Day 4 full-context baseline vs. source filtering

Two representative questions used the same named source bundle: identity/role,
ten mock positions, 500 daily returns, a seven-point curve, a deliberately
oversized mock research summary, 50 memory entries, prior tool outputs, and
three skills. Token counts use tiktoken's `gpt-4.1-mini` encoding. Builder
latency is the average of 2,000 local runs and excludes model/network latency.

| Question/configuration | Included sources | Tokens | Builder latency |
|---|---|---:|---:|
| Full baseline, either question | All seven named sources | 7,427 | 0.203 ms |
| "What's my portfolio volatility?" | user/role, portfolio, market, tool outputs, skills | 3,759 | 0.125 ms |
| "What are the largest concentrations?" | user/role, portfolio, skills | 292 | 0.019 ms |

Filtering reduced context tokens by 49.4% for the volatility question and 96.1%
for the concentration question. Local composition also became faster, though
sub-millisecond builder time is immaterial compared with a model call. The
meaningful expected benefit is avoiding irrelevant research and memory tokens.

**Blocked live comparison:** OpenAI was selected instead of the plan's default
Anthropic provider, but its smoke test returned `insufficient_quota`. No model
answer quality, tool-call transcript, end-to-end token usage, or model latency
is reported; inventing those measurements would invalidate the experiment.
After credits are available, rerun both questions against the same source
bundle and append actual tool calls, answers, and end-to-end latency here.
