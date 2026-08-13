import pytest

from src.runtime.memory import InMemoryMemoryStore, MemoryItem, memory_context


def test_memory_isolated_by_identity_and_scope() -> None:
    store = InMemoryMemoryStore()
    store.remember(
        MemoryItem("PM_USER", "Compare correlation against AGG.", "long_term")
    )
    store.remember(MemoryItem("PM_USER", "Current question context.", "short_term"))
    store.remember(MemoryItem("RISK_USER", "Use stress limits.", "long_term"))

    assert [item.text for item in store.recall("PM_USER", scope="long_term")] == [
        "Compare correlation against AGG."
    ]
    assert store.recall("RISK_USER", scope="short_term") == []


def test_memory_context_is_explicitly_serialized() -> None:
    store = InMemoryMemoryStore()
    store.remember(MemoryItem("PM_USER", "Flag concentration above 5%.", "long_term"))

    context = memory_context(store, "PM_USER")

    assert context[0]["scope"] == "long_term"
    assert context[0]["text"] == "Flag concentration above 5%."
    assert "created_at" in context[0]


@pytest.mark.parametrize("scope", ["", "session", "durable"])
def test_memory_rejects_unknown_scope(scope: str) -> None:
    with pytest.raises(ValueError, match="scope"):
        MemoryItem("PM_USER", "preference", scope)
