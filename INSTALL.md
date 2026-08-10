# INSTALL: Environment & Repo Setup

**Do this once, before Day 1.** This is every piece of software the whole plan needs, plus bootstrapping the repo — self-contained on purpose, so you (or a dev tool) can work through it start to finish without opening `PLAN.md`'s day-by-day steps at all. Once every box in §9's checklist is ticked, go to `PLAN.md` and start Day 1.

**Nothing here requires a FRED, Anthropic, OpenAI, LangSmith, or AWS account.** Those are deliberately deferred to the specific day each is first used, not done now — §5 explains why and gives the summary; the actual step-by-step for each lives in `PLAN.md` Appendix B on the day it's needed (Day 2, 4, 6, and 12 respectively).

---

## 0. How to run this document: manual vs. delegate to a CLI tool

**Recommended: hybrid — hand most of it to whichever CLI tool you already have running, but keep four things manual.**

**Can't be delegated, do these yourself first (a few minutes, unavoidable):**
- Every "signed in" step in §1 (Claude Code, GitHub Copilot Desktop/App, Codex CLI's "Sign in with ChatGPT," `gh auth login`) — browser-based OAuth flows; no agent can click through your own login.
- Docker Desktop's first launch — macOS typically needs you to open the app once and approve its privileged-helper permission dialog; an agent can run the install command but not click "Allow."
- Enabling "Copilot coding agent" in repo Settings (§4) — a GitHub web UI toggle.
- **Decide public vs. private for the repo** before §2 runs — `gh repo create --clone` defaults to whatever you tell it, and that's a one-line decision worth making yourself rather than letting a tool assume.

**Safe to delegate — deterministic, scriptable, reversible:** repo bootstrap (§2), the `uv init`/`uv add` passes (§3), the `npx skills add` command (§4), and the §9 verification checklist.

**A kickoff prompt that reflects this split**, once you've done the manual pieces above:
```
Read INSTALL.md and execute it step by step, in order.
I've already signed into Claude Code / Copilot / Codex and Docker Desktop is running — skip those.
Use --public (or --private, as I've decided) for the repo.
Stop and ask me before anything needing browser/OAuth login, and before
the "Copilot coding agent" repo-settings step.
Run through §9's verification checklist at the end and report which items pass or fail.
```

Keep normal approval prompts on for this session — don't use a skip-all-permissions/auto-approve flag. It's installing system-level tools and touching your dev environment, which is worth watching rather than fire-and-forgetting, and since the OAuth logins block full automation anyway, auto-approve mode doesn't actually save meaningful time here.

---

## 1. Core development environment

- Python 3.11+ (via `pyenv` or `brew install python@3.11`)
- **`uv`** (`curl -LsSf https://astral.sh/uv/install.sh | sh`, or `brew install uv`) — this project uses `uv` for everything Python: virtual environments, dependency installation, and running commands. There's no separate `pip`/`venv`/`pip-tools` step; `uv` replaces all three.
- Docker Desktop for Mac: `brew install --cask docker-desktop` (Homebrew's cask was recently renamed from `docker` — the old token still works as an alias for now, but use `docker-desktop` directly). Or download the `.dmg` straight from `docker.com` if you'd rather not use Homebrew — `docs.docker.com/desktop/setup/install/mac-install/` has the current official steps if anything here goes stale.

  **Launching it, since installing and running are two separate steps:**
  1. Open the app — Spotlight (`Cmd+Space`, type "Docker", `Enter`), Finder → Applications → Docker, or from Terminal: `open -a Docker`. The Terminal command is the one part of this that *can* be scripted/delegated to a CLI tool, unlike the next step.
  2. First launch only: accept the Docker Subscription Service Agreement if prompted, then approve the privileged-helper permission macOS asks for (enter your Mac password or use Touch ID) — this is the step that needs a human click no matter which install method you used (§0's list of things that can't be delegated).
  3. Wait for it to finish starting: a whale icon appears in the menu bar; once its animation settles, Desktop is ready. Clicking the icon shows a status line confirming it's running.
  4. Confirm from Terminal with `docker info` or `docker ps` — **not** `docker --version`, which only confirms the CLI binary is installed and will report a version string even if Desktop is closed. `docker info`/`docker ps` actually tries to reach the daemon, so it fails loudly ("Cannot connect to the Docker daemon...") if Desktop isn't running yet, which is the check that's actually useful here.

  Installed now, but genuinely idle until Day 6 (optional trace UI / Langfuse) and Day 11 (the real payoff: the local `docker-compose.yml` stack). **Not used on Day 12** — AWS Bedrock AgentCore deployment uses direct code deployment for this project's pure-Python agent, not a container build, so don't expect to touch Docker again between Day 11 and the end of the plan.
- GitHub CLI (`brew install gh`)
- GitHub Copilot CLI (install per `docs.github.com/en/copilot/how-tos/copilot-cli` — GA and iterates fast, so follow the current page rather than a remembered command)
- OpenAI Codex CLI — optional third dev-tool choice, alongside Claude Code and GitHub Copilot CLI (§8 explains where it fits): `npm install -g @openai/codex` (or `brew install --cask codex` on macOS; Node.js 18+ required for the npm path). Sign in with `codex` → "Sign in with ChatGPT" — included at no extra cost with ChatGPT Plus/Pro/Business/Edu/Enterprise; pay-per-token API billing is also available but typically costs more for regular use, so prefer the subscription path if you already have one.
- AWS CLI (`brew install awscli`) — installed now, *configured* with real credentials later, once the AWS account exists (`PLAN.md` Appendix B, Day 12)
- VS Code with the Python extension
- GitHub Copilot Desktop app — signed in
- GitHub Copilot app — signed in (needed from Day 8 onward for canvases; confirm access now while you're setting everything else up)
- Claude Code — signed in

---

## 2. Bootstrap the repo

**Recommended path — create the repo on GitHub first, then clone it locally:**

```
gh auth login                                    # one-time, if `gh` isn't already authenticated
gh repo create agentic-pm-lab --public --clone
cd agentic-pm-lab
```

This creates the empty repo on GitHub, then clones it to your machine with the `origin` remote already configured — no separate "init locally, then create on GitHub, then wire up the remote" dance to get wrong before you've written a line of code. `--public` matches this project's own "no company-sensitive data" principle (nothing in it needs to be private); use `--private` instead if you'd rather keep a personal learning repo out of public view while you work, and open it up later.

**Manual alternative**, if you don't have `gh` set up or prefer clicking through the UI:
1. Create the repo at `github.com/new` — don't initialize it with a README or `.gitignore`, since you'll add your own.
2. `git clone https://github.com/<you>/agentic-pm-lab.git && cd agentic-pm-lab`.
3. Everything from here is identical to the `gh`-based path.

**Before your first commit, check two things — fixing them now is a one-line command; fixing them after commits exist takes an amend or a rename:**

1. **Git identity.** Run `git config user.email`. If it's empty, or auto-generated (ends in `.local` — git will also print a warning on your first commit if this is the case), set it for real:
   ```
   git config --global user.name "Your Name"
   git config --global user.email "your-real-email@example.com"
   ```
   If you already committed before catching this, `git commit --amend --reset-author` fixes the most recent commit.

2. **Branch name.** Run `git branch --show-current`. `PLAN.md`'s day-by-day steps assume the branch is called `main` — literal `git push origin main` commands appear throughout. Depending on your git version and config, a fresh repo can default to `master` instead. If it shows `master`, rename it now, before your first push:
   ```
   git branch -m master main
   ```
   Worth setting once, globally, so this doesn't recur on future repos: `git config --global init.defaultBranch main`.

**The very first commit should be the pre-written control-plane documents themselves** — copy `README.md`, `PRD.md`, `PLAN.md`, `PROGRESS.md`, `AGENTS.md`, `REFERENCES.md`, and this file (`INSTALL.md`) into the repo root before writing any code:

```
git add README.md PRD.md PLAN.md PROGRESS.md AGENTS.md REFERENCES.md INSTALL.md
git commit -m "docs: initial README, PRD, PLAN, PROGRESS, AGENTS, REFERENCES, INSTALL"
git push --set-upstream origin main
```

This is the one push in the whole plan that needs `--set-upstream` explicitly — it's the first push of a brand-new repo, so there's no upstream branch for plain `git push` to target yet (you'll see a "no upstream branch" error otherwise). Every push after this one can just be `git push`.

Everything below assumes you're now working from inside the cloned repo.

---

## 3. Python environment & every package the plan needs

```
uv init --no-readme          # creates pyproject.toml + .python-version, once, inside the repo

uv add fastapi uvicorn duckdb pydantic pyyaml streamlit \
    yfinance fredapi \
    statsmodels \
    deepagents anthropic openai \
    opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-exporter-otlp langsmith \
    jsonschema tiktoken \
    pyportfolioopt \
    boto3

uv add --dev pytest ruff pre-commit responses
```

Also add these three, even though they're not *used* until later days — installing everything now means no day after this one requires a new install:
```
uv add mcp                        # official Model Context Protocol Python SDK (modelcontextprotocol.io); first used Day 10
uv add bedrock-agentcore           # AWS's own AgentCore SDK (github.com/aws/bedrock-agentcore-sdk-python); first used Day 12
uv add cedarpy                    # Cedar Python bindings — see the naming warning below; first used Day 7 for policy-as-code (PLAN.md §15)
```

**Naming warning, worth checking again if you're reading this months later:** the PyPI package literally named `cedar-policy` is *not* legitimate — as of this writing it's a version `0.0.1` placeholder with no author, no description, and a fake `github.com/unknown/cedar-policy` source URL (checked via `pypi.org/pypi/cedar-policy/json`). There is no official AWS/cedar-policy-org Python package on PyPI. The de facto standard is the community-maintained **`cedarpy`** (`github.com/k9securityio/cedar-py`), whose version number tracks the Cedar engine's major.minor version — verify the GitHub repo (stars, license, recent commits, release tag matching the PyPI version) before trusting any Cedar-related package name, since this is exactly the kind of name a dependency-confusion attack would squat on. `cedarpy` exposes `is_authorized`, `PolicySet`, and `validate_policies` — enough to both evaluate policies at runtime and syntax-check `.cedar` files in a pre-commit hook, no separate CLI required, though Cedar also ships a standalone CLI (`cedarpolicy.com`) if you'd rather use that for the pre-commit syntax-check hook (`PLAN.md` §11.2) — either is enough to get started, and both can coexist.

Commit `pyproject.toml` and `uv.lock` together:
```
git add pyproject.toml uv.lock
git commit -m "chore: uv project init and dependency install"
git push
```

From here on, run everything through `uv run` (`uv run pytest`, `uv run uvicorn ...`, `uv run python src/ingestion/prices.py`) instead of activating a virtual environment by hand — `uv run` finds and uses the project's environment automatically.

| Package(s) | Group | Purpose | First used |
|---|---|---|---|
| `fastapi`, `uvicorn`, `duckdb`, `pydantic`, `pyyaml`, `streamlit` | runtime | core scaffolding | Day 1 |
| `pytest`, `ruff`, `pre-commit`, `responses` | dev | testing, linting, local quality gates, HTTP mocking | Day 1 (pytest/ruff/responses used from Day 3) |
| `yfinance`, `fredapi` | runtime | public market/macro data ingestion | Day 2 |
| `statsmodels` | runtime | econometrics | Day 3 |
| `jsonschema` | runtime | validates tool/MCP/skill contracts against their JSON Schemas | Day 3 (tool contracts), Day 4 (skill contracts), Day 10 (MCP contracts) |
| `deepagents`, `anthropic`, `openai` | runtime | agent framework and model access | Day 4 |
| `tiktoken` | runtime | token counting for the context-engineering experiment and OTel cost telemetry | Day 4 (context builder), Day 6 (span attributes) |
| `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-exporter-otlp`, `langsmith` | runtime | observability, datasets, and experiments | Day 6 |
| `cedar-policy` (Python bindings) | runtime | policy-as-code evaluation for authorization (`governance/policies/`) | Day 7 |
| MCP server library | runtime | Tool Layer wrapped as MCP | Day 10 |
| `pyportfolioopt` (pulls in `cvxpy` + a solver transitively — heavier than this project's other dependencies, worth knowing) | runtime | mean-variance, max-Sharpe, and risk-parity (HRP) portfolio optimization | Day 12 |
| `boto3` + AgentCore SDK package | runtime | AWS Bedrock AgentCore integration | Day 12 |
| `langchain-ollama` — optional, only if doing the local-model variant (`PLAN.md` §3) | runtime | binds Deep Agents to a local Ollama model | Days 4–6 |

---

## 4. GitHub-specific setup

- **Check your Copilot plan tier first, before hunting for the coding-agent setting** — it requires **Copilot Pro+, not plain Pro.** Click your profile picture (top-right, any GitHub page) → **Settings** (this is your account settings, not the repo's) → in the "Access" section of the sidebar, **Billing & licensing** → **Licensing** (or **Plans and usage**, if you're on GitHub's older billing UI) → under "GitHub Copilot," see **Current plan**. If it says Pro, you'd need to upgrade to Pro+ before the next step is usable — the upgrade option is right there in the same screen. **One easy mix-up to avoid:** "GitHub Pro" (the platform plan — repo hosting, Actions minutes) and "Copilot Pro+" (the Copilot plan) are two separate product lines with confusingly similar names; the tier that matters for coding agent is specifically the Copilot one, not your GitHub account plan.
- **Enable Copilot coding agent for the repo** (GitHub's docs are increasingly calling this **"Cloud agent"** — same feature, naming shift in progress; look for either label): open the repo on GitHub → **Settings** (repo-level this time) → **Copilot** in the sidebar → **Coding agent** (or **Cloud agent**). For a personal, non-organization-owned repo this is generally available by default rather than something to switch on from nothing — you're mainly confirming it isn't opted out.
- **Worth confirming once you're there, not assuming:** whether "automations" (the scheduled/triggered agent runs Day 11's `morning-brief.yml` depends on) are available for a public repo specifically — current docs gave mixed signals on this when checked, distinct from coding-agent access itself. Five minutes of checking the actual toggle state now saves a confusing surprise on Day 11.
- Install Jon Gallant's `create-canvas-app` skill, even though canvas work doesn't start until Day 8:
```
npx skills add jongio/skills --skill create-canvas-app -g --agent github-copilot
```

Writing the project's actual `.pre-commit-config.yaml` (with its specific hooks) and running `uv run pre-commit install` happens on Day 1 itself in `PLAN.md`, since the hook set is part of that day's build — `pre-commit` the tool is already installed via §3 above.

---

## 5. Accounts you'll set up later, and why not now

Software is installed once, here, in one sitting. Accounts are different — a key or cloud credential sitting unused for days is one more thing to forget or let go stale, so each gets set up in `PLAN.md` Appendix B on the specific day it's first needed, with full step-by-step instructions there:

| Account | First needed | Cost |
|---|---|---|
| GitHub (+ Copilot) | Now | Already have, per your existing access |
| Claude (Anthropic) | Now (Claude Code) / Day 4 (agent API key) | Already have, per your existing access |
| OpenAI | Day 4, optional (agent model) / Now, optional (Codex CLI) | Already have, per your existing access |
| FRED (fred.stlouisfed.org) | Day 2 | **Free** — no paid tier exists |
| LangSmith (smith.langchain.com) | Day 6 | **Free tier is sufficient** |
| Ollama | Days 4–6, optional | **Free** — no account needed at all for local-only use |
| Langfuse | Day 6, optional | **Free** if self-hosted, or free tier if using Langfuse Cloud |
| **AWS** | Day 12 | **Pay-as-you-go — the only account in the whole plan with real, variable cost.** Billing/credit card required; Day 12 includes a budget-alert step and ends with tearing resources down. The optional Days 13–14 AWS extension reuses this same account and adds small incremental cost. |

**A note on the OpenAI row specifically, since it's easy to conflate two separate things:** a pay-per-token **API key** for the Portfolio Manager agent's optional alternate model (Day 4), versus a **ChatGPT Plus-or-higher plan** for Codex CLI as a dev tool (§8). If your existing OpenAI access is API-only, Codex CLI still works via that same API key, just typically at higher cost for regular use than a ChatGPT subscription.

**In short: AWS is the one *mandatory* account with real, usage-based cost.** Everything else is free or already covered by access you have — including Codex CLI, if you're using it, as long as your existing OpenAI access is a ChatGPT Plus-or-higher plan or you're comfortable with API billing.

---

## 6. Optional: local-model variant (Ollama)

Only needed if you plan to run the Days 4–6 local-model comparison (`PLAN.md` §3) — skip this section entirely otherwise.

- Ollama itself (`ollama.com`, or `brew install ollama`)
- One or more tool-calling-capable local models, pulled via `ollama pull <model>` (`PLAN.md` §3 has hardware/sizing guidance)
- `langchain-ollama`: `uv add langchain-ollama`
- Optional: Langfuse, self-hosted via Docker, as a local alternative to LangSmith for Day 6

---

## 7. What genuinely can't be done yet

Two things are configured, not installed, and both require a real account to exist first — which is why they wait for their specific day in `PLAN.md` Appendix B rather than living here:
- AWS CLI **credentials** (`aws configure`) — the CLI binary is installed in §1, but there's nothing to configure until the Day 12 AWS account exists.
- Bedrock **model access** — an in-console toggle per model, only meaningful once you're in the AWS console on Day 12.

---

## 8. How to work with Claude Code, GitHub Copilot, and Codex CLI

All three read `AGENTS.md` automatically at the start of a session inside the repo (Codex CLI's own `/init` command is literally "create an AGENTS.md file" — this project's already has one, so that step's done) — that's the entire purpose of that file. In practice, starting a day looks like this:

**Claude Code:**
```
cd agentic-pm-lab
claude
```
Then, in the session: *"Let's do Day 4."* Claude Code picks up `AGENTS.md`'s routing automatically (read `PROGRESS.md`, then `PLAN.md`'s Day 4 section) — the day number is the only thing you need to supply.

**GitHub Copilot CLI:**
```
cd agentic-pm-lab
copilot
```
Same message. Copilot CLI reads `AGENTS.md` the same way (via the `.github/copilot-instructions.md` pointer if it doesn't pick up the repo-root file directly).

**OpenAI Codex CLI:**
```
cd agentic-pm-lab
codex
```
Same message again. Where Codex tends to fit best in this plan: it's a reasonable substitute for Claude Code specifically — deep multi-file reasoning, architecture decisions, debugging unfamiliar APIs (`PLAN.md` §7's tool-guidance table calls out which days lean that way) — if you'd rather use an OpenAI-model-backed tool for that role, or want to compare the two on the same day's work. Codex also has its own on-demand skills mechanism, conceptually the same shape as this project's `skills/` folder, so the shared `SKILL.md` library is likely readable by it too — worth confirming once you're using it regularly, since exact compatibility can shift.

**GitHub Copilot Desktop / the Copilot app:** open the app, select this repo, start a new agent session, and give it the same message. This is the tool of choice specifically for the canvas-building days (8–10) and the Day 11 PR exercise, since those lean on app-specific features (`/create-canvas`, Copilot coding agent) not available from the CLI alone — nothing here substitutes for it.

**A reusable kickoff prompt**, works with any of the three CLI tools:
```
Read PROGRESS.md for current status, then PLAN.md's Appendix B section for Day <N>.
Work through the numbered steps in order, committing at each checkpoint listed
(see PLAN.md's "Git workflow used throughout" for the exact commands).
Ask me before anything that needs an account or API key I haven't set up yet.
```

**Checking real usage, per tool** — this is the raw data `docs/comparison-notes.md` (dev-tool section) wants logged; nothing tracks it for you automatically, each tool just reports on itself differently:
- **Claude Code:** run `/usage` (or `/status`) inside a session — shows your current 5-hour rolling window and weekly quota, both as a percentage with reset times. If you're billing via an API key rather than a subscription, `/cost` shows the running spend for that session instead. For account-level history, `Settings → Usage` on claude.ai.
- **GitHub Copilot:** since June 2026, Copilot runs on usage-based AI Credits on individual plans too, not just team/enterprise — check the Copilot usage dashboard under your GitHub account settings for the current credit balance and burn rate.
- **Codex CLI:** `/status` inside a session shows the current session's configuration; for account-level credit/usage detail, check your ChatGPT account's usage page. Codex's self-serve usage reporting is less granular than Claude Code's as of this writing — verify what's actually shown against OpenAI's current docs rather than assuming parity.

**Which tool for which day** is summarized in `PLAN.md` §7's per-day table and repeated in `AGENTS.md`'s quick reference — that's a default, not a rule. Any of the three CLI tools works any day (the canvas days and Day 11's PR exercise still need the Copilot app specifically for the parts that touch it), and switching mid-day is expected (Day 8 deliberately uses both Copilot surfaces already).

---

## 9. Verification checklist — confirm you're ready for Day 1

- [ ] `python3 --version` shows 3.11 or higher
- [ ] `uv --version` runs
- [ ] `docker info` (or `docker ps`) runs without a "Cannot connect to the Docker daemon" error — confirms Desktop is actually open and running, not just installed (`docker --version` alone won't catch a closed Desktop app, since it only checks the CLI binary)
- [ ] `gh auth status` shows you're logged in
- [ ] `copilot --version` (or equivalent) runs
- [ ] `codex --version` runs, and `codex` then "Sign in with ChatGPT" completes successfully (optional — only if you plan to use Codex CLI)
- [ ] `aws --version` runs (credentials come later, on Day 12 — just confirm the CLI itself is installed)
- [ ] The repo is cloned locally, with `origin` pointing at your GitHub repo (`git remote -v`), the current branch is `main` (`git branch --show-current`), and `git config user.email` shows a real address, not an auto-generated `.local` one
- [ ] `README.md`, `PRD.md`, `PLAN.md`, `PROGRESS.md`, `AGENTS.md`, `REFERENCES.md`, and this file are committed and pushed
- [ ] `pyproject.toml` and `uv.lock` exist and are committed; `uv run python -c "import fastapi, deepagents, boto3, jsonschema, tiktoken"` succeeds with no import errors (add `import cedarpy` to this same check once Day 7 arrives and it's actually wired up)
- [ ] Copilot coding agent is enabled in repo Settings
- [ ] `npx skills add jongio/skills --skill create-canvas-app -g --agent github-copilot` completed without error
- [ ] Claude Code and GitHub Copilot CLI both start successfully inside the repo directory (plus Codex CLI, if using it)
- [ ] Optional, only if doing the local-model variant: `ollama --version` runs and at least one model is pulled (`ollama list`)
- [ ] **`PROGRESS.md`'s "Environment setup" line updated from ⬜ to ✅**, and that change committed and pushed — nothing else in this project flips that checkbox automatically, since `progress-tracker.yml` (the mechanism that auto-updates everything else in `PROGRESS.md`) isn't built until Day 1 itself; this one line has to be done by hand, here, or it just sits stale forever

Once every box here is checked, open `PLAN.md` and start Day 1 — its own steps begin from the mock data layer, since the repo and environment are already in place.
