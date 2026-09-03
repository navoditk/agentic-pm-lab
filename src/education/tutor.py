"""Tool-agnostic access to the 14 domain tutor personas: browse a topic's
scope without an IDE agent surface, take its multiple-choice quiz, and record
the attempt for the comprehension tracker in scripts/check_learner_progress.py.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
LEARNER_PROGRESS_DIR = REPO_ROOT / "data" / "learner_progress"

# Same 13 names as tests/unit/scripts/test_tutor_agents.py's TUTORS tuple, plus
# ficc-tutor-agent (kept at its documented "user-scoped" docs/agent-templates/
# location rather than .github/agents/ -- see PROGRESS.md's Day 2 entry) --
# this catalog is the canonical map from topic id to where its content, its
# reference-anchor into REFERENCES.md, its deep-dive companion doc, and its
# quiz all live.
REFERENCES_FILE = "docs/reference/REFERENCES.md"
TOPIC_CATALOG: dict[str, dict[str, str]] = {
    "portfolio-construction-tutor": {
        "label": "Portfolio construction",
        "agent_file": ".github/agents/portfolio-construction-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/portfolio-construction-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#portfolio-optimization-and-portfolio-construction",
        "deep_dive": "docs/learning/tutors/portfolio-construction-tutor.md",
    },
    "agent-architecture-tutor": {
        "label": "Agent architecture",
        "agent_file": ".github/agents/agent-architecture-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/agent-architecture-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#agent-harnesses-skills-prompts-and-custom-agents",
        "deep_dive": "docs/learning/tutors/agent-architecture-tutor.md",
    },
    "langgraph-deep-agents-tutor": {
        "label": "LangGraph and Deep Agents",
        "agent_file": ".github/agents/langgraph-deep-agents-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/langgraph-deep-agents-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#langgraph--langgraph-deep-agents",
        "deep_dive": "docs/learning/tutors/langgraph-deep-agents-tutor.md",
    },
    "aws-agentcore-tutor": {
        "label": "AWS Bedrock AgentCore",
        "agent_file": ".github/agents/aws-agentcore-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/aws-agentcore-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#aws-bedrock--agentcore",
        "deep_dive": "docs/learning/tutors/aws-agentcore-tutor.md",
    },
    "data-provenance-research-tutor": {
        "label": "Data provenance and research quality",
        "agent_file": ".github/agents/data-provenance-research-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/data-provenance-research-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#data-engineering-provenance-and-research-correctness",
        "deep_dive": "docs/learning/tutors/data-provenance-research-tutor.md",
    },
    "evaluation-agentops-tutor": {
        "label": "Evaluations and AgentOps",
        "agent_file": ".github/agents/evaluation-agentops-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/evaluation-agentops-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#langsmith-tracing-datasets-experiments-evaluation",
        "deep_dive": "docs/learning/tutors/evaluation-agentops-tutor.md",
    },
    "opentelemetry-tutor": {
        "label": "OpenTelemetry",
        "agent_file": ".github/agents/opentelemetry-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/opentelemetry-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#opentelemetry-python",
        "deep_dive": "docs/learning/tutors/opentelemetry-tutor.md",
    },
    "investment-committee-tutor": {
        "label": "Investment committee challenge",
        "agent_file": ".github/agents/investment-committee-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/investment-committee-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#tutor-agent-study-map",
        "deep_dive": "docs/learning/tutors/investment-committee-tutor.md",
    },
    "copilot-canvas-mcp-tutor": {
        "label": "Copilot Canvas and MCP",
        "agent_file": ".github/agents/copilot-canvas-mcp-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/copilot-canvas-mcp-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#github-copilot-app-canvas-prompts-skills-custom-agents",
        "deep_dive": "docs/learning/tutors/copilot-canvas-mcp-tutor.md",
    },
    "agent-development-lifecycle-tutor": {
        "label": "Agent development lifecycle",
        "agent_file": ".github/agents/agent-development-lifecycle-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/agent-development-lifecycle-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#agent-harnesses-skills-prompts-and-custom-agents",
        "deep_dive": "docs/learning/tutors/agent-development-lifecycle-tutor.md",
    },
    "governance-delivery-tutor": {
        "label": "Governance and delivery",
        "agent_file": ".github/agents/governance-delivery-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/governance-delivery-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#security-authnauthz-policy-as-code-prompt-injection",
        "deep_dive": "docs/learning/tutors/governance-delivery-tutor.md",
    },
    "document-to-skill-tutor": {
        "label": "Document-to-skill pipeline",
        "agent_file": ".github/agents/document-to-skill-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/document-to-skill-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#document-ingestion-and-document-to-skill-design",
        "deep_dive": "docs/learning/tutors/document-to-skill-tutor.md",
    },
    "investment-data-tutor": {
        "label": "Public investment data",
        "agent_file": ".github/agents/investment-data-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/investment-data-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#public-data-terminology-and-decision-use-primers",
        "deep_dive": "docs/learning/tutors/investment-data-tutor.md",
    },
    "ficc-tutor-agent": {
        "label": "FICC fundamentals",
        "agent_file": "docs/agent-templates/ficc-tutor-agent.agent.md",
        "quiz_file": "evals/tutor_quizzes/ficc-tutor-agent.jsonl",
        "reference": f"{REFERENCES_FILE}#ficc--fixed-income-fundamentals",
        "deep_dive": "docs/learning/tutors/ficc-tutor-agent.md",
    },
}

SCOPE_HEADER = "## Independent practice examples"


def list_topics() -> list[dict[str, str]]:
    """Return a compact catalog suitable for a CLI or UI selector."""
    return [
        {"id": topic_id, "label": record["label"]}
        for topic_id, record in TOPIC_CATALOG.items()
    ]


def teach_topic(topic_id: str) -> dict[str, Any]:
    """Return one tutor's scope description, sourced from its own .agent.md file."""
    try:
        record = TOPIC_CATALOG[topic_id]
    except KeyError as exc:
        available = ", ".join(sorted(TOPIC_CATALOG))
        raise ValueError(
            f"unknown topic {topic_id}; choose one of: {available}"
        ) from exc
    agent_path = REPO_ROOT / record["agent_file"]
    content = agent_path.read_text()
    _frontmatter, _, body = content.partition("---\n")
    _frontmatter2, _, body = body.partition("---")
    scope_text = body.split(SCOPE_HEADER, maxsplit=1)[0].strip()
    return {
        "topic": topic_id,
        "label": record["label"],
        "scope_text": scope_text,
        "agent_file": record["agent_file"],
        "reference": record["reference"],
        "deep_dive": record["deep_dive"],
        "read_only": True,
        "investment_advice": False,
    }


