"""Metrics, propagation and sampling — asserted against real SDK behaviour.

Every test here reads points back out of an `InMemoryMetricReader` or inspects
a real sampler, rather than asserting that a mock was called. A mock would
pass even if the instrument were never registered with a meter, which is
precisely the failure this module exists to prevent: the repository claimed
"traces and metrics" for a long time while recording no metrics at all.
"""

import pytest
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace.sampling import Decision, ParentBased
from opentelemetry.trace import SpanContext, TraceFlags, set_span_in_context

from src.observability import metrics as m
from src.observability.telemetry import (
    configured_sampler,
    extract_trace_context,
    inject_trace_context,
)


@pytest.fixture
def reader():
    """A fresh provider per test, so recorded points cannot leak between them."""
    m.reset_metrics_for_testing()
    reader = InMemoryMetricReader()
    m.configure_metrics(reader=reader)
    yield reader
    m.reset_metrics_for_testing()


def points(reader, name):
    """Return the data points recorded for one instrument."""
    data = reader.get_metrics_data()
    if data is None:
        return []
    found = []
    for resource_metric in data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == name:
                    found.extend(metric.data.data_points)
    return found


# --- instruments actually record ---------------------------------------------


def test_agent_run_records_a_count_and_a_duration(reader):
    m.record_agent_run(
        model="claude-sonnet-4", duration_seconds=1.25, success=True, agent="pm"
    )

    runs = points(reader, "app.agent.runs")
    assert len(runs) == 1
    assert runs[0].value == 1
    assert runs[0].attributes["outcome"] == "success"
    assert runs[0].attributes["agent"] == "pm"

    durations = points(reader, "app.agent.duration")
    assert len(durations) == 1
    assert durations[0].sum == pytest.approx(1.25)
    assert durations[0].count == 1


def test_failed_runs_are_labelled_not_dropped(reader):
    """An error rate needs both outcomes recorded under the same instrument."""
    m.record_agent_run(model="x", duration_seconds=0.1, success=True)
    m.record_agent_run(model="x", duration_seconds=0.2, success=False)

    outcomes = {
        p.attributes["outcome"]: p.value for p in points(reader, "app.agent.runs")
    }
    assert outcomes == {"success": 1, "error": 1}


def test_model_name_is_normalised_so_provider_prefixes_do_not_split_series(reader):
    """`anthropic:claude-x` and `claude-x` must aggregate as one model."""
    m.record_agent_run(model="anthropic:claude-x", duration_seconds=0.1, success=True)
    m.record_agent_run(model="claude-x", duration_seconds=0.1, success=True)

    models = {p.attributes["model"] for p in points(reader, "app.agent.runs")}
    assert models == {"claude-x"}


def test_tool_calls_are_labelled_by_tool(reader):
    m.record_tool_call(tool="price_bond", duration_seconds=0.01)
    m.record_tool_call(tool="price_bond", duration_seconds=0.02)
    m.record_tool_call(tool="optimize_portfolio", duration_seconds=0.5, success=False)

    by_tool = {
        (p.attributes["tool"], p.attributes["outcome"]): p.value
        for p in points(reader, "app.tool.calls")
    }
    assert by_tool == {("price_bond", "success"): 2, ("optimize_portfolio", "error"): 1}


def test_tokens_split_by_direction_so_cost_can_be_attributed(reader):
    m.record_token_usage(
        model="claude-x", input_tokens=1000, output_tokens=250, estimated_cost_usd=0.02
    )

    by_direction = {
        p.attributes["direction"]: p.value for p in points(reader, "app.llm.tokens")
    }
    assert by_direction == {"input": 1000, "output": 250}

    cost = points(reader, "app.llm.estimated_cost")
    assert len(cost) == 1 and cost[0].value == pytest.approx(0.02)


def test_zero_values_record_nothing_rather_than_a_zero_series(reader):
    """A model that reported no usage should not create an empty cost series."""
    m.record_token_usage(model="claude-x", input_tokens=0, output_tokens=0)
    assert points(reader, "app.llm.tokens") == []
    assert points(reader, "app.llm.estimated_cost") == []


