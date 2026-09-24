"""Shared OpenTelemetry instrumentation and operational agent metrics."""

import json
import logging
import os
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from fastapi import FastAPI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from opentelemetry import propagate, trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import (
    ALWAYS_ON,
    ParentBased,
    Sampler,
    TraceIdRatioBased,
)
from opentelemetry.trace import Span, Status, StatusCode

P = ParamSpec("P")
R = TypeVar("R")

_logger = logging.getLogger(__name__)

SERVICE_NAME = "agentic-pm-lab"
MODEL_PRICES_PER_MILLION_USD = {
    # https://platform.openai.com/docs/guides/pricing
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    # https://platform.claude.com/docs/en/about-claude/pricing
    "claude-haiku-4-5-20251001": {"input": 1.00, "output": 5.00},
}

_provider: TracerProvider | None = None
_langsmith_exporter_configured = False


def configure_telemetry(service_name: str = SERVICE_NAME) -> TracerProvider:
    """Install one SDK tracer provider without replacing an existing SDK provider."""
    global _provider
    if _provider is not None:
        _configure_langsmith_exporter(_provider)
        return _provider
    current = trace.get_tracer_provider()
    if isinstance(current, TracerProvider):
        _provider = current
        _configure_langsmith_exporter(current)
        return current
    _provider = TracerProvider(
        resource=Resource.create({"service.name": service_name}),
        sampler=configured_sampler(),
    )
    trace.set_tracer_provider(_provider)
    _configure_langsmith_exporter(_provider)
    return _provider


def _configure_langsmith_exporter(provider: TracerProvider) -> None:
    """Attach one OTLP exporter when LangSmith OTel-only tracing is enabled."""
    global _langsmith_exporter_configured
    if _langsmith_exporter_configured:
        return
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "").lower() == "true"
    tracing_mode = os.getenv("LANGSMITH_TRACING_MODE", "").lower()
    api_key = os.getenv("LANGSMITH_API_KEY")
    if not (tracing_enabled and tracing_mode in {"otel", "hybrid"} and api_key):
        return
    endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    headers = {"x-api-key": api_key}
    project = os.getenv("LANGSMITH_PROJECT")
    if project:
        headers["Langsmith-Project"] = project
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=f"{endpoint.rstrip('/')}/otel/v1/traces",
                headers=headers,
            )
        )
    )
    _langsmith_exporter_configured = True


def configured_sampler() -> Sampler:
    """Head sampler built from `OTEL_TRACES_SAMPLER_ARG`, default keep-everything.

    Two things make this safe rather than a knob that silently loses data.
    `ParentBased` means a child span follows the decision already made
    upstream. A plain `TraceIdRatioBased` sampler decides from the trace id
    alone and ignores the parent's sampled flag, so when two services sample
    at different ratios, a trace kept upstream loses its spans downstream --
    holes in the middle, the most confusing failure mode of ratio sampling. And the
    default is 1.0, so a repository run locally or in CI keeps every trace;
    sampling is something you opt into when volume makes keeping everything
    expensive, not a default that quietly hides the trace you needed.
    """
    raw = os.getenv("OTEL_TRACES_SAMPLER_ARG")
    if raw is None:
        return ALWAYS_ON
    try:
        ratio = float(raw)
    except ValueError as error:
        raise ValueError(
            f"OTEL_TRACES_SAMPLER_ARG must be a number between 0 and 1, got {raw!r}"
        ) from error
    if not 0.0 <= ratio <= 1.0:
        raise ValueError(f"OTEL_TRACES_SAMPLER_ARG must be within [0, 1], got {ratio}")
    return ParentBased(root=TraceIdRatioBased(ratio))


def inject_trace_context(carrier: dict[str, str] | None = None) -> dict[str, str]:
    """Write the current span's context into a carrier for an outbound call.

    This is what makes a trace survive a process boundary. Without it the MCP
    server's spans become a second, unrelated trace, and the question "which
    agent request caused this tool call" stops being answerable -- which is
    most of the reason for tracing an agent system at all.
    """
    carrier = {} if carrier is None else carrier
    propagate.inject(carrier)
    return carrier


def extract_trace_context(carrier: Mapping[str, str]) -> Any:
    """Recover an upstream context from an inbound carrier.

    Pass the result as `context=` when starting a span, so the new span
    becomes a child of the caller's rather than a new root. A carrier with no
    trace headers yields a context that simply starts a new trace, so an
    uninstrumented caller degrades quietly instead of failing.
    """
    return propagate.extract(dict(carrier))


def instrument_fastapi(app: FastAPI) -> None:
    """Auto-instrument one FastAPI application exactly once."""
    configure_telemetry()
    if getattr(app.state, "otel_instrumented", False):
        return
    FastAPIInstrumentor.instrument_app(app)
    app.state.otel_instrumented = True


