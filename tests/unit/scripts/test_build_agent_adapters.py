"""The CLI adapters, tested on the ways one CLI could silently lose an agent.

Each CLI reads its own directory and format, so a missing or stale adapter
fails quietly: the agent simply is not there in that CLI. These pin that every
source reaches every CLI, with the permissions it declared.
"""

import tomllib

import pytest

from scripts import build_agent_adapters as build
from scripts.build_agent_adapters import (
    ROOT,
    Agent,
    claude_agent,
    codex_agent,
    copilot_agent,
    expected_outputs,
    load_agents,
    main,
)


def agent(capabilities=("read", "search"), **extra):
    return Agent(
        name="demo",
        description="A demo agent.",
        capabilities=capabilities,
        user_scoped=False,
        body="\nDo things.\n",
        source="agents/demo.md",
        **extra,
    )


def test_committed_adapters_are_current():
    assert main(["--check"]) == 0


def test_every_agent_reaches_every_cli():
    outputs = {p.relative_to(ROOT).as_posix() for p in expected_outputs()}
    for a in load_agents():
        if a.user_scoped:
            base = f"docs/agent-templates/{a.name}"
            expected = {f"{base}.agent.md", f"{base}.claude.md", f"{base}.codex.toml"}
        else:
            expected = {
                f".github/agents/{a.name}.agent.md",
                f".claude/agents/{a.name}.md",
                f".codex/agents/{a.name}.toml",
            }
        assert expected <= outputs, a.name


def test_every_skill_is_discoverable_by_claude_code_and_codex():
    outputs = {p.relative_to(ROOT).as_posix() for p in expected_outputs()}
    for skill in (ROOT / "skills").glob("*/SKILL.md"):
        name = skill.parent.name
        assert f".claude/skills/{name}/SKILL.md" in outputs
        assert f".agents/skills/{name}/SKILL.md" in outputs


def test_read_only_capabilities_map_to_each_clis_vocabulary():
    a = agent()
    assert "tools: [read, search]" in copilot_agent(a)
    assert "tools: Read, Grep, Glob" in claude_agent(a)
    assert 'sandbox_mode = "read-only"' in codex_agent(a)


def test_edit_capability_is_the_only_way_to_a_writable_codex_sandbox():
    assert 'sandbox_mode = "read-only"' in codex_agent(agent(("read", "execute")))
    assert 'sandbox_mode = "workspace-write"' in codex_agent(agent(("read", "edit")))
    assert 'sandbox_mode = "workspace-write"' in codex_agent(agent(None))


def test_unrestricted_agents_omit_the_tools_restriction():
    a = agent(None)
    assert "tools:" not in copilot_agent(a) and "tools:" not in claude_agent(a)


def test_every_codex_adapter_is_valid_toml_with_the_required_fields():
    for path, text in expected_outputs().items():
        if path.suffix == ".toml":
            data = tomllib.loads(text)
            assert {"name", "description", "developer_instructions"} <= set(data), path


def test_skill_loaders_carry_the_canonical_description():
    """Every CLI picks a skill implicitly by its description, so a loader
    that says "discovery loader" would never be picked for the real task."""
    outputs = expected_outputs()
    source = (ROOT / "skills/agentic-pm-mastery/SKILL.md").read_text()
    loader = outputs[ROOT / ".claude/skills/agentic-pm-mastery/SKILL.md"]
    canonical = next(
        line for line in source.splitlines() if line.startswith("description:")
    )
    assert canonical in loader


def test_a_source_with_an_unknown_capability_is_rejected(tmp_path, monkeypatch):
    (tmp_path / "x.md").write_text(
        "---\nname: x\ndescription: d\ncapabilities: [read, teleport]\n---\nbody\n"
    )
    monkeypatch.setattr(build, "AGENT_SOURCES", tmp_path)
    with pytest.raises(ValueError, match="unknown capabilities"):
        load_agents()


def test_a_source_whose_name_differs_from_its_file_is_rejected(tmp_path, monkeypatch):
    (tmp_path / "x.md").write_text("---\nname: y\ndescription: d\n---\nbody\n")
    monkeypatch.setattr(build, "AGENT_SOURCES", tmp_path)
    with pytest.raises(ValueError, match="must match the file name"):
        load_agents()
