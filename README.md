# Zoo MCP — Code-Example Discovery Layer

> Give your coding agent **live, high-signal example code** on demand. Not summaries. Not vibes. Snippets with provenance.

## What is Zoo MCP?

Zoo MCP is an MCP (Model Context Protocol) server that exposes tools to **find and fetch example code** from reliable public sources via APIs. It helps AI coding agents discover real-world code examples with full provenance (repo URL, path, license).

### Key Features

- **9 specialized tools** for code discovery across GitHub, Grep.app, Libraries.io, and Stack Exchange
- **Provenance tracking**: every snippet includes source URL, repo, file path, and ref
- **Rate limit handling**: exponential backoff with jitter, respects API quotas
- **Safety first**: domain allowlisting, path traversal protection, no code execution
- **Byte budgets**: configurable response size limits
- **STDIO & WebSocket** transport modes

## Quick Start

### Installation

```bash
git clone <repo-url> zoo-mcp
cd zoo-mcp
pip install -e .
```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Key environment variables:

```bash
GITHUB_TOKEN=ghp_xxx                    # Recommended for higher rate limits
LIBRARIESIO_API_KEY=xxx                 # Optional but recommended
GREP_API_URL=https://grep.app/api/search
ZOO_MCP_WORKSPACE=./workspace
ZOO_MCP_MAX_RETURN_BYTES=300000
ORG_ALLOWLIST=aws-samples,GoogleCloudPlatform,microsoft,openai
```

### Running the Server

**STDIO mode (default, for local agents):**

```bash
python -m zoo_mcp.server stdio
```

**WebSocket mode (for remote agents):**

```bash
python -m zoo_mcp.server websocket --host 127.0.0.1 --port 8080
```

## MCP Configuration

### For Claude Desktop / Cline

Add to your MCP settings file (e.g., `.mcp.json`):

```json
{
  "mcpServers": {
    "zoo-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/zoo-mcp",
        "zoo-mcp"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here",
        "LIBRARIESIO_API_KEY": "your_librariesio_key_here",
        "STACKEXCHANGE_KEY": "your_stackexchange_key_here",
        "GREP_API_KEY": "your_grep_api_key_here",
        "GREP_API_URL": "https://grep.app/api/search",
        "ZOO_MCP_WORKSPACE": "./workspace",
        "ZOO_MCP_MAX_RETURN_BYTES": "300000"
      }
    }
  }
}
```

**Note:** Replace `/path/to/zoo-mcp` with the absolute path to your zoo-mcp directory, and add your actual API keys.

## Available Tools

### 1. `gh_search_repos`
Discover repositories by query with qualifiers (language, stars, pushed, topic, org).

### 2. `gh_search_code`
Find code files matching a query.

### 3. `gh_get_contents`
Fetch file or directory listing (README, docs, examples).

### 4. `gh_get_archive`
Download repository snapshot without history (zipball/tarball).

### 5. `grep_search`
Cross-repo regex code search for definitions or call-sites.

### 6. `libsio_dependents`
Find top dependents of a package (repos that use it).

### 7. `gh_releases`
Fetch recent release notes (migration hints, breaking changes).

### 8. `gh_issues_with_code`
Find issues/PRs containing fenced code blocks matching a regex/keyword.

### 9. `so_accepted`
Get accepted Stack Overflow answers with code blocks.

## Agent Orchestration Pattern

**Recommended workflow:**

1. Start with **dependents** (`libsio_dependents`) or **call-site search** (`grep_search`)
2. Grab **small, concrete snippets** from results
3. If deeper reference needed, use `gh_get_contents` or `gh_get_archive`
4. Always cite sources

### Example Flow

```json
// 1. Find repos using axum
{"tool": "libsio_dependents", "args": {"package": "axum", "ecosystem": "cargo", "limit": 30}}

// 2. Search for WebSocket usage patterns
{"tool": "grep_search", "args": {"query": "use axum::\\w+|WebSocket", "language": "Rust", "limit": 50}}

// 3. Fetch specific examples directory
{"tool": "gh_get_contents", "args": {"owner": "tokio-rs", "repo": "axum", "path": "examples/", "ref": "main"}}
```

## Principles

- **Search → Snipe → Fetch**: Don't clone blindly. Find precise hits first.
- **Provenance Always**: Every snippet carries source URL, repo, commit/ref, file path.
- **Prefer Call-Sites** over toy examples: Real usage > README sugar.
- **Reverse-Deps Are Fuel**: Dependents provide living examples.
- **Small > Large**: Favor small files and complete functions/classes.

## Guardrails

- **Domain allowlist**: Only `github.com` and `gitlab.com`
- **Byte budgets**: Responses never exceed `ZOO_MCP_MAX_RETURN_BYTES`
- **Rate limits**: Exponential backoff with jitter; quota surfaced in outputs
- **Safety**: No code execution, path traversal protection

## Development

### Setup

```bash
# Install in development mode
pip install -e ".[dev]"

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys (see API_KEYS_GUIDE.md)
```

### Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_guards.py

# Run with coverage
pytest --cov=zoo_mcp
```

All tests passing: ✅ 24 tests

### Code Formatting

```bash
black zoo_mcp tests
ruff check zoo_mcp tests
```

### Testing with Real APIs

Create a `.env.local` file with your API keys and test:

```bash
# Load your local config
export $(cat .env.local | xargs)

# Test basic functionality
python -c "from zoo_mcp.adapters.github import GitHubAdapter; print(GitHubAdapter().search_repos('fastapi'))"
```

## Architecture

```
zoo_mcp/
├── adapters/          # API clients (GitHub, Grep, Libraries.io, Stack Exchange)
├── tools/             # MCP tool bindings
├── schemas.py         # Pydantic models for inputs/outputs
├── limits.py          # Rate limiting, backoff, windowing utilities
├── guards.py          # Domain allowlist, path safety, byte budgets
└── server.py          # FastMCP server entry point
```

## License

MIT

## Contributing

PRs welcome! Please ensure tests pass and code is formatted with `black`.