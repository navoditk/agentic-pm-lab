"""Failure handling shared by specialist agents."""

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import httpx
from jsonschema import Draft202012Validator, ValidationError
from langchain.agents.middleware import (
    ModelRetryMiddleware,
    ToolCallLimitMiddleware,
    ToolErrorMiddleware,
    ToolRetryMiddleware,
)
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ToolCallRequest,
)
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from openai import APITimeoutError, RateLimitError

CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "contracts" / "tools"
RETRYABLE_EXCEPTIONS = (
    TimeoutError,
    httpx.TimeoutException,
    APITimeoutError,
    RateLimitError,
)


class ToolContractError(ValueError):
    """Raised when a tool result violates its checked JSON Schema contract."""


class ContractValidationMiddleware(AgentMiddleware):
    """Validate tool inputs and outputs when an exact-name contract exists."""

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        tool_name = request.tool.name if request.tool else request.tool_call["name"]
        schema_path = CONTRACTS_DIR / f"{tool_name}.schema.json"
        if not schema_path.is_file():
            return handler(request)

        schema = json.loads(schema_path.read_text())
        result = handler(request)
        if not isinstance(result, ToolMessage) or result.status == "error":
            return result

        try:
            output = (
                json.loads(result.content) if isinstance(result.content, str) else None
            )
            if output is None:
                raise ToolContractError("tool result is not a JSON object")
            Draft202012Validator(schema).validate(
                {
                    "input": request.tool_call["args"],
                    "output": output,
                }
            )
        except (json.JSONDecodeError, ValidationError) as error:
            raise ToolContractError(
                f"{tool_name} response failed contract validation"
            ) from error
        return result


def _dead_letter(
    error: Exception,
    request: ToolCallRequest,
) -> str:
    tool_name = request.tool.name if request.tool else request.tool_call["name"]
    retryable = isinstance(error, RETRYABLE_EXCEPTIONS)
    return json.dumps(
        {
            "status": "dead_letter",
            "tool": tool_name,
            "error_type": type(error).__name__,
            "retryable": retryable,
            "message": (
                "retry budget exhausted; no result was produced"
                if retryable
                else "tool response failed validation; no result was accepted"
            ),
        }
    )


def specialist_recovery_middleware(
    *,
    max_retries: int = 2,
    initial_delay: float = 0.1,
    tool_call_limit: int = 8,
) -> Sequence[AgentMiddleware]:
    """Return bounded specialist retry, validation, and dead-letter middleware."""
    return (
        ToolErrorMiddleware(on_error=_dead_letter),
        ToolRetryMiddleware(
            max_retries=max_retries,
            retry_on=RETRYABLE_EXCEPTIONS,
            on_failure="error",
            backoff_factor=2.0,
            initial_delay=initial_delay,
            max_delay=2.0,
            jitter=False,
        ),
        ContractValidationMiddleware(),
        ToolCallLimitMiddleware(
            run_limit=tool_call_limit,
            exit_behavior="error",
        ),
        ModelRetryMiddleware(
            max_retries=max_retries,
            retry_on=RETRYABLE_EXCEPTIONS,
            on_failure="error",
            backoff_factor=2.0,
            initial_delay=initial_delay,
            max_delay=2.0,
            jitter=False,
        ),
    )


def orchestrator_recovery_middleware(
    *,
    max_retries: int = 2,
    initial_delay: float = 0.1,
    delegation_limit: int = 6,
) -> Sequence[AgentMiddleware]:
    """Return bounded model retries and delegation limits for the orchestrator."""
    return (
        ToolCallLimitMiddleware(
            tool_name="task",
            run_limit=delegation_limit,
            exit_behavior="error",
        ),
        ModelRetryMiddleware(
            max_retries=max_retries,
            retry_on=RETRYABLE_EXCEPTIONS,
            on_failure="error",
            backoff_factor=2.0,
            initial_delay=initial_delay,
            max_delay=2.0,
            jitter=False,
        ),
    )
