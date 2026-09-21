from pathlib import Path

import yaml

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]
ROOT = SKILL_DIR.parents[1]


def test_agentic_pm_mastery_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_skill_is_tool_neutral_and_preserves_offline_learning():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()

    assert "CLI's structured question/choice tool" in skill_text
    assert "Otherwise, retain progress in the active conversation" in skill_text
    # The documented entry point, not the module behind it. This asserts the
    # exact string a learner is told to type, so the skill cannot drift from
    # the CLI the rest of the documentation now routes through.
    assert "agentic-pm-lab quiz <topic-id>" in skill_text


def test_contract_prohibits_live_and_investment_actions():
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())

    assert contract["side_effects"] == "none"
    assert {"investment_advice", "order_execution", "live_provider_invocation"} <= set(
        contract["forbidden_tools"]
    )


def test_all_cli_loaders_reference_the_canonical_skill():
    loader_paths = (
        ROOT / ".github/skills/agentic-pm-mastery/SKILL.md",
        ROOT / ".claude/skills/agentic-pm-mastery/SKILL.md",
        ROOT / ".agents/skills/agentic-pm-mastery/SKILL.md",
    )

    for loader in loader_paths:
        assert loader.is_file()
        assert "skills/agentic-pm-mastery/SKILL.md" in loader.read_text()
