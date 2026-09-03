# Learnings

Reflective retro log, one dated entry per day, written the same day rather than reconstructed later. Distinct from `PROGRESS.md`'s narrative log: that's "what happened and where's the evidence," this is "what worked, what didn't, what I'd do differently."

## 2026-09-02 — QA-reviewing the curriculum-depth pass found real fabrications, not just style nits

**What worked:** treating "citations resolve to real paths" (verified programmatically after the authoring pass) as a floor, not proof of accuracy, and dispatching a *separate* round of forks whose only job was to open the cited source and check the claim against it, not just the path. That distinction mattered: the fabricated claim in the FICC glossary ("the bond validator returns `needs_review` for an unresolved call provision") pointed at a real, existing file (`src/ingestion/fixed_income.py`) — the citation-resolution check would have passed it every time, because the file exists; only actually reading `REQUIRED_BOND_FIELDS` and confirming it has no callability field caught that the claim itself was false. Two of the three real defects found were exactly this shape: a real path, cited confidently, supporting a claim the file doesn't actually make.

**What I'd flag:** this fabrication was in content I wrote directly myself (the FICC glossary/tutor/quiz), not fork output — writing quickly from domain knowledge about what a bond instrument-master validator *should* check, rather than re-reading the specific function before asserting what it *does* check. The portfolio-construction backwards-narrative bug (describing `risk_parity`'s weight as "between" and "less aggressive" than `max_sharpe`'s, when the actual numbers show the opposite) came from a fork, but the same root cause: a plausible-sounding narrative asserted before double-checking the specific numbers it was built on. The fix in both cases wasn't "write more carefully" as a general resolution — it's the concrete practice of running the code and reading the exact function body before writing a specific, falsifiable claim about it, every time, not just for the first pass.

## 2026-09-02 — Deepening 14 tutors in parallel, and a lesson in fork discipline

