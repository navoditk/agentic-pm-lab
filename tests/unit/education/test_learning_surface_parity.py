"""Every learning surface must offer the same curriculum.

The CLI, the published page, and the agentexpert skill all read the same
catalog, but each one also frames it in its own words: headings, routes,
module labels. That framing is where they drift. These tests fail when a
module exists in the catalog but one surface never mentions it.
"""

from pathlib import Path

import pytest

from scripts.build_learning_curriculum import DEFAULT_OUTPUT
from src.agentic_pm_lab import build_parser, cmd_learn
from src.education.tutor import COURSE_CATALOG, TOPIC_CATALOG

ROOT = Path(__file__).resolve().parents[3]
MODULES = sorted({course["stage"] for course in COURSE_CATALOG.values()})


def _cli_listing(capsys):
    cmd_learn(build_parser().parse_args(["learn"]))
    return capsys.readouterr().out


@pytest.mark.parametrize("module", MODULES)
def test_every_module_is_offered_on_every_surface(module, capsys):
    routes = ROOT / "skills/agentic-pm-mastery/references/learning-paths.md"
    assert module in _cli_listing(capsys), "CLI"
    assert module in DEFAULT_OUTPUT.read_text(encoding="utf-8"), "page"
    assert module in routes.read_text(encoding="utf-8"), "skill routes"


def test_every_course_is_offered_on_every_surface(capsys):
    listing = _cli_listing(capsys)
    page = DEFAULT_OUTPUT.read_text(encoding="utf-8")
    for topic_id in TOPIC_CATALOG:
        assert topic_id in listing, f"CLI missing {topic_id}"
        assert f'id="{topic_id}"' in page, f"page missing {topic_id}"
    # The skill resolves courses from the catalog at run time rather than
    # listing them, so its obligation is to point at the catalog.
    skill = (ROOT / "skills/agentic-pm-mastery/SKILL.md").read_text(encoding="utf-8")
    assert "docs/learning/tutor-courses.json" in skill
    assert "src/education/tutor.py" in skill
