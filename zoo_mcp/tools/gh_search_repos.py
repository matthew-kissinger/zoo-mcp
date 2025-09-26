import logging
from zoo_mcp.schemas import GHSearchReposInput, GHSearchReposOutput
from zoo_mcp.adapters.github import GitHubAdapter
from zoo_mcp.guards import truncate_to_budget, validate_org_allowlist

logger = logging.getLogger(__name__)


def gh_search_repos(
    adapter: GitHubAdapter,
    input_data: GHSearchReposInput,
    max_bytes: int,
    org_allowlist: list = None,
) -> GHSearchReposOutput:
    result = adapter.search_repos(
        query=input_data.q,
        sort=input_data.sort,
        order=input_data.order,
        per_page=input_data.per_page,
        page=input_data.page,
        time_windows=input_data.time_windows,
    )

    if org_allowlist:
        filtered_items = []
        for item in result["items"]:
            org = item["full_name"].split("/")[0]
            if validate_org_allowlist(org, org_allowlist):
                filtered_items.append(item)
        result["items"] = filtered_items

    output = GHSearchReposOutput(**result)
    return output