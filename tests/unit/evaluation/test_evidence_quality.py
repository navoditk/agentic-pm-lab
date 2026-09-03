from src.evaluation.evidence_quality import (
    abstention_check,
    citation_completeness,
    contradiction_check,
    evaluate_evidence_bundle,
)


def test_citations_require_known_evidence_ids_for_every_claim():
    result = citation_completeness(
        [
            {"id": "rates", "evidence_ids": ["curve-1"]},
            {"id": "credit", "evidence_ids": ["missing"]},
        ],
        {"curve-1"},
    )

    assert result["status"] == "fail"
    assert result["invalid_evidence_ids"] == ["credit:missing"]


def test_abstention_and_contradiction_are_independent_dimensions():
    assert (
        abstention_check(
            "This is mock data and requires human review.",
            required_disclosures=["mock data", "human review"],
        )["status"]
        == "pass"
    )
    assert (
        contradiction_check(
            [
                {"subject": "curve", "value": "steepening"},
                {"subject": "curve", "value": "flattening"},
            ]
        )["status"]
        == "fail"
    )


def test_bundle_passes_for_grounded_bounded_answer():
    result = evaluate_evidence_bundle(
        claims=[
            {
                "id": "risk",
                "evidence_ids": ["risk-1"],
                "subject": "rates",
                "value": "-2%",
            }
        ],
        valid_evidence_ids={"risk-1"},
        answer="The result uses mock data and requires human review.",
        required_disclosures=["mock data", "human review"],
    )

    assert result["status"] == "pass"
