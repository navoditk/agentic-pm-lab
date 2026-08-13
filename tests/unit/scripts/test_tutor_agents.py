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
)


def test_tutor_agents_have_independent_examples_and_read_only_contract() -> None:
    for name in TUTORS:
        content = (ROOT / ".github" / "agents" / f"{name}.agent.md").read_text()
        assert "tools: [read, search]" in content
        assert "## Independent practice examples" in content
        examples, negatives = content.split("Negative examples:", maxsplit=1)
        assert sum(f"{index}." in examples for index in range(1, 6)) == 5
        assert sum(f"{index}." in negatives for index in range(1, 4)) == 3
        assert "Do not edit files" in content
