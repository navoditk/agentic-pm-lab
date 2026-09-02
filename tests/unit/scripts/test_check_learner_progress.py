import json

from scripts.check_learner_progress import build_table, update_learner_progress_md

MARKERS = """# Learner progress

<!-- LEARNER_PROGRESS:START -->
placeholder
<!-- LEARNER_PROGRESS:END -->
"""


def _write_attempts(log_dir, topic, *scores_totals):
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / f"{topic}.jsonl"
    with path.open("w") as handle:
        for score, total in scores_totals:
            handle.write(
                json.dumps({"topic": topic, "score": score, "total": total}) + "\n"
            )


def test_build_table_marks_not_attempted_when_no_log_exists(tmp_path):
    table = build_table(["some-topic"], tmp_path)
    assert "| some-topic | 0 | - | ⬜ Not attempted |" in table


def test_build_table_marks_passed_at_or_above_threshold(tmp_path):
    _write_attempts(tmp_path, "topic-a", (3, 5), (4, 5))
    table = build_table(["topic-a"], tmp_path)
    assert "| topic-a | 2 | 4/5 | ✅ Passed |" in table


def test_build_table_marks_attempted_below_threshold(tmp_path):
    _write_attempts(tmp_path, "topic-b", (2, 5))
    table = build_table(["topic-b"], tmp_path)
    assert "| topic-b | 1 | 2/5 | 🟡 Attempted |" in table


def test_update_learner_progress_md_writes_between_markers(tmp_path):
    log_dir = tmp_path / "logs"
    _write_attempts(log_dir, "topic-a", (5, 5))
    md_path = tmp_path / "LEARNER_PROGRESS.md"
    md_path.write_text(MARKERS)

    update_learner_progress_md(["topic-a"], log_dir=log_dir, md_path=md_path)

    updated = md_path.read_text()
    assert "1 of 1 tutor topics passed" in updated
    assert "topic-a | 1 | 5/5 | ✅ Passed" in updated
    assert "placeholder" not in updated
