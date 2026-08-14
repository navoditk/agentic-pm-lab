import pytest
from langchain_core.messages import AIMessage

from src.agents.devils_advocate import (
    CHALLENGE_CATEGORIES,
    challenge_thesis,
    create_devils_advocate_agent,
    run_committee_challenge,
)
from tests.unit.agents.fakes import ScriptedToolCallingModel

THESIS = {
    "thesis_id": "THESIS-001",
    "claims": [
        {
            "claim_id": "C1",
            "text": "Issuer A can absorb higher funding costs.",
            "evidence_ids": ["E1"],
            "causal": True,
        },
        {
            "claim_id": "C2",
            "text": "The position is diversifying.",
            "evidence_ids": [],
            "causal": False,
        },
    ],
    "evidence": [
        {
            "evidence_id": "E1",
            "publication_date": "2026-07-01",
            "contradicts_claim": True,
            "supports_causality": False,
        },
    ],
    "allocation": [
        {"security_id": "ISSUER-A", "weight": 0.40, "liquidity_status": "illiquid"},
    ],
    "invalidation_conditions": [],
}


def test_challenge_covers_adversarial_categories_and_preserves_uncertainty():
    result = challenge_thesis(THESIS, decision_date="2026-08-13")

    assert result["status"] == "challenged"
    assert result["recommendation"] == "revise_or_decline"
    assert result["approved"] is False
    assert result["critic_may_approve"] is False
    assert set(result["coverage"]["categories"]) == set(CHALLENGE_CATEGORIES)
    assert result["coverage"]["coverage_ratio"] == 1.0
    assert {item["category"] for item in result["findings"]} == {
        "missing_evidence",
        "contradictory_data",
        "stale_sources",
        "concentration_risk",
        "liquidity_risk",
        "unsupported_causality",
        "invalidation_conditions",
    }


def test_clean_thesis_has_no_false_positive_findings():
    thesis = {
        "thesis_id": "THESIS-CLEAN",
        "claims": [{"claim_id": "C1", "evidence_ids": ["E1"], "causal": False}],
        "evidence": [{"evidence_id": "E1", "publication_date": "2026-08-10"}],
        "allocation": [
            {"security_id": "A", "weight": 0.10, "liquidity_status": "liquid"}
        ],
        "invalidation_conditions": ["funding spread exceeds 100 bps"],
    }

    result = challenge_thesis(thesis, decision_date="2026-08-13")

    assert result["status"] == "no_findings"
    assert result["findings"] == []


def test_committee_requires_separate_human_reviewer():
    pending = run_committee_challenge(THESIS, decision_date="2026-08-13")
    approved = run_committee_challenge(
        THESIS,
        decision_date="2026-08-13",
        human_reviewer="ADMIN_USER",
        approval="approve",
    )

    assert pending["status"] == "pending_human_review"
    assert pending["approved"] is False
    assert approved["status"] == "approved"
    assert approved["reviewer"] == "ADMIN_USER"
    assert approved["approved"] is True


def test_critic_cannot_approve_and_agent_has_no_tools():
    with pytest.raises(PermissionError, match="cannot approve"):
        run_committee_challenge(
            THESIS,
            decision_date="2026-08-13",
            human_reviewer="DEVILS_ADVOCATE",
            approval="approve",
        )

    agent = create_devils_advocate_agent(
        ScriptedToolCallingModel(responses=[AIMessage(content="critique")])
    )
    assert agent.name == "devils-advocate"
