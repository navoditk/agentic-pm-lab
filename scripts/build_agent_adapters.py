"""Generate every CLI's agents and skill loaders from one CLI-neutral source.

Claude Code, GitHub Copilot, and Codex each discover agents and skills in
their own directories and formats. Maintaining a copy per CLI by hand is how
they drift, so the repository keeps one CLI-neutral source and generates the
rest:

    agents/<name>.md           ->  .github/agents/<name>.agent.md   Copilot
                                   .claude/agents/<name>.md         Claude Code
                                   .codex/agents/<name>.toml        Codex
    skills/<name>/SKILL.md     ->  .claude/skills/<name>/SKILL.md   Claude Code, Copilot
                                   .agents/skills/<name>/SKILL.md   Codex, Copilot

An agent marked `install: user` is deliberately not active in the repository;
its adapters are written to docs/agent-templates/ for a learner to install.

An agent's `capabilities` use neutral words (read, search, execute, web,
edit), mapped to each CLI below; `all` omits the restriction. Formats were
taken from each CLI's documentation (see docs/guides/CLI_AGENTS_AND_SKILLS.md).

    uv run python scripts/build_agent_adapters.py          # regenerate
    uv run python scripts/build_agent_adapters.py --check  # CI: fail if stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_SOURCES = ROOT / "agents"
SKILL_SOURCES = ROOT / "skills"
TEMPLATES = ROOT / "docs/agent-templates"
CAPABILITIES = ("read", "search", "execute", "web", "edit")

# Copilot's primary tool aliases; its docs list Claude Code's names as
# compatible aliases too, but the primary ones are unambiguous.
COPILOT_TOOLS = {c: c for c in CAPABILITIES}
CLAUDE_TOOLS = {
    "read": ["Read"],
    "search": ["Grep", "Glob"],
    "execute": ["Bash"],
    "web": ["WebFetch", "WebSearch"],
    "edit": ["Edit", "Write"],
}
MARKER = "Generated from {source} by scripts/build_agent_adapters.py; edit the source, not this file."


@dataclass(frozen=True)
class Agent:
    name: str
    description: str
    capabilities: tuple[str, ...] | None  # None means every tool
    user_scoped: bool
    body: str
    source: str


def _frontmatter(text: str, path: Path) -> tuple[dict[str, str], str]:
    match = re.match(r"---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path}: missing frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields, match.group(2)


def load_agents() -> list[Agent]:
    agents = []
    for path in sorted(AGENT_SOURCES.glob("*.md")):
        fields, body = _frontmatter(path.read_text(encoding="utf-8"), path)
        if fields.get("name") != path.stem:
            raise ValueError(f"{path}: name must match the file name")
        raw = fields.get("capabilities", "all")
        capabilities = None
        if raw != "all":
            capabilities = tuple(
                c.strip() for c in raw.strip("[]").split(",") if c.strip()
            )
            unknown = set(capabilities) - set(CAPABILITIES)
            if unknown:
                raise ValueError(f"{path}: unknown capabilities {sorted(unknown)}")
        agents.append(
            Agent(
                name=fields["name"],
                description=fields["description"],
                capabilities=capabilities,
                user_scoped=fields.get("install") == "user",
                body=body,
                source=path.relative_to(ROOT).as_posix(),
            )
        )
    return agents


def copilot_agent(agent: Agent) -> str:
    tools = ""
    if agent.capabilities is not None:
        tools = f"tools: [{', '.join(COPILOT_TOOLS[c] for c in agent.capabilities)}]\n"
    return (
        f"---\nname: {agent.name}\ndescription: {agent.description}\n{tools}---\n"
        f"<!-- {MARKER.format(source=agent.source)} -->\n{agent.body}"
    )


def claude_agent(agent: Agent) -> str:
    tools = ""
    if agent.capabilities is not None:
        names = [n for c in agent.capabilities for n in CLAUDE_TOOLS[c]]
        tools = f"tools: {', '.join(names)}\n"
    return (
        f"---\nname: {agent.name}\ndescription: {agent.description}\n{tools}---\n"
        f"<!-- {MARKER.format(source=agent.source)} -->\n{agent.body}"
    )


def codex_agent(agent: Agent) -> str:
    writes = agent.capabilities is None or "edit" in agent.capabilities
    if "'''" in agent.body:
        raise ValueError(f"{agent.source}: body cannot contain ''' for TOML")
    notes = [f"# {MARKER.format(source=agent.source)}"]
    if agent.capabilities is not None and "web" in agent.capabilities:
        notes.append(
            "# This agent uses the web. Codex does not document per-agent network\n"
            "# access; enable network access in your Codex configuration if needed."
        )
    return (
        "\n".join(notes)
        + f"\nname = {json.dumps(agent.name)}\n"
        + f"description = {json.dumps(agent.description, ensure_ascii=False)}\n"
        + f'sandbox_mode = "{"workspace-write" if writes else "read-only"}"\n'
        + f"developer_instructions = '''\n{agent.body.strip()}\n'''\n"
    )


def skill_loader(name: str, description: str, cli: str) -> str:
    # The canonical description, not a loader-specific one: every CLI picks a
    # skill implicitly by matching its description, so it must be the real one.
    return (
        f"---\nname: {name}\ndescription: {description}\n---\n"
        f"<!-- {MARKER.format(source=f'skills/{name}/SKILL.md')} -->\n\n"
        f"# {name}\n\n"
        f"This is the {cli} discovery loader for a CLI-neutral skill. Load and\n"
        f"follow the canonical skill at\n"
        f"[`skills/{name}/SKILL.md`](../../../skills/{name}/SKILL.md). Its\n"
        f"contract, references, and tests are in the same package. Do not\n"
        f"maintain skill content in this loader.\n"
    )


def expected_outputs() -> dict[Path, str]:
    outputs: dict[Path, str] = {}
    for agent in load_agents():
        if agent.user_scoped:
            outputs[TEMPLATES / f"{agent.name}.agent.md"] = copilot_agent(agent)
            outputs[TEMPLATES / f"{agent.name}.claude.md"] = claude_agent(agent)
            outputs[TEMPLATES / f"{agent.name}.codex.toml"] = codex_agent(agent)
        else:
            outputs[ROOT / f".github/agents/{agent.name}.agent.md"] = copilot_agent(
                agent
            )
            outputs[ROOT / f".claude/agents/{agent.name}.md"] = claude_agent(agent)
            outputs[ROOT / f".codex/agents/{agent.name}.toml"] = codex_agent(agent)
    for skill in sorted(SKILL_SOURCES.glob("*/SKILL.md")):
        fields, _ = _frontmatter(skill.read_text(encoding="utf-8"), skill)
        name = skill.parent.name
        for directory, cli in (
            (".claude/skills", "Claude Code"),
            (".agents/skills", "Codex"),
        ):
            outputs[ROOT / directory / name / "SKILL.md"] = skill_loader(
                name, fields["description"], cli
            )
    return outputs


def managed_files() -> set[Path]:
    """Every file in the generated locations, so stale ones can be found."""
    patterns = (
        (".github/agents", "*.agent.md"),
        (".claude/agents", "*.md"),
        (".codex/agents", "*.toml"),
        (".claude/skills", "*/SKILL.md"),
        (".agents/skills", "*/SKILL.md"),
        (".github/skills", "*/SKILL.md"),
        ("docs/agent-templates", "*"),
    )
    return {p for d, g in patterns for p in (ROOT / d).glob(g) if p.is_file()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check", action="store_true", help="fail if any output is stale"
    )
    args = parser.parse_args(argv)
    outputs = expected_outputs()
    stale = [
        p
        for p, text in outputs.items()
        if not p.exists() or p.read_text(encoding="utf-8") != text
    ]
    extra = sorted(managed_files() - set(outputs))
    if args.check:
        problems = [f"stale or missing: {p.relative_to(ROOT)}" for p in stale]
        problems += [
            f"not generated from a source: {p.relative_to(ROOT)}" for p in extra
        ]
        if problems:
            print("\n".join(problems))
            print("Regenerate with: uv run python scripts/build_agent_adapters.py")
            return 1
        print(f"Agent and skill adapters are current ({len(outputs)} files).")
        return 0
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outputs[path], encoding="utf-8")
    for path in extra:
        path.unlink()
        if not any(path.parent.iterdir()):
            path.parent.rmdir()
    print(f"Wrote {len(stale)}, removed {len(extra)}, of {len(outputs)} adapters.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
