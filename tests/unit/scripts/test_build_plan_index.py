"""The plan index, tested on the failure modes that make an index worse than none.

An index whose line ranges are wrong is actively harmful: it sends an agent
to confidently read the wrong part of a document, which is harder to notice
than having no index at all. So these assert the two ways the ranges go
wrong -- headings that are not headings, and ids that are not unique -- plus
that the committed file stays current.
"""

import json

import pytest

from scripts.build_plan_index import (
    INDEX_PATH,
    build_index,
    index_document,
    iter_headings,
    render,
    section_id,
)

# --- fenced content is not a heading -----------------------------------------


def test_headings_inside_a_code_fence_are_not_headings():
    """The trap this indexer exists to avoid.

    `docs/PLAN.md` embeds an example prompt file whose body uses `## Role`,
    `## Task`, `## Output` and `## Validation`. A naive scan reports four
    phantom top-level sections and emits ranges pointing at the wrong place.
    """
    lines = [
        "## Real Section",
        "```markdown",
        "## Role",
        "## Task",
        "```",
        "## Another Real Section",
    ]
    assert [text for _, _, text in iter_headings(lines)] == [
        "Real Section",
        "Another Real Section",
    ]


def test_tilde_fences_count_too():
    lines = ["~~~", "## Not A Heading", "~~~", "## Heading"]
    assert [t for _, _, t in iter_headings(lines)] == ["Heading"]


def test_a_fence_with_a_language_tag_still_opens_and_closes():
    lines = ["```python", "## nope", "```", "## yes"]
    assert [t for _, _, t in iter_headings(lines)] == ["yes"]


def test_the_real_plan_has_no_phantom_sections():
    """Regression against the actual document, not a synthetic one."""
    sections = index_document("docs/PLAN.md")
    titles = {s["title"] for s in sections}
    assert not titles & {"Role", "Task", "Output", "Validation"}


# --- ranges ------------------------------------------------------------------


def test_a_section_ends_where_the_next_same_level_heading_begins():
    """`start_line` and `end_line` are both 1-indexed and inclusive.

    A nested `### A.1` does not end `## A` -- only a same-or-shallower
    heading does -- so A covers lines 1-4 and B starts on line 5, with no
    gap and no overlap between them.
    """
    lines = ["## A", "body", "### A.1", "more", "## B", "tail"]
    sections = {s["id"]: s for s in _index(lines)}
    assert (sections["a"]["start_line"], sections["a"]["end_line"]) == (1, 4)
    assert sections["b"]["start_line"] == 5
    assert sections["a"]["end_line"] + 1 == sections["b"]["start_line"]


def test_a_parent_range_contains_its_children():
    """Reading a parent must not silently omit its subsections."""
    lines = ["## Parent", "x", "### Child", "y", "## Next"]
    sections = {s["id"]: s for s in _index(lines)}
    child, parent = sections["child"], sections["parent"]
    assert parent["start_line"] <= child["start_line"] < parent["end_line"]


def test_start_line_is_one_indexed_to_match_read_and_sed():
    lines = ["## First"]
    assert _index(lines)[0]["start_line"] == 1


def _index(lines):
    """Run the same entry-building logic over synthetic lines."""
    import scripts.build_plan_index as m

    headings = m.iter_headings(lines)
    entries, seen = [], {}
    for position, (start, level, text) in enumerate(headings):
        end = len(lines)
        for later_start, later_level, _ in headings[position + 1 :]:
            if later_level <= level:
                end = later_start
                break
        base = m.section_id(text)
        seen[base] = seen.get(base, 0) + 1
        entries.append(
            {
                "id": base if seen[base] == 1 else f"{base}-{seen[base]}",
                "title": text,
                "level": level,
                "start_line": start + 1,
                "end_line": end,
            }
        )
    return entries


# --- ids ---------------------------------------------------------------------


def test_repeated_headings_get_unique_ids():
    """An ambiguous id resolves to whichever came first, which is a silent bug."""
    ids = [s["id"] for s in _index(["## Day 1 — x", "a", "## Day 1 — y", "b"])]
    assert len(ids) == len(set(ids))


def test_day_headings_get_a_stable_day_id():
    assert section_id("Day 7 — Control Layer for real") == "day-7"
    assert section_id("Days 13–14 foundation") == "day-13"


def test_every_id_in_the_real_index_is_unique_per_document():
    for document in build_index()["documents"].values():
        ids = [s["id"] for s in document["sections"]]
        assert len(ids) == len(set(ids))


# --- the day lookup ----------------------------------------------------------


def test_day_lookup_resolves_to_appendix_b_not_the_forward_plan_summary():
    """Days 10-14 appear twice in PLAN.md; only Appendix B carries the steps."""
    index = build_index()
    plan = index["documents"]["docs/PLAN.md"]
    appendix = next(s for s in plan["sections"] if s["title"].startswith("Appendix B"))
    for entry in index["day_deep_dive"].values():
        assert appendix["start_line"] <= entry["start_line"] < appendix["end_line"]


def test_day_lookup_covers_every_day_appendix_b_documents():
    index = build_index()
    assert len(index["day_deep_dive"]) >= 12
    assert "day-1" in index["day_deep_dive"]


def test_the_lookup_is_cheaper_than_reading_the_whole_file():
    """The entire point, asserted rather than assumed."""
    index = build_index()
    whole = index["documents"]["docs/PLAN.md"]["approx_tokens"]
    largest = max(e["approx_tokens"] for e in index["day_deep_dive"].values())
    assert largest < whole / 10, (
        f"a day costs {largest} tokens against {whole} for the file; "
        "the index is not buying enough to justify itself"
    )


def test_ranges_point_at_the_heading_they_claim(tmp_path):
    from pathlib import Path

    lines = Path("docs/PLAN.md").read_text(encoding="utf-8").splitlines()
    for day, entry in build_index()["day_deep_dive"].items():
        heading = lines[entry["start_line"] - 1]
        number = day.split("-")[1]
        assert f"Day {number}" in heading, (
            f"{day} points at line {entry['start_line']}: {heading!r}"
        )


# --- staleness ---------------------------------------------------------------


def test_the_committed_index_is_current():
    """Line numbers rot the moment a routed document is edited."""
    assert INDEX_PATH.exists(), "run: uv run python scripts/build_plan_index.py"
    assert INDEX_PATH.read_text(encoding="utf-8") == render(build_index()), (
        "docs/plan-index.json is stale; regenerate it"
    )


def test_the_committed_index_is_valid_json_with_the_expected_shape():
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    assert "day_deep_dive" in index and "documents" in index
    for path, document in index["documents"].items():
        assert document["sections"], f"{path} indexed with no sections"


@pytest.mark.parametrize("required", ["docs/PLAN.md", "PROGRESS.md"])
def test_the_largest_routed_documents_are_indexed(required):
    assert required in build_index()["documents"]
