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
