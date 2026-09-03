from pathlib import Path

ROOT = Path(__file__).parents[3]
TUTORS = (
    "portfolio-construction-tutor",
    "agent-architecture-tutor",
    "langgraph-deep-agents-tutor",
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

# ficc-tutor-agent is deliberately "user-scoped" (PROGRESS.md's Day 2 entry) and
# lives under docs/agent-templates/ rather than .github/agents/ with the other
# 13, but it's held to the exact same structural contract.
TUTOR_PATHS = {
    name: ROOT / ".github" / "agents" / f"{name}.agent.md" for name in TUTORS
}
TUTOR_PATHS["ficc-tutor-agent"] = (
    ROOT / "docs" / "agent-templates" / "ficc-tutor-agent.agent.md"
)


def test_tutor_agents_have_independent_examples_and_read_only_contract() -> None:
    for name, path in TUTOR_PATHS.items():
        content = path.read_text()
        assert "tools: [read, search]" in content, name
        assert "## Independent practice examples" in content, name
        examples, negatives = content.split("Negative examples:", maxsplit=1)
        assert sum(f"{index}." in examples for index in range(1, 6)) == 5, name
        assert sum(f"{index}." in negatives for index in range(1, 4)) == 3, name
        assert "Do not edit files" in content, name
