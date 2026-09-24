"""LangGraph's mechanics beyond the supervisor, model-free, for the LangGraph course.

`handbuilt_graph.py` shows the supervisor shape from primitives. This module
covers what a production graph also depends on: streaming, dynamic fan-out
with `Send`, subgraphs, time travel, and durable execution. Every graph here
is deterministic and runs offline, so the behaviour on screen is LangGraph's,
not a model's.

Each fact below was checked against the pinned LangGraph (1.2) and its
documentation, and is pinned by a test in
tests/unit/agents/test_graph_mechanics.py:

- Stream modes: `updates` emits each node's write, `values` the full state
  after each step, `custom` whatever a node emits through
  `get_stream_writer()`. With `subgraphs=True`, output arrives as
  `(namespace, data)` tuples naming the subgraph that produced it.
- `Send` starts one task per item, all in the same super-step. Their writes
  to a shared key need a reducer; without one LangGraph raises
  `InvalidUpdateError` rather than keeping one of them.
- Replay from a checkpoint skips the nodes before it and re-runs the nodes
  after it. `update_state` forks: it adds a checkpoint and never rewrites
  history.
- On resume after `interrupt()`, the node runs again from its first line, so
  anything before the interrupt must be idempotent.
- When one parallel node fails, the writes of the nodes that succeeded in
  that super-step are kept, and resuming re-runs only the failed one.
- Durability `exit` persists only when the run ends, so a crash mid-run
  leaves no intermediate checkpoint to resume from; `sync` and `async`
  persist every step.
"""

from __future__ import annotations

import operator
from collections import Counter
from typing import Annotated, Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send, interrupt

# --- fan-out with Send, and streaming ------------------------------------------


class ReviewState(TypedDict):
    issuers: list[str]
    notes: Annotated[list[str], operator.add]
    summary: str


class UnreducedReviewState(TypedDict):
    issuers: list[str]
    notes: list[str]
    summary: str


def _plan(state: dict) -> dict:
    return {}


def _one_review_per_issuer(state: dict) -> list[Send]:
    # Each Send carries its own input, not the whole state: the map step.
    return [Send("review", {"issuer": issuer}) for issuer in state["issuers"]]


def _review(task: dict) -> dict:
    # A progress event for anyone streaming with stream_mode="custom".
    get_stream_writer()({"reviewed": task["issuer"]})
    return {"notes": [f"{task['issuer']}: reviewed"]}


def _summarise(state: dict) -> dict:
    return {"summary": f"{len(state['notes'])} issuers reviewed"}


def credit_review_graph(
    *, reducer: bool = True, checkpointer: BaseCheckpointSaver | None = None
):
    """Plan, fan out one review per issuer, then summarise (map-reduce)."""
    graph = StateGraph(ReviewState if reducer else UnreducedReviewState)
    graph.add_node("plan", _plan)
    graph.add_node("review", _review)
    graph.add_node("summarise", _summarise)
    graph.add_edge(START, "plan")
    graph.add_conditional_edges("plan", _one_review_per_issuer, ["review"])
    graph.add_edge("review", "summarise")
    graph.add_edge("summarise", END)
    return graph.compile(checkpointer=checkpointer)


# --- subgraphs --------------------------------------------------------------------


class DeskState(TypedDict):
    exposure: float


def desk_graph():
    """A parent graph with a compiled subgraph added as a node.

    Adding the subgraph directly works because both share the `exposure` key.
    With different schemas you would call the subgraph from a node and map
    state in and out.
    """
    limits = StateGraph(DeskState)
    limits.add_node("cap", lambda s: {"exposure": min(s["exposure"], 100.0)})
    limits.add_edge(START, "cap")
    limits.add_edge("cap", END)

    desk = StateGraph(DeskState)
    desk.add_node("limits", limits.compile())
    desk.add_edge(START, "limits")
    desk.add_edge("limits", END)
    return desk.compile()


# --- time travel ------------------------------------------------------------------


class PipelineState(TypedDict):
    value: int


def pipeline_graph(calls: Counter, checkpointer: BaseCheckpointSaver):
    """load -> price -> report, counting how often each node runs."""

    def step(name: str, update):
        def node(state: dict) -> dict:
            calls[name] += 1
            return {"value": update(state["value"])}

        return node

    graph = StateGraph(PipelineState)
    graph.add_node("load", step("load", lambda v: v + 1))
    graph.add_node("price", step("price", lambda v: v * 10))
    graph.add_node("report", step("report", lambda v: v))
    graph.add_edge(START, "load")
    graph.add_edge("load", "price")
    graph.add_edge("price", "report")
    graph.add_edge("report", END)
    return graph.compile(checkpointer=checkpointer)


# --- durable execution --------------------------------------------------------------


class ApprovalState(TypedDict):
    trade: str
    approved: bool


def approval_graph(effects: list[str], checkpointer: BaseCheckpointSaver):
    """One node that records a side effect, then pauses for a human.

    `effects` is appended to before the interrupt, so a test can count how
    often that code runs.
    """

    def request_approval(state: dict) -> dict:
        effects.append(f"notified desk about {state['trade']}")
        decision = interrupt({"approve": state["trade"]})
        return {"approved": bool(decision)}

    graph = StateGraph(ApprovalState)
    graph.add_node("request_approval", request_approval)
    graph.add_edge(START, "request_approval")
    graph.add_edge("request_approval", END)
    return graph.compile(checkpointer=checkpointer)


class ParallelState(TypedDict):
    results: Annotated[list[str], operator.add]


def parallel_pricing_graph(
    calls: Counter, failing: set[str], checkpointer: BaseCheckpointSaver
):
    """Two pricers in one super-step; any named in `failing` raises."""

    def pricer(name: str):
        def node(state: dict) -> dict[str, Any]:
            calls[name] += 1
            if name in failing:
                raise RuntimeError(f"{name} feed unavailable")
            return {"results": [name]}

        return node

    graph = StateGraph(ParallelState)
    for name in ("rates", "credit"):
        graph.add_node(name, pricer(name))
        graph.add_edge(START, name)
        graph.add_edge(name, END)
    return graph.compile(checkpointer=checkpointer)
