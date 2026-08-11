# REFERENCES: Curated Reading, by Topic

One or two best starting points per topic, favoring official docs and hands-on tutorials over general blog posts — not exhaustive. This is the single, canonical copy: update it directly as you find something genuinely useful or a link goes stale, rather than maintaining a separate mirror elsewhere.

**How this is used day to day:** you don't need to browse this whole file mid-session. Each day in `PLAN.md`'s Appendix B has its own short "While it builds, read" list (1–5 items) pointing at the specific subsection below that's relevant to that day's work — this file is the full bibliography those pointers link into, for whenever you want the complete picture on a topic rather than just today's slice.

---

### Origins & inspiration

Not a "read before Day N" entry like the sections below — this is the source of the core idea, worth reading once for context rather than as day-specific prep.

- **OpenAI Cookbook: "Multi-Agent Portfolio Collaboration with OpenAI Agents SDK"** (Raj Pathak, Chelsea Hu) — `developers.openai.com/cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration`. This is where the Portfolio-Manager-orchestrating-Macro/Fundamental/Quant-specialists pattern that structures this entire project comes from — a Portfolio Manager agent using specialist agents *as tools* to solve an investment research problem, built there on OpenAI's Agents SDK. This project translates the same pattern onto LangGraph Deep Agents' native `subagents` mechanism instead (`PRD.md` §1, `PLAN.md` Day 5) — worth reading the original once to see the pattern in its native habitat before building the LangGraph version, and worth a second look on Day 5 specifically to compare the two frameworks' takes on the same idea (agents-as-tools vs. native sub-agent spawning).

---

### FastAPI & DuckDB (Day 1 foundation)
- FastAPI official tutorial: `fastapi.tiangolo.com/tutorial/`
- DuckDB Python API guide: `duckdb.org/docs/api/python/overview`

### LangGraph & LangGraph Deep Agents
- **Where this project's multi-agent pattern originally comes from**: OpenAI's own cookbook, "Multi-Agent Portfolio Collaboration with the Agents SDK" (Raj Pathak, Chelsea Hu) — the Portfolio-Manager-orchestrates-Macro/Fundamental/Quant-specialists shape that Day 5 reimplements natively on LangGraph Deep Agents' `subagents` support instead of the OpenAI Agents SDK. Worth reading directly before Day 5, not just taking the reimplementation on faith: `developers.openai.com/cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration`
- Deep Agents overview and quickstart: `docs.langchain.com/oss/python/deepagents`
- Deep Agents GitHub repo (source, examples, issues): `github.com/langchain-ai/deepagents`
- LangGraph core concepts (the runtime Deep Agents sits on): `docs.langchain.com` LangGraph section
- LangGraph human-in-the-loop / `interrupt` patterns (used Day 4 and Day 7): `docs.langchain.com` LangGraph "Human-in-the-loop" section
- `langchain-ai/langchain-skills` — official example skills and quickstarts, including the `SKILL.md` format spec

### LangSmith (tracing, datasets, experiments, evaluation)
- LangSmith evaluation docs (datasets, experiments, evaluators): `docs.langchain.com/langsmith/evaluation`
- LangSmith quickstart (sign up, first trace, first eval): `smith.langchain.com` → Settings → API Keys, then the in-product quickstart
- LangSmith + pytest / GitHub Actions integration, for wiring `eval-regression.yml`: LangSmith docs, "Test before you ship" section

### Context engineering (Day 4, PLAN.md §13)
- Anthropic's "Effective context engineering for AI agents" — the conceptual grounding for treating context assembly as its own deliberate layer rather than incidental prompt accumulation
- LangGraph/LangChain context management docs (memory, summarization, trimming) — the concrete APIs `src/context/` builds on

### OpenTelemetry (Python)
- Official Python getting-started guide: `opentelemetry.io/docs/languages/python/getting-started/`
- FastAPI auto-instrumentation reference: `opentelemetry-python-contrib.readthedocs.io`, `instrumentation/fastapi`
- OpenTelemetry Collector docs, if you add a local Jaeger/Collector service in Docker Compose
- OpenTelemetry GenAI semantic conventions (token counts, model, cost attributes) — the standard attribute names to use when extending spans with cost/token telemetry (Day 6): `opentelemetry.io/docs/specs/semconv/gen-ai/`

