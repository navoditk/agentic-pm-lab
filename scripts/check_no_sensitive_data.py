"""Pre-commit hook: reject a commit containing any banned term.

Reinforces docs/PRD.md §3 principle 3 (public/mock data only, no company-sensitive
terminology) at commit time rather than only at review time. Banned terms
live in config/security/banned-terms.txt, one per line, case-insensitive.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BANNED_TERMS_PATH = REPO_ROOT / "config/security/banned-terms.txt"


def load_banned_terms(path: Path = BANNED_TERMS_PATH) -> list[str]:
    if not path.exists():
        return []
    terms = []
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            terms.append(stripped.lower())
    return terms


def scan_file(path: Path, banned_terms: list[str]) -> list[str]:
    try:
        text = path.read_text(errors="ignore")
    except (OSError, UnicodeDecodeError):
        return []
    lower_text = text.lower()
    return [term for term in banned_terms if term in lower_text]


def main(argv: list[str]) -> int:
    banned_terms = load_banned_terms()
    if not banned_terms:
        return 0

    found_any = False
    for filename in argv:
        path = Path(filename)
        if path.name == BANNED_TERMS_PATH.name:
            continue
        matches = scan_file(path, banned_terms)
        if matches:
            found_any = True
            print(f"{path}: contains banned term(s): {', '.join(matches)}")

    if found_any:
        print(
            "Commit blocked -- remove the banned term(s) above (docs/PRD.md §3, principle 3)."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
