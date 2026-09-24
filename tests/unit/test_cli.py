"""The console script, tested as the front door a new user actually types.

Driven through `build_parser()` and the command functions rather than by
shelling out, so the suite stays fast -- except where the point *is* the
subprocess boundary, which is called out where it happens.

The behaviours worth pinning are the ones a user notices: an unknown name
produces a readable error and a non-zero status rather than a traceback, and
every advertised command exists. A CLI that tracebacks on a typo is the
single most common reason people stop trusting one.
"""

import pytest

from src.agentic_pm_lab import (
    CHECKS,
    OVERVIEW,
    build_parser,
    cmd_course,
    cmd_learn,
    cmd_plan,
)
from src.education.tutor import TOPIC_CATALOG


def parse(argv):
    return build_parser().parse_args(argv)


# --- the advertised surface exists -------------------------------------------


@pytest.mark.parametrize(
    "command", ["learn", "course", "quiz", "progress", "plan", "check"]
)
def test_every_advertised_command_parses(command):
    """The overview text promises these; a promise with no parser is a 404."""
    assert command in OVERVIEW
    assert parse([command, "x"] if command in {"course", "quiz"} else [command])


def test_the_overview_separates_learner_from_developer_commands():
    """Mixing the two audiences is what made scripts/ unreadable."""
    assert "Learning" in OVERVIEW and "Development" in OVERVIEW
    learning, development = OVERVIEW.split("Development", 1)
    assert "quiz" in learning and "learn" in learning
    assert "check" in development and "plan" in development


def test_check_is_not_offered_as_a_learner_command():
    learning = OVERVIEW.split("Development", 1)[0]
    assert "check" not in learning


# --- errors are readable ------------------------------------------------------


def test_an_unknown_topic_reports_cleanly_instead_of_raising(capsys):
    assert cmd_course(parse(["course", "not-a-topic"])) == 1
    assert "unknown topic" in capsys.readouterr().err


def test_an_unknown_day_lists_the_days_that_do_exist(capsys):
    """An error that does not say what would have worked wastes a round trip."""
    assert cmd_plan(parse(["plan", "99"])) == 1
    err = capsys.readouterr().err
    assert "99" in err and "Known:" in err


def test_learn_with_no_topic_lists_rather_than_erroring(capsys):
    assert cmd_learn(parse(["learn"])) == 0
    out = capsys.readouterr().out
    assert f"{len(TOPIC_CATALOG)} courses" in out
    assert "opentelemetry-tutor" in out


def test_learn_lists_courses_in_step_order_under_stage_headings(capsys):
    """The listing is the terminal copy of the recommended order, so it must
    follow `step`, not dict insertion luck or the alphabet."""
    cmd_learn(parse(["learn"]))
    out = capsys.readouterr().out
    assert out.index("agent-architecture-tutor") < out.index("document-to-skill-tutor")
    assert out.index("Agent core (required)") < out.index("agent-architecture-tutor")
    assert out.count("Agent core") == 1
    assert "Finance domain (optional)" in out
    assert "The required module is about" in out


# --- plan ---------------------------------------------------------------------


def test_plan_prints_the_day_with_its_location(capsys):
    assert cmd_plan(parse(["plan", "7"])) == 0
    out = capsys.readouterr().out
    assert "docs/PLAN.md lines" in out
    assert "Day 7" in out


def test_quiet_omits_the_location_header_so_output_can_be_piped(capsys):
    """Quiet drops the `# file lines N-M` banner, not the markdown.

    The content legitimately begins with `### Day 7`, so "starts with #" is
    the wrong check -- what must be absent is the location line this command
    adds, which would otherwise be pasted into an agent as if it were part
    of the plan.
    """
    assert cmd_plan(parse(["plan", "7", "--quiet"])) == 0
    out = capsys.readouterr().out
    assert "docs/PLAN.md lines" not in out
    assert out.startswith("### Day 7")


def test_plan_output_is_a_small_fraction_of_the_whole_file(capsys):
    """The reason the command exists, asserted rather than claimed."""
    cmd_plan(parse(["plan", "7", "--quiet"]))
    day = len(capsys.readouterr().out)
    from pathlib import Path

    whole = len(Path("docs/PLAN.md").read_text(encoding="utf-8"))
    assert day < whole / 10


def test_plan_list_shows_every_day_with_its_cost(capsys):
    assert cmd_plan(parse(["plan", "--list"])) == 0
    out = capsys.readouterr().out
    assert "day-1" in out and "tokens" in out


# --- check --------------------------------------------------------------------


def test_check_runs_the_same_gates_as_ci():
    """Drift between local `check` and CI is how "it passed locally" happens.

    Scans every workflow rather than ci.yml alone. The narrower version of
    this test passed while `check` was missing the skill and governance
    suites entirely -- root pytest is scoped to `tests/` by `testpaths`, so
    those run only in contract-tests.yml and authorization-tests.yml, and
    `check` reported green on a PR that CI failed.
    """
    from pathlib import Path

    workflows = "\n".join(
        path.read_text(encoding="utf-8")
        for path in Path(".github/workflows").glob("*.yml")
    )
    for _, command in CHECKS:
        script = next((part for part in command if part.startswith("scripts/")), None)
        if script:
            assert script in workflows, f"{script} runs locally but not in CI"


def test_check_covers_the_suites_root_pytest_excludes():
    """`pytest -q` alone does not reach skills/ or governance/tests."""
    commands = [" ".join(command) for _, command in CHECKS]
    assert any("pytest skills" in command for command in commands)
    assert any("pytest governance/tests" in command for command in commands)


def test_fast_is_a_strict_subset_of_the_full_gate_set():
    assert CHECKS[:3] != CHECKS
    assert all(check in CHECKS for check in CHECKS[:3])
