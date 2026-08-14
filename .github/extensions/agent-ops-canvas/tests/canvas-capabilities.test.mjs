import assert from "node:assert/strict";
import { createActions } from "../canvas.mjs";

function initialState() {
  return {
    runs: [
      {
        id: "approval-run",
        title: "Paused backtest",
        kind: "approval",
        model: "gpt-4.1-mini",
        status: "waiting-for-approval",
        question: "Run backtest with approval gating.",
        summary: "Paused before the backtest tool ran.",
        metrics: { inputTokens: null, outputTokens: null, estimatedCostUsd: null, latencySeconds: null },
        comparisonNote: "Approval gate from Day 7.",
        guardrails: [{ name: "approval gate", result: "pending", detail: "Needs human approval." }],
        evaluation: { subset: "n/a", status: "paused", note: "Approve to resume." },
        approval: { state: "waiting", hook: "interrupt_on", approvedAt: null },
        trace: {
          id: "root",
          label: "run_backtest",
          status: "waiting-for-approval",
          detail: "Paused by approval interrupt.",
          retryCount: 0,
          children: [
            {
              id: "gate",
              label: "approval gate",
              status: "waiting-for-approval",
              detail: "Human approval required.",
              retryCount: 0,
              children: [],
            },
          ],
        },
      },
      {
        id: "day5-multi-local-qwen3",
        title: "Day 5 local multi-agent run",
        kind: "multi-agent",
        model: "qwen3:4b",
        status: "completed",
        question: "Reprice the rate leg in Macro and run rolling volatility in Quant.",
        summary: "Returned an empty final response in 18.825s with no task call.",
        metrics: { inputTokens: null, outputTokens: 0, estimatedCostUsd: null, latencySeconds: 18.825 },
        comparisonNote: "Local comparison.",
        guardrails: [{ name: "routing", result: "fail", detail: "No task delegation occurred." }],
        evaluation: { subset: "ad hoc", status: "failed", note: "Delegation never started." },
        trace: {
          id: "root",
          label: "Portfolio Manager",
          status: "failed",
          detail: "No task call was made before the empty final response.",
          retryCount: 0,
          children: [],
        },
      },
    ],
    selectedRunId: "approval-run",
    selectedNodeId: "root",
    latestEvaluation: null,
    evaluationError: null,
    error: null,
    lastRefresh: null,
    evidenceHealth: {
      structured: { freshness: "2026-08-12", status: "healthy", provider: "public-fixtures" },
      unstructured: { freshness: "2026-08-11", status: "degraded", provider: "mock" },
      providers: [],
      note: "Unstructured provider is degraded; no replacement narrative was generated.",
    },
    committee: {
      thesisId: "THESIS-001",
      thesis: "Test thesis",
      approvalState: "pending_human_review",
      findings: [
        { category: "contradictory_data", severity: "high", message: "Contradiction", evidenceIds: ["E1"] },
        { category: "liquidity_risk", severity: "medium", message: "Liquidity", evidenceIds: [] },
        { category: "invalidation_conditions", severity: "high", message: "No invalidation", evidenceIds: [] },
      ],
      allocationDelta: [],
    },
    fixedIncome: { curveDate: "2026-08-12", vintage: "2026-08-12", liquidityStatus: "degraded" },
    promotion: { promotable: false, checks: [{ name: "live", status: "blocked" }] },
    slo: { citationCoverage: 1, p95LatencySeconds: 1 },
    incident: { status: "ready", lastExercise: null, steps: [] },
  };
}

function invoke(actionName, input = {}, state = initialState(), extra = {}) {
  const setCalls = [];
  const actions = createActions(extra.runEvaluation ?? (async () => ({
    experiment_name: "day9-full-abc123",
    experiment_id: "exp-1",
    run_url: "https://smith.langchain.com/test",
    case_count: 18,
    dimension_scores: { routing: 1, tool_selection: 1 },
    input_tokens: 10,
    output_tokens: 2,
    estimated_cost_usd: 0.5,
    total_latency_seconds: 1.2,
  })));
  const ctx = {
    state,
    input,
    askAgent: extra.askAgent,
    set: (next) => {
      setCalls.push(next);
      state = typeof next === "function" ? next(state) : next;
    },
  };
  return Promise.resolve(actions[actionName].handler(ctx)).then((result) => ({ result, state, setCalls }));
}

async function run() {
  const trace = await invoke("get_trace", { run_id: "approval-run", node_id: "gate" });
  assert.equal(trace.result.run_id, "approval-run");
  assert.equal(trace.state.selectedNodeId, "gate");

  const retryCalls = [];
  const retried = await invoke("retry_node", { run_id: "day5-multi-local-qwen3", node_id: "root", reason: "re-run" }, initialState(), {
    askAgent: async (prompt) => retryCalls.push(prompt),
  });
  assert.equal(retried.state.runs[1].trace.retryCount, 1);
  assert.match(retryCalls[0], /Retry node root/);

  const approvals = [];
  const approved = await invoke("approve_run", { run_id: "approval-run", approved: true }, initialState(), {
    askAgent: async (prompt) => approvals.push(prompt),
  });
  assert.equal(approved.state.runs[0].status, "approved");
  assert.equal(approved.state.runs[0].approval.state, "approved");
  assert.match(approvals[0], /Resume the paused backtest run/);

  const evaluation = await invoke("run_evaluation", { subset: "full", run_id: "approval-run" }, initialState(), {
    runEvaluation: async () => ({
      experiment_name: "day9-full-abc123",
      experiment_id: "exp-1",
      run_url: "https://smith.langchain.com/test",
      case_count: 18,
      dimension_scores: { routing: 1, tool_selection: 1 },
      input_tokens: 10,
      output_tokens: 2,
      estimated_cost_usd: 0.5,
      total_latency_seconds: 1.2,
    }),
  });
  assert.equal(evaluation.state.latestEvaluation.status, "completed");
  assert.equal(evaluation.state.latestEvaluation.caseCount, 18);

  const costs = await invoke("get_cost_metrics", { run_id: "day5-multi-local-qwen3" });
  assert.equal(costs.result.metrics.latencySeconds, 18.825);

  const guardrails = await invoke("get_guardrail_results", { run_id: "approval-run" });
  assert.equal(guardrails.result.guardrails[0].result, "pending");

  const runs = await invoke("get_runs", { kind: "approval", query: "paused" });
  assert.equal(runs.result.count, 1);

  const health = await invoke("get_evidence_health", {});
  assert.equal(health.result.evidenceHealth.unstructured.status, "degraded");
  assert.match(health.result.evidenceHealth.note, /no replacement narrative/);

  const committee = await invoke("get_committee_artifact", {});
  assert.equal(committee.result.committee.approvalState, "pending_human_review");
  assert.equal(committee.result.committee.findings.length, 3);

  const fixedIncome = await invoke("get_fixed_income_panel", {});
  assert.equal(fixedIncome.result.fixedIncome.curveDate, "2026-08-12");
  assert.equal(fixedIncome.result.fixedIncome.liquidityStatus, "degraded");

  const promotion = await invoke("get_promotion_checks", {});
  assert.equal(promotion.result.promotion.promotable, false);
  assert.equal(promotion.result.promotion.checks.some((check) => check.status === "blocked"), true);

  const incident = await invoke("run_incident_exercise", { provider: "fixture-provider" });
  assert.equal(incident.result.fabricatedResearch, false);
  assert.equal(incident.state.incident.status, "degraded");

  await assert.rejects(
    invoke("replay_dead_letter", { run_id: "approval-run", node_id: "gate" }),
    /not replayable/,
  );
}

await run();
