# Evaluations and AgentOps — deep dive

*Companion to [`agents/evaluation-agentops-tutor.md`](../../../agents/evaluation-agentops-tutor.md). Read that first for the fast orientation; this document goes further. Self-check with `uv run agentic-pm-lab quiz evaluation-agentops-tutor`.*

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
- **Evaluator types.** Code-based graders (substring, schema, exact value)
  are fast, cheap, and reproducible, and blind to nuance. Model-based
  graders read nuance and bring their own biases. Human review is the
  reference both are calibrated against, and the slowest.
- **Outcome versus trajectory.** Anthropic's
  [agent-evals guide](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
  advises grading "what the agent produced, not the path it took", because a
  fixed tool sequence fails valid alternatives. The path is still graded
  where it is a *requirement*: a forbidden tool never executed, a call
  budget held, every record traceable. `src/foundations/grading.py` is that
  split in code.
- **Repeated trials.** An agent is non-deterministic, so one run per task
  measures luck along with skill. pass@k "measures the likelihood that an
  agent gets at least one correct solution in k attempts"; pass^k "measures
  the probability that all k trials succeed". They agree at k=1 and then
  diverge. Which one you report depends on the product: a tool a person
  retries until it works is judged by pass@k, an unattended job that must
  work every time by pass^k.
- **Offline versus online.** Offline evaluation runs a fixed dataset before
  release: fast, repeatable, and able to block a change, but it only knows
  the cases someone wrote. Production monitoring "reveals real user
  behavior at scale" but is "reactive; problems reach users before you know
  about them". You need both, and online failures are where new offline
  cases come from.

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

### The judgement the harness cannot encode

Everything above is machinery. This section is the part that stays your job,
and it is where most evaluation setups quietly go wrong.

**This repository scores answers by substring matching.** Read
`final_answer_evaluator` in `scripts/run_eval.py`: it lowercases the answer
and checks that each `required_facts` entry appears in it. That is
deterministic, free, and reproducible — genuine virtues, and the reason it is
the default here. It is also wrong in both directions. An answer saying
"duration is 8.2 years" fails a required fact written as "8.2 years
duration". An answer that states the right number and then draws the opposite
conclusion passes, because the substring is present. Knowing *which* kind of
wrong your evaluator is, is more useful than its score.

**LLM-as-a-judge** is the usual answer to that, and it brings its own
failure modes rather than removing them:

- *Position bias* — a judge comparing two answers tends to favour one for
  its position. Zheng et al.'s
  [conservative fix](https://arxiv.org/abs/2306.05685) is to "call a judge
  twice by swapping the order of two answers and only declare a win when an
  answer is preferred in both orders", and to call it a tie otherwise.
  Randomising the order hides the bias in the noise; swapping measures it.
- *Verbosity bias* — longer answers score higher for the same content, so a
  judge rewards padding unless the rubric penalises it explicitly.
- *Self-preference* — a judge scores text from its own model family more
  generously, which matters when the judge and the system share a provider.
- *Non-reproducibility* — the judge is itself a model. Your baseline moves
  when the judge version changes, and nothing in the diff will say so. Pin
  the judge model in the baseline alongside the system model, the way
  `config/eval-baseline.json` already pins `model`.

If you adopt one, **the rubric is the artifact**, not the prompt. A rubric
that says "rate helpfulness 1-5" produces confident noise. One that says
"score 0 unless the answer states the assumption, the units, and one
limitation" produces something two people would agree on — which is the only
useful test of a rubric.

**Calibrate before you trust it.** Anthropic's guide says model graders
"should be frequently calibrated against expert human judgment". Label a
sample by hand, run the judge on it, and measure agreement, but not raw
agreement alone. On a set where 90% of answers are good, a judge that passes
everything agrees with you 90% of the time and has learned nothing. Cohen's
kappa, (p_o − p_e) / (1 − p_e), subtracts the agreement chance would give
([Cohen's kappa](https://en.wikipedia.org/wiki/Cohen%27s_kappa)): that
always-pass judge scores exactly 0.

### Calibration and repeated trials: `judge_lab.py`

`src/evaluation/judge_lab.py` holds the arithmetic and protocols above with
scripted judges, pinned in `tests/unit/evaluation/test_judge_lab.py`:

| Idea | Test |
|---|---|
| Raw agreement flatters an always-pass judge (90%) that kappa scores 0 | `test_raw_agreement_flatters_a_judge_that_always_says_pass` |
| A judge with the same 90% agreement but real signal scores kappa 0.44 | `test_kappa_credits_agreement_beyond_chance` |
| Swapping the order turns a position-biased judge's wins into ties | `test_swapping_the_order_exposes_a_position_biased_judge` |
| pass@k and pass^k agree at k=1 (0.8) and diverge at k=3 (0.992 against 0.512) | `test_pass_at_k_and_pass_hat_k_agree_at_one_and_diverge_after` |
| Two agents with the same pass@1 rank in opposite orders on pass@3 and pass^3 | `test_the_same_mean_success_rate_can_hide_opposite_reliability` |

The last test is the one to remember. A steady agent that succeeds four times
in five on every task, and a split agent that always solves eight tasks and
never solves two, both score 0.8 on pass@1. Retries rescue the steady agent
and cannot rescue a task that never works, so it wins on pass@3. Requiring
every run to succeed punishes its flakiness, so it loses on pass^3. A single
number hid which agent you have.

**Sample size, arithmetically.** `config/eval-baseline.json` sets
`allowed_score_drop` to 0.1, and the subsets hold 22 active cases (`full`)
and 7 (`fast`). So:

| Subset | Cases | One case is worth | Trips the 10% tolerance? |
|---|---|---|---|
| `full` | 22 | 4.5% | no — it takes 3 flipping (13.6%) |
| `fast` | 7 | 14.3% | **yes — a single case** |

That is worth sitting with. On the fast subset, one case changing behaviour
is indistinguishable from a real regression, because it exceeds the
tolerance on its own. On the full subset, two cases can flip without anything
being reported. Neither is a bug — it is what those numbers mean, and you
cannot reason about a red or green run without doing this arithmetic first.

**So when is a move noise?** With a deterministic evaluator and a fixed
model, it usually is not: the same inputs give the same score, and a change
means something actually changed. The moment any non-determinism enters —
a real model call, a judge, a live data source — a single-case move on a
small subset tells you almost nothing on its own. Re-run before believing it,
and treat "the score moved" and "the system got worse" as two different
claims until you have evidence for the second.

## The four threads

This course *is* the evaluation thread; the table shows how it rests on the
other three.

| Thread | In evaluation | Evidence |
|---|---|---|
| **Observability** | Evaluators read the same spans the system emits, and online evaluation is monitoring: a denial or error rate is a production eval with no dataset. | `docs/learning/observability-evaluation.md` |
| **Traceability** | A failed case is only diagnosable if its trace and audit records can be found from it; the trajectory graders check that every record carries the run's trace id. | `grade_traceable` in `src/foundations/grading.py` |
| **Governance** | Policy compliance is its own dimension, scored from the control layer without a model, so a good answer can never average away a policy failure. | `_policy_case()` in `scripts/run_eval.py` |
| **Evaluation** | Calibrated graders, enough trials to separate skill from luck, and a gate whose tolerance you have done the arithmetic on. | `tests/unit/evaluation/test_judge_lab.py` |

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
6. Run `uv run pytest tests/unit/evaluation/test_judge_lab.py -q`. Before
   reading `test_kappa_credits_agreement_beyond_chance`, compute kappa for
   its labels by hand: observed agreement, chance agreement, then the
   formula.
7. For the golden dataset's portfolio-risk questions, decide whether pass@k
   or pass^k is the right headline, and how many trials you would need
   before a one-case move means anything.

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
- **Trusting a judge because its agreement looks high.** Check kappa, not
  raw agreement, on a hand-labelled sample where one label dominates.
- **Comparing two answers once.** Swap the order and require the same
  winner; a judge that flips is telling you about position, not quality.
- **Reporting one run per task.** A non-deterministic agent needs repeated
  trials, and the headline must say whether it is pass@k or pass^k.
- **Treating offline evaluation as the finish line.** It only knows the
  cases someone wrote; production monitoring finds the rest.

## Further reading

- [`docs/reference/REFERENCES.md#langsmith-tracing-datasets-experiments-evaluation`](../../reference/REFERENCES.md#langsmith-tracing-datasets-experiments-evaluation)
  and the adjacent [`#opentelemetry-python`](../../reference/REFERENCES.md#opentelemetry-python)
  section.
- `skills/eval-dataset-authoring/SKILL.md`'s full golden-case and
  guardrail-case authoring checklist.
- `PROGRESS.md`'s 2026-09-02 entry and `docs/learning/LEARNINGS.md`'s
  matching entry for the full guardrail-evaluator-fix story, including what
  was deliberately left undone (activating stub cases, regenerating a paid
  baseline run).
- `agents/eval-triage-agent.md`, the sibling read-only persona
  for investigating one specific failing run rather than teaching the
  dimension model itself.
