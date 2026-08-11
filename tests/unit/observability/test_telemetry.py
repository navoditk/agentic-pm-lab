import pytest
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
)
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)
from opentelemetry.trace import StatusCode

from src.analytics.pricers import black_scholes_price, price_bond
from src.api.main import app
from src.control.allowlist import check_permission
from src.control.audit import record_audit_event
from src.observability.telemetry import (
    configure_telemetry,
    observe_agent_run,
)


@pytest.fixture(scope="module")
def span_exporter():
    exporter = InMemorySpanExporter()
    configure_telemetry().add_span_processor(SimpleSpanProcessor(exporter))
    return exporter


def test_analytics_span_records_safe_inputs_latency_and_success(span_exporter):
    span_exporter.clear()

    price_bond(
        [{"time_years": 1, "amount": 105}],
        [0.5, 1],
        [4, 4.5],
        compounding_frequency=1,
    )

    spans = {span.name: span for span in span_exporter.get_finished_spans()}
    span = spans["analytics.price_bond"]
    assert span.attributes["app.tool.name"] == "price_bond"
    assert span.attributes["app.tool.input.argument_count"] == 4
    assert span.attributes["app.operation.duration_ms"] >= 0
    assert span.attributes["app.operation.success"] is True
    assert span.status.status_code is StatusCode.OK


def test_analytics_failure_is_explicit_on_span(span_exporter):
    span_exporter.clear()

    with pytest.raises(ValueError, match="spot and strike must be positive"):
        black_scholes_price(0, 100, 1, 0.04, 0.2, "call")

    span = span_exporter.get_finished_spans()[-1]
    assert span.attributes["app.operation.success"] is False
    assert span.status.status_code is StatusCode.ERROR
    assert span.events[-1].name == "exception"


def test_agent_span_records_genai_usage_and_estimated_cost(span_exporter):
    span_exporter.clear()

    with observe_agent_run(
        "agent.test.invoke",
        "openai:gpt-4.1-mini",
    ) as (_span, metrics):
        metrics.on_llm_end(
            LLMResult(
                generations=[
                    [
                        ChatGeneration(
                            message=AIMessage(
                                content="done",
                                usage_metadata={
                                    "input_tokens": 1_000,
                                    "output_tokens": 100,
                                    "total_tokens": 1_100,
                                },
                            )
                        )
                    ]
                ]
            )
        )
        metrics.on_tool_start({"name": "price_bond"}, "{}")

    span = span_exporter.get_finished_spans()[-1]
    assert span.attributes["gen_ai.request.model"] == "gpt-4.1-mini"
    assert span.attributes["gen_ai.usage.input_tokens"] == 1_000
    assert span.attributes["gen_ai.usage.output_tokens"] == 100
    assert span.attributes["app.tool.call_count"] == 1
    assert span.attributes["app.cost.estimated_usd"] == pytest.approx(0.00056)


def test_fastapi_app_is_auto_instrumented():
    assert app.state.otel_instrumented is True


def test_authorization_and_audit_are_child_traceable_operations(
    span_exporter,
    tmp_path,
):
    span_exporter.clear()

    allowed = check_permission("risk", "price-bond")
    record_audit_event(
        "risk_user",
        "risk",
        "price-bond",
        allowed,
        log_path=tmp_path / "audit.jsonl",
    )

    spans = {span.name: span for span in span_exporter.get_finished_spans()}
    permission = spans["control.check_permission"]
    audit = spans["control.record_audit_event"]
    assert permission.attributes["app.auth.allowed"] is False
    assert permission.attributes["app.auth.role"] == "risk"
    assert audit.attributes["app.operation.type"] == "audit"
    assert audit.attributes["app.auth.allowed"] is False
