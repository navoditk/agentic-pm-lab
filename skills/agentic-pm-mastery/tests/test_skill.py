import json
import re
from pathlib import Path

import yaml

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]
ROOT = SKILL_DIR.parents[1]


def test_agentic_pm_mastery_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_skill_is_tool_neutral_and_preserves_offline_learning():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()

    assert "CLI's structured question/choice tool" in skill_text
    assert "Otherwise, retain progress in the active conversation" in skill_text
    # The documented entry point, not the module behind it. This asserts the
    # exact string a learner is told to type, so the skill cannot drift from
    # the CLI the rest of the documentation now routes through.
    assert "agentic-pm-lab quiz <topic-id>" in skill_text


def test_contract_prohibits_live_and_investment_actions():
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())

    # The only write is the learner's own gitignored quiz log, on request.
    assert "data/learner_progress/" in contract["side_effects"]
    assert "No tracked file is modified" in contract["side_effects"]
    assert "repository_editing" in contract["forbidden_tools"]
    assert {"investment_advice", "order_execution", "live_provider_invocation"} <= set(
        contract["forbidden_tools"]
    )


def test_all_cli_loaders_reference_the_canonical_skill():
    loader_paths = (
        ROOT / ".claude/skills/agentic-pm-mastery/SKILL.md",
        ROOT / ".agents/skills/agentic-pm-mastery/SKILL.md",
    )

    for loader in loader_paths:
        assert loader.is_file()
        assert "skills/agentic-pm-mastery/SKILL.md" in loader.read_text()


def test_recorded_quizzes_go_through_the_cli_and_only_on_request():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()

    assert "agentic-pm-lab quiz <topic-id> --answers" in skill_text
    assert "Only when the learner asks" in skill_text
    assert "Never fill in" in skill_text


def _xp_scheme(skill_text):
    rows = re.findall(r"^\| [^|]+ \| \+\d+[^|]* \| (\d+) \|$", skill_text, re.MULTILINE)
    levels_line = re.search(r"^Levels: (.+)\.$", skill_text, re.MULTILINE).group(1)
    levels = [
        int(threshold.replace(",", ""))
        for threshold in re.findall(r"([\d,]+) [A-Z]", levels_line)
    ]
    final = int(re.search(r"final assessment \(\+(\d+)\)", skill_text).group(1))
    return sum(int(row) for row in rows), levels, final


def test_levels_are_calibrated_to_the_real_course_catalog():
    """The inherited scheme topped out after about 6 of 14 courses.

    Every threshold is derived here from the course catalog, so adding a
    course, a lesson, or a stage fails this test until the levels are
    recalculated -- instead of silently saturating again.
    """
    skill_text = (SKILL_DIR / "SKILL.md").read_text()
    per_topic, levels, final = _xp_scheme(skill_text)
    courses = json.loads((ROOT / "docs/learning/tutor-courses.json").read_text())
    ordered = sorted(courses.values(), key=lambda course: course["step"])

    # The lesson row assumes three lessons (+20 each, 60 per topic).
    assert {len(course["lessons"]) for course in ordered} == {3}
    stage_ends = [
        index
        for index, course in enumerate(ordered, start=1)
        if index == len(ordered) or ordered[index]["stage"] != course["stage"]
    ]
    expected = [0, per_topic]
    expected += [per_topic * end for end in stage_ends[:-1]]
    expected += [per_topic * len(ordered) + final]
    assert levels == expected