**What worked:** splitting the work by topic pairs (7 forks × 2 topics, one alone for the largest topic) rather than by task type kept each fork's output internally coherent — one fork could ground a deep-dive doc and its quiz in the exact same source reading, rather than context-switching between 14 topics' worth of unrelated code. The FICC glossary source-verification step (searching for each of 15 new terms' public source before writing the entry, rather than guessing a plausible-looking URL) caught real gaps early — several assumed Investopedia URLs turned out not to be confirmable, and the actual sources found (Investor.gov, FINRA, NY Fed, Corporate Finance Institute, Wikipedia) were both more certain to exist and, in a few cases, more authoritative than the guess would have been.

**What went wrong, worth remembering:** partway through, a coordinator turn that had dispatched several async forks apparently continued executing *as* one of those forks (inheriting the full parent context, including the instinct to keep coordinating) and attempted to launch six more forks from inside a forked worker — which correctly errored ("Fork is not available inside a forked worker"). The lesson isn't about the tooling limit itself, it's that a forked worker inheriting the *entire* parent transcript, including the parent's own goals and pending TODOs, makes it easy to lose track of which narrower slice of that plan is actually this execution's job. Re-grounding in `git status`/`wc -l` ground truth rather than the transcript's implied narrative was what actually resolved the confusion — worth doing earlier next time a nested-execution context feels ambiguous, rather than trying to reason out the causal history first.

## 2026-09-02 — Growing the eval set surfaced a silent CI break

**What worked:** asking "why does this test suite never actually exercise the real `evals/` files?" before writing new cases paid off immediately — `load_cases()` had been crashing on `guardrail_cases.jsonl` since Day 14, and would have kept crashing regardless of how good any new case I wrote was. The fix that mattered most wasn't schema padding, it was noticing that `enforce_content()` in `src/control/guardrails.py` is a pure function: the guardrail dimension didn't need a model call to be real, it needed someone to notice it could be tested exactly like `policy_probe` cases already are. That turned a permanently-`None` stub into a genuinely scored, zero-cost dimension.

**What I'd flag rather than call fully solved:** every new case in this pass — the 3 golden-dataset additions, the 2 new routing/authorization cases, the fixed Day-12 stub — is marked `status: stub` and excluded from `load_cases()`, because activating any of them changes `config/eval-baseline.json`'s case_count and requires a real experiment run to get honest dimension scores, which needs a LangSmith key and a model-provider key I wasn't authorized to spend against. So "grew the eval set" here means *authored and schema-verified*, not *proven correct against live model behavior* — the same gap the original 12 golden cases don't have, since those were actually run. `run_backtest`'s stub case has an extra caveat noted inline: it's approval-gated (`interrupt_on`) and `predict()` doesn't handle a paused graph yet, so activating it needs that handled too, not just a baseline refresh.

**Worth remembering:** `docs/PLAN.md`'s Appendix C tables are explicitly illustrative planning content, and at least one example in it (RISK_USER denied `run_backtest`) no longer matches the real `governance/policies/*.cedar` file. I checked the actual policy file before writing the new authorization case instead of trusting the appendix, and it's a good thing I did — the appendix's specific claim there is now wrong.

## 2026-09-01 — Interactive tutor layer and doc housekeeping

**What worked:** A five-audit review (one fork per doc area, run in parallel, synthesized into one published Artifact) surfaced real, specific drift that a single linear read would likely have missed piecemeal — 35 files with stale pre-reorg doc paths, three undocumented `src/` modules, a self-disclosed RUNBOOK placeholder, and 10 tutor personas that were structurally correct but content-thin. Splitting the fix the same way — a scripted mapping-table replacement for the mechanical path fixes, three parallel forks each owning a disjoint set of tutor topics for the content-heavy deepening-plus-quiz work — kept the turn-around fast without any file-ownership collisions, because each fork's scope was a clean partition of the 13 topics.

**What I'd flag rather than call fully solved:** the quiz grading is deterministic multiple-choice by design (no NLP/LLM judge), which keeps it testable and consistent with every tutor's "no paid services" contract, but it can't assess a free-text explanation the way a human tutor could — it proves recall of a cited fact, not depth of understanding. The comprehension tracker (`LEARNER_PROGRESS.md`) is also self-reported in the sense that nothing stops someone from re-running a quiz until they pass; that's an acceptable trade-off for a solo learning tool, but it would need a stricter model (timed, unlimited-attempt visible, or reviewed) before it meant anything to a third party.

**Explicitly deferred, not solved here:** the review's other two flagged gaps — the eval set's small size (22 cases) relative to the claims resting on it, and FICC-track depth lagging the "fixed-income-first" framing — were left as backlog per the original proposal's scope, not fixed in this pass. They're real content-authoring efforts of their own, not a housekeeping or infrastructure task.

## 2026-08-14 — High-feasibility public investment-data expansion

The safest first expansion was a connector/normalizer slice rather than a
silent replacement of the learning fixtures. SEC Company Facts/submissions,
ALFRED, Treasury auctions, NY Fed SOFR, CFTC COT, and Kenneth French factors
now have bounded fetch paths, source-specific normalization, and fixture-only
unit tests. The new investment-data tutor makes the sample shape and decision
use explicit, and the six-file sample pack makes the normalized shapes
browsable without credentials. This preserves the distinction between a
live-capable connector, a captured provider response, and canonical DuckDB
integration.

The main remaining lesson is that source access is not the hardest part. SEC
XBRL units, ALFRED vintages, Treasury security identifiers, SOFR publication
timing, CFTC release lag, and factor definitions all require source-specific
provenance before deterministic analytics can consume them. The next slice
should capture one bounded response per source, record terms and raw hashes,
then promote only reviewed schemas into source-specific tables.

## 2026-08-14 — Final plan and documentation audit

The 21-day implementation remit is complete and the repository is clean and
fully synchronized with `origin/main`. The audit corrected stale Day 12–20
status language: the temporary AgentCore Runtime request succeeded, standalone
Memory and Guardrails proofs completed, and the on-demand Evaluation fixture
produced a scored result. The remaining Gateway, live-provider, paid-model,
and Copilot-hosted browser items are explicitly optional or account-dependent
evidence, not missing local implementation. This distinction is now reflected
in `README.md`, `PROGRESS.md`, `docs/architecture/ARCHITECTURE.md`, `docs/evidence/EVIDENCE.md`, and
`docs/learning/PLAN_REVIEW.md`.

## 2026-08-13 — AWS runbook hardening

**What worked:** Converting the live setup into a direct CodeZip runbook made
the hidden gates explicit: IAM Identity Center refresh after permission changes,
cross-region model selection, Linux ARM64 packaging, scoped S3 access,
service-linked-role initialization, endpoint readiness, bounded invocation,
CloudWatch correlation, cost capture, and teardown. A minimal fixture and SDK
probe now give a new operator a stable starting point without packaging the full
application.

**What remains limited:** The live version-3 runtime reached `READY` but its
bounded request still returned HTTP 500 without a new application traceback.
The documentation records that as deployment-ready/request-failed evidence and
does not claim a successful cloud inference until the minimal fixture completes
one response.

## 2026-08-13 — Day 20

**What worked:** A deterministic capstone replay can exercise the full governed
PM sequence without overstating live infrastructure: authentication,
portfolio entitlement, freshness, fixed-income calculations, cited research,
Devil's Advocate challenge, human review, audit, OTel, evaluation dimensions,
and version metadata all appear in one artifact. Clean/dirty price, accrued
interest, duration matching, and order suppression make the fixed-income safety
boundary concrete.

**What remains unclaimed:** The capstone uses fixture research and local
structured observations. Live AgentCore, CloudWatch, provider uptime, Canvas
capture, and live external-data evidence remain deployment/evidence work rather
than being inferred from this replay.

## 2026-08-14 — Day 21

**What worked:** A Canvas can be a genuine learner entry point when it calls
the same governed workflow boundary as the terminal path. The new fixture
runner carries one request through authentication, data freshness, research,
fixed-income and scenario analysis, challenge, review, evaluation, and audit.
Each stage returns status, duration, component, operation, and trace ID, while
the final envelope preserves provenance, approval state, failures, and audit
events. Token usage is visible using serialized input/output counts and a
documented four-characters-per-token approximation when no model tokenizer is
available; fixture cost is explicitly zero.

**What remains limited:** The fixture path is a deterministic capstone, not a
model invocation and not a private chain-of-thought recorder. It exposes the
structured execution trace and decision artifacts a system operator needs, but
never claims access to hidden model reasoning. Provider modes are explicit
configuration boundaries and fail closed until credentials, model selection,
pricing, and provider evidence are supplied.

## 2026-08-13 — Day 19

**What worked:** Extending the existing Agent Operations Canvas preserved the
four-Canvas scope while adding a useful production surface for research and
committee work. Provider health, promotion checks, SLOs, fixed-income source
coverage, thesis rebuttals, and incident replay are all visible through shared
handlers and durable state.

**What remains unclaimed:** The local Canvas exercises degraded-provider and
replay behavior, but it does not claim live CloudWatch dashboards, LangSmith
traces, AgentCore promotion, or provider uptime. Those require external
platform evidence and remain visibly blocked in the promotion panel.

## 2026-08-13 — Day 18

**What worked:** A deterministic challenge report makes the committee safety
rules executable: the critic has no tools, cannot approve its own artifact, and
the workflow remains pending until a distinct authorized human decides. The
challenge categories also provide a measurable coverage surface instead of an
unbounded request for skepticism.

**What remains limited:** Contradictions and causal support are represented by
explicit evidence metadata; semantic truth requires a reviewed model/evidence
evaluation. Concentration and liquidity checks are learning-scale thresholds,
not a production risk engine.

## 2026-08-12 — Day 17

**What worked:** The AWS investment-research shape maps cleanly to a separate
native Deep Agents graph when the provider adapter returns evidence records
instead of prose. Keeping quantitative tools and unstructured evidence in
different specialist contracts makes the key trust rule testable: narrative
signals can be cited and summarized but cannot create a risk number.

**What remains mocked:** The thematic provider, EDGAR retrieval, Treasury
auction/SOFR/TRACE/CFTC connectors, and live AgentCore deployment remain
fixture or local evidence. No provider licensing or cloud access is implied by
the local tests.

## 2026-08-12 — Day 15

**What worked:** A small provenance envelope is enough to make the critical
point-in-time rule executable: an observation date describes the economic period,
while a release date describes when the PM could know it. Selecting the latest
eligible vintage by source, series, and observation date prevents a revised
macro value from leaking into an earlier backtest. The bond instrument-master
validator also makes missing conventions visible before valuation.

**What did not happen:** No live ALFRED, Treasury, TRACE, OpenBB, or licensed
market-data call was made. That is deliberate: the local contract and negative
cases should exist before credentials, terms, or provider-specific schemas are
introduced.

**One thing I'd do differently:** Treat bond terms as a first-class contract
before adding more market endpoints. A curve or price feed without settlement,
day-count, coupon, callability, and identifier semantics is not yet usable for a
fixed-income PM calculation.

## 2026-08-12 — Day 16

**What worked:** SEC filing metadata can be made useful without loading a full
document corpus: accession number, CIK, form, filing date, reporting period,
canonical URL, excerpt, and retrieval time provide an attributable evidence
object. The same release-date rule used for macro vintages filters filings for
as-of research.

**What did not happen:** No live EDGAR request was made. The connector is tested
with mocked payloads, keeping unit tests network-free and avoiding premature
decisions about rate limits, caching, and excerpt retention.

**One thing I'd do differently:** Add citation completeness and document-content
extraction only after the metadata contract is stable; otherwise a research
agent can produce polished prose without a reproducible filing identity.

## 2026-08-12 — Day 14

**What worked:** Extending the local guardrail with named topic categories made
the governance distinction testable: normal risk narration passes, while
unqualified trade directives and prompt/credential exfiltration are blocked.
The policy remains applied at input, context, and output boundaries.

**What did not happen:** Fine-tuning, second-region deployment, and Cost
Explorer review were intentionally skipped because no AWS sandbox resources
are active. The configuration records the intended Bedrock Guardrails shape;
it is not evidence of a live managed resource.

**One thing I'd do differently:** Add semantic guardrail cases to the versioned
evaluation dataset at the same time as the local policy, so false-positive
rates and blocked-topic coverage are visible in the AgentOps Canvas earlier.

## 2026-08-12 — Day 13

**What worked:** A narrow memory protocol made the boundary between Deep Agent
working state and managed AgentCore Memory concrete. Identity and scope are
checked before context is serialized, and the same golden dataset can be
represented as an AWS-native evaluation plan without changing the LangSmith
baseline.

**What did not happen:** The AWS account is not configured yet, so there is no
live cross-session Memory transcript, CloudWatch Transaction Search evidence,
or AgentCore Evaluation report. The local tests deliberately do not imply
those cloud capabilities.

**One thing I'd do differently:** Create the AWS evaluation manifest alongside
the Day 12 Runtime intent, so account setup and live evidence can be captured
as one repeatable deployment exercise rather than as a later extension.

## 2026-08-12 — Day 12

**What worked:** The Tool Layer remained genuinely reusable: the same scenario
and optimization functions are now covered by contracts, FastAPI routes, MCP
capabilities, and Deep Agent tools. The AgentCore SDK's direct-code entrypoint
was small enough to keep the managed-runtime boundary visible without creating
a second application implementation. The deployment intent files and ADRs
make the local-to-managed mapping reviewable before any metered AWS call.

**What didn't work / had to be fixed:** The installed PyPortfolioOpt release
expects a private SciPy clustering constant that is absent in the installed
SciPy version. HRP therefore needs a deterministic inverse-volatility fallback
until the dependency pair is upgraded and validated. This is a useful
production lesson: a library name in the target architecture is not evidence
that its numerical path is compatible with the pinned environment.

**One thing I'd do differently:** Establish a small dependency compatibility
matrix for numerical libraries before integrating the optimizer, and test the
actual AgentCore model/provider string and IAM permissions in a disposable AWS
account before calling the deployment day complete. The repository now stops
short of claiming that cloud evidence; Days 13–20 can extend it with managed
Memory, evaluations, guardrails, provenance, research, and committee workflows.

---

## 2026-08-09 — Day 1

**What worked:** Following docs/PLAN.md's Day 1 steps in order (data mock → control stub → tool stubs → runtime → CI → skills → pre-commit → progress tracking → tests → docs/architecture/ARCHITECTURE.md) meant each step could be smoke-tested in isolation before moving on — every FastAPI app, the DuckDB loader, and `check_progress.py`'s regex/glob logic all got caught and fixed immediately rather than discovered later during a big-bang test run.

**What didn't work / had to be fixed along the way:**
- `uv init` doesn't create a `.gitignore` when run inside an already-initialized git repo — had to write one by hand before `data/cache/` or a future `.env` could be safely kept out of commits.
- Every skill package uses the same `tests/test_skill.py` filename by design (docs/PLAN.md §8.2), which collides under pytest's default import mode the moment a second skill exists. Fixed with `--import-mode=importlib` in `pyproject.toml`, plus `pythonpath = ["."]` since importlib mode — unlike the default — doesn't auto-add the repo root, which `src.*` imports in tests need.
- `scripts/check_progress.py`'s first version used a non-anchored regex to find the `<!-- PROGRESS:START/END -->` markers in `PROGRESS.md` — but the file's own intro paragraph mentions both marker strings inline as prose (documenting the mechanism), which the regex latched onto instead of the real markers below it, duplicating content. Fixed by anchoring the match to markers that appear alone on their own line.

**One thing I'd do differently:** Write the `pythonpath`/`import-mode` pytest config *before* writing any test files, not after hitting the `ModuleNotFoundError` — the failure mode was predictable in hindsight (console-script `pytest`, unlike `python -m pytest`, doesn't add cwd to `sys.path`) and could have been set up proactively alongside the initial `uv init` in `INSTALL.md` instead of discovered mid-Day-1.

