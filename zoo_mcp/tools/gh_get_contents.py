from zoo_mcp.schemas import GHGetContentsInput, GHGetContentsOutput
from zoo_mcp.adapters.github import GitHubAdapter
from zoo_mcp.guards import truncate_to_budget


def gh_get_contents(
    adapter: GitHubAdapter, input_data: GHGetContentsInput, max_bytes: int
) -> GHGetContentsOutput:
    result = adapter.get_contents(
        owner=input_data.owner, repo=input_data.repo, path=input_data.path, ref=input_data.ref, save_to=input_data.save_to
    )

    for item in result.get("items", []):
        if item.get("content"):
            item["content"] = truncate_to_budget(item["content"], max_bytes)

    return GHGetContentsOutput(**result)