"""Build agent context from named, inspectable sources."""

import json
from typing import Any, TypedDict

CONTEXT_SOURCE_ORDER = (
    "user_role",
    "portfolio_state",
    "market_data",
    "retrieved_research",
    "memory",
    "tool_outputs",
    "skills",
)


class ContextSources(TypedDict):
    user_role: dict[str, Any]
    portfolio_state: dict[str, Any]
    market_data: dict[str, Any]
    retrieved_research: dict[str, Any]
    memory: list[dict[str, Any]]
    tool_outputs: list[dict[str, Any]]
    skills: list[str]


class ContextBundle(TypedDict):
    mode: str
    sources: ContextSources
    rendered: str


def build_full_context(sources: ContextSources) -> ContextBundle:
    """Render every named source in full as the Day 4 overload baseline."""
    missing = set(CONTEXT_SOURCE_ORDER) - set(sources)
    unexpected = set(sources) - set(CONTEXT_SOURCE_ORDER)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing sources: {', '.join(sorted(missing))}")
        if unexpected:
            details.append(f"unexpected sources: {', '.join(sorted(unexpected))}")
        raise ValueError("; ".join(details))

    sections = [
        f"## {source_name}\n"
        f"{json.dumps(sources[source_name], sort_keys=True, indent=2)}"
        for source_name in CONTEXT_SOURCE_ORDER
    ]
    return {
        "mode": "full",
        "sources": sources,
        "rendered": "\n\n".join(sections),
    }