### Model Context Protocol (MCP)
- Official spec and docs: `modelcontextprotocol.io`
- Python SDK: the official `mcp` package on PyPI and its README/examples
- GitHub's own MCP context docs (for wiring a server into Copilot): `docs.github.com/en/copilot/concepts/context/mcp`

### AWS Bedrock & AgentCore
- Main AgentCore documentation hub: `docs.aws.amazon.com/bedrock-agentcore/`
- Quickstart (CLI, zero to running agent): `docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-get-started-cli.html`
- Runtime deployment methods — direct code deployment (Python) vs. container-based (Dockerfile → ECR), the choice made explicit in Day 12: `docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-getting-started.html`
- "Diving Deep into Bedrock AgentCore" official workshop (hands-on, service-by-service labs): `catalog.workshops.aws/agentcore-deep-dive`
- Samples repo (Python examples across Gateway, Memory, Identity, Observability): `github.com/awslabs/agentcore-samples`
- AgentCore Memory (short-term/long-term agent memory): `docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html`
- AgentCore Evaluations: `docs.aws.amazon.com/bedrock-agentcore/latest/devguide/evaluations.html`
- Bedrock Guardrails: `docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html`
- Bedrock custom models / fine-tuning (Day 14 optional stretch): `docs.aws.amazon.com/bedrock/latest/userguide/custom-models.html`
- AWS Cost Explorer (Day 14 optional cost review): `docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html`

### AWS IAM & account basics (Day 12 account setup)
- IAM users, groups, and policies overview: `docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html`
- AWS Budgets (for the Day 12 budget-alert step): `docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html`

### Security: AuthN/AuthZ, policy-as-code, prompt injection (Day 7, PLAN.md §15)
- Cedar policy language docs and playground: `cedarpolicy.com`, `docs.cedarpolicy.com`
- OWASP Top 10 for LLM Applications — prompt injection, sensitive information disclosure, excessive agency are the entries most relevant to the negative tests in `governance/tests/`: `owasp.org/www-project-top-10-for-large-language-model-applications/`
- AWS Verified Permissions (Cedar-based, managed) — worth reading even if this project's own Cedar setup stays local/learning-scale, since it's the natural production analog: `docs.aws.amazon.com/verifiedpermissions/`

### GitHub Copilot App, Canvas, Prompts, Skills, Custom Agents
- Canvas extensions how-to: `docs.github.com/en/copilot/how-tos/github-copilot-app/working-with-canvas-extensions`
- "How to build interactive experiences with canvases" (best conceptual tutorial): GitHub Blog, AI & ML / GitHub Copilot section
- "GitHub Copilot app for Beginners: Getting started" (Canvas Dev Mode, Pick & Polish, Agent Merge): GitHub Blog
- Jon Gallant's `create-canvas-app` skill and blog series: `blog.jongallant.com`, repo `github.com/jongio/skills`
- Prompt files: `docs.github.com/en/copilot/tutorials/customization-library/prompt-files/your-first-prompt-file`
- Custom agents: `docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/create-custom-agents`
- Creating and using personal custom agents in Copilot CLI (including the
  `~/.copilot/agents/` scope):
  `docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/create-custom-agents-for-cli`
- Agent skills reference: `docs.github.com/en/copilot/concepts/agents/about-agent-skills`
- GitHub Actions scheduled workflows (`on: schedule`, cron syntax), for `morning-brief.yml`: `docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#schedule`

### OpenAI Codex CLI (optional alternative dev tool — `INSTALL.md` §8)
- Official CLI reference and overview: `developers.openai.com/codex/cli`
- AGENTS.md guide: `developers.openai.com/codex` — Codex's own conceptual overview of the same file this project already uses for routing
- npm package (install source): `npmjs.com/package/@openai/codex`

### Public data APIs
- FRED API docs: `fred.stlouisfed.org/docs/api/fred/`
- FRED's Treasury yield curve series (the specific series Day 2 pulls to build `curve_points`): search FRED for "Treasury Constant Maturity Rate" (series like `DGS2`, `DGS10`, `DGS30`) — `fred.stlouisfed.org`
- yfinance package docs/README: `pypi.org/project/yfinance`
- SEC EDGAR full-text search and submissions APIs: `sec.gov/edgar/sec-api-documentation`

