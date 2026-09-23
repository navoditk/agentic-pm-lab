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
    "step",
    "stage",
    "est_hours",
    "required",
    "prerequisites",
    "objectives",
    "lessons",
    "local_lab",
    "failure_lab",
    "build_lab",
    "assessment",
}


def check_learning_order(catalog_order: list[str], courses: dict) -> list[str]:
    """The recommended order lives in one place: each course's `step`.

    Steps must run 1..N with no gaps, TOPIC_CATALOG must list topics in step
    order (everything that iterates it -- CLI, curriculum, UI -- inherits the
    order from there), and each stage must be one contiguous run of steps, so
    a stage heading never appears twice.
    """
    errors = []
    steps = {topic: courses.get(topic, {}).get("step") for topic in catalog_order}
    if any(
        not isinstance(step, int) or isinstance(step, bool) for step in steps.values()
    ):
        return [
            f"{topic}: step must be an integer"
            for topic, step in steps.items()
            if not isinstance(step, int) or isinstance(step, bool)
        ]
    if sorted(steps.values()) != list(range(1, len(catalog_order) + 1)):
        errors.append(f"steps must run 1..{len(catalog_order)} with no gaps or repeats")
    by_step = sorted(catalog_order, key=steps.__getitem__)
    if by_step != catalog_order:
        errors.append(
            "TOPIC_CATALOG order does not match course steps; expected "
            + ", ".join(by_step)
        )
    required_by_stage: dict = {}
    for topic in by_step:
        stage = courses[topic].get("stage")
        required = courses[topic].get("required")
        if required_by_stage.setdefault(stage, required) != required:
            errors.append(
                f"{topic}: every course in module {stage!r} must share one "
                "required setting; a module is taken whole or skipped whole"
            )
    seen_stages: list[str] = []
    for topic in by_step:
        stage = courses[topic].get("stage")
        if seen_stages and stage == seen_stages[-1]:
            continue
        if stage in seen_stages:
            errors.append(f"stage {stage!r} is split by another stage at {topic}")
        seen_stages.append(stage)
    return errors


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
        if not isinstance(course.get("stage"), str) or not course["stage"]:
            errors.append(f"{topic}: stage must be a non-empty string")
        if not isinstance(course.get("required"), bool):
            errors.append(f"{topic}: required must be true or false")
        hours = course.get("est_hours")
        if not isinstance(hours, int) or isinstance(hours, bool) or hours <= 0:
            errors.append(f"{topic}: est_hours must be a positive integer")
    errors.extend(check_learning_order(list(TOPIC_CATALOG), courses))
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
