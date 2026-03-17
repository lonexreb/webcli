"""Agent configuration generation for discovered sites."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from site2cli.models import SiteEntry


def generate_claude_mcp_config(sites: list[SiteEntry]) -> dict:
    """Generate Claude Code MCP config with server entries for each discovered site.

    Args:
        sites: List of discovered site entries.

    Returns:
        Dict suitable for Claude Code MCP configuration.
    """
    servers: dict[str, dict] = {}
    for site in sites:
        safe_name = site.domain.replace(".", "-").replace(":", "-")
        server_key = f"site2cli-{safe_name}"

        # Determine MCP server path
        from site2cli.config import get_config

        config = get_config()
        mcp_path = config.data_dir / "mcp" / f"{site.domain.replace('.', '_')}_mcp.py"

        servers[server_key] = {
            "command": sys.executable,
            "args": [str(mcp_path)],
        }

    return {"mcpServers": servers}


def generate_generic_agent_prompt(sites: list[SiteEntry]) -> str:
    """Generate markdown listing available site2cli capabilities and discovered sites.

    Args:
        sites: List of discovered site entries.

    Returns:
        Markdown-formatted prompt text.
    """
    lines = [
        "# Available site2cli Capabilities",
        "",
        "The following websites have been discovered and are available via site2cli:",
        "",
    ]

    if not sites:
        lines.append("*No sites discovered yet. Run `site2cli discover <url>` to get started.*")
        return "\n".join(lines)

    for site in sites:
        lines.append(f"## {site.domain}")
        lines.append(f"- **Base URL**: {site.base_url}")
        lines.append(f"- **Auth**: {site.auth_type.value}")
        if site.description:
            lines.append(f"- **Description**: {site.description}")

        if site.actions:
            lines.append("- **Actions**:")
            for action in site.actions:
                desc = f" — {action.description}" if action.description else ""
                lines.append(f"  - `site2cli run {site.domain} {action.name}`{desc}")
        lines.append("")

    lines.extend([
        "## Usage",
        "",
        "```bash",
        "# Execute an action",
        "site2cli run <domain> <action> [key=value ...]",
        "",
        "# List all discovered sites",
        "site2cli sites list",
        "",
        "# Generate MCP server for a site",
        "site2cli mcp generate <domain>",
        "```",
    ])

    return "\n".join(lines)
