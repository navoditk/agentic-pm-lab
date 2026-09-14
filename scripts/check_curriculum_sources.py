"""Validate external-source ownership and learning-asset impact mappings."""

from __future__ import annotations

import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REGISTRY_PATH = ROOT / "docs/reference/source-registry.yaml"
REQUIRED_SOURCE_FIELDS = {
    "id",
    "title",
    "url",
    "kind",
    "version_or_fingerprint",
    "last_reviewed",
    "review_after_days",
    "owner",
    "severity_rules",
    "impacts",
}
VALID_KINDS = {"github_release", "pypi", "rss", "url"}


def _load_registry(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("source registry must be a mapping")
    return value


def _source_assets(topic: dict[str, str]) -> set[str]:
    return {topic["deep_dive"], topic["agent_file"], topic["quiz_file"]}


def check(
    registry_path: Path = REGISTRY_PATH, *, today: date | None = None
) -> list[str]:
    """Return deterministic registry validation errors without making network calls."""
    from src.education.tutor import TOPIC_CATALOG

    today = today or datetime.now(UTC).date()
    try:
        registry = _load_registry(registry_path)
    except (OSError, TypeError, UnicodeError, yaml.YAMLError) as error:
        return [f"invalid source registry: {error}"]

    if registry.get("version") != 1:
        return ["source registry version must be 1"]
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        return ["source registry sources must be a non-empty list"]

    errors: list[str] = []
    ids: set[str] = set()
    covered_topics: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            errors.append("source records must be mappings")
            continue
        source_id = source.get("id", "<unknown>")
        if not isinstance(source_id, str) or not source_id:
            errors.append("source id must be a non-empty string")
            continue
        if source_id in ids:
            errors.append(f"duplicate source id: {source_id}")
        ids.add(source_id)
        missing = REQUIRED_SOURCE_FIELDS - set(source)
        if missing:
            errors.append(f"{source_id}: missing {sorted(missing)}")
            continue
        parsed_url = urlparse(source["url"])
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            errors.append(f"{source_id}: url must be an absolute HTTPS URL")
        if source["kind"] not in VALID_KINDS:
            errors.append(f"{source_id}: invalid kind {source['kind']!r}")
        if source["kind"] == "pypi" and (
            not isinstance(source.get("monitor"), str) or not source["monitor"]
        ):
            errors.append(f"{source_id}: pypi sources require a monitor project")
        if "monitor_baseline" in source and (
            not isinstance(source["monitor_baseline"], str)
            or not source["monitor_baseline"]
        ):
            errors.append(f"{source_id}: monitor_baseline must be a non-empty string")
        if (
            not isinstance(source["version_or_fingerprint"], str)
            or not source["version_or_fingerprint"]
        ):
            errors.append(f"{source_id}: version_or_fingerprint must be non-empty")
        reviewed = source["last_reviewed"]
        if not isinstance(reviewed, date):
            errors.append(f"{source_id}: last_reviewed must be an ISO date")
        elif (
            not isinstance(source["review_after_days"], int)
            or source["review_after_days"] <= 0
        ):
            errors.append(f"{source_id}: review_after_days must be a positive integer")
        elif reviewed + timedelta(days=source["review_after_days"]) < today:
            errors.append(f"{source_id}: external-source review is overdue")
        if not isinstance(source["owner"], str) or not source["owner"]:
            errors.append(f"{source_id}: owner must be non-empty")
        if (
            not isinstance(source["severity_rules"], list)
            or not source["severity_rules"]
        ):
            errors.append(f"{source_id}: severity_rules must be a non-empty list")

        impacts = source["impacts"]
        if not isinstance(impacts, list) or not impacts:
            errors.append(f"{source_id}: impacts must be a non-empty list")
            continue
        impact_topics: set[str] = set()
        for impact in impacts:
            if not isinstance(impact, dict):
                errors.append(f"{source_id}: impact records must be mappings")
                continue
            topic_id = impact.get("topic")
            if topic_id not in TOPIC_CATALOG:
                errors.append(f"{source_id}: unknown topic {topic_id!r}")
                continue
            if topic_id in impact_topics:
                errors.append(f"{source_id}: duplicate impact topic {topic_id}")
            impact_topics.add(topic_id)
            covered_topics.add(topic_id)
            assets = impact.get("assets")
            if not isinstance(assets, list) or not all(
                isinstance(asset, str) for asset in assets
            ):
                errors.append(f"{source_id}/{topic_id}: assets must be a list of paths")
                continue
            expected_assets = _source_assets(TOPIC_CATALOG[topic_id])
            if set(assets) != expected_assets:
                errors.append(
                    f"{source_id}/{topic_id}: assets must map the topic deep dive, "
                    "persona, and quiz bank"
                )
            for asset in assets:
                if not (ROOT / asset).is_file():
                    errors.append(f"{source_id}/{topic_id}: missing asset {asset}")
    uncovered = sorted(set(TOPIC_CATALOG) - covered_topics)
    if uncovered:
        errors.append(
            f"topics without an external source mapping: {', '.join(uncovered)}"
        )
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Curriculum source registry check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
