# Foundations Mastery Plan: quizzes and the mastery skill

**Status:** Proposed. Nothing here is built yet.
**Scope:** The quiz banks under `evals/tutor_quizzes/`, the course catalog in
`docs/learning/tutor-courses.json`, the `agentic-pm-mastery` skill, and the
learner CLI.
**Constraint kept throughout:** every course, quiz, and lab stays offline and
model-free by default. No paid model, AWS account, or live provider is needed
to learn or to be assessed.

## 1. Goal

A learner who completes the curriculum should be able to explain and apply
the foundations **outside this repository**, not only describe how this
repository uses them. The foundations are: the agent loop and tool calling,
LangChain core, LangGraph, AWS Bedrock, AgentCore, MCP, OpenTelemetry,
observability and traceability, evaluations, and agent security.

"Mastery" means three things, and the quizzes will test all three:

| Level | The learner can… | Evidence |
|---|---|---|
| **Concept** | Explain the idea without naming this repo, citing a canonical source | Concept-tier questions citing an external source |
| **Implementation** | Trace how this repo applies it, and name the simplification | Implementation-tier questions citing a repo file (what exists today) |
| **Transfer** | Apply it to a situation the repo never shows | Transfer-tier scenario questions and the build labs |

## 2. Where things stand

Measured on `main`, 2026-09-22:

| Finding | Number |
|---|---|
| Quiz questions across 14 courses | 366 |
| …citing repository code | 281 (77%) |
| …citing repository docs | 85 (23%) |
| …citing any external or canonical source | **0** |
| …worded around repo specifics (function names, paths, "per this tutor") | ~206 (56%) |
| External sources tracked for freshness in `docs/reference/source-registry.yaml` | 17 |
| Links in `docs/reference/REFERENCES.md` | 191, none of them assessed |

The gaps by foundation:

| Foundation | Today | Gap |
|---|---|---|
| Agent loop, tool calling, structured output, ReAct vs workflow | Assumed; no course teaches it | No course; no framework-free example |
| LangChain core (chat models, messages, `@tool`, Runnables, structured output, callbacks) | Used in `src/agents/`, never taught | No course |
| LangGraph | Strong: hand-built graph, reducers, checkpoints, interrupts | Streaming, subgraphs, `Send` fan-out, time travel |
| AWS Bedrock model layer (Converse, model access, inference profiles, throttling, Knowledge Bases, caching) | Only through AgentCore | No foundations course |
| AgentCore | Good service map | Identity and outbound auth, Policy, Gateway targets as concepts |
| MCP | Folded into a Canvas course | Primitives, transports, lifecycle, auth, tool-poisoning risks |
| OpenTelemetry | Strong: signals, propagation, sampling | GenAI semantic conventions, Collector, exporters |
| Observability and traceability | Pieces exist: `trace_id` in audit, eval, and capstone records | Never taught end to end as one idea |
| Evaluations | Strong on independent dimensions and gates | LLM-as-judge calibration, trajectory evaluation, variance, online vs offline |
| Agent security | Cedar, guardrails, role spoofing | Indirect prompt injection, OWASP LLM Top 10, excessive agency |

## 3. Design principles

1. **Every concept question cites a registered external source.** The source
   gets an entry in `source-registry.yaml`, so when upstream docs change, the
   freshness gate flags the exact questions affected, as it already does for
   deep dives.
2. **Behaviour claims are proven by a test, not a doc.** This follows the
   `AGENTS.md` rule learned from the LangGraph reducer mistake. A question
   about how a dependency behaves names a test that exercises that behaviour
   (`verified_by`), and CI runs it.
