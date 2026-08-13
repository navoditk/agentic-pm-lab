"""Memory boundary for PM preferences and session context.

The in-memory implementation keeps Day 13 deterministic and network-free.  The
protocol is intentionally small so an AgentCore Memory client can be injected
when the AWS account is available without changing the agent's business logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol


@dataclass(frozen=True)
class MemoryItem:
    """A user-scoped memory item with an explicit scope and timestamp."""

    identity: str
    text: str
    scope: str = "long_term"
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.identity.strip():
            raise ValueError("identity must not be empty")
        if not self.text.strip():
            raise ValueError("text must not be empty")
        if self.scope not in {"short_term", "long_term"}:
            raise ValueError("scope must be short_term or long_term")
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(UTC).isoformat())


class MemoryStore(Protocol):
    """Minimal contract consumed by PM agent orchestration."""

    def remember(self, item: MemoryItem) -> None: ...

    def recall(
        self, identity: str, *, scope: str | None = None
    ) -> list[MemoryItem]: ...


class InMemoryMemoryStore:
    """Deterministic local substitute for AgentCore Memory."""

    def __init__(self) -> None:
        self._items: list[MemoryItem] = []

    def remember(self, item: MemoryItem) -> None:
        if not isinstance(item, MemoryItem):
            raise TypeError("item must be a MemoryItem")
        self._items.append(item)

    def recall(self, identity: str, *, scope: str | None = None) -> list[MemoryItem]:
        if not identity.strip():
            raise ValueError("identity must not be empty")
        if scope is not None and scope not in {"short_term", "long_term"}:
            raise ValueError("scope must be short_term or long_term")
        return [
            item
            for item in self._items
            if item.identity == identity and (scope is None or item.scope == scope)
        ]


def memory_context(store: MemoryStore, identity: str) -> list[dict[str, str]]:
    """Serialize recalled memory for explicit, auditable context injection."""
    return [
        {"scope": item.scope, "text": item.text, "created_at": item.created_at}
        for item in store.recall(identity)
    ]
