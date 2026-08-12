from pathlib import Path

import yaml

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_canvas_capability_authoring_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_contract_and_frontmatter_cover_canvas_and_tests():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()
    _, frontmatter, _ = skill_text.split("---", 2)
    metadata = yaml.safe_load(frontmatter)
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())

    assert contract["covers"] == metadata["covers"]


def test_skill_requires_shared_handlers_and_governed_backends():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()

    assert "same handler" in skill_text
    assert "governed Tool/MCP interface" in skill_text
    assert "Render with Preact" in skill_text
    assert "`innerHTML`" in skill_text
    assert "opened and inspected in the GitHub Copilot app" in skill_text