3. **Labs stay model-free.** Scripted fake chat models (built on
   `langchain_core`'s `GenericFakeChatModel`), `botocore.stub.Stubber` for Bedrock, in-process
   MCP client and server pairs, and OTel in-memory exporters. Optional live
   variants are clearly labelled and never required.
4. **You can't pass on repo trivia.** Passing requires a minimum score in
   each tier, not just overall.
5. **One order, one catalog.** New courses go into `tutor-courses.json` with a
   `step` and `stage`, so the generated tables, CLI, site, and XP calibration
   test all update automatically.

## 4. Changes to the quiz format

Extend each question record. The additions are backward compatible, since
existing questions get defaults:

```json
{
  "id": "opentelemetry-tutor-q31",
  "topic": "opentelemetry-tutor",
  "tier": "concept",
  "concept": "otel.context-propagation",
  "question": "A service receives a request carrying a W3C traceparent header. What should its first span use as its parent?",
  "choices": ["...", "...", "...", "..."],
  "correct_index": 2,
  "explanation": "One or two sentences on why, and why the tempting distractor is wrong.",
  "citation": "src/observability/telemetry.py",
  "source_id": "opentelemetry-context-propagation",
  "source_anchor": "#propagators",
  "verified_by": "tests/unit/observability/test_propagation.py::test_remote_parent"
}
```

| Field | Rule |
|---|---|
| `tier` | `concept`, `implementation`, or `transfer`. Existing questions default to `implementation` until reviewed. |
| `concept` | A dotted id from a new `docs/learning/concepts.yaml` taxonomy. Used for spaced review and the mastery matrix. |
| `explanation` | Required for new questions. Shown after answering, in the CLI, the site, and the skill. |
| `source_id` | Required for `concept`. Must exist in `source-registry.yaml`. |
| `verified_by` | Required when the answer is a claim about dependency behaviour. |

**New validator** (`scripts/check_quiz_banks.py`, added to CI and
`agentic-pm-lab check`). It enforces:
- the tier mix per course;
- that every `source_id` is registered and every `citation` and `verified_by` path exists;
- a balanced spread of correct-answer positions (today's banks are not checked for this);
- no duplicate questions.

**Pass rule:** at least 80% overall **and** at least 70% in each tier.
`record_answers` and the learner-progress table store per-tier scores and
the missed `concept` ids.

**Tier mix per course:** 40% concept, 40% implementation, 20% transfer, with
25–35 questions per course.

## 5. Curriculum changes

### New courses

| Proposed step | Course | Stage | Core concepts | Model-free labs |
|---|---|---|---|---|
| 1 | **Agent foundations** | Foundations | Agent loop; tool calling and schemas; structured output; workflow vs agent; ReAct and plan-and-execute; context windows and context engineering; memory types | Build a 60-line agent loop against a scripted fake model: parse a tool call, execute it, feed back the result, stop. Then break it with a malformed tool call. |
| 2 | **LangChain core** | Foundations | Chat models and messages; `@tool` and generated JSON Schema; Runnables and composition; `with_structured_output`; callbacks and tracing hooks | Generate a tool schema from a typed function and assert it. Get structured output from a fake model: `GenericFakeChatModel` implements neither `bind_tools` nor `with_structured_output`, but a subclass whose `bind_tools` returns itself, scripted with an `AIMessage` carrying `tool_calls`, does (verified 2026-09-22). Attach a callback that counts tokens. |
| before AgentCore | **AWS Bedrock foundations** | Operate and govern | Converse API request and response; model access and inference profiles; guardrails as an API; Knowledge Bases and RAG; prompt caching; throttling and retries; IAM for model invocation | Use `Stubber` to exercise a Converse call, a guardrail intervention, and a `ThrottlingException` with bounded retry, all offline. |
| split from Canvas | **Model Context Protocol** | Integrate and extend | Tools, resources, prompts; stdio vs streamable HTTP; initialization and capability negotiation; authorization; tool poisoning and confused-deputy risks | In-process client and server over the pinned SDK's memory streams (`mcp.shared.memory.create_client_server_memory_streams`, mcp 2.0.0; wiring a full session over them is Phase C's first task): list tools, call one, and prove an unentitled identity is refused at the boundary. A poisoned tool description fixture. |
| end of path | **Traceability end to end** | Integrate and extend | One `trace_id` across request, policy decision, tool call, audit, eval record, and provenance; lineage; replay; what model risk needs to reconstruct a decision | Given a trace id from a fixture run, reconstruct the full decision record. Then find the gap when one hop drops the context. |

This takes the curriculum from 14 to 18 courses. Canvas keeps its own course,
now focused on UX, shared state, and approval evidence.

### Deepened courses

Each gets about 8–12 concept questions and 4–6 transfer questions, with
existing implementation questions reviewed and trimmed to about 40%:

| Course | Additions |
|---|---|
| LangGraph and Deep Agents | Streaming modes, subgraphs, `Send` fan-out, time travel and state history, durable execution semantics |
| OpenTelemetry | GenAI semantic conventions (`gen_ai.*`), Collector pipelines, exporters, span events vs logs, exemplars |
| Evaluations and AgentOps | LLM-as-judge design and calibration (agreement against labelled cases), trajectory evaluation, repeated-trial variance, online vs offline evaluation |
| AWS Bedrock AgentCore | Identity (inbound and outbound auth), Policy, Gateway targets, Memory strategies, Observability, Evaluations; "what each service replaces in the local stack" |
| Governance and delivery | OWASP LLM Top 10, indirect prompt injection through retrieved content, excessive agency, least privilege for tools |
| Agent architecture | Multi-agent trade-offs from published research, context budget design, when *not* to use an agent |

### Sources to register

Each is added to `source-registry.yaml` with the topics it affects, and
reviewed before any question cites it:

- Anthropic, *Building effective agents*, plus the engineering posts already in
  `REFERENCES.md` on context engineering, writing tools for agents, agent
  evals, and the multi-agent research system
- Yao et al., *ReAct* (arXiv 2210.03629)
- LangChain core concepts documentation
- LangGraph documentation on streaming, subgraphs, and persistence (the
  existing `langgraph` entry, extended)
- AWS Bedrock User Guide: Converse API, inference profiles, Knowledge Bases,
  prompt caching
- MCP specification: lifecycle, transports, authorization, security best
  practices
- OpenTelemetry specification: context propagation, and the GenAI semantic
  conventions
- Zheng et al., *Judging LLM-as-a-Judge* (arXiv 2306.05685)
- OWASP Top 10 for LLM Applications

## 6. Mastery skill and CLI changes

| Change | What it does |
|---|---|
| **Concept-first lessons** | Each objective is taught concept (vendor-neutral, cited) → this repo's implementation → one transfer question. The teaching protocol already has the slots; it gains the order and the transfer step. |
| **Placement quiz** | `agentic-pm-lab placement`: 12 concept questions across the foundations. It recommends a starting step and which Foundations courses can be skipped. The skill offers it on first `agentexpert`. |
| **Spaced review** | Missed `concept` ids from recorded attempts come back in `agentic-pm-lab review` and in the skill's "quiz me", weighted toward older misses. |
| **Mastery matrix** | `agentic-pm-lab progress` adds a foundations × tier grid (concept, implementation, transfer) next to the per-course table. XP stays a motivator; the matrix is the evidence. |
| **Tier-filtered practice** | `agentic-pm-lab quiz <topic> --tier concept` for practice. Recording still requires the full bank. |
| **Cross-foundation final assessment** | Rewrite `references/final-assessment.md` around one request traced through MCP → LangGraph → Bedrock → OTel → evaluation → audit, with a question at each hop. |
| **XP recalibration** | Automatic. The skill's calibration test derives the level thresholds from the catalog, so adding four courses fails CI until the thresholds are recalculated. |

## 7. Phased delivery

Each phase is one or two reviewable PRs and leaves `main` green.

| Phase | Delivers | Acceptance |
|---|---|---|
| **A. Infrastructure** | Question fields and defaults, `concepts.yaml`, `check_quiz_banks.py`, per-tier pass rule and recording, `--tier`, explanations shown in CLI, site, and skill | CI enforces the format; existing 366 questions validate with `tier: implementation`; no score semantics change for existing attempts |
| **B. Foundations courses** | Agent foundations, LangChain core; sources registered; about 60 questions; labs with tests | Both courses meet the tier mix; every concept question cites a registered source; labs run offline in CI |
| **C. Platform foundations** | AWS Bedrock foundations; MCP split into its own course; about 60 questions | `Stubber` labs pass in CI (Converse and `ThrottlingException` stubbing verified offline 2026-09-22); in-process MCP session proven in a test before any lab depends on it; Canvas course re-scoped without losing coverage |
| **D. Deepen existing courses** | About 90 new concept and transfer questions across LangGraph, OTel, Evals, AgentCore, Governance, and Architecture; implementation questions reviewed | Every course meets the tier mix; every behaviour claim has `verified_by` |
| **E. Traceability and assessment** | Traceability course, placement quiz, spaced review, mastery matrix, new final assessment | A fixture run is reconstructable from a single trace id in a test; placement and review run offline |

Estimated growth: about 230 new questions (366 → about 600), 14 → 18
courses, and roughly 53 → 72 learner hours.

## 8. Quality control for new questions

- Questions may be drafted with an assistant, but **every answer key is
  checked by a person against the cited source or the named test** before
  merge. The PR lists each question id with the section it was checked
  against.
- Distractors must be plausible misconceptions, not filler. Each question's
  `explanation` names the misconception its strongest distractor encodes.
- No question may depend on a version-specific detail unless the registry
  pins that version.
- A sample of new questions is taken cold by someone who has not read the
  course. Any question answered correctly by everyone, or by nobody, is
  revised.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Vendor docs drift and answers go stale | Registry freshness per question via `source_id`; weekly monitor already runs |
| Question volume lowers quality | Phase gates; human answer-key review; cold-take sampling |
| The curriculum gets long | Placement quiz lets experienced learners skip; stages stay independent |
| Behaviour taught wrong | `verified_by` tests, per `AGENTS.md` |
| AWS content becomes vendor marketing | Every AWS concept is framed as "what this replaces in the local stack", with its failure modes |

## 10. Decisions needed before Phase A

1. **New courses vs folding into existing ones.** The plan proposes four new
   courses plus a split. The alternative is fewer courses with larger quiz
   banks, which gives a shorter path but less focused courses.
2. **Split MCP from Canvas?** Recommended, because MCP is foundational and
   Canvas is a product surface.
3. **Per-tier pass threshold.** 70% is proposed.
4. **Optional live labs** (for example a real Bedrock Converse call). They
   would be labelled optional, never required for completion, and never run
   in CI. Proposed: allowed, but not in the first phases.
