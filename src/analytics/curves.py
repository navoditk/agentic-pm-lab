"""Linear interpolation over observed yield-curve tenors."""

from bisect import bisect_right
from collections.abc import Sequence
from itertools import pairwise

from src.observability.telemetry import traced_analytics


def _validated_curve(
    tenors_years: Sequence[float],
    rates_pct: Sequence[float],
) -> tuple[list[float], list[float]]:
    if len(tenors_years) != len(rates_pct):
        raise ValueError("tenors_years and rates_pct must have the same length")
    if len(tenors_years) < 2:
        raise ValueError("at least two curve points are required")
    tenors = [float(tenor) for tenor in tenors_years]
    rates = [float(rate) for rate in rates_pct]
    if any(tenor <= 0 for tenor in tenors):
        raise ValueError("curve tenors must be positive")
    if any(right <= left for left, right in pairwise(tenors)):
        raise ValueError("curve tenors must be strictly increasing")
    return tenors, rates


@traced_analytics("interpolate_curve")
def interpolate_curve(
    tenors_years: Sequence[float],
    rates_pct: Sequence[float],
    target_tenors_years: Sequence[float],
) -> list[float]:
    """Linearly interpolate rates without extrapolating beyond the curve."""
    tenors, rates = _validated_curve(tenors_years, rates_pct)
    interpolated: list[float] = []
    for raw_target in target_tenors_years:
        target = float(raw_target)
        if target < tenors[0] or target > tenors[-1]:
            raise ValueError(
                f"target tenor {target} is outside [{tenors[0]}, {tenors[-1]}]"
            )
        right_index = bisect_right(tenors, target)
        if right_index and tenors[right_index - 1] == target:
            interpolated.append(rates[right_index - 1])
            continue
        left_index = right_index - 1
        weight = (target - tenors[left_index]) / (
            tenors[right_index] - tenors[left_index]
        )
        interpolated.append(
            rates[left_index] + weight * (rates[right_index] - rates[left_index])
        )
    return interpolated
