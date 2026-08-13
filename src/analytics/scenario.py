"""Deterministic rates and credit scenario analysis for portfolio positions."""

from collections.abc import Sequence
from typing import Literal, TypedDict

from src.observability.telemetry import traced_analytics


class ScenarioPosition(TypedDict, total=False):
    security_id: str
    weight: float
    duration: float
    spread_duration: float
    beta: float


class ScenarioResult(TypedDict):
    scenario_type: str
    shock_bps: float
    horizon: str
    portfolio_return_impact: float
    position_impacts: list[dict[str, float | str]]
    assumptions: list[str]
    mock: bool


@traced_analytics("scenario_analysis")
def scenario_analysis(
    positions: Sequence[ScenarioPosition],
    scenario_type: Literal["rates", "credit"],
    shock_bps: float,
    *,
    horizon: str = "instantaneous",
) -> ScenarioResult:
    """Estimate first-order portfolio return impact from a rate or spread shock."""
    if not positions:
        raise ValueError("at least one position is required")
    if scenario_type not in ("rates", "credit"):
        raise ValueError("scenario_type must be 'rates' or 'credit'")
    if shock_bps == 0:
        raise ValueError("shock_bps must not be zero")
    if not horizon.strip():
        raise ValueError("horizon must not be empty")

    total_weight = sum(float(position.get("weight", 0)) for position in positions)
    if total_weight <= 0 or total_weight > 1.0000001:
        raise ValueError("position weights must be positive and sum to at most 1")

    impacts: list[dict[str, float | str]] = []
    portfolio_impact = 0.0
    for position in positions:
        security_id = str(position.get("security_id", "unknown"))
        weight = float(position.get("weight", 0))
        sensitivity = float(
            position.get(
                "duration" if scenario_type == "rates" else "spread_duration", 0
            )
        )
        if sensitivity < 0 or weight < 0:
            raise ValueError("weights and sensitivities must be non-negative")
        impact = -weight * sensitivity * shock_bps / 10_000
        portfolio_impact += impact
        impacts.append({"security_id": security_id, "weight": weight, "impact": impact})

    return {
        "scenario_type": scenario_type,
        "shock_bps": float(shock_bps),
        "horizon": horizon,
        "portfolio_return_impact": portfolio_impact,
        "position_impacts": impacts,
        "assumptions": [
            "First-order duration/spread-duration approximation; convexity is excluded.",
            "Position weights and sensitivities are supplied by the caller.",
            "Portfolio positions are mock unless an external provenance record says otherwise.",
        ],
        "mock": True,
    }
