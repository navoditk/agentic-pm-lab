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

**Cloud follow-up:** OpenAI was selected instead of the plan's default
Anthropic provider. Its first smoke test returned `insufficient_quota`; credits
were later added and `gpt-4.1-mini` succeeded. The exact Day 4 overloaded
context runs have not been repeated in the cloud, so no invented comparison is
reported here.

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

### 2026-08-11 — Day 5 multi-agent variant

Both variants received the same cross-domain question, named-source context,
and explicit instruction to delegate rate repricing to Macro and rolling
volatility to Quant.

| Model | Result | Observed limitation |
|---|---|---|
| OpenAI `gpt-4.1-mini` | Called both native sub-agents and synthesized their results | Portfolio Manager omitted `periods_per_year=12` from the Quant task, so the tool used its default annualization. The routing passed, but parameter preservation did not. |
| Ollama `qwen3:4b` | Returned an empty final response in 18.825 seconds with no `task` call | The 4B model failed at orchestrator-level delegation even with explicit specialist names and a small structured payload. |

The cloud parameter-loss defect led to stronger orchestrator and Quant
instructions plus a deterministic routing case that preserves the calculation
arguments. The local result is a genuine capability gap for this hierarchy;
reducing the question to a single specialist would no longer test Day 5's
multi-agent requirement.

## Development tool comparison

Record actual Claude Code, GitHub Copilot, and Codex CLI usage on this
repository rather than relying only on published benchmarks. Usage is reported
by each tool separately; `INSTALL.md` §8 identifies where to retrieve it.

| Day | Tool | Task type | Session length / turns | Usage reported | Quality note | Use again? |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

Update the running conclusion only after several comparable entries exist.

## Day 13 AWS extension findings

Day 13 keeps the cloud boundary explicit. The local memory store and
evaluation manifest are deterministic substitutes: they prove identity
isolation, scope handling, context serialization, and same-dataset report
comparison without creating AWS resources. The AgentCore adapter can be added
at deployment time behind the same small contract.

### AgentCore Memory vs. Deep Agent session state

Deep Agent state is useful for the current run or an application-managed
checkpoint. It should not silently become durable user memory. The Day 13
boundary separates short-term session context from long-term, user-scoped
preferences. Authorization and portfolio access remain control-layer
decisions, not consequences of a remembered instruction.

The standalone proof is the preference “Flag concentration above 5%.” A fresh
lookup for `PM_USER` returns it, while a lookup for `RISK_USER` does not. The
production AgentCore exercise must repeat this test with a real session
boundary and deletion/retention evidence.

### AgentCore Evaluations vs. LangSmith

The comparison preserves separate dimensions instead of creating an opaque
aggregate score. LangSmith remains the development baseline for dataset
iteration, evaluator debugging, and OTel-linked traces. AgentCore Evaluations
is the AWS-native production comparison path, using the same golden dataset
and searchable runtime traces. The manifest in
`src/evals/agentcore_evaluations.py` records trajectory, tool selection,
response quality, and policy dimensions.

No live AgentCore Evaluation report is claimed yet; that requires the AWS
account, a deployed Runtime, CloudWatch Transaction Search, and an evaluator
model.

This section records Day 13 evidence and identifies the remaining live-cloud work.

| Topic | Finding |
|---|---|
| AgentCore Memory vs. session-state handling | Local contract proves identity isolation and explicit scopes; live cross-session evidence remains pending AWS setup. |
| AgentCore Evaluations vs. LangSmith | Same-dataset comparison manifest is ready; live AWS report remains pending Runtime and Transaction Search setup. |
| Cost-lowering techniques | — |