**Also worth noting, from environment setup before Day 1:** the PyPI package literally named `cedar-policy` turned out to be a squatted placeholder (v0.0.1, fake source URL) — the real Cedar Python bindings are the community-maintained `cedarpy`. A good reminder to verify a dependency's actual metadata (author, repo, release history) before trusting a name match, especially for a security-relevant package.

---

## 2026-08-10 — Day 2

**What worked:** Normalizing yfinance and FRED responses before persistence
made the DuckDB writers source-agnostic and easy to test. A shared atomic JSON
cache kept the rate-limit behavior explicit, and building the curve only from a
date shared by every Treasury tenor prevented a visually plausible but
internally inconsistent snapshot.

**What didn't work / had to be fixed along the way:**
- yfinance's multi-symbol response uses a two-level column index, so the parser
  had to locate the ticker level rather than assume one fixed column order.
- The progress tracker reports the whole Data Layer rather than individual
  tables. Its partial state is still the correct signal: three ingestion files
  are real and the one loader that owns security/portfolio fixtures remains
  mocked.
- Pre-commit's formatter changed both new test files after their first staging,
  reinforcing the workflow rule to re-stage and commit again rather than bypass
  the hook.

**One thing I'd do differently:** Define the normalized provider-record shapes
as typed structures before writing the clients. The current dictionaries are
tested and clear, but `TypedDict` definitions would make the yfinance/FRED to
DuckDB boundary easier to evolve safely.

