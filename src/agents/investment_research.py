"""Separate Deep Agent workflow for investment research and synthesis."""

from collections.abc import Mapping, Sequence

from deepagents import create_deep_agent
from deepagents.middleware.subagents import CompiledSubAgent, SubAgent
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph

from src.agents.multi_agent import (
    get_max_drawdown,
    get_research_summary_tool,
    get_risk_metrics,
    get_volatility,
    interpolate_curve_tool,
    optimize_portfolio_tool,
    run_factor_regression,
    scenario_analysis_tool,
)
from src.agents.recovery import (
    orchestrator_recovery_middleware,
    specialist_recovery_middleware,
)
from src.agents.single_agent import get_portfolio_exposure
from src.control.authorization import tools_for_identity

RESEARCH_MANAGER_PROMPT = """You are an investment-research supervisor.
Delegate quantitative claims to quantitative-analysis, source interpretation to
news-research, and final synthesis to smart-summarizer. Keep structured market
observations separate from unstructured evidence. Every numeric claim must be
returned by a deterministic tool with parameters and provenance. Every research
claim must cite its evidence record and uncertainty. Never turn narrative text
into a risk number, allocation, or causal claim without a deterministic input.
"""

QUANTITATIVE_PROMPT = """You are the Quantitative Analysis specialist.
Analyze prices, factors, risk, curve shape, scenarios, and optimization using
the supplied deterministic tools. Report inputs, units, windows, annualization,
and point-in-time limitations. Do not infer a risk number from narrative text.
"""

NEWS_RESEARCH_PROMPT = """You are the News/Research specialist.
Use EDGAR and permitted public evidence records supplied in context. Return
citations, publication and retrieval times, novelty, licensing state, and
uncertainty. You may summarize evidence, but you may not create a numeric risk
measure or allocation recommendation from narrative content.
"""

SUMMARIZER_PROMPT = """You are the Smart Summarizer specialist.
Produce a structured synthesis with separate sections for calculations and
evidence. Link every conclusion to a tool result or evidence citation. State
unknowns, stale or mocked sources, licensing limits, and confidence. Do not
fill missing data or hide disagreement between specialists.
"""

QUANTITATIVE_TOOLS: tuple[BaseTool, ...] = (
    get_volatility,
    get_max_drawdown,
    get_risk_metrics,
    run_factor_regression,
    scenario_analysis_tool,
    optimize_portfolio_tool,
    interpolate_curve_tool,
)
NEWS_RESEARCH_TOOLS: tuple[BaseTool, ...] = (get_research_summary_tool,)
SUMMARIZER_TOOLS: tuple[BaseTool, ...] = ()


def research_specialist_subagents(
    identity: str,
    models: Mapping[str, str | BaseChatModel] | None = None,
) -> list[SubAgent]:
    """Build isolated research specialists with governed tool filtering."""
    configured = models or {}
    definitions = (
        (
            "quantitative-analysis",
            "Prices, factors, risk, and optimization.",
            QUANTITATIVE_PROMPT,
            QUANTITATIVE_TOOLS,
        ),
        (
            "news-research",
            "EDGAR and permitted public research evidence.",
            NEWS_RESEARCH_PROMPT,
            NEWS_RESEARCH_TOOLS,
        ),
        (
            "smart-summarizer",
            "Cited structured synthesis and uncertainty.",
            SUMMARIZER_PROMPT,
            SUMMARIZER_TOOLS,
        ),
    )
    result: list[SubAgent] = []
    for name, description, prompt, tools in definitions:
        spec: SubAgent = {
            "name": name,
            "description": description,
            "system_prompt": prompt,
            "tools": tools_for_identity(identity, tools),
            "middleware": list(specialist_recovery_middleware()),
        }
        if name in configured:
            spec["model"] = configured[name]
        result.append(spec)
    return result


def create_investment_research_agent(
    identity: str,
    model: str | BaseChatModel,
    *,
    specialist_models: Mapping[str, str | BaseChatModel] | None = None,
    subagents: Sequence[SubAgent | CompiledSubAgent] | None = None,
) -> CompiledStateGraph:
    """Construct the separate research task graph."""
    return create_deep_agent(
        model=model,
        tools=tools_for_identity(identity, (get_portfolio_exposure,)),
        system_prompt=RESEARCH_MANAGER_PROMPT,
        middleware=orchestrator_recovery_middleware(),
        subagents=subagents
        or research_specialist_subagents(identity, specialist_models),
        name="investment-research-supervisor",
    )