def load_quiz(topic_id: str) -> list[dict[str, Any]]:
    """Read one topic's multiple-choice quiz bank."""
    record = TOPIC_CATALOG[topic_id]
    path = REPO_ROOT / record["quiz_file"]
    questions = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            questions.append(json.loads(line))
    return questions


def grade_answers(topic_id: str, answers: list[int]) -> dict[str, Any]:
    """Score a completed attempt. Pure function -- no I/O beyond reading the quiz bank."""
    questions = load_quiz(topic_id)
    if len(answers) != len(questions):
        raise ValueError(
            f"expected {len(questions)} answers for {topic_id}, got {len(answers)}"
        )
    results = []
    score = 0
    for question, answer in zip(questions, answers, strict=True):
        correct = answer == question["correct_index"]
        score += int(correct)
        results.append(
            {
                "id": question["id"],
                "correct": correct,
                "correct_index": question["correct_index"],
                "your_index": answer,
                "citation": question["citation"],
            }
        )
    return {
        "topic": topic_id,
        "score": score,
        "total": len(questions),
        "results": results,
    }


def record_attempt(
    topic_id: str,
    score: int,
    total: int,
    *,
    log_dir: Path | None = None,
) -> Path:
    """Append one attempt record to data/learner_progress/<topic_id>.jsonl."""
    log_dir = log_dir or LEARNER_PROGRESS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{topic_id}.jsonl"
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "topic": topic_id,
        "score": score,
        "total": total,
    }
    with log_path.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return log_path
