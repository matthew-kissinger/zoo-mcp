from zoo_mcp.schemas import GHGetArchiveInput, GHGetArchiveOutput
from zoo_mcp.adapters.github import GitHubAdapter


def gh_get_archive(adapter: GitHubAdapter, input_data: GHGetArchiveInput) -> GHGetArchiveOutput:
    result = adapter.get_archive(
        owner=input_data.owner, repo=input_data.repo, ref=input_data.ref, format=input_data.format, save_to=input_data.save_to
    )
    return GHGetArchiveOutput(**result)