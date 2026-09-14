from datetime import date

from scripts.check_curriculum_sources import REGISTRY_PATH, check


def test_source_registry_is_complete_and_current():
    assert check(today=date(2026, 9, 13)) == []


def test_source_registry_rejects_unknown_topic(tmp_path):
    registry = REGISTRY_PATH.read_text().replace(
        "topic: agent-architecture-tutor", "topic: not-a-tutor", 1
    )
    path = tmp_path / "registry.yaml"
    path.write_text(registry)

    assert any(
        "unknown topic" in error for error in check(path, today=date(2026, 9, 13))
    )


def test_source_registry_rejects_overdue_review(tmp_path):
    registry = REGISTRY_PATH.read_text().replace(
        "last_reviewed: 2026-09-02", "last_reviewed: 2020-01-01", 1
    )
    path = tmp_path / "registry.yaml"
    path.write_text(registry)

    assert any(
        "review is overdue" in error for error in check(path, today=date(2026, 9, 13))
    )


def test_source_registry_requires_all_topic_assets(tmp_path):
    registry = REGISTRY_PATH.read_text().replace(
        ", evals/tutor_quizzes/agent-architecture-tutor.jsonl]", "]", 1
    )
    path = tmp_path / "registry.yaml"
    path.write_text(registry)

    assert any("deep dive, persona, and quiz bank" in error for error in check(path))
