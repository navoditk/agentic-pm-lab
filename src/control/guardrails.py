"""Lightweight local content guardrail backed by the repository denied terms."""

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.observability.telemetry import observe_operation

REPO_ROOT = Path(__file__).resolve().parents[2]
BANNED_TERMS_PATH = REPO_ROOT / "config" / "security" / "banned-terms.txt"


class GuardrailViolation(ValueError):
    """Raised when local input, context, or output contains a denied term."""


def load_denied_terms(path: Path = BANNED_TERMS_PATH) -> tuple[str, ...]:
    """Load normalized denied terms from the shared pre-commit configuration."""
    return tuple(
        line.strip().lower()
        for line in path.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def denied_terms(text: str) -> tuple[str, ...]:
    """Return configured terms present in text, without exposing matched content."""
    normalized = text.lower()
    return tuple(term for term in load_denied_terms() if term in normalized)


def enforce_content(text: str, stage: str) -> None:
    """Raise on denied content and emit a guardrail decision span."""
    matches = denied_terms(text)
    with observe_operation(
        "control.enforce_content",
        "guardrail",
        {
            "app.guardrail.stage": stage,
            "app.guardrail.allowed": not matches,
            "app.guardrail.match_count": len(matches),
        },
    ):
        if matches:
            raise GuardrailViolation(
                f"Content blocked by local guardrail during {stage}"
            )


def enforce_agent_input(
    question: str,
    sources: Mapping[str, Any],
) -> None:
    """Check the user question and assembled source values before model access."""
    enforce_content(question, "input")
    enforce_content(json.dumps(sources, sort_keys=True, default=str), "context")


def enforce_agent_output(result: Mapping[str, Any]) -> None:
    """Check the completed agent result before returning it to the caller."""
    enforce_content(json.dumps(result, sort_keys=True, default=str), "output")
