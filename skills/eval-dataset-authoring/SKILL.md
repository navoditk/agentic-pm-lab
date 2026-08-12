---
name: eval-dataset-authoring
description: Add consistent, executable evaluation cases with explicit routing, tool, argument, context, fact, safety, and answer expectations.
license: MIT
covers:
  - evals
  - scripts/run_eval.py
last_verified_commit: e768274
---

# eval-dataset-authoring

Use this skill when adding or revising a case in `evals/`. Evaluation cases are
executable product requirements, not example prompts without pass criteria.

## Golden-case checklist

1. Assign a stable `id`, one `domain`, and `fast: true|false`.
2. Include public or invented `sources` sufficient to answer the question.
3. Name every expected specialist in `expected_routing`.
4. Name deterministic tools in `expected_tools` and important argument
   subsets in `important_arguments`.
5. List named context sources required by the task; exclude irrelevant ones.
6. List `forbidden_actions`, including unsupported calculation or
   recommendation behavior.
7. Write `required_facts` as criteria a correct answer must communicate, not
   an exact reference-answer string.
8. Keep policy and guardrail cases in their companion files so those
   dimensions fail independently.

Do not add a case for a tool that does not exist yet. Day 12 optimization and
scenario-engine cases remain in the plan until their deterministic engines are
implemented.
