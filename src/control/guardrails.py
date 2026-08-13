"""Lightweight local content guardrail backed by the repository denied terms."""

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from src.control.audit import record_audit_event
from src.control.identity import role_for_identity
from src.observability.telemetry import observe_operation

REPO_ROOT = Path(__file__).resolve().parents[2]
BANNED_TERMS_PATH = REPO_ROOT / "config" / "security" / "banned-terms.txt"


class GuardrailViolation(ValueError):
    """Raised when local input, context, or output contains a denied term."""


TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "unqualified_trading_directive",
        re.compile(
            r"(?:\b(?:buy|sell|short|liquidate|exit)\b.{0,80}"
            r"\b(?:now|today|immediately|shares?|units?|position|trade|order)\b)"
            r"|\b(?:place|execute|submit)\s+(?:a\s+)?"
            r"(?:buy|sell|trade|order)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "prompt_or_credential_exfiltration",
        re.compile(
            r"\b(?:reveal|show|print|dump|expose|ignore)\b.{0,80}"
            r"\b(?:system\s+prompt|hidden\s+instructions?|credentials?|"
            r"api\s+keys?|secrets?)\b",
            re.IGNORECASE,
        ),
    ),
)


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


def denied_topics(text: str) -> tuple[str, ...]:
    """Return semantic topic categories matched by the local policy patterns."""
    return tuple(name for name, pattern in TOPIC_PATTERNS if pattern.search(text))


def enforce_content(text: str, stage: str) -> None:
    """Raise on denied content and emit a guardrail decision span."""
    matches = denied_terms(text)
    topics = denied_topics(text)
    match_count = len(matches) + len(topics)
    with observe_operation(
        "control.enforce_content",
        "guardrail",
        {
            "app.guardrail.stage": stage,
            "app.guardrail.allowed": not match_count,
            "app.guardrail.match_count": match_count,
        },
    ):
        if matches or topics:
            raise GuardrailViolation(
                f"Content blocked by local guardrail during {stage}"
            )


def enforce_agent_input(
    question: str,
    sources: Mapping[str, Any],
    identity: str,
) -> None:
    """Check the user question and assembled source values before model access."""
    _enforce_and_audit(question, "input", identity)
    _enforce_and_audit(
        json.dumps(sources, sort_keys=True, default=str),
        "context",
        identity,
    )


def enforce_agent_output(result: Mapping[str, Any], identity: str) -> None:
    """Check the completed agent result before returning it to the caller."""
    _enforce_and_audit(
        json.dumps(result, sort_keys=True, default=str),
        "output",
        identity,
    )


def _enforce_and_audit(text: str, stage: str, identity: str) -> None:
    role = role_for_identity(identity) or "unknown"
    try:
        enforce_content(text, stage)
    except GuardrailViolation:
        record_audit_event(
            identity,
            role,
            f"content-{stage}",
            "denied",
            "Guardrail",
        )
        raise
    record_audit_event(
        identity,
        role,
        f"content-{stage}",
        "allowed",
        "Guardrail",
    )
