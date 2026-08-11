from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_contract_covers_match_skill_frontmatter():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()
    _, frontmatter, _ = skill_text.split("---", 2)
    skill_metadata = yaml.safe_load(frontmatter)
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())

    assert contract["covers"] == skill_metadata["covers"]


def test_checklist_requires_contract_and_authorization_tests():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()

    assert "contracts/tools/<function>.schema.json" in skill_text
    assert "allowed and denied authorization tests" in skill_text
