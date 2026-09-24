"""Amazon Bedrock at the model layer, for the AWS Bedrock course.

Agent foundations built an agent loop against a scripted model. This module
puts a real Bedrock client behind the same loop: `ConverseModel` translates
between the loop's messages and the Converse API, so `run_agent()` runs
unchanged with Bedrock as its model, spans, audit, and allowlist included.

Every lab is offline. `stubbed_client()` makes a bedrock-runtime client with
dummy credentials and no network, and `botocore.stub.Stubber` feeds it
responses. Stubber validates every request and response against the service
model shipped with botocore, so the shapes here are checked against the SDK,
not assumed. What each part relies on, and where it comes from:

- Converse is one API for all Bedrock models that support messages; it needs
  `bedrock:InvokeModel` (ConverseStream needs
  `bedrock:InvokeModelWithResponseStream`). AWS user guide.
- Through Converse, tool use is client-side: the model returns
  `stopReason: "tool_use"` with `toolUse` blocks, and your code runs them and
  returns `toolResult` blocks in a `user` message, with `status: "error"` on
  failure. AWS tool-use guide. (Server-side tool use, where Bedrock invokes a
  registered Lambda function or AgentCore Gateway itself, is a Responses API
  mode, not Converse.)
- With prompt caching, `inputTokens` counts only uncached input; the total is
  `inputTokens + cacheReadInputTokens + cacheWriteInputTokens`. AWS user guide.
- Throttling (429) and service unavailability (503) are retried with
  exponential backoff and jitter; access and validation errors are not.
  AWS error-code guide. botocore's own retry modes (legacy, standard,
  adaptive) do this in production, but Stubber bypasses them, so the lab's
  explicit `with_retries` is what the tests can observe.
"""

from __future__ import annotations

import json
import random
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any

import boto3
from botocore.exceptions import ClientError
from opentelemetry import trace
from opentelemetry.trace import SpanKind

from src.foundations.agent_loop import ModelTurn, ToolCall

tracer = trace.get_tracer(__name__)

# Retry only what can succeed on a later attempt. An AccessDeniedException or
# ValidationException will fail identically every time; retrying it only
# delays the error and costs quota.
RETRYABLE = {
    "ThrottlingException",
    "ServiceUnavailableException",
    "ModelNotReadyException",
    "InternalServerException",
}


def stubbed_client(region: str = "us-east-1") -> Any:
    """A bedrock-runtime client for Stubber: dummy credentials, no network."""
    return boto3.client(
        "bedrock-runtime",
        region_name=region,
        aws_access_key_id="lab",
        aws_secret_access_key="lab",  # pragma: allowlist secret - offline stub placeholder
    )


def tool_config(tools: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The loop's tool specs, as Converse `toolSpec`s."""
    return {
        "tools": [
            {
                "toolSpec": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "inputSchema": {"json": tool["parameters"]},
                }
            }
            for tool in tools
        ]
    }


