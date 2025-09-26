from zoo_mcp.schemas import GHSearchCodeInput, GHSearchCodeOutput
from zoo_mcp.adapters.github import GitHubAdapter


def gh_search_code(adapter: GitHubAdapter, input_data: GHSearchCodeInput) -> GHSearchCodeOutput:
    result = adapter.search_code(
        query=input_data.q, per_page=input_data.per_page, page=input_data.page
    )
    return GHSearchCodeOutput(**result)