"""Regenerate docs/learning/LEARNER_PROGRESS.md's comprehension table from the
append-only quiz-attempt logs under data/learner_progress/*.jsonl.

This tracks whether a learner has *understood* a tutor topic (best quiz
score), separate from config/progress.yaml / PROGRESS.md, which tracks
whether the underlying code was *built*. Run by hand after taking a quiz:
`uv run python scripts/check_learner_progress.py`.
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LEARNER_PROGRESS_DIR = REPO_ROOT / "data" / "learner_progress"
LEARNER_PROGRESS_MD_PATH = REPO_ROOT / "docs" / "learning" / "LEARNER_PROGRESS.md"

START_MARKER = "<!-- LEARNER_PROGRESS:START -->"
END_MARKER = "<!-- LEARNER_PROGRESS:END -->"

PASS_THRESHOLD = 0.8


def _load_attempts(topic: str, log_dir: Path) -> list[dict]:
    log_path = log_dir / f"{topic}.jsonl"
    if not log_path.exists():
        return []
    attempts = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if line:
            attempts.append(json.loads(line))
    return attempts


def _best_ratio(attempts: list[dict]) -> float:
    ratios = [a["score"] / a["total"] for a in attempts if a["total"]]
    return max(ratios) if ratios else 0.0


def build_table(topics: list[str], log_dir: Path) -> str:
    rows = ["| Topic | Attempts | Best score | Status |", "|---|---|---|---|"]
    for topic in topics:
        attempts = _load_attempts(topic, log_dir)
        if not attempts:
            rows.append(f"| {topic} | 0 | - | ⬜ Not attempted |")
            continue
        best = max(attempts, key=lambda a: a["score"] / a["total"] if a["total"] else 0)
        ratio = _best_ratio(attempts)
        status = "✅ Passed" if ratio >= PASS_THRESHOLD else "🟡 Attempted"
        rows.append(
            f"| {topic} | {len(attempts)} | {best['score']}/{best['total']} | {status} |"
        )
    return "\n".join(rows)


def render_status_block(topics: list[str], log_dir: Path) -> str:
    table = build_table(topics, log_dir)
    passed = sum(
        1
        for topic in topics
        if _best_ratio(_load_attempts(topic, log_dir)) >= PASS_THRESHOLD
    )
    return f"""{START_MARKER}

## Status: {passed} of {len(topics)} tutor topics passed (≥80% quiz score)

**Tracks comprehension, not implementation.** A topic shows ✅ here only
after the learner has taken and passed its quiz with
`uv run python scripts/tutor.py <topic> --quiz`; nothing here is inferred
from what code exists. Compare with `PROGRESS.md`, which tracks whether the
day's code was built.

{table}

{END_MARKER}"""


def update_learner_progress_md(
    topics: list[str],
    *,
    log_dir: Path | None = None,
    md_path: Path | None = None,
) -> None:
    log_dir = log_dir or LEARNER_PROGRESS_DIR
    md_path = md_path or LEARNER_PROGRESS_MD_PATH
    content = md_path.read_text()
    new_block = render_status_block(topics, log_dir)
    pattern = re.compile(
        r"^" + re.escape(START_MARKER) + r"$.*?^" + re.escape(END_MARKER) + r"$",
        re.DOTALL | re.MULTILINE,
    )
    if not pattern.search(content):
        raise RuntimeError(
            f"Could not find {START_MARKER}/{END_MARKER} markers in {md_path}"
        )
    updated = pattern.sub(new_block, content)
    md_path.write_text(updated)


def main() -> int:
    from src.education.tutor import TOPIC_CATALOG

    update_learner_progress_md(sorted(TOPIC_CATALOG))
    print("LEARNER_PROGRESS.md updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
