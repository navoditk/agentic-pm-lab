from pathlib import Path

import yaml

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_scenario_analysis_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_day5_contract_cannot_execute_scenarios():
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())

    assert contract["allowed_tools"] == []
    assert contract["version"] == "0.1.0"
    assert contract["side_effects"] == "none"


def test_skill_prohibits_invented_scenario_results():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()

    assert "Do not estimate or narrate a numeric impact" in skill_text
    assert "Day 12 deterministic" in skill_text
