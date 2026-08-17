from pathlib import Path
from types import SimpleNamespace

from scripts import run_openai_capstone


def test_direct_openai_capstone_records_usage_and_governance(
    monkeypatch, tmp_path: Path
):
    class FakeResponses:
        def create(self, **kwargs):
            assert kwargs["model"] == "gpt-4.1-mini"
            return SimpleNamespace(
                id="resp_test",
                status="completed",
                output_text="committee summary",
                usage=SimpleNamespace(
                    input_tokens=11, output_tokens=7, total_tokens=18
                ),
            )

    class FakeClient:
        def __init__(self):
            self.responses = FakeResponses()

    monkeypatch.setattr(run_openai_capstone, "OpenAI", FakeClient)
    result = run_openai_capstone.run_capstone(
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
    assert result["pricing"]["estimated_token_cost_usd"] == 0.0000156
    assert result["reasoning_note"]
