# Zoo MCP — Code-Example Discovery Layer

![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)

> Give your coding agent **live, high-signal example code** on demand. Not summaries. Not vibes. Snippets with provenance.

## What is Zoo MCP?

Zoo MCP is an MCP (Model Context Protocol) server that exposes tools to **find and fetch example code** from reliable public sources via APIs. It helps AI coding agents discover real-world code examples with full provenance (repo URL, path, license).

### Key Features

- **12 specialized tools** for code discovery across GitHub, Exa, Grep.app, Libraries.io, and Stack Exchange
- **Provenance tracking**: every snippet includes source URL, repo, file path, and ref
- **Rate limit handling**: exponential backoff with jitter, respects API quotas
- **Safety first**: domain allowlisting, path traversal protection, no code execution
- **Byte budgets**: configurable response size limits
- **STDIO & WebSocket** transport modes

## Quick Start

**New to Zoo MCP?** Use the built-in help tool: `zoo_help("quick-start")` for a 5-minute walkthrough, or `zoo_help("overview")` for a comprehensive introduction.

Available help topics: `overview`, `discovery`, `zoo`, `workflows`, `tools`, `quick-start`

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
EXA_API_KEY=xxx                         # Optional but recommended for semantic search
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
        "EXA_API_KEY": "your_exa_api_key_here",
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

## Features

### Code Discovery (Original)
- **12 specialized tools** for code discovery across GitHub, Exa, Grep.app, Libraries.io, and Stack Exchange
- Search repositories, code files, issues, and Stack Overflow answers
- **Semantic/neural search** with Exa for meaning-based code discovery
- Real-time fetching with full provenance tracking

### Zoo Management (New - Persistent Storage)
- **Create "Zoos"** - Project-specific code example collections
- **Organize with Tasks** - Group examples by topic/feature
- **Commit Examples** - Store code from any discovery tool
- **Rich Metadata** - Auto-generated file maps, structure analysis, summaries
- **Smart Search** - Grep across stored examples, find functions/classes
- **Export/Import** - Share zoo collections as JSON or markdown

## Available Tools

### Original Discovery Tools (12)

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

### 10. `exa_search`
Semantic/neural web search powered by Exa (meaning-based, not keyword-based).

### 11. `exa_code_search`
Code-specific semantic search optimized for GitHub, Stack Overflow, and documentation sites.

### 12. `exa_find_similar`
Find pages similar to a given URL using neural similarity matching.

---

### Help Tool (1 tool)

#### `zoo_help`
Get comprehensive help about Zoo MCP tools and workflows.

**Usage**: `zoo_help(topic?)`

**Available topics**:
- `overview` - General introduction and architecture
- `discovery` - Discovery tools (search APIs)
- `zoo` - Zoo management (persistent storage)
- `workflows` - Common usage patterns with examples
- `tools` - Complete tool reference
- `quick-start` - Getting started guide

---

### Zoo Management Tools (32 Tools)

#### Zoo CRUD (6 tools)
- `zoo_create(name, description, tags?)` - Create new zoo
- `zoo_list()` - List all zoos
- `zoo_get(zoo_id)` - Get zoo with tasks
- `zoo_update(zoo_id, ...)` - Update metadata
- `zoo_delete(zoo_id)` - Delete zoo
- `zoo_search(query)` - Search zoos

#### Task CRUD (5 tools)
- `task_create(zoo_id, name, description, tags?)` - Create task
- `task_list(zoo_id)` - List tasks
- `task_get(zoo_id, task_id)` - Get task with examples
- `task_update(zoo_id, task_id, ...)` - Update metadata
- `task_delete(zoo_id, task_id)` - Delete task

#### Example Commit (11 tools)
- `example_commit_from_url(zoo_id, task_id, url, description, tags?)` - From GitHub URL
- `example_commit_from_content(zoo_id, task_id, filename, content, ...)` - Direct content
- `example_commit_from_search_result(zoo_id, task_id, search_type, result, ...)` - From any search tool
- `example_list(zoo_id, task_id)` - List examples (metadata only)
- `example_get_meta(zoo_id, task_id, example_id)` - Get metadata
- `example_get_content(zoo_id, task_id, example_id, filename?)` - Get source code
- `example_get_file_map(zoo_id, task_id, example_id)` - Get file outline
- `example_update_meta(...)` - Update metadata
- `example_add_file(...)` - Add file to example
- `example_delete(...)` - Delete example

