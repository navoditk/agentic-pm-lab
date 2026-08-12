import assert from "node:assert/strict";
import { canvasConfig } from "../canvas.mjs";

function call(actionName, input = {}, state = { cards: [] }) {
  const setCalls = [];
  const def = canvasConfig.actions[actionName];
  const ctx = {
    state,
    input,
    set: (next) => {
      setCalls.push(next);
      state = typeof next === "function" ? next(state) : next;
    },
  };
  return Promise.resolve(def.handler(ctx)).then((result) => ({ result, setCalls, state }));
}

async function run() {
  const added = await call("add_card", { title: "Ship docs", assignee: "PM_USER" });
  assert.equal(added.result.column, "backlog");
  assert.equal(added.state.cards[0].title, "Ship docs");

  const id = added.state.cards[0].id;
  const moved = await call("move_card", { id, column: "review" }, added.state);
  assert.equal(moved.state.cards[0].column, "review");

  const assigned = await call("assign_card", { id, assignee: "RISK_USER" }, moved.state);
  assert.equal(assigned.state.cards[0].assignee, "RISK_USER");

  try {
    await call("add_card", { title: "   " });
    assert.fail("blank title should throw");
  } catch (error) {
    assert.match(String(error.message), /required/);
  }
  try {
    await call("move_card", { id: "missing", column: "review" });
    assert.fail("missing card should throw");
  } catch (error) {
    assert.match(String(error.message), /No card/);
  }
}

await run();
