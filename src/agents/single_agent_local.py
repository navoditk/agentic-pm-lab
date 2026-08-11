"""Local-model variant of the Day 4 single Deep Agent."""

from typing import Any

from langchain_ollama import ChatOllama
from langgraph.graph.state import CompiledStateGraph

from src.agents.single_agent import create_single_agent, invoke_single_agent
from src.context.builder import ContextSources

DEFAULT_LOCAL_MODEL = "qwen3:4b"


def create_local_agent(
    model_name: str = DEFAULT_LOCAL_MODEL,
) -> CompiledStateGraph:
    """Construct the same agent with a local Ollama chat model."""
    return create_single_agent(
        model=ChatOllama(
            model=model_name,
            temperature=0,
            validate_model_on_init=True,
        )
    )


def invoke_local_agent(
    question: str,
    sources: ContextSources,
    *,
    agent: CompiledStateGraph | None = None,
) -> dict[str, Any]:
    """Invoke the local variant through the shared context path."""
    return invoke_single_agent(
        question,
        sources,
        agent=agent or create_local_agent(),
    )
