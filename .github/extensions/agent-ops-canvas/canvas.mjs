import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { userStore } from "./canvas-kit/storage.mjs";
import { nid } from "./canvas-kit/format.mjs";

const execFileAsync = promisify(execFile);
const EXT_NAME = "agent-ops-canvas";
const REPO_ROOT = fileURLToPath(new URL("../../..", import.meta.url));
const DEFAULT_RUN_ID = "day7-full-450f21c2";

function fileFor(domainId) {
  const safe = String(domainId).replace(/[^A-Za-z0-9._-]/g, "_") || "default";
  return userStore(EXT_NAME, `${safe}.json`);
}

function metric(inputTokens, outputTokens, estimatedCostUsd, latencySeconds) {
  return { inputTokens, outputTokens, estimatedCostUsd, latencySeconds };
}

function node(id, label, status, detail, extras = {}) {
  return { id, label, status, detail, retryCount: 0, children: [], ...extras };
}

function seedRuns() {
  return [
    {
      id: "day4-single-local-volatility",
      title: "Day 4 single-agent volatility question",
      kind: "single-agent",
      model: "qwen3:4b",
      status: "completed",
      question: "What's my portfolio volatility?",
      summary: "Local 4B model called get_volatility with the supplied returns, window=2, and periods_per_year=252.",
      metrics: metric(7359, 0, null, 129.696),
      comparisonNote: "Single-agent local comparison from docs/comparison-notes.md.",
      guardrails: [
        { name: "context filtering", result: "pass", detail: "Used a filtered source bundle instead of the overloaded full context." },
        { name: "tool selection", result: "pass", detail: "Called get_volatility with the expected shape." },
      ],
      evaluation: {
        subset: "single-agent",
        status: "ad hoc",
        note: "Cloud run was blocked by insufficient quota when this comparison was first recorded.",
      },
      trace: node("root", "single_agent.invoke", "completed", "Built context, called get_volatility, and composed the answer.", {
        children: [
          node("context", "context builder", "completed", "Filtered named sources: user/role, portfolio, market, tool outputs, skills."),
          node("tool", "get_volatility", "completed", "Handled 500 returns with the expected window and annualization."),
          node("answer", "final answer", "completed", "Reported the four returned tool values without inventing data."),
        ],
      }),
    },
    {
      id: "day5-multi-cloud-gpt41-mini",
      title: "Day 5 cloud multi-agent run",
      kind: "multi-agent",
      model: "gpt-4.1-mini",
      status: "completed",
      question: "Reprice the rate leg in Macro and run rolling volatility in Quant.",
      summary: "Called both native sub-agents and synthesized their results, but omitted periods_per_year=12 from the Quant task.",
      metrics: metric(null, null, null, null),
      comparisonNote: "Cloud multi-agent comparison from docs/comparison-notes.md.",
      guardrails: [
        { name: "routing", result: "pass", detail: "Delegated to Macro and Quant." },
        { name: "parameter preservation", result: "warn", detail: "Dropped periods_per_year=12 in the Quant task." },
      ],
      evaluation: {
        subset: "ad hoc",
        status: "completed",
        note: "Routing passed, parameter preservation did not.",
      },
      trace: node("root", "Portfolio Manager", "completed", "Delegated to specialist sub-agents and synthesized their answers.", {
        children: [
          node("macro", "Macro specialist", "completed", "Handled the rate leg repricing."),
          node("quant", "Quant specialist", "completed", "Handled rolling volatility, but used the default annualization."),
          node("fundamental", "Fundamental specialist", "completed", "No direct task in this question."),
        ],
      }),
    },
    {
      id: "day5-multi-local-qwen3",
      title: "Day 5 local multi-agent run",
      kind: "multi-agent",
      model: "qwen3:4b",
      status: "completed",
      question: "Reprice the rate leg in Macro and run rolling volatility in Quant.",
      summary: "Returned an empty final response in 18.825s with no task call.",
      metrics: metric(null, 0, null, 18.825),
      comparisonNote: "Local multi-agent comparison from docs/comparison-notes.md.",
      guardrails: [
        { name: "routing", result: "fail", detail: "No task delegation occurred." },
      ],
      evaluation: {
        subset: "ad hoc",
        status: "failed",
        note: "The 4B model failed at orchestrator-level delegation even with explicit specialist names.",
      },
      trace: node("root", "Portfolio Manager", "failed", "No task call was made before the empty final response.", {
        children: [
          node("attempt", "delegation attempt", "failed", "No sub-agent was invoked."),
        ],
      }),
    },
    {
      id: "day6-fast-18ee584c",
      title: "Day 6 fast evaluation",
      kind: "evaluation",
      model: "gpt-4.1-mini",
      status: "completed",
      question: "Fast subset evaluation baseline.",
      summary: "Accepted fast OTel/LangSmith evaluation baseline.",
      metrics: metric(49007, 2703, 0.0239276, 78.37),
      comparisonNote: "Fast baseline from docs/observability-evaluation.md.",
      guardrails: [
        { name: "policy compliance", result: "unscored", detail: "Policy and guardrail dimensions were still stubbed at this point." },
      ],
      evaluation: {
        subset: "fast",
        status: "accepted",
        note: "5 cases; policy and guardrails intentionally unscored.",
      },
      trace: node("root", "evaluation.case", "completed", "LangSmith experiment case with OTel-captured prompts and completions.", {
        children: [
          node("span", "evaluation.case span", "completed", "Recorded langsmith.trace.session_id and reference_example_id."),
        ],
      }),
    },
    {
      id: "day6-full-5bcd4d5c",
      title: "Day 6 full evaluation",
      kind: "evaluation",
      model: "gpt-4.1-mini",
      status: "completed",
      question: "Full baseline evaluation.",
      summary: "Accepted full OTel/LangSmith evaluation baseline.",
      metrics: metric(159416, 8530, 0.0774144, 363.44),
      comparisonNote: "Full baseline from docs/observability-evaluation.md.",
      guardrails: [
        { name: "policy compliance", result: "unscored", detail: "Policy and guardrail dimensions were still stubbed at this point." },
      ],
      evaluation: {
        subset: "full",
        status: "accepted",
        note: "15 cases; policy and guardrails intentionally unscored.",
      },
      trace: node("root", "evaluation.case", "completed", "LangSmith experiment root linked to the dataset example.", {
        children: [
          node("span", "agent.portfolio_manager.invoke", "completed", "Captured prompt/completion and cost/latency span attributes."),
        ],
      }),
    },
    {
      id: "day7-fast-94e7cd22",
      title: "Day 7 fast policy probe",
      kind: "evaluation",
      model: "gpt-4.1-mini",
      status: "completed",
      question: "Fast subset with deterministic policy checks.",
      summary: "Fast policy floor retained; observed routing/tool variability was lower than the floor.",
      metrics: metric(53885, 3336, 0.0268916, 70.38909895997494),
      comparisonNote: "Fast policy extension from config/eval-baseline.json.",
      guardrails: [
        { name: "policy compliance", result: "pass", detail: "Identity/tool/portfolio checks all passed deterministically." },
      ],
      evaluation: {
        subset: "fast",
        status: "accepted",
        note: "7 cases; deterministic policy compliance added without lowering behavioral floors.",
      },
      trace: node("root", "evaluation.case", "completed", "OTel-routed LangSmith evaluation with deterministic policy probes.", {
        children: [
          node("span", "policy probe", "completed", "No model tokens spent on policy cases."),
        ],
      }),
    },
    {
      id: "day7-full-450f21c2",
      title: "Day 7 full policy experiment",
      kind: "evaluation",
      model: "gpt-4.1-mini",
      status: "completed",
      question: "Full subset with policy compliance activated.",
      summary: "18-case full experiment scored policy compliance at 100%.",
      metrics: metric(158817, 10123, 0.0797236, 204.60224625072442),
      comparisonNote: "Full policy baseline from config/eval-baseline.json.",
      guardrails: [
        { name: "policy compliance", result: "pass", detail: "Deterministic Cedar decisions were all correct." },
      ],
      evaluation: {
        subset: "full",
        status: "accepted",
        note: "18 cases; 100% policy compliance, 86.7% tool selection, 93.3% tool arguments.",
      },
      trace: node("root", "evaluation.case", "completed", "LangSmith experiment root with preserved native OTel parentage.", {
        children: [
          node("span", "agent.portfolio_manager.invoke", "completed", "Captured the cost/token/latency attributes."),
        ],
      }),
    },
    {
      id: "day7-backtest-approval",
      title: "Day 7 backtest approval gate",
      kind: "approval",
      model: "gpt-4.1-mini",
      status: "waiting-for-approval",
      question: "Run backtest with interrupt_on approval gating.",
      summary: "Paused before the backtest tool ran.",
      metrics: metric(null, null, null, null),
      comparisonNote: "Approval gate from Day 7 interrupt_on exercise.",
      guardrails: [
        { name: "approval gate", result: "pending", detail: "The run is intentionally paused until a human approves it." },
      ],
      evaluation: {
        subset: "n/a",
        status: "paused",
        note: "Approving this run should resume the paused agent flow.",
      },
      approval: { state: "waiting", hook: "interrupt_on", approvedAt: null },
      trace: node("root", "run_backtest", "waiting-for-approval", "Paused by the approval interrupt before the tool ran.", {
        children: [
          node("gate", "approval gate", "waiting-for-approval", "Human approval required before resuming the backtest."),
        ],
      }),
    },
  ];
}

