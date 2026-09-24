"""OpenTelemetry behaviour the OTel course teaches, run rather than described.

Quiz questions in evals/tutor_quizzes/opentelemetry-tutor.jsonl cite these
tests by name (`verified_by`). Every provider here is private and in memory.
"""

import subprocess
import sys
import textwrap

import pytest
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.sdk.trace.sampling import Decision, TraceIdRatioBased
from opentelemetry.trace import (
    NonRecordingSpan,
    SpanContext,
    StatusCode,
    TraceFlags,
    set_span_in_context,
)

from src.observability.otel_lab import latency_metrics, price_bond, tracer_with


def test_an_exception_on_a_span_becomes_an_exception_event():
    exporter = InMemorySpanExporter()
    _, tracer = tracer_with(exporter)
    with pytest.raises(ValueError):
        price_bond(tracer, 0)
    [span] = exporter.get_finished_spans()
    events = {event.name: event for event in span.events}
    # A point in time worth keeping: an event, with its own timestamp.
    assert events["curve.loaded"].timestamp >= span.start_time
    assert events["exception"].attributes["exception.type"] == "ValueError"
    assert (
        "tenor must be positive" in events["exception"].attributes["exception.message"]
    )
    assert span.status.status_code == StatusCode.ERROR


def test_a_batch_processor_exports_nothing_until_it_is_flushed():
    exporter = InMemorySpanExporter()
    provider, tracer = tracer_with(exporter, batched=True)
    price_bond(tracer, 5)
    assert exporter.get_finished_spans() == ()
    provider.force_flush()
    assert [s.name for s in exporter.get_finished_spans()] == ["price_bond"]


@pytest.mark.parametrize(
    ("exit_call", "exported"), [("", True), ("os._exit(0)", False)]
)
def test_batched_spans_survive_a_normal_exit_but_not_an_abrupt_one(exit_call, exported):
    """The SDK shuts the provider down, flushing the batch, at a normal
    interpreter exit. A process that exits abruptly never gets there."""
    script = textwrap.dedent(
        f"""
        import os
        from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
        from src.observability.otel_lab import price_bond, tracer_with

        class Stdout(SpanExporter):
            def export(self, spans):
                print("exported", len(spans), flush=True)
                return SpanExportResult.SUCCESS

        _, tracer = tracer_with(Stdout(), batched=True)
        price_bond(tracer, 5)
        {exit_call}
        """
    )
    out = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout
    assert ("exported 1" in out) is exported


def test_an_exemplar_links_a_measurement_to_the_active_trace():
    exporter = InMemorySpanExporter()
    _, tracer = tracer_with(exporter)
    meters, reader = latency_metrics()
    latency = meters.get_meter("otel-lab").create_histogram(
        "app.tool.duration", unit="ms"
    )
    with tracer.start_as_current_span("price_bond") as span:
        latency.record(12.0)
        trace_id = span.get_span_context().trace_id
    latency.record(5.0)  # no active span, so no exemplar
    point = (
        reader.get_metrics_data().resource_metrics[0].scope_metrics[0].metrics[0]
    ).data.data_points[0]
    assert point.count == 2
    assert [(e.value, e.trace_id) for e in point.exemplars] == [(12.0, trace_id)]


def test_a_plain_ratio_sampler_ignores_a_sampled_upstream_parent():
    """The ratio decision depends on the trace id alone, so one service with
    one ratio never splits a trace. It ignores the parent's sampled flag, so
    a downstream service at a lower ratio drops spans of a trace kept
    upstream. ParentBased, which configured_sampler() uses, keeps them:
    test_a_sampled_parent_keeps_its_children_even_at_ratio_zero."""
    parent = set_span_in_context(
        NonRecordingSpan(
            SpanContext(
                trace_id=0xABC,
                span_id=0xDEF,
                is_remote=True,
                trace_flags=TraceFlags(TraceFlags.SAMPLED),
            )
        )
    )
    downstream = TraceIdRatioBased(0.0)
    assert downstream.should_sample(parent, 0xABC, "child").decision is Decision.DROP
    same_ratio = TraceIdRatioBased(0.5)
    decisions = {
        same_ratio.should_sample(context, 0xABC, name).decision
        for context, name in [(None, "root"), (parent, "child")]
    }
    assert len(decisions) == 1  # same trace id, same decision, parent or not
