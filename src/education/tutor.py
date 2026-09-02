"""Tool-agnostic access to the 13 domain tutor personas: browse a topic's
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

# Same 13 names as tests/unit/scripts/test_tutor_agents.py's TUTORS tuple --
# that file is the canonical enforcement of tutor-file structure; this catalog
# is the canonical map from topic id to where its content and quiz live.
TOPIC_CATALOG: dict[str, dict[str, str]] = {
    "portfolio-construction-tutor": {
        "label": "Portfolio construction",
        "agent_file": ".github/agents/portfolio-construction-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/portfolio-construction-tutor.jsonl",
    },
    "agent-architecture-tutor": {
        "label": "Agent architecture",
        "agent_file": ".github/agents/agent-architecture-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/agent-architecture-tutor.jsonl",
    },
    "langgraph-deep-agents-tutor": {
        "label": "LangGraph and Deep Agents",
        "agent_file": ".github/agents/langgraph-deep-agents-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/langgraph-deep-agents-tutor.jsonl",
    },
    "aws-agentcore-tutor": {
        "label": "AWS Bedrock AgentCore",
        "agent_file": ".github/agents/aws-agentcore-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/aws-agentcore-tutor.jsonl",
    },
    "data-provenance-research-tutor": {
        "label": "Data provenance and research quality",
        "agent_file": ".github/agents/data-provenance-research-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/data-provenance-research-tutor.jsonl",
    },
    "evaluation-agentops-tutor": {
        "label": "Evaluations and AgentOps",
        "agent_file": ".github/agents/evaluation-agentops-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/evaluation-agentops-tutor.jsonl",
    },
    "opentelemetry-tutor": {
        "label": "OpenTelemetry",
        "agent_file": ".github/agents/opentelemetry-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/opentelemetry-tutor.jsonl",
    },
    "investment-committee-tutor": {
        "label": "Investment committee challenge",
        "agent_file": ".github/agents/investment-committee-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/investment-committee-tutor.jsonl",
    },
    "copilot-canvas-mcp-tutor": {
        "label": "Copilot Canvas and MCP",
        "agent_file": ".github/agents/copilot-canvas-mcp-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/copilot-canvas-mcp-tutor.jsonl",
    },
    "agent-development-lifecycle-tutor": {
        "label": "Agent development lifecycle",
        "agent_file": ".github/agents/agent-development-lifecycle-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/agent-development-lifecycle-tutor.jsonl",
    },
    "governance-delivery-tutor": {
        "label": "Governance and delivery",
        "agent_file": ".github/agents/governance-delivery-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/governance-delivery-tutor.jsonl",
    },
    "document-to-skill-tutor": {
        "label": "Document-to-skill pipeline",
        "agent_file": ".github/agents/document-to-skill-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/document-to-skill-tutor.jsonl",
    },
    "investment-data-tutor": {
        "label": "Public investment data",
        "agent_file": ".github/agents/investment-data-tutor.agent.md",
        "quiz_file": "evals/tutor_quizzes/investment-data-tutor.jsonl",
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
        "reference": "docs/reference/REFERENCES.md",
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
