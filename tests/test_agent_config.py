"""Tests for agent configuration generation."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from site2cli.generators.agent_config import (
    generate_claude_mcp_config,
    generate_generic_agent_prompt,
)
from site2cli.models import AuthType, SiteEntry, Tier


def _make_site(domain: str = "example.com", actions: int = 2) -> SiteEntry:
    """Create a minimal SiteEntry for testing."""
    from site2cli.models import SiteAction

    site_actions = [
        SiteAction(
            name=f"action_{i}",
            description=f"Test action {i}",
            tier=Tier.API,
        )
        for i in range(actions)
    ]
    return SiteEntry(
        domain=domain,
        base_url=f"https://{domain}",
        description=f"Test site {domain}",
        actions=site_actions,
        auth_type=AuthType.NONE,
    )


def test_claude_config_zero_sites():
    config = generate_claude_mcp_config([])
    assert config == {"mcpServers": {}}


def test_claude_config_one_site():
    sites = [_make_site("example.com")]
    config = generate_claude_mcp_config(sites)
    assert "mcpServers" in config
    assert "site2cli-example-com" in config["mcpServers"]
    server = config["mcpServers"]["site2cli-example-com"]
    assert "command" in server
    assert "args" in server


def test_claude_config_three_sites():
    sites = [_make_site(d) for d in ["a.com", "b.io", "c.org"]]
    config = generate_claude_mcp_config(sites)
    assert len(config["mcpServers"]) == 3
    assert "site2cli-a-com" in config["mcpServers"]
    assert "site2cli-b-io" in config["mcpServers"]
    assert "site2cli-c-org" in config["mcpServers"]


def test_claude_config_valid_json():
    sites = [_make_site("example.com")]
    config = generate_claude_mcp_config(sites)
    # Should be serializable
    serialized = json.dumps(config, indent=2)
    parsed = json.loads(serialized)
    assert parsed == config


def test_generic_prompt_no_sites():
    prompt = generate_generic_agent_prompt([])
    assert "No sites discovered" in prompt


def test_generic_prompt_with_sites():
    sites = [_make_site("example.com", actions=2)]
    prompt = generate_generic_agent_prompt(sites)
    assert "example.com" in prompt
    assert "action_0" in prompt
    assert "action_1" in prompt
    assert "site2cli run" in prompt


def test_generic_prompt_includes_usage():
    sites = [_make_site("test.io")]
    prompt = generate_generic_agent_prompt(sites)
    assert "## Usage" in prompt
    assert "site2cli run" in prompt
    assert "site2cli sites list" in prompt


def test_cli_init_command():
    """init command is registered and shows help."""
    from site2cli.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["init", "--help"])
    assert result.exit_code == 0
    assert "agent" in result.output.lower()
