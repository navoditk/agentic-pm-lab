@AGENTS.md

## Why this file exists

`AGENTS.md` is the canonical router for every coding agent used here — Claude
Code, GitHub Copilot, and OpenAI Codex CLI all read it, and it is the only
place project rules are maintained. This file exists solely to import it.

Claude Code reads `AGENTS.md` directly in most sessions, but **not** in all of
them. It falls back to reading `CLAUDE.md` alone when the session runs on
Amazon Bedrock or another third-party provider, when telemetry is disabled,
when `disableAllHooks` or `allowManagedHooksOnly` is set, on Claude Code
before v2.1.277, and on the first session after an upgrade. Several of those
are routine in a corporate environment.

Without this import, those sessions would silently load no project context at
all — the repo rules in `AGENTS.md` (public and mock data only, no network in
`tests/unit/`, Cedar as the sole authorization authority, contract and
freshness sync) would go unenforced with no warning that anything was missing.

An import rather than a symlink is deliberate: the Edit and Write tools refuse
to write through a symlink, and Git checks a committed symlink out as a plain
text file on Windows clones unless `core.symlinks` is set, which would leave
that clone with a one-line `CLAUDE.md` instead of the instructions.

Keep this file a pointer. Add Claude-specific instructions below the import if
they are ever needed; anything that applies to every agent belongs in
`AGENTS.md`.
