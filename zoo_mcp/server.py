import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)

mcp = FastMCP("zoo-mcp")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GREP_API_URL = os.getenv("GREP_API_URL", "https://grep.app/api/search")
GREP_API_KEY = os.getenv("GREP_API_KEY")
LIBRARIESIO_API_KEY = os.getenv("LIBRARIESIO_API_KEY")
STACKEXCHANGE_KEY = os.getenv("STACKEXCHANGE_KEY")
EXA_API_KEY = os.getenv("EXA_API_KEY")
ORG_ALLOWLIST_STR = os.getenv("ORG_ALLOWLIST")
WORKSPACE = os.getenv("ZOO_MCP_WORKSPACE", "./workspace")
MAX_RETURN_BYTES = int(os.getenv("ZOO_MCP_MAX_RETURN_BYTES", "300000"))

from zoo_mcp.guards import parse_org_allowlist, ensure_workspace

ORG_ALLOWLIST = parse_org_allowlist(ORG_ALLOWLIST_STR)
WORKSPACE_PATH = ensure_workspace(WORKSPACE)

from zoo_mcp.adapters.github import GitHubAdapter
from zoo_mcp.adapters.grep import GrepAdapter
from zoo_mcp.adapters.librariesio import LibrariesIOAdapter
from zoo_mcp.adapters.stackexchange import StackExchangeAdapter
from zoo_mcp.adapters.exa import ExaAdapter
from zoo_mcp.schemas import *

github_adapter = GitHubAdapter(token=GITHUB_TOKEN, workspace=WORKSPACE_PATH)
grep_adapter = GrepAdapter(api_url=GREP_API_URL, api_key=GREP_API_KEY)
libsio_adapter = LibrariesIOAdapter(api_key=LIBRARIESIO_API_KEY)
so_adapter = StackExchangeAdapter(api_key=STACKEXCHANGE_KEY)
exa_adapter = ExaAdapter(api_key=EXA_API_KEY) if EXA_API_KEY else None

logger.info(f"Zoo MCP initialized")
logger.info(f"Workspace: {WORKSPACE_PATH}")
logger.info(f"Max return bytes: {MAX_RETURN_BYTES}")
if ORG_ALLOWLIST:
    logger.info(f"Org allowlist: {ORG_ALLOWLIST}")


@mcp.tool()
def zoo_help(topic: str = "overview") -> dict:
    """
    Get comprehensive help about Zoo MCP tools and workflows.

    Available topics:
    - overview: General introduction and architecture
    - discovery: Discovery tools (search APIs)
    - zoo: Zoo management (persistent storage)
    - workflows: Common usage patterns with examples
    - tools: Complete tool reference
    - quick-start: Getting started guide
    """
    from zoo_mcp.tools.help import zoo_help as help_func

    return help_func(topic)


@mcp.tool()
def gh_search_repos(
    q: str,
    sort: str = "best-match",
    order: str = "desc",
    per_page: int = 50,
    page: int = 1,
    time_windows: list[str] = None,
) -> dict:
    """Search GitHub repositories with qualifiers (language, stars, pushed, topic, org)"""
    from zoo_mcp.tools.gh_search_repos import gh_search_repos as tool_func

    input_data = GHSearchReposInput(
        q=q, sort=sort, order=order, per_page=per_page, page=page, time_windows=time_windows
    )
    result = tool_func(github_adapter, input_data, MAX_RETURN_BYTES, ORG_ALLOWLIST)
    return result.model_dump()


@mcp.tool()
def gh_search_code(q: str, per_page: int = 50, page: int = 1) -> dict:
    """Find code files matching a query on GitHub"""
    from zoo_mcp.tools.gh_search_code import gh_search_code as tool_func

    input_data = GHSearchCodeInput(q=q, per_page=per_page, page=page)
    result = tool_func(github_adapter, input_data)
    return result.model_dump()