---

## 2026-08-10 — Day 3

**What worked:** Keeping analytics functions pure made the hand calculations,
contract validation, and FastAPI wiring independent concerns. Writing schemas
from completed signatures exposed the exact distinction between internal
functions and governed tools, while the boundary dependency ensured every
known-identity decision was audited before execution.

**What didn't work / had to be fixed along the way:**
- The Day 1 endpoint stubs accepted only identifiers, which was insufficient
  for real regression and backtest inputs. The routes were preserved, but their
  first formal contracts now require explicit typed data rather than inventing
  portfolio returns from unrelated holdings.
- Day 3 describes six real analytics modules but the Day 1 route list contains
  research instead of risk. Research stayed mocked as required, and a governed
  `/tools/risk` route was added so all six real modules are actually callable.
- Adding mandatory identity enforcement correctly broke the older curve test;
  the test now supplies a known identity instead of weakening the boundary with
  an insecure default.

**One thing I'd do differently:** Define the Day 1 stub request models as the
eventual contracts, even while their implementations return mock data. That
would let a mock-to-real migration preserve both route and payload shape rather
than discovering an intentionally underspecified seam on replacement day.

---

## 2026-08-10 — Day 4

**What worked:** Deep Agents accepted the existing deterministic functions as
LangChain tools without a hand-built graph, loaded the shared skills directory,
and exposed `interrupt_on` as a configuration seam. A scripted tool-calling
chat model proved routing without credits, while the Ollama variant proved the
same harness could execute real volatility and exposure tools locally.

