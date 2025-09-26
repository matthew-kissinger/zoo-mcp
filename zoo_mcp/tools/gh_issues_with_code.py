from zoo_mcp.schemas import GHIssuesWithCodeInput, GHIssuesWithCodeOutput
from zoo_mcp.adapters.github import GitHubAdapter
from zoo_mcp.guards import truncate_to_budget


def gh_issues_with_code(
    adapter: GitHubAdapter, input_data: GHIssuesWithCodeInput, max_bytes: int
) -> GHIssuesWithCodeOutput:
    result = adapter.search_issues_with_code(
        owner=input_data.owner, repo=input_data.repo, query=input_data.q, limit=input_data.limit
    )

    for item in result.get("items", []):
        for block in item.get("code_blocks", []):
            if block.get("text"):
                block["text"] = truncate_to_budget(block["text"], max_bytes // 10)

    return GHIssuesWithCodeOutput(**result)