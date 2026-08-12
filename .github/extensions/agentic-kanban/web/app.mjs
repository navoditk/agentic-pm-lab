// web/app.mjs — Preact view for the Agentic Kanban canvas.
//
// SHARED state arrives over /events (SSE); the agent mutates the same data.
// LOCAL UI state (the draft input) lives in useState. Because Preact DIFFS the
// DOM (no innerHTML repaint), live pushes never clobber what you're typing.

import { html, mountCanvas, useState, Icon } from "/kit/client.mjs";

const TITLE = "Agentic Kanban";
const COLUMNS = [
  { id: "backlog", label: "Backlog", icon: "inbox" },
  { id: "in_progress", label: "In progress", icon: "loader-circle" },
  { id: "review", label: "Review", icon: "search-check" },
  { id: "done", label: "Done", icon: "circle-check" },
];

function NewCard({ invoke, onError }) {
  const [title, setTitle] = useState("");
  const [assignee, setAssignee] = useState("");
  const [busy, setBusy] = useState(false);

  async function add() {
    const cleanTitle = title.trim();
    if (!cleanTitle || busy) return;
    setBusy(true);
    try {
      await invoke("add_card", { title: cleanTitle, assignee: assignee.trim() });
      setTitle("");
      setAssignee("");
      onError("");
    } catch (error) {
      onError(error.message);
    } finally {
      setBusy(false);
    }
  }

  return html`
    <div class="ck-card ck-row" style="margin:12px 0 16px">
      <div class="ck-col ck-grow" style="gap:8px">
        <input
          class="ck-input"
          aria-label="Card title"
          placeholder="What needs to happen?"
          value=${title}
          onInput=${(event) => setTitle(event.target.value)}
          onKeyDown=${(event) => { if (event.key === "Enter") add(); }}
        />
        <input
          class="ck-input"
          aria-label="Assignee"
          placeholder="Assignee (optional)"
          value=${assignee}
          onInput=${(event) => setAssignee(event.target.value)}
        />
      </div>
      <button class="ck-btn ck-btn-primary" disabled=${!title.trim() || busy} onClick=${add}>
        <${Icon} name="plus" size=${16} />Create
      </button>
    </div>
  `;
}

function Card({ card, invoke, onError }) {
  const [assignee, setAssignee] = useState(card.assignee);
  const [busy, setBusy] = useState(false);

  async function run(action, input) {
    if (busy) return;
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
    <div class="ck-card ck-col" style="gap:10px">
      <strong>${card.title}</strong>
      <div class="ck-row" style="gap:6px">
        <${Icon} name="user-round" size=${14} />
        <input
          class="ck-input ck-grow"
          aria-label=${`Assignee for ${card.title}`}
          placeholder="Unassigned"
          value=${assignee}
          onInput=${(event) => setAssignee(event.target.value)}
          onBlur=${() => {
            if (assignee.trim() !== card.assignee) {
              run("assign_card", { id: card.id, assignee });
            }
          }}
        />
      </div>
      <select
        class="ck-input"
        aria-label=${`Column for ${card.title}`}
        value=${card.column}
        disabled=${busy}
        onChange=${(event) => run("move_card", { id: card.id, column: event.target.value })}
      >
        ${COLUMNS.map((column) =>
          html`<option key=${column.id} value=${column.id}>${column.label}</option>`)}
      </select>
    </div>
  `;
}

function App({ state, invoke, connected }) {
  const [error, setError] = useState("");
  if (!state) return html`<p class="ck-muted">Loading…</p>`;
  const cards = state.cards ?? [];

  return html`
    <div>
      <div class="ck-spread" style="margin-bottom:14px">
        <div class="ck-row" style="gap:8px">
          <${Icon} name="layout-dashboard" size=${20} />
          <h1 style="margin:0">${TITLE}</h1>
        </div>
        <span class="ck-status">
          <span class=${`ck-dot ${connected ? "ck-dot-live" : "ck-dot-off"}`}></span>
          ${connected ? "live" : "reconnecting…"}
        </span>
      </div>

      <p class="ck-muted">One live board for you and Copilot. Create, assign, and move work from either side.</p>
      ${error
        ? html`<div class="ck-callout ck-error"><${Icon} name="circle-x" size=${16} />${error}</div>`
        : null}
      <${NewCard} invoke=${invoke} onError=${setError} />

      <div class="kanban-grid">
        ${COLUMNS.map((column) => {
          const columnCards = cards.filter((card) => card.column === column.id);
          return html`
            <section class="kanban-column" key=${column.id}>
              <div class="ck-spread">
                <div class="ck-row" style="gap:6px">
                  <${Icon} name=${column.icon} size=${16} />
                  <strong>${column.label}</strong>
                </div>
                <span class="ck-badge ck-badge-muted">${columnCards.length}</span>
              </div>
              <div class="ck-col" style="gap:10px;margin-top:10px">
                ${columnCards.length
                  ? columnCards.map((card) =>
                    html`<${Card} key=${card.id} card=${card} invoke=${invoke} onError=${setError} />`)
                  : html`<div class="ck-empty">No cards</div>`}
              </div>
            </section>
          `;
        })}
      </div>
    </div>
  `;
}

mountCanvas({ view: (model) => html`<${App} ...${model} />` });
