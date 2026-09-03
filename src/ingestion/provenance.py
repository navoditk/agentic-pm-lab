"""Point-in-time selection and provenance envelopes for research data."""

from collections.abc import Iterable
from datetime import date
from typing import Any

REQUIRED_PROVENANCE_FIELDS = {
    "source",
    "series_id",
    "observation_date",
    "release_date",
    "unit",
    "vintage",
}


def assess_observation_quality(
    observations: Iterable[dict[str, Any]],
    *,
    decision_date: str,
    licensing_state: str = "permitted",
) -> dict[str, Any]:
    """Classify evidence before it is used by a decision workflow.

    This is intentionally a small local policy helper. It makes stale,
    conflicting, incomplete, and unlicensed fixture states explicit instead of
    allowing a caller to silently select a plausible record.
    """
    records = list(observations)
    if not records:
        return {"status": "incomplete", "reason": "no observations supplied"}
    try:
        for record in records:
            _validate_observation(record)
    except (KeyError, TypeError, ValueError) as exc:
        return {"status": "incomplete", "reason": str(exc)}
    if licensing_state not in {"permitted", "restricted", "unknown"}:
        raise ValueError("licensing_state must be permitted, restricted, or unknown")
    if licensing_state != "permitted":
        return {"status": "unlicensed", "reason": licensing_state}
    eligible = [record for record in records if eligible_as_of(record, decision_date)]
    if not eligible:
        return {"status": "stale", "reason": "no record was eligible at decision time"}
    by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for record in eligible:
        key = (
            str(record["source"]),
            str(record["series_id"]),
            str(record["observation_date"]),
        )
        by_key.setdefault(key, []).append(record)
    conflicts = [
        key
        for key, values in by_key.items()
        if len({float(value["value"]) for value in values}) > 1
    ]
    if conflicts:
        return {"status": "conflicted", "conflicting_keys": conflicts}
    return {"status": "usable", "eligible_count": len(eligible)}


def make_observation(
    *,
    source: str,
    series_id: str,
    observation_date: str,
    release_date: str,
    value: float,
    unit: str,
    vintage: str,
    source_url: str | None = None,
) -> dict[str, Any]:
    """Create a normalized observation with explicit information timing."""
    observation = {
        "source": source,
        "series_id": series_id,
        "observation_date": _parse_date(observation_date).isoformat(),
        "release_date": _parse_date(release_date).isoformat(),
        "value": float(value),
        "unit": unit,
        "vintage": vintage,
    }
    if source_url is not None:
        observation["source_url"] = source_url
    if _parse_date(release_date) < _parse_date(observation_date):
        raise ValueError("release_date cannot precede observation_date")
    return observation


def eligible_as_of(observation: dict[str, Any], decision_date: str) -> bool:
    """Return whether a record was knowable at the decision date."""
    _validate_observation(observation)
    decision = _parse_date(decision_date)
    return (
        _parse_date(str(observation["observation_date"])) <= decision
        and _parse_date(str(observation["release_date"])) <= decision
    )


def select_point_in_time(
    observations: Iterable[dict[str, Any]],
    *,
    decision_date: str,
) -> list[dict[str, Any]]:
    """Select the latest eligible vintage for each source/series/observation."""
    selected: dict[tuple[str, str, str], dict[str, Any]] = {}
    for observation in observations:
        _validate_observation(observation)
        if not eligible_as_of(observation, decision_date):
            continue
        key = (
            str(observation["source"]),
            str(observation["series_id"]),
            str(observation["observation_date"]),
        )
        current = selected.get(key)
        if current is None or str(observation["release_date"]) > str(
            current["release_date"]
        ):
            selected[key] = dict(observation)
    return sorted(
        selected.values(),
        key=lambda item: (
            str(item["observation_date"]),
            str(item["source"]),
            str(item["series_id"]),
        ),
    )


def _validate_observation(observation: dict[str, Any]) -> None:
    missing = REQUIRED_PROVENANCE_FIELDS.difference(observation)
    if missing:
        raise ValueError(f"observation is missing provenance fields: {sorted(missing)}")
    _parse_date(str(observation["observation_date"]))
    _parse_date(str(observation["release_date"]))


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO date: {value}") from exc
