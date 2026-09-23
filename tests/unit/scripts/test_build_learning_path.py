"""The generated learning-path tables, tested on how they could mislead.

A stale copy is worse than none: the README would recommend one order while
the CLI printed another. So these assert the committed targets are current,
that links resolve from wherever each copy lives, and that rewriting leaves
everything outside the markers alone.
"""

import re

import pytest

from scripts.build_learning_path import (
    END_MARKER,
    ROOT,
    START_MARKER,
    TARGETS,
    main,
    render_block,
    rewrite,
)
from src.education.tutor import TOPIC_CATALOG


def test_committed_targets_are_current():
    assert main(["--check"]) == 0


@pytest.mark.parametrize("target", TARGETS, ids=lambda p: p.name)
def test_every_link_resolves_relative_to_its_target(target):
    links = re.findall(r"\]\(([^)]+)\)", render_block(target))
    assert len(links) == len(TOPIC_CATALOG)
    for link in links:
        assert (target.parent / link).resolve().is_file(), link


def test_rows_follow_the_catalog_order():
    block = render_block(ROOT / "README.md")
    positions = [block.index(f"`{topic}`") for topic in TOPIC_CATALOG]
    assert positions == sorted(positions)


def test_rewrite_only_touches_the_marked_block():
    text = f"before\n{START_MARKER}\nold\n{END_MARKER}\nafter\n"
    out = rewrite(text, f"{START_MARKER}\nnew\n{END_MARKER}", ROOT / "README.md")
    assert out == f"before\n{START_MARKER}\nnew\n{END_MARKER}\nafter\n"


def test_a_target_without_markers_is_an_error_not_a_silent_skip():
    with pytest.raises(ValueError, match="markers"):
        rewrite("no markers here", "block", ROOT / "README.md")
