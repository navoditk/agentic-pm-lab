from pathlib import Path

from scripts.build_learning_curriculum import DEFAULT_OUTPUT, build_html, write_output


def test_curriculum_includes_every_topic_and_quiz():
    rendered = build_html()

    assert "Agentic PM Lab Learning Curriculum" in rendered
    assert rendered.count("Start this topic's quiz") == 14
    assert "portfolio-construction-tutor-q1" in rendered
    assert "ficc-tutor-agent-q1" in rendered


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
