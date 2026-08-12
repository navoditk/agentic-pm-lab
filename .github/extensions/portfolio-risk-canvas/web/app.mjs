import { html, mountCanvas, useMemo, useState, Icon, percent, compactNumber, relativeTime } from "/kit/client.mjs";

const TITLE = "Portfolio Risk";

const VIEWS = [
  { id: "overview", label: "Overview", icon: "layout-dashboard" },
  { id: "scenarios", label: "Scenarios", icon: "siren" },
  { id: "traces", label: "Traces", icon: "git-branch" },
  { id: "provenance", label: "Provenance", icon: "badge-info" },
  { id: "approvals", label: "Approvals", icon: "circle-check" },
  { id: "evaluation", label: "Evaluation", icon: "flask-conical" },
];

const SCENARIOS = {
  rates_50bps: {
    id: "rates_50bps",
    label: "Rates +50 bps",
    type: "macro",
    impact: { volatility: 0.018, drawdown: -0.024, return: -0.006 },
    note: "Duration-sensitive positions soften; hedge cost rises.",
  },
  credit_75bps: {
    id: "credit_75bps",
    label: "Credit +75 bps",
    type: "credit",
    impact: { volatility: 0.026, drawdown: -0.039, return: -0.012 },
    note: "Credit spread risk dominates the stress outcome.",
  },
  convexity_rally: {
    id: "convexity_rally",
    label: "Mortgage rally",
    type: "mortgage",
    impact: { volatility: 0.014, drawdown: -0.019, return: -0.004 },
    note: "Negative convexity creates asymmetric downside in a rally.",
  },
};

function MetricCard({ title, value, caption }) {
  return html`
    <div class="ck-card metric-card">
      <div class="ck-caption">${title}</div>
      <div style="font-size:1.2rem;font-weight:var(--ck-fw-semibold)">${value}</div>
      <div class="ck-muted">${caption}</div>
    </div>
  `;
}

function TraceNode({ node, selectedNodeId, onPick }) {
  return html`
    <div class=${`trace-node ${node.id === selectedNodeId ? "trace-node-active" : ""}`}>
      <div class="ck-spread">
        <button class="ck-btn ck-btn-sm" onClick=${() => onPick(node.id)}>
          <${Icon} name=${node.status === "completed" ? "circle-check" : "circle-dot"} size=${14} />
          ${node.label}
        </button>
        <span class="ck-caption">${node.status}</span>
      </div>
      <div class="ck-muted" style="margin-top:6px">${node.detail}</div>
      ${node.children?.length
        ? html`<div class="trace-children">
            ${node.children.map((child) => html`<${TraceNode} key=${child.id} node=${child} selectedNodeId=${selectedNodeId} onPick=${onPick} />`)}
          </div>`
        : null}
    </div>
  `;
}

function ScenarioButton({ scenario, active, onClick }) {
  return html`
    <button class=${`ck-card scenario-card ${active ? "scenario-card-active" : ""}`} onClick=${onClick}>
      <div class="ck-spread">
        <strong>${scenario.label}</strong>
        <span class="ck-badge ck-badge-accent">${scenario.type}</span>
      </div>
      <div class="ck-muted" style="margin-top:6px">${scenario.note}</div>
      <div class="ck-row ck-caption" style="margin-top:10px; gap:8px; flex-wrap:wrap">
        <span>vol ${percent(scenario.impact.volatility)}</span>
        <span>dd ${percent(scenario.impact.drawdown)}</span>
        <span>ret ${percent(scenario.impact.return)}</span>
      </div>
    </button>
  `;
}

