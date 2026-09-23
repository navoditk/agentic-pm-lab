# Agents and skills across CLIs

Every agent and skill in this repository works in Claude Code, GitHub Copilot,
and Codex. Each CLI discovers them in its own directory and format, so the
repository keeps **one CLI-neutral source** for each and generates the rest.

| You edit | Generated for | Where |
|---|---|---|
| `agents/<name>.md` | GitHub Copilot | `.github/agents/<name>.agent.md` |
| | Claude Code | `.claude/agents/<name>.md` |
| | Codex | `.codex/agents/<name>.toml` |
| `skills/<name>/SKILL.md` | Claude Code (and Copilot) | `.claude/skills/<name>/SKILL.md` |
| | Codex (and Copilot) | `.agents/skills/<name>/SKILL.md` |

Never edit a generated file; each one says so in its first lines. Change the
source, then run:

```bash
uv run python scripts/build_agent_adapters.py
```

CI and `uv run agentic-pm-lab check` fail if any generated file is stale,
missing, or has no source.

## Writing an agent source

```markdown
---
name: my-agent               # must match the file name
description: When to use it  # every CLI chooses agents by this
capabilities: [read, search] # or `all`; see the table below
---

The agent's instructions, in plain Markdown, written for any CLI.
```

Capabilities are neutral words, translated for each CLI:

| Capability | Copilot `tools` | Claude Code `tools` | Codex |
|---|---|---|---|
| `read` | `read` | `Read` | read-only sandbox |
| `search` | `search` | `Grep`, `Glob` | read-only sandbox |
| `execute` | `execute` | `Bash` | read-only sandbox |
| `web` | `web` | `WebFetch`, `WebSearch` | not configurable per agent; the adapter says so |
| `edit` | `edit` | `Edit`, `Write` | `workspace-write` sandbox |
| `all` | no restriction | no restriction | `workspace-write` sandbox |

Keep instructions CLI-neutral: name repository files and commands, not one
CLI's tool names or slash commands. An agent with `install: user` is
deliberately not active in the repository; its three adapters are written to
`docs/agent-templates/` for a learner to copy into their own user directory.

## Writing a skill

Skills follow the open [Agent Skills](https://agentskills.io) standard, which
all three CLIs support: a `SKILL.md` with `name` and `description`, plus any
references, contract, and tests in the same package under `skills/`. The
generated loaders copy the canonical `description`, because each CLI picks a
skill implicitly by matching it, and point to the canonical package.

## Where each format comes from

Checked against each CLI's documentation on 2026-09-23:

- **Claude Code** reads project subagents from `.claude/agents/` (Markdown with
  `name`, `description`, and an optional comma-separated `tools`) and project
  skills only from `.claude/skills/`.
- **GitHub Copilot** reads custom agents from `.github/agents/*.agent.md`
  (tool aliases `read`, `search`, `edit`, `execute`, `web`; Claude Code's names
  are accepted as compatible aliases) and project skills from `.github/skills`,
  `.claude/skills`, or `.agents/skills`.
- **Codex** reads custom agents from `.codex/agents/*.toml` (`name`,
  `description`, and `developer_instructions` required; `sandbox_mode`
  optional) and skills from `.agents/skills`.

**Known limitation.** Copilot reads both `.claude/skills` and `.agents/skills`,
so it may list each skill twice. Its documentation does not say whether it
de-duplicates by name. Two loaders are needed because Claude Code and Codex
each read only one of those directories.
