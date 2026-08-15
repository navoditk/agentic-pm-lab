# Day 21 — Canvas End-to-End PM Workflow

**Status:** Implemented local fixture path; external provider modes remain
explicit setup paths.

## Objective

Make the Portfolio Risk Canvas a reliable starting point for a new learner who
wants to emulate a complete PM AI request from the user interface. The default
exercise must work after local repository setup, without an API key, model
download, AWS account, or cloud spend.

## What runs

The default path is not a synthetic JavaScript-only demo. The Canvas action
starts the provider-neutral runner, which invokes the existing Python
institutional capstone:

```text
Canvas question
  -> run_pm_workflow action
  -> scripts/run_canvas_pm_workflow.py
  -> src/capstone/workflow.py
  -> identity and entitlement
  -> point-in-time checks
  -> cited research fixture
  -> fixed-income validation and scenarios
  -> Devil's Advocate challenge
  -> committee artifact and evaluation
  -> audit event and Canvas evidence panel
```

The Canvas does not duplicate portfolio calculations or committee logic. It
stores the returned evidence envelope and renders it through shared state.

## Execution modes

| Mode | Default? | Provider invoked | Cost behavior | Evidence status |
|---|---:|---|---|---|
| `fixture` | Yes | Deterministic local capstone | Zero model cost; transparent token approximation | Local implementation evidence |
| `local` | No | Not invoked by default | No fallback cost | Blocked until explicitly configured |
| `openai` | No | Not invoked by default | Provider pricing required | Blocked until explicitly configured |
| `anthropic` | No | Not invoked by default | Provider pricing required | Blocked until explicitly configured |
| `aws` | No | Not invoked by default | AWS/model cost required | Blocked until explicitly configured |

The non-fixture modes are visible to teach the provider boundary. They fail
closed rather than silently returning fixture output. Their actual execution
paths remain the existing local-model, hosted-model, and AgentCore experiments,
with credentials, budget, and evidence requirements documented separately.

## Observable evidence envelope

Each fixture run returns:

- deterministic request ID;
- identity, portfolio, question, mode, provider, and decision date;
- ordered stage events;
- component and stage status;
- stage duration in milliseconds;
- active OTel trace ID when one exists;
- structured audit events;
- freshness, provenance, scenario, committee, and evaluation output;
- input, output, and total token estimates;
- token-accounting basis;
- estimated cost, currency, and pricing basis;
- latency;
- approval and order-execution state; and
- explicit model-reasoning privacy status.

The stage trace is operational reasoning evidence: it shows what the system
attempted, which tools and controls were reached, what succeeded or failed,
and what output was produced. It intentionally does not capture private model
chain-of-thought. A future provider adapter should add actual provider usage
metadata and model spans without changing this envelope.

## Token and cost accounting

Fixture mode does not invoke a model, so its cost is exactly `$0.00`. It still
reports nonzero input/output token estimates using a transparent approximation:
serialized characters divided by four, rounded up. This is explicitly labelled
as an estimate and must not be compared directly with provider billing.

For a real provider run, replace the estimate with provider-reported usage:

| Field | Meaning |
|---|---|
| `input_tokens` | Prompt/context tokens sent to the model |
| `output_tokens` | Completion tokens returned by the model |
| `total_tokens` | Sum of input and output tokens |
| `estimated_usd` | Cost derived from model-specific pricing |
| `basis` | Whether usage is provider-reported or estimated |

The existing OpenTelemetry agent instrumentation records these same categories
on agent spans. The Canvas envelope makes the accounting visible to a learner
even when the default run is deterministic.

## Failure and privacy behavior

- Invalid action inputs are rejected by the Canvas schema boundary.
- Runner failures are returned as visible `failed` state with an error type.
- Unconfigured provider modes return `blocked` state with zero tokens and zero
  cost; they never substitute fixture output.
- Authorization, freshness, guardrail, approval, and provider limitations remain
  visible in the returned evidence.
- Private model chain-of-thought is never captured or exposed.
- Structured execution events, tool arguments, outputs, policy decisions,
  citations, retries, latency, and token/cost metadata are the supported audit
  surface.
- Order execution remains disabled.

## Reproduce the workflow without Canvas

The same default workflow can be run from a terminal:

```bash
uv run python scripts/run_canvas_pm_workflow.py \
  --question "What happens if rates rise by 50 bps?" \
  --identity PM_USER \
  --portfolio-id PORT_A \
  --mode fixture \
  --audit-log /tmp/day21-canvas.audit.jsonl
```

The Canvas exercise is therefore a visual entry point over a reproducible
command-line path, not a separate implementation.

## Acceptance evidence

Run:

```bash
node .github/extensions/portfolio-risk-canvas/tests/canvas-capabilities.test.mjs
node .github/extensions/portfolio-risk-canvas/test/smoke.test.mjs
uv run pytest tests/unit/scripts/test_canvas_pm_workflow.py tests/unit/capstone -q
```

For a hosted or AWS comparison, create an experiment under `experiments/` with
the provider, model/version, prompt, token usage, cost basis, latency, trace
link, output, limitations, and cleanup state. Do not promote a fixture result
to live-provider evidence.
