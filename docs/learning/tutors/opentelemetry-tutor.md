# OpenTelemetry — deep dive

*Companion to [`agents/opentelemetry-tutor.md`](../../../agents/opentelemetry-tutor.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz opentelemetry-tutor`.*

## What this actually is

OpenTelemetry (OTel) is a vendor-neutral standard for producing traces,
metrics, and logs from an application — a *trace* is the end-to-end record of
one request as it moves through a system, made up of nested *spans*, each
representing one unit of work (an HTTP call, a database query, a tool
invocation) with a start time, a duration, and a set of key/value
*attributes*. The point of instrumenting with OTel rather than ad hoc logging
is that spans compose: a single trace ID can connect a request's authorization
check, its tool calls, its model invocation, and its audit record into one
navigable structure, and because the format is vendor-neutral, the same trace
can be viewed in more than one backend without instrumenting twice.

For an agentic system specifically, tracing matters more than in a typical
web service, because an agent's behavior is comparatively opaque — a single
user question can trigger several nested tool calls and delegate to
sub-agents, and without a trace, "why did it do that" has no answer except
re-reading the conversation. OTel is also where cost and quality tracking
naturally attach: once every model call is a span, token counts, latency, and
estimated dollar cost become span attributes, and evaluation frameworks like
LangSmith can read the same spans rather than requiring a second,
purpose-built instrumentation pass.

## Core concepts

- **Trace and span.** A trace is a tree of spans sharing one trace ID; a span
  is one timed unit of work with attributes and (on error) a recorded
  exception and status.
- **TracerProvider.** The SDK object that actually creates spans and routes
  them to configured exporters. An application should have exactly one, or
  spans from the same logical request end up split across disconnected trees.
- **Span attributes.** Structured key/value metadata on a span — this project
  follows the GenAI semantic-convention namespace (`gen_ai.usage.input_tokens`,
  etc.) where applicable, plus its own `app.*` namespace for things the
  standard doesn't cover (cost, tool argument counts).
- **Exporter.** The component that ships finished spans somewhere — to the
  console, to a collector, or (as here) via OTLP HTTP directly to a backend
  like LangSmith.
- **Metrics, the second signal.** A trace answers "what happened in this one
  request"; a metric answers "what is happening across all of them". They are
  not interchangeable, and span attributes cannot substitute: you cannot
  aggregate over spans you never exported, and at any sampling rate below 1.0
  you are aggregating over a subset without knowing which. A single slow
  trace is an anecdote; a latency histogram is an SLO.
- **Counter vs histogram.** A counter is monotonic and answers "how many" —
  runs, tool calls, tokens, denials. A histogram records a distribution and
  answers "how long, and how long for the slow ones" — the p95 that a mean
  hides. Choosing the wrong instrument is the most common metrics mistake:
  averaging latency throws away exactly the tail you needed.
- **Context propagation.** How a trace ID and span context travel from one
  function call to the next and, across a process boundary, through
  W3C `traceparent` headers — so a downstream service's spans join the
  caller's trace instead of starting a disconnected one. Without it the
  question "which agent request caused this tool call" stops being
  answerable, which is most of the reason for tracing an agent system.
- **Sampling, and why parent-based matters.** Sampling decides which traces
  are exported, to control volume and cost. A `TraceIdRatioBased` sampler
  decides from the trace id alone, deterministically, so one service with
  one ratio never splits a trace. But it "MUST ignore the parent
  `SampledFlag`" ([trace SDK](https://opentelemetry.io/docs/specs/otel/trace/sdk/)),
  so when services sample at different ratios, a trace kept upstream loses
  its spans downstream: holes in the middle, a parent kept and a child
  dropped. `ParentBased` fixes this by making a child follow the decision
  already taken upstream: the ratio applies only at the root, and once a
  trace is in, all of it is in.
- **Privacy in telemetry.** Spans are a second place sensitive data can leak
  if you're not careful — the discipline this project applies is recording
  *counts and metadata*, never raw prompt text, portfolio holdings, or
  credentials, in any span attribute.
- **Span events.** "A Span Event can be thought of as a structured log
  message (or annotation) on a Span, typically used to denote a meaningful,
  singular point in time during the Span's duration." The test for event
  versus attribute is whether the timestamp matters: if it does, use an
  event; if not, an attribute
  ([traces](https://opentelemetry.io/docs/concepts/signals/traces/)). A
  recorded exception is itself an event, named `exception`.
- **Logs, the third signal.** Logs are records you already write, and the
  SDK's logging bridge stamps each one emitted inside a span with that
  span's trace and span ids, so a log line and a trace can be joined. A
  span event lives *inside* one span and is exported with it; a log record
  is its own signal with its own pipeline and retention.
- **Exemplars.** "An exemplar is a recorded value that associates
  OpenTelemetry context to a metric event", so that you can "link Trace
  signals w/ Metrics": a latency histogram's slow bucket carries the trace
  id of a request that landed in it
  ([metrics data model](https://opentelemetry.io/docs/specs/otel/metrics/data-model/)).
  With the SDK's default filter, only measurements taken inside a sampled
  span get one.
- **GenAI semantic conventions.** Agent spans have standard names and kinds
  (status: Development). A model call is `{gen_ai.operation.name}
  {gen_ai.request.model}`, such as `chat claude-haiku`; its "span kind
  SHOULD be `CLIENT` and MAY be set to `INTERNAL` on spans representing call
  to models running in the same process". A tool call is `execute_tool
  {gen_ai.tool.name}`, kind `INTERNAL`. An in-process agent run is an
  `invoke_agent` internal span
  ([GenAI spans](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-spans.md),
  [agent spans](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/gen-ai-agent-spans.md)).
  Message content (`gen_ai.input.messages`, `gen_ai.output.messages`,
  `gen_ai.system_instructions`) is `Opt-In` and flagged as "likely to
  contain sensitive information", which is the convention agreeing with
  this project's privacy rule.
- **Processors and exporters.** A `SimpleSpanProcessor` exports each span
  as it ends; a `BatchSpanProcessor` queues spans and exports them in
  batches, which is what production uses. The SDK flushes the batch when
  the interpreter exits normally, but a process that is killed or exits
  abruptly loses whatever is queued, so a short-lived job should call
  `force_flush()` before it ends.
- **The Collector.** A separate service between applications and backends.
  Receivers "collect telemetry from one or more sources", processors "modify
  or transform it", and exporters "send data to one or more backends". A
  pipeline wires them together, and "the order of the processors in a
  pipeline determines the order of the processing operations". Defining a
  component is not enough: "configuring a receiver does not enable it.
  Receivers are enabled by adding them to the appropriate pipelines within
  the service section"
  ([Collector configuration](https://opentelemetry.io/docs/collector/configuration/)).
  A minimal traces pipeline looks like this:

  ```yaml
  receivers:
    otlp:
      protocols:
        http:
  processors:
    batch:
  exporters:
    otlphttp:
      endpoint: https://backend.example/otlp
  service:
    pipelines:
      traces:
        receivers: [otlp]
        processors: [batch]
        exporters: [otlphttp]
  ```

  This repository exports straight from the SDK to LangSmith over OTLP and
  runs no Collector. A Collector earns its place when several services need
  the same processing, such as redaction, sampling, or fan-out to two
  backends, done once instead of in every application.

## How this repository implements it

`src/observability/telemetry.py` is the single shared instrumentation module,
and it's worth reading in full rather than trusting a summary — every
function here maps to one of the concepts above:

- **`configure_telemetry()`** installs exactly one process-wide
  `TracerProvider`. It's idempotent by design: if a provider already exists
  (module-level `_provider`, or one already installed by something else via
  `trace.get_tracer_provider()`), it reuses it instead of layering a second
  one — this is the concrete mechanism behind "an application should have
  exactly one TracerProvider" above. Every other function in this module
  calls `configure_telemetry()` first, so instrumentation never depends on
  call order.
- **`_configure_langsmith_exporter()`** attaches one `OTLPSpanExporter`
  pointed at LangSmith's `/otel/v1/traces` endpoint, but only when
  `LANGSMITH_TRACING=true`, `LANGSMITH_TRACING_MODE` is `otel` or `hybrid`,
  and an API key is present — and it's also guarded to attach at most once
  (`_langsmith_exporter_configured`). LangSmith is a *view* onto the same OTel
  stream this repository already produces, not a second, parallel tracing
  system.
- **`instrument_fastapi()`** auto-instruments a FastAPI app exactly once,
  guarded by `app.state.otel_instrumented` — the same "idempotent by design"
  pattern as the provider itself.
- **`observe_operation()`** is the context manager behind every non-agent
  span (authorization, audit, identity checks): it always sets
  `app.operation.success` and `app.operation.duration_ms`, on both the
  success and exception paths, via a `try/except/else/finally` block — read
  that block closely, because "always record duration and success, even on
  failure" is exactly what makes traces trustworthy for diagnosing failures,
  not just successes.
- **`traced_analytics()`** is the decorator wrapping every deterministic Tool
  Layer function. It records `app.tool.name`, `app.tool.input.argument_count`,
  and `app.tool.input.item_count` — counts and shapes, never the actual
  argument values — which is the concrete implementation of the "never log
  raw payloads" privacy rule above.
- **`observe_agent_run()`** plus **`OperationalMetricsHandler`** create the
  agent root span and attach GenAI-namespaced attributes:
  `gen_ai.usage.input_tokens`/`output_tokens`, plus `app.tool.call_count`,
  `app.retrieval.call_count`, and `app.retry.count`.
  `OperationalMetricsHandler.apply_to_span()` also computes
  `app.cost.estimated_usd` by looking the model name up in
  `MODEL_PRICES_PER_MILLION_USD` and multiplying by the measured token
  counts — cost tracking is a direct consequence of tokens already being span
  attributes, not a separate accounting system.

### Metrics, propagation and sampling

`src/observability/metrics.py` is the metrics half, deliberately a separate
module from `telemetry.py` because it is a separate OTel signal.
`configure_metrics()` mirrors `configure_telemetry()`'s contract — one
provider, idempotent, yields to one already installed. Its `reader` argument
is the testing seam: pass an `InMemoryMetricReader` and
`tests/unit/observability/test_metrics.py` reads recorded points back out and
asserts on them, rather than asserting a mock was called. That distinction
matters here more than usual, because a mock passes even when the instrument
was never registered with a meter — which is exactly the state this
repository was in when it claimed "traces and metrics" while recording none.

Eight instruments: counters for agent runs, tool calls, tokens, estimated
cost, retries and authorization denials; histograms for agent and tool
duration. Two details are worth copying rather than skimming. Model names are
normalised (`anthropic:claude-x` and `claude-x` collapse to one series) so a
provider prefix cannot silently split a metric in two. And authorization
denials are counted separately from errors, because a denial is the control
layer *working* — a denial rate that suddenly drops to zero is as interesting
as one that spikes, and burying it in an error counter loses that signal.

Recording is wired into the existing instrumentation points rather than
bolted on: `traced_analytics` records a tool call and its duration,
`observe_agent_run` records the run, its token split and its retries. Both
call sites wrap the recording in a `try`/`except` that logs at debug level,
on the principle that instrumentation must never be the reason a bond price
fails to compute.

Denials are wired separately, at the places that actually refuse — the MCP
boundary's identity and portfolio checks, and `enforce_source_access` in the
control layer — each with its own `reason` label, and the role resolved so a
denial rate can be broken down by who was refused. Both import
`record_authorization_denial` *inside* the function rather than at module
scope, so the control layer never takes an import-time dependency on
observability.

Note what that wiring costs to get wrong, because this repository got it
wrong: the counter existed, was tested, and was described in this document
for a while before anything called it. A tested instrument with no call site
reports zero forever, and zero is indistinguishable from "nothing was
refused" — a false all-clear on the control layer. That is why the tests
assert the *call sites* reach the instrument, not merely that the instrument
works when called.

`inject_trace_context()` and `extract_trace_context()` in `telemetry.py` are
the propagation pair — inject before an outbound call, extract on the way in
and pass the result as `context=` when starting the span. A carrier with no
`traceparent` yields a context that simply starts a new trace, so an
uninstrumented caller degrades quietly instead of raising.

`configured_sampler()` reads `OTEL_TRACES_SAMPLER_ARG` and returns
`ParentBased(TraceIdRatioBased(ratio))`. The default with the variable unset
is `ALWAYS_ON`: a repository run locally or in CI keeps every trace, and
sampling is something you opt into when volume makes keeping everything
expensive. An out-of-range or non-numeric value raises rather than falling
back to a default, because silently sampling at a rate you did not choose
means losing traces you believed you had.

### Events, batching, and exemplars: `otel_lab.py`

`src/observability/otel_lab.py` isolates three behaviours with private,
in-memory providers, pinned in `tests/unit/observability/test_otel_lab.py`:

| Behaviour | Test |
|---|---|
| A timestamped event on a span, and an exception recorded as an `exception` event with `ERROR` status | `test_an_exception_on_a_span_becomes_an_exception_event` |
| A batch processor exports nothing until flushed | `test_a_batch_processor_exports_nothing_until_it_is_flushed` |
| Batched spans survive a normal exit, not an abrupt one | `test_batched_spans_survive_a_normal_exit_but_not_an_abrupt_one` |
| A histogram measurement inside a span carries that trace as an exemplar; one outside a span does not | `test_an_exemplar_links_a_measurement_to_the_active_trace` |

The GenAI span kinds are pinned where the spans are made: the Agent
foundations loop's spans are all `INTERNAL`, because its scripted model runs
in-process (`test_spans_follow_the_genai_conventions_and_nest_under_the_run`),
and the Bedrock course's chat span is `CLIENT`, because the model is remote
(`test_the_chat_span_records_bedrock_usage_by_the_genai_conventions`).

## The four threads

This course *is* the observability thread; the table shows how it serves the
other three.

| Thread | Where OpenTelemetry carries it | Evidence |
|---|---|---|
| **Observability** | Spans for one request, metrics for all of them, exemplars to get from a slow bucket to a trace, and events for the moments inside a span. | `test_an_exemplar_links_a_measurement_to_the_active_trace` |
| **Traceability** | The trace id is the join key: audit records carry it, `traceparent` carries it across processes, and logs and exemplars carry it into the other signals. A span lost from an unflushed batch is a hole in that record. | `test_batched_spans_survive_a_normal_exit_but_not_an_abrupt_one` |
| **Governance** | Telemetry records decisions but never makes them, and it must not leak what the controls protect: counts, not content, and GenAI message content only by explicit opt-in. | `observe_operation()` in `src/control/authorization.py`; the privacy pitfall below |
| **Evaluation** | Evaluators such as LangSmith read the same spans rather than a second instrumentation, and denial and error rates are metrics a regression gate can hold. | `docs/learning/observability-evaluation.md` |

## Worked walkthrough

Trace one authorization decision end to end:

1. Read `observe_operation()`'s signature and its `try/except/else/finally`
   block in `src/observability/telemetry.py`.
2. Find a call site: `src/control/authorization.py`'s `check_tool_permission()`
   wraps its Cedar decision in `observe_operation("control.check_tool_permission", "authorization", {...})`.
3. Run the authorization test suite with tracing configured locally
   (`uv run pytest tests/unit/control/test_role_gating.py -q`) and note that
   every allowed/denied decision in that suite carries a 32-character OTel
   trace ID, per `docs/architecture/ARCHITECTURE.md`'s Security Model section.
4. Compare that span's attributes against what `traced_analytics()` records
   for a Tool Layer call, and against what `observe_agent_run()` records for
   a full agent invocation — three different span shapes for three different
   kinds of operation, all created through the same single `TracerProvider`.
5. Set `LANGSMITH_TRACING=true` with a real `LANGSMITH_API_KEY` (see
   `docs/guides/RUNBOOK.md`) and re-run a golden-dataset case through
   `scripts/run_eval.py` to see the same spans land in LangSmith as an
   experiment run, not a second, separately-instrumented path.
6. Run the signal tests:
   ```bash
   uv run pytest tests/unit/observability/test_otel_lab.py -q
   ```
   Before reading `test_an_exemplar_links_a_measurement_to_the_active_trace`,
   predict how many exemplars the histogram point has, and why.
7. Write the Collector pipeline that receives OTLP, drops any span attribute
   named `portfolio.holdings`, batches, and exports to two backends. Say
   which part of it would silently do nothing if you only defined it.

## Common pitfalls

- **Logging the full prompt and portfolio holdings into a span "to make
  debugging easier."** This is explicitly rejected: `traced_analytics()`
  only ever records counts (`argument_count`, `item_count`), never raw
  values, and the same discipline applies to every other span in this
  module. A trace that leaks sensitive data defeats the entire purpose of
  keeping the sensitive data inside the governed tool boundary in the first
  place.
- **Standing up a second, unrelated tracing system per agent or per team.**
  `configure_telemetry()`'s single-provider guarantee exists precisely so
  every span, regardless of which part of the system produced it, lands in
  one correlated stream — a second tracer provider means two disconnected
  trees for what should be one trace.
- **Treating a trace ID as a form of authorization.** A span attribute is
  observability metadata, not an access-control decision. The boundary that
  actually decides "may this identity do this" is `src/control/authorization.py`
  and the Cedar policies it evaluates — a trace can *record* that decision
  after the fact, but it never makes it.
- **Using a span attribute for a moment in time.** If *when* something
  happened matters, such as the curve finishing loading, record an event.
  An attribute has no timestamp of its own.
- **A short-lived job that never flushes.** A batch processor holds spans
  until its next export. A normal exit flushes it; a killed or abruptly
  exited process loses the batch. Call `force_flush()` before the job ends.
- **Defining a Collector component and expecting it to run.** A receiver,
  processor, or exporter does nothing until a pipeline in `service` lists
  it.
- **Turning on GenAI content capture by default.** Message content is
  opt-in in the conventions for the same reason this project records counts:
  it is likely to hold sensitive data.

## Further reading

- [`docs/reference/REFERENCES.md#opentelemetry-python`](../../reference/REFERENCES.md#opentelemetry-python)
  for the official Python SDK docs and semantic-convention references.
- [`docs/learning/observability-evaluation.md`](../observability-evaluation.md)
  for the accepted baseline scores tied to this telemetry and how they were
  derived.
- [`docs/architecture/ARCHITECTURE.md`](../../architecture/ARCHITECTURE.md)'s
  "Observability and evaluation" section for how this module's spans feed
  both the local view and the LangSmith-backed evaluation pipeline
  `evaluation-agentops-tutor` covers in depth.
- `docs/architecture/ARCHITECTURE.md`'s Observability row for how the future
  AgentCore/CloudWatch export path (`aws-agentcore-tutor`) extends this same
  stream rather than replacing it.