@mcp.tool()
def gh_get_contents(owner: str, repo: str, path: str, ref: str = None, save_to: str = None) -> dict:
    """Fetch file or directory listing from GitHub (README, docs, examples)"""
    from zoo_mcp.tools.gh_get_contents import gh_get_contents as tool_func

    input_data = GHGetContentsInput(owner=owner, repo=repo, path=path, ref=ref, save_to=save_to)
    result = tool_func(github_adapter, input_data, MAX_RETURN_BYTES)
    return result.model_dump()


@mcp.tool()
def gh_get_archive(owner: str, repo: str, ref: str = None, format: str = "zipball", save_to: str = None) -> dict:
    """Download repository snapshot without history (zipball/tarball)"""
    from zoo_mcp.tools.gh_get_archive import gh_get_archive as tool_func

    input_data = GHGetArchiveInput(owner=owner, repo=repo, ref=ref, format=format, save_to=save_to)
    result = tool_func(github_adapter, input_data)
    return result.model_dump()


@mcp.tool()
def gh_releases(owner: str, repo: str, limit: int = 5) -> dict:
    """Fetch recent release notes (migration hints, breaking changes)"""
    from zoo_mcp.tools.gh_releases import gh_releases as tool_func

    input_data = GHReleasesInput(owner=owner, repo=repo, limit=limit)
    result = tool_func(github_adapter, input_data, MAX_RETURN_BYTES)
    return result.model_dump()


@mcp.tool()
def gh_issues_with_code(owner: str, repo: str, q: str, limit: int = 20) -> dict:
    """Find issues/PRs containing fenced code blocks matching a regex/keyword"""
    from zoo_mcp.tools.gh_issues_with_code import gh_issues_with_code as tool_func

    input_data = GHIssuesWithCodeInput(owner=owner, repo=repo, q=q, limit=limit)
    result = tool_func(github_adapter, input_data, MAX_RETURN_BYTES)
    return result.model_dump()


@mcp.tool()
def grep_search(query: str, language: str = None, path: str = None, limit: int = 50) -> dict:
    """Cross-repo regex code search for definitions or call-sites (high signal)"""
    from zoo_mcp.tools.grep_search import grep_search as tool_func

    input_data = GrepSearchInput(query=query, language=language, path=path, limit=limit)
    result = tool_func(grep_adapter, input_data, MAX_RETURN_BYTES)
    return result.model_dump()


@mcp.tool()
def libsio_dependents(package: str, ecosystem: str, limit: int = 50) -> dict:
    """Find top dependents of a package (repos that use it)"""
    from zoo_mcp.tools.libsio_dependents import libsio_dependents as tool_func

    input_data = LibsIODependentsInput(package=package, ecosystem=ecosystem, limit=limit)
    result = tool_func(libsio_adapter, input_data)
    return result.model_dump()


@mcp.tool()
def so_accepted(q: str, tags: list[str] = None, limit: int = 10) -> dict:
    """Get accepted Stack Overflow answers with code blocks"""
    from zoo_mcp.tools.so_accepted import so_accepted as tool_func

    input_data = SOAcceptedInput(q=q, tags=tags, limit=limit)
    result = tool_func(so_adapter, input_data, MAX_RETURN_BYTES)
    return result.model_dump()


@mcp.tool()
def exa_search(
    query: str,
    search_type: str = "auto",
    num_results: int = 10,
    include_domains: list[str] = None,
    exclude_domains: list[str] = None,
    start_published_date: str = None,
    end_published_date: str = None,
    use_autoprompt: bool = True,
    category: str = None,
) -> dict:
    """Search the web using Exa's neural/keyword search (meaning-based search)"""
    if not exa_adapter:
        return {"items": [], "error": "EXA_API_KEY not configured"}

    from zoo_mcp.tools.exa_search import exa_search as tool_func

    input_data = ExaSearchInput(
        query=query,
        search_type=search_type,
        num_results=num_results,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        start_published_date=start_published_date,
        end_published_date=end_published_date,
        use_autoprompt=use_autoprompt,
        category=category,
    )
    result = tool_func(exa_adapter, input_data, MAX_RETURN_BYTES)
    return result.model_dump()


