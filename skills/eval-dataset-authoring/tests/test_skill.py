import json
from pathlib import Path

import yaml

from scripts.run_eval import load_jsonl, validate_case
from scripts.validate_skill import validate_skill

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[1]


def test_eval_dataset_authoring_package_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_contract_covers_dataset_and_runner():
    contract = yaml.safe_load((SKILL_DIR / "contract.yaml").read_text())

    assert contract["covers"] == ["evals", "scripts/run_eval.py"]
    assert contract["side_effects"].startswith("Writes version-controlled")


def test_every_golden_case_has_the_required_shape():
    for case in load_jsonl(REPO_ROOT / "evals" / "golden_dataset.jsonl"):
        assert validate_case(case) == []


def test_example_is_valid_json():
    example = json.loads((SKILL_DIR / "examples" / "golden_case.json").read_text())
    assert example["domain"] == "quant"
