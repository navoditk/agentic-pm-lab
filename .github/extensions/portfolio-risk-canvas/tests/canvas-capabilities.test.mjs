import assert from "node:assert/strict";
import { canvasConfig } from "../canvas.mjs";

function invoke(actionName, input = {}, state) {
  const actions = canvasConfig.actions;
  const current = state ?? canvasConfig.createInitialState();
  const calls = [];
  const ctx = {
    state: current,
    input,
    set: (next) => {
      calls.push(next);
      state = typeof next === "function" ? next(state ?? current) : next;
    },
  };
  return Promise.resolve(actions[actionName].handler(ctx)).then((result) => ({
    result,
    state: state ?? current,
    calls,
  }));
}

async function run() {
  const initial = canvasConfig.createInitialState();
  const question = await invoke("ask_pm_question", { questionId: "risk_snapshot" }, initial);
  assert.equal(question.result.status, "completed");
  assert.match(question.state.questionRun.answer, /Largest concentration/);

  const stress = await invoke("ask_pm_question", { questionId: "rates_stress" }, question.state);
  assert.match(stress.state.questionRun.answer, /\+50 bps fixture/);

  const scenario = await invoke("run_scenario", { scenarioId: "rates_50bps" }, initial);
  assert.equal(scenario.result.scenarioId, "rates_50bps");
  assert.equal(scenario.state.scenarioResult.type, "macro");

  const denied = await (async () => {
    try {
      await invoke("select_portfolio", { portfolio: "PORT_B" }, initial);
      return null;
    } catch (error) {
      return error;
    }
  })();
  assert.ok(denied);
  assert.match(String(denied.message), /cannot access PORT_B/);

  const risk = await invoke("set_identity", { identity: "RISK_USER" }, initial);
  const switched = await invoke("select_portfolio", { portfolio: "PORT_B" }, risk.state);
  assert.equal(switched.state.portfolio, "PORT_B");

  const blockedApproval = await (async () => {
    try {
      await invoke("approve_run", { approvalId: "run_backtest" }, risk.state);
      return null;
    } catch (error) {
      return error;
    }
  })();
  assert.ok(blockedApproval);
  assert.match(String(blockedApproval.message), /Only ADMIN_USER/);

  const admin = await invoke("set_identity", { identity: "ADMIN_USER" }, switched.state);
  const approved = await invoke("approve_run", { approvalId: "run_backtest" }, admin.state);
  assert.equal(approved.state.approvals[0].status, "approved");

  const trace = await invoke("inspect_trace", { nodeId: "macro" }, approved.state);
  assert.equal(trace.state.selectedTraceNode, "macro");
  assert.equal(trace.state.trace.children[0].status, "focused");
}

await run();
