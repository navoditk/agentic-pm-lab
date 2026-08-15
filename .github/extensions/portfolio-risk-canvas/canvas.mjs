import { fileURLToPath } from "node:url";
import { userStore } from "./canvas-kit/storage.mjs";

const EXT_NAME = "portfolio-risk-canvas";

const ROLE_BY_IDENTITY = {
  PM_USER: "pm",
  RISK_USER: "risk",
  ADMIN_USER: "admin",
};

const PORTFOLIO_ACCESS = {
  PM_USER: ["PORT_A"],
  RISK_USER: ["PORT_A", "PORT_B"],
  ADMIN_USER: ["PORT_A", "PORT_B"],
};

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

const PM_QUESTIONS = {
  risk_snapshot: {
    id: "risk_snapshot",
    prompt: "What are the largest current portfolio risks?",
    route: "Quant/Risk specialist -> exposure and risk tools",
    evidence: "mock holdings + public price inputs",
  },
  rates_stress: {
    id: "rates_stress",
    prompt: "What happens if rates rise by 50 bps?",
    route: "Macro specialist -> scenario tool -> risk summary",
    evidence: "public curve inputs + mock scenario fixture",
  },
  portfolio_access: {
    id: "portfolio_access",
    prompt: "Can I inspect PORT_B from this session?",
    route: "Identity -> portfolio entitlement -> deny or allow",
    evidence: "local role and portfolio policy fixtures",
  },
};

function fileFor(domainId) {
  const safe = String(domainId).replace(/[^A-Za-z0-9._-]/g, "_") || "default";
  return userStore(EXT_NAME, `${safe}.json`);
}

function canAccessPortfolio(identity, portfolio) {
  return (PORTFOLIO_ACCESS[identity] ?? []).includes(portfolio);
}

function seedState() {
  return {
    identity: "PM_USER",
    role: ROLE_BY_IDENTITY.PM_USER,
    portfolio: "PORT_A",
    portfolioLabel: "Core Portfolio",
    view: "overview",
    currentMetrics: {
      totalMarketValue: 1250000,
      volatility: 0.123,
      maxDrawdown: -0.074,
      largestPositionWeight: 0.31,
      concentrationHhi: 0.217,
    },
    scenarioId: null,
    scenarioResult: null,
    holdings: [
      { id: "BOND_10Y", name: "10Y duration sleeve", weight: 0.31, provenance: "real public curve inputs + mock holdings" },
      { id: "CREDIT_A", name: "Credit carry book", weight: 0.27, provenance: "mock security master" },
      { id: "MBS_A", name: "Mortgage convexity book", weight: 0.22, provenance: "mock security master" },
      { id: "EQUITY_HEDGE", name: "Equity hedge overlay", weight: 0.20, provenance: "public ETF price inputs" },
    ],
    provenance: [
      { id: "macro", label: "Rates / macro curve", kind: "real", note: "Public FRED / Treasury data already in the repo." },
      { id: "portfolio", label: "Holdings and classifications", kind: "mock", note: "Security master remains mock until a real fundamentals source exists." },
      { id: "scenario", label: "Scenario impacts", kind: "mock", note: "Scenario fixtures are mock; the governed MCP contract is documented separately." },
    ],
    guardrails: [
      { id: "port-a", title: "PORT_A access", result: "allowed", detail: "PM_USER can inspect the primary portfolio." },
      { id: "port-b", title: "PORT_B access", result: "blocked", detail: "PM_USER cannot switch to PORT_B." },
      { id: "backtest", title: "Backtest approval", result: "pending", detail: "ADMIN_USER must approve the paused run." },
    ],
    trace: {
      id: "root",
      label: "portfolio_manager.invoke",
      status: "completed",
      detail: "Portfolio Manager gathered macro and risk context before preparing the canvas summary.",
      children: [
        {
          id: "macro",
          label: "Macro specialist",
          status: "completed",
          detail: "Rates and curve context reviewed from public data.",
          children: [],
        },
        {
          id: "quant",
          label: "Quant/Risk specialist",
          status: "completed",
          detail: "Risk, volatility, and concentration reviewed against the mock portfolio.",
          children: [],
        },
      ],
    },
    approvals: [
      {
        id: "run_backtest",
        title: "Paused backtest",
        status: "waiting",
        requiredRole: "admin",
        note: "Day 7 interrupt_on gate; only ADMIN_USER may approve it.",
        approvedAt: null,
      },
    ],
    evaluations: [
      {
        id: "day6-full",
        label: "Day 6 full evaluation",
        score: "86.7% tool selection",
        note: "LangSmith baseline with policy stubbed at the time.",
      },
      {
        id: "day7-policy",
        label: "Day 7 policy experiment",
        score: "100% policy compliance",
        note: "Deterministic policy cases added without lowering behavioral floors.",
      },
    ],
    comparison: {
      singleAgent: {
        label: "Day 4 single-agent comparison",
        latencySeconds: 129.696,
        note: "Local Qwen3 4B volatility run.",
      },
      multiAgent: {
        label: "Day 5 multi-agent comparison",
        latencySeconds: 18.825,
        note: "Local multi-agent run returned empty without delegating.",
      },
    },
    selectedScenario: "rates_50bps",
    selectedTraceNode: "root",
    integration: {
      boundary: "governed-mcp",
      tool: "risk_metrics",
      status: "contract-backed",
      note: "Canvas capability tests use the same identity and portfolio boundary as the MCP adapter.",
    },
    lastAction: "Canvas seeded with portfolio/risk summary.",
    questionRun: null,
    updatedAt: new Date().toISOString(),
  };
}

