"""The repository's front door: one routed command instead of 37 script paths.

`scripts/` holds 37 entry points and the README names four, so most of what
this repository can do is undiscoverable without listing the directory. This
module is the single console script declared in `pyproject.toml`, and it
exists to route -- every subcommand delegates to the module or script that
already does the work, and none of them reimplement it.

Commands are grouped by who they are for, because the two audiences want
different things and mixing them is what made `scripts/` hard to read:

- **Learner commands** (`learn`, `quiz`, `course`, `progress`) are the
  offline, read-only path through the 14 tutor courses. They need no model,
  no network and no API key.
- **Developer commands** (`plan`, `check`) serve someone *building* the
  repository rather than learning from it.

`plan` deserves its justification, since reading a day in a terminal is
something an editor does better. Its real use is extracting a bounded chunk
to hand to an agent that cannot read your filesystem -- a browser-based
Copilot or ChatGPT session in a locked-down environment, where
`agentic-pm-lab plan 7` yields roughly 1,800 tokens to paste rather than
1,904 lines to hunt through.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = REPO_ROOT / "docs/plan-index.json"

# Mirrors the gate order in .github/workflows/ci.yml. Kept as data so the
# local command and CI cannot drift into checking different things.
CHECKS: tuple[tuple[str, list[str]], ...] = (
    ("lint", ["ruff", "check", "."]),
    ("format", ["ruff", "format", "--check", "."]),
    ("docs consistency", ["python", "scripts/check_docs_consistency.py"]),
    ("tutor courses", ["python", "scripts/check_tutor_courses.py"]),
    ("learning path", ["python", "scripts/build_learning_path.py", "--check"]),
    ("curriculum sources", ["python", "scripts/check_curriculum_sources.py"]),
    (
        "curriculum artifact",
        ["python", "scripts/build_learning_curriculum.py", "--check"],
    ),
    ("document index", ["python", "scripts/build_plan_index.py", "--check"]),
    ("doc links", ["python", "scripts/check_doc_links.py"]),
    ("tests", ["pytest", "-q"]),
    # Root pytest is scoped to tests/ (see pyproject testpaths), so the skill
    # and governance suites run only in their own workflows. Without these two
    # lines `check` would report green while contract-tests.yml failed -- which
    # it did, on a skill test asserting a command string this CLI had changed.
    ("skill contracts", ["python", "scripts/check_skill_contracts.py"]),
    ("skill tests", ["pytest", "skills", "-q"]),
    ("authorization tests", ["pytest", "governance/tests", "-q"]),
)

OVERVIEW = """\
agentic-pm-lab -- governed agent engineering for portfolio management

Learning (offline, read-only; no model, network or API key needed)
  learn [TOPIC]       list the 14 courses, or teach one
  course TOPIC        the full outline: objectives, lessons, and the three labs
  quiz TOPIC          take the topic's quiz interactively
  progress            what you have completed, from recorded attempts

Development
  plan DAY            print one day's implementation steps
  check               run the same gates CI runs