@mcp.tool()
def exa_code_search(
    query: str,
    num_results: int = 10,
    include_domains: list[str] = None,
) -> dict:
    """Search for code examples using Exa (optimized for GitHub, Stack Overflow, docs)"""
    if not exa_adapter:
        return {"items": [], "error": "EXA_API_KEY not configured"}

    from zoo_mcp.tools.exa_code_search import exa_code_search as tool_func

    input_data = ExaCodeSearchInput(
        query=query,
        num_results=num_results,
        include_domains=include_domains,
    )
    result = tool_func(exa_adapter, input_data, MAX_RETURN_BYTES)
    return result.model_dump()


@mcp.tool()
def exa_find_similar(
    url: str,
    num_results: int = 10,
    exclude_source_domain: bool = False,
    include_domains: list[str] = None,
    exclude_domains: list[str] = None,
    start_published_date: str = None,
) -> dict:
    """Find pages similar to a given URL using Exa's neural search"""
    if not exa_adapter:
        return {"items": [], "error": "EXA_API_KEY not configured"}

    from zoo_mcp.tools.exa_find_similar import exa_find_similar as tool_func

    input_data = ExaFindSimilarInput(
        url=url,
        num_results=num_results,
        exclude_source_domain=exclude_source_domain,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        start_published_date=start_published_date,
    )
    result = tool_func(exa_adapter, input_data, MAX_RETURN_BYTES)
    return result.model_dump()


@mcp.tool()
def zoo_create(name: str, description: str, tags: list[str] = None) -> dict:
    """Create a new code example zoo"""
    from zoo_mcp.tools.zoo_crud import zoo_create as tool_func

    zoo_meta = tool_func(WORKSPACE_PATH, name, description, tags)
    return zoo_meta.model_dump()


@mcp.tool()
def zoo_list() -> dict:
    """List all zoos with metadata"""
    from zoo_mcp.tools.zoo_crud import zoo_list as tool_func

    zoos = tool_func(WORKSPACE_PATH)
    return {"zoos": [z.model_dump() for z in zoos]}


@mcp.tool()
def zoo_get(zoo_id: str) -> dict:
    """Get zoo details with task list"""
    from zoo_mcp.tools.zoo_crud import zoo_get as tool_func

    result = tool_func(WORKSPACE_PATH, zoo_id)
    return {
        "zoo": result["zoo"].model_dump(),
        "tasks": [t.model_dump() for t in result["tasks"]]
    }


@mcp.tool()
def zoo_update(zoo_id: str, name: str = None, description: str = None, tags: list[str] = None) -> dict:
    """Update zoo metadata"""
    from zoo_mcp.tools.zoo_crud import zoo_update as tool_func

    zoo_meta = tool_func(WORKSPACE_PATH, zoo_id, name, description, tags)
    return zoo_meta.model_dump()


@mcp.tool()
def zoo_delete(zoo_id: str) -> dict:
    """Delete zoo and all contents"""
    from zoo_mcp.tools.zoo_crud import zoo_delete as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id)


@mcp.tool()
def zoo_search(query: str) -> dict:
    """Search zoos by name/description/tags"""
    from zoo_mcp.tools.zoo_crud import zoo_search as tool_func

    zoos = tool_func(WORKSPACE_PATH, query)
    return {"zoos": [z.model_dump() for z in zoos]}


@mcp.tool()
def task_create(zoo_id: str, name: str, description: str, tags: list[str] = None) -> dict:
    """Create a task in a zoo"""
    from zoo_mcp.tools.task_crud import task_create as tool_func

    task_meta = tool_func(WORKSPACE_PATH, zoo_id, name, description, tags)
    return task_meta.model_dump()


@mcp.tool()
def task_list(zoo_id: str, status_filter: str = None) -> dict:
    """List tasks in a zoo"""
    from zoo_mcp.tools.task_crud import task_list as tool_func

    tasks = tool_func(WORKSPACE_PATH, zoo_id, status_filter)
    return {"tasks": [t.model_dump() for t in tasks]}


