"""Portfolio exposure and concentration analytics.

Sector and asset-class tags intentionally come from the mock security master
until a public fundamentals source replaces it.
"""

from collections import defaultdict
from collections.abc import Sequence
from typing import TypedDict


class Position(TypedDict):
    security_id: str
    market_value: float


class Security(TypedDict):
    security_id: str
    asset_class: str
    sector: str


class PositionWeight(TypedDict):
    security_id: str
    market_value: float
    weight: float


class PortfolioSummary(TypedDict):
    total_market_value: float
    weights: list[PositionWeight]
    exposure_by_asset_class: dict[str, float]
    exposure_by_sector: dict[str, float]
    largest_position_weight: float
    concentration_hhi: float
    security_master_is_mock: bool


def portfolio_summary(
    positions: Sequence[Position],
    security_master: Sequence[Security],
) -> PortfolioSummary:
    """Calculate weights, grouped exposures, and concentration."""
    if not positions:
        raise ValueError("at least one position is required")
    securities = {security["security_id"]: security for security in security_master}
    missing = sorted(
        {
            position["security_id"]
            for position in positions
            if position["security_id"] not in securities
        }
    )
    if missing:
        raise ValueError(f"security master is missing: {', '.join(missing)}")

    market_values = [float(position["market_value"]) for position in positions]
    if any(value < 0 for value in market_values):
        raise ValueError("market values must be non-negative")
    total_market_value = sum(market_values)
    if total_market_value <= 0:
        raise ValueError("total market value must be positive")

    asset_class_exposure: defaultdict[str, float] = defaultdict(float)
    sector_exposure: defaultdict[str, float] = defaultdict(float)
    weights: list[PositionWeight] = []
    for position, market_value in zip(positions, market_values, strict=True):
        security_id = position["security_id"]
        security = securities[security_id]
        weight = market_value / total_market_value
        weights.append(
            {
                "security_id": security_id,
                "market_value": market_value,
                "weight": weight,
            }
        )
        asset_class_exposure[security["asset_class"]] += weight
        sector_exposure[security["sector"]] += weight

    return {
        "total_market_value": total_market_value,
        "weights": weights,
        "exposure_by_asset_class": dict(sorted(asset_class_exposure.items())),
        "exposure_by_sector": dict(sorted(sector_exposure.items())),
        "largest_position_weight": max(item["weight"] for item in weights),
        "concentration_hhi": sum(item["weight"] ** 2 for item in weights),
        "security_master_is_mock": True,
    }
