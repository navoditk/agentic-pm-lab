"""Build the self-contained Agentic PM Lab learning curriculum website."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/agentic-pm-curriculum.html"
REPOSITORY_URL = "https://github.com/navoditk/agentic-pm-lab"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Documents whose full text is also rendered on the page, mapped to
# (heading-id prefix, id of the element that holds the whole document). A link
# to one of them stays on the page instead of sending a reader who may have
# no other access off to GitHub. Filled by `load_curriculum`; empty for a bare
# `render_markdown` call, which keeps the plain GitHub-link behaviour.
IN_PAGE_DOCUMENTS: dict[str, tuple[str, str]] = {}


def slugify(heading: str) -> str:
    """GitHub's heading-anchor rule, so a `doc.md#section` link means the same
    thing on the page as it does on GitHub."""
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", heading)
    text = re.sub(r"[^\w\- ]", "", text.lower().replace("`", ""))
    return text.replace(" ", "-")


def in_page_link(relative_path: str, fragment: str) -> str | None:
    document = IN_PAGE_DOCUMENTS.get(relative_path)
    if document is None:
        return None
    prefix, container_id = document
    return f"#{prefix}{fragment}" if fragment else f"#{container_id}"


def repository_link(href: str, source_path: Path | None) -> str:
    """Keep links to on-page documents on the page; send the rest to GitHub."""
    parsed = urlsplit(href)
    if href.startswith("#") and source_path is not None:
        try:
            source = source_path.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            return href
        return in_page_link(source, parsed.fragment) or href
    if parsed.scheme or parsed.netloc or href.startswith(("#", "/", "mailto:")):
        return href
    if source_path is None:
        return href

    target = (source_path.parent / parsed.path).resolve()
    try:
        relative_target = target.relative_to(ROOT)
    except ValueError:
        return href
    on_page = in_page_link(relative_target.as_posix(), parsed.fragment)
    if on_page:
        return on_page
    location = "tree" if target.is_dir() else "blob"
    return urlunsplit(
        (
            "https",
            "github.com",
            f"{urlsplit(REPOSITORY_URL).path}/{location}/main/{relative_target.as_posix()}",
            parsed.query,
            parsed.fragment,
        )
    )


# Top-level directories whose contents are worth linking to. Anchored, so a
# path only matches from a real repository root rather than mid-string.
_LINKABLE_ROOTS = (
    "src",
    "tests",
    "scripts",
    "docs",
    "skills",
    "config",
    "governance",
    "evals",
    "data",
    "experiments",
    ".github",
)
_PATH_IN_CODE = re.compile(
    r"<code>((?:"
    + "|".join(re.escape(d) for d in _LINKABLE_ROOTS)
    + r")/[\w./-]+)</code>"
)
_ANCHOR_SPAN = re.compile(r"(<a\b[^>]*>.*?</a>)", re.DOTALL)


def linkify_repository_paths(rendered: str) -> str:
    """Turn `<code>src/foo.py</code>` into a link to that file on GitHub.

    The curriculum cites repository files constantly -- 205 such references --
    but only the handful already written as Markdown links were clickable. For
    the reader this page is built for, someone in an environment where cloning
    is not allowed, an unlinked path is a dead end: they can see that
    `src/observability/telemetry.py` matters and have no way to look at it.

    Two guards keep this from creating noise. A path is linked only if it
    **exists in the repository**, so a renamed or illustrative path stays
    plain text rather than becoming a 404. And anchor spans are held out of
    the substitution, so a path already inside a Markdown link is not wrapped
    a second time into nested anchors.

    Fenced blocks never reach this function -- `render_markdown` escapes them
    directly into `<pre>` -- so sample code is left alone.
    """

    def link_one(match: re.Match[str]) -> str:
        path = match.group(1)
        if not (ROOT / path).exists():
            return match.group(0)
        on_page = in_page_link(path, "")
        if on_page:
            return f'<a href="{on_page}"><code>{path}</code></a>'
        location = "tree" if (ROOT / path).is_dir() else "blob"
        return (
            f'<a class="src" href="{REPOSITORY_URL}/{location}/main/{path}">'
            f"<code>{path}</code></a>"
        )

    return "".join(
        part if _ANCHOR_SPAN.fullmatch(part) else _PATH_IN_CODE.sub(link_one, part)
        for part in _ANCHOR_SPAN.split(rendered)
    )


def source_file_link(path: str) -> str:
    """Render one repository path as a clickable `<code>` link.

    For the places that build HTML directly rather than going through
    `inline_markdown` -- the per-course "Source:" line and the footer. Those
    are the citations a reader is most likely to want to open, and they were
    the ones left as dead text.
    """
    safe = html.escape(path)
    if not (ROOT / path).exists():
        return f"<code>{safe}</code>"
    location = "tree" if (ROOT / path).is_dir() else "blob"
    return (
        f'<a class="src" href="{REPOSITORY_URL}/{location}/main/{safe}">'
        f"<code>{safe}</code></a>"
    )


_CODE_SPAN = re.compile(r"(<code>.*?</code>)", re.DOTALL)
# *text*, but not **bold**, a list marker, or an asterisk inside a word.
_EMPHASIS = re.compile(r"(?<![*\w])\*(?![\s*])([^*\n]+?)(?<!\s)\*(?![*\w])")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCE = re.compile(r"^[ \t]*```.*$", re.MULTILINE)


def strip_comments(markdown: str) -> str:
    """Remove HTML comments outside code fences, wherever they sit.

    Comments are source-only notes, such as generated-block markers. Removing
    only whole lines that start with `<!--` left inline comments on the page
    as escaped text, and dropped any prose after a multi-line comment's `-->`.
    """
    parts: list[str] = []
    position, inside = 0, False
    for fence in _FENCE.finditer(markdown):
        segment = markdown[position : fence.start()]
        parts.append(segment if inside else _COMMENT.sub("", segment))
        parts.append(fence.group(0))
        position, inside = fence.end(), not inside
    tail = markdown[position:]
    parts.append(tail if inside else _COMMENT.sub("", tail))
    return "".join(parts)


def inline_markdown(text: str, source_path: Path | None = None) -> str:
    """Render the small Markdown subset used by curriculum source documents."""
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    # Emphasis may wrap code spans, but must not reach inside one, so `a*b*c`
    # in code stays literal: hold code spans aside while emphasis is applied.
    spans: list[str] = []

    def hold(match: re.Match[str]) -> str:
        spans.append(match.group(0))
        return f"\x00{len(spans) - 1}\x00"

    escaped = _EMPHASIS.sub(r"<em>\1</em>", _CODE_SPAN.sub(hold, escaped))
    escaped = re.sub(r"\x00(\d+)\x00", lambda m: spans[int(m.group(1))], escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)",
        lambda match: (
            f'<a href="{repository_link(html.unescape(match.group(2)), source_path)}">'
            f"{match.group(1)}</a>"
        ),
        escaped,
    )
    return linkify_repository_paths(escaped)


def render_markdown(markdown: str, source_path: Path | None = None) -> str:
    """Render headings, lists, code blocks, tables, links, and paragraphs.

    Headings get ids only for documents registered in IN_PAGE_DOCUMENTS, with
    that document's prefix, so fourteen deep dives can each have a "Core
    concepts" section without colliding ids.
    """
    markdown = strip_comments(markdown)
    output: list[str] = []
    paragraph: list[str] = []
    list_tag: str | None = None
    item: list[str] = []
    in_table = False
    in_code = False
    code: list[str] = []
    prefix = None
    if source_path is not None:
        try:
            document = IN_PAGE_DOCUMENTS.get(
                source_path.resolve().relative_to(ROOT).as_posix()
            )
        except ValueError:
            document = None
        prefix = document[0] if document else None
    seen_slugs: dict[str, int] = {}

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline_markdown(' '.join(paragraph), source_path)}</p>")
            paragraph.clear()

    def flush_item() -> None:
        if item:
            output.append(f"<li>{inline_markdown(' '.join(item), source_path)}</li>")
            item.clear()

    def close_list() -> None:
        nonlocal list_tag, in_table
        flush_item()
        if list_tag:
            output.append(f"</{list_tag}>")
            list_tag = None
        # A table ends at the first line that is not a table row. Leaving one
        # open is not cosmetic: inside an unclosed <table> the browser ignores
        # a later </details>, so everything after it on the page is swallowed
        # into that collapsed section. That hid every course on the published
        # page behind the Phase 1 recap.
        if in_table:
            output.append("</tbody></table></div>")
            in_table = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        # Indented fences count. A ```python opening a block inside a numbered
        # list is indented by three spaces, and matching only at column zero
        # left fourteen such blocks in the tutor docs rendering as literal
        # backticks inside a paragraph -- the reader saw ``` and a squashed
        # one-line version of what should have been a code sample.
        if line.lstrip().startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                output.append(
                    f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>"
                )
                code.clear()
            in_code = not in_code
            continue
        if in_code:
            code.append(raw_line)
            continue
        if not line:
            flush_paragraph()
            close_list()
            continue
        if line.startswith("#"):
            flush_paragraph()
            close_list()
            level = min(len(line) - len(line.lstrip("#")), 4)
            text = line[len(line) - len(line.lstrip("#")) :].strip()
            id_attr = ""
            if prefix is not None:
                slug = slugify(text)
                count = seen_slugs.get(slug, 0)
                seen_slugs[slug] = count + 1
                anchor = f"{slug}-{count}" if count else slug
                id_attr = f' id="{html.escape(prefix + anchor)}"'
            output.append(
                f"<h{level}{id_attr}>{inline_markdown(text, source_path)}</h{level}>"
            )
            continue
        if line.startswith("> "):
            flush_paragraph()
            close_list()
            output.append(
                f"<blockquote>{inline_markdown(line[2:], source_path)}</blockquote>"
            )
            continue
        if line in {"---", "***", "___"}:
            flush_paragraph()
            close_list()
            output.append("<hr>")
            continue
        unordered = re.match(r"^\s*[-*] (.+)$", line)
        ordered = re.match(r"^\s*\d+\. (.+)$", line)
        if unordered or ordered:
            flush_paragraph()
            flush_item()
            expected_tag = "ul" if unordered else "ol"
            if list_tag != expected_tag:
                close_list()
                output.append(f"<{expected_tag}>")
                list_tag = expected_tag
            item.append((unordered or ordered).group(1))
            continue
        # A wrapped list item: an indented line that continues the item above.
        # Treating it as a paragraph split the sentence and closed the list.
        if list_tag and item and raw_line[:1] in {" ", "\t"}:
            item.append(line.strip())
            continue
        if "|" in line and line.strip().startswith("|"):
            flush_paragraph()
            flush_item()
            if list_tag:
                output.append(f"</{list_tag}>")
                list_tag = None
            if set(line.replace("|", "").strip()) <= {"-", ":"}:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not in_table:
                output.append('<div class="table-wrap"><table><thead><tr>')
                output.extend(
                    f"<th>{inline_markdown(cell, source_path)}</th>" for cell in cells
                )
                output.append("</tr></thead><tbody>")
                in_table = True
            else:
                output.append("<tr>")
                output.extend(
                    f"<td>{inline_markdown(cell, source_path)}</td>" for cell in cells
                )
                output.append("</tr>")
            continue
        close_list()
        paragraph.append(line.strip())
    flush_paragraph()
    close_list()
    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
    return "\n".join(output)


def topic_freshness(
    catalog: dict[str, dict[str, str]], registry: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Summarize reviewed external sources for each learner-facing course."""
    freshness = {topic_id: {"sources": []} for topic_id in catalog}
    for source in registry["sources"]:
        reviewed = source["last_reviewed"]
        next_review = reviewed + timedelta(days=source["review_after_days"])
        source_status = source.get(
            "monitor_state",
            "enrollment-pending" if "monitor_baseline" not in source else "scheduled",
        )
        for impact in source["impacts"]:
            freshness[impact["topic"]]["sources"].append(
                {
                    "title": source["title"],
                    "url": source["url"],
                    "status": source_status,
                    "last_reviewed": reviewed.isoformat(),
                    "next_review": next_review.isoformat(),
                }
            )
    for topic in freshness.values():
        topic["sources"].sort(key=lambda source: source["title"])
        topic["status"] = next(
            (
                status
                for status in (
                    "upstream-review-required",
                    "source-check-unavailable",
                    "enrollment-pending",
                )
                if any(source["status"] == status for source in topic["sources"])
            ),
            "scheduled",
        )
    return freshness


