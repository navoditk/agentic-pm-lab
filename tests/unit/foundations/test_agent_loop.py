"""The hand-built agent loop, tested on the behaviours the course teaches.

Quiz questions in evals/tutor_quizzes/agent-foundations-tutor.jsonl cite
these tests by name (`verified_by`), so each one pins a claim a learner is
assessed on. Rename one only together with the question that cites it.
"""

import json

import pytest
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from src.foundations.agent_loop import (
    ModelTurn,
    ScriptedModel,
    ToolCall,
    demo_tools,
    run_agent,
)
from src.observability.telemetry import configure_telemetry

ALLOWED = {"interpolate_yield"}


@pytest.fixture(scope="module")
def spans():
    exporter = InMemorySpanExporter()
    configure_telemetry().add_span_processor(SimpleSpanProcessor(exporter))
    return exporter


@pytest.fixture
def audit_log(tmp_path):
    return tmp_path / "audit.jsonl"


def call(name, arguments, call_id="c1"):
    return ModelTurn(tool_calls=(ToolCall(call_id, name, arguments),))


def run(turns, audit_log, **kwargs):
    model = ScriptedModel(turns)
    kwargs.setdefault("allowed_tools", ALLOWED)
    result = run_agent(
        "What is the 3-year yield?", model, demo_tools(), audit_log=audit_log, **kwargs
    )
    return model, result


# --- the loop ----------------------------------------------------------------


def test_the_loop_feeds_each_tool_result_back_before_the_model_answers(audit_log):
    model, result = run(
        [
            call("interpolate_yield", '{"target_tenor_years": 3}'),
            ModelTurn(text="The 3-year yield is 4.3%."),
        ],
        audit_log,
    )
    assert result.stop_reason == "answered"
    # The second model call saw the tool result from the first.
    tool_message = model.seen_messages[1][-1]
    assert tool_message["role"] == "tool" and tool_message["tool_call_id"] == "c1"
    assert json.loads(tool_message["content"]) == {"result": pytest.approx(4.3)}


def test_the_model_answering_without_a_tool_call_ends_the_loop(audit_log):
    model, result = run([ModelTurn(text="I can answer directly.")], audit_log)
    assert result.stop_reason == "answered" and len(model.seen_messages) == 1


def test_max_steps_stops_a_model_that_never_stops_calling_tools(audit_log):
    turns = [
        call("interpolate_yield", '{"target_tenor_years": 3}', f"c{i}")
        for i in range(10)
    ]
    model, result = run(turns, audit_log, max_steps=3)
    assert result.stop_reason == "max_steps" and result.answer is None
    assert len(model.seen_messages) == 3


# --- failure: malformed and failing calls go back to the model ------------------


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ("{not json", "JSONDecodeError"),
        ('{"target_tenor_years": "three"}', "ValidationError"),
        ('{"tenor": 3}', "ValidationError"),
    ],
)
def test_a_malformed_tool_call_becomes_an_error_the_model_can_see(
    audit_log, arguments, expected
):
    model, result = run(
        [call("interpolate_yield", arguments), ModelTurn(text="Retrying failed.")],
        audit_log,
    )
    error = json.loads(model.seen_messages[1][-1]["content"])["error"]
    assert error.startswith(expected)
    assert result.stop_reason == "answered"  # no crash: the model got to react


def test_a_tool_that_raises_reports_the_error_instead_of_crashing(audit_log):
    model, _ = run(
        [
            call("interpolate_yield", '{"target_tenor_years": 30}'),
            ModelTurn(text="30 years is outside the curve."),
        ],
        audit_log,
    )
    assert "outside" in json.loads(model.seen_messages[1][-1]["content"])["error"]


# --- governance ---------------------------------------------------------------


def test_the_model_is_only_shown_allowed_tools(audit_log):
    model, _ = run([ModelTurn(text="ok")], audit_log)
    assert model.seen_tools == [["interpolate_yield"]]


def test_a_forbidden_tool_is_refused_in_code_even_when_requested(audit_log):
    """The model was never shown place_order and asks for it anyway: a
    hallucinated or injected call. Being hidden is not enough; the check at
    execution is what stops it (demo place_order raises if it ever runs)."""
    model, result = run(
        [
            call("place_order", '{"ticker": "X", "quantity": 1}'),
            ModelTurn(text="I cannot place orders."),
        ],
        audit_log,
    )
    assert "not permitted" in model.seen_messages[1][-1]["content"]
    assert [(r["tool_name"], r["decision"]) for r in result.audit] == [
        ("place_order", "denied")
    ]


def test_an_unknown_tool_is_refused_and_audited(audit_log):
    _, result = run([call("delete_everything", "{}"), ModelTurn(text="ok")], audit_log)
    assert result.audit[0]["decision"] == "denied"


# --- observability and traceability ------------------------------------------------


