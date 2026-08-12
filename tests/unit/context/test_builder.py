import pytest

from src.context.builder import (
    CONTEXT_SOURCE_ORDER,
    build_filtered_context,
    build_full_context,
    count_context_tokens,
)


@pytest.fixture
def context_sources():
    return {
        "user_role": {"identity": "PM_USER", "role": "pm"},
        "portfolio_state": {"portfolio_id": "PORT_A"},
        "market_data": {"returns": [0.01, -0.01]},
        "retrieved_research": {"summary": "mock research"},
        "memory": [{"summary": "prior turn"}],
        "tool_outputs": [{"tool": "get_volatility", "result": 0.2}],
        "skills": ["portfolio-risk-summary"],
    }


def test_full_context_includes_every_named_source_in_order(context_sources):
    bundle = build_full_context(context_sources)

    assert bundle["mode"] == "full"
    assert tuple(bundle["sources"]) == CONTEXT_SOURCE_ORDER
    headings = [f"## {source_name}" for source_name in CONTEXT_SOURCE_ORDER]
    assert [bundle["rendered"].index(heading) for heading in headings] == sorted(
        bundle["rendered"].index(heading) for heading in headings
    )


def test_filtered_context_includes_only_explicit_sources(context_sources):
    bundle = build_filtered_context(
        context_sources,
        ["user_role", "market_data", "skills"],
    )

    assert tuple(bundle["sources"]) == ("user_role", "market_data", "skills")
    assert "retrieved_research" not in bundle["rendered"]
    assert count_context_tokens(bundle["rendered"]) > 0


def test_filtered_context_requires_identity_context(context_sources):
    with pytest.raises(ValueError, match="user_role is required"):
        build_filtered_context(context_sources, ["market_data"])


def test_full_context_rejects_missing_named_source(context_sources):
    del context_sources["memory"]

    with pytest.raises(ValueError, match="missing sources: memory"):
        build_full_context(context_sources)
