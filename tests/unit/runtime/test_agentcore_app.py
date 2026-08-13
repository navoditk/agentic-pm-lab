from typing import Any

import pytest

from src.runtime import agentcore_app


def test_agentcore_entrypoint_rejects_malformed_payload() -> None:
    with pytest.raises(ValueError, match="question"):
        agentcore_app.invoke({"identity": "PM_USER", "sources": {}})


def test_agentcore_entrypoint_preserves_identity_and_marks_approval(
    monkeypatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_create(identity: str, model: str):
        captured["create"] = (identity, model)
        return "fake-agent"

    def fake_invoke(question: str, sources: dict[str, Any], **kwargs):
        captured["invoke"] = (question, sources, kwargs)
        return {"messages": [{"content": "approved test result"}]}

    monkeypatch.setattr(agentcore_app, "create_multi_agent", fake_create)
    monkeypatch.setattr(agentcore_app, "invoke_multi_agent", fake_invoke)
    result = agentcore_app.invoke(
        {
            "identity": "PM_USER",
            "question": "Review risk",
            "sources": {"market_data": {}},
        }
    )

    assert result["runtime"] == "amazon-bedrock-agentcore"
    assert result["approval_required"] is True
    assert captured["invoke"][1]["user_role"] == {"identity": "PM_USER"}
