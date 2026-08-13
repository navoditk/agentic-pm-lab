# REFERENCES: Curated Reading, by Topic

One or two best starting points per topic, favoring official docs and hands-on tutorials over general blog posts — not exhaustive. This is the single, canonical copy: update it directly as you find something genuinely useful or a link goes stale, rather than maintaining a separate mirror elsewhere.

**How this is used day to day:** you don't need to browse this whole file mid-session. Each day in `docs/PLAN.md`'s Appendix B has its own short "While it builds, read" list (1–5 items) pointing at the specific subsection below that's relevant to that day's work — this file is the full bibliography those pointers link into, for whenever you want the complete picture on a topic rather than just today's slice.

---

### Origins & inspiration

Not a "read before Day N" entry like the sections below — this is the source of the core idea, worth reading once for context rather than as day-specific prep.

- **OpenAI Cookbook: "Multi-Agent Portfolio Collaboration with OpenAI Agents SDK"** (Raj Pathak, Chelsea Hu) — `developers.openai.com/cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration`. This is where the Portfolio-Manager-orchestrating-Macro/Fundamental/Quant-specialists pattern that structures this entire project comes from — a Portfolio Manager agent using specialist agents *as tools* to solve an investment research problem, built there on OpenAI's Agents SDK. This project translates the same pattern onto LangGraph Deep Agents' native `subagents` mechanism instead (`docs/PRD.md` §1, `docs/PLAN.md` Day 5) — worth reading the original once to see the pattern in its native habitat before building the LangGraph version, and worth a second look on Day 5 specifically to compare the two frameworks' takes on the same idea (agents-as-tools vs. native sub-agent spawning).

---

### FastAPI & DuckDB (Day 1 foundation)
- FastAPI official tutorial: `fastapi.tiangolo.com/tutorial/`
- DuckDB Python API guide: `duckdb.org/docs/api/python/overview`

### LangGraph & LangGraph Deep Agents
- **Where this project's multi-agent pattern originally comes from**: OpenAI's own cookbook, "Multi-Agent Portfolio Collaboration with the Agents SDK" (Raj Pathak, Chelsea Hu) — the Portfolio-Manager-orchestrates-Macro/Fundamental/Quant-specialists shape that Day 5 reimplements natively on LangGraph Deep Agents' `subagents` support instead of the OpenAI Agents SDK. Worth reading directly before Day 5, not just taking the reimplementation on faith: `developers.openai.com/cookbook/examples/agents_sdk/multi-agent-portfolio-collaboration/multi_agent_portfolio_collaboration`
- Deep Agents overview and quickstart: `docs.langchain.com/oss/python/deepagents`
- Deep Agents customization reference (`tools`, `skills`, `interrupt_on`, and
  provider model strings), used on Day 4:
  `docs.langchain.com/oss/python/deepagents/customization`
- Deep Agents GitHub repo (source, examples, issues): `github.com/langchain-ai/deepagents`
- LangGraph core concepts (the runtime Deep Agents sits on): `docs.langchain.com` LangGraph section
- LangGraph human-in-the-loop / `interrupt` patterns (used Day 4 and Day 7): `docs.langchain.com` LangGraph "Human-in-the-loop" section
- Ollama tool-calling documentation and the Qwen3 4B model page, used for the
  optional Day 4 local variant: `docs.ollama.com/capabilities/tool-calling` and
  `ollama.com/library/qwen3:4b`
- `langchain-ai/langchain-skills` — official example skills and quickstarts, including the `SKILL.md` format spec

### LangSmith (tracing, datasets, experiments, evaluation)
- LangSmith evaluation docs (datasets, experiments, evaluators): `docs.langchain.com/langsmith/evaluation`
- LangSmith quickstart (sign up, first trace, first eval): `smith.langchain.com` → Settings → API Keys, then the in-product quickstart
- LangSmith + pytest / GitHub Actions integration, for wiring `eval-regression.yml`: LangSmith docs, "Test before you ship" section

