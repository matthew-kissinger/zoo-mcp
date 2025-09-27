def zoo_help(topic: str = "overview") -> dict:
    """
    Comprehensive help system for Zoo MCP.

    Available topics:
    - overview: General introduction and architecture
    - discovery: Discovery tools (search APIs)
    - zoo: Zoo management (persistent storage)
    - workflows: Common usage patterns
    - tools: Complete tool reference
    - quick-start: Getting started guide
    """

    help_content = {
        "overview": """
# Zoo MCP - Code Example Discovery & Curation Platform

## What is Zoo MCP?

Zoo MCP is a Model Context Protocol (MCP) server that provides AI coding agents with:

1. **Discovery Layer**: 12 tools to search for real-world code examples across:
   - GitHub (repositories, code, issues, releases)
   - Exa (semantic/neural search across 1B+ webpages)
   - Grep.app (regex pattern matching)
   - Libraries.io (package dependents)
   - Stack Overflow (accepted answers)

2. **Curation Layer**: 32 tools to organize, store, and query discovered examples in "Zoos":
   - Create project-specific code example collections
   - Organize examples by tasks/features
   - Search/grep across stored examples
   - Export/import for team sharing

## Why Use Zoo MCP?

**Problem**: AI agents need real-world code examples, not toy snippets or outdated docs.

**Solution**: Zoo MCP gives agents the ability to:
- Find production code examples with full provenance
- Understand how real developers solve problems
- Build a curated library of high-quality examples
- Search by meaning (semantic search), not just keywords

## Two-Layer Architecture

```
┌─────────────────────────────────────────┐
│   Discovery Layer (12 tools)            │
│   • GitHub search (6 tools)             │
│   • Exa semantic search (3 tools)       │
│   • Grep pattern search (1 tool)        │
│   • Libraries.io dependents (1 tool)    │
│   • Stack Overflow answers (1 tool)     │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│   Curation Layer (32 tools)             │
│   • Create Zoos (collections)           │
│   • Organize with Tasks                 │
│   • Store examples with metadata        │
│   • Search/grep stored examples         │
│   • Export/import for sharing           │
└─────────────────────────────────────────┘
```

## Key Features

- **Semantic Search**: Find code by meaning, not just keywords (via Exa)
- **Full Provenance**: Every example includes source URL, repo, file path, license
- **Smart Organization**: Hierarchical structure (Zoo → Tasks → Examples)
- **Rich Metadata**: Auto-generated file maps, language detection, function extraction
- **Rate Limit Handling**: Exponential backoff, respects API quotas
- **Security**: Domain allowlisting, path traversal protection, no code execution

## Quick Stats

- **Total Tools**: 44 (12 discovery + 32 curation)
- **APIs Integrated**: 5 (GitHub, Exa, Grep.app, Libraries.io, Stack Exchange)
- **Search Modes**: Keyword, semantic/neural, regex, similarity
- **Storage Format**: JSON files (Git-friendly, human-readable)

Use `zoo_help("quick-start")` to get started or `zoo_help("workflows")` for usage patterns.
""",

        "discovery": """
# Discovery Tools (12 tools)

Discovery tools search external APIs to find real-world code examples.

## GitHub Tools (6 tools)

### 1. gh_search_repos(q, sort?, order?, per_page?, page?, time_windows?)
Search GitHub repositories with qualifiers.

**Example**:
```
gh_search_repos(
    q="language:rust stars:>100 websocket",
    sort="stars",
    per_page=20
)
```

### 2. gh_search_code(q, per_page?, page?)
Search code files on GitHub.

**Example**:
```
gh_search_code(
    q="fastapi dependency injection filename:main.py"
)
```

### 3. gh_get_contents(owner, repo, path, ref?, save_to?)
Fetch file or directory contents from a GitHub repo.

**Example**:
```
gh_get_contents(
    owner="fastapi",
    repo="fastapi",
    path="examples/websocket.py"
)
```

### 4. gh_get_archive(owner, repo, ref?, format?, save_to?)
Download entire repository as zip/tarball.

**Example**:
```
gh_get_archive(
    owner="tokio-rs",
    repo="axum",
    format="zipball"
)
```

### 5. gh_releases(owner, repo, limit?)
Fetch recent release notes (migration hints, breaking changes).

**Example**:
```
gh_releases(
    owner="fastapi",
    repo="fastapi",
    limit=5
)
```

### 6. gh_issues_with_code(owner, repo, q, limit?)
Find issues/PRs containing code blocks matching a query.

**Example**:
```
gh_issues_with_code(
    owner="fastapi",
    repo="fastapi",
    q="async database",
    limit=10
)
```

## Exa Tools (3 tools) - Semantic/Neural Search

### 7. exa_search(query, search_type?, num_results?, ...)
Semantic web search (meaning-based, not keyword).

**Example**:
```
exa_search(
    query="python async best practices",
    search_type="neural",
    num_results=10
)
```

**Why use this**: Finds content by meaning. "Auth patterns" finds authentication implementations even without exact keywords.

### 8. exa_code_search(query, num_results?, include_domains?)
Code-specific semantic search (GitHub, Stack Overflow, docs).

**Example**:
```
exa_code_search(
    query="fastapi websocket authentication",
    num_results=15
)
```

**Why use this**: Optimized for code discovery across multiple platforms simultaneously.

### 9. exa_find_similar(url, num_results?, exclude_source_domain?)
Find pages/repos similar to a given URL.

**Example**:
```
exa_find_similar(
    url="https://github.com/fastapi/fastapi",
    num_results=10,
    exclude_source_domain=True
)
```

**Why use this**: Discover architecturally similar projects.

## Other Discovery Tools

### 10. grep_search(query, language?, path?, limit?)
Cross-repo regex pattern search via Grep.app.

**Example**:
```
grep_search(
    query="async fn.*handle_request",
    language="rust",
    limit=30
)
```

### 11. libsio_dependents(package, ecosystem, limit?)
Find top repos that depend on a package.

**Example**:
```
libsio_dependents(
    package="fastapi",
    ecosystem="pypi",
    limit=50
)
```

**Why use this**: See how real projects use a library.

### 12. so_accepted(q, tags?, limit?)
Get accepted Stack Overflow answers with code blocks.

**Example**:
```
so_accepted(
    q="fastapi background tasks",
    tags=["python", "fastapi"],
    limit=5
)
```

## Discovery Best Practices

1. **Start Broad, Then Narrow**: Use gh_search_repos first, then gh_search_code
2. **Use Semantic Search**: exa_code_search finds by meaning, not just keywords
3. **Find Real Usage**: libsio_dependents shows production code
4. **Pattern Search**: grep_search for specific code patterns (regex)
5. **Check Issues**: gh_issues_with_code often has solution code snippets
""",

        "zoo": """
# Zoo Management Tools (32 tools)

Zoo tools let you organize, store, and query discovered code examples.

## Hierarchy

```
Zoo (Collection)
└── Task (Feature/Topic)
    └── Example (Code Sample)
        └── Files (Source Code)
```

## Zoo CRUD (6 tools)

### zoo_create(name, description, tags?)
Create a new code example collection.

**Example**:
```
zoo_create(
    name="FastAPI Production Patterns",
    description="Real-world FastAPI implementations",
    tags=["fastapi", "python", "rest-api"]
)
```

### zoo_list()
List all your zoos.

### zoo_get(zoo_id)
Get zoo details with task list.

### zoo_update(zoo_id, name?, description?, tags?)
Update zoo metadata.

### zoo_delete(zoo_id)
Delete zoo and all contents.

### zoo_search(query)
Search zoos by name/description/tags.

## Task CRUD (5 tools)

### task_create(zoo_id, name, description, tags?)
Create a task within a zoo to organize examples.

**Example**:
```
task_create(
    zoo_id="zoo_abc123",
    name="WebSocket Authentication",
    description="Examples of auth in WebSocket connections",
    tags=["websocket", "auth", "jwt"]
)
```

### task_list(zoo_id, status_filter?)
List all tasks in a zoo.

### task_get(zoo_id, task_id, include_examples?)
Get task details with optional example list.

### task_update(zoo_id, task_id, ...)
Update task metadata/status.

### task_delete(zoo_id, task_id)
Delete task and all its examples.

## Example Management (10 tools)

### example_commit_from_url(zoo_id, task_id, url, description, tags?)
Commit example from GitHub URL.

**Example**:
```
example_commit_from_url(
    zoo_id="zoo_abc123",
    task_id="task_xyz789",
    url="https://github.com/fastapi/fastapi/blob/master/examples/websocket.py",
    description="Official FastAPI WebSocket example",
    tags=["official", "websocket"]
)
```

### example_commit_from_search_result(zoo_id, task_id, search_type, result_data, description, tags?, fetch_full?)
Commit example from any discovery tool result.

**Example**:
```
# First search
results = exa_code_search("fastapi dependency injection")

# Then commit best result
example_commit_from_search_result(
    zoo_id="zoo_abc123",
    task_id="task_xyz789",
    search_type="exa_code_search",
    result_data=results["items"][0],
    description="Production DI pattern",
    tags=["dependency-injection"],
    fetch_full=True
)
```

**Supported search types**:
- `gh_search_code`
- `gh_get_contents`
- `grep_search`
- `exa_search`
- `exa_code_search`
- `exa_find_similar`
- `stackoverflow`
- `gh_issues`

### example_commit_from_content(zoo_id, task_id, filename, content, language, description, ...)
Commit code directly without fetching.

### Other Example Tools
- `example_list(zoo_id, task_id)` - List examples (metadata only)
- `example_get_meta(zoo_id, task_id, example_id)` - Get metadata
- `example_get_content(zoo_id, task_id, example_id, filename?)` - Get source code
- `example_get_file_map(zoo_id, task_id, example_id)` - Get file structure
- `example_update_meta(...)` - Update metadata
- `example_add_file(...)` - Add file to example
- `example_delete(...)` - Delete example

## Query Tools (6 tools)

### zoo_grep(zoo_id, pattern, language?, task_filter?, flags?, max_results?)
Regex search across all examples in a zoo.

**Example**:
```
zoo_grep(
    zoo_id="zoo_abc123",
    pattern="async def.*auth",
    language="python",
    flags="i"
)
```

### task_grep(zoo_id, task_id, pattern, ...)
Search within a specific task.

### example_grep(zoo_id, task_id, example_id, pattern, flags?)
Search within a single example.

### zoo_search_examples(zoo_id, query)
Search examples by description, tags, or filename.

### example_get_function(zoo_id, task_id, example_id, function_name)
Extract specific function from an example.

**Example**:
```
example_get_function(
    zoo_id="zoo_abc123",
    task_id="task_xyz789",
    example_id="ex_def456",
    function_name="authenticate_user"
)
```

### example_get_snippet(zoo_id, task_id, example_id, filename, start_line, end_line)
Get specific line range from a file.

## Export/Import (4 tools)

### zoo_export_json(zoo_id, include_content?, output_path?)
Export zoo to JSON file.

**Example**:
```
# Export to project directory
zoo_export_json(
    zoo_id="zoo_abc123",
    include_content=True,
    output_path="./my-zoo-backup.json"
)
```

### zoo_export_markdown(zoo_id, include_code_samples?, output_path?)
Export zoo to markdown documentation.

### zoo_import_json(input_path)
Import zoo from JSON file.

### zoo_get_index(zoo_id, include_tasks?, include_examples?)
Get compact overview of zoo (context-efficient).
""",

        "workflows": """
# Common Workflows

## Workflow 1: Discovery → Store → Query

**Goal**: Find production examples and build a searchable library.

```
# 1. Search for examples
results = exa_code_search(
    query="fastapi websocket authentication",
    num_results=20
)

# 2. Create zoo and task
zoo = zoo_create(
    name="FastAPI Patterns",
    description="Production FastAPI implementations"
)

task = task_create(
    zoo_id=zoo["id"],
    name="WebSocket Auth",
    description="WebSocket authentication patterns"
)

# 3. Commit best examples
for result in results["items"][:5]:
    example_commit_from_search_result(
        zoo_id=zoo["id"],
        task_id=task["id"],
        search_type="exa_code_search",
        result_data=result,
        description=result["title"]
    )

# 4. Later: Query stored examples
matches = task_grep(
    zoo_id=zoo["id"],
    task_id=task["id"],
    pattern="async.*authenticate"
)

# 5. Extract specific function
func = example_get_function(
    zoo_id=zoo["id"],
    task_id=task["id"],
    example_id=matches[0]["example_id"],
    function_name="authenticate_websocket"
)
```

## Workflow 2: Package Exploration

**Goal**: Learn how a library is used in production.

```
# 1. Find repos using the package
dependents = libsio_dependents(
    package="fastapi",
    ecosystem="pypi",
    limit=50
)

# 2. Search for specific usage patterns
for dep in dependents["dependents"][:10]:
    repo_name = dep["repo"]

    # Search for auth implementations
    code_results = gh_search_code(
        q=f"repo:{repo_name} fastapi Depends authenticate"
    )

    # Store interesting examples
    if code_results["items"]:
        example_commit_from_search_result(
            zoo_id="zoo_fastapi_patterns",
            task_id="task_auth",
            search_type="gh_search_code",
            result_data=code_results["items"][0],
            description=f"Auth from {repo_name}"
        )
```

## Workflow 3: Semantic Discovery

**Goal**: Find code by meaning, not keywords.

```
# Instead of keyword search...
# ❌ gh_search_code("JWT token validation")

# Use semantic search
# ✅ exa_code_search("how to verify user identity in APIs")

results = exa_code_search(
    query="validate user identity in REST APIs with tokens",
    num_results=15
)

# Exa understands meaning and finds:
# - JWT implementations
# - OAuth flows
# - Session validation
# - API key verification
# Even if they don't contain exact keywords!
```

## Workflow 4: Pattern Mining

**Goal**: Find specific code patterns across repos.

```
# Find async error handling patterns
grep_results = grep_search(
    query="async fn.*Result<.*Error>",
    language="rust",
    limit=50
)

# Store patterns
zoo = zoo_create(
    name="Rust Async Patterns",
    description="Error handling in async Rust"
)

task = task_create(
    zoo_id=zoo["id"],
    name="Result Type Patterns",
    description="Common Result<T, E> usage"
)

for hit in grep_results["hits"]:
    example_commit_from_search_result(
        zoo_id=zoo["id"],
        task_id=task["id"],
        search_type="grep_search",
        result_data=hit,
        description=f"Pattern from {hit['repo']}",
        fetch_full=True  # Get full file, not just snippet
    )
```

## Workflow 5: Team Knowledge Base

**Goal**: Build and share curated examples with team.

```
# 1. Create team zoo
zoo = zoo_create(
    name="Team Best Practices",
    description="Our approved patterns and examples"
)

# 2. Curate examples
# (Add examples using any discovery method)

# 3. Export for sharing
zoo_export_json(
    zoo_id=zoo["id"],
    output_path="./team-shared/best-practices.json"
)

# 4. Team members import
zoo_import_json(
    input_path="./team-shared/best-practices.json"
)

# 5. Search team examples
results = zoo_search_examples(
    zoo_id=zoo["id"],
    query="database connection pooling"
)
```

## Workflow 6: Finding Similar Projects

**Goal**: Discover architecturally similar codebases.

```
# Find projects similar to FastAPI
similar = exa_find_similar(
    url="https://github.com/tiangolo/fastapi",
    num_results=20,
    exclude_source_domain=False
)

# Explore each similar project
for item in similar["items"]:
    print(f"Similar: {item['title']}")
    print(f"URL: {item['url']}")

    # If it's on GitHub, explore it
    if "github.com" in item["url"]:
        # Extract owner/repo from URL
        # Then use gh_get_contents to explore
```

## Best Practices

1. **Start with Semantic Search**: Use `exa_code_search` for discovery
2. **Organize as You Go**: Create zoos/tasks before committing examples
3. **Use Descriptive Tags**: Makes searching later much easier
4. **Fetch Full Files**: Use `fetch_full=True` when committing from snippets
5. **Export Regularly**: Back up your zoos with `zoo_export_json`
6. **Search Before Adding**: Use `zoo_search_examples` to avoid duplicates
7. **Keep Metadata Rich**: Good descriptions = better search results later
""",

        "tools": """
# Complete Tool Reference

## Discovery Tools (12)

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `gh_search_repos` | Search repositories | q, sort, order, per_page |
| `gh_search_code` | Search code files | q, per_page, page |
| `gh_get_contents` | Get file/dir contents | owner, repo, path, ref |
| `gh_get_archive` | Download repo archive | owner, repo, ref, format |
| `gh_releases` | Get release notes | owner, repo, limit |
| `gh_issues_with_code` | Find issues with code | owner, repo, q, limit |
| `exa_search` | Semantic web search | query, search_type, num_results |
| `exa_code_search` | Semantic code search | query, num_results |
| `exa_find_similar` | Find similar pages | url, num_results |
| `grep_search` | Regex pattern search | query, language, limit |
| `libsio_dependents` | Find package users | package, ecosystem, limit |
| `so_accepted` | Stack Overflow answers | q, tags, limit |

## Zoo Management Tools (32)

### Zoo CRUD (6)
- `zoo_create(name, description, tags?)`
- `zoo_list()`
- `zoo_get(zoo_id)`
- `zoo_update(zoo_id, ...)`
- `zoo_delete(zoo_id)`
- `zoo_search(query)`

### Task CRUD (5)
- `task_create(zoo_id, name, description, tags?)`
- `task_list(zoo_id, status_filter?)`
- `task_get(zoo_id, task_id, include_examples?)`
- `task_update(zoo_id, task_id, ...)`
- `task_delete(zoo_id, task_id)`

### Example Management (10)
- `example_commit_from_url(...)`
- `example_commit_from_search_result(...)`
- `example_commit_from_content(...)`
- `example_list(zoo_id, task_id, ...)`
- `example_get_meta(zoo_id, task_id, example_id)`
- `example_get_content(zoo_id, task_id, example_id, filename?)`
- `example_get_file_map(zoo_id, task_id, example_id)`
- `example_update_meta(...)`
- `example_add_file(...)`
- `example_delete(...)`

### Query Tools (6)
- `zoo_grep(zoo_id, pattern, ...)`
- `task_grep(zoo_id, task_id, pattern, ...)`
- `example_grep(zoo_id, task_id, example_id, pattern)`
- `zoo_search_examples(zoo_id, query)`
- `example_get_function(zoo_id, task_id, example_id, function_name)`
- `example_get_snippet(zoo_id, task_id, example_id, filename, start_line, end_line)`

### Export/Import (4)
- `zoo_export_json(zoo_id, include_content?, output_path?)`
- `zoo_export_markdown(zoo_id, include_code_samples?, output_path?)`
- `zoo_import_json(input_path)`
- `zoo_get_index(zoo_id, include_tasks?, include_examples?)`

### Help Tool (1)
- `zoo_help(topic?)` - This tool! Topics: overview, discovery, zoo, workflows, tools, quick-start
""",

        "quick-start": """
# Quick Start Guide

## Prerequisites

1. **API Keys** (at least GitHub recommended):
   - GitHub Token: https://github.com/settings/tokens
   - Exa Key: https://dashboard.exa.ai/api-keys (optional but recommended)
   - See `API_KEYS_GUIDE.md` for details

2. **Configuration**: Add keys to `.env` or MCP config

## 5-Minute Walkthrough

### Step 1: Search for Examples

```
# Semantic search for code
results = exa_code_search(
    query="fastapi websocket chat",
    num_results=10
)
```

### Step 2: Create a Zoo

```
zoo = zoo_create(
    name="My First Zoo",
    description="Learning FastAPI WebSockets",
    tags=["fastapi", "websocket", "learning"]
)

# Save the zoo ID!
zoo_id = zoo["id"]
```

### Step 3: Create a Task

```
task = task_create(
    zoo_id=zoo_id,
    name="Chat Examples",
    description="WebSocket chat implementations"
)

# Save the task ID!
task_id = task["id"]
```

### Step 4: Store an Example

```
example_commit_from_search_result(
    zoo_id=zoo_id,
    task_id=task_id,
    search_type="exa_code_search",
    result_data=results["items"][0],  # First result
    description="Production chat example",
    tags=["chat", "production"]
)
```

### Step 5: Search Your Zoo

```
# Search by text
matches = zoo_search_examples(
    zoo_id=zoo_id,
    query="chat"
)

# Search by code pattern
code_matches = task_grep(
    zoo_id=zoo_id,
    task_id=task_id,
    pattern="async def.*message"
)
```

### Step 6: Extract Code

```
# Get specific function
function_code = example_get_function(
    zoo_id=zoo_id,
    task_id=task_id,
    example_id=matches[0]["id"],
    function_name="handle_message"
)
```

## Next Steps

1. **Explore More Tools**: `zoo_help("discovery")` or `zoo_help("zoo")`
2. **Learn Workflows**: `zoo_help("workflows")`
3. **Read Full Docs**: See `README.md` and `ARCHITECTURE.md`
4. **Try Semantic Search**: `exa_code_search` is powerful!
5. **Build Your Library**: Create zoos for different projects/topics

## Common Questions

**Q: What's the difference between discovery and zoo tools?**
A: Discovery tools search external APIs. Zoo tools store and organize what you find.

**Q: Do I need API keys?**
A: GitHub token is highly recommended (5000 req/hr vs 60). Others are optional.

**Q: What's semantic search?**
A: Exa tools find code by meaning, not keywords. "Auth patterns" finds authentication even without those exact words.

**Q: Can I export my zoos?**
A: Yes! Use `zoo_export_json` to save as JSON, or `zoo_export_markdown` for documentation.

**Q: Where is data stored?**
A: In `./workspace` directory (or `ZOO_MCP_WORKSPACE` env var). JSON files, Git-friendly.

**Q: How do I get more help?**
A: Use `zoo_help(topic)` with topics: overview, discovery, zoo, workflows, tools, quick-start

## Tips for Success

1. ✅ **Use descriptive names** for zoos, tasks, and examples
2. ✅ **Tag everything** - makes searching easier later
3. ✅ **Start with semantic search** (`exa_code_search`) for discovery
4. ✅ **Fetch full files** when committing (use `fetch_full=True`)
5. ✅ **Export regularly** to back up your work
6. ✅ **Search before adding** to avoid duplicates
7. ✅ **Organize as you go** - create tasks to group related examples

Happy coding! 🚀
"""
    }

    # Normalize topic
    topic = topic.lower().strip()

    # Handle variations
    topic_map = {
        "start": "quick-start",
        "quickstart": "quick-start",
        "getting-started": "quick-start",
        "intro": "overview",
        "search": "discovery",
        "storage": "zoo",
        "examples": "workflows",
        "reference": "tools",
        "all": "tools"
    }

    topic = topic_map.get(topic, topic)

    # Get content or show available topics
    if topic in help_content:
        return {
            "topic": topic,
            "content": help_content[topic].strip(),
            "available_topics": list(help_content.keys())
        }
    else:
        return {
            "error": f"Unknown topic: {topic}",
            "available_topics": list(help_content.keys()),
            "usage": "zoo_help(topic) where topic is one of: " + ", ".join(help_content.keys())
        }