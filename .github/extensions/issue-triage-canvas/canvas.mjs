import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { userStore } from "./canvas-kit/storage.mjs";
import { safeFetch } from "./canvas-kit/net.mjs";

const execFileAsync = promisify(execFile);
const EXT_NAME = "issue-triage-canvas";
const DEFAULT_REPOSITORY = "navoditk/agentic-pm-lab";
const API_ROOT = "https://api.github.com";

function fileFor(domainId) {
  const safe = String(domainId).replace(/[^A-Za-z0-9._-]/g, "_") || "default";
  return userStore(EXT_NAME, `${safe}.json`);
}

async function githubToken(required) {
  const envToken = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
  if (envToken) return envToken;
  try {
    const { stdout } = await execFileAsync("gh", ["auth", "token"], {
      timeout: 5_000,
      maxBuffer: 16_384,
    });
    return stdout.trim();
  } catch {
    if (required) {
      throw new Error("GitHub authentication is required; run `gh auth login`");
    }
    return "";
  }
}

async function githubRequest(path, { method = "GET", body, authRequired = false } = {}) {
  const token = await githubToken(authRequired);
  const response = await safeFetch(`${API_ROOT}${path}`, {
    method,
    headers: {
      Accept: "application/vnd.github+json",
      "User-Agent": "agentic-pm-lab-canvas",
      "X-GitHub-Api-Version": "2022-11-28",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  if (!response.ok) {
    const requestId = response.headers.get("x-github-request-id");
    throw new Error(`GitHub API returned HTTP ${response.status}${requestId ? ` (${requestId})` : ""}`);
  }
  return response.status === 204 ? null : response.json();
}

function priorityFor(issue) {
  const labels = issue.labels.map((label) => label.toLowerCase());
  if (labels.some((label) => /critical|urgent|p0|priority: high/.test(label))) return "high";
  if (labels.some((label) => /p1|priority: medium|bug/.test(label))) return "medium";
  return "normal";
}

function mapIssues(rows) {
  return rows
    .filter((row) => !row.pull_request)
    .map((row) => {
      const issue = {
        number: row.number,
        title: String(row.title),
        url: String(row.html_url),
        state: row.state === "closed" ? "closed" : "open",
        labels: (row.labels ?? []).map((label) => String(label.name ?? label)),
        assignees: (row.assignees ?? []).map((user) => String(user.login)),
        comments: Number(row.comments ?? 0),
        updatedAt: String(row.updated_at),
        priority: "normal",
      };
      issue.priority = priorityFor(issue);
      return issue;
    })
    .sort((left, right) => {
      const rank = { high: 0, medium: 1, normal: 2 };
      return rank[left.priority] - rank[right.priority]
        || right.comments - left.comments
        || right.updatedAt.localeCompare(left.updatedAt);
    });
}

function replaceIssue(current, number, update) {
  let found = false;
  const issues = current.issues.map((issue) => {
    if (issue.number !== number) return issue;
    found = true;
    return { ...issue, ...update };
  });
  if (!found) throw new Error(`Issue #${number} is not loaded`);
  return { ...current, issues, error: null };
}

export function createActions(requestGithub = githubRequest) {
  return {
    refresh_issues: {
      description: "Load open issues from the configured GitHub repository.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler: async ({ state, set }) => {
        const repository = state.repository;
        try {
          const rows = await requestGithub(`/repos/${repository}/issues?state=open&per_page=50`);
          const issues = mapIssues(rows);
          set((current) => current.repository === repository
            ? { ...current, issues, error: null, lastRefresh: new Date().toISOString() }
            : current);
          return { count: issues.length, repository };
        } catch (error) {
          const message = `Couldn't load issues: ${error.message}`;
          set((current) => current.repository === repository
            ? { ...current, error: message, lastRefresh: new Date().toISOString() }
            : current);
          return { ok: false, error: message };
        }
      },
    },

    set_repository: {
      description: "Select the owner/repository whose issues should be triaged.",
      inputSchema: {
        type: "object",
        properties: {
          repository: {
            type: "string",
            pattern: "^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$",
            description: "GitHub owner/repository.",
          },
        },
        required: ["repository"],
        additionalProperties: false,
      },
      handler: ({ set, input }) => {
        const repository = input.repository.trim();
        set((current) => ({ ...current, repository, issues: [], error: null, lastRefresh: null }));
        return { repository };
      },
    },

    assign_issue: {
      description: "Replace the assignees on a loaded GitHub issue.",
      inputSchema: {
        type: "object",
        properties: {
          number: { type: "integer", minimum: 1 },
          assignees: {
            type: "array",
            items: { type: "string" },
            maxItems: 10,
            description: "GitHub usernames; an empty list clears assignments.",
          },
        },
        required: ["number", "assignees"],
        additionalProperties: false,
      },
      handler: async ({ state, set, input }) => {
        if (!state.issues.some((issue) => issue.number === input.number)) {
          throw new Error(`Issue #${input.number} is not loaded`);
        }
        const data = await requestGithub(
          `/repos/${state.repository}/issues/${input.number}`,
          { method: "PATCH", body: { assignees: input.assignees }, authRequired: true },
        );
        const assignees = (data.assignees ?? []).map((user) => String(user.login));
        set((current) => replaceIssue(current, input.number, { assignees }));
        return { number: input.number, assignees };
      },
    },

    set_issue_status: {
      description: "Set a loaded GitHub issue to open or closed.",
      inputSchema: {
        type: "object",
        properties: {
          number: { type: "integer", minimum: 1 },
          state: { type: "string", enum: ["open", "closed"] },
        },
        required: ["number", "state"],
        additionalProperties: false,
      },
      handler: async ({ state, set, input }) => {
        if (!state.issues.some((issue) => issue.number === input.number)) {
          throw new Error(`Issue #${input.number} is not loaded`);
        }
        const data = await requestGithub(
          `/repos/${state.repository}/issues/${input.number}`,
          { method: "PATCH", body: { state: input.state }, authRequired: true },
        );
        const issueState = data.state === "closed" ? "closed" : "open";
        set((current) => replaceIssue(current, input.number, { state: issueState }));
        return { number: input.number, state: issueState };
      },
    },

    list_issues: {
      description: "Summarize loaded issues for Copilot in priority order.",
      inputSchema: { type: "object", properties: {}, additionalProperties: false },
      handler: ({ state }) => ({
        count: state.issues.length,
        summary: state.issues.length
          ? state.issues.map((issue) =>
            `- #${issue.number} [${issue.priority}] ${issue.title} (${issue.state})`).join("\n")
          : "No issues loaded.",
      }),
    },
  };
}

export const canvasConfig = {
  id: "issue-triage-canvas",
  displayName: "Issue Triage",
  description: "Prioritize open repository issues and apply assignment or status updates.",
  assetsDir: fileURLToPath(new URL("./web/", import.meta.url)),
  inputSchema: {
    type: "object",
    properties: {
      repository: {
        type: "string",
        pattern: "^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$",
        description: "GitHub owner/repository to triage.",
      },
    },
    additionalProperties: false,
  },
  resolveDomainId: (input) => input?.repository ?? DEFAULT_REPOSITORY,
  createInitialState: (_ctx, input) => ({
    repository: input?.repository ?? DEFAULT_REPOSITORY,
    issues: [],
    error: null,
    lastRefresh: null,
    autoRefreshSec: 60,
  }),
  loadState: async (domainId) => fileFor(domainId).load(null),
  saveState: async (domainId, state) => fileFor(domainId).save(state),
  statusLine: (_ctx, state) => `${state.issues.length} issues · ${state.repository}`,
  actions: createActions(),
};
