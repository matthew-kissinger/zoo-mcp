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
from zoo_mcp.schemas import *

github_adapter = GitHubAdapter(token=GITHUB_TOKEN, workspace=WORKSPACE_PATH)
grep_adapter = GrepAdapter(api_url=GREP_API_URL, api_key=GREP_API_KEY)
libsio_adapter = LibrariesIOAdapter(api_key=LIBRARIESIO_API_KEY)
so_adapter = StackExchangeAdapter(api_key=STACKEXCHANGE_KEY)

logger.info(f"Zoo MCP initialized")
logger.info(f"Workspace: {WORKSPACE_PATH}")
logger.info(f"Max return bytes: {MAX_RETURN_BYTES}")
if ORG_ALLOWLIST:
    logger.info(f"Org allowlist: {ORG_ALLOWLIST}")


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