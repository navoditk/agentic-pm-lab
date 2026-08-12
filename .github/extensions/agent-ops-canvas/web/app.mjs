import {
  html,
  mountCanvas,
  useEffect,
  useMemo,
  useState,
  Icon,
  pollWhileVisible,
  compactNumber,
  relativeTime,
  percent,
} from "/kit/client.mjs";

const TITLE = "Agent Operations";
const RUN_KINDS = ["all", "single-agent", "multi-agent", "evaluation", "approval"];
const EVAL_SUBSETS = ["fast", "full"];

function formatMetric(value, suffix = "") {
  if (value === null || value === undefined) return "—";
  if (suffix === "$") return `$${Number(value).toFixed(4)}`;
  if (suffix === "s") return `${Number(value).toFixed(2)}s`;
  return String(value);
}

function RunNode({ node, selectedNodeId, onSelect }) {
  return html`
    <div class="trace-node ${node.id === selectedNodeId ? "trace-node-active" : ""}">
      <div class="ck-spread">
        <button class="ck-btn ck-btn-sm" onClick=${() => onSelect(node.id)}>
          <${Icon} name=${node.status === "completed" ? "circle-check" : node.status === "failed" ? "circle-x" : "circle-dot"} size=${14} />
          <span>${node.label}</span>
        </button>
        <span class="ck-caption">${node.retryCount ? `retries ${node.retryCount}` : node.status}</span>
      </div>
      <div class="ck-muted" style="margin:6px 0 0">${node.detail}</div>
      ${node.children?.length
        ? html`<div class="trace-children">${node.children.map((child) => html`<${RunNode} key=${child.id} node=${child} selectedNodeId=${selectedNodeId} onSelect=${onSelect} />`)}</div>`
        : null}
    </div>
  `;
}

function RunCard({ run, active, onClick }) {
  return html`
    <button class=${`ck-card run-card ${active ? "run-card-active" : ""}`} onClick=${onClick}>
      <div class="ck-spread">
        <strong>${run.title}</strong>
        <span class="ck-badge ${run.status === "completed" ? "ck-badge-success" : run.status === "waiting-for-approval" ? "ck-badge-attention" : "ck-badge-muted"}">${run.status}</span>
      </div>
      <div class="ck-muted" style="margin-top:6px">${run.summary}</div>
      <div class="ck-row ck-caption" style="margin-top:10px; gap:8px; flex-wrap:wrap">
        <span>${run.kind}</span>
        <span>${run.model}</span>
        <span>${formatMetric(run.metrics.latencySeconds, "s")}</span>
        <span>${run.metrics.estimatedCostUsd === null ? "n/a" : formatMetric(run.metrics.estimatedCostUsd, "$")}</span>
      </div>
    </button>
  `;
}

function MetricTile({ label, value, caption }) {
  return html`
    <div class="ck-card metric-tile">
      <div class="ck-caption">${label}</div>
      <div style="font-size:1.15rem;font-weight:var(--ck-fw-semibold)">${value}</div>
      ${caption ? html`<div class="ck-muted">${caption}</div>` : null}
    </div>
  `;
}

function PanelTitle({ icon, title, action }) {
  return html`
    <div class="ck-spread" style="margin-bottom:10px">
      <div class="ck-row" style="gap:8px">
        <${Icon} name=${icon} size=${18} />
        <strong>${title}</strong>
      </div>
      ${action}
    </div>
  `;
}

