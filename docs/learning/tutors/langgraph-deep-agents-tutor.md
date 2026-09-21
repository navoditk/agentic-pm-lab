# LangGraph and Deep Agents — deep dive

*Companion to [`.github/agents/langgraph-deep-agents-tutor.agent.md`](../../../.github/agents/langgraph-deep-agents-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz langgraph-deep-agents-tutor`.*

## What this actually is

LangGraph models an agent as a graph: nodes do work, edges route between
them, and a checkpointer can snapshot the graph's state at any point so
execution can pause and later resume from exactly there. Deep Agents is a
library built on top of LangGraph that provides a ready-made supervisor
pattern — a coordinator agent with a `task` tool that hands work off to named
sub-agents — so you don't hand-wire the graph nodes and edges for that
specific, common shape yourself.

The distinction that matters most for this repository: a LangGraph *node*
should never do arithmetic. Its job is state, routing, and delegation. Every
number in a response has to come from a deterministic function under
`src/analytics/`, called as a *tool*, not computed by the model inside a
node. This is the same architectural boundary the agent-architecture tutor
describes, viewed from the graph-mechanics side rather than the
supervisor-design side.

## Core concepts

- **Graph, node, edge.** The graph is the whole agent; nodes are units of
  work (a model call, a tool call, a delegation); edges determine what runs
  next, which can depend on the previous node's output.
- **State.** The data that persists and threads through the graph as it
  executes — in Deep Agents' supervisor pattern, this includes the running
  message history each specialist and the orchestrator sees.
- **Checkpointer.** A pluggable store (`BaseCheckpointSaver`) that persists
  graph state so a run can be paused and resumed later, potentially after a
  process restart, without losing completed work.
- **Interrupt.** A configured pause point — the graph halts before a
  specific tool executes and waits for an external signal (typically human
  approval) before continuing.
- **Delegation via `task`.** Deep Agents' native mechanism for a supervisor
  to hand work to a named sub-agent: the supervisor calls a `task` tool with
  a `subagent_type` and a task description; the sub-agent runs in its own,
  isolated context.
- **Isolated context.** A sub-agent does not automatically see the
  supervisor's full conversation — only what the `task` call's description
  explicitly includes. This is why a task description has to restate any
  data the sub-agent needs, verbatim.
- **State schema and reducers.** The graph's state is a `TypedDict`, and a
  key may carry a *reducer* that decides what happens when more than one
  node writes it. Without one you get two different failures depending on
  *when* the writes happen. Sequentially — one node after another — the last
  write wins and earlier values are silently discarded. Concurrently, where a
  fan-out has two branches writing the same key in one step, LangGraph does
  not pick a winner at all: it raises `InvalidUpdateError` ("can receive only
  one value per step"). The silent case is the one that costs you a
  debugging session; the loud case is the one people expect to be silent and
  are surprised by. `Annotated[list[str], operator.add]` resolves both by
  telling the graph how to combine writes. Deep Agents manages its own
  message state, so you only meet this when you build a graph yourself.
- **Conditional edge.** An edge whose target is chosen at runtime by a path
  function reading state. This is the routing decision Deep Agents performs
  *inside* its `task` tool — same choice, made invisibly rather than by an
  edge you declared.

## How this repository implements it

`src/agents/multi_agent.py`'s `create_multi_agent()` builds the Portfolio
Manager as a Deep Agent whose *only* delegation mechanism is the native
`task` tool over `specialist_subagents()` — macro, quant, fundamental. The
orchestrator itself is never bound the underlying analytics tools; only its
specialists are, and each specialist gets a distinct, non-overlapping tuple
(`MACRO_TOOLS`, `QUANT_TOOLS`, `FUNDAMENTAL_TOOLS`). Because each specialist
runs in an isolated context window, the orchestrator's prompt explicitly
requires copying the relevant named-source data into each `task` description
— nothing is implicitly shared.

`create_checkpointed_multi_agent()` wires an `InMemorySaver`
(`langgraph.checkpoint.memory`) as the `BaseCheckpointSaver` — explicitly a
development-only choice; a durable checkpointer is a stated prerequisite
before real deployment, since an in-memory store loses all state on process
restart. `interrupt_on` — a `Mapping[str, bool | dict]` passed into
`create_multi_agent()` — is how `run_backtest` is configured to pause: the
graph halts *before* that tool executes, and only `resume_multi_agent()` can
continue it. Critically, `resume_multi_agent()` continues the *checkpointed
state*, not the original input — an already-completed specialist's result is
preserved and not silently re-run. This was exercised directly: crashing the
Quant specialist after Macro had already completed changed the observed
invocation counts from `macro=1, quant=1` (failure) to `macro=1, quant=2`
after resume — Macro's completed work was never redone.

`src/agents/recovery.py`'s `ContractValidationMiddleware` and the
`specialist_recovery_middleware()`/`orchestrator_recovery_middleware()`
factories wrap tool calls at the graph-node level with retry/backoff
(bounded by `RETRYABLE_EXCEPTIONS` and `ToolCallLimitMiddleware`), converting
an exhausted or malformed result into `dead_letter_payload()` rather than
either crashing the graph or letting a node's output stand in for a real
tool result.

### Reading the abstraction: `handbuilt_graph.py`

`create_deep_agent(...)` is one call that returns a compiled graph, which is
excellent for building and unhelpful for learning — the graph is never
visible. `src/agents/handbuilt_graph.py` builds the *same shape* from
primitives so the two can be read side by side: classify, route to one of
three specialists, collect findings, synthesise.

It is deliberately model-free. Classification is keyword matching and the
specialists call the real deterministic analytics, so the whole graph runs in
a unit test with no network and no API key. An LLM in the loop would make the
graph mechanics the least interesting thing on screen. Nothing in it is on
the production path.

Line up the two and the abstraction becomes concrete:

| Explicit in `handbuilt_graph.py` | Who does it in `multi_agent.py` |
|---|---|
| `StateGraph(ResearchState)` and a `TypedDict` schema | Deep Agents, over its own message state |
| `graph.add_node(...)` for each specialist | the `subagents=` list |
| `add_conditional_edges` plus a path function | the orchestrator calling `task` with a `subagent_type` |
| `graph.add_edge(specialist, "synthesise")` | the supervisor resuming after a `task` returns |
| `graph.compile(checkpointer=...)` | `create_checkpointed_multi_agent()` |

The reducer is the part worth dwelling on, because it is the one that bites.
`findings` is annotated `Annotated[list[str], operator.add]`. Drop that
annotation and a second node writing `findings` replaces the first node's
value rather than appending — a fan-out that looks like it worked and
returned one branch's results.
`tests/unit/agents/test_handbuilt_graph.py` asserts both behaviours against
two real graphs rather than describing the difference, so the failure mode is
executable rather than a warning you have to take on trust.

## Worked walkthrough

1. Read `src/agents/multi_agent.py`'s `create_checkpointed_multi_agent()` and
   note exactly what `InMemorySaver` gives you and what it doesn't (state
   only survives within the same process).
2. Run the resume-after-crash test directly:
   ```bash
   uv run pytest tests/unit/agents/test_failure_recovery.py -q
   ```
   and read the test that asserts the `macro=1, quant=1` → `macro=1, quant=2`
   invocation-count change described above.
3. Find `DEFAULT_INTERRUPT_ON` in `src/agents/multi_agent.py` and confirm
   `run_backtest` is the only tool configured to pause by default — explain
   why a pricing or volatility tool is not.
4. Compare `specialist_subagents()`'s three independent specialist
   definitions with a hand-built LangGraph graph that hard-codes three nodes
   and conditional edges between them — list what `create_multi_agent()`'s
   `task`-based delegation gives you "for free" (isolated context per
   sub-agent, a uniform delegation tool, no hand-wired edges) and what a
   hand-built graph would have to reimplement itself.
5. Read `docs/learning/comparison-notes.md`'s account of the Day 5 local-model
   (Qwen3 4B) run that returned empty without delegating at all — explain
   which middleware in `src/agents/recovery.py` would catch a similarly
   silent failure today, and which parts (the model simply not calling
   `task`) no middleware can force.

## Common pitfalls

- **Doing arithmetic inside a graph node.** A node's job is state, routing,
  and delegation — never computing a number itself. Any request that a model
  "just calculate" volatility, drawdown, or a price inline should be
  redirected to the matching `src/analytics/` function, called as a tool.
- **Letting a sub-agent inherit every parent tool automatically.**
  `specialist_subagents()` binds each specialist only its own domain's tool
  tuple; the orchestrator itself gets none of the analytics tools directly.
  An architecture where sub-agents inherit everything defeats the purpose of
  having named, narrow tool sets in the first place.
- **Treating text as approval.** A message in the model's context that says
  "approved" is not what resumes a paused `run_backtest` call. Only the
  `interrupt_on`/checkpoint control state, resumed explicitly through
  `resume_multi_agent()`, constitutes approval — the graph's actual paused
  state is the source of truth, not anything the model said about it.

## Further reading

- [`docs/reference/REFERENCES.md#langgraph--langgraph-deep-agents`](../../reference/REFERENCES.md#langgraph--langgraph-deep-agents)
- `docs/architecture/ARCHITECTURE.md`'s "Multi-agent orchestration (Day 5)"
  and "Failure and recovery (Day 5)" sections.
- `docs/learning/comparison-notes.md` for the Day 4/5 local-vs-cloud-model
  comparison, including the Qwen3 4B failure mode referenced above.