Run any command with --help for its options.
The formula layer beneath this repository lives in pm-mechanics; this one
covers how to build and govern the agents, not how the metrics are derived.
"""


def _tutor():
    """Import the tutor module, with the repo root on the path.

    The repository's own modules are imported as `src.education.tutor`, which
    resolves when a script runs from the repo root but not when this console
    script is invoked from anywhere else -- and being runnable from anywhere
    is most of the point of installing a command.
    """
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from src.education import tutor

    return tutor


def cmd_learn(args: argparse.Namespace) -> int:
    tutor = _tutor()
    if not args.topic:
        topics = tutor.list_topics()
        print(f"The {len(topics)} courses, in the recommended order:")
        stage = None
        for entry in topics:
            if entry["stage"] != stage:
                stage = entry["stage"]
                print(f"\n  {stage}")
            print(
                f"  {entry['step']:>3}. {entry['id']:<36} "
                f"{entry['label']:<38} ~{entry['est_hours']}h"
            )
        total = sum(entry["est_hours"] for entry in topics)
        print(
            f"\nAbout {total} hours in total; the order is a recommendation, not a gate."
            "\nTeach one with:  agentic-pm-lab learn <topic>"
            "\nOutline one with: agentic-pm-lab course <topic>"
        )
        return 0
    try:
        print(json.dumps(tutor.teach_topic(args.topic), indent=2, sort_keys=True))
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


def cmd_course(args: argparse.Namespace) -> int:
    try:
        print(json.dumps(_tutor().course_outline(args.topic), indent=2, sort_keys=True))
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


def cmd_quiz(args: argparse.Namespace) -> int:
    """Delegates to the existing interactive runner rather than duplicating it."""
    return subprocess.call(
        [sys.executable, str(REPO_ROOT / "scripts/tutor.py"), args.topic, "--quiz"],
        cwd=REPO_ROOT,
    )


def cmd_progress(_: argparse.Namespace) -> int:
    return subprocess.call(
        [sys.executable, str(REPO_ROOT / "scripts/check_learner_progress.py")],
        cwd=REPO_ROOT,
    )


def _load_index() -> dict | None:
    if not INDEX_PATH.exists():
        print(
            "docs/plan-index.json is missing. Generate it with:\n"
            "  uv run python scripts/build_plan_index.py",
            file=sys.stderr,
        )
        return None
    return json.loads(INDEX_PATH.read_text(encoding="utf-8"))


def cmd_plan(args: argparse.Namespace) -> int:
    index = _load_index()
    if index is None:
        return 1
    days = index.get("day_deep_dive", {})

    if args.list or args.day is None:
        print("Days with implementation steps:\n")
        for key, entry in days.items():
            print(
                f"  {key:<8} ~{entry['approx_tokens']:>5} tokens   {entry['title'][:56]}"
            )
        print("\nPrint one with:  agentic-pm-lab plan 7")
        return 0

    key = f"day-{args.day}"
    entry = days.get(key)
    if entry is None:
        print(
            f"No implementation steps for day {args.day}. "
            f"Known: {', '.join(d.split('-')[1] for d in days)}",
            file=sys.stderr,
        )
        return 1

    lines = (REPO_ROOT / entry["file"]).read_text(encoding="utf-8").splitlines()
    body = "\n".join(lines[entry["start_line"] - 1 : entry["end_line"]])
    if args.quiet:
        print(body)
        return 0
    print(
        f"# {entry['file']} lines {entry['start_line']}-{entry['end_line']} "
        f"(~{entry['approx_tokens']} tokens)\n"
    )
    print(body)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    """Run the CI gates locally, in CI's order, stopping at the first failure."""
    selected = CHECKS[:3] if args.fast else CHECKS
    failed = []
    for name, command in selected:
        print(f"-- {name} ", end="", flush=True)
        result = subprocess.run(
            ["uv", "run", *command],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print("ok")
        else:
            print("FAILED")
            failed.append(name)
            sys.stdout.write(result.stdout[-2000:])
            sys.stderr.write(result.stderr[-2000:])
            if not args.keep_going:
                break
    if failed:
        print(f"\n{len(failed)} check(s) failed: {', '.join(failed)}")
        return 1
    print(f"\nAll {len(selected)} checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentic-pm-lab",
        description="Governed agent engineering for portfolio management.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command")

    learn = sub.add_parser("learn", help="list the courses, or teach one")
    learn.add_argument("topic", nargs="?", help="topic id; omit to list")
    learn.set_defaults(func=cmd_learn)

    course = sub.add_parser("course", help="full outline for one course")
    course.add_argument("topic")
    course.set_defaults(func=cmd_course)

    quiz = sub.add_parser("quiz", help="take a topic's quiz interactively")
    quiz.add_argument("topic")
    quiz.set_defaults(func=cmd_quiz)

    progress = sub.add_parser("progress", help="what you have completed")
    progress.set_defaults(func=cmd_progress)

    plan = sub.add_parser(
        "plan",
        help="print one day's implementation steps (developer)",
        description=(
            "Print a bounded slice of docs/PLAN.md. Useful for pasting into an "
            "agent that cannot read your filesystem -- a browser-based Copilot "
            "or ChatGPT session -- where one day is ~1,800 tokens against "
            "~51,000 for the whole file."
        ),
    )
    plan.add_argument("day", nargs="?", type=int, help="day number, e.g. 7")
    plan.add_argument("--list", action="store_true", help="list available days")
    plan.add_argument(
        "--quiet",
        action="store_true",
        help="omit the location header, for piping",
    )
    plan.set_defaults(func=cmd_plan)

    check = sub.add_parser("check", help="run the gates CI runs (developer)")
    check.add_argument("--fast", action="store_true", help="lint and format only")
    check.add_argument(
        "--keep-going", action="store_true", help="run all gates, do not stop at first"
    )
    check.set_defaults(func=cmd_check)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        print(OVERVIEW, end="")
        raise SystemExit(0)
    raise SystemExit(args.func(args))
