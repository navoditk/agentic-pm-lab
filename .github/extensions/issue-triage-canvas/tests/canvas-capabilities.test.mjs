import assert from "node:assert/strict";
import { createActions } from "../canvas.mjs";

const issue = {
  number: 4,
  title: "Refresh dashboard",
  html_url: "https://github.com/navoditk/agentic-pm-lab/issues/4",
  state: "open",
  labels: [{ name: "bug" }],
  assignees: [],
  comments: 1,
  updated_at: "2026-08-12T00:00:00Z",
};

async function run() {
  const calls = [];
  const requestGithub = async (path, options = {}) => {
    calls.push({ path, options });
    if (options.body?.assignees) return { ...issue, assignees: options.body.assignees.map((login) => ({ login })) };
    if (options.body?.state) return { ...issue, state: options.body.state };
    return [issue];
  };
  const actions = createActions(requestGithub);
  const state = { repository: "navoditk/agentic-pm-lab", issues: [], error: null, lastRefresh: null };
  let next = state;
  const set = (updater) => {
    next = typeof updater === "function" ? updater(next) : updater;
  };
  await actions.refresh_issues.handler({ state: next, set });
  assert.equal(next.issues[0].number, 4);

  await actions.assign_issue.handler({ state: { ...next, issues: [next.issues[0]] }, set, input: { number: 4, assignees: ["navoditk"] } });
  assert.deepEqual(next.issues[0].assignees, ["navoditk"]);

  await actions.set_issue_status.handler({ state: { ...next, issues: [next.issues[0]] }, set, input: { number: 4, state: "closed" } });
  assert.equal(next.issues[0].state, "closed");
  assert.ok(calls.length >= 3);
}

await run();
