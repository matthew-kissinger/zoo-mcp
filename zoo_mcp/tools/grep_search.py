from zoo_mcp.schemas import GrepSearchInput, GrepSearchOutput
from zoo_mcp.adapters.grep import GrepAdapter
from zoo_mcp.guards import truncate_to_budget


def grep_search(adapter: GrepAdapter, input_data: GrepSearchInput, max_bytes: int) -> GrepSearchOutput:
    result = adapter.search(
        query=input_data.query,
        language=input_data.language,
        path=input_data.path,
        limit=input_data.limit,
    )

    for hit in result.get("hits", []):
        if hit.get("snippet"):
            hit["snippet"] = truncate_to_budget(hit["snippet"], max_bytes // 10)

    return GrepSearchOutput(**result)