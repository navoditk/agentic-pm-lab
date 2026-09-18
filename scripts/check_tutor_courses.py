"""Validate that every tutor has a complete offline course outline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MASTERY_SKILL = ROOT / "skills/agentic-pm-mastery/SKILL.md"
MASTERY_REFERENCES = ROOT / "skills/agentic-pm-mastery/references"
MASTERY_LOADERS = (
    ROOT / ".github/skills/agentic-pm-mastery/SKILL.md",
    ROOT / ".claude/skills/agentic-pm-mastery/SKILL.md",
    ROOT / ".agents/skills/agentic-pm-mastery/SKILL.md",
)
REQUIRED = {
    "prerequisites",
    "objectives",
    "lessons",
    "local_lab",
    "failure_lab",
    "build_lab",
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
    required_skill_files = (
        MASTERY_SKILL,
        MASTERY_REFERENCES / "learning-paths.md",
        MASTERY_REFERENCES / "scenarios.md",
        MASTERY_REFERENCES / "final-assessment.md",
    )
    for path in required_skill_files:
        if not path.is_file():
            errors.append(f"missing mastery skill asset: {path.relative_to(ROOT)}")
    if MASTERY_SKILL.is_file():
        skill_text = MASTERY_SKILL.read_text()
        for required_source in (
            "src/education/tutor.py",
            "docs/learning/tutor-courses.json",
            "docs/evidence/EVIDENCE.md",
        ):
            if required_source not in skill_text:
                errors.append(
                    f"mastery skill omits canonical source: {required_source}"
                )
    canonical_link = "skills/agentic-pm-mastery/SKILL.md"
    for path in MASTERY_LOADERS:
        if not path.is_file():
            errors.append(f"missing mastery skill loader: {path.relative_to(ROOT)}")
        elif canonical_link not in path.read_text():
            errors.append(
                f"mastery skill loader omits canonical package: {path.relative_to(ROOT)}"
            )
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