#### Search & Query (6 tools)
- `zoo_grep(zoo_id, pattern, ...)` - Regex search across zoo
- `task_grep(zoo_id, task_id, pattern, ...)` - Regex search in task
- `example_grep(zoo_id, task_id, example_id, pattern)` - Regex search in example
- `zoo_search_examples(zoo_id, query)` - Search by description/tags
- `example_get_function(zoo_id, task_id, example_id, function_name)` - Extract function
- `example_get_snippet(zoo_id, task_id, example_id, filename, start, end)` - Get line range

#### Export & Import (4 tools)
- `zoo_export_json(zoo_id, include_content?, output_path?)` - Export to JSON
  - If `output_path` not specified → exports to MCP workspace
  - If `output_path` specified → can export to **any path** (including user's project directory)
- `zoo_export_markdown(zoo_id, include_code_samples?, output_path?)` - Export to markdown
  - Same path flexibility as JSON export
- `zoo_import_json(input_path)` - Import from JSON (can import from any accessible path)
- `zoo_get_index(zoo_id, include_tasks?, include_examples?)` - Get compact index

**Path Examples:**
```python
# Export to MCP workspace (default)
zoo_export_json(zoo_id="my-zoo")

# Export to user's current project
zoo_export_json(zoo_id="my-zoo", output_path="./my-zoo-backup.json")

# Export to specific location
zoo_export_json(zoo_id="my-zoo", output_path="/Users/name/Desktop/zoo-export.json")

# Import from user's project
zoo_import_json(input_path="./my-zoo-backup.json")
```

## Agent Orchestration Patterns

### Pattern 1: Discovery & Search (Original)

**Recommended workflow:**

1. Start with **dependents** (`libsio_dependents`) or **call-site search** (`grep_search`)
2. Grab **small, concrete snippets** from results
3. If deeper reference needed, use `gh_get_contents` or `gh_get_archive`
4. Always cite sources

### Pattern 2: Zoo Management (Persistent Curation)

**Workflow:**

1. **Create Zoo** for your project domain
2. **Create Tasks** for specific features/modules
3. **Search** using discovery tools (gh_search_code, grep_search, etc.)
4. **Review** results and **commit** selected examples to tasks
5. **Query** stored examples with grep/search
6. **Extract** specific functions/snippets as needed
7. **Export** for team sharing or backup

### Example Flow (Original Discovery)

```json
// 1. Find repos using axum
{"tool": "libsio_dependents", "args": {"package": "axum", "ecosystem": "cargo", "limit": 30}}

// 2. Search for WebSocket usage patterns
{"tool": "grep_search", "args": {"query": "use axum::\\w+|WebSocket", "language": "Rust", "limit": 50}}

// 3. Fetch specific examples directory
{"tool": "gh_get_contents", "args": {"owner": "tokio-rs", "repo": "axum", "path": "examples/", "ref": "main"}}
```

### Example Flow (Zoo Management)

```python
# 1. Create zoo for Three.js game development
zoo = zoo_create(
    name="Three.js Game Dev",
    description="Code examples for 3D game development",
    tags=["threejs", "webgl", "game-dev"]
)

# 2. Create task for terrain generation
task = task_create(
    zoo_id=zoo["id"],
    name="Terrain Generation",
    description="Procedural terrain generation techniques",
    tags=["procedural", "heightmap"]
)

# 3. Search for examples
code_results = gh_search_code("THREE.js terrain procedural")

# 4. Review and commit selected example
example = example_commit_from_search_result(
    zoo_id=zoo["id"],
    task_id=task["id"],
    search_type="gh_search_code",
    result_data=code_results["items"][0],
    description="Official Three.js terrain implementation",
    tags=["official", "heightmap"],
    fetch_full=True
)

# 5. Later: Query stored examples
matches = task_grep(
    zoo_id=zoo["id"],
    task_id=task["id"],
    pattern="function.*terrain"
)

# 6. Extract specific function
terrain_func = example_get_function(
    zoo_id=zoo["id"],
    task_id=task["id"],
    example_id=example["id"],
    function_name="generateTerrain"
)

# 7. Export for team
zoo_export_json(
    zoo_id=zoo["id"],
    output_path="./team-shared/threejs-zoo.json"
)
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