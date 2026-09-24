# Agent architecture — deep dive

*Companion to [`agents/agent-architecture-tutor.md`](../../../agents/agent-architecture-tutor.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz agent-architecture-tutor`.*

## What this actually is

"Agent architecture" is the set of design decisions that separate a chatbot
wrapper around an LLM from a system that can be trusted with real work:
where does state live, what can the model actually call, who checks its
output, and what happens when a step fails. None of these questions are
about prompting — they're about the code and infrastructure *around* the
model. A well-architected agent system makes the model's job narrow (reason
and choose) and keeps everything else — arithmetic, authorization, retries,
audit — in deterministic code the model cannot silently override.

This repository's answer to "how much agent do you actually need" is layered:
a single Deep Agent for simple cases, a supervisor-with-specialists hierarchy
when a task genuinely splits into independent domains, and a second, separate
supervisor when the domains involved are different enough that mixing them
into one hierarchy would blur their tool boundaries. The architecture is not
one pattern reused everywhere — it's a small set of patterns applied where
each one earns its complexity.

## Core concepts

- **Workflow vs. agent.** A workflow is a fixed sequence of steps; an agent
  decides its own next step from a set of options. This repository uses
  agents only where the next step genuinely depends on the model's judgment
  (which specialist to delegate to) and deterministic code everywhere else
  (the specialist's actual calculations).
- **Supervisor / sub-agent pattern.** One orchestrator agent that does not
  itself compute anything, delegating to narrower specialist agents that each
  own one domain and one tool set.
- **Context boundary.** What information a given agent invocation actually
  sees. A narrower, explicitly-chosen context is both cheaper and safer than
  handing everything to every call by default.
- **Tool contract.** A machine-checkable description of a tool's inputs and
  outputs (a JSON Schema), checked before/after the call — not just documented
  in a prompt, which a model can ignore or misremember.
- **Checkpoint / interrupt / resume.** A durable snapshot of an in-progress
  run that lets execution pause (for human approval) and later continue from
  exactly where it left off, rather than re-running from scratch.
- **Dead letter.** An explicit, structured failure result returned instead of
  either crashing the whole run or letting the model quietly fabricate an
  answer when a tool call is exhausted or malformed.
- **Least-context principle.** Give an agent only the named sources a specific
  task needs, not everything available, so an over-broad context can't leak
  data the task never asked for.

## When not to use an agent

Anthropic's
[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)
opens its guidance with restraint: "we recommend finding the simplest
solution possible, and only increasing complexity when needed. This might
mean not building agentic systems at all. Agentic systems often trade
latency and cost for better task performance." And when more is warranted,
"workflows offer predictability and consistency for well-defined tasks,
whereas agents are the better option when flexibility and model-driven
decision-making are needed at scale."

Three questions settle most cases before any framework is chosen:

1. **Are the steps known in advance?** Then write them as code. Pricing a
   bond, computing a drawdown, and applying a policy are workflows, and
   this repository keeps them in `src/analytics/` and `src/control/`.
2. **Does one model call with the right context answer it?** Then a single
   call, with retrieval, beats a loop.
3. **Does the next step genuinely depend on what the last one found?** Only
   then is an agent loop worth its latency, cost, and non-determinism.

## Multi-agent: what the evidence says

The case for several agents is real and conditional. Anthropic's
[multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
reports that a lead agent with subagents "outperformed single-agent Claude
Opus 4 by 90.2%" on its research evaluation. It also reports the price:
"agents typically use about 4× more tokens than chat interactions, and
multi-agent systems use about 15× more tokens than chats", and on its
browsing evaluation "token usage by itself explains 80% of the variance" in
performance. So multi-agent systems "require tasks where the value of the
task is high enough to pay for the increased performance", and they suit
"heavy parallelization, information that exceeds single context windows,
and interfacing with numerous complex tools". They fit poorly where tasks
"require all agents to share the same context or involve many dependencies
between agents", which includes "most coding tasks".

Cognition's [Don't build multi-agents](https://cognition.com/blog/dont-build-multi-agents)
makes the opposing case from the same facts. Its principles are "share
context, and share full agent traces, not just individual messages" and
"actions carry implicit decisions, and conflicting decisions carry bad
results". Split a game clone between two subagents that cannot see each
other's work, and one builds a background from the wrong game while the
other builds a bird that matches neither.

The two are compatible once you ask what the subtasks share. This
repository's Portfolio Manager splits a question into macro, quant, and
fundamental work that can be done independently, and the orchestrator
alone makes the decisions that must be consistent: which specialists to
ask, what data each needs (restated in the `task` description, because
contexts are isolated), and the synthesis. Where the domains differ enough
to blur tool boundaries, ADR 0018 adds a second supervisor rather than
widening the first.

## Context budget design

Context is a budget, not a container. Anthropic's
[context-engineering article](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
describes an "attention budget" and sets the goal as the "smallest possible
set of high-signal tokens that maximize the likelihood of some desired
outcome". Its long-horizon techniques each spend the budget differently:

- **Sub-agents** do focused work in their own context and "return only a
  condensed, distilled summary of its work (often 1,000-2,000 tokens)", so
  the coordinator's context grows by summaries, not transcripts.
- **Compaction** summarises a conversation near its limit and continues from
  the summary.
- **Structured notes** move state out of the context into files the agent
  reads back when it needs them.
- **Just-in-time retrieval** keeps references in context and loads the data
  through tools on demand, slower than pre-loading and far cheaper.

This repository's version is `build_filtered_context()`: every call names the
sources it needs, and `build_full_context()` survives only as the measured
overload baseline.

## How this repository implements it

`src/context/builder.py` is the single point where prompt context gets
assembled. `CONTEXT_SOURCE_ORDER` names exactly seven sources
(`user_role`, `portfolio_state`, `market_data`, `retrieved_research`,
`memory`, `tool_outputs`, `skills`). `build_full_context()` requires and
renders all seven verbatim — this is a *measured* baseline (see
`docs/learning/comparison-notes.md`), not the recommended default.
`build_filtered_context()` instead takes an explicit allowlist, so an omitted
source never leaks into a prompt by accident; every source that does appear
had to be named on purpose.

`src/agents/multi_agent.py`'s `create_multi_agent()` builds the Portfolio
Manager orchestrator. The orchestrator is bound only the native Deep Agents
`task` delegation tool — never the underlying analytics tools directly — and
delegates to `specialist_subagents()`, which returns three specialists
(macro, quant, fundamental), each with its own system prompt and its own
narrow tool tuple (`MACRO_TOOLS`, `QUANT_TOOLS`, `FUNDAMENTAL_TOOLS`). Compare
this with `src/agents/investment_research.py`, a *second*, separate
supervisor (documented in `docs/adr/0018-research-supervisor-pattern.md`)
over Quantitative Analysis, News/Research, and Smart Summarizer specialists.
The existence of two supervisors rather than one enlarged hierarchy is itself
an architectural decision: research and portfolio-management are different
enough domains that merging their specialists into one orchestrator would
blur tool boundaries and make authorization harder to reason about.

Failure handling lives in `src/agents/recovery.py`. `ContractValidationMiddleware`
checks a tool's actual input/output against `contracts/tools/<tool_name>.schema.json`
when that contract file exists — note it silently passes through when no
contract is found, so a new tool without a contract gets no validation until
one is added. `ModelRetryMiddleware`/`ToolRetryMiddleware` only retry the
exceptions listed in `RETRYABLE_EXCEPTIONS` (timeouts and rate limits — not
arbitrary errors), and `ToolCallLimitMiddleware` caps the number of calls per
run so a stuck loop can't retry forever. When retries are exhausted or a
result is malformed, the middleware returns `dead_letter_payload()` (from
`src/observability/telemetry.py`) — an explicit, structured failure the
caller can detect, instead of a crash or a model-invented answer standing in
for a real one.

## Worked walkthrough

1. Read `src/agents/multi_agent.py`'s `specialist_subagents()` — note how it
   builds three `SubAgent` dicts and, for `"quant"` only, attaches
   `spec["skills"] = ["./skills/scenario-analysis/"]`.
2. Run the real multi-agent test suite:
   ```bash
   uv run pytest tests/unit/agents/test_multi_agent.py -q
   ```
3. Open `tests/unit/agents/test_failure_recovery.py` and find the test that
   crashes the Quant specialist mid-run, then resumes — this is the concrete,
   tested version of the "design a retry/checkpoint/resume strategy" practice
   example above; compare invocation counts before and after resume.
4. Trace one context-assembly call: construct a small `ContextSources` dict
   missing one of the seven required keys and call `build_full_context()` —
   confirm it raises rather than silently proceeding with a gap.
5. Grep `contracts/tools/` for which tools currently have a schema file and
   which don't, and explain what `ContractValidationMiddleware` does for a
   tool call in each case.

## Common pitfalls

- **Letting the model decide authorization.** Nothing about which portfolio
  or tool a caller may access is ever inferred from agent reasoning or a
  skill's stated intent — that's `governance/policies/` (Cedar) and the
  tool-boundary re-check, evaluated before the model ever sees a request and
  again at the API/MCP boundary. An agent that "decides" access is an agent
  with a security bug.
- **Defaulting to full context "for simplicity."** `build_full_context()`
  exists as a measured overload baseline specifically *because* someone
  measured it and found it worse (more tokens, no better answers) than a
  chosen allowlist — see the token-cost comparison in
  `docs/learning/comparison-notes.md`. Reaching for it as the easy default
  reintroduces the exact problem it was built to document.
- **Retrying without a ceiling.** An unbounded retry loop on a genuinely
  broken tool doesn't recover, it just burns time and money before failing
  anyway. `ToolCallLimitMiddleware`'s per-run ceiling and the explicit
  `dead_letter` result exist so a failure surfaces quickly and legibly
  instead of hanging.
- **Reaching for multi-agent because the task is important.** The published
  gains come with about fifteen times the tokens of a chat, and they appear
  on parallel, breadth-first work. For tightly coupled work, one agent with
  good context is usually better.
- **Splitting work whose parts make decisions for each other.** Two agents
  that cannot see each other's choices produce parts that do not fit. Keep
  those decisions in one place.
- **Returning transcripts instead of summaries.** A specialist that hands
  its whole working context back spends the coordinator's budget on detail
  the coordinator does not need.

## The four threads

| Thread | In the architecture | Evidence |
|---|---|---|
| **Observability** | Every agent in a hierarchy emits spans into one provider, so a delegated specialist's work nests under the orchestrator's trace instead of starting its own. Multi-agent cost is visible only if tokens are recorded per agent. | `configure_telemetry()` in `src/observability/telemetry.py` |
| **Traceability** | The orchestrator's `task` descriptions are the only channel into a specialist, which makes them the record of what each specialist was told. | `create_multi_agent()` and `specialist_subagents()` in `src/agents/multi_agent.py` |
| **Governance** | Each specialist gets its own narrow tool tuple and the orchestrator gets none, so splitting work never widens what any one agent may do. | `tests/unit/agents/test_multi_agent.py::test_specialists_have_domain_specific_tool_boundaries` |
| **Evaluation** | An architecture choice is a claim about cost and quality, so it is settled by measurement: the full-versus-filtered context comparison, and pass rates over repeated trials, not a demo. | `docs/learning/comparison-notes.md` |

## Further reading

- [`docs/reference/REFERENCES.md#agent-harnesses-skills-prompts-and-custom-agents`](../../reference/REFERENCES.md#agent-harnesses-skills-prompts-and-custom-agents)
- `docs/adr/0018-research-supervisor-pattern.md` — why a second supervisor,
  not a bigger first one.
- `docs/architecture/ARCHITECTURE.md`'s "Multi-agent orchestration" and
  "Failure and recovery" sections for the canonical current-state diagrams.
- `docs/learning/comparison-notes.md` for the Day 4 full-vs-filtered-context
  token measurements referenced above.
