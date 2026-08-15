import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const home = await mkdtemp(join(tmpdir(), "portfolio-risk-smoke-"));
process.env.COPILOT_HOME = home;

const { canvasConfig } = await import("../canvas.mjs");
const { createCanvasRuntime } = await import("../canvas-kit/server.mjs");
const runtime = createCanvasRuntime(canvasConfig);

let passed = 0;
async function test(label, fn) {
  try {
    await fn();
    passed++;
    console.log(`  ok  ${label}`);
  } catch (error) {
    console.error(`FAIL  ${label}\n      ${error.message}`);
    process.exitCode = 1;
    throw error;
  }
}

const post = (url, actionName, input) =>
  fetch(new URL("/action", url), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actionName, input }),
  }).then(async (response) => ({ status: response.status, body: await response.json() }));
const getState = (url) => fetch(new URL("/state", url)).then((response) => response.json());

try {
  const open = await runtime.openInstance({
    instanceId: "smoke",
    input: {},
    ctx: { instanceId: "smoke", input: {} },
  });

  await test("opens on a loopback url", () =>
    assert.match(open.url, /^http:\/\/127\.0\.0\.1:\d+\/$/));

  await test("GET /state has seeded portfolio data", async () => {
    const state = await getState(open.url);
    assert.equal(state.identity, "PM_USER");
    assert.equal(state.portfolio, "PORT_A");
    assert.ok(Array.isArray(state.holdings));
    assert.ok(state.holdings.length >= 1);
  });

  await test("PM_USER cannot switch to PORT_B", async () => {
    const result = await post(open.url, "select_portfolio", { portfolio: "PORT_B" });
    assert.equal(result.status, 500);
    assert.match(result.body.message, /cannot access PORT_B/);
  });

  await test("run_scenario applies a shock", async () => {
    const result = await post(open.url, "run_scenario", { scenarioId: "credit_75bps" });
    assert.equal(result.body.ok, true);
    const state = await getState(open.url);
    assert.equal(state.selectedScenario, "credit_75bps");
    assert.equal(state.scenarioResult.type, "credit");
  });

  await test("PM question returns a traced learning response", async () => {
    const result = await post(open.url, "ask_pm_question", { questionId: "rates_stress" });
    assert.equal(result.body.ok, true);
    assert.equal(result.body.result.status, "completed");
    assert.match(result.body.result.route, /Macro specialist/);
    const state = await getState(open.url);
    assert.equal(state.questionRun.traceId, "canvas-rates_stress");
  });

  await test("end-to-end fixture workflow returns stage and token evidence", async () => {
    const result = await post(open.url, "run_pm_workflow", { questionId: "risk_snapshot", mode: "fixture" });
    assert.equal(result.body.ok, true);
    assert.equal(result.body.result.status, "completed");
    assert.equal(result.body.result.mode, "fixture");
    assert.ok(result.body.result.execution_trace.length >= 8);
    assert.ok(result.body.result.token_usage.total_tokens > 0);
    assert.equal(result.body.result.cost.estimated_usd, 0);
    assert.equal(result.body.result.private_chain_of_thought_captured, false);
  });

  await test("provider modes fail closed without substituting fixture evidence", async () => {
    const result = await post(open.url, "run_pm_workflow", { questionId: "risk_snapshot", mode: "openai" });
    assert.equal(result.body.ok, true);
    assert.equal(result.body.result.status, "blocked");
    assert.match(result.body.result.reason, /not selected by the default/);
    assert.equal(result.body.result.token_usage.total_tokens, 0);
  });

  await test("RISK_USER can inspect PORT_B", async () => {
    await post(open.url, "set_identity", { identity: "RISK_USER" });
    const result = await post(open.url, "select_portfolio", { portfolio: "PORT_B" });
    assert.equal(result.body.ok, true);
    const state = await getState(open.url);
    assert.equal(state.identity, "RISK_USER");
    assert.equal(state.portfolio, "PORT_B");
  });

  await test("only ADMIN_USER may approve the paused run", async () => {
    const denied = await post(open.url, "approve_run", { approvalId: "run_backtest" });
    assert.equal(denied.status, 500);
    assert.match(denied.body.message, /Only ADMIN_USER/);
    await post(open.url, "set_identity", { identity: "ADMIN_USER" });
    const allowed = await post(open.url, "approve_run", { approvalId: "run_backtest" });
    assert.equal(allowed.body.ok, true);
    const state = await getState(open.url);
    assert.equal(state.approvals[0].status, "approved");
  });
} finally {
  await runtime.shutdown();
  await rm(home, { recursive: true, force: true });
}

console.log(`\n${passed} checks passed`);
