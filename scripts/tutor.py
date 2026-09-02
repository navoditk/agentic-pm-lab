"""Browse a tutor topic or take its quiz, without needing an IDE agent surface."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.education.tutor import (
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic", nargs="?", help="topic id, or omit to list topics")
    parser.add_argument(
        "--quiz",
        action="store_true",
        help="take the topic's multiple-choice quiz interactively",
    )
    args = parser.parse_args()
    if args.topic is None:
        if args.quiz:
            parser.error("--quiz requires a topic id")
        print(json.dumps(list_topics(), indent=2, sort_keys=True))
        return
    if args.quiz:
        _run_quiz(args.topic)
        return
    print(json.dumps(teach_topic(args.topic), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
