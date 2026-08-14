"""Provider-shaped research fixtures with citation and licensing metadata.

The adapter intentionally returns evidence records, not a generated narrative.
That keeps provider commentary on the retrieval path and prevents it from
silently becoming a risk or allocation input.
"""

from datetime import UTC, datetime
from typing import Any


def mocked_thematic_screen(
    query: str,
    *,
    entity: str,
    publication_time: str,
    retrieval_time: str | None = None,
    novelty: float = 1.0,
    licensing: str = "fixture-only",
) -> dict[str, Any]:
    """Return one cited, clearly mocked thematic-screen evidence record."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if not entity.strip():
        raise ValueError("entity must not be empty")
    _parse_timestamp(publication_time)
    retrieved = retrieval_time or datetime.now(UTC).isoformat()
    _parse_timestamp(retrieved)
    if not 0.0 <= novelty <= 1.0:
        raise ValueError("novelty must be between 0 and 1")
    return {
        "provider": "mock-bigdata-thematic-screen",
        "query": query,
        "entity": entity,
        "publication_time": publication_time,
        "retrieval_time": retrieved,
        "novelty": novelty,
        "licensing": {"state": licensing, "redistribution": "not_permitted"},
        "evidence": {
            "title": f"Mock thematic screen for {entity}",
            "excerpt": f"Fixture evidence matching '{query}' for {entity}.",
            "source_url": "https://example.com/public-fixture/thematic-screen",
        },
        "mock": True,
    }


def _parse_timestamp(value: str) -> None:
    try:
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO timestamp: {value}") from exc
