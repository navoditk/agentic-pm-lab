"""The capstone's acceptance test: a decision rebuilt from one trace id.

Quiz questions in evals/tutor_quizzes/traceability-capstone-tutor.jsonl cite
these tests by name (`verified_by`). Nothing here leaves the process.
"""

import pytest
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from src.capstone.trace_lab import (
    HOPS,
    PRICING_SPAN,
    Stores,
    missing_hops,
    reconstruct,
    run_decision,
)
from src.control.audit import current_trace_id
from src.observability.telemetry import configure_telemetry


@pytest.fixture(scope="module")
def exporter():
    spans = InMemorySpanExporter()
    configure_telemetry().add_span_processor(SimpleSpanProcessor(spans))
    return spans


@pytest.fixture
def stores(exporter, tmp_path):
    exporter.clear()
    return Stores(
        spans=exporter,
        audit_log=tmp_path / "audit.jsonl",
        eval_log=tmp_path / "evals.jsonl",
        evidence_log=tmp_path / "evidence.jsonl",
    )


def test_a_fixture_decision_is_reconstructable_from_one_trace_id(stores):
    trace_id = run_decision(stores)
    record = reconstruct(trace_id, stores)
    assert missing_hops(record) == []
    assert record["tool"] == ["execute_tool interpolate_yield"]
    assert [r["decision"] for r in record["policy"]] == ["allowed"]
    [evidence] = record["evidence"]
    assert evidence["series_id"] == "DGS5" and evidence["eligible"] is True
    [evaluation] = record["evaluation"]
    assert evaluation["passed"] is True


def test_the_evaluation_record_carries_the_versions_a_replay_needs(stores):
    [evaluation] = reconstruct(run_decision(stores), stores)["evaluation"]
    assert set(evaluation["versions"]) == {"model", "prompt", "policy", "data"}


def test_dropping_the_context_at_one_hop_leaves_a_gap_and_orphans(stores):
    trace_id = run_decision(stores, propagate=False)
    record = reconstruct(trace_id, stores)
    assert missing_hops(record) == ["pricing"]
    # The pricing service still ran and still recorded: under another trace.
    [orphan] = [s for s in stores.spans.get_finished_spans() if s.name == PRICING_SPAN]
    assert f"{orphan.context.trace_id:032x}" != trace_id
    assert missing_hops(reconstruct(f"{orphan.context.trace_id:032x}", stores)) == [
        hop for hop in HOPS if hop != "pricing"
    ]


def test_a_record_written_after_the_span_ends_has_no_trace_id(exporter):
    """The id comes from the active context, so a record made once the
    request span has ended cannot be joined to the decision."""
    from opentelemetry import trace

    with trace.get_tracer("capstone").start_as_current_span("POST /decisions"):
        inside = current_trace_id()
    assert inside is not None
    assert current_trace_id() is None
