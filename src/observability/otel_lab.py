"""OpenTelemetry signals beyond spans and counters, offline, for the OTel course.

`telemetry.py` and `metrics.py` are the repository's production wiring. This
module isolates four behaviours a learner needs before trusting that wiring,
each with its own in-memory provider so nothing leaks into the global one:

- A span event is a timestamped point inside a span; an exception recorded
  on a span becomes an event named `exception` with `exception.type` and
  `exception.message` attributes.
- A `BatchSpanProcessor` exports nothing until its batch is flushed. The SDK
  flushes on a normal interpreter exit, but not when a process is killed or
  exits abruptly, so short-lived jobs should flush before they end.
- An exemplar links a metric measurement to the trace that was active when
  it was recorded. With the default trace-based filter, only measurements
  taken inside a sampled span get one.

Each is pinned by a test in tests/unit/observability/test_otel_lab.py.
"""

from __future__ import annotations

from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    SimpleSpanProcessor,
    SpanExporter,
)
from opentelemetry.trace import Tracer


def tracer_with(
    exporter: SpanExporter, *, batched: bool = False, delay_ms: int = 60_000
) -> tuple[TracerProvider, Tracer]:
    """A private provider that exports to `exporter`, simply or in batches."""
    provider = TracerProvider()
    processor = (
        BatchSpanProcessor(exporter, schedule_delay_millis=delay_ms)
        if batched
        else SimpleSpanProcessor(exporter)
    )
    provider.add_span_processor(processor)
    return provider, provider.get_tracer("otel-lab")


def price_bond(tracer: Tracer, tenor_years: float) -> float:
    """Record a curve-load moment as an event; reject a non-positive tenor."""
    with tracer.start_as_current_span("price_bond") as span:
        # When it happened matters, so this is an event, not an attribute.
        span.add_event("curve.loaded", {"curve.points": 12})
        if tenor_years <= 0:
            # start_as_current_span records the exception as an event and sets
            # the span's status to ERROR on the way out.
            raise ValueError(f"tenor must be positive, got {tenor_years}")
        span.set_attribute("bond.tenor_years", tenor_years)
        return 100.0 - tenor_years


def latency_metrics() -> tuple[MeterProvider, InMemoryMetricReader]:
    """A private meter provider whose metrics can be read back in a test."""
    reader = InMemoryMetricReader()
    return MeterProvider(metric_readers=[reader]), reader