@contextmanager
def observe_operation(
    name: str,
    operation_type: str,
    attributes: Mapping[str, str | bool | int | float],
) -> Iterator[Span]:
    """Trace one non-agent operation with consistent success and latency fields."""
    configure_telemetry()
    tracer = trace.get_tracer("agentic_pm_lab.operations")
    started = time.perf_counter()
    with tracer.start_as_current_span(name) as span:
        span.set_attribute("app.operation.type", operation_type)
        span.set_attribute(
            "langsmith.span.kind",
            "tool" if operation_type in {"tool", "authorization", "audit"} else "chain",
        )
        for key, value in attributes.items():
            span.set_attribute(key, value)
        try:
            yield span
        except Exception as error:
            span.set_attribute("app.operation.success", False)
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, type(error).__name__))
            raise
        else:
            span.set_attribute("app.operation.success", True)
            span.set_status(Status(StatusCode.OK))
        finally:
            span.set_attribute(
                "app.operation.duration_ms",
                (time.perf_counter() - started) * 1000,
            )


def _item_count(values: Sequence[Any]) -> int:
    count = 0
    for value in values:
        if isinstance(value, Mapping | Sequence) and not isinstance(
            value, str | bytes | bytearray
        ):
            count += len(value)
        else:
            count += 1
    return count


def _record_tool_metric(name: str, elapsed: float, succeeded: bool) -> None:
    """Mirror one tool span into the metrics signal.

    Import is local and failures are swallowed on purpose: instrumentation
    must never be the reason a deterministic analytics call fails. A dropped
    metric point is an acceptable loss; a bond price that raises because a
    meter was misconfigured is not.
    """
    try:
        from src.observability.metrics import record_tool_call

        record_tool_call(tool=name, duration_seconds=elapsed, success=succeeded)
    except Exception:
        _logger.debug("tool metric not recorded for %s", name, exc_info=True)


def _record_agent_metrics(
    *,
    operation_name: str,
    model_name: str,
    elapsed: float,
    handler: "OperationalMetricsHandler",
    succeeded: bool,
) -> None:
    """Mirror one agent run and its token usage into the metrics signal."""
    try:
        from src.observability.metrics import (
            record_agent_run,
            record_retry,
            record_token_usage,
        )

        normalized = model_name.rsplit(":", 1)[-1]
        prices = MODEL_PRICES_PER_MILLION_USD.get(normalized)
        estimated_cost = 0.0
        if prices:
            estimated_cost = (
                handler.input_tokens * prices["input"]
                + handler.output_tokens * prices["output"]
            ) / 1_000_000
        record_agent_run(
            model=model_name,
            duration_seconds=elapsed,
            success=succeeded,
            agent=operation_name,
        )
        record_token_usage(
            model=model_name,
            input_tokens=handler.input_tokens,
            output_tokens=handler.output_tokens,
            estimated_cost_usd=estimated_cost,
        )
        for _ in range(handler.retry_count):
            record_retry(component=operation_name)
    except Exception:
        _logger.debug(
            "agent metrics not recorded for %s", operation_name, exc_info=True
        )


