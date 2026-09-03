# Topic depth path

This is the no-cost route from “I can describe the component” to “I can
explain its trade-offs, inspect its implementation, test its failure modes, and
teach it to someone else.” It complements the 21-day build plan; it does not
claim that a tutor or a quiz creates production expertise.

Use [`TUTOR_COURSE_GUIDE.md`](TUTOR_COURSE_GUIDE.md) for the complete course
sequence and `uv run python scripts/tutor.py <topic-id> --course` for the
topic-specific syllabus.

## The four-pass method

For every topic, complete these passes in order:

1. **Orient:** read the linked tutor deep dive and the named official starting
   references. Write down the vocabulary, purpose, boundaries, and one design
   trade-off.
2. **Trace:** follow one request through the repository implementation and its
   tests. Identify inputs, state, outputs, errors, and evidence artifacts.
3. **Break:** run or author a local adversarial case: stale data, bad input,
   unauthorized access, provider failure, prompt injection, or an incomplete
   answer. Record the expected safe behavior.
4. **Teach:** explain the topic without the repository, then map the explanation
   back to two files and one limitation. Take the quiz only after the teach-back.

All exercises below use fixtures, mocks, or local code. They do not require an
AWS account, paid model, live provider, or hosted Canvas session.

## Study matrix

| Topic | Trace in the repo | Depth exercise | Completion evidence |
|---|---|---|---|
| FICC and fixed income | `src/analytics/pricers.py`, `curves.py`, `risk.py`, `src/ingestion/fixed_income.py` | Derive a bond price, duration/DV01, and parallel versus curve-shape shock; identify missing terms that require `needs_review` | Worked calculation, assumptions, glossary links, quiz |
| Portfolio construction | `src/analytics/optimizer.py`, `portfolio.py`, optimizer tests | Compare minimum volatility, maximum Sharpe, and risk parity; perturb covariance and explain instability | Allocation table, constraints, sensitivity note, quiz |
| LangGraph/Deep Agents | `src/agents/single_agent.py`, `multi_agent.py`, `recovery.py` | Trace delegation, checkpoint/resume, retry, dead-letter, and human interrupt paths; inject a specialist failure | State diagram, failure test, teach-back |
| Agent architecture | `src/context/builder.py`, `src/agents/`, `docs/architecture/ARCHITECTURE.md` | Design a bounded context budget and explain what must stay out of prompts and traces | Context inventory, threat review, quiz |
| AWS AgentCore | `src/runtime/agentcore_app.py`, `config/agentcore.yaml`, AWS runbooks | Map Runtime, Gateway, Identity, Policy, Memory, Evaluations, and Guardrails to local equivalents; classify evidence as intent, deployment, or request success | Mapping table, teardown checklist, evidence classification |
| OpenTelemetry | `src/observability/telemetry.py`, `docs/learning/tutors/opentelemetry-tutor.md` | Trace one API request through authorization, analytics, audit, and agent spans; design privacy-safe attributes | Trace sketch, redaction review, local test |
| LangSmith and evaluation | `scripts/run_eval.py`, `evals/`, `config/eval-baseline.json` | Add one case with independent routing, tool, argument, answer, and policy criteria; explain why one aggregate score is insufficient | Case, evaluator output, regression decision |
| Data provenance | `src/ingestion/provenance.py`, `governed_public.py`, `src/research/` | Construct two vintages and decide which is eligible at a historical decision time | Eligibility table, stale/conflict case, quiz |
| MCP and Canvas | `src/mcp_server/server.py`, `.github/extensions/`, Canvas exercises | Show that UI state, MCP metadata, and tool enforcement cannot bypass authorization | Sequence diagram, negative test, evidence boundary |
| Governance and security | `src/control/`, `governance/policies/`, `tests/unit/control/` | Attempt role spoofing, portfolio bypass, output exfiltration, and a write-shaped read; explain each denial layer | Threat table, passing negative tests |
| Investment committee | `src/agents/devils_advocate.py`, `src/capstone/workflow.py` | Produce a thesis, dissent, open questions, evidence grades, and approval decision from fixtures | Decision record with uncertainty and dissent |
| Public investment data | `src/ingestion/public_investment.py`, `data/samples/public_investment/` | Compare SEC, ALFRED, Treasury, SOFR, CFTC, and factor records by publication time, licensing, and decision use | Source cards, provenance comparison, quiz |
| Document-to-skill | `docs/learning/tutors/document-to-skill-tutor.md`, skill packages | Turn a public formula into a cited candidate skill, then reject ambiguous or untested executable code | Document map, source-derived test vector, review status |
| Delivery and AgentOps | `.github/workflows/`, `experiments/`, AgentOps Canvas | Classify a failure as code, data, provider, policy, model, or evidence failure and choose the recovery path | Incident note, replay artifact, promotion decision |

## A no-cost capstone

Use the fixture Canvas-to-capstone path with a synthetic rates-and-credit
question. Before running it, predict the stages, tools, policy decisions,
approval state, evidence records, and failure behavior. Afterward, compare the
prediction with the structured execution envelope. Then deliberately alter one
fixture to be stale, unauthorized, contradictory, or incomplete and repeat the
run.

Useful commands are documented in [`RUNBOOK.md`](../guides/RUNBOOK.md) and
[`CANVAS_EXERCISES.md`](../guides/CANVAS_EXERCISES.md). Record the result in a
small markdown note or issue; do not treat a successful fixture run as live
provider or AWS evidence.

For a compact command-line version of the rates, provenance, and evidence
exercise, run:

```bash
uv run python scripts/run_depth_exercise.py --pretty
```

The command is deterministic and offline. It demonstrates duration/DV01,
key-rate DV01, point-in-time eligibility, citation completeness, abstention,
and contradiction-aware evidence checks in one inspectable JSON envelope.

## What “deep enough” means here

A topic is locally mastered when the learner can:

- define the main concepts and distinguish adjacent concepts;
- trace the repository's implementation and name its simplifications;
- reproduce one result from inputs and assumptions;
- predict and test at least one failure or adversarial path;
- explain what evidence would be required for a live or production claim; and
- teach the trade-off without relying on a vendor slogan or a single score.

For current external APIs, always re-check the official documentation linked in
[`REFERENCES.md`](../reference/REFERENCES.md). The repository's code and
fixtures are the local ground truth; references explain the external systems,
not what this repository has actually proven.
