from zoo_mcp.schemas import ExaCodeSearchInput, ExaCodeSearchOutput
from zoo_mcp.adapters.exa import ExaAdapter
from zoo_mcp.guards import truncate_to_budget


def exa_code_search(adapter: ExaAdapter, input_data: ExaCodeSearchInput, max_bytes: int) -> ExaCodeSearchOutput:
    result = adapter.search_code(
        query=input_data.query,
        num_results=input_data.num_results,
        include_domains=input_data.include_domains,
    )

    for item in result.get("items", []):
        if item.get("text"):
            item["text"] = truncate_to_budget(item["text"], max_bytes // 10)

    return ExaCodeSearchOutput(**result)