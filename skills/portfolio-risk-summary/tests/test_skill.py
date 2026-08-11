from pathlib import Path

import yaml

from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]


def test_portfolio_risk_summary_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_contract_allows_exactly_three_read_only_tools():
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())

    assert contract["allowed_tools"] == [
        "get_portfolio_exposure",
        "get_volatility",
        "get_max_drawdown",
    ]
    assert contract["side_effects"] == "none"


def test_skill_requires_mock_data_disclosure():
    skill_text = (SKILL_DIR / "SKILL.md").read_text()

    assert "classification is mocked" in skill_text
