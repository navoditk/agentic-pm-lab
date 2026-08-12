from pathlib import Path

import yaml

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_control_layer_role_change_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_contract_and_frontmatter_cover_same_authorities():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()
    _, frontmatter, _ = skill_text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())

    assert contract["covers"] == metadata["covers"]


def test_checklist_preserves_cedar_as_permission_authority():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()

    assert "Never put an `allowed_tools` list in `config/roles.yaml`" in skill_text
    assert "allowed and denied case" in skill_text
    assert "Tool Layer boundary re-check" in skill_text