**What didn't work / had to be fixed along the way:**
- The newly created OpenAI key authenticated but had no credits, so cloud-model
  sample runs and cloud latency/quality measurements were blocked.
- The original dependency set included the OpenAI SDK but not
  `langchain-openai`; Deep Agents' provider string needed the LangChain
  integration added explicitly.
- Qwen3 4B called tools correctly for small, explicit contexts but skipped
  `get_volatility` when asked to pass a 500-return array, even after irrelevant
  research and memory were filtered. Filtering context size is not equivalent
  to guaranteeing small-model tool reliability.
- The local warm tool run took roughly 130 seconds, making it useful as a
  privacy/offline comparison but not a drop-in latency substitute.

**One thing I'd do differently:** Verify provider billing and run a one-line
model request before starting any provider-specific integration. For the local
path, start with a compact argument artifact or file reference rather than
asking a 4B model to reproduce hundreds of numeric values in a tool call.

---

## 2026-08-11 — Day 5

**What worked:** Native `subagents` kept orchestration declarative: the
Portfolio Manager needed only the `task` tool while each specialist received a
small domain-specific tool set. LangGraph checkpoint pending writes also did
exactly what the recovery exercise needed—after Quant crashed, resuming the
same thread reran Quant but preserved Macro's completed result.

**What didn't work / had to be fixed along the way:**
- The first cloud run routed to both correct specialists but dropped
  `periods_per_year=12` from the Quant task, silently changing annualization.
  Stronger parameter-preservation instructions and a deterministic routing case
  now cover that seam.
