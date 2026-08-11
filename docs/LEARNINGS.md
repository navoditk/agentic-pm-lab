# Learnings

Reflective retro log, one dated entry per day, written the same day rather than reconstructed later. Finalized Day 12. Distinct from `PROGRESS.md`'s narrative log: that's "what happened and where's the evidence," this is "what worked, what didn't, what I'd do differently."

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
