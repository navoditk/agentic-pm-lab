"""Report external curriculum-source changes without modifying curriculum content."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
try:
    from scripts.check_curriculum_sources import REGISTRY_PATH, _load_registry
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from check_curriculum_sources import REGISTRY_PATH, _load_registry

DEFAULT_OUTPUT = ROOT / "artifacts/curriculum-source-report.json"
USER_AGENT = "agentic-pm-lab-curriculum-monitor/1.0"
Fetch = Callable[[str, str], tuple[dict[str, str], bytes]]


def _fetch(url: str, method: str) -> tuple[dict[str, str], bytes]:
    request = Request(url, method=method, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=15) as response:
        headers = {key.lower(): value for key, value in response.headers.items()}
        return headers, response.read(65_536) if method == "GET" else b""


def _observed_pypi(source: dict[str, Any], fetch: Fetch) -> str:
    project = source.get("monitor", source["id"])
    _headers, body = fetch(f"https://pypi.org/pypi/{project}/json", "GET")
    value = json.loads(body)
    return str(value["info"]["version"])


def _observed_url(source: dict[str, Any], fetch: Fetch) -> str:
    try:
        headers, _body = fetch(source["url"], "HEAD")
    except HTTPError as error:
        if error.code not in {403, 405, 501}:
            raise
        headers, body = fetch(source["url"], "GET")
        return (
            headers.get("etag")
            or headers.get("last-modified")
            or hashlib.sha256(body).hexdigest()
        )
    return (
        headers.get("etag") or headers.get("last-modified") or "validator-unavailable"
    )


def monitor_source(source: dict[str, Any], fetch: Fetch = _fetch) -> dict[str, Any]:
    """Observe one source and return a report-only change classification."""
    result = {
        "id": source["id"],
        "title": source["title"],
        "url": source["url"],
        "kind": source["kind"],
        "baseline": source["version_or_fingerprint"],
        "topics": [impact["topic"] for impact in source["impacts"]],
        "assets": sorted(
            {asset for impact in source["impacts"] for asset in impact["assets"]}
        ),
    }
    try:
        observed = (
            _observed_pypi(source, fetch)
            if source["kind"] == "pypi"
            else _observed_url(source, fetch)
        )
    except (
        HTTPError,
        URLError,
        OSError,
        KeyError,
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as error:
        return {**result, "status": "unavailable", "detail": str(error)}

    if observed == "validator-unavailable":
        return {
            **result,
            "status": "unbaselined",
            "observed": observed,
            "detail": "The source supplied no HTTP validator; add monitor_baseline after review.",
        }
    if observed == source["version_or_fingerprint"]:
        return {**result, "status": "unchanged", "observed": observed}
    if source["kind"] != "pypi" and "monitor_baseline" not in source:
        return {
            **result,
            "status": "unbaselined",
            "observed": observed,
            "detail": "Add monitor_baseline after the first documented review.",
        }
    return {**result, "status": "changed", "observed": observed}


def build_report(
    registry_path: Path = REGISTRY_PATH, *, fetch: Fetch = _fetch
) -> dict[str, Any]:
    """Build a deterministic report shape; network results are captured as data."""
    registry = _load_registry(registry_path)
    results = [monitor_source(source, fetch) for source in registry["sources"]]
    display_path = (
        registry_path.relative_to(ROOT)
        if registry_path.is_relative_to(ROOT)
        else registry_path
    )
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "registry": str(display_path),
        "summary": {
            status: sum(result["status"] == status for result in results)
            for status in ("changed", "unbaselined", "unchanged", "unavailable")
        },
        "sources": results,
    }


def write_issue_files(report: dict[str, Any], directory: Path) -> None:
    """Write review bodies for material changes without calling GitHub."""
    directory.mkdir(parents=True, exist_ok=True)
    for source in report["sources"]:
        if source["status"] not in {"changed", "unbaselined"}:
            continue
        assets = "\n".join(f"- `{asset}`" for asset in source["assets"])
        topics = ", ".join(f"`{topic}`" for topic in source["topics"])
        body = f"""## External curriculum source review

The scheduled monitor classified this source as **{source["status"]}**.
It does not modify lessons, quizzes, or registry baselines.

- Source: [{source["title"]}]({source["url"]})
- Baseline: `{source["baseline"]}`
- Observed: `{source.get("observed", "unavailable")}`
- Affected topics: {topics}

### Assets to review
{assets}

### Maintainer checklist

- [ ] Classify the upstream change: no-action, clarification, behavioral,
  breaking, or security.
- [ ] Confirm checked-in dependency and repository behavior.
- [ ] Update only affected learning assets and quiz citations.
- [ ] Update `version_or_fingerprint` and/or `monitor_baseline` plus
  `last_reviewed` in `docs/reference/source-registry.yaml`.
- [ ] Regenerate `artifacts/agentic-pm-curriculum.html` and run curriculum checks.

See `docs/learning/CURRICULUM_FRESHNESS_PLAN.md` for change control.
"""
        (directory / f"{source['id']}.md").write_text(body, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--issue-dir", type=Path)
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.issue_dir:
        write_issue_files(report, args.issue_dir)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
