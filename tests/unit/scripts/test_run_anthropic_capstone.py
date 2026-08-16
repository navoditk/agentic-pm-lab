from pathlib import Path
from types import SimpleNamespace

from scripts import run_anthropic_capstone


def test_direct_anthropic_capstone_records_usage_and_governance(
    monkeypatch, tmp_path: Path
):
    class FakeMessages:
        def create(self, **kwargs):
            assert kwargs["model"] == "claude-haiku-4-5-20251001"
            return SimpleNamespace(
                id="msg_test",
                stop_reason="end_turn",
                content=[SimpleNamespace(type="text", text="committee summary")],
                usage=SimpleNamespace(input_tokens=11, output_tokens=7),
            )

    class FakeClient:
        def __init__(self):
            self.messages = FakeMessages()

    monkeypatch.setattr(run_anthropic_capstone.anthropic, "Anthropic", FakeClient)
    result = run_anthropic_capstone.run_capstone(
        question="What changed?",
        identity="PM_USER",
        portfolio_id="PORT_A",
        decision_date="2026-08-13",
        audit_log=tmp_path / "audit.jsonl",
    )

    assert result["answer"] == "committee summary"
    assert result["usage"] == {
        "input_tokens": 11,
        "output_tokens": 7,
        "total_tokens": 18,
    }
    assert result["approval_required"] is True
    assert result["order_execution"] is False
    assert result["pricing"]["estimated_token_cost_usd"] == 0.000046
    assert result["reasoning_note"]
    assert result["workflow_stages"][-1]["stage"] == "response_emitted"