def to_converse_messages(
    transcript: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Translate the loop's transcript into Converse messages.

    Converse has two roles, user and assistant. Tool results are content
    blocks in a user message. This lab puts all the results for one assistant
    turn into a single user message, one block per `toolUseId`. That is a
    choice: AWS's own single-tool example appends a user message per result,
    and the API reference states no rule either way.
    """
    messages: list[dict[str, Any]] = []
    for entry in transcript:
        if entry["role"] == "user":
            messages.append({"role": "user", "content": [{"text": entry["content"]}]})
        elif entry["role"] == "assistant":
            content: list[dict[str, Any]] = []
            if entry.get("content"):
                content.append({"text": entry["content"]})
            for call in entry.get("tool_calls", []):
                arguments = call["arguments"]
                content.append(
                    {
                        "toolUse": {
                            "toolUseId": call["id"],
                            "name": call["name"],
                            "input": json.loads(arguments)
                            if isinstance(arguments, str)
                            else arguments,
                        }
                    }
                )
            messages.append({"role": "assistant", "content": content})
        elif entry["role"] == "tool":
            payload = json.loads(entry["content"])
            block = {
                "toolResult": {
                    "toolUseId": entry["tool_call_id"],
                    "content": [{"json": payload}],
                    "status": "error" if "error" in payload else "success",
                }
            }
            previous = messages[-1] if messages else None
            if (
                previous
                and previous["role"] == "user"
                and "toolResult" in (previous["content"][-1])
            ):
                previous["content"].append(block)
            else:
                messages.append({"role": "user", "content": [block]})
    return messages


def with_retries[T](
    call: Callable[[], T],
    *,
    attempts: int = 4,
    base_delay: float = 0.5,
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
) -> T:
    """Bounded retry with exponential backoff and full jitter."""
    rng = rng or random.Random()
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except ClientError as error:
            code = error.response["Error"]["Code"]
            if code not in RETRYABLE or attempt == attempts:
                raise
            sleep(rng.uniform(0, base_delay * 2 ** (attempt - 1)))
    raise AssertionError("unreachable")  # pragma: no cover


class ConverseModel:
    """A Bedrock model behind the Agent foundations loop's model interface."""

    # A call to a model in another process: a CLIENT span, per the GenAI
    # semantic conventions.
    span_kind = SpanKind.CLIENT

    def __init__(
        self,
        client: Any,
        model_id: str,
        *,
        system: str | None = None,
        cache_system: bool = False,
        guardrail: Mapping[str, str] | None = None,
        retry: Callable[[Callable[[], Any]], Any] = with_retries,
    ) -> None:
        self.client = client
        self.name = model_id
        self.system = system
        self.cache_system = cache_system
        self.guardrail = guardrail
        self.retry = retry
        self.responses: list[dict[str, Any]] = []

    def request(
        self,
        transcript: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "modelId": self.name,
            "messages": to_converse_messages(transcript),
        }
        if self.system:
            system: list[dict[str, Any]] = [{"text": self.system}]
            if self.cache_system:
                # Mark the stable prefix. It is cached only if the prefix meets
                # the model's minimum token count; the request succeeds either way.
                system.append({"cachePoint": {"type": "default"}})
            request["system"] = system
        if tools:
            request["toolConfig"] = tool_config(tools)
        if self.guardrail:
            request["guardrailConfig"] = dict(self.guardrail)
        return request

    def __call__(
        self,
        transcript: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
    ) -> ModelTurn:
        request = self.request(transcript, tools)
        response = self.retry(lambda: self.client.converse(**request))
        self.responses.append(response)
        span = trace.get_current_span()
        usage = response.get("usage", {})
        span.set_attribute("gen_ai.provider.name", "aws.bedrock")
        span.set_attribute("gen_ai.response.finish_reasons", [response["stopReason"]])
        span.set_attribute("gen_ai.usage.input_tokens", total_input_tokens(usage))
        span.set_attribute("gen_ai.usage.output_tokens", usage.get("outputTokens", 0))
        content = response["output"]["message"]["content"]
        text = "".join(block.get("text", "") for block in content) or None
        if response["stopReason"] != "tool_use":
            return ModelTurn(text=text)
        return ModelTurn(
            text=text,
            tool_calls=tuple(
                ToolCall(
                    block["toolUse"]["toolUseId"],
                    block["toolUse"]["name"],
                    block["toolUse"]["input"],
                )
                for block in content
                if "toolUse" in block
            ),
        )


def total_input_tokens(usage: Mapping[str, int]) -> int:
    """With prompt caching, `inputTokens` is only the uncached part."""
    return (
        usage.get("inputTokens", 0)
        + usage.get("cacheReadInputTokens", 0)
        + usage.get("cacheWriteInputTokens", 0)
    )


def apply_guardrail(
    client: Any, guardrail_id: str, version: str, text: str, *, source: str
) -> tuple[bool, str]:
    """Check text against a guardrail without invoking any model.

    `source` is INPUT for user content and OUTPUT for model output. Returns
    whether the guardrail intervened, and the text to use: the guardrail's
    output when it intervened, the original text when it did not.
    """
    response = client.apply_guardrail(
        guardrailIdentifier=guardrail_id,
        guardrailVersion=version,
        source=source,
        content=[{"text": {"text": text}}],
    )
    intervened = response["action"] == "GUARDRAIL_INTERVENED"
    outputs = response.get("outputs") or []
    return intervened, (outputs[0]["text"] if intervened and outputs else text)


def invoke_through_profile_policy(
    profile_arn: str, foundation_model_arns: Sequence[str]
) -> dict[str, Any]:
    """Least privilege for calling one model only through one inference profile.

    Mirrors the pattern in AWS's inference-profile prerequisites: allow the
    profile, and allow the foundation model in every Region the profile routes
    to, but only when the request comes through that profile.
    """
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": [profile_arn],
            },
            {
                "Effect": "Allow",
                "Action": ["bedrock:InvokeModel"],
                "Resource": list(foundation_model_arns),
                "Condition": {
                    "StringLike": {"bedrock:InferenceProfileArn": profile_arn}
                },
            },
        ],
    }