function findRun(runs, runId) {
  return runs.find((run) => run.id === runId) ?? null;
}

function updateRun(runs, runId, updater) {
  let found = false;
  const updated = runs.map((run) => {
    if (run.id !== runId) return run;
    found = true;
    return updater(run);
  });
  if (!found) throw new Error(`Unknown run ${runId}`);
  return updated;
}

function updateNodeTree(node_, nodeId, updater) {
  if (node_.id === nodeId) return updater(node_);
  const children = node_.children.map((child) => updateNodeTree(child, nodeId, updater));
  return children.some((child, index) => child !== node_.children[index])
    ? { ...node_, children }
    : node_;
}

function walkNodes(node_, nodes = []) {
  nodes.push(node_);
  node_.children.forEach((child) => walkNodes(child, nodes));
  return nodes;
}

function summarizeRuns(runs) {
  return runs.map((run) => ({
    id: run.id,
    title: run.title,
    kind: run.kind,
    model: run.model,
    status: run.status,
    summary: run.summary,
    metrics: run.metrics,
    question: run.question,
  }));
}

async function runRealEvaluation(subset) {
  if (!process.env.LANGSMITH_API_KEY) {
    throw new Error("LANGSMITH_API_KEY is required to run a real LangSmith experiment");
  }
  const { stdout } = await execFileAsync(
    "uv",
    ["run", "python", "scripts/run_eval.py", "--subset", subset],
    { cwd: REPO_ROOT, maxBuffer: 2_000_000, env: process.env },
  );
  return JSON.parse(stdout);
}

