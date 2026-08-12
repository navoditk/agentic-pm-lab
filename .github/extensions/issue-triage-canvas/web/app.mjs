import {
  html,
  mountCanvas,
  useEffect,
  useMemo,
  useState,
  Icon,
  pollWhileVisible,
  relativeTime,
} from "/kit/client.mjs";

const PRIORITY_BADGE = {
  high: "ck-badge-danger",
  medium: "ck-badge-attention",
  normal: "ck-badge-muted",
};

function Toolbar({ state, invoke, busy, setBusy, onError }) {
  const [repository, setRepository] = useState(state.repository);

  async function run(action, input = {}) {
    setBusy(true);
    try {
      await invoke(action, input);
      onError("");
    } catch (error) {
      onError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return html`
    <div class="ck-card ck-row" style="margin:12px 0 16px">
      <input
        class="ck-input ck-grow"
        aria-label="GitHub repository"
        value=${repository}
        onInput=${(event) => setRepository(event.target.value)}
      />
      <button
        class="ck-btn"
        disabled=${busy || repository.trim() === state.repository}
        onClick=${() => run("set_repository", { repository: repository.trim() })}
      >Set repository</button>
      <button class="ck-btn ck-btn-primary" disabled=${busy} onClick=${() => run("refresh_issues")}>
        <${Icon} name=${busy ? "loader-circle" : "refresh-cw"} size=${16} class=${busy ? "ck-spinner" : ""} />
        ${busy ? "Loading…" : "Refresh"}
      </button>
    </div>
  `;
}

function Issue({ issue, invoke, onError }) {
  const [assignees, setAssignees] = useState(issue.assignees.join(", "));
  const [busy, setBusy] = useState(false);

  async function run(action, input) {
    setBusy(true);
    try {
      await invoke(action, input);
      onError("");
    } catch (error) {
      onError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return html`
    <article class="ck-card ck-col issue-card" style="gap:10px">
      <div class="ck-spread">
        <div class="ck-row" style="gap:8px">
          <span class=${`ck-badge ${PRIORITY_BADGE[issue.priority]}`}>${issue.priority}</span>
          <a href=${issue.url} target="_blank" rel="noreferrer">#${issue.number} ${issue.title}</a>
        </div>
        <span class="ck-caption">${relativeTime(issue.updatedAt)}</span>
      </div>
      <div class="ck-row issue-meta">
        ${issue.labels.map((label) => html`<span class="ck-badge ck-badge-accent">${label}</span>`)}
        <span class="ck-caption">${issue.comments} comments</span>
      </div>
      <div class="ck-row">
        <input
          class="ck-input ck-grow"
          aria-label=${`Assignees for issue ${issue.number}`}
          placeholder="Comma-separated GitHub usernames"
          value=${assignees}
          onInput=${(event) => setAssignees(event.target.value)}
        />
        <button
          class="ck-btn"
          disabled=${busy}
          onClick=${() => run("assign_issue", {
            number: issue.number,
            assignees: assignees.split(",").map((name) => name.trim()).filter(Boolean),
          })}
        ><${Icon} name="user-round-check" size=${16} />Assign</button>
        <button
          class=${`ck-btn ${issue.state === "open" ? "ck-btn-danger" : ""}`}
          disabled=${busy}
          onClick=${() => run("set_issue_status", {
            number: issue.number,
            state: issue.state === "open" ? "closed" : "open",
          })}
        >
          <${Icon} name=${issue.state === "open" ? "circle-check" : "circle-dot"} size=${16} />
          ${issue.state === "open" ? "Close" : "Reopen"}
        </button>
      </div>
    </article>
  `;
}

function App({ state, invoke, connected }) {
  const [query, setQuery] = useState("");
  const [priority, setPriority] = useState("all");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    if (state && !state.lastRefresh) invoke("refresh_issues").catch(() => {});
  }, [state?.lastRefresh]);
  useEffect(
    () => pollWhileVisible(() => invoke("refresh_issues"), state?.autoRefreshSec || 0),
    [state?.autoRefreshSec],
  );

  const issues = useMemo(() => {
    if (!state) return [];
    const needle = query.trim().toLowerCase();
    return state.issues.filter((issue) =>
      (priority === "all" || issue.priority === priority)
      && (!needle || `${issue.number} ${issue.title} ${issue.labels.join(" ")}`.toLowerCase().includes(needle)));
  }, [state?.issues, query, priority]);

  if (!state) return html`<p class="ck-muted">Loading…</p>`;
  const error = actionError || state.error;

  return html`
    <div>
      <div class="ck-spread">
        <div class="ck-row" style="gap:8px">
          <${Icon} name="list-filter" size=${20} />
          <h1 style="margin:0">Issue Triage</h1>
        </div>
        <span class="ck-status">
          <span class=${`ck-dot ${connected ? "ck-dot-live" : "ck-dot-off"}`}></span>
          ${connected ? "live" : "reconnecting…"}
        </span>
      </div>

      <${Toolbar}
        state=${state}
        invoke=${invoke}
        busy=${busy}
        setBusy=${setBusy}
        onError=${setActionError}
      />

      ${error
        ? html`<div class="ck-callout ck-error"><${Icon} name="circle-x" size=${16} />${error}</div>`
        : null}

      <div class="ck-row" style="margin:14px 0">
        <input
          class="ck-input ck-grow"
          aria-label="Filter issues"
          placeholder="Filter by number, title, or label…"
          value=${query}
          onInput=${(event) => setQuery(event.target.value)}
        />
        <select class="ck-input" value=${priority} onChange=${(event) => setPriority(event.target.value)}>
          <option value="all">All priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="normal">Normal</option>
        </select>
      </div>

      <div class="ck-spread ck-caption" style="margin-bottom:8px">
        <span>${issues.length} of ${state.issues.length} open issues</span>
        <span>${state.lastRefresh ? `updated ${relativeTime(state.lastRefresh)}` : "not loaded"}</span>
      </div>
      <div class="ck-col" style="gap:10px">
        ${issues.length
          ? issues.map((issue) =>
            html`<${Issue} key=${issue.number} issue=${issue} invoke=${invoke} onError=${setActionError} />`)
          : html`<div class="ck-empty"><${Icon} name="inbox" size=${20} />No matching issues.</div>`}
      </div>
    </div>
  `;
}

mountCanvas({ view: (model) => html`<${App} ...${model} />` });
