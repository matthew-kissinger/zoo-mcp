from zoo_mcp.schemas import GHReleasesInput, GHReleasesOutput
from zoo_mcp.adapters.github import GitHubAdapter
from zoo_mcp.guards import truncate_to_budget


def gh_releases(
    adapter: GitHubAdapter, input_data: GHReleasesInput, max_bytes: int
) -> GHReleasesOutput:
    result = adapter.get_releases(owner=input_data.owner, repo=input_data.repo, limit=input_data.limit)

    for release in result.get("releases", []):
        if release.get("body"):
            release["body"] = truncate_to_budget(release["body"], max_bytes // len(result["releases"]))

    return GHReleasesOutput(**result)