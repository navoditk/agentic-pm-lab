from pathlib import Path

ROOT = Path(__file__).parents[3]
TUTORS = (
    "agent-foundations-tutor",
    "portfolio-construction-tutor",
    "agent-architecture-tutor",
    "langgraph-deep-agents-tutor",
    "mcp-tutor",
    "aws-agentcore-tutor",
    "data-provenance-research-tutor",
    "evaluation-agentops-tutor",
    "opentelemetry-tutor",
    "investment-committee-tutor",
    "copilot-canvas-mcp-tutor",
    "agent-development-lifecycle-tutor",
    "governance-delivery-tutor",
    "document-to-skill-tutor",
    "investment-data-tutor",
)

# Canonical, CLI-neutral sources (agents/). The per-CLI files under
# .github/agents, .claude/agents, and .codex/agents are generated from these by
# scripts/build_agent_adapters.py. ficc-tutor-agent is deliberately
# user-scoped (install: user), so its adapters go to docs/agent-templates/.
TUTOR_PATHS = {name: ROOT / "agents" / f"{name}.md" for name in TUTORS}
TUTOR_PATHS["ficc-tutor-agent"] = ROOT / "agents" / "ficc-tutor-agent.md"


def test_tutor_agents_have_independent_examples_and_read_only_contract() -> None:
    for name, path in TUTOR_PATHS.items():
        content = path.read_text()
        assert "capabilities: [read, search]" in content, name
        assert "## Independent practice examples" in content, name
        examples, negatives = content.split("Negative examples:", maxsplit=1)
        assert sum(f"{index}." in examples for index in range(1, 6)) == 5, name
        assert sum(f"{index}." in negatives for index in range(1, 4)) == 3, name
        assert "Do not edit files" in content, name
