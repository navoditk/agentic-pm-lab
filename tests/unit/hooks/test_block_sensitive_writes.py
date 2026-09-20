"""The PreToolUse hook, tested through its real stdin/stdout contract.

Driven as a subprocess with actual JSON payloads rather than by importing and
calling `main()`, because the contract *is* the interface: a hook that returns
the right value but prints the wrong shape, or exits non-zero, fails silently
in a way an in-process test would not catch.

The two behaviours that matter in opposite directions are both pinned here --
it must block a banned term, and it must never block anything else, including
when it fails. A hook that over-blocks is worse than no hook, because it makes
legitimate edits impossible with no obvious cause.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / ".claude/hooks/block_sensitive_writes.py"


def run_hook(payload: object) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload if isinstance(payload, str) else json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    return result.returncode, result.stdout


def banned_term() -> str:
    sys.path.insert(0, str(REPO_ROOT))
    from scripts.check_no_sensitive_data import load_banned_terms

    terms = load_banned_terms()
    if not terms:
        pytest.skip("no banned terms configured")
    return terms[0]


def decision(stdout: str) -> str | None:
    if not stdout.strip():
        return None
    return json.loads(stdout)["hookSpecificOutput"]["permissionDecision"]


def test_a_write_carrying_a_banned_term_is_denied():
    code, out = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "notes.md", "content": f"x {banned_term()} y"},
        }
    )
    assert code == 0, "the hook signals its decision in JSON, not via exit status"
    assert decision(out) == "deny"


def test_an_edit_carrying_a_banned_term_is_denied():
    code, out = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Edit",
            "tool_input": {"file_path": "notes.md", "new_string": banned_term()},
        }
    )
    assert code == 0
    assert decision(out) == "deny"


def test_the_reason_names_the_term_and_the_rule():
    """A block the author cannot act on is a block they will work around."""
    _, out = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "n.md", "content": banned_term()},
        }
    )
    reason = json.loads(out)["hookSpecificOutput"]["permissionDecisionReason"]
    assert banned_term() in reason.lower()
    assert "principle 3" in reason


def test_clean_content_produces_no_decision():
    code, out = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {"file_path": "n.md", "content": "an ordinary sentence"},
        }
    )
    assert code == 0
    assert decision(out) is None, "silence lets the normal permission flow run"


def test_non_content_tools_are_ignored():
    """Bash carries no file content; scanning its command would misfire."""
    _, out = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": f"grep {banned_term()} log.txt"},
        }
    )
    assert decision(out) is None


def test_the_banned_terms_file_itself_stays_editable():
    """Otherwise the list becomes unmaintainable the moment it has an entry."""
    _, out = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": "config/security/banned-terms.txt",
                "content": banned_term(),
            },
        }
    )
    assert decision(out) is None


@pytest.mark.parametrize("payload", ["not json", "", "[]", '{"tool_name": "Write"}'])
def test_malformed_input_never_blocks(payload):
    """The hook must not become the reason a legitimate edit is impossible."""
    code, out = run_hook(payload)
    assert code == 0
    assert decision(out) is None


def test_a_path_containing_the_term_is_not_mistaken_for_content():
    """Only the content-carrying fields are scanned, not the whole payload."""
    _, out = run_hook(
        {
            "hook_event_name": "PreToolUse",
            "tool_name": "Write",
            "tool_input": {
                "file_path": f"docs/{banned_term()}/readme.md",
                "content": "clean text",
            },
        }
    )
    assert decision(out) is None
