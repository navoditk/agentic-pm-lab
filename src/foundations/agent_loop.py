"""The agent loop, built by hand, with nothing hidden.

An agent is a loop: ask the model what to do next, do it, show the model what
happened, and repeat until the model answers or a limit stops it. Frameworks
wrap this loop; `langchain_loop.py` runs the same one in LangChain so the two
can be read side by side, the way `src/agents/handbuilt_graph.py` sits beside
`multi_agent.py`.

It is deliberately **model-free**. `ScriptedModel` replays planned turns, so
every path, including a malformed tool call and a request for a forbidden
tool, runs in a unit test with no network, key, or sampling noise.

Four threads run through the loop from the first line, because they are not
features to add later:

- **Observability.** One `invoke_agent` span per run, a `chat` span per model
  call, and an `execute_tool` span per tool call, named by the OpenTelemetry
  GenAI semantic conventions (status: Development).
- **Traceability.** Audit records are written inside the run's span, so each
  carries the run's trace id (`src/control/audit.py::current_trace_id`), and
  one id reconstructs the decision.
- **Governance.** The model is only *shown* allowed tools, and the allowlist
  is checked again in code before anything runs: the model can ask for
  anything, but a request is not permission. Refusals are audited and
  returned to the model, never hidden.
- **Evals.** `RunResult` keeps the full transcript and audit trail, so
  `grading.py` can grade the outcome and check the path constraints that are
  requirements.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from src.analytics.curves import interpolate_curve
from src.control.audit import current_trace_id, record_audit_event
from src.observability.telemetry import configure_telemetry

tracer = trace.get_tracer(__name__)
AGENT_NAME = "foundations-agent"

# Illustrative fixture, not market data: a fixed curve keeps the lab deterministic.
DEMO_CURVE_TENORS = (1.0, 2.0, 5.0, 10.0)
DEMO_CURVE_RATES_PCT = (4.0, 4.2, 4.5, 4.8)


@dataclass(frozen=True)
class Tool:
    """A tool is a name, a description the model reads, a JSON Schema for its
    arguments, and a function. The schema is written by hand here; LangChain
    generates it from type hints (part 2)."""

    name: str
    description: str
    parameters: Mapping[str, Any]
    function: Callable[..., Any]

    def spec(self) -> dict[str, Any]:
        """What the model is shown: never the function itself."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": dict(self.parameters),
        }


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    # Raw, as the model produced it: usually a JSON string, possibly malformed.
    arguments: Any


@dataclass(frozen=True)
class ModelTurn:
    text: str | None = None
    tool_calls: tuple[ToolCall, ...] = ()


class ScriptedModel:
    """Stands in for an LLM: returns planned turns in order, and records what
    it was shown each time, so a test can check what the model saw."""

    name = "scripted-model"

    def __init__(self, turns: Sequence[ModelTurn]) -> None:
        self._turns = list(turns)
        self.seen_messages: list[list[dict[str, Any]]] = []
        self.seen_tools: list[list[str]] = []

    def __call__(
        self, messages: Sequence[Mapping[str, Any]], tools: Sequence[Mapping[str, Any]]
    ) -> ModelTurn:
        self.seen_messages.append([dict(message) for message in messages])
        self.seen_tools.append([tool["name"] for tool in tools])
        if not self._turns:
            raise RuntimeError("the scripted model has no more turns")
        return self._turns.pop(0)


@dataclass
class RunResult:
    answer: str | None
    stop_reason: str  # "answered" or "max_steps"
    transcript: list[dict[str, Any]]
    trace_id: str | None
    audit: list[dict[str, Any]] = field(default_factory=list)

    @property
    def tool_calls_requested(self) -> list[str]:
        return [
            call["name"]
            for message in self.transcript
            for call in message.get("tool_calls", [])
        ]


def governed_call(
    name: str,
    call_id: str,
    *,
    known: Collection[str],
    allowed: Collection[str],
    run: Callable[[], Any],
    audit_log: Path,
    identity: str,
    role: str,
    audit: list[dict[str, Any]],
) -> str:
    """Execute one requested tool call behind the allowlist, inside its span.

    Shared by both loops so they differ only in what the framework does.
    Returns the content of the tool message the model will see next: a result,
    or an error the model can react to. Nothing here raises to the loop, because
    a bad tool call is something for the model to recover from, not a crash.
    """
    with tracer.start_as_current_span(f"execute_tool {name}") as span:
        span.set_attribute("gen_ai.operation.name", "execute_tool")
        # str(): a malformed call can arrive without a name or id, and OTel
        # silently drops a None attribute, which would hide it from the trace.
        span.set_attribute("gen_ai.tool.name", str(name))
        span.set_attribute("gen_ai.tool.call.id", str(call_id))
        span.set_attribute("gen_ai.tool.type", "function")
        if name not in known or name not in allowed:
            # Complete mediation: checked in code on every call, whatever the
            # model was shown and whatever its reasoning said.
            reason = "unknown tool" if name not in known else "not permitted"
            span.set_attribute("app.tool.permitted", False)
            span.set_status(Status(StatusCode.ERROR, reason))
            audit.append(
                record_audit_event(
                    identity, role, name, "denied", "Tool", log_path=audit_log
                )
            )
            return json.dumps({"error": f"tool {name!r} is {reason}"})
        span.set_attribute("app.tool.permitted", True)
        audit.append(
            record_audit_event(
                identity, role, name, "allowed", "Tool", log_path=audit_log
            )
        )
        try:
            return json.dumps({"result": run()})
        # Deliberately broad: whatever a tool raises becomes a message the
        # model can react to, rather than a crash that ends the run.
        except Exception as error:  # noqa: BLE001
            span.set_status(Status(StatusCode.ERROR, type(error).__name__))
            return json.dumps({"error": f"{type(error).__name__}: {error}"})


