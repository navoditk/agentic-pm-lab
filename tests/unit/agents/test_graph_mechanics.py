"""LangGraph mechanics the LangGraph course teaches, run rather than described.

Quiz questions in evals/tutor_quizzes/langgraph-deep-agents-tutor.jsonl cite
these tests by name (`verified_by`). Every graph is model-free, so what each
test observes is LangGraph's behaviour.
"""

from collections import Counter

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import InvalidUpdateError
from langgraph.types import Command

from src.agents.graph_mechanics import (
    approval_graph,
    credit_review_graph,
    desk_graph,
    parallel_pricing_graph,
    pipeline_graph,
)

ISSUERS = {"issuers": ["ACME", "GLOBEX"], "notes": [], "summary": ""}


def thread(name):
    return {"configurable": {"thread_id": name}}


# --- streaming -------------------------------------------------------------------


def test_updates_mode_streams_each_write_and_values_mode_the_full_state():
    graph = credit_review_graph()
    updates = list(graph.stream(ISSUERS, stream_mode="updates"))
    # One entry per node write, and each fanned-out review is its own entry.
    assert [next(iter(u)) for u in updates] == ["plan", "review", "review", "summarise"]
    final = list(graph.stream(ISSUERS, stream_mode="values"))[-1]
    assert final["summary"] == "2 issuers reviewed" and len(final["notes"]) == 2


def test_custom_mode_streams_what_a_node_emits_through_the_stream_writer():
    events = list(credit_review_graph().stream(ISSUERS, stream_mode="custom"))
    assert sorted(e["reviewed"] for e in events) == ["ACME", "GLOBEX"]


def test_subgraph_output_is_namespaced_only_when_asked():
    graph = desk_graph()
    assert list(graph.stream({"exposure": 250.0}, stream_mode="updates")) == [
        {"limits": {"exposure": 100.0}}
    ]
    nested = list(
        graph.stream({"exposure": 250.0}, stream_mode="updates", subgraphs=True)
    )
    namespaces = [namespace for namespace, _ in nested]
    assert namespaces[0][0].startswith("limits:")  # from inside the subgraph
    assert namespaces[-1] == ()  # the parent graph


# --- Send fan-out and reducers -------------------------------------------------------


def test_send_fans_out_one_task_per_item_in_one_super_step():
    graph = credit_review_graph(checkpointer=InMemorySaver())
    graph.invoke(ISSUERS, thread("fan-out"))
    steps = [s.next for s in graph.get_state_history(thread("fan-out"))]
    assert ("review", "review") in steps  # both reviews were pending together


def test_concurrent_writes_without_a_reducer_raise_rather_than_pick_one():
    with pytest.raises(InvalidUpdateError, match="one value per step"):
        credit_review_graph(reducer=False).invoke(ISSUERS)


# --- time travel ----------------------------------------------------------------------


def test_replay_skips_nodes_before_the_checkpoint_and_reruns_those_after():
    calls = Counter()
    graph = pipeline_graph(calls, InMemorySaver())
    graph.invoke({"value": 1}, thread("t"))
    before_price = next(
        s for s in graph.get_state_history(thread("t")) if s.next == ("price",)
    )
    assert graph.invoke(None, before_price.config) == {"value": 20}
    assert calls == Counter(load=1, price=2, report=2)


def test_update_state_forks_instead_of_rewriting_history():
    calls = Counter()
    graph = pipeline_graph(calls, InMemorySaver())
    graph.invoke({"value": 1}, thread("t"))
    history = list(graph.get_state_history(thread("t")))
    before_price = next(s for s in history if s.next == ("price",))
    fork = graph.update_state(before_price.config, {"value": 100})
    assert graph.invoke(None, fork) == {"value": 1000}
    after = list(graph.get_state_history(thread("t")))
    # The original run's checkpoints are all still there.
    original = {s.config["configurable"]["checkpoint_id"] for s in history}
    assert original < {s.config["configurable"]["checkpoint_id"] for s in after}


# --- durable execution -----------------------------------------------------------------


def test_a_resumed_node_reruns_from_its_first_line():
    effects: list[str] = []
    graph = approval_graph(effects, InMemorySaver())
    paused = graph.invoke({"trade": "T1", "approved": False}, thread("a"))
    assert paused["__interrupt__"][0].value == {"approve": "T1"}
    assert graph.invoke(Command(resume=True), thread("a"))["approved"] is True
    # The code before interrupt() ran on the first call and again on resume.
    assert effects == ["notified desk about T1"] * 2


def test_a_failed_parallel_branch_resumes_without_rerunning_its_sibling():
    calls, failing = Counter(), {"credit"}
    graph = parallel_pricing_graph(calls, failing, InMemorySaver())
    with pytest.raises(RuntimeError, match="credit feed unavailable"):
        graph.invoke({"results": []}, thread("p"))
    failing.clear()
    result = graph.invoke(None, thread("p"))
    assert sorted(result["results"]) == ["credit", "rates"]
    assert calls == Counter(rates=1, credit=2)  # rates' write was kept


@pytest.mark.parametrize(("durability", "checkpoints"), [("sync", 5), ("exit", 1)])
def test_exit_durability_keeps_no_intermediate_checkpoints(durability, checkpoints):
    graph = pipeline_graph(Counter(), InMemorySaver())
    graph.invoke({"value": 1}, thread(durability), durability=durability)
    assert len(list(graph.get_state_history(thread(durability)))) == checkpoints
