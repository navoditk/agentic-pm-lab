from scripts.check_docs_consistency import check


def test_current_documentation_claims_are_consistent():
    assert check() == []
