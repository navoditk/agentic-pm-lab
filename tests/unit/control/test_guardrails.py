import pytest

from src.control.guardrails import (
    GuardrailViolation,
    denied_terms,
    enforce_agent_input,
    enforce_content,
)


def _denied_term() -> str:
    return "ACME-" + "INTERNAL-PROJECT-CODE"


def test_denied_terms_use_the_shared_repository_configuration():
    assert denied_terms(f"prefix {_denied_term()} suffix") == (_denied_term().lower(),)


def test_guardrail_blocks_denied_input_without_echoing_content():
    with pytest.raises(GuardrailViolation, match="during input") as error:
        enforce_content(f"Summarize {_denied_term()}", "input")

    assert _denied_term() not in str(error.value)


def test_guardrail_checks_named_context_before_model_access():
    sources = {
        "user_role": {"identity": "PM_USER"},
        "portfolio_state": {"note": _denied_term()},
    }

    with pytest.raises(GuardrailViolation, match="during context"):
        enforce_agent_input("Summarize the portfolio.", sources, "PM_USER")
