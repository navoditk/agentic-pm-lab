from pathlib import Path

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_skill_tester_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_tester_forbids_live_model_calls():
    assert "must not call a live network" in (SKILL_DIR / "SKILL.md").read_text()
