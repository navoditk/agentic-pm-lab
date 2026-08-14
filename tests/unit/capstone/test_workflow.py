from pathlib import Path

import pytest

from src.capstone.workflow import run_institutional_pm_capstone
from src.control.audit import read_audit_log


def test_capstone_keeps_structured_and_unstructured_provenance_separate(tmp_path: Path):
    result = run_institutional_pm_capstone(
        identity="PM_USER",
        portfolio_id="PORT_A",
        decision_date="2026-08-13",
        audit_log_path=tmp_path / "audit.jsonl",
    )

    assert result["evaluation"]["status"] == "pass"
    assert (
        result["provenance_paths"]["structured_calculations"]["rates_scenario"][
            "shock_bps"
        ]
        == 50.0
    )
    assert result["provenance_paths"]["unstructured_evidence"][0]["mock"] is True
    assert result["committee_artifact"]["status"] == "pending_human_review"
    assert result["committee_artifact"]["approved"] is False
    assert result["versions"]["prompt_version"] == "institutional-pm-capstone-v1"
    assert result["live_provider_evidence"] is False
    assert len(read_audit_log(tmp_path / "audit.jsonl")) == 1


def test_capstone_fixed_income_includes_clean_dirty_accrued_and_hedge(tmp_path: Path):
    result = run_institutional_pm_capstone(
        identity="PM_USER",
        portfolio_id="PORT_A",
        decision_date="2026-08-13",
        audit_log_path=tmp_path / "audit.jsonl",
    )
    fixed_income = result["provenance_paths"]["structured_calculations"]["fixed_income"]
    hedge = result["provenance_paths"]["structured_calculations"]["hedge"]

    assert fixed_income["validation"]["status"] == "valid"
    assert fixed_income["dirty_price"] == pytest.approx(
        fixed_income["clean_price"] + fixed_income["accrued_interest"]
    )
    assert hedge["action"] == "human_review_only"
    assert hedge["order_generated"] is False


def test_capstone_requires_authentication_and_portfolio_entitlement(tmp_path: Path):
    with pytest.raises(PermissionError, match="not recognized"):
        run_institutional_pm_capstone(
            identity="UNKNOWN",
            portfolio_id="PORT_A",
            decision_date="2026-08-13",
            audit_log_path=tmp_path / "audit.jsonl",
        )
    with pytest.raises(PermissionError, match="not authorized"):
        run_institutional_pm_capstone(
            identity="PM_USER",
            portfolio_id="PORT_B",
            decision_date="2026-08-13",
            audit_log_path=tmp_path / "audit.jsonl",
        )


def test_capstone_human_reviewer_can_reject_but_not_auto_approve(tmp_path: Path):
    result = run_institutional_pm_capstone(
        identity="PM_USER",
        portfolio_id="PORT_A",
        decision_date="2026-08-13",
        audit_log_path=tmp_path / "audit.jsonl",
        human_reviewer="ADMIN_USER",
        approval="reject",
    )
    assert result["committee_artifact"]["status"] == "rejected"
    assert result["committee_artifact"]["approved"] is False
