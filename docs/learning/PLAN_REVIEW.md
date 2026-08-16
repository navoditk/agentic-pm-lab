# 21-day plan completion audit

Reviewed 2026-08-16 UTC against `docs/PLAN.md`, `PROGRESS.md`, the repository
implementation, `docs/EVIDENCE.md`, the Day 21 Canvas workflow, and the dated
experiment records. The Day 21 Canvas workflow is part of the canonical plan;
its provider-neutral fixture acceptance is complete while live provider
evidence remains separately labelled.

## Bottom line

The 21-day local learning plan is complete. The stronger interpretation,
“every planned provider, AWS service, browser surface, and end-to-end hosted
workflow has live evidence,” is not complete. `PROGRESS.md` intentionally marks
the local slices complete while its narrative and `docs/EVIDENCE.md` preserve
the live gaps.

This distinction is correct and should remain the project's completion rule:

```text
local implementation + deterministic tests != live provider/cloud evidence
deployment READY != successful request execution
mock fixture != production data or provider availability
```

## Day-by-day audit

| Day | Local slice | Live/evidence status | Assessment |
|---|---|---|---|
| 1 | Walking skeleton, CI, progress tracking, docs | [Learning Project](https://github.com/users/navoditk/projects/2) configured with roadmap, views, and saved browser evidence | Complete for learning scope |
| 2 | Public-data adapters and provenance-aware DuckDB path | [Bounded ALFRED/Treasury/SEC capture](../../experiments/runs/2026-08-16-live-public-data-004/) completed | Local complete; live high-feasibility capture evidenced |
| 3 | Deterministic pricing, risk, optimization, contracts, and tool boundary | No production data or hosted tool boundary claimed | Local complete |
| 4 | Single Deep Agent, skills, context, local-model comparison | OpenAI smoke evidence exists; local Qwen limitation recorded | Complete for learning scope |
| 5 | Multi-agent orchestration, retries, dead letters, checkpoint/resume | Provider-dependent hosted replay is not a release gate | Complete for learning scope |
| 6 | OTel, LangSmith runner, golden dataset, evaluators | AgentCore runtime logs and namespace metrics captured; hosted ADOT/OTel span export and paid LangSmith reruns remain optional | Local/eval complete; runtime metrics evidenced |
| 7 | AuthN/AuthZ, Cedar, guardrails, human approval, adversarial tests | No managed authorization service claimed | Local complete |
| 8 | Kanban and issue-triage Canvas foundations | Interactive Copilot browser/screenshot evidence remains unclaimed; browser connector unavailable on 2026-08-16 | Local complete; hosted follow-up |
| 9 | Agent Operations Canvas and run history | Live LangSmith path requires credentials | Local complete; live follow-up |
| 10 | Governed MCP boundary and Portfolio/Risk Canvas | Visual Copilot/browser evidence remains unclaimed; local capability and smoke tests pass | Local complete; hosted follow-up |
| 11 | Runtime, automation, prompts, CI, runbooks | Scheduled morning-brief workflow, artifact upload, and review issue verified; native Copilot automation evidence remains unclaimed | Local and scheduled-workflow complete; Copilot follow-up |
| 12 | Scenario engine, optimization, AgentCore intent and entrypoint | Runtime/endpoint reached `READY`; successful hosted counterpart invocation, CloudWatch stages, usage, cost, and teardown; no Gateway | Local complete; hosted counterpart live-complete; full hosted capstone/Gateway follow-up |
| 13 | Memory boundaries and evaluation manifest | Live semantic Memory retrieval and scored on-demand Evaluation fixture captured; hosted-runtime span collection remains optional | Local complete; AWS control/data paths evidenced |
| 14 | Guardrail logic, cases, evaluation dimensions | Live standalone Bedrock Guardrail pass/block proof captured; managed attachment remains optional | Local complete; standalone AWS proof complete |
| 15 | Point-in-time provenance and bond metadata | Live ALFRED vintage and Treasury daily yield-curve capture evidenced; TRACE/OpenBB remain unclaimed | Local complete; high-feasibility provider evidence complete |
| 16 | SEC metadata, citations, document-to-skill foundation | Live SEC submissions and Company Facts metadata capture evidenced; full filing-text path remains separate | Local complete; metadata evidence complete |
| 17 | Research specialists, fixed-income branch, mocked provider adapter | No live provider or successful AgentCore research run | Local complete; live AWS/provider incomplete |
| 18 | Independent Devil's Advocate and committee challenge | Semantic truth and production liquidity analysis remain limited | Local complete with explicit limitations |
| 19 | AgentOps Canvas, SLO/promotion/degraded-provider/replay controls | Canvas loopback/capability tests pass; hosted AgentCore runtime metrics and logs evidenced; Copilot-hosted visual capture remains unclaimed | Local complete; hosted observability evidence complete |
| 20 | Institutional PM capstone replay and release evidence structure | Local full replay complete; hosted AgentCore counterpart completed, but the deployed proof slice does not yet execute every local capstone stage | Local complete; hosted integration evidenced; full hosted reproduction remains |

## Documentation audit

The core documentation set is aligned as of this review:

- `INSTALL.md`: one-time repository setup and tool onboarding.
- `AGENTS.md`: routing, safety, skill selection, and current-day workflow.
- `docs/PRD.md`: business problem, architecture intent, principles, acceptance
  criteria, and non-goals.
- `docs/PLAN.md`: day-by-day implementation plan and contracts.
- `PROGRESS.md`: generated local completion table plus narrative evidence.
- `docs/ARCHITECTURE.md`: current architecture and security model.
- `docs/RUNBOOK.md`: local operation, tests, evaluations, and teardown.
- `docs/AWS_AGENTCORE_SETUP.md`: reproducible AWS setup, deployment, evidence,
  billing, and teardown runbook.
- `experiments/README.md`: provider-neutral experiment mandate, run manifest,
  token/infrastructure accounting, comparison rubric, and ad hoc commands.
- `docs/EVIDENCE.md`: local versus live evidence ledger.
- `docs/LEARNINGS.md`: dated retrospectives.
- `docs/REFERENCES.md`: canonical bibliography, including the refreshed agent
  harness section reviewed on 2026-08-13.

The experiment framework is now the recommended place to record new local,
non-AWS, or AWS trials. It requires an explicit question, setup, input/output,
usage, pricing basis, evidence, findings, limitations, decision, and cleanup
state. AWS model-token costs and AWS infrastructure costs are recorded as
separate fields, with billing-lag status preserved.

## Remaining optional or account-dependent evidence

These are not missing implementation days or blockers for the core 21-day plan:

The PRD interpretation is therefore: Tier 1 is implemented and locally
validated; the core Tier 2 architecture is implemented, with temporary Runtime
evidence captured; Tier 2 Gateway/provider/browser evidence and Tier 3
comparisons remain intentionally optional or account-dependent. The project
must not claim those external validations until their prerequisites exist.

1. If desired, deploy and tear down a governed Gateway path with a real
   HTTPS-hosted MCP target.
2. The AgentCore Evaluation item is now complete for the on-demand API: a
   documented Strands-compatible span/event fixture scored one session. A
   future hosted-runtime rerun can still validate CloudWatch collection of
   those spans, but it is an instrumentation enhancement rather than an
   unresolved evaluation API blocker. Live Memory and standalone Guardrails
   evidence are complete; managed Guardrail attachment remains a separate
   optional extension. Hosted runtime logs and `AWS/Bedrock-AgentCore` metrics
   are now evidenced; hosted ADOT/OTel span export remains optional.
3. The reviewed ALFRED/Treasury/SEC capture is now promoted into governed
   source-specific cached tables with scheduled freshness checks. Other sources
   such as Treasury auctions, TRACE, N-PORT, ratings, GDELT, and provider
   research still require separate terms, access, and live evidence.
4. Complete native Copilot automation and Copilot/Canvas browser evidence where
   the platform account makes those steps available. GitHub Projects and the
   scheduled morning-brief workflow are now evidenced.
5. The full deterministic capstone has now been packaged behind the hosted
   AgentCore entrypoint and compared with the local fixture using a manifest,
   token record, CloudWatch logs/metrics, budget snapshot, and Cost Explorer
   estimate. Hosted ADOT/OTel span export remains optional; the structured
   execution trace is the supported audit artifact and does not expose private
   model chain-of-thought.

6. A temporary managed Bedrock Guardrail attachment was exercised. The
   attachment and blocked-input path worked, but a neutral review prompt was
   also blocked because the serialized prompt contains governance/review
   vocabulary. The standalone Guardrail proof remains complete; managed
   attachment is a refinement item rather than a claimed production-ready
   allowed path. See the [managed Guardrail findings](../../experiments/runs/agentcore-managed-guardrail-20260816-215000/findings.md).

Do not change the local status table to “incomplete” solely because these live
tasks are unclaimed. Instead, keep the two evidence classes visible and update
the ledger when a live run genuinely succeeds.