- An injected research timeout initially aborted the entire parallel workflow.
  Specialist retries now use bounded exponential backoff and end in an explicit
  dead-letter result rather than a success-shaped fallback.
- A malformed bond-pricing response was initially summarized as if valid.
  Exact-name contracts are now checked at tool execution before output can
  reach a specialist.
- Qwen3 4B constructed the full hierarchy but returned an empty response
  without calling either sub-agent, even under explicit routing instructions.

**One thing I'd do differently:** Put contract validation and retry middleware
around tools before the first live multi-agent run. The fail-first exercise was
valuable, but these are infrastructure invariants rather than behavior that
should depend on prompt compliance.

---

## 2026-08-12 — Day 6

**What worked:** One OTel provider was enough for framework
auto-instrumentation, deterministic tools, control operations, agent economics,
and LangSmith export. Routing evaluation roots directly to LangSmith experiment
sessions preserved the normal trace hierarchy while linking each run to its
versioned dataset example.

**What didn't work / had to be fixed along the way:**
- LangSmith's HTTP exporter required `/otel/v1/traces`; the base `/otel`
  endpoint returned 404 for this exporter configuration.
- Overriding `langsmith.trace.id` broke native OTel parentage because descendant
  spans retained their original trace lineage. The correct correlation is the
  native OTel trace plus the root span ID that LangSmith pads into a run UUID.