# Whole documents rendered on the page besides the deep dives: title ->
# (repository path, id of the <details> that holds it).
SHARED_GUIDES: dict[str, tuple[str, str]] = {
    "Mastery skill": ("docs/learning/MASTERY_SKILL.md", "guide-mastery"),
    "Course guide": ("docs/learning/TUTOR_COURSE_GUIDE.md", "guide-course"),
    "Depth path": ("docs/learning/DEPTH_PATH.md", "guide-depth"),
    "Phase 1 recap": ("docs/learning/PHASE_1_RECAP.md", "roadmap-recap"),
}


def load_curriculum() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from src.education.tutor import TOPIC_CATALOG, load_quiz

    courses = json.loads((ROOT / "docs/learning/tutor-courses.json").read_text())
    registry = yaml.safe_load(
        (ROOT / "docs/reference/source-registry.yaml").read_text(encoding="utf-8")
    )
    if not isinstance(registry, dict):
        raise TypeError("source registry must be a mapping")
    freshness = topic_freshness(TOPIC_CATALOG, registry)
    topics: dict[str, Any] = {}
    shared_guides = {title: ROOT / path for title, (path, _) in SHARED_GUIDES.items()}
    IN_PAGE_DOCUMENTS.clear()
    for topic_id, source in TOPIC_CATALOG.items():
        IN_PAGE_DOCUMENTS[source["deep_dive"]] = (f"{topic_id}--", topic_id)
    for path, container_id in SHARED_GUIDES.values():
        IN_PAGE_DOCUMENTS[path] = (f"{container_id}--", container_id)
    fingerprint_parts: list[str] = []
    for topic_id, source in TOPIC_CATALOG.items():
        deep_dive_path = ROOT / source["deep_dive"]
        quiz_path = ROOT / source["quiz_file"]
        deep_dive = deep_dive_path.read_text()
        quiz = load_quiz(topic_id)  # applies the default tier, like every surface
        topics[topic_id] = {
            **source,
            "course": courses[topic_id],
            "deep_dive_html": render_markdown(deep_dive, deep_dive_path),
            "quiz": quiz,
            "freshness": freshness[topic_id],
        }
        fingerprint_parts.extend((deep_dive, quiz_path.read_text()))
    fingerprint_parts.append(json.dumps(courses, sort_keys=True))
    shared_html = {}
    for title, path in shared_guides.items():
        content = path.read_text()
        shared_html[title] = render_markdown(content, path)
        fingerprint_parts.append(content)
    fingerprint = hashlib.sha256("\n".join(fingerprint_parts).encode()).hexdigest()[:12]
    return (
        TOPIC_CATALOG,
        topics,
        {"fingerprint": fingerprint, "shared_html": shared_html},
    )


