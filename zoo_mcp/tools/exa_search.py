from zoo_mcp.schemas import ExaSearchInput, ExaSearchOutput
from zoo_mcp.adapters.exa import ExaAdapter
from zoo_mcp.guards import truncate_to_budget


def exa_search(adapter: ExaAdapter, input_data: ExaSearchInput, max_bytes: int) -> ExaSearchOutput:
    result = adapter.search(
        query=input_data.query,
        search_type=input_data.search_type,
        num_results=input_data.num_results,
        include_domains=input_data.include_domains,
        exclude_domains=input_data.exclude_domains,
        start_published_date=input_data.start_published_date,
        end_published_date=input_data.end_published_date,
        use_autoprompt=input_data.use_autoprompt,
        category=input_data.category,
    )

    for item in result.get("items", []):
        if item.get("text"):
            item["text"] = truncate_to_budget(item["text"], max_bytes // 10)

    return ExaSearchOutput(**result)