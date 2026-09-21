"""Generate a line-range index for the large routed documents.

`AGENTS.md` sends an agent to "Appendix B, Day 7" -- a prose heading, not a
location. Complying with that means reading `docs/PLAN.md`, which is ~50,000
tokens, to use the ~1,300 that one day actually occupies. The index turns
every heading into a line range so the agent can read the range instead of
the file.

Generated, never hand-edited. Line numbers rot the moment anyone edits a
source document, so `--check` re-derives the index and compares, and CI runs
it the same way `check_progress.py` validates its committed table.

One parsing detail is load-bearing: **headings inside fenced code blocks are
not headings.** `docs/PLAN.md` embeds an example prompt file containing
`## Role`, `## Task`, `## Output` and `## Validation`. A naive
`startswith("## ")` scan reports those as four top-level sections and emits
line ranges that send an agent to the wrong place. Every heading scan here
tracks fences, and `tests/unit/scripts/test_build_plan_index.py` pins it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = REPO_ROOT / "docs/plan-index.json"

# Every document `AGENTS.md` routes to that is large enough for whole-file
# reads to be wasteful. Ordered, so the generated file has a stable shape.
INDEXED_DOCUMENTS = (
    "docs/PLAN.md",
    "docs/reference/REFERENCES.md",
    "PROGRESS.md",
    "docs/architecture/PRD.md",
    "docs/architecture/ARCHITECTURE.md",
    "INSTALL.md",
)

FENCE = re.compile(r"^\s*(```|~~~)")
DAY = re.compile(r"^#{2,4}\s+Days?\s+(\d+)", re.IGNORECASE)


def iter_headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """Return `(line_index, level, text)` for real headings only.

    A fence toggles on any ``` or ~~~ line regardless of language tag, which
    is what keeps an embedded prompt template's `## Role` out of the index.
    """
    headings: list[tuple[int, int, str]] = []
    in_fence = False
    for index, line in enumerate(lines):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = re.match(r"^(#{2,4})\s+(.*\S)\s*$", line)
        if match:
            headings.append((index, len(match.group(1)), match.group(2)))
    return headings


def slugify(text: str) -> str:
    slug = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text).replace("`", "")
    slug = re.sub(r"[^\w\s-]", "", slug.lower()).strip()
    return re.sub(r"[\s_]+", "-", slug)[:80].strip("-")


def section_id(text: str) -> str:
    """Prefer a stable `day-7` id where the heading names a day."""
    day = DAY.match(f"## {text}")
    if day:
        return f"day-{int(day.group(1))}"
    return slugify(text)


def index_document(relative_path: str) -> list[dict[str, Any]]:
    lines = (REPO_ROOT / relative_path).read_text(encoding="utf-8").splitlines()
    headings = iter_headings(lines)
    entries: list[dict[str, Any]] = []
    seen: dict[str, int] = {}

    for position, (start, level, text) in enumerate(headings):
        # A section ends at the next heading of the same or shallower level,
        # so a parent's range still contains its children.
        end = len(lines)
        for later_start, later_level, _ in headings[position + 1 :]:
            if later_level <= level:
                end = later_start
                break
        body = "\n".join(lines[start:end])
        # Ids must be unique to be usable as a lookup key. `docs/PLAN.md`
        # describes Days 10-14 twice -- once as a short forward-plan summary
        # in §17, once as the Appendix B deep dive -- and an ambiguous `day-10`
        # would resolve to whichever came first, which is the ~190-token
        # summary rather than the ~1,350-token steps an agent asked for.
        base = section_id(text)
        seen[base] = seen.get(base, 0) + 1
        unique_id = base if seen[base] == 1 else f"{base}-{seen[base]}"
        entries.append(
            {
                "id": unique_id,
                "title": text,
                "level": level,
                "file": relative_path,
                "start_line": start + 1,  # 1-indexed, to match Read/sed
                "end_line": end,
                "approx_tokens": len(body) // 4,
            }
        )
    return entries


def day_deep_dives(sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Map `day-N` to the Appendix B deep dive, not the §17 summary.

    This is the lookup `AGENTS.md` routes to: "read Appendix B for that day".
    Resolved by line containment rather than by id, because several days are
    described in both places and only the Appendix B entry carries the steps.
    """
    appendix = next(
        (
            s
            for s in sections
            if s["level"] == 2 and s["title"].startswith("Appendix B")
        ),
        None,
    )
    if appendix is None:
        return {}
    lookup = {}
    for section in sections:
        if not DAY.match(f"## {section['title']}"):
            continue
        if appendix["start_line"] <= section["start_line"] < appendix["end_line"]:
            day = re.match(r"^day-(\d+)", section["id"])
            if day:
                lookup[f"day-{int(day.group(1))}"] = {
                    "file": section["file"],
                    "start_line": section["start_line"],
                    "end_line": section["end_line"],
                    "approx_tokens": section["approx_tokens"],
                    "title": section["title"],
                }
    return dict(sorted(lookup.items(), key=lambda kv: int(kv[0].split("-")[1])))


def build_index() -> dict[str, Any]:
    documents = {}
    plan_sections: list[dict[str, Any]] = []
    for relative_path in INDEXED_DOCUMENTS:
        if not (REPO_ROOT / relative_path).exists():
            continue
        entries = index_document(relative_path)
        if relative_path == "docs/PLAN.md":
            plan_sections = entries
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        documents[relative_path] = {
            "total_lines": len(text.splitlines()),
            "approx_tokens": len(text) // 4,
            "sections": entries,
        }
    return {
        "day_deep_dive": day_deep_dives(plan_sections),
        "generated_by": "scripts/build_plan_index.py",
        "purpose": (
            "Line ranges for the large routed documents, so an agent can read "
            "one section instead of a whole file. Regenerate with "
            "`uv run python scripts/build_plan_index.py`."
        ),
        "documents": documents,
    }


def render(index: dict[str, Any]) -> str:
    return json.dumps(index, indent=2, sort_keys=False) + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed index is stale, without rewriting it",
    )
    args = parser.parse_args(argv)

    rendered = render(build_index())

    if args.check:
        if not INDEX_PATH.exists():
            print(f"{INDEX_PATH.relative_to(REPO_ROOT)} is missing; run this script.")
            return 1
        if INDEX_PATH.read_text(encoding="utf-8") != rendered:
            print(
                f"{INDEX_PATH.relative_to(REPO_ROOT)} is stale. A routed document "
                "changed without the index being regenerated, so its line ranges "
                "now point at the wrong places.\n"
                "Run: uv run python scripts/build_plan_index.py"
            )
            return 1
        print("Plan index is current.")
        return 0

    INDEX_PATH.write_text(rendered, encoding="utf-8")
    total = sum(len(d["sections"]) for d in build_index()["documents"].values())
    print(f"Wrote {INDEX_PATH.relative_to(REPO_ROOT)} ({total} sections).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
