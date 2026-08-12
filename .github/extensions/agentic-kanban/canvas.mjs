// canvas.mjs — Agentic Kanban canvas definition (kit config; SDK-free).
//
// Shared state: the agent and the user read/write the SAME state through the
// SAME action handlers. State is durable per-user and keyed by a "domain"
// resolved from the open input (defaults to "default").

import { fileURLToPath } from "node:url";
import { userStore } from "./canvas-kit/storage.mjs";
import { nid } from "./canvas-kit/format.mjs";

const EXT_NAME = "agentic-kanban";

function fileFor(domainId) {
  const safe = String(domainId).replace(/[^A-Za-z0-9._-]/g, "_") || "default";
  return userStore(EXT_NAME, `${safe}.json`);
}

export const canvasConfig = {
  id: "agentic-kanban",
  displayName: "Agentic Kanban",
  description: "Create, assign, and move work on a shared agent-and-human Kanban board.",
  assetsDir: fileURLToPath(new URL("./web/", import.meta.url)),

  inputSchema: {
    type: "object",
    properties: {
      domain: { type: "string", description: "Logical board to open. Omit for the default." },
    },
    additionalProperties: false,
  },

  resolveDomainId: (input) => (input?.domain ? String(input.domain) : "default"),
  stateSchema: {
    type: "object",
    properties: {
      cards: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id: { type: "string" },
            title: { type: "string" },
            assignee: { type: "string" },
            column: { type: "string", enum: ["backlog", "in_progress", "review", "done"] },
            createdAt: { type: "string" },
          },
          required: ["id", "title", "assignee", "column", "createdAt"],
          additionalProperties: false,
        },
      },
    },
    required: ["cards"],
    additionalProperties: false,
  },
  createInitialState: () => ({ cards: [] }),
  loadState: async (domainId) => fileFor(domainId).load(null),
  saveState: async (domainId, state) => fileFor(domainId).save(state),
  statusLine: (_ctx, state) => `${state.cards.length} cards`,

  actions: {
    add_card: {
      description: "Create a card in the shared Kanban board.",
      inputSchema: {
        type: "object",
        properties: {
          title: { type: "string", description: "Concise work item title." },
          assignee: { type: "string", description: "Assignee name; omit for unassigned." },
          column: {
            type: "string",
            enum: ["backlog", "in_progress", "review", "done"],
            description: "Initial workflow column; defaults to backlog.",
          },
        },
        required: ["title"],
        additionalProperties: false,
      },
      handler: ({ set, input }) => {
        const title = input.title.trim();
        if (!title) throw new Error("Card title is required");
        const card = {
          id: nid(),
          title,
          assignee: input.assignee?.trim() ?? "",
          column: input.column ?? "backlog",
          createdAt: new Date().toISOString(),
        };
        set((current) => ({ ...current, cards: [card, ...current.cards] }));
        return { id: card.id, column: card.column };
      },
    },

    assign_card: {
      description: "Set or clear the assignee for an existing card.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Card identifier." },
          assignee: { type: "string", description: "Assignee name; empty clears assignment." },
        },
        required: ["id", "assignee"],
        additionalProperties: false,
      },
      handler: ({ set, input }) => {
        let found = false;
        const assignee = input.assignee.trim();
        set((current) => {
          const cards = current.cards.map((card) => {
            if (card.id !== input.id) return card;
            found = true;
            return { ...card, assignee };
          });
          return { ...current, cards };
        });
        if (!found) throw new Error(`No card with id ${input.id}`);
        return { id: input.id, assignee };
      },
    },

    move_card: {
      description: "Move an existing card to a workflow column.",
      inputSchema: {
        type: "object",
        properties: {
          id: { type: "string", description: "Card identifier." },
          column: {
            type: "string",
            enum: ["backlog", "in_progress", "review", "done"],
          },
        },
        required: ["id", "column"],
        additionalProperties: false,
      },
      handler: ({ set, input }) => {
        let found = false;
        set((current) => {
          const cards = current.cards.map((card) => {
            if (card.id !== input.id) return card;
            found = true;
            return { ...card, column: input.column };
          });
          return { ...current, cards };
        });
        if (!found) throw new Error(`No card with id ${input.id}`);
        return { id: input.id, column: input.column };
      },
    },

    list_cards: {
      description: "List the current cards so Copilot can inspect the shared board.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler: ({ state }) => {
        if (!state.cards.length) return { summary: "No cards yet.", count: 0 };
        const summary = state.cards
          .map((card) =>
            `- [${card.column}] ${card.title}${card.assignee ? ` (${card.assignee})` : ""}`)
          .join("\n");
        return { count: state.cards.length, summary };
      },
    },
  },
};