### Python testing & mocking
- `pytest` documentation, especially fixtures and markers (for the `unit`/`eval` split in PLAN.md §4): `docs.pytest.org`
- `unittest.mock` standard library docs, for mocking network calls
- `responses` library (mocking `requests`-based HTTP calls like yfinance/FRED): its PyPI/GitHub README
- LangChain's testing utilities for fake/scripted chat models (used in `src/agents/` tests, PLAN.md §4)

### Quant/fixed-income formulas (Day 3 tool layer)
- `statsmodels` OLS regression docs (used for the factor regression tool): `statsmodels.org/stable/regression.html`
- Investopedia: bond pricing, duration, and convexity — plain-language first pass before implementing `src/analytics/pricers.py`
- Investopedia: Black-Scholes model — plain-language first pass before implementing the option pricer
- Investopedia: yield curve construction and interpolation — before implementing `src/analytics/curves.py`; covers what "bootstrapping" a curve from discrete tenor points actually means
- Investopedia: credit spreads (and OAS — option-adjusted spread) — before the scenario engine's credit-shock path (Day 12) and PRD.md §4's spread-risk questions
- Investopedia: mortgage-backed securities and negative convexity — a genuinely distinct concept from plain bond convexity (prepayment risk flips the sign), directly relevant to PRD.md §4's "how does mortgage convexity affect the portfolio" question
- Investopedia: volatility, maximum drawdown, and correlation as risk metrics — before implementing `src/analytics/risk.py`; these currently have no dedicated primer elsewhere in this file, easy to assume they're self-explanatory and skip
- Investopedia: factor investing / factor models, conceptual overview — read before `statsmodels`' API docs above, since the API is easy to use correctly while still not knowing what a "factor" means economically

### Portfolio optimization (Day 12)
- `PyPortfolioOpt` documentation hub (the library `src/analytics/optimizer.py` is built on): `pyportfolioopt.readthedocs.io`
- `PyPortfolioOpt` User Guide, mean-variance optimization section specifically (`EfficientFrontier`, `min_volatility()`, `max_sharpe()`): `pyportfolioopt.readthedocs.io/en/latest/UserGuide.html`
- `PyPortfolioOpt` cookbook notebook on mean-variance optimization (a full worked example, download-to-allocation): `github.com/robertmartin8/PyPortfolioOpt`, `cookbook/2-Mean-Variance-Optimisation.ipynb`
- Harry Markowitz, "Portfolio Selection," *Journal of Finance*, 1952 — the original paper behind mean-variance optimization; PyPortfolioOpt's own docs cite it directly as the theoretical basis for `EfficientFrontier`. Investopedia's "Modern Portfolio Theory" page is a reasonable plain-language substitute if the original paper is more than you want today.
- Investopedia: the efficient frontier and the Sharpe ratio — what `max_sharpe()` is actually maximizing, and why "highest return" alone isn't the optimization target
- Investopedia (or PyPortfolioOpt's own HRP documentation page): Hierarchical Risk Parity — the conceptual difference between "equal risk contribution" (risk parity) and "maximum risk-adjusted return" (mean-variance), since `optimize_risk_parity()` and `optimize_max_sharpe()` are answering genuinely different questions, not two ways of asking the same one

### FICC / fixed income fundamentals
- Investopedia's fixed-income section, for plain-language first passes at any term before it goes in `docs/ficc-glossary.md`
- U.S. Treasury interest-rate statistics, the public source used for the yield
  curve glossary entry: `home.treasury.gov/resource-center/data-chart-center/interest-rates`
- FINRA's duration primer, used for the Day 2 glossary definition:
  `finra.org/investors/insights/duration-what-interest-rate-hike-could-do-your-bond-portfolio`
- A standard CFA-curriculum-level fixed income text, if you want a more rigorous second pass once the practical vocabulary from building the tools is in place

### Git & version control
- `git-scm.com/doc` — the official Git reference, especially `git commit`, `git push`, and `git tag`
- GitHub's own "About pull requests" and "Conventional Commits" (`conventionalcommits.org`), for the commit-message convention used throughout Appendix B

### Pre-commit & CI tooling
- `pre-commit` framework docs: `pre-commit.com`
- `ruff` docs (linting + formatting): `docs.astral.sh/ruff`
- `detect-secrets` (`github.com/Yelp/detect-secrets`) or `gitleaks` (`github.com/gitleaks/gitleaks`) — pick one, both are well-documented
- `uv` docs (dependency management, this project's package manager — PLAN.md §1, `INSTALL.md`): `docs.astral.sh/uv`
