"""Build the self-contained Agentic PM Lab learning curriculum website."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts/agentic-pm-curriculum.html"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def inline_markdown(text: str) -> str:
    """Render the small Markdown subset used by curriculum source documents."""
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)",
        r'<a href="\2">\1</a>',
        escaped,
    )
    return escaped


def render_markdown(markdown: str) -> str:
    """Render headings, lists, code blocks, tables, links, and paragraphs."""
    output: list[str] = []
    paragraph: list[str] = []
    list_tag: str | None = None
    in_code = False
    code: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_tag
        if list_tag:
            output.append(f"</{list_tag}>")
            list_tag = None

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if line.startswith("```"):
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
            output.append(
                f"<h{level}>{inline_markdown(line[level:].strip())}</h{level}>"
            )
            continue
        if line.startswith("> "):
            flush_paragraph()
            close_list()
            output.append(f"<blockquote>{inline_markdown(line[2:])}</blockquote>")
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
            expected_tag = "ul" if unordered else "ol"
            if list_tag != expected_tag:
                close_list()
                output.append(f"<{expected_tag}>")
                list_tag = expected_tag
            output.append(
                f"<li>{inline_markdown((unordered or ordered).group(1))}</li>"
            )
            continue
        if "|" in line and line.strip().startswith("|"):
            flush_paragraph()
            close_list()
            if set(line.replace("|", "").strip()) <= {"-", ":"}:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            tag = "th" if not any("<table" in item for item in output[-1:]) else "td"
            if tag == "th":
                output.append("<table><thead><tr>")
                output.extend(f"<th>{inline_markdown(cell)}</th>" for cell in cells)
                output.append("</tr></thead><tbody>")
            else:
                output.append("<tr>")
                output.extend(f"<td>{inline_markdown(cell)}</td>" for cell in cells)
                output.append("</tr>")
            continue
        if output and output[-1] == "</tr>":
            output.append("</tbody></table>")
        paragraph.append(line.strip())
    flush_paragraph()
    close_list()
    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
    if output and output[-1] == "</tr>":
        output.append("</tbody></table>")
    return "\n".join(output)


def load_curriculum() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from src.education.tutor import TOPIC_CATALOG

    courses = json.loads((ROOT / "docs/learning/tutor-courses.json").read_text())
    topics: dict[str, Any] = {}
    shared_guides = {
        "Mastery skill": ROOT / "docs/learning/MASTERY_SKILL.md",
        "Course guide": ROOT / "docs/learning/TUTOR_COURSE_GUIDE.md",
        "Depth path": ROOT / "docs/learning/DEPTH_PATH.md",
    }
    fingerprint_parts: list[str] = []
    for topic_id, source in TOPIC_CATALOG.items():
        deep_dive_path = ROOT / source["deep_dive"]
        quiz_path = ROOT / source["quiz_file"]
        deep_dive = deep_dive_path.read_text()
        quiz = [json.loads(line) for line in quiz_path.read_text().splitlines() if line]
        topics[topic_id] = {
            **source,
            "course": courses[topic_id],
            "deep_dive_html": render_markdown(deep_dive),
            "quiz": quiz,
        }
        fingerprint_parts.extend((deep_dive, quiz_path.read_text()))
    fingerprint_parts.append(json.dumps(courses, sort_keys=True))
    shared_html = {}
    for title, path in shared_guides.items():
        content = path.read_text()
        shared_html[title] = render_markdown(content)
        fingerprint_parts.append(content)
    fingerprint = hashlib.sha256("\n".join(fingerprint_parts).encode()).hexdigest()[:12]
    return (
        TOPIC_CATALOG,
        topics,
        {"fingerprint": fingerprint, "shared_html": shared_html},
    )


def build_html() -> str:
    catalog, topics, metadata = load_curriculum()
    cards = "\n".join(
        f'<a class="topic-card" href="#{topic_id}"><span>{index:02}</span>'
        f"<strong>{html.escape(source['label'])}</strong></a>"
        for index, (topic_id, source) in enumerate(catalog.items(), start=1)
    )
    sections = []
    quiz_data: dict[str, list[dict[str, Any]]] = {}
    for topic_id, topic in topics.items():
        course = topic["course"]
        quiz_data[topic_id] = topic["quiz"]
        sections.append(
            f"""<section id="{topic_id}" class="topic">