def test_authorization_denials_are_counted_separately_from_errors(reader):
    """A denial is the control layer working, not a failure."""
    m.record_authorization_denial(reason="portfolio_not_entitled", role="analyst")

    denials = points(reader, "app.authorization.denials")
    assert len(denials) == 1
    assert denials[0].attributes["reason"] == "portfolio_not_entitled"
    assert points(reader, "app.agent.runs") == []


def test_negative_durations_are_clamped_rather_than_poisoning_the_histogram(reader):
    m.record_tool_call(tool="t", duration_seconds=-5.0)
    assert points(reader, "app.tool.duration")[0].sum == pytest.approx(0.0)


def test_configure_metrics_is_idempotent(reader):
    assert m.configure_metrics() is m.configure_metrics()


# --- propagation -------------------------------------------------------------


def test_inject_writes_a_w3c_traceparent_when_a_span_is_active():
    from opentelemetry import trace

    from src.observability.telemetry import configure_telemetry

    configure_telemetry()
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("outbound"):
        carrier = inject_trace_context()

    assert "traceparent" in carrier, (
        "a cross-process call would start an unrelated trace"
    )


def test_extract_makes_the_new_span_a_child_of_the_caller():
    """The whole point: the trace must survive a process boundary."""
    trace_id, span_id = 0x1234567890ABCDEF1234567890ABCDEF, 0xFEDCBA9876543210
    carrier = {"traceparent": f"00-{trace_id:032x}-{span_id:016x}-01"}

    context = extract_trace_context(carrier)

    from opentelemetry import trace

    recovered = trace.get_current_span(context).get_span_context()
    assert recovered.trace_id == trace_id
    assert recovered.span_id == span_id


def test_extract_from_an_uninstrumented_caller_degrades_quietly():
    """No headers is a new trace, not an exception."""
    context = extract_trace_context({})
    from opentelemetry import trace

    assert not trace.get_current_span(context).get_span_context().is_valid


def test_inject_and_extract_round_trip():
    from opentelemetry import trace

    from src.observability.telemetry import configure_telemetry

    configure_telemetry()
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("caller") as span:
        carrier = inject_trace_context()
        original = span.get_span_context().trace_id

    recovered = trace.get_current_span(
        extract_trace_context(carrier)
    ).get_span_context()
    assert recovered.trace_id == original


# --- sampling ----------------------------------------------------------------


def test_default_keeps_every_trace(monkeypatch):
    """A repo run locally or in CI must not silently drop the trace you needed."""
    monkeypatch.delenv("OTEL_TRACES_SAMPLER_ARG", raising=False)
    sampler = configured_sampler()
    result = sampler.should_sample(None, 0x2A, "span")
    assert result.decision is Decision.RECORD_AND_SAMPLE


def test_ratio_sampler_is_parent_based(monkeypatch):
    monkeypatch.setenv("OTEL_TRACES_SAMPLER_ARG", "0.25")
    assert isinstance(configured_sampler(), ParentBased)


def test_a_sampled_parent_keeps_its_children_even_at_ratio_zero(monkeypatch):
    """ParentBased is what stops a sampled trace arriving with holes in it."""
    monkeypatch.setenv("OTEL_TRACES_SAMPLER_ARG", "0.0")
    sampler = configured_sampler()

    sampled_parent = set_span_in_context(
        __import__(
            "opentelemetry.trace", fromlist=["NonRecordingSpan"]
        ).NonRecordingSpan(
            SpanContext(
                trace_id=0xABC,
                span_id=0xDEF,
                is_remote=True,
                trace_flags=TraceFlags(TraceFlags.SAMPLED),
            )
        )
    )
    result = sampler.should_sample(sampled_parent, 0xABC, "child")
    assert result.decision is Decision.RECORD_AND_SAMPLE


@pytest.mark.parametrize("bad", ["2.0", "-0.1", "half", ""])
def test_an_invalid_sampler_ratio_raises_rather_than_defaulting(monkeypatch, bad):
    """Silently falling back would mean losing traces you believed you kept."""
    monkeypatch.setenv("OTEL_TRACES_SAMPLER_ARG", bad)
    with pytest.raises(ValueError):
        configured_sampler()
