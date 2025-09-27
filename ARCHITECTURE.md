# Zoo MCP Architecture

> **Agent Map**: Complete codebase structure for AI coding agents

This document provides a comprehensive overview of Zoo MCP's architecture, designed to help AI agents navigate and understand the codebase.

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Directory Structure](#directory-structure)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [API Adapters](#api-adapters)
6. [Tool System](#tool-system)
7. [Storage System](#storage-system)
8. [Extension Points](#extension-points)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Client (Claude)                     │
│                    (sends tool requests)                     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastMCP Server                          │
│                    (zoo_mcp/server.py)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Tool Registry: 44 MCP Tools                           │ │
│  │  • 12 Discovery Tools (search APIs)                    │ │
│  │  • 32 Zoo Management Tools (storage)                   │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
┌───────────────┐  ┌──────────┐  ┌──────────────┐
│   Adapters    │  │  Tools   │  │   Storage    │
│ (API Clients) │  │ (Logic)  │  │ (Workspace)  │
└───────────────┘  └──────────┘  └──────────────┘
        │                │                │
        ▼                ▼                ▼
┌───────────────┐  ┌──────────┐  ┌──────────────┐
│ External APIs │  │ Schemas  │  │ File System  │
│ (GitHub, Exa) │  │(Pydantic)│  │   (JSON)     │
└───────────────┘  └──────────┘  └──────────────┘
```

---

## Directory Structure

```
zoo-mcp/
├── zoo_mcp/                    # Main package
│   ├── __init__.py
│   ├── server.py              # FastMCP server + tool registration
│   ├── schemas.py             # Pydantic models for all I/O
│   ├── guards.py              # Security: path validation, byte limits
│   ├── limits.py              # Rate limiting, backoff, caching
│   ├── analyzer.py            # Code analysis (language detection, AST)
│   ├── storage.py             # File system operations for zoo data
│   ├── zoo_models.py          # Zoo/Task/Example metadata models
│   │
│   ├── adapters/              # External API clients
│   │   ├── __init__.py
│   │   ├── github.py         # GitHub REST API adapter
│   │   ├── exa.py            # Exa semantic search adapter
│   │   ├── grep.py           # Grep.app regex search adapter
│   │   ├── librariesio.py    # Libraries.io dependents adapter
│   │   ├── stackexchange.py  # Stack Exchange API adapter
│   │   └── example_committer.py  # Commit examples to storage
│   │
│   └── tools/                 # MCP tool implementations
│       ├── __init__.py
│       ├── gh_search_repos.py
│       ├── gh_search_code.py
│       ├── gh_get_contents.py
│       ├── gh_get_archive.py
│       ├── gh_releases.py
│       ├── gh_issues_with_code.py
│       ├── exa_search.py
│       ├── exa_code_search.py
│       ├── exa_find_similar.py
│       ├── grep_search.py
│       ├── libsio_dependents.py
│       ├── so_accepted.py
│       ├── zoo_crud.py        # Zoo CRUD operations
│       ├── task_crud.py       # Task CRUD operations
│       ├── example_crud.py    # Example CRUD operations
│       ├── zoo_query.py       # Search/grep stored examples
│       └── zoo_export.py      # Export/import zoo data
│
├── tests/                      # Test suite
│   ├── test_adapters.py
│   ├── test_guards.py
│   ├── test_limits.py
│   └── test_schemas.py
│
├── workspace/                  # Zoo storage (gitignored)
│   └── {zoo_id}/
│       ├── zoo.json           # Zoo metadata
│       └── {task_id}/
│           ├── task.json      # Task metadata
│           └── examples/
│               └── {example_id}/
│                   ├── meta.json        # Example metadata
│                   └── source_files/    # Actual code files
│
├── .env.example               # Environment variables template
├── .env.local                 # Your local config (gitignored)
├── .gitignore
├── README.md                  # Main documentation
├── API_KEYS_GUIDE.md         # How to obtain API keys
├── ARCHITECTURE.md           # This file
└── pyproject.toml            # Package configuration
```

---

## Core Components

### 1. `server.py` - MCP Server Entry Point

**Purpose**: FastMCP server that registers all 44 tools and initializes adapters.

**Key responsibilities**:
- Load environment variables
- Initialize API adapters (GitHub, Exa, Grep, Libraries.io, Stack Exchange)
- Register 44 MCP tools with FastMCP
- Handle STDIO/WebSocket transport modes

**Key code**:
```python
mcp = FastMCP("zoo-mcp")

# Initialize adapters
github_adapter = GitHubAdapter(token=GITHUB_TOKEN, workspace=WORKSPACE_PATH)
exa_adapter = ExaAdapter(api_key=EXA_API_KEY)
# ... other adapters

# Register tools
@mcp.tool()
def gh_search_repos(q: str, ...) -> dict:
    # Tool implementation
```

---

### 2. `schemas.py` - Pydantic Models

**Purpose**: Type-safe input/output schemas for all tools using Pydantic.

**Key schemas**:
```python
# Input schemas
class GHSearchReposInput(BaseModel):
    q: str
    sort: Optional[Literal["stars", "updated"]]
    per_page: Optional[int] = Field(default=50, le=100)

# Output schemas
class GHSearchReposOutput(BaseModel):
    items: List[RepoItem]
    rate: RateLimit

# Storage schemas
class ZooMetadata(BaseModel):
    id: str
    name: str
    description: str
    tags: List[str]
    created_at: str
```

**Naming convention**:
- Input: `{Tool}Input`
- Output: `{Tool}Output`
- Models: `{Entity}` (e.g., `RepoItem`, `ExampleMetadata`)

---

### 3. `guards.py` - Security Layer

**Purpose**: Protect against malicious inputs and enforce safety constraints.

**Key functions**:
```python
def safe_path_join(base: Path, user_input: str) -> Path:
    """Prevent path traversal attacks"""

def truncate_to_budget(text: str, max_bytes: int) -> str:
    """Enforce byte budgets"""

def parse_org_allowlist(csv: str) -> set:
    """Parse organization allowlist"""

def ensure_workspace(path: str) -> Path:
    """Validate and create workspace directory"""
```

**Security features**:
- Path traversal protection
- Byte budget enforcement
- Domain allowlisting
- No code execution

---

### 4. `limits.py` - Rate Limiting

**Purpose**: Handle API rate limits with exponential backoff and caching.

**Key features**:
```python
class RateLimitError(Exception): pass

def handle_rate_limit_headers(response) -> Optional[int]:
    """Check rate limit headers, return wait time if exceeded"""

def parse_rate_limit(response) -> dict:
    """Extract rate limit info from response"""

class PageCache:
    """15-minute TTL cache for API responses"""
```

**Behavior**:
- Exponential backoff with jitter
- Respects `Retry-After` and `X-RateLimit-*` headers
- 15-minute self-cleaning cache
- Surfaces rate limit info in tool outputs

---

### 5. `analyzer.py` - Code Analysis

**Purpose**: Analyze code files to extract metadata and structure.

**Key functions**:
```python
def analyze_file(filename: str, content: str, path: str) -> FileMetadata:
    """
    Extract:
    - Language detection
    - Function/class definitions
    - Import statements
    - Key concepts
    - Line count
    - File size
    """
```

**Detection capabilities**:
- Language detection (40+ languages)
- Function/class extraction (Python, JavaScript, TypeScript, Rust, Go)
- Import analysis
- Key concept identification

---

### 6. `storage.py` - File System Operations

**Purpose**: Abstract file system operations for zoo storage.

**Key functions**:
```python
def get_zoo_path(workspace: Path, zoo_id: str) -> Path
def get_task_path(workspace: Path, zoo_id: str, task_id: str) -> Path
def get_example_path(...) -> Path

def load_json(path: Path) -> dict
def save_json(path: Path, data: dict)

def generate_id(prefix: str) -> str  # e.g., "zoo_abc123"
def list_subdirs(path: Path) -> List[Path]
def delete_directory(path: Path)
```

**Storage structure**:
```
workspace/
└── {zoo_id}/
    ├── zoo.json                 # ZooMetadata
    └── {task_id}/
        ├── task.json           # TaskMetadata
        └── examples/
            └── {example_id}/
                ├── meta.json   # ExampleMetadata
                └── source_files/
                    ├── code.py
                    └── README.md
```

---

### 7. `zoo_models.py` - Storage Models

**Purpose**: Pydantic models for persisted zoo data.

**Key models**:
```python
class ZooMetadata(BaseModel):
    id: str
    name: str
    description: str
    tags: List[str]
    task_count: int
    example_count: int
    created_at: str
    updated_at: str

class TaskMetadata(BaseModel):
    id: str
    zoo_id: str
    name: str
    description: str
    tags: List[str]
    status: str  # "active", "archived"
    example_count: int
    created_at: str
    updated_at: str

class ExampleMetadata(BaseModel):
    id: str
    task_id: str
    source_type: str  # "github", "exa", "grep", etc.
    source_tool: str  # "gh_search_code", "exa_code_search", etc.
    source_url: str
    repo: Optional[str]
    ref: Optional[str]
    description: str
    tags: List[str]
    language: Optional[str]
    files: List[FileMetadata]
    stats: dict
    created_at: str
    updated_at: str
```

---

## Data Flow

### Discovery Flow (Search → Result)

```
1. User calls tool via MCP
   ↓
2. server.py routes to tool function
   ↓
3. Tool function validates input (Pydantic schema)
   ↓
4. Tool calls adapter method
   ↓
5. Adapter makes HTTP request to API
   ↓
6. Adapter parses response
   ↓
7. guards.py truncates to byte budget
   ↓
8. Tool returns Pydantic output schema
   ↓
9. FastMCP serializes to JSON
   ↓
10. MCP client receives result
```

**Example**:
```python
# User request
exa_code_search(query="fastapi websocket", num_results=5)

# Flow
server.py::exa_code_search()
  → tools/exa_code_search.py::exa_code_search()
    → adapters/exa.py::ExaAdapter.search_code()
      → HTTP POST to api.exa.ai
      → Parse JSON response
    → guards.py::truncate_to_budget()
  → Return ExaCodeSearchOutput
→ MCP client receives JSON
```

---

### Storage Flow (Search → Commit → Store)

```
1. User searches with discovery tool
   ↓
2. User calls example_commit_from_search_result()
   ↓
3. Tool determines search type
   ↓
4. Routes to appropriate committer function
   ↓
5. Committer creates example structure:
   - Generate example ID
   - Create directories
   - Fetch full file if needed (GitHub)
   ↓
6. analyzer.py analyzes each file
   ↓
7. storage.py saves files and metadata
   ↓
8. Updates zoo/task counters
   ↓
9. Returns ExampleMetadata
```

**Example**:
```python
# User searches
result = exa_code_search("fastapi auth")

# User commits
example_commit_from_search_result(
    zoo_id="my-zoo",
    task_id="auth-patterns",
    search_type="exa_code_search",
    result_data=result["items"][0]
)

# Flow
tools/example_crud.py::example_commit_from_search_result()
  → adapters/example_committer.py::commit_from_exa_code_search()
    → storage.py::get_task_path()
    → _create_example_structure()
    → adapters/github.py::get_contents() # if fetch_full=True
    → analyzer.py::analyze_file()
    → storage.py::save_json()
    → _finalize_example()
  → Return ExampleMetadata
```

---

## API Adapters

### Adapter Pattern

All adapters follow a consistent pattern:

```python
class ExampleAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def method_name(self, param: str) -> Dict[str, Any]:
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse and return standardized format
            return {
                "items": [...],
                "metadata": {...}
            }
        except Exception as e:
            logger.error(f"API call failed: {e}")
            return {"items": [], "error": str(e)}
```

---

### GitHub Adapter (`adapters/github.py`)

**Methods**:
- `search_repos(query, sort, order, per_page, page)` → List[RepoItem]
- `search_code(query, per_page, page)` → List[CodeItem]
- `get_contents(owner, repo, path, ref)` → ContentItem | List[ContentItem]
- `get_archive(owner, repo, ref, format)` → archive_path
- `get_releases(owner, repo, limit)` → List[ReleaseItem]
- `search_issues_with_code(owner, repo, query, limit)` → List[IssueWithCode]

**Features**:
- Bearer token auth for `github_pat_*` tokens
- Rate limit handling
- 15-minute page cache
- Workspace management for archives

---

### Exa Adapter (`adapters/exa.py`)

**Methods**:
- `search(query, search_type, num_results, ...)` → List[ExaResult]
- `search_code(query, num_results, ...)` → List[ExaResult]
- `find_similar(url, num_results, ...)` → List[ExaResult]

**Features**:
- Neural/semantic search
- Searches 1B+ webpages
- Auto-extracts GitHub repo/path from URLs
- Returns dense, relevant context

---

### Grep Adapter (`adapters/grep.py`)

**Methods**:
- `search(query, language, path, limit)` → List[GrepHit]

**Features**:
- Regex pattern matching
- Cross-repo search
- HTML stripping from snippets

---

### Libraries.io Adapter (`adapters/librariesio.py`)

**Methods**:
- `get_dependents(package, ecosystem, limit)` → List[DependentRepo]

**Features**:
- Find repos using a package
- Supports multiple ecosystems (npm, cargo, pip, etc.)

---

### Stack Exchange Adapter (`adapters/stackexchange.py`)

**Methods**:
- `search_accepted_answers(query, tags, limit)` → List[SOAnswer]

**Features**:
- Finds accepted answers only
- Extracts code blocks from markdown
- Language detection for code blocks

---

### Example Committer (`adapters/example_committer.py`)

**Purpose**: Unified interface for committing examples from any search source.

**Methods**:
```python
def commit_from_gh_search_code(...)
def commit_from_grep_search(...)
def commit_from_exa_code_search(...)
def commit_from_exa_search(...)
def commit_from_so_accepted(...)
def commit_from_gh_issues(...)
def commit_from_url(...)
def commit_from_content(...)
```

**Pattern**: Each method follows the same flow:
1. Create example structure
2. Fetch/process code
3. Analyze files
4. Save metadata
5. Update counters

---

## Tool System

### Tool Categories

**Discovery Tools (12)**:
1. `gh_search_repos` - Search GitHub repositories
2. `gh_search_code` - Search code files
3. `gh_get_contents` - Get file/directory contents
4. `gh_get_archive` - Download repo archive
5. `gh_releases` - Get release notes
6. `gh_issues_with_code` - Find issues with code
7. `exa_search` - Semantic web search
8. `exa_code_search` - Semantic code search
9. `exa_find_similar` - Find similar pages
10. `grep_search` - Regex code search
11. `libsio_dependents` - Find package dependents
12. `so_accepted` - Stack Overflow answers

**Zoo Management Tools (32)**:
- Zoo CRUD (6): create, list, get, update, delete, search
- Task CRUD (5): create, list, get, update, delete
- Example CRUD (10): commit (3 types), list, get_meta, get_content, get_file_map, update_meta, add_file, delete
- Query Tools (6): zoo_grep, task_grep, example_grep, search_examples, get_function, get_snippet
- Export/Import (4): export_json, export_markdown, import_json, get_index

---

### Tool Implementation Pattern

All tools follow this structure:

```python
# In server.py
@mcp.tool()
def tool_name(param1: str, param2: int = 10) -> dict:
    """Tool description for MCP"""
    from zoo_mcp.tools.tool_module import tool_function

    # Validate input
    input_data = ToolInput(param1=param1, param2=param2)

    # Call tool function
    result = tool_function(adapter, input_data, MAX_RETURN_BYTES)

    # Return as dict
    return result.model_dump()

# In tools/tool_module.py
def tool_function(adapter: Adapter, input: ToolInput, max_bytes: int) -> ToolOutput:
    # 1. Call adapter method
    raw_result = adapter.method(...)

    # 2. Apply guards/limits
    processed = truncate_to_budget(raw_result, max_bytes)

    # 3. Return Pydantic model
    return ToolOutput(**processed)
```

---

## Extension Points

### Adding a New API Adapter

1. **Create adapter** in `zoo_mcp/adapters/new_api.py`:
   ```python
   class NewAPIAdapter:
       def __init__(self, api_key: str):
           self.api_key = api_key

       def search(self, query: str) -> dict:
           # Implementation
   ```

2. **Add schemas** in `zoo_mcp/schemas.py`:
   ```python
   class NewAPIInput(BaseModel):
       query: str

   class NewAPIOutput(BaseModel):
       items: List[ResultItem]
   ```

3. **Create tool** in `zoo_mcp/tools/new_api_search.py`:
   ```python
   def new_api_search(adapter, input, max_bytes):
       result = adapter.search(input.query)
       return NewAPIOutput(**result)
   ```

4. **Register tool** in `zoo_mcp/server.py`:
   ```python
   new_api_adapter = NewAPIAdapter(os.getenv("NEW_API_KEY"))

   @mcp.tool()
   def new_api_search(query: str) -> dict:
       from zoo_mcp.tools.new_api_search import new_api_search as tool_func
       input_data = NewAPIInput(query=query)
       result = tool_func(new_api_adapter, input_data, MAX_RETURN_BYTES)
       return result.model_dump()
   ```

5. **Add to example_committer** if you want storage support:
   ```python
   def commit_from_new_api(workspace, zoo_id, task_id, result, description, tags):
       # Implementation
   ```

---

### Adding a New Tool

1. **Define schemas** in `schemas.py`
2. **Implement tool function** in `tools/my_tool.py`
3. **Register with FastMCP** in `server.py`
4. **Update README.md** documentation

---

## Key Design Decisions

### Why Pydantic?
- Type safety
- Automatic validation
- Easy serialization to/from JSON
- IDE autocomplete support

### Why FastMCP?
- Built for MCP protocol
- Automatic tool registration
- Handles transport (STDIO/WebSocket)
- Minimal boilerplate

### Why File System Storage?
- Simple, no database needed
- Git-friendly (JSON files)
- Easy backup/export
- Human-readable

### Why Adapters?
- Separate concerns (API client vs tool logic)
- Easy to test
- Reusable across multiple tools
- Easier to add new APIs

### Why Guards?
- Security: prevent path traversal, code execution
- Stability: enforce byte budgets, prevent OOM
- Compliance: domain allowlisting

---

## Performance Considerations

**Caching**:
- 15-minute TTL page cache for GitHub API
- Reduces redundant API calls
- Self-cleaning (no memory leaks)

**Byte Budgets**:
- Default: 300KB max response size
- Configurable via `ZOO_MCP_MAX_RETURN_BYTES`
- Prevents large responses from overwhelming MCP clients

**Rate Limiting**:
- Exponential backoff with jitter
- Respects API rate limit headers
- Surfaces rate limit info to users

**File System**:
- Lazy loading: metadata loaded on demand
- Incremental counters: O(1) counter updates
- No database overhead

---

## Testing

**Test Coverage**:
- `tests/test_adapters.py` - API adapter unit tests
- `tests/test_guards.py` - Security validation tests
- `tests/test_limits.py` - Rate limiting tests
- `tests/test_schemas.py` - Pydantic schema validation

**Running Tests**:
```bash
pytest                    # All tests
pytest -v                # Verbose
pytest tests/test_guards.py  # Specific file
pytest --cov=zoo_mcp     # With coverage
```

---

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GITHUB_TOKEN` | Recommended | None | GitHub API access (5000 req/hr vs 60) |
| `EXA_API_KEY` | Recommended | None | Exa semantic search |
| `LIBRARIESIO_API_KEY` | Recommended | None | Package dependent search |
| `GREP_API_KEY` | Optional | None | Grep.app API (public works without) |
| `GREP_API_URL` | Optional | `https://grep.app/api/search` | Grep.app endpoint |
| `STACKEXCHANGE_KEY` | Optional | None | Stack Overflow (10k req/day vs 300) |
| `ZOO_MCP_WORKSPACE` | Optional | `./workspace` | Storage directory |
| `ZOO_MCP_MAX_RETURN_BYTES` | Optional | `300000` | Max response size |
| `ORG_ALLOWLIST` | Optional | None | CSV of allowed GitHub orgs |

---

## Security Model

**Threats Mitigated**:
1. **Path Traversal**: `safe_path_join()` validates all file paths
2. **Code Execution**: No `eval()`, `exec()`, or subprocess calls
3. **Memory Exhaustion**: Byte budgets prevent large responses
4. **Malicious URLs**: Domain allowlisting for GitHub/GitLab only
5. **API Key Exposure**: `.env` files gitignored

**Threats NOT Mitigated**:
- Malicious code in fetched files (user responsibility)
- API rate limit exhaustion (soft limit via backoff)

---

## Contributing

When contributing:
1. Follow existing patterns (adapter → tool → registration)
2. Add Pydantic schemas for all inputs/outputs
3. Include tests for new functionality
4. Update documentation (README.md, ARCHITECTURE.md)
5. Ensure `.env.local` is not committed

---

## References

- **FastMCP**: https://github.com/jlowin/fastmcp
- **Model Context Protocol**: https://modelcontextprotocol.io/
- **Pydantic**: https://docs.pydantic.dev/
- **GitHub REST API**: https://docs.github.com/en/rest
- **Exa API**: https://docs.exa.ai/

---

**Last Updated**: 2025-09-27
**Version**: 1.1.0 (with Exa integration)