def _parse_and_validate(tool: Tool, raw: Any) -> dict[str, Any]:
    """Models emit arguments as text. Parse, then check against the schema:
    the schema is a contract, and a contract nobody checks is a comment."""
    arguments = json.loads(raw) if isinstance(raw, str) else raw
    jsonschema.validate(arguments, tool.parameters)
    return arguments


def run_agent(
    question: str,
    model: Callable[..., ModelTurn],
    tools: Sequence[Tool],
    *,
    allowed_tools: Collection[str],
    audit_log: Path,
    max_steps: int = 5,
    identity: str = "learner",
    role: str = "RESEARCH_USER",
) -> RunResult:
    """Run the loop until the model answers or `max_steps` model calls pass."""
    # Install the tracer provider before the first span. Without this, a fresh
    # process opens the run span on OpenTelemetry's no-op provider (no trace
    # id), and the first audit call then configures telemetry and starts an
    # unrelated trace, so the run and its audit records no longer share an id.
    configure_telemetry()
    by_name = {tool.name: tool for tool in tools}
    # Least privilege in what the model is shown, not only in what runs.
    visible = [tool.spec() for tool in tools if tool.name in allowed_tools]
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    audit: list[dict[str, Any]] = []
    with tracer.start_as_current_span(f"invoke_agent {AGENT_NAME}") as run_span:
        run_span.set_attribute("gen_ai.operation.name", "invoke_agent")
        run_span.set_attribute("gen_ai.agent.name", AGENT_NAME)
        trace_id = current_trace_id()
        for _ in range(max_steps):
            with tracer.start_as_current_span(f"chat {model.name}") as span:
                span.set_attribute("gen_ai.operation.name", "chat")
                span.set_attribute("gen_ai.request.model", model.name)
                turn = model(messages, visible)
            if not turn.tool_calls:
                messages.append({"role": "assistant", "content": turn.text})
                run_span.set_attribute("app.agent.stop_reason", "answered")
                return RunResult(turn.text, "answered", messages, trace_id, audit)
            messages.append(
                {
                    "role": "assistant",
                    "content": turn.text,
                    "tool_calls": [
                        {"id": c.id, "name": c.name, "arguments": c.arguments}
                        for c in turn.tool_calls
                    ],
                }
            )
            for call in turn.tool_calls:
                tool = by_name.get(call.name)
                content = governed_call(
                    call.name,
                    call.id,
                    known=by_name,
                    allowed=allowed_tools,
                    run=lambda tool=tool, call=call: tool.function(
                        **_parse_and_validate(tool, call.arguments)
                    ),
                    audit_log=audit_log,
                    identity=identity,
                    role=role,
                    audit=audit,
                )
                messages.append(
                    {"role": "tool", "tool_call_id": call.id, "content": content}
                )
        # A stopping condition that is not the model's choice: without it, a
        # model that never stops calling tools never stops costing money.
        run_span.set_attribute("app.agent.stop_reason", "max_steps")
        return RunResult(None, "max_steps", messages, trace_id, audit)


def demo_tools() -> list[Tool]:
    """One useful tool and one that must never run."""

    def interpolate_yield(target_tenor_years: float) -> float:
        return interpolate_curve(
            DEMO_CURVE_TENORS, DEMO_CURVE_RATES_PCT, [target_tenor_years]
        )[0]

    def place_order(ticker: str, quantity: int) -> str:
        raise AssertionError("place_order executed: governance failed")

    return [
        Tool(
            name="interpolate_yield",
            description=(
                "Interpolate the demo yield curve at one tenor. "
                "Returns a yield in percent. Tenor must be 1 to 10 years."
            ),
            parameters={
                "type": "object",
                "properties": {"target_tenor_years": {"type": "number"}},
                "required": ["target_tenor_years"],
                "additionalProperties": False,
            },
            function=interpolate_yield,
        ),
        Tool(
            name="place_order",
            description="Place a trade order.",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
                "required": ["ticker", "quantity"],
            },
            function=place_order,
        ),
    ]
