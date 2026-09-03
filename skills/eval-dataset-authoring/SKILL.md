---
name: eval-dataset-authoring
description: Add consistent, executable evaluation cases with explicit routing, tool, argument, context, fact, safety, and answer expectations.
license: MIT
covers:
  - evals
  - scripts/run_eval.py
last_verified_commit: f677d70
---

# eval-dataset-authoring

Use this skill when adding or revising a case in `evals/`. Evaluation cases are
executable product requirements, not example prompts without pass criteria.

## Golden-case checklist

1. Assign a stable `id`, one `domain`, and `fast: true|false`.
2. Include public or invented `sources` sufficient to answer the question.
3. Name every expected specialist in `expected_routing`.
4. Name deterministic tools in `expected_tools` and important argument
   subsets in `important_arguments`. Check the real `@tool(...)` name in
   `src/agents/single_agent.py` and which specialist's tuple in
   `src/agents/multi_agent.py` actually carries it (`MACRO_TOOLS`,
   `QUANT_TOOLS`, `FUNDAMENTAL_TOOLS`) -- `docs/PLAN.md` Appendix C's tool
   names are illustrative planning content, not always the real ones.
5. List named context sources required by the task; exclude irrelevant ones.
6. List `forbidden_actions`, including unsupported calculation or
   recommendation behavior.
7. Write `required_facts` as criteria a correct answer must communicate, not
   an exact reference-answer string. Where feasible, verify the number by
   calling the real `src/analytics/*.py` function directly rather than
   hand-computing it.
8. Keep policy and guardrail cases in their companion files so those
   dimensions fail independently.
9. A case that isn't ready to affect CI (not yet activated, not yet run for
   real, or its dependency just landed) gets `"status": "stub"` --
   `load_cases()` skips it entirely, so it can't silently change
   `config/eval-baseline.json`'s `case_count` or scores. Flipping a case from
   stub to active always requires re-running `scripts/run_eval.py` for real
   and regenerating the baseline alongside it in the same change, never by
   hand-editing the baseline's scores.
10. A guardrail-dimension case (`evals/guardrail_cases.jsonl`) needs the full
    schema in point 1-7 padded with neutral/empty values (mirroring how
    `authorization_cases.jsonl`'s `policy_probe` cases pad theirs), plus
    `"dimension": "guardrail_behavior"` and `"expected": "pass"|"block"`.
    `_guardrail_case()` in `scripts/run_eval.py` then short-circuits every
    other evaluator to not-applicable for it, and `predict()` scores it
    deterministically via `src/control/guardrails.py`'s `enforce_content()`
    -- no model call needed, same as a `policy_probe` case.

Do not add a case for a tool that does not exist yet. Day 12 built
`run_backtest`, `optimize_portfolio`, and `scenario_analysis` -- cases for
those are welcome now (as `stub` until a real run activates them), so this
caveat now only applies to genuinely unbuilt tools.
