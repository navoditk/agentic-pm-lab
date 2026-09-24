# LangGraph and Deep Agents — deep dive

*Companion to [`agents/langgraph-deep-agents-tutor.md`](../../../agents/langgraph-deep-agents-tutor.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz langgraph-deep-agents-tutor`.*

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
- **Super-step.** One round of the graph. "Nodes that run in parallel are
  part of the same super-step, while nodes that run sequentially belong to
  separate super-steps"
  ([graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)).
  A checkpoint is saved per super-step, which is why reducers, fan-out, and
  recovery are all described in terms of it.
- **`Send` fan-out.** A path function can return a list of `Send(node,
  input)` objects, starting one task per item with its own input: the map
  half of map-reduce, for a number of branches known only at run time. The
  branches run in one super-step, so a key they all write needs a reducer.
- **Subgraphs.** A compiled graph can be a node. Add it directly when parent
  and subgraph "share state keys"; call it from a node, mapping state in and
  out, when they have "different state schemas"
  ([subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)).
- **Streaming modes.** `stream_mode` chooses what a run emits as it goes:
  `values` is the "full state after each step", `updates` the "state updates
  after each step", `custom` is data a node emits through
  `get_stream_writer`, and `messages` streams LLM tokens. With
  `subgraphs=True`, output arrives as `(namespace, data)` tuples naming the
  subgraph ([streaming](https://docs.langchain.com/oss/python/langgraph/streaming)).
- **Time travel.** Every checkpoint on a thread can be revisited. Replaying
  from one means "nodes before the checkpoint are not re-executed" while
  "nodes after the checkpoint re-execute, including any LLM calls, API
  requests, and interrupts". `update_state` "does not roll back a thread. It
  creates a new checkpoint that branches from the specified point"
  ([time travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)).
- **Durable execution.** A checkpointed run survives failure in two ways.
  When one node fails in a super-step, "LangGraph stores pending checkpoint
  writes from any other nodes that completed successfully", so resuming
  does not re-run them. And the `durability` setting decides when state is
  written: `exit` "only when graph execution exits", `async` "while the next
  step executes", `sync` "before the next step starts"
  ([checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)).
- **Resuming an interrupt re-runs the node.** "The runtime restarts the
  entire node from the beginning—it does not resume from the exact line
  where interrupt was called", so side effects before `interrupt()` should
  be idempotent ([interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)).

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
annotation and a node that writes `findings` *after* another replaces its
value rather than appending, silently. Two nodes writing it in the *same*
super-step, as a fan-out does, fail loudly instead, with
`InvalidUpdateError`. `tests/unit/agents/test_handbuilt_graph.py` and
`test_concurrent_writes_without_a_reducer_raise_rather_than_pick_one` run
both cases against real graphs, so neither is a warning you have to take on
trust.

### Beyond the supervisor: `graph_mechanics.py`

`src/agents/graph_mechanics.py` holds five small, model-free graphs for the
mechanics a production graph depends on and the supervisor hides: a credit
review that fans out one `Send` per issuer, a desk graph with a limits
subgraph, a three-step pricing pipeline for time travel, an approval node
that interrupts, and two pricers that run in parallel. Each fact is pinned
by a test in `tests/unit/agents/test_graph_mechanics.py`:

| Mechanic | What the test shows |
|---|---|
| Streaming | `test_updates_mode_streams_each_write_and_values_mode_the_full_state`; `test_custom_mode_streams_what_a_node_emits_through_the_stream_writer`; `test_subgraph_output_is_namespaced_only_when_asked` |
| `Send` fan-out | `test_send_fans_out_one_task_per_item_in_one_super_step`; `test_concurrent_writes_without_a_reducer_raise_rather_than_pick_one` |
| Time travel | `test_replay_skips_nodes_before_the_checkpoint_and_reruns_those_after` (the pipeline's `load` runs once, `price` and `report` twice); `test_update_state_forks_instead_of_rewriting_history` |
| Durable execution | `test_a_resumed_node_reruns_from_its_first_line` (the desk is notified twice); `test_a_failed_parallel_branch_resumes_without_rerunning_its_sibling`; `test_exit_durability_keeps_no_intermediate_checkpoints` (one checkpoint instead of five) |

The resumed-node test is the one to remember. Deep Agents' `interrupt_on`
pauses inside a node too, so the same rule applies to the Portfolio
Manager's approval step: whatever runs before the pause runs again on
resume.

## The four threads

| Thread | In a LangGraph agent | Evidence |
|---|---|---|
| **Observability** | Streaming is a live feed for a caller: progress, partial state, tokens. It is not telemetry: it goes to whoever is iterating the stream and is gone afterwards. Latency, errors, and cost across runs still come from spans and metrics, as in the OpenTelemetry course. | `test_custom_mode_streams_what_a_node_emits_through_the_stream_writer` |
| **Traceability** | A thread's checkpoint history records the state after every super-step, which makes a run inspectable and replayable. It is state storage, not an audit log: `InMemorySaver` loses it on restart, `exit` durability never writes it, and forks add branches beside the original. | `test_update_state_forks_instead_of_rewriting_history`, `test_exit_durability_keeps_no_intermediate_checkpoints` |
| **Governance** | Approval is the checkpointed interrupt state resumed through `resume_multi_agent()`, never text in the model's context. And because a resumed node re-runs from its start, a notification or order placed before the pause would happen twice. | `test_a_resumed_node_reruns_from_its_first_line` |
| **Evaluation** | Graph behaviour is testable without a model: count node invocations to prove completed work was not redone, as the crash-and-resume test does, and replay from a checkpoint to re-run only the step under test. | `tests/unit/agents/test_failure_recovery.py`, `test_replay_skips_nodes_before_the_checkpoint_and_reruns_those_after` |

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
6. Run the mechanics tests:
   ```bash
   uv run pytest tests/unit/agents/test_graph_mechanics.py -q
   ```
   Before reading `test_replay_skips_nodes_before_the_checkpoint_and_reruns_those_after`,
   predict the call counts for `load`, `price`, and `report`.
7. Read `test_a_resumed_node_reruns_from_its_first_line`. Rewrite
   `approval_graph`'s node so the desk is notified exactly once, and say
   which of your two options survives a process restart.
8. Read `test_exit_durability_keeps_no_intermediate_checkpoints`. For a
   ten-minute backtest graph, choose a durability mode and defend it.

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
- **Side effects before `interrupt()`.** The node re-runs from its first
  line on resume, so a notification, an order, or a counter before the
  pause happens again. Move it after the interrupt, into its own node, or
  make it idempotent.
- **Expecting `update_state` to rewrite history.** It forks. The original
  checkpoints stay, and the next run continues from the fork.
- **`exit` durability on a long run.** It is the fastest mode, and a crash
  mid-run leaves nothing to resume from. Use it only where a rerun from the
  start is acceptable.
- **A fan-out without a reducer.** Branches in one super-step that write the
  same key raise `InvalidUpdateError`. Give the key a reducer.

## Further reading

- [`docs/reference/REFERENCES.md#langgraph--langgraph-deep-agents`](../../reference/REFERENCES.md#langgraph--langgraph-deep-agents)
- `docs/architecture/ARCHITECTURE.md`'s "Multi-agent orchestration (Day 5)"
  and "Failure and recovery (Day 5)" sections.
- `docs/learning/comparison-notes.md` for the Day 4/5 local-vs-cloud-model
  comparison, including the Qwen3 4B failure mode referenced above.
