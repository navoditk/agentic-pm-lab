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

A later Ollama run applied the full and filtered bundles to the actual agent
for the same overloaded volatility question:

| Agent context | Tokens | End-to-end latency | Tool calls |
|---|---:|---:|---|
| Full | 7,359 | 59.992 s | None |
| Filtered | 3,686 | 154.063 s | None |

Filtering halved tokens but did not recover tool use, and the single-run latency
was worse rather than better. The 4B local model failed to turn the 500-return
array into `get_volatility` arguments in either configuration. This is a useful
quality result: source filtering reduces context size, but does not by itself
make a small model reliable on large structured tool arguments. Repeated runs
and cloud measurements are needed before drawing a latency conclusion.

**Blocked live comparison:** OpenAI was selected instead of the plan's default
Anthropic provider, but its smoke test returned `insufficient_quota`. No model
answer quality, tool-call transcript, end-to-end token usage, or model latency
is reported; inventing those measurements would invalidate the experiment.
After credits are available, rerun both questions against the same source
bundle and append actual tool calls, answers, and end-to-end latency here.

## Local vs. cloud model

### 2026-08-10 — Day 4 single-agent variant

The optional local variant uses Ollama 0.32.7 with `qwen3:4b` and the same
Deep Agent, tools, skills directory, system prompt, and context path as the
OpenAI configuration.

| Question | Local result | Cloud result |
|---|---|---|
| Portfolio volatility | Called `get_volatility` with the supplied returns, window 2, and 252 periods/year; reported the four tool values without inventing data | Blocked by `insufficient_quota` before an agent run |
| Largest concentration | Called `get_portfolio_exposure`, identified the 60% position, and disclosed that classifications were mocked | Blocked by `insufficient_quota` before an agent run |

A warm local volatility run took 129.696 seconds end to end. Tool selection and
argument shape were correct, but the 4B model needed an explicit instruction to
use the named tool and was substantially slower than an API response would
normally be expected to be. OpenAI credits were later added and a
`gpt-4.1-mini` smoke test returned successfully, but matched cloud
latency/answer-quality runs have not yet been executed.

## Development tool comparison

Record actual Claude Code, GitHub Copilot, and Codex CLI usage on this
repository rather than relying only on published benchmarks. Usage is reported
by each tool separately; `INSTALL.md` §8 identifies where to retrieve it.

| Day | Tool | Task type | Session length / turns | Usage reported | Quality note | Use again? |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

Update the running conclusion only after several comparable entries exist.

## Optional AWS extension findings

This section fills in only if optional Days 13–14 are completed.

| Topic | Finding |
|---|---|
| AgentCore Memory vs. session-state handling | — |
| AgentCore Evaluations vs. LangSmith | — |
| Cost-lowering techniques | — |