### Context engineering (Day 4, docs/PLAN.md §13)
- Anthropic's "Effective context engineering for AI agents" — the conceptual grounding for treating context assembly as its own deliberate layer rather than incidental prompt accumulation
- LangGraph/LangChain context management docs (memory, summarization, trimming) — the concrete APIs `src/context/` builds on
- Anthropic, [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — context as a finite, managed resource with progressive disclosure and task-specific retrieval
- OpenAI, [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/) — repository maps, durable artifacts, instruction layering, and making context legible to agents
- Anthropic, [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) — initializer/coding-agent separation, resumable work, and cross-session artifacts
- OpenAI, [Unrolling the Codex agent loop](https://openai.com/index/unrolling-the-codex-agent-loop/) — the model loop, tool execution, and the harness responsibilities around an agent

### OpenTelemetry (Python)
- Official Python getting-started guide: `opentelemetry.io/docs/languages/python/getting-started/`
- FastAPI auto-instrumentation reference: `opentelemetry-python-contrib.readthedocs.io`, `instrumentation/fastapi`
- OpenTelemetry Collector docs, if you add a local Jaeger/Collector service in Docker Compose
- OpenTelemetry GenAI semantic conventions (token counts, model, cost attributes) — the standard attribute names to use when extending spans with cost/token telemetry (Day 6): `opentelemetry.io/docs/specs/semconv/gen-ai/`

### Model Context Protocol (MCP)
- Official spec and docs: `modelcontextprotocol.io`
- Python SDK: the official `mcp` package on PyPI and its README/examples
- GitHub's own MCP context docs (for wiring a server into Copilot): `docs.github.com/en/copilot/concepts/context/mcp`
- Anthropic, [MCP documentation](https://docs.anthropic.com/en/docs/mcp) — protocol concepts and how MCP connects models to tools and context

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
- AWS multi-agent investment research assistant using quantitative analysis,
  news/research, summarization, Bedrock Data Automation, S3, OpenSearch, and
  Lambda. Use it as an architecture comparison, not a replacement for the
  Deep Agents implementation:
  [AWS investment research assistant](https://aws.amazon.com/blogs/machine-learning/part-3-building-an-ai-powered-assistant-for-investment-research-with-multi-agent-collaboration-in-amazon-bedrock-and-amazon-bedrock-data-automation/)
- AWS guidance for investment analysis using structured and unstructured data:
  [Investment analysis using Amazon Bedrock](https://docs.aws.amazon.com/solutions/investment-analysis-using-amazon-bedrock/)
- LinqAlpha Devil's Advocate case study: independent thesis challenge,
  evidence-linked rebuttals, and machine-readable outputs:
  [LinqAlpha Devil's Advocate](https://aws.amazon.com/blogs/machine-learning/how-linqalpha-assesses-investment-theses-using-devils-advocate-on-amazon-bedrock/)
- AWS Deep Agents and AgentCore context-rich research pattern, including
  browser, code interpretation, memory, and evaluation:
  [Context-rich research agents](https://aws.amazon.com/blogs/machine-learning/build-context-rich-research-agents-with-deep-agents-and-bedrock-agentcore/)
- AWS AgentCore AgentOps guidance covering governance, operations, evaluation,
  and observability as separate production pillars:
  [AgentOps with AgentCore](https://aws.amazon.com/blogs/machine-learning/agentops-operationalize-agentic-ai-at-scale-with-amazon-bedrock-agentcore/)
- AWS AgentCore samples, including runtime, memory, gateway, policy, and
  observability labs: [AgentCore samples](https://github.com/awslabs/amazon-bedrock-agent-samples)
- AWS getting-started AgentCore labs:
  [Runtime and Memory samples](https://github.com/aws-samples/sample-getting-started-with-amazon-agentcore)
- AWS multi-agent orchestration guidance:
  [Multi-agent orchestration on AWS](https://docs.aws.amazon.com/solutions/multi-agent-orchestration-on-aws/)
- AWS video: [AgentCore introduction](https://www.youtube.com/watch?v=9LF6rz6Fe1Q)
- AWS video: [AgentCore observability](https://www.youtube.com/watch?v=i2Pxnck_3tY)
- AWS video/session: [Architecting multi-agent systems with AgentCore](https://builder.aws.com/content/3FeE9KhL4DUukPB5s4GgNwlspyJ/aws-tech-tales-or-s5-e19-or-architecting-multi-agent-systems-with-aws-bedrock-agentcore)
- AWS re:Invent session: [How Yahoo Finance built multi-agent research systems](https://www.classcentral.com/course/youtube-aws-re-invent-2025-how-yahoo-finance-built-research-multi-agent-systems-with-gen-ai-sps321-509393)

### AWS IAM & account basics (Day 12 account setup)
- IAM users, groups, and policies overview: `docs.aws.amazon.com/IAM/latest/UserGuide/introduction.html`
- AWS Budgets (for the Day 12 budget-alert step): `docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html`

### Security: AuthN/AuthZ, policy-as-code, prompt injection (Day 7, docs/PLAN.md §15)
- Cedar policy language docs and playground: `cedarpolicy.com`, `docs.cedarpolicy.com`
- OWASP Top 10 for LLM Applications — prompt injection, sensitive information disclosure, excessive agency are the entries most relevant to the negative tests in `governance/tests/`: `owasp.org/www-project-top-10-for-large-language-model-applications/`
- AWS Verified Permissions (Cedar-based, managed) — worth reading even if this project's own Cedar setup stays local/learning-scale, since it's the natural production analog: `docs.aws.amazon.com/verifiedpermissions/`
- AWS security and enterprise best practices for AgentCore:
  [AI agents in enterprises](https://aws.amazon.com/blogs/machine-learning/ai-agents-in-enterprises-best-practices-with-amazon-bedrock-agentcore/)

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

### Agent harnesses, skills, prompts, and custom agents
- OpenAI, [A practical guide to building agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/) — tools, instructions, manager/decentralized orchestration, guardrails, and human intervention
- OpenAI, [New tools for building agents](https://openai.com/index/new-tools-for-building-agents/) — Agents SDK concepts: tools, handoffs, guardrails, and tracing
- OpenAI, [The next evolution of the Agents SDK](https://openai.com/index/the-next-evolution-of-the-agents-sdk/) — harnesses, skills, MCP, AGENTS.md, sandboxing, memory, approvals, and long-running work
- OpenAI, [Unlocking the Codex harness](https://openai.com/index/unlocking-the-codex-harness/) — separating the agent harness from product surfaces and reusing an app-server protocol
- Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — when to use workflows versus agents, prompt chaining, routing, parallelization, orchestrator-workers, and evaluator-optimizer patterns

### Tutor-agent study map
- Use `portfolio-construction-tutor` with the [portfolio optimization and
  portfolio construction](#portfolio-optimization-and-portfolio-construction)
  reading path.
- Use `agent-architecture-tutor` and `langgraph-deep-agents-tutor` with the
  LangGraph, Deep Agents, context engineering, skills, and agent-harness
  resources above.
- Use `aws-agentcore-tutor` with the [AWS Bedrock & AgentCore](#aws-bedrock--agentcore)
  section and the official AgentCore workshops and samples.
- Use `data-provenance-research-tutor` with the public-data, point-in-time,
  SEC EDGAR, sentiment, and backtesting sections.
- Use `evaluation-agentops-tutor` and `opentelemetry-tutor` with the
  OpenTelemetry, LangSmith, AgentCore Evaluations, and AgentOps resources.
- Use `investment-committee-tutor` with the AWS investment-research and
  LinqAlpha Devil's Advocate examples.
- Use `copilot-canvas-mcp-tutor` with the GitHub Copilot Canvas and MCP
  documentation and the repository's Canvas capability tests.
- Anthropic, [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — multi-turn evaluation design, trajectory checks, and using tests as the ground truth
- Anthropic, [Writing effective tools for agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — tool descriptions and interfaces as part of the agent-control surface
- Anthropic, [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — parallel research, synthesis, context budgets, and research-agent tradeoffs
- Anthropic, [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — progressive disclosure, reusable skills, and tool/context packaging
- Anthropic, [Agents for financial services](https://www.anthropic.com/news/finance-agents) — reference patterns combining skills, governed connectors, subagents, long-running sessions, and auditability in finance
- AWS, [AgentCore resources and technical walkthroughs](https://aws.amazon.com/bedrock/agentcore/resources/) — videos and hands-on material across Runtime, Memory, Gateway, Identity, Policy, Observability, and Evaluations

### OpenAI Codex CLI (optional alternative dev tool — `INSTALL.md` §8)
- Official CLI reference and overview: `developers.openai.com/codex/cli`
- AGENTS.md guide: `developers.openai.com/codex` — Codex's own conceptual overview of the same file this project already uses for routing
- npm package (install source): `npmjs.com/package/@openai/codex`

### Public data APIs
- FRED API docs: `fred.stlouisfed.org/docs/api/fred/`
- FRED/ALFRED real-time periods and vintage dates, essential for avoiding
  revised-data leakage in backtests:
  `fred.stlouisfed.org/docs/api/fred/realtime_period.html`
- FRED's Treasury yield curve series (the specific series Day 2 pulls to build `curve_points`): search FRED for "Treasury Constant Maturity Rate" (series like `DGS2`, `DGS10`, `DGS30`) — `fred.stlouisfed.org`
- U.S. Treasury daily interest-rate XML feeds, including nominal and real
  yield curves, bill rates, and long-term rates:
  `home.treasury.gov/treasury-daily-interest-rate-xml-feed`
- yfinance package docs/README: `pypi.org/project/yfinance`
- SEC EDGAR full-text search and submissions APIs: `sec.gov/edgar/sec-api-documentation`
- SEC Form N-PORT public datasets for monthly fund and ETF holdings:
  `sec.gov/data-research/sec-markets-data/form-n-port-data-sets`
- FINRA TRACE trade activity and licensing overview. Useful for fixed-income
  liquidity exercises, but professional transaction-level access may be paid
  or restricted: `finra.org/filing-reporting/trace/data`
- FINRA Fixed Income API datasets, including Treasury aggregates, breadth, and
  capped-volume datasets: `developer.finra.org/node/1171`
- Kenneth French Data Library: daily/monthly factors, portfolios, and
  international returns for factor regression and backtest validation:
  `mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html`
- GDELT Project event and Global Knowledge Graph codebooks for public news and
  event metadata. Treat automated tone as a noisy feature, not truth:
  `github.com/GDELT-API` and `data.gdeltproject.org/documentation/`

### Data engineering, provenance, and research correctness
- ALFRED vintage-aware observations: `fred.stlouisfed.org/docs/api/fred/alfred.html`
- Pandas time-series and timezone handling:
  `pandas.pydata.org/docs/user_guide/timeseries.html`
- Apache Arrow and Parquet metadata concepts for immutable research snapshots:
  `arrow.apache.org/docs/` and `parquet.apache.org/docs/`
- Great Expectations or Soda for a later data-quality validation layer:
  `docs.greatexpectations.io` or `docs.soda.io`

### News, sentiment, and research retrieval
- SEC filing text is the preferred first sentiment extension because it is
  attributable, issuer-linked, and tied to filing timestamps.
- GDELT is useful for event counts, themes, geography, and source diversity;
  prefer the raw event/GKG codebooks over treating generated summaries as
  ground truth.
- For every news connector, study robots, terms, and licensing before caching
  or redistributing article text. Store references and permitted excerpts.

### Backtesting and portfolio construction realism
- Add tests for look-ahead bias, survivorship bias, stale prices, corporate
  actions, transaction costs, slippage, turnover, liquidity, rebalance timing,
  and infeasible constraints before adding model sophistication.
- Use the Kenneth French library as a public factor benchmark, while documenting
  publication cadence, missing data, and return units.
- Extend PyPortfolioOpt exercises with bounds, leverage, concentration,
  transaction costs, turnover, and infeasible-constraint behavior.
- Use [vectorbt](https://vectorbt.dev/) as an optional research/backtesting
  comparison for vectorized portfolio simulations and parameter sweeps; keep
  the repository's deterministic backtest as the reference implementation so
  the learning path does not hide assumptions inside a large framework.
- Read [skfolio's model-selection guide](https://skfolio.org/user_guide/model_selection.html)
  for walk-forward, purged, embargoed, and randomized validation designed for
  financial time series. This is a study/reference path before adding the
  dependency.

### Python testing & mocking
- `pytest` documentation, especially fixtures and markers (for the `unit`/`eval` split in docs/PLAN.md §4): `docs.pytest.org`
- `unittest.mock` standard library docs, for mocking network calls
- `responses` library (mocking `requests`-based HTTP calls like yfinance/FRED): its PyPI/GitHub README
- LangChain's testing utilities for fake/scripted chat models (used in `src/agents/` tests, docs/PLAN.md §4)

### Quant/fixed-income formulas (Day 3 tool layer)
- `statsmodels` OLS regression docs (used for the factor regression tool): `statsmodels.org/stable/regression.html`
- Investopedia: bond pricing, duration, and convexity — plain-language first pass before implementing `src/analytics/pricers.py`
- Investopedia: Black-Scholes model — plain-language first pass before implementing the option pricer
- Investopedia: yield curve construction and interpolation — before implementing `src/analytics/curves.py`; covers what "bootstrapping" a curve from discrete tenor points actually means
- Investopedia: credit spreads (and OAS — option-adjusted spread) — before the scenario engine's credit-shock path (Day 12) and docs/PRD.md §4's spread-risk questions
- Investopedia: mortgage-backed securities and negative convexity — a genuinely distinct concept from plain bond convexity (prepayment risk flips the sign), directly relevant to docs/PRD.md §4's "how does mortgage convexity affect the portfolio" question
- Investopedia: volatility, maximum drawdown, and correlation as risk metrics — before implementing `src/analytics/risk.py`; these currently have no dedicated primer elsewhere in this file, easy to assume they're self-explanatory and skip
- Investopedia: factor investing / factor models, conceptual overview — read before `statsmodels`' API docs above, since the API is easy to use correctly while still not knowing what a "factor" means economically
- Investor.gov's beta glossary entry, used for the Day 3 factor-beta definition:
  `investor.gov/introduction-investing/investing-basics/glossary/beta`
- Investopedia's Sharpe-ratio primer, used alongside the backtest metric:
  `investopedia.com/terms/s/sharperatio.asp`

### Portfolio optimization and portfolio construction

Use this as a staged reading path: first understand the investment decision,
then the optimizer, then the estimation and implementation risks around it.

#### Current project foundation
- [PyPortfolioOpt documentation](https://pyportfolioopt.readthedocs.io/en/latest/)
  and its [User Guide](https://pyportfolioopt.readthedocs.io/en/latest/UserGuide.html):
  the current library behind `src/analytics/optimizer.py`, including efficient
  frontiers, constraints, shrinkage, Black-Litterman, and HRP.
- [PyPortfolioOpt cookbook](https://github.com/robertmartin8/PyPortfolioOpt/tree/master/cookbook),
  especially the [mean-variance notebook](https://github.com/robertmartin8/PyPortfolioOpt/blob/master/cookbook/2-Mean-Variance-Optimisation.ipynb)
  and the [Black-Litterman notebook](https://github.com/robertmartin8/PyPortfolioOpt/blob/master/cookbook/4-Black-Litterman-Allocation.ipynb).
- [Markowitz, “Portfolio Selection” (1952)](https://doi.org/10.2307/2975974):
  the original mean-variance framing; read alongside the project warning that
  expected returns and covariance are estimates, not facts.
- [PyPortfolioOpt Black-Litterman guide](https://pyportfolioopt.readthedocs.io/en/latest/BlackLitterman.html):
  a practical bridge from PM views and confidence to expected-return inputs.
- [PyPortfolioOpt HRP guide](https://pyportfolioopt.readthedocs.io/en/latest/OtherOptimizers.html):
  why hierarchical risk parity is different from maximizing Sharpe ratio.

#### Constraints, solvers, and institutional realism
- [CVXPY documentation](https://www.cvxpy.org/) and its [finance/portfolio examples](https://www.cvxpy.org/examples/):
  the explicit convex-modeling layer underneath PyPortfolioOpt. CVXPY is
  currently present transitively through PyPortfolioOpt; it is not yet a new
  direct application dependency because the project has not added a custom
  optimization model.
- [Cvxportfolio manual](https://www.cvxportfolio.com/en/stable/manual.html):
  the strongest cookbook-style reference for multi-period policies, leverage,
  transaction costs, holding costs, constraints, and backtesting. Treat it as
  a future comparison framework, not a replacement for this repo's tool
  boundary.
- [Riskfolio-Lib documentation](https://riskfolio-lib.readthedocs.io/en/latest/):
  useful for downside/CVaR, robust, Black-Litterman, factor-risk, tracking
  error, turnover, cardinality, and risk-budgeting comparisons. It is broader
  than the current learning slice and should be evaluated in an isolated
  extension rather than added to the core environment immediately.
- [Riskfolio-Lib convex portfolio models](https://riskfolio-lib.readthedocs.io/en/latest/riskfoliolib/portfolio.html):
  worked reference for alternative risk measures and factor risk-contribution
  constraints.

#### Estimation risk, validation, and robustness
- [skfolio](https://skfolio.org/) and its [walk-forward/model-selection guide](https://skfolio.org/user_guide/model_selection.html):
  a modern scikit-learn-compatible comparison for covariance estimators,
  shrinkage, robust risk measures, nested optimization, purged/embargoed
  validation, and multiple randomized backtests. The project should study it
  before deciding whether to add it as an optional dependency.
- [skfolio model-selection examples](https://skfolio.org/auto_examples/model_selection/index.html):
  practical examples for HRP/HERC, regularization, nested clusters, and
  randomized validation.
- [VectorBT documentation](https://vectorbt.dev/) and its
  [portfolio optimization tutorial](https://vectorbt.pro/tutorials/portfolio-optimization/):
  optional high-throughput research/backtesting comparison; the optimization
  tutorial is a useful cookbook even if the Pro page is not used.
- [Ledoit-Wolf covariance shrinkage](https://scikit-learn.org/stable/modules/covariance.html):
  practical estimation-risk reference before trusting a sample covariance
  matrix in an optimizer.

#### Business-use-case reading checklist
- Benchmark-relative construction: tracking error, active risk, information
  ratio, benchmark-relative constraints, and active share.
- Risk budgeting: asset, sector, issuer, duration, spread, and factor
  contribution budgets rather than only nominal weight limits.
- Implementation: turnover, bid/ask spread, market impact, liquidity capacity,
  rebalance windows, and infeasible-constraint handling.
- Downside and robustness: CVaR/expected shortfall, drawdown, stress regimes,
  uncertainty sets, shrinkage, and sensitivity of weights to inputs.
- PM communication: current-versus-proposed weights, binding constraints,
  expected risk/return change, implementation cost, data vintage, and an
  explicit human approval decision.

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
- `uv` docs (dependency management, this project's package manager — docs/PLAN.md §1, `INSTALL.md`): `docs.astral.sh/uv`