def traced_analytics(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Wrap one deterministic analytics function in a tool-level span."""

    def decorator(function: Callable[P, R]) -> Callable[P, R]:
        @wraps(function)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            configure_telemetry()
            tracer = trace.get_tracer("agentic_pm_lab.analytics")
            started = time.perf_counter()
            with tracer.start_as_current_span(f"analytics.{name}") as span:
                span.set_attribute("app.operation.type", "tool")
                span.set_attribute("langsmith.span.kind", "tool")
                span.set_attribute("app.tool.name", name)
                span.set_attribute(
                    "app.tool.input.argument_count", len(args) + len(kwargs)
                )
                span.set_attribute(
                    "app.tool.input.item_count",
                    _item_count([*args, *kwargs.values()]),
                )
                span.set_attribute("app.tool.call_count", 1)
                span.set_attribute(
                    "app.retrieval.call_count",
                    int(name == "get_research_summary"),
                )
                span.set_attribute("app.retry.count", 0)
                succeeded = False
                try:
                    result = function(*args, **kwargs)
                except Exception as error:
                    span.set_attribute("app.operation.success", False)
                    span.record_exception(error)
                    span.set_status(Status(StatusCode.ERROR, type(error).__name__))
                    raise
                else:
                    succeeded = True
                    span.set_attribute("app.operation.success", True)
                    span.set_status(Status(StatusCode.OK))
                    return result
                finally:
                    elapsed = time.perf_counter() - started
                    span.set_attribute("app.operation.duration_ms", elapsed * 1000)
                    _record_tool_metric(name, elapsed, succeeded)

        return wrapped

    return decorator


class OperationalMetricsHandler(BaseCallbackHandler):
    """Collect nested model/tool/retrieval counts for one agent invocation."""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.tool_calls = 0
        self.retrieval_calls = 0
        self.retry_count = 0
        self._lock = threading.Lock()

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        del kwargs
        input_tokens = 0
        output_tokens = 0
        for generations in response.generations:
            for generation in generations:
                message = getattr(generation, "message", None)
                usage = getattr(message, "usage_metadata", None)
                if usage:
                    input_tokens += int(usage.get("input_tokens", 0))
                    output_tokens += int(usage.get("output_tokens", 0))
        if not input_tokens and not output_tokens and response.llm_output:
            usage = response.llm_output.get("token_usage", {})
            input_tokens = int(usage.get("prompt_tokens", 0))
            output_tokens = int(usage.get("completion_tokens", 0))
        with self._lock:
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        **kwargs: Any,
    ) -> None:
        del input_str, kwargs
        name = serialized.get("name", "")
        with self._lock:
            self.tool_calls += 1
            if name == "get_research_summary":
                self.retrieval_calls += 1

    def on_retriever_start(
        self,
        serialized: dict[str, Any],
        query: str,
        **kwargs: Any,
    ) -> None:
        del serialized, query, kwargs
        with self._lock:
            self.retrieval_calls += 1

    def on_retry(self, retry_state: Any, **kwargs: Any) -> None:
        del retry_state, kwargs
        with self._lock:
            self.retry_count += 1

    def apply_to_span(self, span: Span, model_name: str) -> None:
        """Attach collected GenAI and operational-economics attributes."""
        normalized_model = model_name.rsplit(":", 1)[-1]
        span.set_attribute("gen_ai.operation.name", "invoke_agent")
        span.set_attribute("gen_ai.request.model", normalized_model)
        span.set_attribute("gen_ai.usage.input_tokens", self.input_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", self.output_tokens)
        span.set_attribute("gen_ai.usage.prompt_tokens", self.input_tokens)
        span.set_attribute("gen_ai.usage.completion_tokens", self.output_tokens)
        span.set_attribute(
            "gen_ai.usage.total_tokens",
            self.input_tokens + self.output_tokens,
        )
        span.set_attribute("app.tool.call_count", self.tool_calls)
        span.set_attribute("app.retrieval.call_count", self.retrieval_calls)
        span.set_attribute("app.retry.count", self.retry_count)
        prices = MODEL_PRICES_PER_MILLION_USD.get(normalized_model)
        estimated_cost = 0.0
        if prices:
            estimated_cost = (
                self.input_tokens * prices["input"]
                + self.output_tokens * prices["output"]
            ) / 1_000_000
        span.set_attribute("app.cost.estimated_usd", estimated_cost)


@contextmanager
def observe_agent_run(
    operation_name: str,
    model_name: str,
) -> Iterator[tuple[Span, OperationalMetricsHandler]]:
    """Create a root agent span and yield its callback metrics collector."""
    configure_telemetry()
    tracer = trace.get_tracer("agentic_pm_lab.agents")
    metrics = OperationalMetricsHandler()
    started = time.perf_counter()
    succeeded = False
    with tracer.start_as_current_span(operation_name) as span:
        span.set_attribute("app.operation.type", "agent")
        span.set_attribute("langsmith.span.kind", "chain")
        span.set_attribute("langsmith.trace.name", operation_name)
        try:
            yield span, metrics
        except Exception as error:
            span.set_attribute("app.operation.success", False)
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, type(error).__name__))
            raise
        else:
            succeeded = True
            span.set_attribute("app.operation.success", True)
            span.set_status(Status(StatusCode.OK))
        finally:
            metrics.apply_to_span(span, model_name)
            elapsed = time.perf_counter() - started
            span.set_attribute("app.operation.duration_ms", elapsed * 1000)
            # The same figures also go out as metrics: the span answers "what
            # happened in this run", the instruments answer "what is happening
            # across all of them". Neither substitutes for the other.
            _record_agent_metrics(
                operation_name=operation_name,
                model_name=model_name,
                elapsed=elapsed,
                handler=metrics,
                succeeded=succeeded,
            )


def dead_letter_payload(
    *,
    operation: str,
    error_type: str,
    retryable: bool,
    message: str,
) -> str:
    """Serialize an explicit failure state for a tool response."""
    return json.dumps(
        {
            "status": "dead_letter",
            "tool": operation,
            "error_type": error_type,
            "retryable": retryable,
            "message": message,
        }
    )
