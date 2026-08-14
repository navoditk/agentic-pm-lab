"""AWS Bedrock AgentCore direct-code runtime entrypoint."""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from opentelemetry import trace

from src.agents.multi_agent import create_multi_agent, invoke_multi_agent
from src.observability.telemetry import observe_operation

app = BedrockAgentCoreApp()
LOGGER = logging.getLogger(__name__)
DEFAULT_AGENTCORE_MODEL = "bedrock_converse:us.anthropic.claude-haiku-4-5-20251001-v1:0"


def _require_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _trace_id() -> str:
    """Return the active OTel trace ID, or an explicit zero value."""
    context = trace.get_current_span().get_span_context()
    return format(context.trace_id, "032x") if context.is_valid else "0" * 32


def _stage(request_id: str, name: str, **fields: Any) -> dict[str, Any]:
    """Emit safe structured evidence for one workflow stage."""
    event = {
        "event": "agentcore.workflow.stage",
        "request_id": request_id,
        "trace_id": _trace_id(),
        "stage": name,
        **fields,
    }
    LOGGER.info(json.dumps(event, sort_keys=True, default=str))
    return {"stage": name, "trace_id": event["trace_id"]}


@app.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """Invoke the governed Portfolio Manager from AgentCore Runtime."""
    if not isinstance(payload, dict):
        raise TypeError("invocation payload must be an object")
    request_id = payload.get("request_id")
    if not isinstance(request_id, str) or not request_id.strip():
        request_id = f"agentcore-{uuid.uuid4().hex}"
    stages: list[dict[str, Any]] = []
    stages.append(
        _stage(request_id, "request_received", payload_fields=sorted(payload))
    )
    identity = _require_string(payload, "identity")
    question = _require_string(payload, "question")
    sources = payload.get("sources")
    if not isinstance(sources, dict):
        raise TypeError("sources must be an object")
    stages.append(_stage(request_id, "input_validated", identity=identity))
    model = os.getenv(
        "AGENTCORE_MODEL",
        DEFAULT_AGENTCORE_MODEL,
    )
    with observe_operation(
        "agentcore.workflow.orchestration",
        "chain",
        {
            "app.request_id": request_id,
            "app.auth.identity": identity,
            "app.model.name": model,
        },
    ):
        stages.append(_stage(request_id, "orchestration_started", model=model))
        result = invoke_multi_agent(
            question,
            {**sources, "user_role": {"identity": identity}},
            model_name=model,
            agent=create_multi_agent(identity, model=model),
        )
        stages.append(_stage(request_id, "orchestration_completed"))
    stages.append(
        _stage(request_id, "response_emitted", result_type=type(result).__name__)
    )
    return {
        "request_id": request_id,
        "trace_id": _trace_id(),
        "identity": identity,
        "model": model,
        "result": result,
        "runtime": "amazon-bedrock-agentcore",
        "approval_required": True,
        "order_execution": False,
        "workflow_stages": stages,
        "reasoning_note": (
            "The trace records observable stages, authorization, tool activity, "
            "guardrail outcomes, and outputs. Private model chain-of-thought is "
            "not captured or exposed."
        ),
    }


if __name__ == "__main__":  # pragma: no cover
    app.run()
