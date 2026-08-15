from pathlib import Path

from scripts.run_canvas_pm_workflow import run_workflow


def test_fixture_workflow_returns_stage_trace_and_token_accounting(tmp_path: Path):
    result = run_workflow(
        question="What happens if rates rise by 50 bps?",
        identity="PM_USER",
        portfolio_id="PORT_A",
        decision_date="2026-08-13",
        mode="fixture",
        audit_log=tmp_path / "audit.jsonl",
    )

    assert result["status"] == "completed"
    assert result["mode"] == "fixture"
    assert result["execution_trace"]
    assert result["token_usage"]["total_tokens"] > 0
    assert result["cost"]["estimated_usd"] == 0.0
    assert result["private_chain_of_thought_captured"] is False
    assert result.get("audit_events", True)


def test_provider_mode_is_explicitly_blocked_without_fallback(tmp_path: Path):
    result = run_workflow(
        question="What are the largest current portfolio risks?",
        identity="PM_USER",
        portfolio_id="PORT_A",
        decision_date="2026-08-13",
        mode="openai",
        audit_log=tmp_path / "audit.jsonl",
    )

    assert result["status"] == "blocked"
    assert result["provider_configured"] is False
    assert result["token_usage"]["total_tokens"] == 0
    assert "fixture result was substituted" in result["reason"]
