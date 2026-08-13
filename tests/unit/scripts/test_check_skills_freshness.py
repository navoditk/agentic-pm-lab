from pathlib import Path

from scripts.check_skills_freshness import audit_skills


def _skill(
    tmp_path: Path, name: str, covers: list[str], commit: str = "abc123"
) -> Path:
    skill_dir = tmp_path / name
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: test\nlicense: MIT\n"
        f"covers: {covers}\nlast_verified_commit: {commit}\n---\n\n# test\n"
    )
    return skill_dir


def test_freshness_passes_when_covered_code_did_not_change(tmp_path: Path) -> None:
    root = tmp_path / "skills"
    root.mkdir()
    _skill(root, "safe", ["src/analytics"])
    assert audit_skills(root, {"README.md"}) == []


def test_freshness_fails_when_covered_code_changes_without_skill_update(
    tmp_path: Path,
) -> None:
    root = tmp_path / "skills"
    root.mkdir()
    skill = _skill(root, "stale", ["src/analytics"])
    errors = audit_skills(root, {"src/analytics/risk.py"})
    assert errors
    assert str(skill / "SKILL.md") in errors[0]


def test_freshness_passes_when_skill_and_covered_code_change_together(
    tmp_path: Path,
) -> None:
    root = tmp_path / "skills"
    root.mkdir()
    skill = _skill(root, "updated", ["src/analytics"])
    changed = {"src/analytics/risk.py", str(skill.relative_to(tmp_path)) + "/SKILL.md"}
    assert audit_skills(root, changed) == []
