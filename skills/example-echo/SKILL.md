---
name: example-echo
description: A trivial skill that echoes its input back, unchanged. Exists only to prove the Agent Skills loading mechanism works before any real skill depends on it.
license: MIT
covers: []
last_verified_commit: 48e5fe2
---

# example-echo

Given a piece of text, respond with the same text, verbatim, prefixed with `echo: `.

This skill has no tools, no side effects, and covers no source files — it exists purely so that the first day of the project has a working example of the Agent Skills package shape (`SKILL.md` + `contract.yaml` + `examples/` + `tests/`) before any skill with real behavior is written.
