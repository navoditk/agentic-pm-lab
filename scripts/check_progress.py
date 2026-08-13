"""Evaluate config/progress.yaml against the current repo state and regenerate
PROGRESS.md's status table between the <!-- PROGRESS:START/END --> markers
(docs/PLAN.md §6). Run by .github/workflows/progress-tracker.yml on every push to
main; also runnable by hand: `uv run python scripts/check_progress.py`.
"""

import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PROGRESS_YAML_PATH = REPO_ROOT / "config/progress.yaml"
PROGRESS_MD_PATH = REPO_ROOT / "PROGRESS.md"

START_MARKER = "<!-- PROGRESS:START -->"
END_MARKER = "<!-- PROGRESS:END -->"

# One glob pattern list per layer, used to derive the mock->real table by
# grepping for "# MOCK" in whatever currently exists for that layer.
LAYER_PATTERNS = {
    "Data Layer": ["src/ingestion/**/*.py"],
    "Control Layer (AuthN/AuthZ)": [
        "src/control/**/*.py",
        "governance/policies/*.cedar",
    ],
    "Guardrails": [
        "src/control/guardrails.py",
        "governance/guardrails/*.yaml",
    ],
    "Tool Layer": ["src/analytics/**/*.py", "src/api/main.py"],
    "Portfolio Optimization": ["src/analytics/optimiz*.py"],
    "Interactive Layer": [".github/extensions/**/*.js", ".github/extensions/**/*.ts"],
    "Runtime Layer": ["scripts/artifacts_host.py", "docker-compose.yml"],
    "Agent Layer": ["src/agents/**/*.py"],
    "Observability": ["src/context/**/*.py", "src/observability/**/*.py"],
    "Golden dataset / evals": ["evals/*.jsonl"],
    "AWS Bedrock AgentCore": ["src/agents/*agentcore*.py"],
}

MOCK_MARKER = "# MOCK"


def _run_checks(checks: list[dict]) -> list[bool]:
    results = []
    for check in checks:
        if "path_exists" in check:
            results.append((REPO_ROOT / check["path_exists"]).exists())
        elif "tests_pass" in check:
            test_path = REPO_ROOT / check["tests_pass"]
            if not test_path.exists():
                results.append(False)
                continue
            proc = subprocess.run(
                ["uv", "run", "pytest", str(test_path), "-q"],
                cwd=REPO_ROOT,
                capture_output=True,
                check=False,
            )
            results.append(proc.returncode == 0)
        elif "tag_exists" in check:
            proc = subprocess.run(
                ["git", "tag", "-l", check["tag_exists"]],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            results.append(bool(proc.stdout.strip()))
        else:
            results.append(False)
    return results


def build_day_table(progress: dict) -> str:
    rows = ["| Day | Focus | Status | Notes |", "|---|---|---|---|"]
    for key in sorted(progress, key=lambda k: int(k.split("_")[1])):
        day_num = key.split("_")[1]
        entry = progress[key]
        label = entry["label"]
        focus = label
        checks = entry.get("checks") or []
        note = ""
        if not checks:
            status = "⬜ Not started"
        else:
            results = _run_checks(checks)
            if all(results):
                status = "✅ Complete"
            elif any(results):
                status = "🟡 In progress"
                note = f"{sum(results)}/{len(results)} checks passing"
            else:
                status = "⬜ Not started"
        rows.append(f"| {day_num} | {focus} | {status} | {note} |")
    return "\n".join(rows)


def build_mock_real_table() -> str:
    rows = ["| Layer | Status | Detail |", "|---|---|---|"]
    for layer, patterns in LAYER_PATTERNS.items():
        matched = []
        for pattern in patterns:
            matched.extend(REPO_ROOT.glob(pattern))
        matched = sorted(
            {p for p in matched if p.is_file() and p.name != "__init__.py"}
        )
        if not matched:
            rows.append(f"| {layer} | 🔴 Not started | No files yet |")
            continue
        mocked = [p for p in matched if MOCK_MARKER in p.read_text(errors="ignore")]
        if not mocked:
            rows.append(
                f"| {layer} | 🟢 Real | {len(matched)} file(s), no `# MOCK` markers |"
            )
        elif len(mocked) == len(matched):
            rows.append(
                f"| {layer} | 🔴 Mock | {len(matched)} file(s), all still `# MOCK` |"
            )
        else:
            rows.append(
                f"| {layer} | 🟡 Partial | {len(matched) - len(mocked)}/{len(matched)} file(s) real |"
            )
    return "\n".join(rows)


def render_status_block(progress: dict) -> str:
    day_table = build_day_table(progress)
    mock_table = build_mock_real_table()
    total_days = 20
    completed = sum(
        1
        for key, entry in progress.items()
        if int(key.split("_")[1]) <= 20
        and entry.get("checks")
        and all(_run_checks(entry["checks"]))
    )
    return f"""{START_MARKER}

## Status: Day {completed} of {total_days}{" — not yet started" if completed == 0 else ""}

**Environment setup:** ✅ `INSTALL.md` complete. *(This checkbox is the one line in this file that isn't auto-generated by `progress-tracker.yml` — it's flipped to ✅ by hand, as the last item in `INSTALL.md`'s own verification checklist, since that mechanism doesn't exist until Day 1 builds it.)*

*(Days 10–20 are the forward institutional PM track. Days 13–14 are now mainstream milestones; the older optional-extension wording in `docs/PLAN.md` is historical.)*

**Day-by-day completion:**

{day_table}

**Mock → real status, by layer:**

{mock_table}

{END_MARKER}"""


def update_progress_md(progress: dict) -> None:
    content = PROGRESS_MD_PATH.read_text()
    new_block = render_status_block(progress)
    # Anchor each marker to its own line -- the file's intro paragraph
    # mentions both marker strings inline as prose, and a non-anchored match
    # would latch onto that mention instead of the real markers below it.
    pattern = re.compile(
        r"^" + re.escape(START_MARKER) + r"$.*?^" + re.escape(END_MARKER) + r"$",
        re.DOTALL | re.MULTILINE,
    )
    if not pattern.search(content):
        raise RuntimeError(
            f"Could not find {START_MARKER}/{END_MARKER} markers in PROGRESS.md"
        )
    updated = pattern.sub(new_block, content)
    PROGRESS_MD_PATH.write_text(updated)


def main() -> int:
    progress = yaml.safe_load(PROGRESS_YAML_PATH.read_text())
    update_progress_md(progress)
    print("PROGRESS.md updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
