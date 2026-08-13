"""Run deterministic static checks across every repository skill package."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

try:
    from scripts.validate_skill import validate_skill
except ModuleNotFoundError:  # direct ``python scripts/...`` execution
    from validate_skill import validate_skill

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
POLICY_PATH = REPO_ROOT / "governance" / "policies" / "tool-permissions.cedar"


def check_skill(skill_dir: Path, policy_text: str) -> list[str]:
    errors = [f"{skill_dir}: {error}" for error in validate_skill(skill_dir)]
    contract_path = skill_dir / "contract.yaml"
    if not contract_path.is_file():
        return errors
    contract = yaml.safe_load(contract_path.read_text()) or {}
    governed_tools = set(re.findall(r'Tool::"([^"]+)"', policy_text))
    for tool in contract.get("allowed_tools") or []:
        # Meta-skills describe editor/shell capabilities, not runtime Tool
        # Layer capabilities governed by Cedar.
        if tool not in governed_tools and not any(
            cover == "skills" or cover.startswith("scripts")
            for cover in (contract.get("covers") or [])
        ):
            errors.append(
                f"{skill_dir}: allowed tool is absent from Cedar policy: {tool}"
            )
    forbidden = set(contract.get("forbidden_tools") or [])
    allowed = set(contract.get("allowed_tools") or [])
    overlap = sorted(allowed & forbidden)
    if overlap:
        errors.append(
            f"{skill_dir}: tool is both allowed and forbidden: {', '.join(overlap)}"
        )
    output_schema = contract.get("output_schema")
    if isinstance(output_schema, str) and output_schema:
        schema_path = REPO_ROOT / str(output_schema)
        if not schema_path.is_file():
            errors.append(f"{skill_dir}: output_schema does not exist: {output_schema}")
        else:
            try:
                json.loads(schema_path.read_text())
            except json.JSONDecodeError as error:
                errors.append(f"{skill_dir}: output_schema is invalid JSON: {error}")
    if not list((skill_dir / "examples").glob("*.json")):
        errors.append(f"{skill_dir}: examples directory has no JSON examples")
    return errors


def main() -> int:
    policy_text = POLICY_PATH.read_text()
    errors = [
        error
        for skill_dir in sorted(SKILLS_ROOT.iterdir())
        if skill_dir.is_dir()
        for error in check_skill(skill_dir, policy_text)
    ]
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print(
        f"Static skill contract check passed for {len(list(SKILLS_ROOT.glob('*/SKILL.md')))} skills."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