function App({ state, invoke, connected }) {
  const [busy, setBusy] = useState(false);
  const [selectedNode, setSelectedNode] = useState(state?.selectedTraceNode ?? "root");
  const [approvalId, setApprovalId] = useState("run_backtest");
  const [selectedScenario, setSelectedScenario] = useState(state?.selectedScenario ?? "rates_50bps");

  const scenarioResult = state?.scenarioResult;
  const comparison = state?.comparison;
  const activeScenario = useMemo(
    () => state?.selectedScenario ?? "rates_50bps",
    [state?.selectedScenario],
  );

  async function run(action, input) {
    setBusy(true);
    try {
      await invoke(action, input);
    } finally {
      setBusy(false);
    }
  }

  if (!state) return html`<p class="ck-muted">Loading…</p>`;

  return html`
    <div>
      <div class="ck-spread" style="margin-bottom:14px">
        <div class="ck-row" style="gap:8px">
          <${Icon} name="landmark" size=${20} />
          <h1 style="margin:0">${TITLE}</h1>
        </div>
        <span class="ck-status">
          <span class=${`ck-dot ${connected ? "ck-dot-live" : "ck-dot-off"}`}></span>
          ${connected ? "live" : "reconnecting…"}
        </span>
      </div>

      <div class="ck-card ck-row" style="margin:12px 0 16px; gap:8px; flex-wrap:wrap">
        <select class="ck-input" value=${state.identity} onChange=${(e) => run("set_identity", { identity: e.target.value })}>
          <option value="PM_USER">PM_USER</option>
          <option value="RISK_USER">RISK_USER</option>
          <option value="ADMIN_USER">ADMIN_USER</option>
        </select>
        <select class="ck-input" value=${state.portfolio} onChange=${(e) => run("select_portfolio", { portfolio: e.target.value })}>
          <option value="PORT_A">PORT_A</option>
          <option value="PORT_B">PORT_B</option>
        </select>
        <button class="ck-btn" disabled=${busy} onClick=${() => run("set_view", { view: "overview" })}>Overview</button>
        <button class="ck-btn" disabled=${busy} onClick=${() => run("set_view", { view: "scenarios" })}>Scenarios</button>
        <button class="ck-btn" disabled=${busy} onClick=${() => run("set_view", { view: "traces" })}>Trace</button>
        <button class="ck-btn" disabled=${busy} onClick=${() => run("set_view", { view: "provenance" })}>Provenance</button>
      </div>

      <div class="ops-layout">
        <section>
          <div class="ck-card">
            <div class="ck-spread">
              <strong>Current portfolio</strong>
              <span class="ck-badge ck-badge-success">${state.role}</span>
            </div>
            <div class="ck-muted" style="margin-top:6px">${state.portfolioLabel}</div>
            <div class="ck-row" style="gap:10px; flex-wrap:wrap; margin-top:12px">
              <${MetricCard} title="Market value" value=${compactNumber(state.currentMetrics.totalMarketValue)} caption="Mock positions + public inputs" />
              <${MetricCard} title="Volatility" value=${percent(state.currentMetrics.volatility)} caption="Day 6 style risk metric" />
              <${MetricCard} title="Max drawdown" value=${percent(state.currentMetrics.maxDrawdown)} caption="Path dependent risk" />
              <${MetricCard} title="Largest position" value=${percent(state.currentMetrics.largestPositionWeight)} caption="Concentration snapshot" />
            </div>
          </div>

          <div class="ck-card" style="margin-top:12px">
            <div class="ck-spread">
              <strong>Holdings</strong>
              <span class="ck-caption">Current allocation</span>
            </div>
            <div class="ck-col" style="gap:8px; margin-top:10px">
              ${state.holdings.map((holding) => html`
                <div class="ck-row" key=${holding.id} style="gap:10px; align-items:flex-start">
                  <span class="ck-badge ck-badge-muted">${percent(holding.weight)}</span>
                  <div>
                    <strong>${holding.name}</strong>
                    <div class="ck-muted">${holding.provenance}</div>
                  </div>
                </div>
              `)}
            </div>
          </div>

          <div class="ck-card" style="margin-top:12px">
            <div class="ck-spread">
              <strong>Guardrails</strong>
              <span class="ck-caption">Role-gated controls</span>
            </div>
            <div class="ck-col" style="gap:8px; margin-top:10px">
              ${state.guardrails.map((item) => html`
                <div class="ck-row" key=${item.id} style="gap:8px; align-items:flex-start">
                  <span class=${`ck-badge ${item.result === "allowed" ? "ck-badge-success" : item.result === "blocked" ? "ck-badge-danger" : "ck-badge-attention"}`}>${item.result}</span>
                  <div>
                    <strong>${item.title}</strong>
                    <div class="ck-muted">${item.detail}</div>
                  </div>
                </div>
              `)}
            </div>
          </div>
        </section>

        <section class="ops-main">
          <div class="ck-card">
            <div class="ck-spread">
              <strong>Scenario shock</strong>
              <span class="ck-caption">${state.lastAction}</span>
            </div>
            <div class="ck-row" style="gap:10px; flex-wrap:wrap; margin-top:12px">
              ${Object.values(SCENARIOS).map((scenario) =>
                html`<${ScenarioButton}
                  key=${scenario.id}
                  scenario=${scenario}
                  active=${activeScenario === scenario.id}
                  onClick=${() => {
                    setSelectedScenario(scenario.id);
                    run("run_scenario", { scenarioId: scenario.id });
                  }}
                />`)}
            </div>
          </div>

          ${scenarioResult
            ? html`
              <div class="ck-card" style="margin-top:12px">
                <div class="ck-spread">
                  <strong>Scenario result</strong>
                  <span class="ck-badge ck-badge-accent">${scenarioResult.type}</span>
                </div>
                <div class="ck-row" style="gap:10px; flex-wrap:wrap; margin-top:12px">
                  <${MetricCard} title="Baseline volatility" value=${percent(scenarioResult.comparedAgainst.volatility)} caption="Before the shock" />
                  <${MetricCard} title="Stressed volatility" value=${percent(scenarioResult.stressed.volatility)} caption="After the shock" />
                  <${MetricCard} title="Baseline drawdown" value=${percent(scenarioResult.comparedAgainst.maxDrawdown)} caption="Before the shock" />
                  <${MetricCard} title="Stressed drawdown" value=${percent(scenarioResult.stressed.maxDrawdown)} caption="After the shock" />
                </div>
                <div class="ck-muted" style="margin-top:10px">${scenarioResult.note}</div>
              </div>
            `
            : null}

          <div class="ck-card" style="margin-top:12px">
            <div class="ck-spread">
              <strong>Agent trace</strong>
              <span class="ck-caption">Pick a node to focus</span>
            </div>
            <div style="margin-top:10px">
              <${TraceNode} node=${state.trace} selectedNodeId=${selectedNode} onPick=${(nodeId) => {
                setSelectedNode(nodeId);
                run("inspect_trace", { nodeId });
              }} />
            </div>
          </div>

          <div class="ck-card" style="margin-top:12px">
            <div class="ck-spread">
              <strong>Approvals</strong>
              <span class="ck-caption">Only ADMIN_USER may approve</span>
            </div>
            <div class="ck-row" style="gap:8px; flex-wrap:wrap; margin-top:10px">
              <select class="ck-input" value=${approvalId} onChange=${(e) => setApprovalId(e.target.value)}>
                ${state.approvals.map((approval) => html`<option value=${approval.id}>${approval.title}</option>`)}
              </select>
              <button class="ck-btn ck-btn-primary" disabled=${busy} onClick=${() => run("approve_run", { approvalId })}>
                <${Icon} name="circle-check" size=${16} />Approve
              </button>
            </div>
            <div class="ck-col" style="gap:8px; margin-top:10px">
              ${state.approvals.map((approval) => html`
                <div class="ck-card" key=${approval.id}>
                  <div class="ck-spread">
                    <strong>${approval.title}</strong>
                    <span class="ck-badge ${approval.status === "approved" ? "ck-badge-success" : "ck-badge-attention"}">${approval.status}</span>
                  </div>
                  <div class="ck-muted" style="margin-top:6px">${approval.note}</div>
                  ${approval.approvedAt ? html`<div class="ck-caption" style="margin-top:6px">approved ${relativeTime(approval.approvedAt)}</div>` : null}
                </div>
              `)}
            </div>
          </div>
        </section>

        <section>
          <div class="ck-card">
            <div class="ck-spread">
              <strong>Provenance</strong>
              <span class="ck-caption">What is real vs. mock</span>
            </div>
            <div class="ck-col" style="gap:8px; margin-top:10px">
              ${state.provenance.map((item) => html`
                <div class="ck-row" key=${item.id} style="gap:8px; align-items:flex-start">
                  <span class=${`ck-badge ${item.kind === "real" ? "ck-badge-success" : "ck-badge-muted"}`}>${item.kind}</span>
                  <div>
                    <strong>${item.label}</strong>
                    <div class="ck-muted">${item.note}</div>
                  </div>
                </div>
              `)}
            </div>
          </div>

          <div class="ck-card" style="margin-top:12px">
            <div class="ck-spread">
              <strong>Evaluation</strong>
              <span class="ck-caption">Versioned comparison footprint</span>
            </div>
            <div class="ck-col" style="gap:8px; margin-top:10px">
              ${state.evaluations.map((item) => html`
                <div class="ck-card" key=${item.id}>
                  <div class="ck-spread">
                    <strong>${item.label}</strong>
                    <span class="ck-badge ck-badge-accent">${item.score}</span>
                  </div>
                  <div class="ck-muted" style="margin-top:6px">${item.note}</div>
                </div>
              `)}
            </div>
          </div>

          <div class="ck-card" style="margin-top:12px">
            <div class="ck-spread">
              <strong>Comparison</strong>
              <span class="ck-caption">Day 4 / Day 5 context</span>
            </div>
            <div class="ck-card" style="margin-top:10px">
              <strong>${comparison.singleAgent.label}</strong>
              <div class="ck-caption">${comparison.singleAgent.note}</div>
              <div class="ck-muted">Latency: ${comparison.singleAgent.latencySeconds.toFixed(3)}s</div>
            </div>
            <div class="ck-card" style="margin-top:10px">
              <strong>${comparison.multiAgent.label}</strong>
              <div class="ck-caption">${comparison.multiAgent.note}</div>
              <div class="ck-muted">Latency: ${comparison.multiAgent.latencySeconds.toFixed(3)}s</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  `;
}

mountCanvas({ view: (model) => html`<${App} ...${model} />` });
