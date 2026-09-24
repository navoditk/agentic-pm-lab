# Capstone: traceability end to end — deep dive

*Companion to [`agents/traceability-capstone-tutor.md`](../../../agents/traceability-capstone-tutor.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz traceability-capstone-tutor`.*

This capstone comes after the Agent core module and assumes all of it. It
does not introduce a new layer. It asks one question of the layers you have
built: given a single trace id, can you show what was asked, what was
allowed, what ran, on what evidence, and how the result was judged? A model
risk reviewer, an auditor, or you at 3 a.m. will ask exactly that, and the
answer is either a record you can rebuild or a story you cannot check.

## What this actually is

Every Agent core course added a thread: spans in OpenTelemetry, audit records
at the tool boundary, evaluation records in the Evaluations course, and
point-in-time evidence in the provenance work. Each writes to its own store,
with its own retention, owned by a different part of the system. Nothing
joins them except an identifier they all carry. Traceability is the
discipline of making sure that identifier is present at every hop, so that
the stores can be read together after the fact.

OpenTelemetry states the mechanism directly: "with context propagation,
signals (traces, metrics, and logs) can be correlated with each other,
regardless of where they are generated", and "the default propagator uses
the headers specified by the W3C TraceContext specification"
([context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)).
W3C Trace Context defines the `traceparent` header whose trace-id identifies
"the whole trace" ([Trace Context](https://www.w3.org/TR/trace-context/)).

## Core concepts

- **Trace correlation.** One trace id, present on the request span, every
  model and tool span, every audit record, the evaluation record, and the
  evidence record. Correlation is a property of the *weakest* hop: one
  record without the id breaks the chain at that point.
- **Context propagation.** Inside a process, the active span carries the
  context and records pick it up, as `record_audit_event` does. Across a
  process boundary it survives only if the caller injects it into the
  request (`traceparent`) and the receiver extracts it. Otherwise the
  receiver starts a new trace, and its work is recorded but orphaned.
- **Audit records.** What was decided, by which control, for which
  identity, on which resource, and under which trace id. Not the data
  itself: counts and identifiers, never holdings or prompts.
- **Provenance.** Which source, which series, which vintage, released when,
  and whether it was knowable at the decision date. A decision is only as
  reconstructable as its evidence.
- **Lineage.** The chain from inputs through each transformation to the
  output. In an agent, the trace is the lineage of one decision: the tool
  calls are the transformations, and the evidence records are the inputs.
- **Replay.** Rebuilding a decision is not the same as re-running it. A
  re-run needs the versions that produced the original: model, prompt,
  policy, and data. Without them a re-run answers a different question.

## How this repository implements it

`src/capstone/trace_lab.py` runs one fixture decision through every layer,
each writing to its own store:

| Hop | Store | What it records |
|---|---|---|
| Request | spans | `POST /decisions`, the root |
| Evidence | evidence log | FRED `DGS5`, its release date, and whether it was eligible at the decision date |
| Agent | spans | `invoke_agent`, from the Agent foundations loop |
| Tool | spans | `execute_tool interpolate_yield` |
| Policy | audit log | the tool boundary's `allowed` decision |
| Pricing | spans and audit log | a separate service, joined by `traceparent` |
| Evaluation | evaluation log | the outcome grade, and the model, prompt, policy, and data versions |

`reconstruct(trace_id, stores)` takes nothing but the id and finds each hop
in its store; `missing_hops()` names any hop with nothing under that id.
`tests/unit/capstone/test_trace_lab.py` holds the acceptance test:

| What the test shows | Test |
|---|---|
| The whole decision is rebuilt from one trace id, with no missing hop | `test_a_fixture_decision_is_reconstructable_from_one_trace_id` |
| The evaluation record carries the versions a replay would need | `test_the_evaluation_record_carries_the_versions_a_replay_needs` |
| Skip propagation to the pricing service and exactly that hop goes missing; its span and audit record exist under a different trace | `test_dropping_the_context_at_one_hop_leaves_a_gap_and_orphans` |

The last test is the capstone in one assertion. Nothing failed: the pricing
service ran, priced the bond, and wrote its audit record. The decision just
cannot prove it happened, because the one field that would join the records
is different.

## The four threads

The capstone is where the four threads meet.

| Thread | In the capstone | Evidence |
|---|---|---|
| **Observability** | Spans supply the request, agent, tool, and pricing hops, and the trace id every other store copies. | `reconstruct()` reads the span exporter |
| **Traceability** | One id joins four stores; one hop without it is a gap, and the records on the other side are orphans. | `test_dropping_the_context_at_one_hop_leaves_a_gap_and_orphans` |
| **Governance** | The policy hop is the audit record of the tool boundary's decision; a decision whose controls cannot be shown to have run has not been governed as far as anyone can prove. | the `policy` hop in `reconstruct()` |
| **Evaluation** | The evaluation record is part of the decision's history, and its versions make a replay answer the same question. | `test_the_evaluation_record_carries_the_versions_a_replay_needs` |

## Worked walkthrough

1. Run the acceptance test:
   ```bash
   uv run pytest tests/unit/capstone/test_trace_lab.py -q
   ```
2. Read `run_decision()` and, for each hop in the table above, point to the
   line that writes it and the line that puts the trace id on it.
3. Read `test_dropping_the_context_at_one_hop_leaves_a_gap_and_orphans`.
   Before reading the asserts, predict which hop goes missing and what
   `reconstruct()` returns for the orphan's trace id.
4. Change `run_decision()` so the evaluation record is written *after* the
   request span ends. Predict what happens to its trace id, run the test,
   and explain the failure.
5. Answer, from the stores alone: which policy allowed the tool call, which
   data vintage the decision relied on, and which prompt version produced
   the answer.

## Common pitfalls

- **A record written outside the span.** Anything recorded after the
  request span ends, or on a background thread without the context, gets
  no trace id or a different one. The work happened; the proof did not.
- **Propagating on the way out and not reading on the way in.** Injecting
  `traceparent` does nothing if the receiving service starts a fresh span
  instead of extracting it.
- **Logging content to make records "complete".** Reconstruction needs
  identifiers and decisions, not holdings or prompts. A complete audit
  trail of sensitive data is a second breach surface.
- **Rebuilding without versions.** A re-run under today's model, prompt, or
  policy is a new decision, not a replay of the old one.
- **Sampling away the evidence.** A sampled-out trace has no spans to
  rebuild from. Keep audit and evaluation records regardless of sampling,
  and sample with `ParentBased` so a kept trace is complete.

## Further reading

- [`docs/reference/REFERENCES.md#traceability-capstone`](../../reference/REFERENCES.md#traceability-capstone)
- The OpenTelemetry course, for propagation and sampling; the Governance
  course, for what an audit record must contain; the Evaluations course, for
  what makes an evaluation record trustworthy.
- `src/capstone/workflow.py`, the Day 20 institutional capstone, which records
  versions and trace ids for every stage of a larger decision.
