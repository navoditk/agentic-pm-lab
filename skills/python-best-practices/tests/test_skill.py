"""Schema/lint stage of §8.3's pipeline, run against python-best-practices."""

from pathlib import Path

import yaml

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_skill_md_has_required_frontmatter():
    content = (SKILL_DIR / "SKILL.md").read_text()
    frontmatter = content.split("---")[1]
    data = yaml.safe_load(frontmatter)
    for field in ("name", "description", "license", "covers", "last_verified_commit"):
        assert field in data


def test_contract_yaml_is_well_formed():
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())
    assert contract["allowed_tools"] == []
    assert contract["side_effects"] == "none"
    assert contract["covers"] == [".pre-commit-config.yaml", "pyproject.toml"]
