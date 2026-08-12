"""Ollama/Qwen3 variant of the Day 5 multi-agent hierarchy."""

from collections.abc import Collection
from typing import Any

from langchain_ollama import ChatOllama
from langgraph.graph.state import CompiledStateGraph

from src.agents.multi_agent import create_multi_agent, invoke_multi_agent
from src.context.builder import ContextSources
from src.control.identity import identity_from_sources

DEFAULT_LOCAL_MODEL = "qwen3:4b"
SPECIALIST_NAMES = ("macro", "quant", "fundamental")


def _local_model(model_name: str) -> ChatOllama:
    return ChatOllama(
        model=model_name,
        temperature=0,
        num_predict=512,
        validate_model_on_init=True,
    )


def create_local_multi_agent(
    identity: str,
    model_name: str = DEFAULT_LOCAL_MODEL,
) -> CompiledStateGraph:
    """Construct the Portfolio Manager and each specialist on Ollama."""
    return create_multi_agent(
        identity,
        model=_local_model(model_name),
        specialist_models={name: _local_model(model_name) for name in SPECIALIST_NAMES},
    )


def invoke_local_multi_agent(
    question: str,
    sources: ContextSources,
    *,
    agent: CompiledStateGraph | None = None,
    relevant_sources: Collection[str] | None = None,
    iteration_limit: int = 50,
) -> dict[str, Any]:
    """Invoke the local hierarchy through the shared context path."""
    return invoke_multi_agent(
        question,
        sources,
        agent=agent or create_local_multi_agent(identity_from_sources(sources)),
        relevant_sources=relevant_sources,
        iteration_limit=iteration_limit,
        model_name=f"ollama:{DEFAULT_LOCAL_MODEL}",
    )
