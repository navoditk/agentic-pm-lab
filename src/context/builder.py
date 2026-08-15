"""Build agent context from named, inspectable sources."""

import json
from collections.abc import Collection
from typing import Any, TypedDict

import tiktoken

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
    sources: dict[str, Any]
    rendered: str


def _render_sources(sources: dict[str, Any]) -> str:
    return "\n\n".join(
        f"## {source_name}\n{json.dumps(value, sort_keys=True, indent=2)}"
        for source_name, value in sources.items()
    )


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

    ordered_sources = {
        source_name: sources[source_name] for source_name in CONTEXT_SOURCE_ORDER
    }
    return {
        "mode": "full",
        "sources": ordered_sources,
        "rendered": _render_sources(ordered_sources),
    }


def build_filtered_context(
    sources: ContextSources,
    relevant_sources: Collection[str],
) -> ContextBundle:
    """Render only explicitly selected named sources."""
    selected = set(relevant_sources)
    unknown = selected - set(CONTEXT_SOURCE_ORDER)
    if unknown:
        raise ValueError(f"unknown sources: {', '.join(sorted(unknown))}")
    if "user_role" not in selected:
        raise ValueError("user_role is required in filtered context")
    filtered = {
        source_name: sources[source_name]
        for source_name in CONTEXT_SOURCE_ORDER
        if source_name in selected
    }
    return {
        "mode": "filtered",
        "sources": filtered,
        "rendered": _render_sources(filtered),
    }


def count_context_tokens(rendered_context: str, model: str = "gpt-4.1-mini") -> int:
    """Count context tokens, with an offline-safe estimate when needed.

    ``tiktoken`` may lazily download an encoding file for a model that is not
    cached. Unit tests and the default Canvas fixture must remain offline, so a
    transparent four-characters-per-token approximation is used as a fallback.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except (KeyError, OSError, ValueError):  # pragma: no cover - cache-dependent
        return max(1, (len(rendered_context) + 3) // 4)
    return len(encoding.encode(rendered_context))