def build_html() -> str:
    catalog, topics, metadata = load_curriculum()
    stages: dict[str, list[str]] = {}
    for topic_id in catalog:
        stages.setdefault(topics[topic_id]["course"]["stage"], []).append(topic_id)
    total_hours = sum(topic["course"]["est_hours"] for topic in topics.values())
    core_hours = sum(
        topic["course"]["est_hours"]
        for topic in topics.values()
        if topic["course"]["required"]
    )
    module_notes = {
        "Agent core": "The agent loop, architecture, LangGraph, MCP, OpenTelemetry, evaluations, and governance.",
        "Capstone": "Rebuild one agent decision from a single trace id.",
        "Finance domain": "Apply the core to fixed income and portfolio management.",
        "Platforms": "AWS Bedrock and AgentCore, Copilot Canvas, and skill tooling. Take the ones for your stack.",
    }
    module_rows = "".join(
        f'<tr><th scope="row">{html.escape(stage)}</th>'
        f"<td>{'Required' if topics[ids[0]]['course']['required'] else 'Optional'}</td>"
        f"<td>{len(ids)}</td>"
        f"<td>~{sum(topics[t]['course']['est_hours'] for t in ids)}h</td>"
        f"<td>{html.escape(module_notes.get(stage, ''))}</td></tr>"
        for stage, ids in stages.items()
    )
    first_topic = next(iter(catalog))
    cards = "\n".join(
        f'<h3 class="stage">{html.escape(stage)} '
        f'<span class="badge{"" if topics[ids[0]]["course"]["required"] else " optional"}">'
        f"{'Required' if topics[ids[0]]['course']['required'] else 'Optional'}</span>"
        f' <span class="meta">~{sum(topics[t]["course"]["est_hours"] for t in ids)}h</span></h3>'
        f'<nav class="topic-grid" aria-label="{html.escape(stage)} courses">'
        + "".join(
            f'<a class="topic-card" href="#{t}"><span class="step">{topics[t]["course"]["step"]:02}'
            f"</span><strong>{html.escape(catalog[t]['label'])}</strong>"
            f'<span class="meta">~{topics[t]["course"]["est_hours"]}h · {len(topics[t]["quiz"])} questions</span></a>'
            for t in ids
        )
        + "</nav>"
        for stage, ids in stages.items()
    )
    status_links = " · ".join(
        f'<a href="{REPOSITORY_URL}/blob/main/{path}">{label}</a>'
        for label, path in (
            ("Day-by-day status", "PROGRESS.md"),
            ("Local vs live evidence", "docs/evidence/EVIDENCE.md"),
            ("Architecture", "docs/architecture/ARCHITECTURE.md"),
            ("Completion audit", "docs/learning/PLAN_REVIEW.md"),
            ("Full build plan", "docs/PLAN.md"),
        )
    )
    sections = []
    quiz_data: dict[str, list[dict[str, Any]]] = {}
    for topic_id, topic in topics.items():
        course = topic["course"]
        freshness = topic["freshness"]
        source_items = "".join(
            (
                f'<li><a href="{html.escape(source["url"])}">'
                f'{html.escape(source["title"])}</a> <span class="meta">reviewed '
                f"{source['last_reviewed']}, next review {source['next_review']}</span></li>"
            )
            for source in freshness["sources"]
        )
        freshness_message = {
            "upstream-review-required": "An upstream source changed; review pending.",
            "source-check-unavailable": "Source check unavailable; review pending.",
            # Monitor enrollment is maintainer bookkeeping, not a learner concern.
            "enrollment-pending": "",
        }.get(freshness["status"], "")
        quiz_data[topic_id] = topic["quiz"]
        sections.append(
            f"""<section id="{topic_id}" class="topic">
<p class="eyebrow">Course {course["step"]:02} · {html.escape(course["stage"])} · ~{course["est_hours"]}h</p>
<h2>{html.escape(topic["label"])}</h2>
<p class="source">Source: {source_file_link(topic["deep_dive"])} · {len(topic["quiz"])} quiz questions</p>
<details class="freshness" data-freshness="{freshness["status"]}"><summary>External sources ({len(freshness["sources"])}) <span class="meta">{html.escape(freshness_message)}</span></summary><ul>{source_items}</ul></details>
<div class="course-grid">
<div><h3>Prerequisites</h3><ul>{"".join(f"<li>{inline_markdown(item, ROOT / 'docs/learning/tutor-courses.json')}</li>" for item in course["prerequisites"])}</ul></div>
<div><h3>Objectives</h3><ul>{"".join(f"<li>{inline_markdown(item, ROOT / 'docs/learning/tutor-courses.json')}</li>" for item in course["objectives"])}</ul></div>
</div>
<h3>Lessons</h3><ol>{"".join(f"<li>{inline_markdown(item, ROOT / 'docs/learning/tutor-courses.json')}</li>" for item in course["lessons"])}</ol>
<div class="labs"><p><strong>Local lab (run after cloning):</strong> {inline_markdown(course["local_lab"], ROOT / "docs/learning/tutor-courses.json")}</p>
<p><strong>Failure lab (run after cloning):</strong> {inline_markdown(course["failure_lab"], ROOT / "docs/learning/tutor-courses.json")}</p>
<p><strong>Build lab (run after cloning):</strong> {inline_markdown(course["build_lab"], ROOT / "docs/learning/tutor-courses.json")}</p>
<p><strong>Teach-back:</strong> {inline_markdown(course["assessment"], ROOT / "docs/learning/tutor-courses.json")}</p></div>
<details class="deep-dive"><summary>Read the deep dive</summary><article>{topic["deep_dive_html"]}</article></details>
<button class="quiz-button" data-topic="{topic_id}">Start this topic's quiz</button>
<p class="to-top"><a href="#courses">All courses</a> · <a href="#top">Back to top ↑</a></p>
</section>"""
        )
    quiz_json = json.dumps(quiz_data).replace("</", "<\\/")
    from src.education.tutor import OVERALL_PASS, TIER_PASS

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agentic PM Lab Learning Curriculum</title>
<meta name="description" content="{len(catalog)} source-grounded courses on building and governing agentic AI, with quizzes that run in the browser.">
<style>
:root{{color-scheme:light dark;--ink:#16202c;--muted:#56657a;--accent:#1560a8;--accent-ink:#fff;--card:#fff;--line:#dbe3ec;--soft:#eef4fa;--page:#f6f8fb;--hero:#0e2238;--hero-ink:#dce6f2;--code-bg:#eef2f7;--warning:#7a4a00;--warning-bg:#fff3dc;--ok:#1f8a4c;--ok-bg:#e7f6ed;--bad:#c0392b;--bad-bg:#fbeaea;--gutter:clamp(1rem,4vw,2.5rem);--wrap:1180px;--measure:72ch}}
@media(prefers-color-scheme:dark){{:root{{--ink:#e6ecf2;--muted:#a7b4c3;--accent:#7cb9f4;--accent-ink:#0b1622;--card:#17212c;--line:#314154;--soft:#1f2e3e;--page:#0f1720;--hero:#0a1622;--hero-ink:#c5d3e2;--code-bg:#223244;--warning:#ffd48c;--warning-bg:#45310f;--ok:#4cc38a;--ok-bg:#14301f;--bad:#f07167;--bad-bg:#3a1a17}}}}
*{{box-sizing:border-box}}
html{{font-size:clamp(16px,.85rem + .22vw,19px);scroll-padding-top:4rem;-webkit-text-size-adjust:100%}}
body{{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.6;color:var(--ink);background:var(--page)}}
.wrap{{width:min(var(--wrap),100% - 2*var(--gutter));margin-inline:auto}}
a{{color:var(--accent);text-underline-offset:.15em}} a:focus-visible,button:focus-visible,summary:focus-visible{{outline:3px solid var(--accent);outline-offset:2px;border-radius:.25rem}}
.src{{text-decoration:none;border-bottom:1px dotted currentColor}}.src:hover{{border-bottom-style:solid}}
h1,h2,h3,h4{{line-height:1.2;letter-spacing:-.01em}} h2{{font-size:clamp(1.45rem,1.2rem + 1vw,1.9rem);margin:2.5rem 0 .75rem}} h3{{font-size:1.1rem;margin:1.5rem 0 .4rem}} h4{{font-size:1rem}}
p,li{{max-width:var(--measure)}}
ul,ol{{padding-left:1.25rem}} li{{margin:.2rem 0}}
header.hero{{background:var(--hero);color:#fff;padding:clamp(2rem,6vw,4.5rem) 0 clamp(1.75rem,4vw,3rem)}}
.hero .kicker{{margin:0 0 .75rem;color:var(--hero-ink);font-size:.8rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase}}
.hero h1{{font-size:clamp(2rem,1.4rem + 3vw,3.4rem);margin:0 0 1rem;max-width:18ch}}
.hero .lead{{color:var(--hero-ink);font-size:clamp(1.02rem,.95rem + .35vw,1.25rem);max-width:60ch;margin:0 0 1.5rem}}
.actions{{display:flex;flex-wrap:wrap;gap:.6rem}}
.btn{{display:inline-flex;align-items:center;min-height:44px;padding:.55rem 1.1rem;border-radius:.45rem;font-weight:650;text-decoration:none;border:1px solid transparent}}
.btn.primary{{background:#fff;color:#0e2238}} .btn.ghost{{color:#fff;border-color:#ffffff66}} .btn:hover{{filter:brightness(.95)}}
.jump{{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--line);box-shadow:0 1px 6px #0000000d}}
.jump .wrap{{display:flex;gap:1.5rem;overflow-x:auto;white-space:nowrap;scrollbar-width:none}} .jump .wrap::-webkit-scrollbar{{display:none}}
.jump a{{display:inline-block;padding:.8rem 0;text-decoration:none;font-weight:600;font-size:.95rem}} .jump a:hover{{text-decoration:underline}}
main{{padding:1.5rem 0 4rem}}
.notice{{background:var(--soft);border-left:4px solid var(--accent);border-radius:0 .5rem .5rem 0;padding:.9rem 1.1rem;margin:1rem 0 0;font-size:.95rem}} .notice p{{margin:0;max-width:none}}
.table-wrap{{overflow-x:auto;margin:1rem 0;border:1px solid var(--line);border-radius:.5rem;background:var(--card)}}
table{{border-collapse:collapse;width:100%;font-size:.93rem}} th,td{{padding:.6rem .75rem;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}} tr:last-child td,tr:last-child th{{border-bottom:0}} thead th{{background:var(--soft);font-weight:650;white-space:nowrap}} tbody th{{font-weight:650}}
.modules th[scope=row],.modules td:nth-child(2),.modules td:nth-child(3),.modules td:nth-child(4){{white-space:nowrap}}
.stage{{display:flex;flex-wrap:wrap;align-items:baseline;gap:.5rem;margin-top:2rem}}
.badge{{font-size:.72rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:.15rem .5rem;border-radius:999px;background:var(--accent);color:var(--accent-ink)}} .badge.optional{{background:var(--soft);color:var(--muted);border:1px solid var(--line)}}
.meta{{color:var(--muted);font-size:.85rem;font-weight:400}}
.topic-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,240px),1fr));gap:.75rem}}
.topic-card{{display:flex;flex-direction:column;gap:.2rem;background:var(--card);border:1px solid var(--line);border-radius:.6rem;padding:.9rem 1rem;text-decoration:none;color:var(--ink);transition:border-color .15s,box-shadow .15s}}
.topic-card:hover{{border-color:var(--accent);box-shadow:0 2px 10px #0000000f}} .topic-card .step{{color:var(--accent);font:700 .8rem ui-monospace,SFMono-Regular,Menlo,monospace}} .topic-card strong{{line-height:1.3}}
.topic{{background:var(--card);border:1px solid var(--line);border-radius:.8rem;padding:clamp(1rem,3vw,2rem);margin:1.5rem 0}} .topic h2{{margin-top:.25rem}}
.eyebrow,.source{{color:var(--muted);font-size:.88rem;margin:0}} .topic .source{{margin:.25rem 0 1rem}}
details.freshness{{border:1px solid var(--line);border-radius:.5rem;margin:.75rem 0 1rem;padding:0 .9rem;font-size:.88rem;background:var(--card)}} details.freshness summary{{min-height:40px;gap:.5rem;flex-wrap:wrap;font-weight:600}} details.freshness ul{{margin:.25rem 0 .75rem;padding-left:1.1rem}} details.freshness li{{margin:.2rem 0}}
.freshness[data-freshness="upstream-review-required"],.freshness[data-freshness="source-check-unavailable"],.freshness.overdue{{background:var(--warning-bg);border-color:transparent}} .flag{{color:var(--warning)}}
.course-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:0 2rem}}
.labs{{background:var(--soft);border-radius:.5rem;padding:.4rem 1.1rem;margin:1.25rem 0}} .labs p{{max-width:none}}
details{{border-top:1px solid var(--line);margin-top:1.25rem;padding-top:.9rem}} summary{{cursor:pointer;font-weight:650;min-height:44px;display:flex;align-items:center}} summary::marker{{color:var(--accent)}}
details[open]>summary{{margin-bottom:.5rem}}
article{{max-width:80ch}} article table{{font-size:.9rem}}
code{{font:.88em ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--code-bg);padding:.1em .35em;border-radius:.3rem;overflow-wrap:anywhere}}
pre{{overflow:auto;background:#142130;color:#eef3f8;padding:1rem 1.1rem;border-radius:.5rem;font-size:.88rem;line-height:1.5}} pre code{{background:none;padding:0;overflow-wrap:normal}}
blockquote{{margin:1rem 0;padding:.5rem 1rem;border-left:3px solid var(--line);color:var(--muted)}}
button{{font:inherit;background:var(--accent);border:0;border-radius:.45rem;color:var(--accent-ink);min-height:44px;padding:.6rem 1.1rem;font-weight:650;cursor:pointer}}
.quiz-button{{margin-top:1.25rem}}
.to-top{{display:flex;justify-content:flex-end;gap:1rem;font-size:.88rem;margin:1rem 0 0;max-width:none}}
dialog{{width:min(760px,100vw - 1.5rem);max-height:min(92vh,100dvh - 1.5rem);overflow:auto;border:0;border-radius:.8rem;box-shadow:0 20px 60px #0007;padding:clamp(1rem,3vw,1.75rem);background:var(--card);color:var(--ink)}} dialog::backdrop{{background:#000a}}
dialog h2{{font-size:1.2rem;margin:.25rem 0 1rem}} .quiz-bar{{display:flex;justify-content:space-between;align-items:center;gap:1rem;border-bottom:1px solid var(--line);padding-bottom:.6rem;margin-bottom:.75rem}} .quiz-bar strong{{font-size:.95rem}} #close{{background:var(--soft);color:var(--ink);min-height:40px;padding:.4rem .9rem}} #quiz-body:focus{{outline:none}}
.choice{{display:block;width:100%;margin:.5rem 0;text-align:left;background:var(--soft);color:var(--ink);border:1px solid var(--line);font-weight:500;line-height:1.4}} .choice:hover:not(:disabled){{border-color:var(--accent)}} .choice:disabled{{cursor:default;opacity:.7}} .choice.right{{opacity:1;border:2px solid var(--ok);background:var(--ok-bg)}} .choice.wrong{{opacity:1;border:2px solid var(--bad);background:var(--bad-bg)}}
.result{{font-weight:700}} #feedback{{margin-top:1rem}} #feedback button{{margin-top:.75rem;display:block}}
footer{{border-top:1px solid var(--line);color:var(--muted);font-size:.85rem;padding:1.5rem 0 2.5rem}} footer p{{max-width:none;margin:.25rem 0}}
@media(max-width:600px){{.topic{{border-radius:.6rem}} .to-top{{justify-content:flex-start}} h2{{margin-top:2rem}} .actions .btn{{flex:1 1 100%;justify-content:center}}}}
@media print{{.jump,.quiz-button,.actions,dialog{{display:none}} details{{border:0}} body{{background:#fff}}}}
</style></head><body>
<header id="top" class="hero"><div class="wrap">
<p class="kicker">Agentic PM Lab · Learning curriculum</p>
<h1>Build and govern agentic AI, one course at a time</h1>
<p class="lead">{len(catalog)} source-grounded courses, taught through a fixed-income portfolio-management platform. Read every course and take its quiz here, in your browser; nothing to install.</p>
<div class="actions"><a class="btn primary" href="#{first_topic}">Start with course 01</a><a class="btn ghost" href="#courses">Browse all courses</a><a class="btn ghost" href="{REPOSITORY_URL}">View the repository</a></div>
</div></header>
<nav class="jump" aria-label="Page sections"><div class="wrap"><a href="#start">Start</a><a href="#roadmap">What was built</a><a href="#guides">Guides</a><a href="#courses">Courses</a><a href="#top">Top ↑</a></div></nav>
<main class="wrap">
<div class="notice" role="note"><p><strong>Learning material only.</strong> Built on public and mock data; it is not investment advice, a trading system, or evidence of production readiness. Quiz scores here stay in this browser. To record them, and to do the labs, clone the repository.</p></div>
<h2 id="start">Start a path</h2>
<p>The courses are grouped into modules. Only <strong>Agent core</strong> and the <strong>Capstone</strong> are required, about {core_hours} hours together; everything is about {total_hours} hours.</p>
<div class="table-wrap"><table class="modules"><thead><tr><th scope="col">Module</th><th scope="col">Status</th><th scope="col">Courses</th><th scope="col">Time</th><th scope="col">What it covers</th></tr></thead><tbody>{module_rows}</tbody></table></div>
<p>Each course has objectives, three lessons, a deep dive, three labs that run after cloning, and a quiz. Already know some of it? After cloning, <code>uv run agentic-pm-lab placement</code> tells you which required courses you can skip ahead. For a guided tutor, open the repository in Claude Code, Copilot, or Codex and say <code>agentexpert</code>.</p>
<h2 id="roadmap">What was built</h2>
<p>The courses teach a platform built over a 21-day plan: deterministic analytics, governed agents, evaluation, observability, MCP, Canvas, and an AWS AgentCore path. Every day is complete for local, fixture-based verification; live cloud and provider evidence is tracked separately.</p>
<details id="roadmap-recap"><summary>Phase 1 recap: the 21-day build, day by day</summary><article>{metadata["shared_html"]["Phase 1 recap"]}</article></details>
<p class="source">Status and proof on GitHub: {status_links}</p>
<h2 id="guides">Guides</h2>
<details id="guide-course"><summary>How to use this curriculum, and the recommended order</summary><article>{metadata["shared_html"]["Course guide"]}</article></details>
<details id="guide-mastery"><summary>The agentexpert tutor skill</summary><article>{metadata["shared_html"]["Mastery skill"]}</article></details>
<details id="guide-depth"><summary>Depth path</summary><article>{metadata["shared_html"]["Depth path"]}</article></details>
<h2 id="courses">Courses</h2>{cards}
{"".join(sections)}
</main>
<footer><div class="wrap"><p>Generated by {source_file_link("scripts/build_learning_curriculum.py")} from the repository's curriculum sources. Curriculum fingerprint <code>{metadata["fingerprint"]}</code>.</p><p>Check external framework behaviour against the official references each course cites.</p></div></footer>
<dialog id="quiz" aria-labelledby="quiz-title"><div class="quiz-bar"><strong id="quiz-title">Quiz</strong><button id="close" aria-label="Close the quiz">Close</button></div><div id="quiz-body" tabindex="-1"></div></dialog>
<script>
const quizzes={quiz_json}; const dialog=document.querySelector('#quiz'), body=document.querySelector('#quiz-body');
let questions=[], position=0, correct=0, tierScore={{}};
const OVERALL_PASS={OVERALL_PASS}, TIER_PASS={TIER_PASS};
const esc=text=>String(text).replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]);
document.querySelectorAll('.quiz-button').forEach(button=>button.onclick=()=>{{questions=quizzes[button.dataset.topic];position=0;correct=0;tierScore={{}};document.querySelector('#quiz-title').textContent=button.closest('section').querySelector('h2').textContent+' quiz';render();dialog.showModal();body.focus();}});
document.querySelector('#close').onclick=()=>dialog.close();
function render(){{if(position===questions.length){{const tiers=Object.entries(tierScore);const passed=correct/questions.length>=OVERALL_PASS&&tiers.every(([,s])=>s[0]/s[1]>=TIER_PASS);body.innerHTML=`<h2>Quiz complete</h2><p class="result">Score: ${{correct}} / ${{questions.length}} (${{Math.round(correct/questions.length*100)}}%): ${{passed?'meets':'does not yet meet'}} the pass rule of ${{OVERALL_PASS*100}}% overall and ${{TIER_PASS*100}}% in each tier.</p><ul>${{tiers.map(([t,s])=>`<li>${{esc(t)}}: ${{s[0]}} / ${{s[1]}}</li>`).join('')}}</ul><p>This browser score is a learning check. To record it durably, clone the repository and run <code>uv run agentic-pm-lab quiz &lt;topic-id&gt;</code>. Review the cited sources and repeat the local/failure labs before treating a score as course completion.</p>`;return;}}const q=questions[position];body.innerHTML=`<p class="eyebrow">Question ${{position+1}} of ${{questions.length}} · ${{esc(q.tier)}}</p><h2>${{q.question}}</h2>${{q.choices.map((choice,index)=>`<button class="choice" data-index="${{index}}">${{String.fromCharCode(65+index)}}. ${{choice}}</button>`).join('')}}<p id="feedback"></p>`;body.querySelectorAll('.choice').forEach(button=>button.onclick=()=>answer(Number(button.dataset.index),q));}}
function answer(answer,q){{const ok=answer===q.correct_index;if(ok)correct++;const s=tierScore[q.tier]=tierScore[q.tier]||[0,0];s[1]++;if(ok)s[0]++;body.querySelector('#feedback').innerHTML=`<span class="result">${{ok?'Correct.':'Not quite.'}}</span> Source: <a class="src" href="{REPOSITORY_URL}/blob/main/${{q.citation}}"><code>${{q.citation}}</code></a>.${{q.explanation?` <span class="explanation">${{esc(q.explanation)}}</span>`:''}} <button id="next">Continue</button>`;body.querySelectorAll('.choice').forEach(button=>{{button.disabled=true;const i=Number(button.dataset.index);if(i===q.correct_index)button.classList.add('right');else if(i===answer)button.classList.add('wrong');}});body.querySelector('#next').onclick=()=>{{position++;render();}};}}
function reveal(){{const id=decodeURIComponent(location.hash.slice(1));const target=id&&document.getElementById(id);if(!target)return;for(let d=target.closest('details');d;d=d.parentElement.closest('details'))d.open=true;target.scrollIntoView();}}
addEventListener('hashchange',reveal);reveal();
document.addEventListener('click',e=>{{const link=e.target.closest('a[href^="#"]');if(link&&link.getAttribute('href')===location.hash)setTimeout(reveal);}});
for(const panel of document.querySelectorAll('.freshness')){{const dates=[...panel.textContent.matchAll(/next review (\\d{{4}}-\\d{{2}}-\\d{{2}})/g)].map(match=>match[1]);if(dates.some(value=>new Date(`${{value}}T00:00:00Z`)<new Date())){{panel.classList.add('overdue');panel.querySelector('summary').insertAdjacentHTML('beforeend',' <strong class="flag">Review overdue</strong>');}}}}
</script></body></html>"""


def write_output(output: Path, *, check: bool) -> int:
    output = output.resolve()
    display_path = output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
    rendered = build_html()
    if check:
        if not output.is_file() or output.read_text() != rendered:
            print(f"ERROR: generated curriculum is stale: {display_path}")
            return 1
        print(f"Generated curriculum is current: {display_path}")
        return 0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered)
    print(f"Wrote {display_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    return write_output(args.output, check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