function createState() {
  return {
    runs: seedRuns(),
    selectedRunId: DEFAULT_RUN_ID,
    selectedNodeId: "root",
    latestEvaluation: null,
    evaluationError: null,
    error: null,
    lastRefresh: null,
    evidenceHealth: {
      structured: { freshness: "2026-08-12", status: "healthy", provider: "public-fixtures" },
      unstructured: { freshness: "2026-08-11", status: "degraded", provider: "mock-bigdata-thematic-screen" },
      providers: [
        { name: "SEC EDGAR", availability: "fixture", licensing: "public", citationCoverage: 1, needsReview: 0 },
        { name: "Treasury/FRED", availability: "available", licensing: "public", citationCoverage: 1, needsReview: 0 },
        { name: "Thematic provider", availability: "degraded", licensing: "fixture-only", citationCoverage: 1, needsReview: 1 },
      ],
      lastChecked: "2026-08-13T08:00:00Z",
      note: "Unstructured provider is degraded; no replacement narrative was generated.",
    },
    committee: {
      thesisId: "THESIS-001",
      thesis: "Issuer A can absorb higher funding costs.",
      rebuttalStatus: "challenged",
      findings: [
        { category: "contradictory_data", severity: "high", message: "Linked evidence contradicts the claim.", evidenceIds: ["E1"] },
        { category: "liquidity_risk", severity: "medium", message: "Liquidity status is illiquid.", evidenceIds: [] },
        { category: "invalidation_conditions", severity: "high", message: "No condition would invalidate the thesis.", evidenceIds: [] },
      ],
      allocationDelta: [
        { securityId: "ISSUER-A", currentWeight: 0.4, proposedWeight: 0.25, delta: -0.15 },
      ],
      approvalState: "pending_human_review",
      reviewer: null,
    },
    fixedIncome: {
      curveDate: "2026-08-12",
      vintage: "2026-08-12",
      keyRateDv01: "needs_review",
      spreadDuration: "needs_review",
      carryRolldown: "not available",
      liquidityStatus: "degraded",
      issuerRatingConcentration: "mock security master",
      sourceCoverage: "3/6 topics fixture-backed",
      hedgeAssumptions: "Human review required; no hedge order generated.",
      fallback: "direct-provider fallback not configured",
    },
    promotion: {
      environment: "local",
      checks: [
        { name: "unit tests", status: "pass", detail: "Deterministic suite is green." },
        { name: "governance negatives", status: "pass", detail: "Authorization and guardrail negatives are green." },
        { name: "provider health", status: "warn", detail: "Unstructured provider is degraded." },
        { name: "live AgentCore smoke", status: "blocked", detail: "No live AWS evidence is claimed." },
      ],
      promotable: false,
    },
    slo: { traceCoverage: 1, citationCoverage: 1, p95LatencySeconds: 363.44, providerAvailability: 0.67 },
    incident: { status: "ready", lastExercise: null, steps: [] },
  };
}

