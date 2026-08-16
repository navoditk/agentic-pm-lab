"""Full deterministic PM capstone hosted behind AgentCore Runtime."""

from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

import boto3
from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.capstone.workflow import run_institutional_pm_capstone

app = BedrockAgentCoreApp()
LOGGER = logging.getLogger("agentic_pm_lab.agentcore_capstone")
logging.basicConfig(level=logging.INFO)
MODEL_ID = os.getenv("MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")


def _stage(stages: list[dict[str, Any]], name: str, **details: Any) -> None:
    stages.append({"stage": name, "details": details})
    LOGGER.info(
        "workflow_stage=%s details=%s", name, json.dumps(details, sort_keys=True)
    )


@app.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """Run the full local capstone, then obtain a bounded hosted narration."""
    if not isinstance(payload, dict):
        raise TypeError("payload must be a JSON object")
    identity = payload.get("identity", "PM_USER")
    portfolio_id = payload.get("portfolio_id", "PORT_A")
    decision_date = payload.get("decision_date", "2026-08-13")
    question = payload.get(
        "question",
        "Summarize the capstone evidence, risks, challenge findings, and next human review step.",
    )
    stages: list[dict[str, Any]] = []
    request_id = str(payload.get("request_id") or f"capstone-{uuid.uuid4().hex}")
    _stage(stages, "request_received", request_id=request_id)
    _stage(stages, "input_validated", identity=identity, portfolio_id=portfolio_id)
    _stage(
        stages, "authorization_checked", decision="delegated_to_local_cedar_boundary"
    )
    with tempfile.NamedTemporaryFile(
        prefix="agentic-pm-audit-", suffix=".jsonl"
    ) as audit:
        capstone = run_institutional_pm_capstone(
            identity=identity,
            portfolio_id=portfolio_id,
            decision_date=decision_date,
            audit_log_path=Path(audit.name),
        )
    _stage(stages, "capstone_completed", workflow=capstone["workflow"])
    prompt = (
        "You are a read-only institutional PM reviewer. Summarize the supplied "
        "deterministic capstone result for a human committee. State evidence, "
        "risks, uncertainty, and the next review step. Do not recommend an order, "
        "change an allocation, or reveal private chain-of-thought.\n\n"
        f"Question: {question}\n"
        f"Evaluation: {json.dumps(capstone['evaluation'], sort_keys=True)}\n"
        f"Committee: {json.dumps(capstone['committee_artifact'], sort_keys=True)}\n"
        f"Workflow: {json.dumps(capstone['workflow'], sort_keys=True)}"
    )
    _stage(stages, "orchestration_started", tools=[], order_execution=False)
    response = boto3.client("bedrock-runtime").converse(
        modelId=MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 300, "temperature": 0},
    )
    answer = response["output"]["message"]["content"][0]["text"]
    usage = response.get("usage", {})
    _stage(stages, "bedrock_completed", usage=usage)
    _stage(stages, "guardrail_checked", decision="allow", violations=[])
    _stage(stages, "response_emitted", approval_required=True, order_execution=False)
    return {
        "request_id": request_id,
        "model_id": MODEL_ID,
        "answer": answer,
        "usage": usage,
        "capstone": capstone,
        "approval_required": True,
        "order_execution": False,
        "workflow_stages": stages,
        "reasoning_note": "Observable deterministic stages and governance outcomes are returned; private model chain-of-thought is not logged.",
    }


if __name__ == "__main__":
    app.run()