function findScenario(id) {
  return SCENARIOS[id] ?? null;
}

function updateNode(node, nodeId, updater) {
  if (node.id === nodeId) return updater(node);
  const children = node.children.map((child) => updateNode(child, nodeId, updater));
  if (children.every((child, index) => child === node.children[index])) return node;
  return { ...node, children };
}

function getSelectedScenario(state) {
  return state.selectedScenario ? findScenario(state.selectedScenario) : null;
}

function recordScenario(state, scenario) {
  const impact = scenario.impact;
  return {
    ...state,
    scenarioId: scenario.id,
    selectedScenario: scenario.id,
    scenarioResult: {
      id: scenario.id,
      label: scenario.label,
      type: scenario.type,
      impact,
      note: scenario.note,
      comparedAgainst: {
        volatility: state.currentMetrics.volatility,
        maxDrawdown: state.currentMetrics.maxDrawdown,
      },
      stressed: {
        volatility: state.currentMetrics.volatility + impact.volatility,
        maxDrawdown: state.currentMetrics.maxDrawdown + impact.drawdown,
      },
    },
    lastAction: `Applied scenario: ${scenario.label}`,
    updatedAt: new Date().toISOString(),
  };
}

function answerQuestion(state, question) {
  if (question.id === "risk_snapshot") {
    const largest = [...state.holdings].sort((a, b) => b.weight - a.weight)[0];
    return {
      answer: `Largest concentration is ${largest.name} at ${Math.round(largest.weight * 100)}%; baseline volatility is ${Math.round(state.currentMetrics.volatility * 1000) / 10}% and maximum drawdown is ${Math.round(state.currentMetrics.maxDrawdown * 1000) / 10}%.`,
      finding: "Concentration and drawdown are the first review points.",
    };
  }
  if (question.id === "rates_stress") {
    const scenario = SCENARIOS.rates_50bps;
    const stressedVolatility = state.currentMetrics.volatility + scenario.impact.volatility;
    const stressedDrawdown = state.currentMetrics.maxDrawdown + scenario.impact.drawdown;
    return {
      answer: `Under the +50 bps fixture, volatility moves to ${Math.round(stressedVolatility * 1000) / 10}% and maximum drawdown moves to ${Math.round(stressedDrawdown * 1000) / 10}%.`,
      finding: scenario.note,
      scenario,
    };
  }
  const allowed = canAccessPortfolio(state.identity, "PORT_B");
  return {
    answer: allowed ? `${state.identity} is entitled to inspect PORT_B.` : `${state.identity} is not entitled to inspect PORT_B; the request is denied before tool access.`,
    finding: allowed ? "Entitlement check passed." : "Default-deny entitlement check blocked the request.",
  };
}