export function createActions(runEvaluation = runRealEvaluation) {
  return {
    get_runs: {
      description: "Return the seeded run history and optionally focus one run.",
      inputSchema: {
        type: "object",
        properties: {
          run_id: { type: "string" },
          kind: { type: "string", enum: ["all", "single-agent", "multi-agent", "evaluation", "approval"] },
          query: { type: "string" },
        },
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        const query = String(input.query ?? "").trim().toLowerCase();
        const kind = input.kind ?? "all";
        const runs = state.runs.filter((run) =>
          (kind === "all" || run.kind === kind)
          && (!query || `${run.title} ${run.summary} ${run.question}`.toLowerCase().includes(query)));
        const selectedRunId = input.run_id && findRun(state.runs, input.run_id)
          ? input.run_id
          : state.selectedRunId;
        set((current) => ({
          ...current,
          selectedRunId,
          error: null,
          lastRefresh: new Date().toISOString(),
        }));
        return { count: runs.length, runs: summarizeRuns(runs) };
      },
    },

    get_trace: {
      description: "Return the trace tree for one run and focus it in the canvas.",
      inputSchema: {
        type: "object",
        properties: {
          run_id: { type: "string" },
          node_id: { type: "string" },
        },
        required: ["run_id"],
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        const run = findRun(state.runs, input.run_id);
        if (!run) throw new Error(`Unknown run ${input.run_id}`);
        const nodes = walkNodes(run.trace, []);
        const nodeId = input.node_id && nodes.some((node_) => node_.id === input.node_id)
          ? input.node_id
          : run.trace.id;
        set((current) => ({
          ...current,
          selectedRunId: run.id,
          selectedNodeId: nodeId,
          error: null,
        }));
        return { run_id: run.id, trace: run.trace, node_count: nodes.length };
      },
    },

    retry_node: {
      description: "Mark a node as retried and ask the main agent to rerun it.",
      inputSchema: {
        type: "object",
        properties: {
          run_id: { type: "string" },
          node_id: { type: "string" },
          reason: { type: "string" },
        },
        required: ["run_id", "node_id"],
        additionalProperties: false,
      },
      handler: async ({ state, set, input, askAgent }) => {
        const run = findRun(state.runs, input.run_id);
        if (!run) throw new Error(`Unknown run ${input.run_id}`);
        let found = false;
        const runs = updateRun(state.runs, run.id, (current) => ({
          ...current,
          trace: updateNodeTree(current.trace, input.node_id, (node_) => {
            found = true;
            return {
              ...node_,
              retryCount: (node_.retryCount ?? 0) + 1,
              status: "retried",
              detail: `${node_.detail} (retry requested)`,
            };
          }),
        }));
        if (!found) throw new Error(`Unknown node ${input.node_id} in ${input.run_id}`);
        if (typeof askAgent === "function") {
          await askAgent(
            `Retry node ${input.node_id} in run "${run.title}".` +
            (input.reason ? ` Reason: ${input.reason}` : ""),
          );
        }
        set((current) => ({
          ...current,
          runs,
          selectedRunId: run.id,
          selectedNodeId: input.node_id,
          error: null,
        }));
        return { run_id: run.id, node_id: input.node_id, retries: 1 };
      },
    },

    approve_run: {
      description: "Approve a paused run and ask the main agent to resume it.",
      inputSchema: {
        type: "object",
        properties: {
          run_id: { type: "string" },
          approved: { type: "boolean" },
        },
        required: ["run_id"],
        additionalProperties: false,
      },
      handler: async ({ state, set, input, askAgent }) => {
        const run = findRun(state.runs, input.run_id);
        if (!run) throw new Error(`Unknown run ${input.run_id}`);
        if (run.kind !== "approval") throw new Error(`Run ${run.id} is not paused for approval`);
        const approved = input.approved !== false;
        const now = new Date().toISOString();
        const runs = updateRun(state.runs, run.id, (current) => ({
          ...current,
          status: approved ? "approved" : "rejected",
          approval: { ...(current.approval ?? {}), state: approved ? "approved" : "rejected", approvedAt: now },
          trace: updateNodeTree(current.trace, "run_backtest", (node_) => ({
            ...node_,
            status: approved ? "resumed" : "rejected",
            detail: approved ? "Human approved the paused backtest; agent may resume." : "Human rejected the paused backtest.",
          })),
        }));
        if (approved && typeof askAgent === "function") {
          await askAgent(
            `Resume the paused backtest run "${run.title}" now that it has been approved.`,
          );
        }
        set((current) => ({
          ...current,
          runs,
          selectedRunId: run.id,
          error: null,
        }));
        return { run_id: run.id, approved, status: approved ? "resumed" : "rejected" };
      },
    },

    run_evaluation: {
      description: "Run the real LangSmith experiment for the current agent configuration.",
      inputSchema: {
        type: "object",
        properties: {
          subset: { type: "string", enum: ["fast", "full"] },
          run_id: { type: "string" },
        },
        required: ["subset"],
        additionalProperties: false,
      },
      handler: async ({ state, set, input }) => {
        const subset = input.subset;
        set((current) => ({ ...current, evaluationError: null, latestEvaluation: { status: "running", subset } }));
        try {
          const summary = await runEvaluation(subset);
          const wrapped = {
            status: "completed",
            subset,
            runId: input.run_id ?? state.selectedRunId,
            experimentName: summary.experiment_name,
            experimentId: summary.experiment_id,
            runUrl: summary.run_url,
            caseCount: summary.case_count,
            dimensionScores: summary.dimension_scores,
            inputTokens: summary.input_tokens,
            outputTokens: summary.output_tokens,
            estimatedCostUsd: summary.estimated_cost_usd,
            totalLatencySeconds: summary.total_latency_seconds,
          };
          set((current) => ({
            ...current,
            latestEvaluation: wrapped,
            evaluationError: null,
            error: null,
          }));
          return wrapped;
        } catch (error) {
          const evaluationError = String(error?.message ?? error);
          set((current) => ({ ...current, latestEvaluation: { status: "failed", subset }, evaluationError }));
          return { ok: false, error: evaluationError };
        }
      },
    },

    get_guardrail_results: {
      description: "Return the guardrail summary for one run.",
      inputSchema: {
        type: "object",
        properties: { run_id: { type: "string" } },
        required: ["run_id"],
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        const run = findRun(state.runs, input.run_id);
        if (!run) throw new Error(`Unknown run ${input.run_id}`);
        set((current) => ({ ...current, selectedRunId: run.id, error: null }));
        return { run_id: run.id, guardrails: run.guardrails, summary: run.guardrails.map((g) => g.result).join(", ") };
      },
    },

    get_cost_metrics: {
      description: "Return the cost and latency footprint for one run.",
      inputSchema: {
        type: "object",
        properties: { run_id: { type: "string" } },
        required: ["run_id"],
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        const run = findRun(state.runs, input.run_id);
        if (!run) throw new Error(`Unknown run ${input.run_id}`);
        set((current) => ({ ...current, selectedRunId: run.id, error: null }));
        return { run_id: run.id, metrics: run.metrics };
      },
    },

    get_evidence_health: {
      description: "Return structured and unstructured evidence-provider health without fabricating degraded data.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler: ({ state }) => ({ evidenceHealth: state.evidenceHealth }),
    },

    get_committee_artifact: {
      description: "Return the thesis, rebuttal findings, allocation delta, and human approval state.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler: ({ state }) => ({ committee: state.committee }),
    },

    get_fixed_income_panel: {
      description: "Return fixed-income provenance, risk, liquidity, source coverage, and hedge assumptions.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler: ({ state }) => ({ fixedIncome: state.fixedIncome }),
    },

    get_promotion_checks: {
      description: "Return deployment promotion checks and refuse promotion when a check is blocked or warned.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler: ({ state }) => ({ promotion: state.promotion, slo: state.slo }),
    },

    replay_dead_letter: {
      description: "Replay one failed or dead-lettered trace node and record the request for the main agent.",
      inputSchema: {
        type: "object",
        properties: { run_id: { type: "string" }, node_id: { type: "string" }, reason: { type: "string" } },
        required: ["run_id", "node_id"],
        additionalProperties: false,
      },
      handler: async ({ state, set, input, askAgent }) => {
        const run = findRun(state.runs, input.run_id);
        if (!run) throw new Error(`Unknown run ${input.run_id}`);
        const nodes = walkNodes(run.trace, []);
        const target = nodes.find((node_) => node_.id === input.node_id);
        if (!target) throw new Error(`Unknown node ${input.node_id} in ${input.run_id}`);
        if (!['failed', 'dead_letter', 'retried'].includes(target.status)) {
          throw new Error(`Node ${input.node_id} is not replayable`);
        }
        if (typeof askAgent === "function") {
          await askAgent(`Replay dead-letter node ${input.node_id} in run "${run.title}".` + (input.reason ? ` Reason: ${input.reason}` : ""));
        }
        set((current) => ({ ...current, incident: { ...current.incident, status: "replay-requested", lastExercise: new Date().toISOString() }, error: null }));
        return { run_id: run.id, node_id: input.node_id, status: "replay-requested" };
      },
    },

    run_incident_exercise: {
      description: "Exercise provider outage handling and make degraded state visible.",
      inputSchema: { type: "object", properties: { provider: { type: "string" } }, required: ["provider"], additionalProperties: false },
      handler: ({ state, set, input }) => {
        const provider = String(input.provider).trim();
        if (!provider) throw new Error("provider must not be empty");
        const steps = [
          `Detected outage for ${provider}`,
          "Marked unstructured evidence degraded",
          "Suppressed fabricated replacement research",
          "Queued human/provider recovery review",
        ];
        set((current) => ({ ...current, incident: { status: "degraded", lastExercise: new Date().toISOString(), steps }, evidenceHealth: { ...current.evidenceHealth, unstructured: { ...current.evidenceHealth.unstructured, status: "degraded", provider }, note: "Incident exercise active; no fabricated research returned." } }));
        return { provider, status: "degraded", fabricatedResearch: false, steps };
      },
    },
  };
}

export const canvasConfig = {
  id: "agent-ops-canvas",
  displayName: "Agent Operations",
  description: "Inspect agent runs, research evidence health, committee rebuttals, fixed-income panels, approvals, SLOs, and replay controls.",
  assetsDir: fileURLToPath(new URL("./web/", import.meta.url)),
  inputSchema: {
    type: "object",
    properties: {
      domain: {
        type: "string",
        description: "Logical board to open. Omit for the default workspace.",
      },
    },
    additionalProperties: false,
  },
  resolveDomainId: (input) => (input?.domain ? String(input.domain) : "default"),
  createInitialState: createState,
  loadState: async (domainId) => fileFor(domainId).load(null),
  saveState: async (domainId, state) => fileFor(domainId).save(state),
  statusLine: (_ctx, state) => {
    const selected = findRun(state.runs, state.selectedRunId);
    return selected ? `${selected.title} · ${selected.status}` : `${state.runs.length} runs`;
  },
  actions: createActions(),
};
