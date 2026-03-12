# WebCLI

Turn any website into a CLI/API for AI agents.

WebCLI captures browser network traffic, discovers API patterns, and auto-generates structured interfaces (CLI commands, MCP servers, Python clients) so AI agents can interact with any web service as fast function calls instead of slow browser automation.

## The Problem

AI agents interact with websites through browser automation (Playwright, Puppeteer, Computer Use), which is:
- **10-100x slower** than direct API calls
- **10-100x more expensive** in LLM tokens
- **~15-35% reliable** on academic benchmarks

## The Solution: Progressive Formalization

WebCLI uses a 3-tier system that automatically graduates interactions from slow-but-universal to fast-but-specific:

```
Tier 3: Direct API Calls     (fastest, most reliable)
  ^  Auto-generated from discovered API patterns
Tier 2: Cached Workflows     (medium speed)
  ^  Recorded browser workflows, parameterized + replayed
Tier 1: Browser Exploration   (slowest, universal fallback)
  ^  LLM-driven browser automation for unknown sites
```

## Quick Start

```bash
# Install (lightweight - no browser deps by default)
pip install webcli

# Install with all features
pip install webcli[all]

# Or pick what you need
pip install webcli[browser]   # Playwright for traffic capture
pip install webcli[llm]       # Claude API for smart analysis
pip install webcli[mcp]       # MCP server generation
```

### Discover a Site's API

```bash
# Capture traffic and discover API endpoints
webcli discover kayak.com --action "search flights"

# WebCLI launches a browser, captures network traffic,
# and generates: OpenAPI spec + CLI commands + MCP tools
```

### Use the Generated Interface

```bash
# CLI
webcli run kayak.com search_flights --from SFO --to JFK --date 2025-04-01

# Or as MCP tools for AI agents
webcli mcp generate kayak.com
webcli mcp serve kayak.com
```

### As a Python Library

```python
from webcli.discovery.analyzer import TrafficAnalyzer
from webcli.discovery.spec_generator import generate_openapi_spec
from webcli.generators.mcp_gen import generate_mcp_server_code

# Analyze captured traffic
analyzer = TrafficAnalyzer(exchanges)
endpoints = analyzer.extract_endpoints()

# Generate OpenAPI spec
spec = generate_openapi_spec(api)

# Generate MCP server
mcp_code = generate_mcp_server_code(site, spec)
```

## What Gets Generated

From a single discovery session, WebCLI produces:

| Output | Description |
|--------|-------------|
| **OpenAPI 3.1 Spec** | Full API specification with schemas, parameters, auth |
| **Python Client** | Typed httpx client with methods for each endpoint |
| **CLI Commands** | Typer commands you can run from terminal |
| **MCP Server** | Tools that AI agents (Claude, etc.) can call directly |

## Architecture

```
                    WebCLI Core
+----------+--------------+--------------+------------+
|  CLI     |  MCP Server  |  Python SDK  |  REST API  |
+----------+--------------+--------------+------------+
|                Router / Resolver                     |
|  (Picks best available tier for a given site+action) |
+------------------------------------------------------+
|  Tier 1: Browser  | Tier 2: Cached   | Tier 3: API  |
|  Explorer          | Workflows        | Clients      |
+------------------------------------------------------+
|              API Discovery Engine                    |
|  Traffic Capture -> Pattern Analysis -> Spec Gen     |
+------------------------------------------------------+
|  Auth Manager  |  Site Registry  |  Health Monitor   |
+------------------------------------------------------+
```

## Key Features

- **Auto-discovery**: Captures browser traffic via CDP and infers API patterns
- **Smart analysis**: LLM-assisted endpoint description and parameter inference
- **Progressive promotion**: Actions auto-upgrade from browser -> workflow -> API as patterns stabilize
- **MCP native**: Generated tools work directly with Claude and other MCP-compatible agents
- **Self-healing**: Detects when APIs break and attempts automatic repair
- **Community sharing**: Export/import site specs like yt-dlp extractors
- **Lightweight core**: Heavy deps (Playwright, Anthropic, MCP) are optional

## Development

```bash
# Clone and install with dev dependencies
git clone https://github.com/lonexreb/webcli.git
cd webcli
pip install -e ".[dev]"

# Run tests
pytest                         # Unit + integration tests (no network)
pytest -m live                 # Live tests (hits real APIs)
pytest -v                      # Verbose output

# Lint
ruff check src/ tests/
```

### Test Coverage

- **65 unit/integration tests** covering models, registry, analyzer, spec generation, client generation, CLI, MCP generation, tier promotion, and full pipeline
- **6 live tests** against JSONPlaceholder and httpbin.org
- All tests pass on Python 3.10+

## API Keys

For full functionality:
- **Anthropic API key** (`ANTHROPIC_API_KEY`): Used for LLM-assisted endpoint analysis. Optional — discovery works without it, just without enhanced descriptions.
- **No other keys required** for core functionality.

## Roadmap

- [ ] Community spec registry (share discovered APIs)
- [ ] Browser cookie extraction for authenticated sites
- [ ] OAuth device flow support
- [ ] PyPI package publication
- [ ] Workflow recording and replay (Tier 2)
- [ ] Health monitoring dashboard

## License

MIT
