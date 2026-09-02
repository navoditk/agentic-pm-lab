"""Permanently mocked public-research adapter."""

from src.observability.telemetry import traced_analytics


@traced_analytics("get_research_summary")
def get_research_summary(query: str) -> dict[str, str | bool]:
    """# MOCK — stays mocked; real research is a deferred non-goal (docs/architecture/PRD.md §6)."""
    if not query.strip():
        raise ValueError("query must not be empty")
    return {
        "query": query,
        "summary": "mock research summary",
        "mock": True,
    }