export const canvasConfig = {
  id: "portfolio-risk-canvas",
  displayName: "Portfolio Risk",
  description: "Inspect portfolio risk, scenario shocks, traces, provenance, and approvals.",
  assetsDir: fileURLToPath(new URL("./web/", import.meta.url)),
  inputSchema: {
    type: "object",
    properties: {
      domain: {
        type: "string",
        description: "Logical workspace to open. Omit for the default portfolio-risk board.",
      },
    },
    additionalProperties: false,
  },
  resolveDomainId: (input) => (input?.domain ? String(input.domain) : "default"),
  createInitialState: seedState,
  loadState: async (domainId) => fileFor(domainId).load(null),
  saveState: async (domainId, state) => fileFor(domainId).save(state),
  statusLine: (_ctx, state) => `${state.identity} · ${state.portfolio} · ${state.view}`,

  actions: {
    ask_pm_question: {
      description: "Run one bounded PM learning question through the local governed workflow.",
      inputSchema: {
        type: "object",
        properties: {
          questionId: { type: "string", enum: Object.keys(PM_QUESTIONS) },
        },
        required: ["questionId"],
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        const question = PM_QUESTIONS[input.questionId];
        if (!question) throw new Error(`Unknown PM question ${input.questionId}`);
        const result = answerQuestion(state, question);
        const next = result.scenario ? recordScenario(state, result.scenario) : state;
        const questionRun = {
          id: question.id,
          prompt: question.prompt,
          answer: result.answer,
          finding: result.finding,
          route: question.route,
          evidence: question.evidence,
          status: "completed",
          traceId: `canvas-${question.id}`,
          completedAt: new Date().toISOString(),
        };
        set({
          ...next,
          questionRun,
          lastAction: `Answered PM question: ${question.prompt}`,
          updatedAt: new Date().toISOString(),
        });
        return questionRun;
      },
    },

    set_identity: {
      description: "Switch the active identity and role in the canvas.",
      inputSchema: {
        type: "object",
        properties: {
          identity: { type: "string", enum: ["PM_USER", "RISK_USER", "ADMIN_USER"] },
        },
        required: ["identity"],
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        const identity = input.identity;
        set((current) => ({
          ...current,
          identity,
          role: ROLE_BY_IDENTITY[identity],
          lastAction: `Identity set to ${identity}`,
          updatedAt: new Date().toISOString(),
        }));
        return { identity, role: ROLE_BY_IDENTITY[identity] };
      },
    },

    select_portfolio: {
      description: "Switch the active portfolio view.",
      inputSchema: {
        type: "object",
        properties: {
          portfolio: { type: "string", enum: ["PORT_A", "PORT_B"] },
        },
        required: ["portfolio"],
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        if (!canAccessPortfolio(state.identity, input.portfolio)) {
          throw new Error(`${state.identity} cannot access ${input.portfolio}`);
        }
        const portfolioLabel = input.portfolio === "PORT_A" ? "Core Portfolio" : "Satellite Portfolio";
        set((current) => ({
          ...current,
          portfolio: input.portfolio,
          portfolioLabel,
          guardrails: current.guardrails.map((item) =>
            item.id === "port-b" && input.portfolio === "PORT_B"
              ? { ...item, result: "allowed", detail: `${current.identity} can inspect ${input.portfolio}.` }
              : item
          ),
          lastAction: `Portfolio switched to ${input.portfolio}`,
          updatedAt: new Date().toISOString(),
        }));
        return { portfolio: input.portfolio };
      },
    },

    run_scenario: {
      description: "Apply a precomputed scenario shock to the current portfolio view.",
      inputSchema: {
        type: "object",
        properties: {
          scenarioId: { type: "string", enum: Object.keys(SCENARIOS) },
        },
        required: ["scenarioId"],
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        const scenario = findScenario(input.scenarioId);
        if (!scenario) throw new Error(`Unknown scenario ${input.scenarioId}`);
        set((current) => recordScenario(current, scenario));
        return {
          scenarioId: scenario.id,
          adapter: "governed-mcp-contract",
          stressed: {
            volatility: state.currentMetrics.volatility + scenario.impact.volatility,
            maxDrawdown: state.currentMetrics.maxDrawdown + scenario.impact.drawdown,
          },
        };
      },
    },

    inspect_trace: {
      description: "Focus a node in the local trace tree.",
      inputSchema: {
        type: "object",
        properties: {
          nodeId: { type: "string" },
        },
        required: ["nodeId"],
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        const nodeId = input.nodeId;
        set((current) => ({
          ...current,
          trace: updateNode(current.trace, nodeId, (node) => ({
            ...node,
            status: "focused",
            detail: `${node.detail} (focused in the canvas)`,
          })),
          selectedTraceNode: nodeId,
          lastAction: `Focused trace node ${nodeId}`,
          updatedAt: new Date().toISOString(),
        }));
        return { nodeId };
      },
    },

    approve_run: {
      description: "Approve the paused backtest run.",
      inputSchema: {
        type: "object",
        properties: {
          approvalId: { type: "string", default: "run_backtest" },
        },
        additionalProperties: false,
      },
      handler: ({ state, set, input }) => {
        if (state.identity !== "ADMIN_USER") {
          throw new Error("Only ADMIN_USER can approve the paused backtest");
        }
        const approvalId = input.approvalId || "run_backtest";
        set((current) => ({
          ...current,
          approvals: current.approvals.map((approval) =>
            approval.id !== approvalId
              ? approval
              : {
                  ...approval,
                  status: "approved",
                  approvedAt: new Date().toISOString(),
                }
          ),
          guardrails: current.guardrails.map((item) =>
            item.id === "backtest"
              ? { ...item, result: "allowed", detail: "ADMIN_USER approved the paused backtest." }
              : item
          ),
          lastAction: `Approved ${approvalId}`,
          updatedAt: new Date().toISOString(),
        }));
        return { approvalId, status: "approved" };
      },
    },

    set_view: {
      description: "Change which panel is emphasized in the canvas.",
      inputSchema: {
        type: "object",
        properties: {
          view: {
            type: "string",
            enum: ["overview", "scenarios", "traces", "provenance", "approvals", "evaluation"],
          },
        },
        required: ["view"],
        additionalProperties: false,
      },
      handler: ({ set, input }) => {
        set((current) => ({
          ...current,
          view: input.view,
          lastAction: `View changed to ${input.view}`,
          updatedAt: new Date().toISOString(),
        }));
        return { view: input.view };
      },
    },
  },
};
