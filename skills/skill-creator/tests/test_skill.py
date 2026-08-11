from pathlib import Path

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_skill_creator_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_creator_warns_contract_is_not_authorization():
    assert "not an authorization control" in (SKILL_DIR / "SKILL.md").read_text()
