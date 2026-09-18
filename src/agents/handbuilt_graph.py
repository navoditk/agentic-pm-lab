"""The same delegation, built from LangGraph primitives instead of Deep Agents.

`multi_agent.py` calls `create_deep_agent(...)` and gets a compiled graph
back. That is the right choice for the production path — but it means the
graph itself is never visible, and a reader of this repository could finish
it knowing Deep Agents well and LangGraph barely.

This module builds the *same shape* by hand: classify a question, route it to
one of three specialists with non-overlapping tools, collect findings,
synthesise. Reading the two side by side is the point — everything explicit
here is something `create_deep_agent` generated for you.

It is deliberately **model-free**. Classification is keyword-based and the
specialists call the real deterministic analytics directly, so the graph runs
in a unit test with no network, no API key, and no sampling noise. That is a
teaching decision, not a shortcut: an LLM in the loop would make the graph
mechanics the least interesting thing on screen. Nothing here is on the
production path, and `multi_agent.py` remains the agent that actually runs.

What this makes visible that Deep Agents hides:

- **State schema** — an explicit `TypedDict`, and a reducer that decides what
  happens when two nodes write the same key.
- **Nodes** — plain functions from state to a state update. No magic.
- **Edges** — including a *conditional* edge, which is the routing decision
  Deep Agents performs inside its `task` tool.
- **Compilation** — `.compile()` turning a graph definition into something
  runnable, optionally with a checkpointer.

**Not a template for a real agent.** The specialists here call the analytics
directly. `multi_agent.py` never does that: it passes every tool through
`tools_for_identity(identity, tools)` so the Control Layer filters by
entitlement before the agent can see it. That is omitted here on purpose, to
keep the graph mechanics the only thing on screen — but it is exactly the
line you must not drop when building something real, and
`src/control/authorization.py` is where the enforcement actually lives.
"""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.analytics.portfolio import portfolio_summary
from src.analytics.risk import risk_metrics
from src.analytics.scenario import scenario_analysis

Specialist = Literal["macro", "quant", "fundamental"]


class ResearchState(TypedDict):
    """The graph's state schema.

    `findings` carries `operator.add` as its reducer. Without it, a second
    node writing `findings` would *replace* the first node's value rather
    than appending to it — the single most common LangGraph surprise, and the
    reason a fan-out pattern silently loses all but one branch. With it, the
    key accumulates. Keys with no reducer (`question`, `route`, `answer`)
    use last-write-wins, which is what you want for a scalar.
    """

    question: str
    route: Specialist
    findings: Annotated[list[str], operator.add]
    answer: str


MACRO_TERMS = ("rate", "curve", "duration", "yield", "macro", "shock")
QUANT_TERMS = ("risk", "volatility", "drawdown", "factor", "optimi", "backtest")

# Fixture inputs, so the graph runs with no network and no portfolio store.
# Real analytics, mock data -- the same boundary `multi_agent.py` observes.
FIXTURE_RETURNS = (0.02, -0.04, 0.03, 0.04)
FIXTURE_VALUES = (100.0, 102.0, 98.0, 101.0, 105.0)
FIXTURE_POSITIONS = (
    {"security_id": "MOCK-RATES", "market_value": 600.0},
    {"security_id": "MOCK-CREDIT", "market_value": 400.0},
)
FIXTURE_SECURITY_MASTER = (
    {"security_id": "MOCK-RATES", "asset_class": "rates", "sector": "government"},
    {
        "security_id": "MOCK-CREDIT",
        "asset_class": "credit",
        "sector": "investment_grade",
    },
)


def classify(state: ResearchState) -> dict[str, Specialist]:
    """Pick one specialist. Deep Agents does this inside its `task` tool.

    Keyword matching, not a model — see the module docstring. The interesting
    part is not how the decision is made but that the decision is a *node*
    whose output the next edge reads.
    """
    question = state["question"].lower()
    if any(term in question for term in MACRO_TERMS):
        return {"route": "macro"}
    if any(term in question for term in QUANT_TERMS):
        return {"route": "quant"}
    return {"route": "fundamental"}


def route_to_specialist(state: ResearchState) -> Specialist:
    """The conditional edge's path function.

    It returns a *name*, and the mapping passed to `add_conditional_edges`
    turns that name into the next node. Keeping the decision (`classify`) and
    the routing (this) separate is what makes the decision inspectable in the
    state — a single combined step would hide `route` from every later node.
    """
    return state["route"]


def macro_node(state: ResearchState) -> dict[str, list[str]]:
    """Macro specialist: a rates shock. Non-overlapping tools, as upstream."""
    result = scenario_analysis(
        [{"security_id": "MOCK-1", "weight": 1.0, "duration": 6.0}],
        "rates",
        100,
    )
    impact = result["portfolio_return_impact"]
    return {"findings": [f"macro: a 100bp rates shock moves the book {impact:.2%}"]}


def quant_node(state: ResearchState) -> dict[str, list[str]]:
    """Quant specialist: realised risk over a fixture series."""
    result = risk_metrics(
        FIXTURE_RETURNS,
        FIXTURE_VALUES,
        window=2,
    )
    return {"findings": [f"quant: max drawdown {result['max_drawdown']:.2%}"]}


def fundamental_node(state: ResearchState) -> dict[str, list[str]]:
    """Fundamental specialist: holdings exposure."""
    result = portfolio_summary(FIXTURE_POSITIONS, FIXTURE_SECURITY_MASTER)
    largest = result["largest_position_weight"]
    classes = len(result["exposure_by_asset_class"])
    return {
        "findings": [
            f"fundamental: {classes} asset classes, largest position {largest:.1%}"
        ]
    }


def synthesise(state: ResearchState) -> dict[str, str]:
    """Join the findings. The orchestrator's job, made explicit."""
    findings = state["findings"]
    if not findings:
        return {"answer": "No specialist produced a finding."}
    return {"answer": " | ".join(findings)}


def build_research_graph(
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Assemble and compile the graph.

    Compare with `multi_agent.py`'s `create_multi_agent()`, which is a single
    `create_deep_agent(...)` call. Everything below is what that call builds
    on your behalf: the nodes, the entry point, the conditional routing, the
    convergence onto a synthesis step, and the compile.
    """
    graph = StateGraph(ResearchState)

    graph.add_node("classify", classify)
    graph.add_node("macro", macro_node)
    graph.add_node("quant", quant_node)
    graph.add_node("fundamental", fundamental_node)
    graph.add_node("synthesise", synthesise)

    graph.add_edge(START, "classify")
    # The conditional edge: `route_to_specialist` returns a key, the mapping
    # turns it into a node. This is the delegation decision Deep Agents makes
    # invisibly when the orchestrator calls its `task` tool.
    graph.add_conditional_edges(
        "classify",
        route_to_specialist,
        {"macro": "macro", "quant": "quant", "fundamental": "fundamental"},
    )
    for specialist in ("macro", "quant", "fundamental"):
        graph.add_edge(specialist, "synthesise")
    graph.add_edge("synthesise", END)

    return graph.compile(checkpointer=checkpointer)


def run_research_graph(
    question: str,
    checkpointer: BaseCheckpointSaver | None = None,
    thread_id: str = "handbuilt-demo",
) -> ResearchState:
    """Invoke the graph once. `config` carries the thread a checkpointer keys on."""
    graph = build_research_graph(checkpointer)
    config = {"configurable": {"thread_id": thread_id}} if checkpointer else {}
    return graph.invoke(
        {"question": question, "findings": [], "route": "fundamental", "answer": ""},
        config=config,
    )
