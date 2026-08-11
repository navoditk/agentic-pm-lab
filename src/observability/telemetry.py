"""Shared OpenTelemetry instrumentation and operational agent metrics."""

import json
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from fastapi import FastAPI
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import Span, Status, StatusCode

P = ParamSpec("P")
R = TypeVar("R")

SERVICE_NAME = "agentic-pm-lab"
MODEL_PRICES_PER_MILLION_USD = {
    # https://platform.openai.com/docs/guides/pricing
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
}

_provider: TracerProvider | None = None


def configure_telemetry(service_name: str = SERVICE_NAME) -> TracerProvider:
    """Install one SDK tracer provider without replacing an existing SDK provider."""
    global _provider
    if _provider is not None:
        return _provider
    current = trace.get_tracer_provider()
    if isinstance(current, TracerProvider):
        _provider = current
        return current
    _provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    trace.set_tracer_provider(_provider)
    return _provider


def instrument_fastapi(app: FastAPI) -> None:
    """Auto-instrument one FastAPI application exactly once."""
    configure_telemetry()
    if getattr(app.state, "otel_instrumented", False):
        return
    FastAPIInstrumentor.instrument_app(app)
    app.state.otel_instrumented = True


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
                try:
                    result = function(*args, **kwargs)
                except Exception as error:
                    span.set_attribute("app.operation.success", False)
                    span.record_exception(error)
                    span.set_status(Status(StatusCode.ERROR, type(error).__name__))
                    raise
                else:
                    span.set_attribute("app.operation.success", True)
                    span.set_status(Status(StatusCode.OK))
                    return result
                finally:
                    span.set_attribute(
                        "app.operation.duration_ms",
                        (time.perf_counter() - started) * 1000,
                    )

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
    with tracer.start_as_current_span(operation_name) as span:
        span.set_attribute("app.operation.type", "agent")
        try:
            yield span, metrics
        except Exception as error:
            span.set_attribute("app.operation.success", False)
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, type(error).__name__))
            raise
        else:
            span.set_attribute("app.operation.success", True)
            span.set_status(Status(StatusCode.OK))
        finally:
            metrics.apply_to_span(span, model_name)
            span.set_attribute(
                "app.operation.duration_ms",
                (time.perf_counter() - started) * 1000,
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
