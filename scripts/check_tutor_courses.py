"""Validate that every tutor has a complete offline course outline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REQUIRED = {
    "prerequisites",
    "objectives",
    "lessons",
    "local_lab",
    "failure_lab",
    "assessment",
}


def check() -> list[str]:
    from src.education.tutor import TOPIC_CATALOG

    courses = json.loads((ROOT / "docs/learning/tutor-courses.json").read_text())
    errors = []
    for topic in TOPIC_CATALOG:
        course = courses.get(topic)
        if not isinstance(course, dict):
            errors.append(f"missing course: {topic}")
            continue
        missing = REQUIRED - set(course)
        if missing:
            errors.append(f"{topic}: missing {sorted(missing)}")
        for field in ("prerequisites", "objectives", "lessons"):
            if not isinstance(course.get(field), list) or not course[field]:
                errors.append(f"{topic}: {field} must be a non-empty list")
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Tutor course completeness check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