@mcp.tool()
def task_get(zoo_id: str, task_id: str, include_examples: bool = False) -> dict:
    """Get task details with optional example list"""
    from zoo_mcp.tools.task_crud import task_get as tool_func

    result = tool_func(WORKSPACE_PATH, zoo_id, task_id, include_examples)
    return {
        "task": result["task"].model_dump(),
        "examples": result.get("examples", [])
    }


@mcp.tool()
def task_update(zoo_id: str, task_id: str, name: str = None, description: str = None, status: str = None, tags: list[str] = None) -> dict:
    """Update task metadata"""
    from zoo_mcp.tools.task_crud import task_update as tool_func

    task_meta = tool_func(WORKSPACE_PATH, zoo_id, task_id, name, description, status, tags)
    return task_meta.model_dump()


@mcp.tool()
def task_delete(zoo_id: str, task_id: str) -> dict:
    """Delete task and all examples"""
    from zoo_mcp.tools.task_crud import task_delete as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, task_id)


@mcp.tool()
def example_commit_from_url(zoo_id: str, task_id: str, url: str, description: str, tags: list[str] = None) -> dict:
    """Commit code example from GitHub URL"""
    from zoo_mcp.tools.example_crud import example_commit_from_url as tool_func

    example_meta = tool_func(WORKSPACE_PATH, github_adapter, zoo_id, task_id, url, description, tags)
    return example_meta.model_dump()


@mcp.tool()
def example_commit_from_content(zoo_id: str, task_id: str, filename: str, content: str, language: str, description: str, tags: list[str] = None, source_url: str = None) -> dict:
    """Commit code example from direct content"""
    from zoo_mcp.tools.example_crud import example_commit_from_content as tool_func

    example_meta = tool_func(WORKSPACE_PATH, zoo_id, task_id, filename, content, language, description, tags, source_url)
    return example_meta.model_dump()


@mcp.tool()
def example_commit_from_search_result(zoo_id: str, task_id: str, search_type: str, result_data: dict, description: str, tags: list[str] = None, fetch_full: bool = True) -> dict:
    """Commit example from search tool result (gh_search_code, grep_search, etc.)"""
    from zoo_mcp.tools.example_crud import example_commit_from_search_result as tool_func

    example_meta = tool_func(WORKSPACE_PATH, github_adapter, zoo_id, task_id, search_type, result_data, description, tags, fetch_full)
    return example_meta.model_dump()


@mcp.tool()
def example_list(zoo_id: str, task_id: str, language_filter: str = None, tag_filter: list[str] = None) -> dict:
    """List examples in task (metadata only, no code content)"""
    from zoo_mcp.tools.example_crud import example_list as tool_func

    examples = tool_func(WORKSPACE_PATH, zoo_id, task_id, language_filter, tag_filter)
    return {"examples": examples}


@mcp.tool()
def example_get_meta(zoo_id: str, task_id: str, example_id: str) -> dict:
    """Get example metadata without code content"""
    from zoo_mcp.tools.example_crud import example_get_meta as tool_func

    example_meta = tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id)
    return example_meta.model_dump()


@mcp.tool()
def example_get_content(zoo_id: str, task_id: str, example_id: str, filename: str = None) -> dict:
    """Get example source code content"""
    from zoo_mcp.tools.example_crud import example_get_content as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id, filename)


@mcp.tool()
def example_get_file_map(zoo_id: str, task_id: str, example_id: str) -> dict:
    """Get compact outline/map of example files"""
    from zoo_mcp.tools.example_crud import example_get_file_map as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id)


@mcp.tool()
def example_update_meta(zoo_id: str, task_id: str, example_id: str, description: str = None, tags: list[str] = None) -> dict:
    """Update example metadata"""
    from zoo_mcp.tools.example_crud import example_update_meta as tool_func

    example_meta = tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id, description, tags)
    return example_meta.model_dump()


@mcp.tool()
def example_add_file(zoo_id: str, task_id: str, example_id: str, filename: str, content: str) -> dict:
    """Add another file to existing example"""
    from zoo_mcp.tools.example_crud import example_add_file as tool_func

    example_meta = tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id, filename, content)
    return example_meta.model_dump()


