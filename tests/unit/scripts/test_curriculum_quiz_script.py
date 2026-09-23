"""Run the published page's quiz script in Node, against a stub DOM.

The browser quiz is the only assessment a reader without a clone can take,
and it lives in a JavaScript string inside a Python f-string, where a typo
survives every Python test. This drives the real script: answer a tiered
bank, then check the completion screen applies the same pass rule as
src/education/tutor.py.
"""

import json
import re
import shutil
import subprocess

import pytest

from scripts.build_learning_curriculum import DEFAULT_OUTPUT

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="needs node")

STUB = """
const el = () => ({innerHTML: '', disabled: false, onclick: null,
  querySelector: () => el(), querySelectorAll: () => [], classList: {add(){}},
  insertAdjacentHTML(){}, showModal(){}, close(){}, closest: () => null});
const quizBody = el();
globalThis.location = {hash: ''};
globalThis.addEventListener = () => {};
globalThis.document = {
  querySelector: sel => sel === '#quiz-body' ? quizBody : el(),
  querySelectorAll: () => [], addEventListener: () => {},
  getElementById: () => null};
globalThis.__body = quizBody;
"""

HARNESS = """
questions = %s; position = 0; correct = 0; tierScore = {};
for (const [i, pick] of %s.entries()) { position = i; answer(pick, questions[i]); }
const feedback = __body.innerHTML;
position = questions.length; render();
console.log(JSON.stringify({done: __body.innerHTML}));
"""


def run(bank, picks):
    page = DEFAULT_OUTPUT.read_text(encoding="utf-8")
    script = re.findall(r"<script>(.*?)</script>", page, re.DOTALL)[-1]
    program = STUB + script + HARNESS % (json.dumps(bank), json.dumps(picks))
    out = subprocess.run(
        ["node", "-e", program], capture_output=True, text=True, check=True
    ).stdout
    return json.loads(out.strip().splitlines()[-1])["done"]


def bank(tiers):
    return [
        {
            "id": f"q{i}",
            "question": "?",
            "choices": ["a", "b"],
            "correct_index": 0,
            "citation": "README.md",
            "tier": tier,
            "explanation": "why",
        }
        for i, tier in enumerate(tiers)
    ]


def test_a_weak_tier_fails_the_browser_quiz_despite_a_high_overall_score():
    tiers = ["implementation"] * 16 + ["concept"] * 4
    picks = [0] * 16 + [0, 0, 1, 1]  # 90% overall, 50% concept
    done = run(bank(tiers), picks)
    assert "18 / 20" in done and "does not yet meet" in done
    assert "concept: 2 / 4" in done


def test_meeting_every_threshold_passes_the_browser_quiz():
    done = run(bank(["implementation"] * 10), [0] * 10)
    assert "meets the pass rule" in done and "does not" not in done
