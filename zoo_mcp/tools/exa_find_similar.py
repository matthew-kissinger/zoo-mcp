from zoo_mcp.schemas import ExaFindSimilarInput, ExaFindSimilarOutput
from zoo_mcp.adapters.exa import ExaAdapter
from zoo_mcp.guards import truncate_to_budget


def exa_find_similar(adapter: ExaAdapter, input_data: ExaFindSimilarInput, max_bytes: int) -> ExaFindSimilarOutput:
    result = adapter.find_similar(
        url=input_data.url,
        num_results=input_data.num_results,
        exclude_source_domain=input_data.exclude_source_domain,
        include_domains=input_data.include_domains,
        exclude_domains=input_data.exclude_domains,
        start_published_date=input_data.start_published_date,
    )

    for item in result.get("items", []):
        if item.get("text"):
            item["text"] = truncate_to_budget(item["text"], max_bytes // 10)

    return ExaFindSimilarOutput(**result)