<p class="eyebrow">Course {list(catalog).index(topic_id) + 1:02}</p>
<h2>{html.escape(topic["label"])}</h2>
<p class="source">Source: <code>{html.escape(topic["deep_dive"])}</code> · {len(topic["quiz"])} quiz questions</p>
<div class="course-grid">
<div><h3>Prerequisites</h3><ul>{"".join(f"<li>{inline_markdown(item)}</li>" for item in course["prerequisites"])}</ul></div>
<div><h3>Objectives</h3><ul>{"".join(f"<li>{inline_markdown(item)}</li>" for item in course["objectives"])}</ul></div>
</div>
<h3>Lessons</h3><ol>{"".join(f"<li>{inline_markdown(item)}</li>" for item in course["lessons"])}</ol>
<div class="labs"><p><strong>Local lab:</strong> {inline_markdown(course["local_lab"])}</p>
<p><strong>Failure lab:</strong> {inline_markdown(course["failure_lab"])}</p>
<p><strong>Teach-back:</strong> {inline_markdown(course["assessment"])}</p></div>
<details><summary>Read the deep dive</summary><article>{topic["deep_dive_html"]}</article></details>
<button class="quiz-button" data-topic="{topic_id}">Start this topic's quiz</button>
</section>"""
        )
    quiz_json = json.dumps(quiz_data).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Agentic PM Lab Learning Curriculum</title>
<style>
:root{{color-scheme:light dark;--ink:#18212f;--muted:#536174;--accent:#13599a;--card:#fff;--line:#d8e0ea;--soft:#eef5fc}}
*{{box-sizing:border-box}} body{{margin:0;font:16px/1.58 system-ui,-apple-system,sans-serif;color:var(--ink);background:#f7fafc}}
a{{color:var(--accent)}}header{{background:#0e263e;color:#fff;padding:4rem max(1.5rem,calc((100% - 1120px)/2)) 3rem}}header p{{max-width:850px;font-size:1.12rem}}
main{{max-width:1120px;margin:auto;padding:2rem 1.5rem 5rem}}h1{{font-size:clamp(2rem,5vw,3.8rem);line-height:1.05;margin:.4rem 0 1rem}}h2{{font-size:1.8rem;line-height:1.2}}h3{{margin-bottom:.25rem}}.eyebrow,.source{{color:var(--muted);font-size:.9rem}}.notice,.labs{{background:var(--soft);border-left:4px solid var(--accent);padding:1rem 1.2rem;margin:1.5rem 0}}.topic-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:.7rem}}.topic-card{{background:var(--card);border:1px solid var(--line);border-radius:.5rem;padding:1rem;text-decoration:none;color:var(--ink)}}.topic-card span{{color:var(--accent);font:700 .8rem ui-monospace,monospace;display:block}}.topic{{background:var(--card);border:1px solid var(--line);border-radius:.75rem;padding:1.5rem;margin:1.5rem 0;scroll-margin-top:1rem}}.course-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}}details{{border-top:1px solid var(--line);margin-top:1.25rem;padding-top:1rem}}summary{{cursor:pointer;font-weight:700}}article{{max-width:82ch}}pre{{overflow:auto;background:#172331;color:#f1f5f9;padding:1rem;border-radius:.4rem}}code{{font:.9em ui-monospace,SFMono-Regular,monospace}}table{{border-collapse:collapse;width:100%;overflow-x:auto;display:block}}td,th{{border:1px solid var(--line);padding:.55rem;text-align:left}}button{{background:var(--accent);border:0;border-radius:.35rem;color:#fff;padding:.7rem 1rem;font-weight:700;cursor:pointer}}dialog{{max-width:min(760px,94vw);border:0;border-radius:.8rem;box-shadow:0 10px 50px #0008;padding:1.5rem}}dialog::backdrop{{background:#0008}}.choice{{display:block;width:100%;margin:.5rem 0;text-align:left;background:var(--soft);color:var(--ink)}}.result{{font-weight:700}}footer{{color:var(--muted);font-size:.9rem;margin-top:3rem}}@media(prefers-color-scheme:dark){{:root{{--ink:#e8edf3;--muted:#adbac8;--accent:#73b7f5;--card:#18212b;--line:#3b4b5d;--soft:#233548}}body{{background:#101720}}}}
</style></head><body>
<header><p class="eyebrow">SELF-CONTAINED, OFFLINE LEARNING ARTIFACT</p><h1>Agentic PM Lab<br>Learning Curriculum</h1>
<p>Fourteen source-grounded courses for building and governing fixed-income-first PM AI workflows. Learn with the deep dives, local and failure labs, quizzes, teach-backs, and integrated assessment—without downloading the repository.</p>
</header><main>
<div class="notice"><strong>Learning boundary:</strong> this is public/mock learning material, not investment advice, a trading system, or evidence of production readiness. Course content is generated from the repository’s canonical learning sources. Curriculum fingerprint: <code>{metadata["fingerprint"]}</code>.</div>
<h2>Start a path</h2><ol><li><strong>PM foundations:</strong> FICC, portfolio construction, public data, provenance.</li><li><strong>Governed agent builder:</strong> architecture, Deep Agents, governance, evaluation, OpenTelemetry.</li><li><strong>Platform integrator:</strong> AgentCore, Canvas/MCP, lifecycle, document-to-skill, committee challenge.</li></ol>
<p>For an interactive CLI guide, open the repository in Copilot, Claude Code, or Codex and say <code>pmexpert</code>. For durable offline quiz records, use <code>scripts/tutor.py</code> after cloning.</p>
<details><summary>How to use this curriculum</summary><article>{metadata["shared_html"]["Course guide"]}</article></details>
<details><summary>Mastery-skill guide</summary><article>{metadata["shared_html"]["Mastery skill"]}</article></details>
<details><summary>Depth path</summary><article>{metadata["shared_html"]["Depth path"]}</article></details>
<h2>Courses</h2><nav class="topic-grid">{cards}</nav>
{"".join(sections)}
<footer>Generated by <code>scripts/build_learning_curriculum.py</code> from the checked-in curriculum sources. External framework behavior should be checked against the official references maintained in the repository.</footer>
</main><dialog id="quiz"><button id="close">Close</button><div id="quiz-body"></div></dialog>
<script>
const quizzes={quiz_json}; const dialog=document.querySelector('#quiz'), body=document.querySelector('#quiz-body');
let questions=[], position=0, correct=0;
document.querySelectorAll('.quiz-button').forEach(button=>button.onclick=()=>{{questions=quizzes[button.dataset.topic];position=0;correct=0;render();dialog.showModal();}});
document.querySelector('#close').onclick=()=>dialog.close();
function render(){{if(position===questions.length){{body.innerHTML=`<h2>Quiz complete</h2><p class="result">Score: ${{correct}} / ${{questions.length}} (${{Math.round(correct/questions.length*100)}}%)</p><p>Review the cited sources and repeat the local/failure labs before treating a score as course completion.</p>`;return;}}const q=questions[position];body.innerHTML=`<p class="eyebrow">Question ${{position+1}} of ${{questions.length}}</p><h2>${{q.question}}</h2>${{q.choices.map((choice,index)=>`<button class="choice" data-index="${{index}}">${{String.fromCharCode(65+index)}}. ${{choice}}</button>`).join('')}}<p id="feedback"></p>`;body.querySelectorAll('.choice').forEach(button=>button.onclick=()=>answer(Number(button.dataset.index),q));}}
function answer(answer,q){{const ok=answer===q.correct_index;if(ok)correct++;body.querySelector('#feedback').innerHTML=`<span class="result">${{ok?'Correct.':'Not quite.'}}</span> Source: <code>${{q.citation}}</code>. <button id="next">Continue</button>`;body.querySelectorAll('.choice').forEach(button=>button.disabled=true);body.querySelector('#next').onclick=()=>{{position++;render();}};}}
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
