"""Validate every tutor quiz bank: answer keys, citations, tiers, and balance.

A quiz is only evidence of understanding if it cannot be passed without it.
Two defects this checker exists for were both present at once: 317 of 366
correct answers sat in position B, so always picking B scored 87%, and one
question appeared word for word in two banks. Neither was caught, because
nothing looked at the banks as a whole.

Rules, per docs/learning/FOUNDATIONS_MASTERY_PLAN.md section 4:

- ids are unique across all banks, and question text is not repeated;
- 3-5 distinct choices, and `correct_index` is one of them;
- no answer position holds more than MAX_POSITION_SHARE of a bank's keys;
- `citation` and `verified_by` name files that exist, and a `verified_by`
  test function exists in its file;
- `tier` is concept, implementation, or transfer; `concept` is listed in
  docs/learning/concepts.yaml; concept questions cite a registered source
  and carry an explanation;
- a bank is *tiered* once any question declares a tier, and then every
  question must declare one and the mix must be near 40/40/20.

    uv run python scripts/check_quiz_banks.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MAX_POSITION_SHARE = 0.4
TIER_TARGETS = {"concept": 0.4, "implementation": 0.4, "transfer": 0.2}
TIER_TOLERANCE = 0.1
EXPLAINED_TIERS = {"concept", "transfer"}


def load_concepts(path: Path = ROOT / "docs/learning/concepts.yaml") -> set[str]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {
        f"{domain}.{concept}"
        for domain, body in data["domains"].items()
        for concept in body["concepts"]
    }


def load_source_ids(
    path: Path = ROOT / "docs/reference/source-registry.yaml",
) -> set[str]:
    return {
        source["id"]
        for source in yaml.safe_load(path.read_text(encoding="utf-8"))["sources"]
    }


def _repo_path_exists(reference: str) -> bool:
    path = reference.split("::", 1)[0].split("#", 1)[0]
    return bool(path) and (ROOT / path).exists()


def _test_exists(reference: str) -> bool:
    path, _, name = reference.partition("::")
    if not name or not (ROOT / path).is_file():
        return False
    return f"def {name.split('[', 1)[0]}(" in (ROOT / path).read_text(encoding="utf-8")


def check_question(
    question: dict, topic: str, concepts: set[str], sources: set[str]
) -> list[str]:
    qid = question.get("id", "<no id>")
    errors = []
    if question.get("topic") != topic:
        errors.append(f"{qid}: topic {question.get('topic')!r} is not {topic!r}")
    choices = question.get("choices", [])
    if not 3 <= len(choices) <= 5 or len(set(choices)) != len(choices):
        errors.append(f"{qid}: needs 3-5 distinct choices")
    index = question.get("correct_index")
    if not isinstance(index, int) or not 0 <= index < len(choices):
        errors.append(f"{qid}: correct_index {index!r} is not a choice")
    if not _repo_path_exists(question.get("citation", "")):
        errors.append(f"{qid}: citation {question.get('citation')!r} does not exist")
    tier = question.get("tier")
    if tier is not None and tier not in TIER_TARGETS:
        errors.append(f"{qid}: tier {tier!r} is not one of {sorted(TIER_TARGETS)}")
    concept = question.get("concept")
    if concept is not None and concept not in concepts:
        errors.append(f"{qid}: concept {concept!r} is not in concepts.yaml")
    if tier == "concept":
        if question.get("source_id") not in sources:
            errors.append(
                f"{qid}: a concept question must cite a source registered in "
                "source-registry.yaml via source_id"
            )
        if concept is None:
            errors.append(f"{qid}: a concept question must name its concept")
    elif "source_id" in question and question["source_id"] not in sources:
        errors.append(f"{qid}: source_id {question['source_id']!r} is not registered")
    if tier in EXPLAINED_TIERS and not question.get("explanation"):
        errors.append(f"{qid}: {tier} questions need an explanation")
    verified_by = question.get("verified_by")
    if verified_by is not None and not _test_exists(verified_by):
        errors.append(f"{qid}: verified_by {verified_by!r} is not a test that exists")
    return errors


def check_bank(topic: str, questions: list[dict]) -> list[str]:
    errors = []
    positions = Counter(q.get("correct_index") for q in questions)
    top_position, top_count = positions.most_common(1)[0]
    if len(questions) >= 8 and top_count / len(questions) > MAX_POSITION_SHARE:
        errors.append(
            f"{topic}: {top_count} of {len(questions)} answers are position "
            f"{top_position}; a learner who always picks it would score "
            f"{top_count / len(questions):.0%}"
        )
    declared = [q for q in questions if "tier" in q]
    if declared and len(declared) != len(questions):
        errors.append(
            f"{topic}: a tiered bank must declare a tier on every question "
            f"({len(questions) - len(declared)} missing)"
        )
    elif declared:
        shares = Counter(q["tier"] for q in questions)
        for tier, target in TIER_TARGETS.items():
            share = shares[tier] / len(questions)
            if abs(share - target) > TIER_TOLERANCE:
                errors.append(
                    f"{topic}: {tier} questions are {share:.0%} of the bank; "
                    f"target is {target:.0%} ± {TIER_TOLERANCE:.0%}"
                )
    return errors


def check(banks: dict[str, list[dict]] | None = None) -> list[str]:
    from src.education.tutor import TOPIC_CATALOG

    if banks is None:
        banks = {
            topic: [
                json.loads(line)
                for line in (ROOT / record["quiz_file"]).read_text().splitlines()
                if line.strip()
            ]
            for topic, record in TOPIC_CATALOG.items()
        }
    concepts, sources = load_concepts(), load_source_ids()
    errors: list[str] = []
    ids: Counter[str] = Counter()
    texts: dict[str, str] = {}
    for topic, questions in banks.items():
        errors.extend(check_bank(topic, questions))
        for question in questions:
            errors.extend(check_question(question, topic, concepts, sources))
            ids[question.get("id", "")] += 1
            text = " ".join(question.get("question", "").lower().split())
            if text in texts:
                errors.append(
                    f"{question.get('id')}: repeats the question text of {texts[text]}"
                )
            texts.setdefault(text, question.get("id", ""))
    errors.extend(f"{qid}: id is used {n} times" for qid, n in ids.items() if n > 1)
    return errors


def main() -> int:
    errors = check()
    if errors:
        print("\n".join(f"ERROR: {error}" for error in errors))
        return 1
    print("Quiz banks are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
