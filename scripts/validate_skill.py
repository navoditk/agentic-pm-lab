"""Validate a skill package's shape and static contract consistency."""

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml

REQUIRED_FRONTMATTER = {
    "name",
    "description",
    "license",
    "covers",
    "last_verified_commit",
}
REQUIRED_CONTRACT_FIELDS = {
    "inputs",
    "allowed_tools",
    "forbidden_tools",
    "output_schema",
    "side_effects",
    "approval_required",
    "covers",
    "version",
}


def load_frontmatter(skill_path: Path) -> dict[str, Any]:
    """Parse YAML frontmatter from a SKILL.md file."""
    text = skill_path.read_text()
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must start with YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError("SKILL.md frontmatter is not closed")
    metadata = yaml.safe_load(parts[1])
    if not isinstance(metadata, dict):
        raise TypeError("SKILL.md frontmatter must be a mapping")
    return metadata


def validate_skill(skill_dir: Path) -> list[str]:
    """Return static validation errors for one skill package."""
    errors: list[str] = []
    skill_path = skill_dir / "SKILL.md"
    contract_path = skill_dir / "contract.yaml"
    if not skill_path.is_file():
        errors.append("missing SKILL.md")
    if not contract_path.is_file():
        errors.append("missing contract.yaml")
    if errors:
        return errors

    try:
        metadata = load_frontmatter(skill_path)
    except (OSError, TypeError, UnicodeError, yaml.YAMLError, ValueError) as error:
        return [str(error)]
    missing_metadata = REQUIRED_FRONTMATTER - set(metadata)
    if missing_metadata:
        errors.append(f"frontmatter missing: {', '.join(sorted(missing_metadata))}")

    try:
        contract = yaml.safe_load(contract_path.read_text())
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        return [f"invalid contract.yaml: {error}"]
    if not isinstance(contract, dict):
        return ["contract.yaml must be a mapping"]
    missing_contract = REQUIRED_CONTRACT_FIELDS - set(contract)
    if missing_contract:
        errors.append(f"contract missing: {', '.join(sorted(missing_contract))}")
    if metadata.get("covers") != contract.get("covers"):
        errors.append("SKILL.md and contract.yaml covers must match")
    if not (skill_dir / "examples").is_dir():
        errors.append("missing examples directory")
    if not (skill_dir / "tests" / "test_skill.py").is_file():
        errors.append("missing tests/test_skill.py")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill_dir", type=Path)
    args = parser.parse_args()
    errors = validate_skill(args.skill_dir)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"{args.skill_dir}: valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
