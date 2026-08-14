from src.agents.investment_research import research_specialist_subagents


def test_research_workflow_has_three_isolated_specialists():
    specs = {spec["name"]: spec for spec in research_specialist_subagents("PM_USER")}

    assert set(specs) == {
        "quantitative-analysis",
        "news-research",
        "smart-summarizer",
    }
    assert {tool.name for tool in specs["quantitative-analysis"]["tools"]} == {
        "get_volatility",
        "get_max_drawdown",
        "get_risk_metrics",
        "run_factor_regression",
        "scenario_analysis",
        "optimize_portfolio",
        "interpolate_curve",
    }
    assert {tool.name for tool in specs["news-research"]["tools"]} == {
        "get_research_summary"
    }
    assert specs["smart-summarizer"]["tools"] == ()


def test_risk_identity_cannot_bind_research_tool():
    specs = {spec["name"]: spec for spec in research_specialist_subagents("RISK_USER")}

    assert {tool.name for tool in specs["news-research"]["tools"]} == set()
    assert "get_risk_metrics" in {
        tool.name for tool in specs["quantitative-analysis"]["tools"]
    }
