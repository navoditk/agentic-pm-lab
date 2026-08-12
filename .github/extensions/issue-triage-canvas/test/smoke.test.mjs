import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

const home = await mkdtemp(join(tmpdir(), "issue-triage-smoke-"));
process.env.COPILOT_HOME = home;

const { canvasConfig, createActions } = await import("../canvas.mjs");
const { createCanvasRuntime } = await import("../canvas-kit/server.mjs");

const sampleIssue = {
  number: 7,
  title: "Portfolio refresh fails",
  html_url: "https://github.com/navoditk/agentic-pm-lab/issues/7",
  state: "open",
  labels: [{ name: "bug" }, { name: "priority: high" }],
  assignees: [],
  comments: 3,
  updated_at: "2026-08-12T12:00:00Z",
};
const calls = [];
const requestGithub = async (path, options = {}) => {
  calls.push({ path, options });
  if (options.body?.assignees) {
    return { ...sampleIssue, assignees: options.body.assignees.map((login) => ({ login })) };
  }
  if (options.body?.state) return { ...sampleIssue, state: options.body.state };
  return [sampleIssue, { ...sampleIssue, number: 8, pull_request: {} }];
};

const runtime = createCanvasRuntime({ ...canvasConfig, actions: createActions(requestGithub) });
const post = (url, actionName, input = {}) =>
  fetch(new URL("/action", url), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ actionName, input }),
  }).then(async (response) => ({ status: response.status, body: await response.json() }));
const getState = (url) => fetch(new URL("/state", url)).then((response) => response.json());

let passed = 0;
async function test(label, fn) {
  await fn();
  passed += 1;
  console.log(`  ok  ${label}`);
}

try {
  const open = await runtime.openInstance({
    instanceId: "smoke",
    input: {},
    ctx: { instanceId: "smoke", input: {} },
  });
  await test("opens on a loopback url", () => assert.match(open.url, /^http:\/\/127\.0\.0\.1:\d+\/$/));

  await test("refresh loads issues and excludes pull requests", async () => {
    const result = await post(open.url, "refresh_issues");
    assert.equal(result.body.result.count, 1);
    const state = await getState(open.url);
    assert.equal(state.issues[0].number, 7);
    assert.equal(state.issues[0].priority, "high");
  });

  await test("assign_issue uses the GitHub mutation and shared handler", async () => {
    await post(open.url, "assign_issue", { number: 7, assignees: ["navoditk"] });
    const state = await getState(open.url);
    assert.deepEqual(state.issues[0].assignees, ["navoditk"]);
    assert.equal(calls.at(-1).options.authRequired, true);
  });

  await test("set_issue_status closes a loaded issue", async () => {
    await post(open.url, "set_issue_status", { number: 7, state: "closed" });
    const state = await getState(open.url);
    assert.equal(state.issues[0].state, "closed");
  });

  await test("invalid status is rejected at the schema boundary", async () => {
    const result = await post(open.url, "set_issue_status", { number: 7, state: "archived" });
    assert.equal(result.status, 400);
    assert.equal(result.body.code, "invalid_input");
  });

  await test("a missing issue fails before a GitHub mutation", async () => {
    const callCount = calls.length;
    const result = await post(open.url, "assign_issue", { number: 999, assignees: [] });
    assert.equal(result.status, 500);
    assert.match(result.body.message, /not loaded/);
    assert.equal(calls.length, callCount);
  });
} finally {
  await runtime.shutdown();
  await rm(home, { recursive: true, force: true });
}

console.log(`\n${passed} checks passed`);