- The first SDK `evaluate()` attempt created the experiment shell but sent
  OTel-only target traces to the general project. A manual experiment session
  with `langsmith.trace.session_id` and
  `langsmith.reference_example_id` routed them correctly.
- Plain `inputs` and `outputs` span attributes were consumed without producing
  usable run fields in the tested mapping. The documented
  `gen_ai.prompt`/`gen_ai.completion` attributes produced evaluator-ready
  dictionaries.
- A five-case probe caught ingestion timing and feedback API assumptions before
  another full run: the runner now waits for completed outputs and attaches
  feedback with the experiment session ID.

**One thing I'd do differently:** Start with one minimal OTel-native experiment
case and verify project routing, example linkage, I/O mapping, and feedback in
the UI before invoking the complete dataset. That would have avoided the first
15-call experiment that proved model execution but could not serve as the
accepted baseline.

## 2026-08-12 — Day 9

**What worked:** Pre-seeding the agent-ops canvas with the documented Day 4/5/6/7
history let the UI show a meaningful operations console before any live
LangSmith call was attempted. The shared handlers for `get_runs`, `get_trace`,
`retry_node`, `approve_run`, `get_guardrail_results`, and `get_cost_metrics`
stayed easy to test because the canvas kept the run data, trace tree, and
approval state in one state object and used `askAgent` only at the approval and
retry boundaries.

**What didn't work / had to be fixed along the way:**
- The live `run_evaluation` path is correctly wired to `scripts/run_eval.py`,
  but it needs `LANGSMITH_API_KEY` at runtime. The repository environment here
  does not have that key set, so the canvas surfaces a clear error instead of
  pretending to complete the experiment.
- The comparison panel needed two different kinds of seeded evidence: the Day 4
  single-agent local run and the Day 5 multi-agent local/cloud notes. Keeping
  those observations separate made the side-by-side view more honest than
  collapsing them into one synthetic benchmark.

**One thing I'd do differently:** Capture the live Day 9 evaluation output as a
committed artifact the moment the key is available, instead of leaving the
canvas on a "wired but blocked" state. That would make the comparison panel and
the progress notes more concrete for the next person opening the repo.

---

## 2026-08-11 — Day 7

**What worked:** Separating identity assignment, Cedar policy, content
guardrails, and final tool enforcement made each failure independently
testable. Filtering agent tools before model binding reduced exposure, while
re-checking the same identity and portfolio at the API boundary prevented that
convenience from becoming the security control. LangGraph's native
`interrupt_on` produced a real pre-tool pause with the scripted model.

**What didn't work / had to be fixed along the way:**
- Cedar's `in` operator expresses entity hierarchy, not membership in a list
  of entity UIDs. Explicit resource comparisons were required for the tool
  sets.
- An initial administrator wildcard also allowed unknown tools. Administrator
  permissions now enumerate registered tools and portfolios so default-deny
  applies to every role.
- Merely constructing an agent with `interrupt_on` did not prove approval
  behavior. The final test invokes a scripted backtest call, asserts the graph
  returns an interrupt, and proves no tool result exists.
