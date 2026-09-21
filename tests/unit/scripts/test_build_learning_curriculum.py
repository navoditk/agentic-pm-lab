import re
from datetime import date
from pathlib import Path

from scripts.build_learning_curriculum import (
    DEFAULT_OUTPUT,
    build_html,
    topic_freshness,
    write_output,
)


def test_curriculum_includes_every_topic_and_quiz():
    rendered = build_html()

    assert "Agentic PM Lab Learning Curriculum" in rendered
    assert rendered.count("Start this topic's quiz") == 14
    assert "portfolio-construction-tutor-q1" in rendered
    assert "ficc-tutor-agent-q1" in rendered
    assert "Browser quiz results stay in this browser" in rendered


def test_curriculum_rewrites_checkout_relative_links_to_github():
    rendered = build_html()
    links = re.findall(r'href="([^"]+)"', rendered)

    assert links
    assert all(link.startswith(("https://", "#", "mailto:")) for link in links)
    assert (
        "https://github.com/navoditk/agentic-pm-lab/blob/main/"
        "docs/reference/REFERENCES.md"
    ) in rendered


def test_generated_curriculum_artifact_is_current():
    assert (
        DEFAULT_OUTPUT
        == Path(__file__).resolve().parents[3] / "artifacts/agentic-pm-curriculum.html"
    )
    assert write_output(output=DEFAULT_OUTPUT, check=True) == 0


def test_compiler_supports_a_relative_pages_output(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert write_output(output=Path("_site/index.html"), check=False) == 0
    assert (tmp_path / "_site/index.html").is_file()


def test_topic_freshness_marks_missing_monitor_enrollment():
    catalog = {
        "topic": {
            "deep_dive": "docs/topic.md",
            "agent_file": ".github/agents/topic.md",
            "quiz_file": "evals/topic.jsonl",
        }
    }
    registry = {
        "sources": [
            {
                "title": "Reviewed source",
                "url": "https://example.com/reviewed",
                "last_reviewed": date(2026, 9, 14),
                "review_after_days": 90,
                "monitor_baseline": "v1",
                "impacts": [{"topic": "topic"}],
            },
            {
                "title": "Pending source",
                "url": "https://example.com/pending",
                "last_reviewed": date(2026, 9, 14),
                "review_after_days": 90,
                "impacts": [{"topic": "topic"}],
            },
        ]
    }

    result = topic_freshness(catalog, registry)

    assert result["topic"]["status"] == "enrollment-pending"
    assert result["topic"]["sources"][0]["next_review"] == "2026-12-13"


# --- the published artifact is the product for readers who cannot clone ------
#
# This page is the only way into the material for someone in an environment
# where cloning is not allowed, so a citation it cannot open is a dead end
# rather than a cosmetic flaw.


def test_repository_paths_in_prose_become_links():
    from scripts.build_learning_curriculum import linkify_repository_paths

    out = linkify_repository_paths("<p>See <code>src/analytics/risk.py</code>.</p>")
    assert 'class="src"' in out
    assert "blob/main/src/analytics/risk.py" in out


def test_a_path_that_does_not_exist_is_left_alone():
    """Linking a renamed path would produce a confident 404."""
    from scripts.build_learning_curriculum import linkify_repository_paths

    out = linkify_repository_paths("<p><code>src/not_a_real_module.py</code></p>")
    assert "<a" not in out


def test_a_path_already_inside_a_link_is_not_wrapped_twice():
    """Nested anchors render unpredictably and break keyboard navigation."""
    from scripts.build_learning_curriculum import linkify_repository_paths

    already = '<p><a href="https://x/y"><code>src/analytics/risk.py</code></a></p>'
    assert linkify_repository_paths(already) == already


def test_indented_code_fences_render_as_code_not_paragraphs():
    """A fence inside a numbered list is indented; matching at column zero
    left fourteen blocks rendering as literal backticks in a paragraph."""
    from scripts.build_learning_curriculum import render_markdown

    out = render_markdown("1. Run it:\n\n   ```python\n   x = 1\n   ```\n")
    assert "<pre><code>" in out
    assert "```" not in out


def test_every_generated_repository_link_points_at_a_file_that_exists():
    """Checked against the built artifact, not the renderer, so a path
    emitted by any code path -- not just the linkifier -- is covered."""
    import re
    from pathlib import Path

    from scripts.build_learning_curriculum import DEFAULT_OUTPUT

    html_text = DEFAULT_OUTPUT.read_text(encoding="utf-8")
    root = Path(__file__).resolve().parents[3]
    targets = re.findall(
        r'href="https://github\.com/navoditk/agentic-pm-lab/(?:blob|tree)/main/([^"#]+)',
        html_text,
    )
    assert targets, "the artifact should cite repository files"
    # The quiz builds its citation link client-side, so one href carries a
    # `${...}` template expression rather than a path. It resolves at runtime
    # from the same quiz data these tests already check elsewhere.
    static = {t for t in targets if "${" not in t}
    assert static, "every repository link was a template expression"
    missing = sorted({t for t in static if not (root / t).exists()})
    assert not missing, f"artifact links to missing files: {missing}"


def test_the_artifact_has_no_unrendered_code_fences():
    from scripts.build_learning_curriculum import DEFAULT_OUTPUT

    assert "<p>```" not in DEFAULT_OUTPUT.read_text(encoding="utf-8")
