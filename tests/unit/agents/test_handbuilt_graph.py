"""The hand-built graph, tested as a contrast to the Deep Agents path.

These assert graph *mechanics* — routing, state accumulation, reducers,
checkpointing — because that is what the module exists to make visible.
Nothing here needs a model, which is the point: the graph runs offline, so
the primitives are observable without LLM noise in the way.
"""

import operator
from typing import Annotated, TypedDict

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from src.agents.handbuilt_graph import (
    ResearchState,
    build_research_graph,
    classify,
    route_to_specialist,
    run_research_graph,
    synthesise,
)

# --- routing -----------------------------------------------------------------


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("What happens to duration if rates move 100bp?", "macro"),
        ("How steep is the curve?", "macro"),
        ("What is our max drawdown?", "quant"),
        ("Run a backtest on that factor", "quant"),
        ("How many holdings do we have?", "fundamental"),
    ],
)
def test_classify_routes_to_the_right_specialist(question, expected):
    assert classify({"question": question})["route"] == expected


def test_fundamental_is_the_fallback_not_an_error():
    """An unmatched question still routes somewhere rather than dead-ending."""
    assert classify({"question": "zzzz"})["route"] == "fundamental"


def test_the_route_is_readable_from_state_after_the_run():
    """Why classify and route_to_specialist are separate functions.

    The decision lands in state, so a later node -- or a test, or an audit
    record -- can see which specialist was chosen. Folding the decision into
    the edge would make it invisible the moment it was taken.
    """
    state = run_research_graph("What is our max drawdown?")
    assert state["route"] == "quant"


def test_path_function_reads_the_decision_rather_than_recomputing_it():
    assert route_to_specialist({"route": "macro"}) == "macro"


# --- graph shape -------------------------------------------------------------


def test_graph_has_the_nodes_the_deep_agent_generates_invisibly():
    nodes = set(build_research_graph().get_graph().nodes)
    assert {"classify", "macro", "quant", "fundamental", "synthesise"} <= nodes


def test_every_specialist_converges_on_synthesise():
    """Three branches, one join -- the orchestrator's job, made explicit."""
    graph = build_research_graph().get_graph()
    targets = {
        e.target for e in graph.edges if e.source in {"macro", "quant", "fundamental"}
    }
    assert targets == {"synthesise"}


def test_only_one_specialist_runs_per_question():
    """A conditional edge selects a branch; it does not fan out to all three."""
    state = run_research_graph("What happens if rates move 100bp?")
    assert len(state["findings"]) == 1
    assert state["findings"][0].startswith("macro:")


# --- the reducer, which is the lesson ---------------------------------------


def test_findings_reducer_appends_rather_than_replaces():
    """`operator.add` on the annotation is what makes accumulation work.

    Built here as a standalone two-node graph so both nodes write the same
    key -- the research graph only ever runs one specialist, so it cannot
    demonstrate this on its own.
    """

    class Accumulating(TypedDict):
        findings: Annotated[list[str], operator.add]

    graph = StateGraph(Accumulating)
    graph.add_node("first", lambda s: {"findings": ["a"]})
    graph.add_node("second", lambda s: {"findings": ["b"]})
    graph.add_edge(START, "first")
    graph.add_edge("first", "second")
    graph.add_edge("second", END)

    result = graph.compile().invoke({"findings": []})
    assert result["findings"] == ["a", "b"]


def test_without_a_reducer_the_second_write_wins_and_the_first_is_lost():
    """The failure the annotation prevents, demonstrated rather than asserted.

    This is the most common LangGraph surprise: a fan-out that silently keeps
    only one branch. Same graph, no reducer.
    """

    class Overwriting(TypedDict):
        findings: list[str]

    graph = StateGraph(Overwriting)
    graph.add_node("first", lambda s: {"findings": ["a"]})
    graph.add_node("second", lambda s: {"findings": ["b"]})
    graph.add_edge(START, "first")
    graph.add_edge("first", "second")
    graph.add_edge("second", END)

    result = graph.compile().invoke({"findings": []})
    assert result["findings"] == ["b"], "no reducer means last write wins"


# --- synthesis and checkpointing ---------------------------------------------


def test_synthesise_joins_findings():
    assert synthesise({"findings": ["x", "y"]})["answer"] == "x | y"


def test_synthesise_says_so_when_there_is_nothing_rather_than_returning_empty():
    assert "No specialist" in synthesise({"findings": []})["answer"]


def test_compiling_with_a_checkpointer_persists_state_for_a_thread():
    """What `create_checkpointed_multi_agent()` does upstream, in miniature."""
    saver = InMemorySaver()
    graph = build_research_graph(saver)
    config = {"configurable": {"thread_id": "t1"}}

    graph.invoke(
        {
            "question": "max drawdown?",
            "findings": [],
            "route": "fundamental",
            "answer": "",
        },
        config=config,
    )
    snapshot = graph.get_state(config)

    assert snapshot.values["route"] == "quant"
    assert snapshot.values["findings"], "a checkpointer should retain the run's state"


def test_separate_threads_do_not_share_state():
    saver = InMemorySaver()
    graph = build_research_graph(saver)
    base = {"findings": [], "route": "fundamental", "answer": ""}

    graph.invoke(
        {**base, "question": "rates shock?"},
        config={"configurable": {"thread_id": "a"}},
    )
    graph.invoke(
        {**base, "question": "how many holdings?"},
        config={"configurable": {"thread_id": "b"}},
    )

    a = graph.get_state({"configurable": {"thread_id": "a"}}).values
    b = graph.get_state({"configurable": {"thread_id": "b"}}).values
    assert a["route"] == "macro"
    assert b["route"] == "fundamental"


def test_findings_use_real_analytics_not_hardcoded_strings():
    """Mock data, real computation -- the boundary multi_agent.py also keeps."""
    state = run_research_graph("What is our max drawdown?")
    assert "%" in state["findings"][0], "the figure should come from risk_metrics"


def test_state_schema_declares_the_keys_the_nodes_write():
    assert set(ResearchState.__annotations__) == {
        "question",
        "route",
        "findings",
        "answer",
    }
