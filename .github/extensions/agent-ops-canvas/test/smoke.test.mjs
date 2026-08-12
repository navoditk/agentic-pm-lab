import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const home = await mkdtemp(join(tmpdir(), "agent-ops-smoke-"));
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

  await test("GET /state has seeded runs", async () => {
    const state = await getState(open.url);
    assert.ok(Array.isArray(state.runs));
    assert.ok(state.runs.length >= 5);
    assert.equal(state.selectedRunId, "day7-full-450f21c2");
  });

  await test("get_runs filters the seeded history", async () => {
    const { body } = await post(open.url, "get_runs", { kind: "evaluation", query: "fast" });
    assert.equal(body.result.count >= 1, true);
    assert.match(body.result.runs[0].title, /Day 6|Day 7/);
  });

  await test("get_trace returns a node tree", async () => {
    const { body } = await post(open.url, "get_trace", { run_id: "day5-multi-local-qwen3" });
    assert.equal(body.result.run_id, "day5-multi-local-qwen3");
    assert.ok(body.result.node_count >= 1);
  });

  await test("get_cost_metrics returns the selected run footprint", async () => {
    const { body } = await post(open.url, "get_cost_metrics", { run_id: "day6-full-5bcd4d5c" });
    assert.equal(body.result.metrics.estimatedCostUsd, 0.0774144);
    assert.equal(body.result.metrics.latencySeconds, 363.44);
  });

  await test("get_guardrail_results returns the paused approval summary", async () => {
    const { body } = await post(open.url, "get_guardrail_results", { run_id: "day7-backtest-approval" });
    assert.equal(body.result.guardrails[0].result, "pending");
  });
} finally {
  await runtime.shutdown();
  await rm(home, { recursive: true, force: true });
}

console.log(`\n${passed} checks passed`);
