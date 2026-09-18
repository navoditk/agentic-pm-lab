"""OpenTelemetry metrics — the second signal, alongside `telemetry.py`'s traces.

Traces answer "what happened in this one request". Metrics answer "what is
happening across all of them", and that is a different question: a single
slow trace is an anecdote, a latency histogram is an SLO. Span attributes
cannot answer it, because you cannot aggregate over spans you did not export.

`OperationalMetricsHandler` in `telemetry.py` already accumulates token,
tool, retry and cost figures per run and writes them onto a span. This module
records the same figures as real instruments so they aggregate, and adds the
ones that only make sense in aggregate: latency distribution, error rate, and
authorization-denial counts.

Instruments follow the OpenTelemetry metric naming guidance -- dotted
namespace, unit suffix carried in the `unit` argument rather than the name,
counters named for the thing counted rather than for the verb.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Mapping
from typing import Any

from opentelemetry import metrics
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource

SERVICE_NAME = "agentic-pm-lab"

_provider: MeterProvider | None = None
_instruments: _Instruments | None = None
_lock = threading.Lock()


class _Instruments:
    """The instrument set, created once against a single meter."""

    def __init__(self, meter: metrics.Meter) -> None:
        self.agent_runs = meter.create_counter(
            "app.agent.runs",
            unit="{run}",
            description="Agent invocations, labelled by outcome and model.",
        )
        self.agent_duration = meter.create_histogram(
            "app.agent.duration",
            unit="s",
            description="Wall-clock duration of an agent invocation.",
        )
        self.tool_calls = meter.create_counter(
            "app.tool.calls",
            unit="{call}",
            description="Deterministic tool invocations, labelled by tool name.",
        )
        self.tool_duration = meter.create_histogram(
            "app.tool.duration",
            unit="s",
            description="Wall-clock duration of one deterministic tool call.",
        )
        self.tokens = meter.create_counter(
            "app.llm.tokens",
            unit="{token}",
            description="Model tokens consumed, labelled by direction and model.",
        )
        self.estimated_cost = meter.create_counter(
            "app.llm.estimated_cost",
            unit="USD",
            description="Estimated spend derived from token counts and a static price table.",
        )
        self.retries = meter.create_counter(
            "app.retry.count",
            unit="{retry}",
            description="Retries attempted, labelled by the component that retried.",
        )
        self.authorization_denials = meter.create_counter(
            "app.authorization.denials",
            unit="{denial}",
            description="Requests refused at the policy or tool boundary, labelled by reason.",
        )


def configure_metrics(
    service_name: str = SERVICE_NAME,
    reader: Any | None = None,
) -> MeterProvider:
    """Install one SDK meter provider, without replacing an existing one.

    Mirrors `configure_telemetry`'s contract deliberately: idempotent, and it
    yields to a provider someone else already installed rather than fighting
    over the global.

    Passing `reader` means "build me a dedicated provider and do not touch the
    global" — which is what a test needs, and the reason it bypasses both the
    reuse branch and `set_meter_provider`. OpenTelemetry's global meter
    provider can only be set once per process; without this branch the second
    test in a run would silently reuse the first test's provider and every
    assertion after it would read an empty reader.
    """
    global _provider, _instruments
    with _lock:
        if reader is not None:
            _provider = MeterProvider(
                resource=Resource.create({"service.name": service_name}),
                metric_readers=[reader],
            )
            _instruments = _Instruments(_provider.get_meter(__name__))
            return _provider

        if _provider is not None:
            return _provider

        current = metrics.get_meter_provider()
        if isinstance(current, MeterProvider):
            _provider = current
            _instruments = _Instruments(current.get_meter(__name__))
            return current

        _provider = MeterProvider(
            resource=Resource.create({"service.name": service_name}),
            metric_readers=_default_readers(),
        )
        metrics.set_meter_provider(_provider)
        _instruments = _Instruments(_provider.get_meter(__name__))
        return _provider


def _default_readers() -> list[Any]:
    """An OTLP reader only when an endpoint is configured.

    With no endpoint the provider still works and instruments still record --
    the points simply go nowhere. That keeps local runs and unit tests free of
    connection errors, which is the behaviour the tracing side already has.
    """
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT") or os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    if not endpoint:
        return []
    return [PeriodicExportingMetricReader(OTLPMetricExporter(endpoint=endpoint))]


def reset_metrics_for_testing() -> None:
    """Drop the cached provider so a test can install its own reader."""
    global _provider, _instruments
    with _lock:
        _provider = None
        _instruments = None


def _get() -> _Instruments:
    if _instruments is None:
        configure_metrics()
    assert _instruments is not None
    return _instruments


def record_agent_run(
    *,
    model: str,
    duration_seconds: float,
    success: bool,
    agent: str = "unknown",
) -> None:
    """One completed agent invocation."""
    attributes: Mapping[str, Any] = {
        "model": model.rsplit(":", 1)[-1],
        "agent": agent,
        "outcome": "success" if success else "error",
    }
    instruments = _get()
    instruments.agent_runs.add(1, attributes)
    instruments.agent_duration.record(max(duration_seconds, 0.0), attributes)


def record_tool_call(
    *, tool: str, duration_seconds: float, success: bool = True
) -> None:
    """One deterministic tool invocation."""
    attributes = {"tool": tool, "outcome": "success" if success else "error"}
    instruments = _get()
    instruments.tool_calls.add(1, attributes)
    instruments.tool_duration.record(max(duration_seconds, 0.0), attributes)


def record_token_usage(
    *,
    model: str,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float = 0.0,
) -> None:
    """Token consumption, split by direction so cost can be attributed."""
    normalized = model.rsplit(":", 1)[-1]
    instruments = _get()
    if input_tokens:
        instruments.tokens.add(
            input_tokens, {"model": normalized, "direction": "input"}
        )
    if output_tokens:
        instruments.tokens.add(
            output_tokens, {"model": normalized, "direction": "output"}
        )
    if estimated_cost_usd:
        instruments.estimated_cost.add(estimated_cost_usd, {"model": normalized})


def record_retry(*, component: str) -> None:
    _get().retries.add(1, {"component": component})


def record_authorization_denial(*, reason: str, role: str = "unknown") -> None:
    """A refusal at the policy or tool boundary.

    Counted separately from errors on purpose: a denial is the control layer
    working, and a rate that suddenly drops to zero is as interesting as one
    that spikes.
    """
    _get().authorization_denials.add(1, {"reason": reason, "role": role})
