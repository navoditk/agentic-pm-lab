"""Check whether changed implementation paths have matching skill updates."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from scripts.validate_skill import load_frontmatter
except ModuleNotFoundError:  # direct ``python scripts/...`` execution
    from validate_skill import load_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[1]


def changed_paths(base: str, head: str) -> set[str]:
    """Return repository paths changed between two revisions."""
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {line for line in result.stdout.splitlines() if line}


def _covered(path: str, covered_paths: list[str]) -> bool:
    return any(
        path == covered or path.startswith(f"{covered.rstrip('/')}/")
        for covered in covered_paths
    )


def audit_skills(
    skills_root: Path,
    changed: set[str],
    *,
    require_existing_commit: bool = False,
) -> list[str]:
    """Return stale-skill errors for a changed-file set."""
    errors: list[str] = []
    for skill_path in sorted(skills_root.glob("*/SKILL.md")):
        metadata: dict[str, Any] = load_frontmatter(skill_path)
        covers = metadata.get("covers") or []
        if not isinstance(covers, list) or not all(
            isinstance(item, str) for item in covers
        ):
            errors.append(f"{skill_path}: covers must be a list of paths")
            continue
        affected = sorted(path for path in changed if _covered(path, covers))
        if not affected:
            continue
        skill_relative = skill_path.relative_to(skills_root.parent).as_posix()
        if skill_relative not in changed:
            errors.append(
                f"{skill_path}: stale for changed paths {', '.join(affected)}; update SKILL.md/contract or justify with skills-unaffected"
            )
        if require_existing_commit:
            commit = metadata.get("last_verified_commit")
            result = subprocess.run(
                ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
                cwd=REPO_ROOT,
                capture_output=True,
                check=False,
            )
            if not commit or result.returncode != 0:
                errors.append(
                    f"{skill_path}: last_verified_commit is not a repository commit"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD~1")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--skills-root", type=Path, default=REPO_ROOT / "skills")
    args = parser.parse_args()
    errors = audit_skills(
        args.skills_root,
        changed_paths(args.base, args.head),
        require_existing_commit=True,
    )
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        print(
            "Use a synchronized skill update or document a skills-unaffected justification."
        )
        return 1
    print("Skills freshness check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
