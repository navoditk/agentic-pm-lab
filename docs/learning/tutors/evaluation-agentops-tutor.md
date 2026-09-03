# Evaluations and AgentOps — deep dive

*Companion to [`.github/agents/evaluation-agentops-tutor.agent.md`](../../../.github/agents/evaluation-agentops-tutor.agent.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run python scripts/tutor.py evaluation-agentops-tutor --quiz`.*

## What this actually is

Evaluating an agent is not the same problem as evaluating a function. A
function either returns the right value or it doesn't. An agent can route to
the wrong specialist and still produce a plausible-sounding answer; it can
call the right tool with the wrong argument and still return a number that
looks reasonable; it can give a factually correct answer while violating a
policy it should have refused. A single pass/fail score collapses all of
those into one bit and throws away exactly the information you'd need to fix
the failure. AgentOps is the operational half of the same problem: once you
can score an agent, you need traces to diagnose *why* a run scored badly,
a gate that blocks a regression before it ships, and a way to compare one
model or prompt version against another on the same fixed dataset.

## Core concepts

- **Independent evaluation dimensions.** Scoring routing, tool selection,
  tool arguments, retrieval context, final answer, policy compliance, and
  guardrail behavior as seven separate numbers, not one blended average — so
  a policy failure can't be hidden by a good final answer.
- **Golden dataset.** A fixed, version-controlled set of question/expected-
  answer cases used to regression-test agent behavior the same way a unit
  test suite regression-tests code, except the "expected answer" here is a
  structured contract (expected routing, tools, arguments, facts), not one
  literal string.
- **Fast vs. full subset.** A cheap, small subset (`fast: true` cases) run on
  every PR for quick feedback, and the full dataset run less often (on push
  to `main`) for a fuller regression check — the same tradeoff as a fast unit
  test suite versus a slower integration suite.
- **Baseline and allowed drop.** The last known-good score per dimension,
  plus a tolerance (`allowed_score_drop`) below which a new run is treated as
  a regression rather than noise.
- **Stub case.** A case that is authored and schema-valid but deliberately
  excluded from scoring until it has been validated against a real run — a
  way to grow a dataset without silently changing what a baseline means.
- **Trace / span.** A structured, timestamped record of one step of an
  agent's execution (a tool call, a model invocation, an authorization
  check), with attributes attached — the raw material both evaluation
  scoring and AgentOps diagnosis are built from.

## How this repository implements it

`evals/golden_dataset.jsonl` (and its three companion files —
`routing_cases.jsonl`, `authorization_cases.jsonl`, `guardrail_cases.jsonl`)
hold the cases. Every case has `id`, `domain`, `fast`, `question`, `sources`
(the seven named context inputs from `src/context/builder.py`),
`expected_routing`, `expected_tools`, `important_arguments`,
`required_context_sources`, `forbidden_actions`, and `required_facts`
(substrings a correct answer must contain, not an exact reference string).
`scripts/run_eval.py`'s `load_cases()` reads all four files, skips any case
with `"status": "stub"`, and validates every remaining case against
`REQUIRED_CASE_FIELDS` before it can be scored.

Seven evaluator functions — `routing_evaluator`, `tool_selection_evaluator`,
`tool_arguments_evaluator`, `retrieval_context_evaluator`,
`final_answer_evaluator`, `policy_compliance_evaluator`, and
`guardrail_behavior_evaluator` — each score one dimension independently and
report `None` ("not applicable") rather than a number when a case type
doesn't apply to that dimension. `_policy_case()` and `_guardrail_case()` are
the mechanism: an authorization case (identified by a `policy_probe` input)
short-circuits routing/tool/answer scoring and only gets scored on policy
compliance; a guardrail case (identified by `"dimension":
"guardrail_behavior"`) short-circuits everything except the guardrail
dimension. Both kinds of case are scored *without a model call* —
`predict()` resolves a `policy_probe` case by calling
`src/control/authorization.py`'s `check_tool_permission()`/
`check_portfolio_access()` directly, and resolves a guardrail case by calling
`src/control/guardrails.py`'s `enforce_content()` directly. This is a
recurring pattern worth internalizing: whenever a dimension is backed by a
pure, deterministic function, evaluate it locally instead of paying for a
model call to indirectly re-derive the same yes/no answer.

`config/eval-baseline.json` records the accepted score per dimension for the
`fast` and `full` subsets, plus `allowed_score_drop` (0.1) and the exact
`case_count` each subset should produce. `.github/workflows/eval-regression.yml`
runs `scripts/run_eval.py --subset fast --baseline config/eval-baseline.json`
on every PR and `--subset full` on every push to `main`; `find_regressions()`
fails the run if the observed `case_count` doesn't match the baseline's, or
if any non-null dimension score drops more than `allowed_score_drop` below
its floor.

**A concrete recent example of all of this mattering.** `evals/guardrail_cases.jsonl`'s
Day 14 pass/block cases never actually matched `REQUIRED_CASE_FIELDS` — a
schema regression that made `load_cases()` raise on the *real* `evals/`
directory, silently breaking both `eval-regression.yml` jobs, because every
existing test in `tests/unit/scripts/test_run_eval.py` ran against a
synthetic fixture directory instead of the real one. The fix (see
`PROGRESS.md`'s 2026-09-02 entry) padded the schema, added a real,
deterministic `guardrail_behavior_evaluator` using the `enforce_content()`
pattern above, and corrected `config/eval-baseline.json`'s `full` case_count
from 18 to 22 — a count-only correction, with every existing dimension score
left unchanged and that fact verified in tests rather than asserted in
prose. A new test, `test_real_eval_files_load_without_error`, now calls
`load_cases()` against the actual `evals/` directory specifically so this
class of break can't hide behind a synthetic fixture again. Several new
cases from that same pass are marked `"status": "stub"` — authored,
schema-valid, and grounded in real tool signatures, but not yet scored,
because activating them requires an actual LangSmith + model-provider run
this repository's own discipline won't let you fake with hand-typed numbers.

`src/evals/agentcore_evaluations.py` is the AWS-native comparison path — it
builds a reviewable manifest for an AgentCore Evaluations run but does not
call AWS itself, keeping the local LangSmith evaluator as the trusted
baseline until a live AgentCore run is actually captured. `src/observability/telemetry.py`
is the trace layer underneath both: agent spans carry `gen_ai.usage.input_tokens`/
`output_tokens`, `app.tool.call_count`, `app.retry.count`, and
`app.cost.estimated_usd` attributes, so a slow or expensive run can be
diagnosed from its trace rather than guessed at.

## Worked walkthrough

Trace how one authorization case gets scored without a model call:

1. Read `evals/authorization_cases.jsonl`'s `authorization-pm-user` case and
   its `policy_probe` field.
2. Read `scripts/run_eval.py`'s `predict()` — find the `isinstance(policy_probe, dict)`
   branch and see it calls `role_for_identity()`, `check_tool_permission()`,
   and `check_portfolio_access()` directly, never touching
   `invoke_multi_agent()`.
3. Read `_policy_case()` and see how `routing_evaluator()` (and four other
   evaluators) call it first and return `_not_applicable(...)` immediately —
   confirm this by reading `policy_compliance_evaluator()`, the one evaluator
   that does *not* skip a policy case.
4. Run `uv run python scripts/run_eval.py --validate-only --subset full` and
   confirm the reported case count (22) and that it doesn't crash.
5. Run `uv run pytest tests/unit/scripts/test_run_eval.py -q` and read
   `test_guardrail_case_is_excluded_from_other_dimensions` — it asserts the
   exact same short-circuit behavior for a guardrail case, in one test, with
   no LangSmith or model dependency.

## Common pitfalls

- **Collapsing seven dimensions into one score.** A single averaged number
  can hide a policy-compliance failure behind a good final answer. This
  repository's evaluators are deliberately independent so each dimension
  fails on its own.
- **Lowering a baseline to make a failing run pass.** `allowed_score_drop`
  is a gate, not a negotiable target — a regression should be diagnosed and
  fixed (or the baseline regenerated from a fresh, real, human-reviewed run),
  never hand-edited down to match whatever a bad run happened to produce.
- **Assuming a schema check that isn't exercised is a schema check that
  works.** The guardrail-case break existed for an entire day's worth of
  work because every test used a synthetic fixture instead of the real
  directory. A validation function is only as good as the least-mocked test
  that actually calls it against real data.

## Further reading

- [`docs/reference/REFERENCES.md#langsmith-tracing-datasets-experiments-evaluation`](../reference/REFERENCES.md#langsmith-tracing-datasets-experiments-evaluation)
  and the adjacent [`#opentelemetry-python`](../reference/REFERENCES.md#opentelemetry-python)
  section.
- `skills/eval-dataset-authoring/SKILL.md`'s full golden-case and
  guardrail-case authoring checklist.
- `PROGRESS.md`'s 2026-09-02 entry and `docs/learning/LEARNINGS.md`'s
  matching entry for the full guardrail-evaluator-fix story, including what
  was deliberately left undone (activating stub cases, regenerating a paid
  baseline run).
- `.github/agents/eval-triage-agent.agent.md`, the sibling read-only persona
  for investigating one specific failing run rather than teaching the
  dimension model itself.
