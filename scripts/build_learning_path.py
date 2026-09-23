"""Render the recommended course order into the docs that show it.

The order used to be written out by hand in several places, and they had
drifted: one listed 13 of the 14 courses, and another was cited as "the
recommended order" without containing one. The order now lives only in
`docs/learning/tutor-courses.json` (`step`, `stage`, `est_hours`), and this
script writes the same generated table between markers in each target:

    uv run python scripts/build_learning_path.py          # rewrite targets
    uv run python scripts/build_learning_path.py --check  # CI: fail if stale

Links are made relative to each target file, so the same table works from
the repository root and from docs/learning/.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

START_MARKER = "<!-- LEARNING_PATH:START -->"
END_MARKER = "<!-- LEARNING_PATH:END -->"
TARGETS = (
    ROOT / "README.md",
    ROOT / "docs/learning/TUTOR_COURSE_GUIDE.md",
)


def render_block(target: Path) -> str:
    from src.education.tutor import COURSE_CATALOG, TOPIC_CATALOG

    rows = [
        "| Step | Stage | Course | Topic id | Est. hours |",
        "|---|---|---|---|---|",
    ]
    total = 0
    for topic_id, record in TOPIC_CATALOG.items():
        course = COURSE_CATALOG[topic_id]
        link = os.path.relpath(ROOT / record["deep_dive"], target.parent)
        rows.append(
            f"| {course['step']} | {course['stage']} | [{record['label']}]({link}) "
            f"| `{topic_id}` | ~{course['est_hours']} |"
        )
        total += course["est_hours"]
    table = "\n".join(rows)
    return f"""{START_MARKER}
<!-- Generated from docs/learning/tutor-courses.json by
     scripts/build_learning_path.py. Edit the JSON, not this table. -->

{table}

About {total} hours in total. Hours are rough estimates covering the deep dive,
the three labs, the quiz, and the teach-back. The order is a recommendation,
not a gate: each course lists its own prerequisites, so an experienced learner
can start anywhere.

{END_MARKER}"""


def rewrite(text: str, block: str, target: Path) -> str:
    if START_MARKER not in text or END_MARKER not in text:
        raise ValueError(
            f"{target.relative_to(ROOT)} is missing the learning-path markers"
        )
    head, _, rest = text.partition(START_MARKER)
    _, _, tail = rest.partition(END_MARKER)
    return head + block + tail


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="fail if any target is stale"
    )
    args = parser.parse_args(argv)
    stale = []
    for target in TARGETS:
        current = target.read_text(encoding="utf-8")
        updated = rewrite(current, render_block(target), target)
        if updated == current:
            continue
        if args.check:
            stale.append(str(target.relative_to(ROOT)))
        else:
            target.write_text(updated, encoding="utf-8")
            print(f"updated {target.relative_to(ROOT)}")
    if stale:
        print(
            "Learning-path table is stale in: "
            + ", ".join(stale)
            + "\nRegenerate with: uv run python scripts/build_learning_path.py"
        )
        return 1
    if args.check:
        print("Learning-path tables are current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
