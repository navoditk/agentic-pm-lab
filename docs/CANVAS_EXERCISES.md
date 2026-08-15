# End-to-End Canvas Exercises

These exercises let a learner act as a PM, enter a representative question in
the Portfolio Risk Canvas, and inspect the response and evidence path. They are
learning-scale, deterministic fixture exercises; they do not use live holdings,
place trades, or constitute investment advice.

## Prerequisites

1. Complete [`INSTALL.md`](../INSTALL.md).
2. Read the [Canvas section in the runbook](RUNBOOK.md#canvas-and-github-copilot-app).
3. Read the [Portfolio Risk Canvas README](../.github/extensions/portfolio-risk-canvas/README.md).
4. Run the Canvas tests from the extension directory:

```bash
cd .github/extensions/portfolio-risk-canvas
node tests/canvas-capabilities.test.mjs
node test/smoke.test.mjs
```

When using the GitHub Copilot App, expose the extension according to the Canvas
README, reload extensions, and open `portfolio-risk-canvas`.

## Exercise 1 — Current risk snapshot

**Question:** “What are the largest current portfolio risks?”

Steps:

1. Open the Portfolio Risk Canvas as `PM_USER` on `PORT_A`.
2. Select the question in **PM question exercise**.
3. Choose **Run question**.
4. Read the answer, finding, route, evidence status, and trace identifier.
5. Open the trace and provenance panels.

Expected learning:

- The question routes to the Quant/Risk specialist.
- Concentration, volatility, and drawdown come from deterministic metrics.
- Holdings are mock while public price inputs are separately identified.
- The Canvas displays the workflow result but is not the authorization source.

## Exercise 2 — Rates stress

**Question:** “What happens if rates rise by 50 bps?”

Steps:

1. Select the rates-stress question.
2. Run it from the Canvas.
3. Compare the baseline and stressed volatility and drawdown.
4. Switch to **Scenarios** and inspect the same `rates_50bps` result.
5. Read the provenance panel and identify the public-versus-mock boundary.

Expected learning:

- The route is Macro specialist → scenario tool → risk summary.
- The result is a first-order learning fixture, not a full bond revaluation.
- The answer preserves the scenario assumption and trace identifier.
- A stress result is decision support, not an approved allocation or hedge.

## Exercise 3 — Entitlement denial

**Question:** “Can I inspect PORT_B from this session?”

Steps:

1. Keep the identity as `PM_USER`.
2. Run the portfolio-access question.
3. Confirm that the answer says the request is denied before tool access.
4. Try switching to `PORT_B`; observe the governed action failure.
5. Change identity to `RISK_USER` and repeat the question.

Expected learning:

- PM_USER is denied access to PORT_B by the local entitlement fixture.
- RISK_USER can inspect PORT_B in this learning setup.
- Changing Canvas state is not equivalent to changing authorization policy.
- The same action handler is used by the Canvas UI and agent-facing action path.

## Exercise 4 — Approval and operations follow-up

This exercise connects the Portfolio Risk Canvas with the Agent Operations
Canvas.

1. In Portfolio Risk, inspect the pending backtest approval.
2. Attempt approval as `PM_USER` and record the denial.
3. Switch to `ADMIN_USER` and approve the paused learning run.
4. Open Agent Operations and inspect the seeded run history.
5. Focus a trace node, inspect guardrail and cost metrics, and run the incident
   exercise for the mock research provider.

Expected learning:

- Approval is a separate control decision, not generated prose.
- Agent Operations exposes trace, guardrail, cost, evaluation, provider-health,
  replay, and promotion concepts.
- A degraded provider remains visibly degraded; the Canvas does not fabricate
  replacement research.

## What is real versus fixture-backed?

| Exercise component | Status |
|---|---|
| Canvas state, action schemas, persistence, and SSE updates | Local implementation and tests |
| Identity and portfolio entitlement | Local learning fixtures with boundary tests |
| Risk metrics and scenario response | Deterministic local fixture workflow |
| Public curve/price provenance | Public-data-capable repository path |
| Security master and holdings | Mock data |
| LLM-generated free-form answer | Not used by the bounded exercise action |
| Trade execution | Intentionally unavailable |

For a model-backed or AWS-backed comparison, use the provider-neutral experiment
framework in [`experiments/README.md`](../experiments/README.md), record the
model, tokens, cost, latency, evidence, and limitations, and keep the Canvas
exercise as the deterministic baseline.
