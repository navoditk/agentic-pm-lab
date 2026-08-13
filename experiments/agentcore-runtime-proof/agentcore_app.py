"""Minimal read-only AgentCore proof slice for the Agentic PM Lab."""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp

app = BedrockAgentCoreApp()
LOGGER = logging.getLogger("agentic_pm_lab.agentcore_proof")
logging.basicConfig(level=logging.INFO)
MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
GUARDRAIL_ID = os.getenv("GUARDRAIL_ID")
GUARDRAIL_VERSION = os.getenv("GUARDRAIL_VERSION", "DRAFT")


def _stage(stages: list[dict[str, Any]], name: str, **details: Any) -> None:
    stages.append({"stage": name, "details": details})
    LOGGER.info(
        "workflow_stage=%s details=%s", name, json.dumps(details, sort_keys=True)
    )


@app.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """Run a bounded, read-only portfolio research request."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a JSON object")

    request_id = str(payload.get("request_id") or f"req-{uuid.uuid4().hex}")
    stages: list[dict[str, Any]] = []
    _stage(stages, "request_received", request_id=request_id)

    identity = payload.get("identity")
    question = payload.get("question")
    sources = payload.get("sources")
    if not identity or not question or not isinstance(sources, dict):
        raise ValueError("identity, question, and sources are required")
    _stage(stages, "input_validated", source_count=len(sources))
    _stage(
        stages, "authorization_checked", decision="allow", action="read_only_research"
    )
    _stage(stages, "orchestration_started", tools=[], order_execution=False)

    prompt = (
        "You are a read-only institutional portfolio research assistant. "
        "Use only the supplied public or mock evidence. State assumptions and "
        "uncertainty. Do not provide private chain-of-thought, place trades, "
        "or recommend an order. Return evidence, implications, risks, and "
        "the next human review step.\n\n"
        f"Question: {question}\nEvidence: {json.dumps(sources, sort_keys=True)}"
    )
    client = boto3.client("bedrock-runtime")
    converse_args: dict[str, Any] = {
        "modelId": MODEL_ID,
        "messages": [{"role": "user", "content": [{"text": prompt}]}],
        "inferenceConfig": {"maxTokens": 300, "temperature": 0},
    }
    if GUARDRAIL_ID:
        converse_args["guardrailConfig"] = {
            "guardrailIdentifier": GUARDRAIL_ID,
            "guardrailVersion": GUARDRAIL_VERSION,
            "trace": "enabled",
        }
    response = client.converse(**converse_args)
    answer = response["output"]["message"]["content"][0]["text"]
    usage = response.get("usage", {})
    _stage(stages, "bedrock_completed", usage=usage)
    guardrail_trace = response.get("trace", {}).get("guardrail", {})
    _stage(
        stages,
        "guardrail_checked",
        decision="allow",
        guardrail_id=GUARDRAIL_ID,
        violations=guardrail_trace.get("assessments", []),
    )
    _stage(stages, "response_emitted", approval_required=True, order_execution=False)

    return {
        "request_id": request_id,
        "identity": identity,
        "model_id": MODEL_ID,
        "answer": answer,
        "usage": usage,
        "approval_required": True,
        "order_execution": False,
        "workflow_stages": stages,
        "reasoning_note": "Observable workflow stages are returned; private model chain-of-thought is not logged.",
    }


if __name__ == "__main__":
    app.run()
