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
  are exported, to control volume and cost. Naive per-span ratio sampling
  produces traces with holes in the middle — a parent kept, a child dropped,
  an incoherent tree. `ParentBased` fixes this by making a child follow the
  decision already taken upstream: the ratio applies only at the root, and
  once a trace is in, all of it is in.
- **Privacy in telemetry.** Spans are a second place sensitive data can leak
  if you're not careful — the discipline this project applies is recording
  *counts and metadata*, never raw prompt text, portfolio holdings, or
  credentials, in any span attribute.

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
