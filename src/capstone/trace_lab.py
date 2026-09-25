"""Traceability end to end: one decision, rebuilt from one trace id.

The capstone lab. A fixture decision runs through every layer the Agent core
courses built, and each layer writes to its own store, as it would in a real
deployment:

- spans, from the request, the agent loop, and a separate pricing service;
- audit records, from the loop's tool boundary and from the pricing service;
- an evaluation record, grading the answer, with the versions that produced it;
- an evidence record, with the point-in-time source the decision relied on.

`reconstruct()` takes only a trace id and finds every hop in every store.
That is the question model risk asks of a decision: given this one id, show
what was asked, what was allowed, what ran, on what evidence, and how it was
judged.

The pricing service stands in for a process boundary. It joins the trace
only if the caller injects `traceparent` and the service extracts it. Run
the decision with `propagate=False` and the service's span and audit record
land in a different trace: they still exist, but nothing joins them to the
decision, and `missing_hops()` names the gap. The tests in
tests/unit/capstone/test_trace_lab.py are the capstone's acceptance test
together: the full reconstruction shows every hop is found, and the gap test
is what proves the search is by id, since a store that matched any id would
find the orphaned pricing hop too.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from src.control.audit import current_trace_id, record_audit_event
from src.foundations.agent_loop import (
    ModelTurn,
    ScriptedModel,
    ToolCall,
    demo_tools,
    run_agent,
)
from src.foundations.grading import grade_outcome
from src.ingestion.provenance import eligible_as_of, make_observation
from src.observability.telemetry import (
    configure_telemetry,
    extract_trace_context,
    inject_trace_context,
)

REQUEST_SPAN = "POST /decisions"
PRICING_SPAN = "pricing.price_bond"
DECISION_DATE = "2026-09-01"
VERSIONS = {
    "model": "scripted-model",
    "prompt": "capstone-decision-v1",
    "policy": "cedar-local-v1",
    "data": "public-fixtures-2026-08-12-v1",
}
HOPS = ("request", "evidence", "agent", "tool", "policy", "pricing", "evaluation")


@dataclass(frozen=True)
class Stores:
    """Where each layer writes. Separate on purpose: only the id joins them."""

    spans: InMemorySpanExporter
    audit_log: Path
    eval_log: Path
    evidence_log: Path


def _append(path: Path, record: Mapping[str, Any]) -> None:
    with path.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def _read(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def pricing_service(carrier: Mapping[str, str], stores: Stores) -> float:
    """A separate service: its span joins the caller's trace only through the
    carrier, and its audit record carries whichever trace it is in."""
    tracer = trace.get_tracer("pricing-service")
    context = extract_trace_context(carrier)
    with tracer.start_as_current_span(PRICING_SPAN, context=context):
        record_audit_event(
            "pricing-service",
            "SERVICE",
            "price_bond",
            "allowed",
            "Tool",
            log_path=stores.audit_log,
        )
        return 98.7


def run_decision(stores: Stores, *, propagate: bool = True) -> str:
    """Run the fixture decision and return the request's trace id."""
    configure_telemetry()
    tracer = trace.get_tracer("capstone")
    with tracer.start_as_current_span(REQUEST_SPAN):
        trace_id = current_trace_id()

        # Evidence: a public observation, eligible only if it was knowable then.
        observation = make_observation(
            source="FRED",
            series_id="DGS5",
            observation_date="2026-08-28",
            release_date="2026-08-31",
            value=4.1,
            unit="percent",
            vintage="2026-08-31",
            source_url="https://fred.stlouisfed.org/series/DGS5",
        )
        _append(
            stores.evidence_log,
            {
                "trace_id": trace_id,
                "eligible": eligible_as_of(observation, DECISION_DATE),
                **observation,
            },
        )

        # The agent: one governed tool call, audited at the tool boundary.
        result = run_agent(
            "What is the 3-year yield?",
            ScriptedModel(
                [
                    ModelTurn(
                        tool_calls=(
                            ToolCall(
                                "c1", "interpolate_yield", '{"target_tenor_years": 3}'
                            ),
                        )
                    ),
                    ModelTurn(text="The 3-year yield is 4.3%."),
                ]
            ),
            demo_tools(),
            allowed_tools={"interpolate_yield"},
            audit_log=stores.audit_log,
        )

        # A process boundary: context crosses it only if it is carried.
        pricing_service(inject_trace_context() if propagate else {}, stores)

        # Evaluation, with the versions a replay would need.
        grade = grade_outcome(result, must_contain=["4.3%"])
        _append(
            stores.eval_log,
            {
                "trace_id": current_trace_id(),
                "grader": grade.name,
                "must_contain": ["4.3%"],
                "passed": grade.passed,
                "versions": VERSIONS,
            },
        )
    return trace_id


def reconstruct(trace_id: str, stores: Stores) -> dict[str, list[Any]]:
    """Every hop of one decision, found in every store by its trace id alone."""
    spans = [
        s
        for s in stores.spans.get_finished_spans()
        if f"{s.context.trace_id:032x}" == trace_id
    ]
    audit = [r for r in _read(stores.audit_log) if r.get("trace_id") == trace_id]
    return {
        "request": [s.name for s in spans if s.name == REQUEST_SPAN],
        "evidence": [
            r for r in _read(stores.evidence_log) if r["trace_id"] == trace_id
        ],
        "agent": [s.name for s in spans if s.name.startswith("invoke_agent")],
        "tool": [s.name for s in spans if s.name.startswith("execute_tool")],
        "policy": [r for r in audit if r["identity"] != "pricing-service"],
        "pricing": [s.name for s in spans if s.name == PRICING_SPAN]
        + [r for r in audit if r["identity"] == "pricing-service"],
        "evaluation": [r for r in _read(stores.eval_log) if r["trace_id"] == trace_id],
    }


def missing_hops(record: Mapping[str, list[Any]]) -> list[str]:
    """The hops with nothing recorded under the decision's trace id."""
    return [hop for hop in HOPS if not record.get(hop)]
