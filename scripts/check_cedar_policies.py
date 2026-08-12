"""Parse every version-controlled Cedar policy and fail on invalid syntax."""

import sys
from pathlib import Path

from cedarpy import PolicySet

REPO_ROOT = Path(__file__).resolve().parents[1]
POLICIES_DIR = REPO_ROOT / "governance" / "policies"


def validate_policy(path: Path) -> str | None:
    """Return a syntax error for one policy, or None when it parses."""
    try:
        PolicySet.from_str(path.read_text())
    except ValueError as error:
        return str(error)
    return None


def main() -> int:
    failed = False
    for path in sorted(POLICIES_DIR.glob("*.cedar")):
        error = validate_policy(path)
        if error is not None:
            failed = True
            print(f"{path.relative_to(REPO_ROOT)}: {error}")
    if failed:
        return 1
    print("All Cedar policies are syntactically valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