function App({ state, invoke, connected }) {
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState("all");
  const [compareRunId, setCompareRunId] = useState("day5-multi-local-qwen3");
  const [subset, setSubset] = useState("full");
  const [focusedNodeId, setFocusedNodeId] = useState("root");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (state && !state.lastRefresh) invoke("get_runs", {}).catch(() => {});
  }, [state?.lastRefresh]);
  useEffect(() => pollWhileVisible(() => invoke("get_runs", {}), 60), []);

  const runs = useMemo(() => {
    if (!state) return [];
    const needle = query.trim().toLowerCase();
    return state.runs.filter((run) =>
      (kind === "all" || run.kind === kind)
      && (!needle || `${run.title} ${run.summary} ${run.question}`.toLowerCase().includes(needle)));
  }, [state?.runs, query, kind]);

  const selectedRun = state ? state.runs.find((run) => run.id === state.selectedRunId) ?? state.runs[0] : null;
  const compareRun = state ? state.runs.find((run) => run.id === compareRunId) ?? state.runs[2] : null;

  async function runAction(action, input) {
    setBusy(true);
    try {
      await invoke(action, input);
    } finally {
      setBusy(false);
    }
  }

  if (!state) return html`<p class="ck-muted">Loading…</p>`;
  const latestEvaluation = state.latestEvaluation;
  const evaluationError = state.evaluationError;
  const selectedTrace = selectedRun?.trace;

  return html`
    <div>
      <div class="ck-spread" style="margin-bottom:14px">
        <div class="ck-row" style="gap:8px">
          <${Icon} name="activity" size=${20} />
          <h1 style="margin:0">${TITLE}</h1>
        </div>
        <span class="ck-status">
          <span class=${`ck-dot ${connected ? "ck-dot-live" : "ck-dot-off"}`}></span>
          ${connected ? "live" : "reconnecting…"}
        </span>
      </div>

      <div class="ck-card ck-row" style="margin:12px 0 16px">
        <input class="ck-input ck-grow" placeholder="Search runs…" value=${query} onInput=${(e) => setQuery(e.target.value)} />
        <select class="ck-input" value=${kind} onChange=${(e) => setKind(e.target.value)}>
          ${RUN_KINDS.map((value) => html`<option value=${value}>${value}</option>`)}
        </select>
        <button class="ck-btn" disabled=${busy} onClick=${() => runAction("get_runs", { query, kind })}>
          <${Icon} name="refresh-cw" size=${16} />Refresh
        </button>
      </div>

      <div class="ops-layout">
        <section>
          <${PanelTitle}
            icon="list-filter"
            title=${`Runs (${runs.length})`}
            action=${html`
              <select class="ck-input" value=${compareRunId} onChange=${(e) => setCompareRunId(e.target.value)}>
                ${state.runs.map((run) => html`<option value=${run.id}>Compare: ${run.title}</option>`)}
              </select>
            `}
          />
          <div class="ck-col" style="gap:10px">
            ${runs.map((run) => html`
              <${RunCard}
                key=${run.id}
                run=${run}
                active=${run.id === state.selectedRunId}
                onClick=${() => runAction("get_runs", { run_id: run.id, query, kind })}
              />
            `)}
          </div>
        </section>

        <section class="ops-main">
          <${PanelTitle}
            icon="git-branch"
            title=${selectedRun ? selectedRun.title : "Selected run"}
            action=${html`
              <div class="ck-row" style="gap:8px">
                <button class="ck-btn ck-btn-sm" disabled=${busy || !selectedRun} onClick=${() => selectedRun && runAction("get_trace", { run_id: selectedRun.id, node_id: focusedNodeId })}>
                  <${Icon} name="route" size=${14} />Inspect trace
                </button>
                <button class="ck-btn ck-btn-sm" disabled=${busy || !selectedRun} onClick=${() => selectedRun && runAction("get_guardrail_results", { run_id: selectedRun.id })}>
                  <${Icon} name="shield-check" size=${14} />Guardrails
                </button>
                <button class="ck-btn ck-btn-sm" disabled=${busy || !selectedRun} onClick=${() => selectedRun && runAction("get_cost_metrics", { run_id: selectedRun.id })}>
                  <${Icon} name="clock-3" size=${14} />Costs
                </button>
              </div>
            `}
          />

          <div class="ck-row" style="gap:10px; flex-wrap:wrap">
            <${MetricTile} label="Latency" value=${formatMetric(selectedRun?.metrics.latencySeconds, "s")} caption="End-to-end or evaluation latency" />
            <${MetricTile} label="Cost" value=${selectedRun?.metrics.estimatedCostUsd === null ? "n/a" : formatMetric(selectedRun.metrics.estimatedCostUsd, "$")} caption="Estimated usage cost" />
            <${MetricTile} label="Input tokens" value=${selectedRun?.metrics.inputTokens === null ? "n/a" : compactNumber(selectedRun.metrics.inputTokens)} caption="Observed or estimated" />
            <${MetricTile} label="Output tokens" value=${selectedRun?.metrics.outputTokens === null ? "n/a" : compactNumber(selectedRun.metrics.outputTokens)} caption="Observed or estimated" />
          </div>

          ${evaluationError
            ? html`<div class="ck-callout ck-error" style="margin:12px 0"><${Icon} name="circle-x" size=${16} />${evaluationError}</div>`
            : null}

          ${latestEvaluation
            ? html`
              <div class="ck-card" style="margin:12px 0">
                <div class="ck-spread">
                  <strong>Latest evaluation</strong>
                  <span class="ck-badge ck-badge-accent">${latestEvaluation.status}</span>
                </div>
                <div class="ck-row ck-caption" style="margin-top:6px; gap:8px; flex-wrap:wrap">
                  <span>${latestEvaluation.subset}</span>
                  <span>${latestEvaluation.caseCount ?? "—"} cases</span>
                  <span>${formatMetric(latestEvaluation.totalLatencySeconds, "s")}</span>
                  <span>${latestEvaluation.estimatedCostUsd === null ? "n/a" : formatMetric(latestEvaluation.estimatedCostUsd, "$")}</span>
                </div>
                <div class="ck-muted" style="margin-top:6px">${latestEvaluation.experimentName ?? latestEvaluation.note ?? "Experiment completed."}</div>
              </div>
            `
            : null}

          <div class="ck-row" style="gap:8px; flex-wrap:wrap; margin:12px 0">
            <select class="ck-input" value=${subset} onChange=${(e) => setSubset(e.target.value)}>
              ${EVAL_SUBSETS.map((value) => html`<option value=${value}>${value}</option>`)}
            </select>
            <button class="ck-btn ck-btn-primary" disabled=${busy || !selectedRun} onClick=${() => selectedRun && runAction("run_evaluation", { subset, run_id: selectedRun.id })}>
              <${Icon} name="sparkles" size=${16} />Run evaluation
            </button>
            <button class="ck-btn" disabled=${busy || !selectedRun} onClick=${() => selectedRun && runAction("approve_run", { run_id: selectedRun.id, approved: true })}>
              <${Icon} name="circle-check" size=${16} />Approve run
            </button>
            <button class="ck-btn" disabled=${busy || !selectedRun || !focusedNodeId} onClick=${() => selectedRun && runAction("retry_node", { run_id: selectedRun.id, node_id: focusedNodeId, reason: "Requested from the canvas" })}>
              <${Icon} name="rotate-ccw" size=${16} />Retry node
            </button>
          </div>

          <div class="ck-card" style="margin-top:12px">
            <div class="ck-spread">
              <strong>Trace</strong>
              <span class="ck-caption">Focus: ${focusedNodeId}</span>
            </div>
            ${selectedTrace
              ? html`
                <div style="margin-top:10px">
                  <${RunNode} node=${selectedTrace} selectedNodeId=${focusedNodeId} onSelect=${setFocusedNodeId} />
                </div>
              `
              : html`<div class="ck-empty" style="margin-top:10px"><${Icon} name="route" size=${18} />Select a run to inspect its trace.</div>`}
          </div>
        </section>

        <section>
          <${PanelTitle} icon="columns-3" title="Comparison" />
          <div class="ck-card">
            <div class="ck-caption">Selected</div>
            <strong>${selectedRun?.title ?? "—"}</strong>
            <div class="ck-row ck-caption" style="margin-top:8px; gap:8px; flex-wrap:wrap">
              <span>${formatMetric(selectedRun?.metrics.latencySeconds, "s")}</span>
              <span>${selectedRun?.metrics.estimatedCostUsd === null ? "n/a" : formatMetric(selectedRun.metrics.estimatedCostUsd, "$")}</span>
            </div>
          </div>
          <div class="ck-card" style="margin-top:10px">
            <div class="ck-caption">Compared with</div>
            <strong>${compareRun?.title ?? "—"}</strong>
            <div class="ck-row ck-caption" style="margin-top:8px; gap:8px; flex-wrap:wrap">
              <span>${formatMetric(compareRun?.metrics.latencySeconds, "s")}</span>
              <span>${compareRun?.metrics.estimatedCostUsd === null ? "n/a" : formatMetric(compareRun.metrics.estimatedCostUsd, "$")}</span>
            </div>
          </div>

          <div class="ck-card" style="margin-top:10px">
            <div class="ck-caption">Latency delta</div>
            <strong>
              ${selectedRun?.metrics.latencySeconds && compareRun?.metrics.latencySeconds
                ? `${formatMetric(selectedRun.metrics.latencySeconds - compareRun.metrics.latencySeconds, "s")}`
                : "—"}
            </strong>
            <div class="ck-muted" style="margin-top:6px">
              ${selectedRun?.metrics.latencySeconds && compareRun?.metrics.latencySeconds
                ? `Selected minus comparison = ${(selectedRun.metrics.latencySeconds - compareRun.metrics.latencySeconds).toFixed(2)} seconds`
                : "Pick two runs with latency to compare."}
            </div>
          </div>

          <div class="ck-card" style="margin-top:10px">
            <strong>Guardrails</strong>
            <div class="ck-col" style="gap:8px; margin-top:10px">
              ${(selectedRun?.guardrails ?? []).map((guardrail) => html`
                <div class="ck-row" key=${guardrail.name} style="gap:8px; align-items:flex-start">
                  <span class=${`ck-badge ${guardrail.result === "pass" ? "ck-badge-success" : guardrail.result === "warn" ? "ck-badge-attention" : guardrail.result === "pending" ? "ck-badge-muted" : "ck-badge-danger"}`}>${guardrail.result}</span>
                  <div>
                    <strong>${guardrail.name}</strong>
                    <div class="ck-muted">${guardrail.detail}</div>
                  </div>
                </div>
              `)}
            </div>
          </div>

          <div class="ck-card" style="margin-top:10px">
            <strong>Run notes</strong>
            <div class="ck-muted" style="margin-top:8px">
              ${selectedRun?.comparisonNote ?? "Select a run to see notes."}
            </div>
          </div>
        </section>
      </div>
    </div>
  `;
}

mountCanvas({ view: (model) => html`<${App} ...${model} />` });
