# Learnings

Reflective retro log, one dated entry per day, written the same day rather than reconstructed later. Distinct from `PROGRESS.md`'s narrative log: that's "what happened and where's the evidence," this is "what worked, what didn't, what I'd do differently."

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

**What worked:** Following docs/PLAN.md's Day 1 steps in order (data mock → control stub → tool stubs → runtime → CI → skills → pre-commit → progress tracking → tests → docs/ARCHITECTURE.md) meant each step could be smoke-tested in isolation before moving on — every FastAPI app, the DuckDB loader, and `check_progress.py`'s regex/glob logic all got caught and fixed immediately rather than discovered later during a big-bang test run.

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
