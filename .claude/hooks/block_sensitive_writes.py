#!/usr/bin/env python3
"""PreToolUse hook: refuse to write a banned term into a file.

The repo's first rule -- public and mock data only, no company-sensitive
terminology -- was enforced only by the pre-commit hook, which fires long
after the agent wrote the content. Claude Code's own documentation is explicit
that instructions in `AGENTS.md`/`CLAUDE.md` are context rather than enforced
configuration, and that blocking an action regardless of what the model
decides is what a `PreToolUse` hook is for.

This is the fast-feedback layer, not the authority: `scripts/check_no_sensitive
_data.py` still runs at commit time and remains the portable floor for Codex,
Copilot and CI, none of which read Claude Code hooks. Both read the same
`config/security/banned-terms.txt`, so there is one list, not two.

Contract: stdin carries the PreToolUse JSON; `permissionDecision: "deny"` on
stdout blocks the call. Exit 0 always -- a hook that crashes must not become
the reason a legitimate edit is impossible, so anything unexpected falls
through to the normal permission flow and lets pre-commit catch it.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

# The text-carrying fields of the tools that can introduce content. Read into
# a tuple per tool rather than scanning every value, so a path that happens to
# contain a banned substring is not mistaken for banned content.
CONTENT_FIELDS = {
    "Write": ("content",),
    "Edit": ("new_string",),
    "NotebookEdit": ("new_source",),
}


def deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        # Valid JSON of the wrong shape -- `[]` parses fine and then blows up
        # on `.get`. Checked rather than caught so the failure path stays the
        # same quiet fall-through as every other unexpected input.
        return 0

    fields = CONTENT_FIELDS.get(payload.get("tool_name", ""))
    if not fields:
        return 0

    tool_input = payload.get("tool_input") or {}
    candidate = "\n".join(str(tool_input.get(field, "")) for field in fields).lower()
    if not candidate.strip():
        return 0

    # Editing the banned-terms list itself must stay possible.
    target = str(tool_input.get("file_path", ""))
    if target.endswith("banned-terms.txt"):
        return 0

    try:
        from scripts.check_no_sensitive_data import load_banned_terms

        terms = load_banned_terms()
    except Exception:  # noqa: BLE001 - never block on our own failure
        return 0

    hits = sorted({term for term in terms if term in candidate})
    if hits:
        deny(
            f"Blocked: this write contains banned term(s): {', '.join(hits)}. "
            "The repository is public and mock data only "
            "(docs/architecture/PRD.md §3, principle 3). Remove the term, or "
            "use a mock identifier instead."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
