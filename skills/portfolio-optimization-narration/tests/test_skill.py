from pathlib import Path

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_package_is_valid() -> None:
    assert validate_skill(SKILL_DIR) == []


def test_skill_requires_approval_and_disallows_orders() -> None:
    contract = (SKILL_DIR / "contract.yaml").read_text()
    skill = (SKILL_DIR / "SKILL.md").read_text()
    assert "approval_required: true" in contract
    assert "Never" in skill and "orders" in skill
