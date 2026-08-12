"""Portfolio Manager orchestration over domain-specialist Deep Agents."""

from collections.abc import Collection, Mapping, Sequence
from typing import Any

from deepagents import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent, SubAgent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool, tool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from src.agents.recovery import (
    orchestrator_recovery_middleware,
    specialist_recovery_middleware,
)
from src.agents.single_agent import (
    DEFAULT_MODEL,
    get_max_drawdown,
    get_portfolio_exposure,
    get_risk_metrics,
    get_volatility,
    interpolate_curve_tool,
    price_bond_tool,
    run_backtest_tool,
    run_factor_regression,
)
from src.analytics.research import get_research_summary
from src.context.builder import (
    ContextSources,
    build_filtered_context,
    build_full_context,
)
from src.control.authorization import tools_for_identity
from src.control.identity import identity_from_sources
from src.observability.telemetry import observe_agent_run

PORTFOLIO_MANAGER_PROMPT = """You are the Portfolio Manager orchestrator.
Delegate domain analysis through the task tool: macro for rates and curves,
quant for portfolio risk/econometrics/backtests, and fundamental for holdings
and research. For cross-cutting questions, call every relevant specialist and
then synthesize their results. Include the supplied data needed by a specialist
in its task description because specialists have isolated context. Attribute
each conclusion to its specialist. Copy all calculation parameters, units, and
annualization assumptions into the task description exactly as supplied. Never
calculate a numeric claim yourself, invent missing data, treat a dead-letter
result as success, or treat mocked research/classifications as real.
"""

MACRO_PROMPT = """You are the Macro specialist.
Answer only rates, curve, regime, and liquidity questions. Use your
deterministic tools for every numeric claim. State when the supplied data cannot
answer a regime or liquidity question; never invent market data.
"""

QUANT_PROMPT = """You are the Quant/Risk specialist.
Answer only risk, factor, concentration, and backtest questions. Use
deterministic tools for every numeric claim and state assumptions and data
limitations. Preserve the supplied calculation parameters exactly and disclose
the window and annualization used. Treat dead-letter tool output as a failure,
not data. Do not make unsupported investment recommendations.
"""

FUNDAMENTAL_PROMPT = """You are the Fundamental specialist.
Answer only holdings, benchmark, attribution, and research questions. Use the
portfolio tool for exposure claims and the research tool for research claims.
Always label security-master classifications and research as mocked.
"""


@tool("get_research_summary")
def get_research_summary_tool(query: str) -> dict[str, str | bool]:
    """Return a clearly labeled mocked research summary."""
    return get_research_summary(query)


MACRO_TOOLS: tuple[BaseTool, ...] = (
    interpolate_curve_tool,
    price_bond_tool,
)

QUANT_TOOLS: tuple[BaseTool, ...] = (
    get_volatility,
    get_max_drawdown,
    get_risk_metrics,
    run_factor_regression,
    run_backtest_tool,
)

FUNDAMENTAL_TOOLS: tuple[BaseTool, ...] = (
    get_portfolio_exposure,
    get_research_summary_tool,
)


def specialist_subagents(
    identity: str,
    models: Mapping[str, str | BaseChatModel] | None = None,
) -> list[SubAgent]:
    """Build the three domain specialists with non-overlapping tool sets."""
    configured_models = models or {}
    definitions: tuple[
        tuple[str, str, str, tuple[BaseTool, ...]],
        ...,
    ] = (
        (
            "macro",
            "Rates, yield-curve, macro-regime, and liquidity analysis.",
            MACRO_PROMPT,
            MACRO_TOOLS,
        ),
        (
            "quant",
            "Portfolio risk, factor, concentration, and backtest analysis.",
            QUANT_PROMPT,
            QUANT_TOOLS,
        ),
        (
            "fundamental",
            "Holdings, benchmark, attribution, and mocked research analysis.",
            FUNDAMENTAL_PROMPT,
            FUNDAMENTAL_TOOLS,
        ),
    )

    subagents: list[SubAgent] = []
    for name, description, system_prompt, tools in definitions:
        spec: SubAgent = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "tools": tools_for_identity(identity, tools),
        }
        if name in configured_models:
            spec["model"] = configured_models[name]
        if name == "quant":
            spec["skills"] = ["./skills/scenario-analysis/"]
        spec["middleware"] = list(specialist_recovery_middleware())
        subagents.append(spec)
    return subagents


def create_multi_agent(
    identity: str,
    model: str | BaseChatModel = DEFAULT_MODEL,
    *,
    specialist_models: Mapping[str, str | BaseChatModel] | None = None,
    subagents: Sequence[SubAgent | CompiledSubAgent] | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Construct the Portfolio Manager with Macro, Quant, and Fundamental sub-agents."""
    return create_deep_agent(
        model=model,
        tools=(),
        system_prompt=PORTFOLIO_MANAGER_PROMPT,
        middleware=orchestrator_recovery_middleware(),
        subagents=subagents or specialist_subagents(identity, specialist_models),
        skills=["./skills/"],
        checkpointer=checkpointer,
        name="portfolio-manager",
    )


def create_checkpointed_multi_agent(
    identity: str,
    model: str | BaseChatModel = DEFAULT_MODEL,
    *,
    specialist_models: Mapping[str, str | BaseChatModel] | None = None,
    subagents: Sequence[SubAgent | CompiledSubAgent] | None = None,
) -> CompiledStateGraph:
    """Construct a process-local checkpointed orchestrator for development."""
    return create_multi_agent(
        identity,
        model=model,
        specialist_models=specialist_models,
        subagents=subagents,
        checkpointer=InMemorySaver(),
    )


def invoke_multi_agent(
    question: str,
    sources: ContextSources,
    *,
    agent: CompiledStateGraph | None = None,
    relevant_sources: Collection[str] | None = None,
    thread_id: str | None = None,
    iteration_limit: int = 50,
    model_name: str | None = None,
    callbacks: Sequence[BaseCallbackHandler] = (),
) -> dict[str, Any]:
    """Invoke the Portfolio Manager with context from named sources only."""
    context = (
        build_filtered_context(sources, relevant_sources)
        if relevant_sources is not None
        else build_full_context(sources)
    )
    runtime = agent or create_multi_agent(identity_from_sources(sources))
    prompt = f"{context['rendered']}\n\n## question\n{question}"
    config: dict[str, Any] = {"recursion_limit": iteration_limit}
    if thread_id is not None:
        config["configurable"] = {"thread_id": thread_id}
    observed_model = model_name or (
        DEFAULT_MODEL if agent is None else "configured-agent"
    )
    with observe_agent_run(
        "agent.portfolio_manager.invoke",
        observed_model,
    ) as (_span, metrics):
        config["callbacks"] = [metrics, *callbacks]
        return runtime.invoke(
            {"messages": [{"role": "user", "content": prompt}]},
            config=config,
        )


def resume_multi_agent(
    agent: CompiledStateGraph,
    thread_id: str,
    *,
    iteration_limit: int = 50,
) -> dict[str, Any]:
    """Resume a checkpointed workflow without submitting the original input again."""
    if not thread_id:
        raise ValueError("thread_id must not be empty")
    with observe_agent_run(
        "agent.portfolio_manager.resume",
        "configured-agent",
    ) as (_span, metrics):
        return agent.invoke(
            None,
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": iteration_limit,
                "callbacks": [metrics],
            },
        )