- The first Day 7 fast experiment hit a LangSmith 429 while polling ingested
  runs. Bounded exponential backoff now handles both delayed ingestion and
  explicit rate limiting.
- Fast model behavior varied: one run omitted a tool and repeated malformed
  portfolio arguments. Those observations were retained, but the known-good
  behavioral floors were not lowered; only the new deterministic policy score
  was added.

**One thing I'd do differently:** Define the Cedar entity/action vocabulary
and the deterministic policy-evaluation cases together before writing either
policy file. That would have made unknown-resource behavior and the evaluation
shape explicit before the first implementation pass.

## Public investment-data catalog extension

The sample pack now mirrors the documented source universe instead of only the
six real-capable public connectors. Small fixtures for N-PORT, TRACE, ratings,
GDELT, provider-shaped research, OpenBB metadata, and document/PDF evidence
make schemas and decision boundaries concrete while preserving honest status
labels. The tutor returns the same records, links the public-data primer, and
requires the learner to distinguish mock evidence from connector capability and
live experiment evidence. This is useful because licensing, point-in-time
semantics, entity resolution, and extraction quality are themselves part of the
integration problem.

## Phase 2 curriculum proposal

The next track deliberately shifts emphasis from adding more agent personas to
building the investment and operating controls around them. The proposed plan
starts with mandate and risk policy, then adds data quality, point-in-time
evidence, fixed-income implementation risk, decision records, typed workflow
state, model risk, repeated evaluations, red-team testing, promotion gates,
SLOs, resilience, and replay. It remains a public/mock-data learning track and
does not claim that the Phase 2 implementation has begun.

## Phase 1 recap and learning path

The Phase 1 recap turns the completed 20-day implementation into a reviewable
curriculum. It separates repository-local proof from live provider evidence,
maps each day to its implementation outcome, and gives learners a staged path
through investment data, deterministic tools, orchestration, governance,
evaluation, Canvas, and AWS. Tutor prompts and reference checkpoints make the
learning loop repeatable without implying that reading a reference proves a
capability exists in the repository.

## Repeated institutional PM scorecard

The five-repetition matrix established a useful separation between a stable
automated contract and an unfinished adversarial evaluation program. All four
providers produced the same governed structured capstone shape and passed the
automated checks, but that result does not establish production superiority:
the run used deterministic evidence, one fixed question, and no adversarial
scenario variation. OpenAI direct had the lowest mean token cost in this
sample; direct Anthropic was the most expensive; AWS Claude and Llama add
managed-runtime evidence but their temporary infrastructure charges need a
settled billing snapshot rather than a zero placeholder. The next meaningful
quality step is executing missing-liquidity, stale-evidence, conflicting-source,
unauthorized-access, prompt-injection, and malformed-tool scenarios, followed
by calibrated human narrative review.

## Adversarial scenario harness

The local adversarial pass converted the planned failure list into executable
contracts. The important result is not merely six green checks: each scenario
now records the expected safety behavior and its evidence separately from the
four-model quality baseline. This prevents a model from receiving credit for a
control that is actually enforced by the tool or policy boundary. Hosted
provider replays should be added next, especially for prompt injection and
malformed tool recovery, because local deterministic proof does not measure
provider-specific behavior or latency.

The direct hosted replay added six provider observations across OpenAI and
Anthropic for missing liquidity, stale evidence, and conflicting sources. All
six passed the simple response contract and recorded real token/cost/latency
data. The other three scenarios should remain pre-model checks: measuring a
model response after authorization or guardrail denial would be evidence that
the boundary was bypassed, not a successful test.

The AWS replay confirmed the same three response contracts through temporary
AgentCore Claude and Llama runtimes. It also reinforced an operational lesson:
the hosted response and cleanup artifacts are reliable completion evidence,
while the legacy wrapper's final JSON return can hang after asynchronous
teardown. Discovery mode recovers those completed records without duplicating
model calls or cloud resources.