@mcp.tool()
def example_delete(zoo_id: str, task_id: str, example_id: str) -> dict:
    """Delete example and all files"""
    from zoo_mcp.tools.example_crud import example_delete as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id)


@mcp.tool()
def zoo_grep(zoo_id: str, pattern: str, language: str = None, task_filter: str = None, flags: str = "i", max_results: int = 100) -> dict:
    """Grep (regex search) across all examples in zoo"""
    from zoo_mcp.tools.zoo_query import zoo_grep as tool_func

    matches = tool_func(WORKSPACE_PATH, zoo_id, pattern, language, task_filter, flags, max_results)
    return {"matches": matches, "total": len(matches)}


@mcp.tool()
def task_grep(zoo_id: str, task_id: str, pattern: str, language: str = None, flags: str = "i", max_results: int = 100) -> dict:
    """Grep (regex search) across all examples in task"""
    from zoo_mcp.tools.zoo_query import task_grep as tool_func

    matches = tool_func(WORKSPACE_PATH, zoo_id, task_id, pattern, language, flags, max_results)
    return {"matches": matches, "total": len(matches)}


@mcp.tool()
def example_grep(zoo_id: str, task_id: str, example_id: str, pattern: str, flags: str = "i") -> dict:
    """Grep (regex search) within single example"""
    from zoo_mcp.tools.zoo_query import example_grep as tool_func

    matches = tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id, pattern, flags)
    return {"matches": matches, "total": len(matches)}


@mcp.tool()
def zoo_search_examples(zoo_id: str, query: str) -> dict:
    """Search examples by description, tags, or filename"""
    from zoo_mcp.tools.zoo_query import zoo_search_examples as tool_func

    results = tool_func(WORKSPACE_PATH, zoo_id, query)
    return {"results": results, "total": len(results)}


@mcp.tool()
def example_get_function(zoo_id: str, task_id: str, example_id: str, function_name: str) -> dict:
    """Extract specific function code from example"""
    from zoo_mcp.tools.zoo_query import example_get_function as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id, function_name)


@mcp.tool()
def example_get_snippet(zoo_id: str, task_id: str, example_id: str, filename: str, start_line: int, end_line: int) -> dict:
    """Get specific line range from example file"""
    from zoo_mcp.tools.zoo_query import example_get_snippet as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, task_id, example_id, filename, start_line, end_line)


@mcp.tool()
def zoo_export_json(zoo_id: str, include_content: bool = True, output_path: str = None) -> dict:
    """Export zoo to JSON file"""
    from zoo_mcp.tools.zoo_export import zoo_export_json as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, include_content, output_path)


@mcp.tool()
def zoo_export_markdown(zoo_id: str, include_code_samples: bool = False, output_path: str = None) -> dict:
    """Export zoo to markdown documentation"""
    from zoo_mcp.tools.zoo_export import zoo_export_markdown as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, include_code_samples, output_path)


@mcp.tool()
def zoo_import_json(input_path: str) -> dict:
    """Import zoo from JSON file"""
    from zoo_mcp.tools.zoo_export import zoo_import_json as tool_func

    zoo_meta = tool_func(WORKSPACE_PATH, input_path)
    return zoo_meta.model_dump()


@mcp.tool()
def zoo_get_index(zoo_id: str, include_tasks: bool = True, include_examples: bool = True) -> dict:
    """Get compact index of zoo (for context-efficient browsing)"""
    from zoo_mcp.tools.zoo_export import zoo_get_index as tool_func

    return tool_func(WORKSPACE_PATH, zoo_id, include_tasks, include_examples)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Zoo MCP Server")
    parser.add_argument(
        "mode",
        choices=["stdio", "websocket"],
        default="stdio",
        nargs="?",
        help="Server mode (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="WebSocket host")
    parser.add_argument("--port", type=int, default=8080, help="WebSocket port")

    args = parser.parse_args()

    if args.mode == "websocket":
        logger.info(f"Starting WebSocket server on {args.host}:{args.port}")
        mcp.run(transport="sse", sse_path="/sse", host=args.host, port=args.port)
    else:
        logger.info("Starting STDIO server")
        mcp.run()


if __name__ == "__main__":
    main()