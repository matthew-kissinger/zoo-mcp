from zoo_mcp.schemas import LibsIODependentsInput, LibsIODependentsOutput
from zoo_mcp.adapters.librariesio import LibrariesIOAdapter


def libsio_dependents(adapter: LibrariesIOAdapter, input_data: LibsIODependentsInput) -> LibsIODependentsOutput:
    result = adapter.get_dependents(
        package=input_data.package, ecosystem=input_data.ecosystem, limit=input_data.limit
    )
    return LibsIODependentsOutput(**result)