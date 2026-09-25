"""Tool-agnostic access to the tutor personas: browse a topic's
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
# quiz all live. Entries are listed in the recommended learning order -- the
# `step` field in docs/learning/tutor-courses.json -- and
# scripts/check_tutor_courses.py fails if the two disagree, so anything that
# iterates this dict (the CLI, the curriculum artifact, the UI) teaches in order.
REFERENCES_FILE = "docs/reference/REFERENCES.md"
TOPIC_CATALOG: dict[str, dict[str, str]] = {
    "agent-foundations-tutor": {
        "label": "Agent foundations",
        "agent_file": "agents/agent-foundations-tutor.md",
        "quiz_file": "evals/tutor_quizzes/agent-foundations-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#agent-foundations",
        "deep_dive": "docs/learning/tutors/agent-foundations-tutor.md",
    },
    "agent-architecture-tutor": {
        "label": "Agent architecture",
        "agent_file": "agents/agent-architecture-tutor.md",
        "quiz_file": "evals/tutor_quizzes/agent-architecture-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#agent-harnesses-skills-prompts-and-custom-agents",
        "deep_dive": "docs/learning/tutors/agent-architecture-tutor.md",
    },
    "langgraph-deep-agents-tutor": {
        "label": "LangGraph and Deep Agents",
        "agent_file": "agents/langgraph-deep-agents-tutor.md",
        "quiz_file": "evals/tutor_quizzes/langgraph-deep-agents-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#langgraph--langgraph-deep-agents",
        "deep_dive": "docs/learning/tutors/langgraph-deep-agents-tutor.md",
    },
    "mcp-tutor": {
        "label": "Model Context Protocol",
        "agent_file": "agents/mcp-tutor.md",
        "quiz_file": "evals/tutor_quizzes/mcp-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#model-context-protocol-mcp",
        "deep_dive": "docs/learning/tutors/mcp-tutor.md",
    },
    "opentelemetry-tutor": {
        "label": "OpenTelemetry",
        "agent_file": "agents/opentelemetry-tutor.md",
        "quiz_file": "evals/tutor_quizzes/opentelemetry-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#opentelemetry-python",
        "deep_dive": "docs/learning/tutors/opentelemetry-tutor.md",
    },
    "evaluation-agentops-tutor": {
        "label": "Evaluations and AgentOps",
        "agent_file": "agents/evaluation-agentops-tutor.md",
        "quiz_file": "evals/tutor_quizzes/evaluation-agentops-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#langsmith-tracing-datasets-experiments-evaluation",
        "deep_dive": "docs/learning/tutors/evaluation-agentops-tutor.md",
    },
    "governance-delivery-tutor": {
        "label": "Governance and delivery",
        "agent_file": "agents/governance-delivery-tutor.md",
        "quiz_file": "evals/tutor_quizzes/governance-delivery-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#security-authnauthz-policy-as-code-prompt-injection",
        "deep_dive": "docs/learning/tutors/governance-delivery-tutor.md",
    },
    "traceability-capstone-tutor": {
        "label": "Capstone: traceability end to end",
        "agent_file": "agents/traceability-capstone-tutor.md",
        "quiz_file": "evals/tutor_quizzes/traceability-capstone-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#traceability-capstone",
        "deep_dive": "docs/learning/tutors/traceability-capstone-tutor.md",
    },
    "ficc-tutor-agent": {
        "label": "FICC fundamentals",
        "agent_file": "agents/ficc-tutor-agent.md",
        "quiz_file": "evals/tutor_quizzes/ficc-tutor-agent.jsonl",
        "reference": f"{REFERENCES_FILE}#ficc--fixed-income-fundamentals",
        "deep_dive": "docs/learning/tutors/ficc-tutor-agent.md",
    },
    "portfolio-construction-tutor": {
        "label": "Portfolio construction",
        "agent_file": "agents/portfolio-construction-tutor.md",
        "quiz_file": "evals/tutor_quizzes/portfolio-construction-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#portfolio-optimization-and-portfolio-construction",
        "deep_dive": "docs/learning/tutors/portfolio-construction-tutor.md",
    },
    "data-provenance-research-tutor": {
        "label": "Data provenance and research quality",
        "agent_file": "agents/data-provenance-research-tutor.md",
        "quiz_file": "evals/tutor_quizzes/data-provenance-research-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#data-engineering-provenance-and-research-correctness",
        "deep_dive": "docs/learning/tutors/data-provenance-research-tutor.md",
    },
    "investment-data-tutor": {
        "label": "Public investment data",
        "agent_file": "agents/investment-data-tutor.md",
        "quiz_file": "evals/tutor_quizzes/investment-data-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#public-data-terminology-and-decision-use-primers",
        "deep_dive": "docs/learning/tutors/investment-data-tutor.md",
    },
    "investment-committee-tutor": {
        "label": "Investment committee challenge",
        "agent_file": "agents/investment-committee-tutor.md",
        "quiz_file": "evals/tutor_quizzes/investment-committee-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#tutor-agent-study-map",
        "deep_dive": "docs/learning/tutors/investment-committee-tutor.md",
    },
    "aws-bedrock-tutor": {
        "label": "AWS Bedrock",
        "agent_file": "agents/aws-bedrock-tutor.md",
        "quiz_file": "evals/tutor_quizzes/aws-bedrock-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#aws-bedrock--agentcore",
        "deep_dive": "docs/learning/tutors/aws-bedrock-tutor.md",
    },
    "aws-agentcore-tutor": {
        "label": "AWS Bedrock AgentCore",
        "agent_file": "agents/aws-agentcore-tutor.md",
        "quiz_file": "evals/tutor_quizzes/aws-agentcore-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#aws-bedrock--agentcore",
        "deep_dive": "docs/learning/tutors/aws-agentcore-tutor.md",
    },
    "copilot-canvas-mcp-tutor": {
        "label": "Copilot Canvas",
        "agent_file": "agents/copilot-canvas-mcp-tutor.md",
        "quiz_file": "evals/tutor_quizzes/copilot-canvas-mcp-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#github-copilot-app-canvas-prompts-skills-custom-agents",
        "deep_dive": "docs/learning/tutors/copilot-canvas-mcp-tutor.md",
    },
    "agent-development-lifecycle-tutor": {
        "label": "Agent development lifecycle",
        "agent_file": "agents/agent-development-lifecycle-tutor.md",
        "quiz_file": "evals/tutor_quizzes/agent-development-lifecycle-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#agent-harnesses-skills-prompts-and-custom-agents",
        "deep_dive": "docs/learning/tutors/agent-development-lifecycle-tutor.md",
    },
    "document-to-skill-tutor": {
        "label": "Document-to-skill pipeline",
        "agent_file": "agents/document-to-skill-tutor.md",
        "quiz_file": "evals/tutor_quizzes/document-to-skill-tutor.jsonl",
        "reference": f"{REFERENCES_FILE}#document-ingestion-and-document-to-skill-design",
        "deep_dive": "docs/learning/tutors/document-to-skill-tutor.md",
    },
}

COURSE_CATALOG: dict[str, dict[str, Any]] = json.loads(
    (REPO_ROOT / "docs/learning/tutor-courses.json").read_text()
)

SCOPE_HEADER = "## Independent practice examples"

# Question tiers (docs/learning/FOUNDATIONS_MASTERY_PLAN.md section 4). A
# question that declares no tier is an implementation question: every
# question written before tiers existed tests how this repository works.
TIERS = ("concept", "implementation", "transfer")
DEFAULT_TIER = "implementation"
# The pass rule, in one place for every surface: 80% overall, and 70% within
# each tier the bank contains, so a learner cannot pass on repo trivia alone.
OVERALL_PASS = 0.8
TIER_PASS = 0.7


def attempt_passes(
    score: int, total: int, tiers: dict[str, dict[str, int]] | None = None
) -> bool:
    """Apply the pass rule. Attempts recorded before tiers carry no `tiers`
    and are judged on the overall score alone."""
    if not total or score / total < OVERALL_PASS:
        return False
    return all(
        tier["score"] / tier["total"] >= TIER_PASS
        for tier in (tiers or {}).values()
        if tier["total"]
    )


def list_topics() -> list[dict[str, Any]]:
    """Return a compact catalog, in learning order, for a CLI or UI selector."""
    return [
        {
            "id": topic_id,
            "label": record["label"],
            "step": COURSE_CATALOG[topic_id]["step"],
            "stage": COURSE_CATALOG[topic_id]["stage"],
            "est_hours": COURSE_CATALOG[topic_id]["est_hours"],
            "required": COURSE_CATALOG[topic_id]["required"],
        }
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
        "course": COURSE_CATALOG[topic_id],
        "read_only": True,
        "investment_advice": False,
    }


def course_outline(topic_id: str) -> dict[str, Any]:
    """Return the complete offline course outline for one tutor topic."""
    if topic_id not in TOPIC_CATALOG:
        raise ValueError(f"unknown topic {topic_id}")
    return {
        "topic": topic_id,
        "label": TOPIC_CATALOG[topic_id]["label"],
        **COURSE_CATALOG[topic_id],
        "agent_file": TOPIC_CATALOG[topic_id]["agent_file"],
        "deep_dive": TOPIC_CATALOG[topic_id]["deep_dive"],
        "quiz_file": TOPIC_CATALOG[topic_id]["quiz_file"],
        "read_only": True,
        "offline": True,
    }


def load_quiz(topic_id: str) -> list[dict[str, Any]]:
    """Read one topic's multiple-choice quiz bank."""
    record = TOPIC_CATALOG[topic_id]
    path = REPO_ROOT / record["quiz_file"]
    questions = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            question = json.loads(line)
            question.setdefault("tier", DEFAULT_TIER)
            questions.append(question)
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
    tiers: dict[str, dict[str, int]] = {}
    missed_concepts: set[str] = set()
    for question, answer in zip(questions, answers, strict=True):
        correct = answer == question["correct_index"]
        score += int(correct)
        tier = tiers.setdefault(question["tier"], {"score": 0, "total": 0})
        tier["score"] += int(correct)
        tier["total"] += 1
        if not correct and question.get("concept"):
            missed_concepts.add(question["concept"])
        results.append(
            {
                "id": question["id"],
                "correct": correct,
                "correct_index": question["correct_index"],
                "your_index": answer,
                "citation": question["citation"],
                "tier": question["tier"],
                "explanation": question.get("explanation"),
            }
        )
    return {
        "topic": topic_id,
        "score": score,
        "total": len(questions),
        "tiers": tiers,
        "missed_concepts": sorted(missed_concepts),
        "passed": attempt_passes(score, len(questions), tiers),
        "results": results,
    }


def record_attempt(
    topic_id: str,
    score: int,
    total: int,
    *,
    tiers: dict[str, dict[str, int]] | None = None,
    missed_concepts: list[str] | None = None,
    log_dir: Path | None = None,
) -> Path:
    """Append one attempt record to data/learner_progress/<topic_id>.jsonl.

    `tiers` lets the pass rule be re-applied later; `missed_concepts` feeds
    spaced review. Both are optional so older callers keep working.
    """
    log_dir = log_dir or LEARNER_PROGRESS_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{topic_id}.jsonl"
    record = {
        "timestamp": datetime.now(UTC).isoformat(),
        "topic": topic_id,
        "score": score,
        "total": total,
    }
    if tiers is not None:
        record["tiers"] = tiers
    if missed_concepts:
        record["missed_concepts"] = missed_concepts
    with log_path.open("a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return log_path
