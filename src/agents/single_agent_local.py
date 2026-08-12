"""Local-model variant of the Day 4 single Deep Agent."""

from collections.abc import Collection
from typing import Any

from langchain_ollama import ChatOllama
from langgraph.graph.state import CompiledStateGraph

from src.agents.single_agent import create_single_agent, invoke_single_agent
from src.context.builder import ContextSources
from src.control.identity import identity_from_sources

DEFAULT_LOCAL_MODEL = "qwen3:4b"


def create_local_agent(
    identity: str,
    model_name: str = DEFAULT_LOCAL_MODEL,
) -> CompiledStateGraph:
    """Construct the same agent with a local Ollama chat model."""
    return create_single_agent(
        identity,
        model=ChatOllama(
            model=model_name,
            temperature=0,
            validate_model_on_init=True,
        ),
    )


def invoke_local_agent(
    question: str,
    sources: ContextSources,
    *,
    agent: CompiledStateGraph | None = None,
    relevant_sources: Collection[str] | None = None,
) -> dict[str, Any]:
    """Invoke the local variant through the shared context path."""
    return invoke_single_agent(
        question,
        sources,
        agent=agent or create_local_agent(identity_from_sources(sources)),
        relevant_sources=relevant_sources,
        model_name=f"ollama:{DEFAULT_LOCAL_MODEL}",
    )
