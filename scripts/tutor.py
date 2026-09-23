"""Browse a tutor topic or take its quiz, without needing an IDE agent surface.

A quiz can be taken interactively (`--quiz`), or graded from answers already
given elsewhere (`--quiz --answers 1,0,2,...`). The second form exists for the
`agentexpert` mastery skill: a learner who answers every question in a Claude
Code, Copilot, or Codex conversation can record that attempt in the same
durable log as a terminal attempt, instead of losing it when the session ends.
"""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.check_learner_progress import PASS_THRESHOLD
from src.education.tutor import (
    TOPIC_CATALOG,
    course_outline,
    grade_answers,
    list_topics,
    load_quiz,
    record_attempt,
    teach_topic,
)


def _prompt_index(prompt: str, upper_bound: int) -> int:
    while True:
        raw = input(prompt).strip()
        if raw.isdigit() and 0 <= int(raw) < upper_bound:
            return int(raw)
        print(f"Enter a number from 0 to {upper_bound - 1}.")


def _run_quiz(topic: str) -> None:
    questions = load_quiz(topic)
    answers = []
    for position, question in enumerate(questions, start=1):
        print(f"\nQ{position}. {question['question']}")
        for choice_index, choice in enumerate(question["choices"]):
            print(f"  {choice_index}. {choice}")
        answers.append(
            _prompt_index("Your answer (number): ", len(question["choices"]))
        )
    result = grade_answers(topic, answers)
    record_attempt(topic, result["score"], result["total"])
    print(f"\nScore: {result['score']}/{result['total']}")
    for item in result["results"]:
        mark = "correct" if item["correct"] else "incorrect"
        print(f"  {item['id']}: {mark} (cited: {item['citation']})")


def parse_answers(raw: str, questions: list[dict]) -> list[int]:
    """Turn "1,0,2" into choice indices, rejecting anything the grader should not see.

    The whole bank is required: a five-question practice round scoring 5/5
    would otherwise record as a passed topic. Indices are checked against each
    question's own choices, because an out-of-range answer is a transcription
    error, not a wrong answer, and must not be recorded as one.
    """
    parts = [part.strip() for part in raw.split(",") if part.strip()]
    if len(parts) != len(questions):
        raise ValueError(
            f"expected {len(questions)} answers (the full bank), got {len(parts)}"
        )
    answers = []
    for position, (part, question) in enumerate(zip(parts, questions), start=1):
        if not part.isdigit() or int(part) >= len(question["choices"]):
            raise ValueError(
                f"answer {position} is {part!r}; expected 0 to "
                f"{len(question['choices']) - 1}"
            )
        answers.append(int(part))
    return answers


def record_answers(topic: str, raw: str) -> dict:
    """Grade a full set of answers given elsewhere, and record the attempt."""
    answers = parse_answers(raw, load_quiz(topic))
    result = grade_answers(topic, answers)
    log_path = record_attempt(topic, result["score"], result["total"])
    return {
        "topic": topic,
        "score": result["score"],
        "total": result["total"],
        "passed": result["score"] / result["total"] >= PASS_THRESHOLD,
        "recorded_to": str(
            log_path.relative_to(REPO_ROOT)
            if log_path.is_relative_to(REPO_ROOT)
            else log_path
        ),
        "missed": [
            {"id": item["id"], "citation": item["citation"]}
            for item in result["results"]
            if not item["correct"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic", nargs="?", help="topic id, or omit to list topics")
    parser.add_argument(
        "--quiz",
        action="store_true",
        help="take the topic's multiple-choice quiz interactively",
    )
    parser.add_argument(
        "--answers",
        metavar="LIST",
        help="with --quiz: grade and record comma-separated choice indices for "
        "every question, in bank order, instead of asking interactively",
    )
    parser.add_argument(
        "--course",
        action="store_true",
        help="show the complete course outline for the topic",
    )
    args = parser.parse_args()
    if args.topic is None:
        if args.quiz:
            parser.error("--quiz requires a topic id")
        print(json.dumps(list_topics(), indent=2, sort_keys=True))
        return
    if args.quiz and args.course:
        parser.error("--quiz and --course cannot be combined")
    if args.answers is not None and not args.quiz:
        parser.error("--answers requires --quiz")
    if args.quiz and args.topic not in TOPIC_CATALOG:
        parser.error(
            f"unknown topic {args.topic}; choose one of: {', '.join(TOPIC_CATALOG)}"
        )
    if args.answers is not None:
        try:
            print(json.dumps(record_answers(args.topic, args.answers), indent=2))
        except ValueError as error:
            parser.error(str(error))
        return
    if args.course:
        print(json.dumps(course_outline(args.topic), indent=2, sort_keys=True))
        return
    if args.quiz:
        _run_quiz(args.topic)
        return
    print(json.dumps(teach_topic(args.topic), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