def test_spans_follow_the_genai_conventions_and_nest_under_the_run(spans, audit_log):
    spans.clear()
    run(
        [
            call("interpolate_yield", '{"target_tenor_years": 3}'),
            ModelTurn(text="4.3%"),
        ],
        audit_log,
    )
    finished = {s.name: s for s in spans.get_finished_spans()}
    root = finished["invoke_agent foundations-agent"]
    chat = finished["chat scripted-model"]
    tool = finished["execute_tool interpolate_yield"]
    assert tool.attributes["gen_ai.tool.name"] == "interpolate_yield"
    assert tool.attributes["gen_ai.tool.call.id"] == "c1"
    assert chat.attributes["gen_ai.operation.name"] == "chat"
    for span in (chat, tool):
        assert span.parent.span_id == root.context.span_id
    # The real analytics tool's own span nests under the tool span.
    assert (
        finished["analytics.interpolate_curve"].parent.span_id == tool.context.span_id
    )


def test_every_audit_record_carries_the_runs_trace_id(audit_log):
    _, result = run(
        [
            call("interpolate_yield", '{"target_tenor_years": 3}', "c1"),
            call("place_order", '{"ticker": "X", "quantity": 1}', "c2"),
            ModelTurn(text="done"),
        ],
        audit_log,
    )
    assert result.trace_id and len(result.trace_id) == 32
    written = [json.loads(line) for line in audit_log.read_text().splitlines()]
    assert {r["trace_id"] for r in written} == {result.trace_id}
    assert [r["decision"] for r in written] == ["allowed", "denied"]
    # Decisions only: no prompt, message, or argument content reaches the log.
    for record in written:
        assert not {"prompt", "messages", "arguments", "content"} & set(record)


# --- regressions found in review ---------------------------------------------------


@pytest.mark.parametrize("loop", ["agent_loop", "langchain_loop"])
def test_a_fresh_process_run_shares_one_trace_id_with_its_audit(loop, tmp_path):
    """Run in a new interpreter: in-process tests inherit telemetry that an
    earlier test configured, which is exactly what hid this bug. The run's
    trace id was None while its audit record carried an unrelated id."""
    import subprocess
    import sys

    program = {
        "agent_loop": (
            "from src.foundations.agent_loop import *\n"
            "r = run_agent('q', ScriptedModel([ModelTurn(tool_calls=(ToolCall("
            "'c1', 'place_order', '{}'),)), ModelTurn(text='no')]), demo_tools(),"
            " allowed_tools={'interpolate_yield'}, audit_log=LOG)\n"
        ),
        "langchain_loop": (
            "from langchain_core.messages import AIMessage\n"
            "from src.foundations.langchain_loop import *\n"
            "m = ScriptedToolModel(messages=iter([AIMessage(content='', tool_calls="
            "[{'name': 'place_order', 'args': {}, 'id': 'c1'}]), AIMessage(content='no')]))\n"
            "r = run_langchain_agent('q', m, [interpolate_yield, place_order],"
            " allowed_tools={'interpolate_yield'}, audit_log=LOG)\n"
        ),
    }[loop]
    script = (
        "from pathlib import Path\n"
        f"LOG = Path({str(tmp_path / 'audit.jsonl')!r})\n"
        + program
        + "print(r.trace_id, r.audit[0]['trace_id'])\n"
    )
    out = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=True
    ).stdout.split()
    run_id, audit_id = out[-2], out[-1]
    assert run_id != "None" and len(run_id) == 32
    assert audit_id == run_id


def test_refused_and_failed_tool_calls_mark_their_spans_as_errors(spans, audit_log):
    """What the failure lab asks the learner to predict: the span status."""
    from opentelemetry.trace import StatusCode

    spans.clear()
    run(
        [
            call("place_order", '{"ticker": "X", "quantity": 1}', "c1"),
            call("interpolate_yield", "{not json", "c2"),
            call("interpolate_yield", '{"target_tenor_years": 3}', "c3"),
            ModelTurn(text="done"),
        ],
        audit_log,
    )
    tool_spans = {
        s.attributes["gen_ai.tool.call.id"]: s
        for s in spans.get_finished_spans()
        if s.name.startswith("execute_tool")
    }
    assert tool_spans["c1"].status.status_code is StatusCode.ERROR  # refused
    assert tool_spans["c1"].status.description == "not permitted"
    assert tool_spans["c2"].status.status_code is StatusCode.ERROR  # malformed
    assert tool_spans["c2"].status.description == "JSONDecodeError"
    assert tool_spans["c3"].status.status_code is not StatusCode.ERROR  # succeeded


def test_a_tool_call_without_a_name_is_still_visible_on_its_span(spans, audit_log):
    spans.clear()
    run([call(None, "{}", "c1"), ModelTurn(text="ok")], audit_log)
    tool = next(
        s for s in spans.get_finished_spans() if s.name.startswith("execute_tool")
    )
    assert tool.attributes["gen_ai.tool.name"] == "None"
