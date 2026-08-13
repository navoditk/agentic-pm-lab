"""AWS Bedrock AgentCore direct-code runtime entrypoint."""

from __future__ import annotations

import os
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agents.multi_agent import create_multi_agent, invoke_multi_agent

app = BedrockAgentCoreApp()


def _require_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value


@app.entrypoint
def invoke(payload: dict[str, Any]) -> dict[str, Any]:
    """Invoke the governed Portfolio Manager from AgentCore Runtime."""
    if not isinstance(payload, dict):
        raise TypeError("invocation payload must be an object")
    identity = _require_string(payload, "identity")
    question = _require_string(payload, "question")
    sources = payload.get("sources")
    if not isinstance(sources, dict):
        raise TypeError("sources must be an object")
    model = os.getenv(
        "AGENTCORE_MODEL",
        "bedrock_converse:anthropic.claude-3-5-sonnet-20240620-v1:0",
    )
    result = invoke_multi_agent(
        question,
        {**sources, "user_role": {"identity": identity}},
        model_name=model,
        agent=create_multi_agent(identity, model=model),
    )
    return {
        "identity": identity,
        "model": model,
        "result": result,
        "runtime": "amazon-bedrock-agentcore",
        "approval_required": True,
    }


if __name__ == "__main__":  # pragma: no cover
    app.run()
