from zoo_mcp.schemas import SOAcceptedInput, SOAcceptedOutput
from zoo_mcp.adapters.stackexchange import StackExchangeAdapter
from zoo_mcp.guards import truncate_to_budget


def so_accepted(adapter: StackExchangeAdapter, input_data: SOAcceptedInput, max_bytes: int) -> SOAcceptedOutput:
    result = adapter.search_accepted_answers(
        query=input_data.q, tags=input_data.tags, limit=input_data.limit
    )

    for answer in result.get("answers", []):
        for block in answer.get("code_blocks", []):
            if block.get("text"):
                block["text"] = truncate_to_budget(block["text"], max_bytes // 10)

    return SOAcceptedOutput(**result)