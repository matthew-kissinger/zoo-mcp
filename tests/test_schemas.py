import pytest
from zoo_mcp.schemas import (
    GHSearchReposInput,
    GHSearchCodeInput,
    GHGetContentsInput,
    GrepSearchInput,
    LibsIODependentsInput,
    SOAcceptedInput,
)


def test_gh_search_repos_input():
    input_data = GHSearchReposInput(q="fastapi websocket", sort="stars", order="desc")
    assert input_data.q == "fastapi websocket"
    assert input_data.sort == "stars"
    assert input_data.per_page == 50


def test_gh_search_code_input():
    input_data = GHSearchCodeInput(q="def main", per_page=30)
    assert input_data.q == "def main"
    assert input_data.per_page == 30


def test_gh_get_contents_input():
    input_data = GHGetContentsInput(owner="tokio-rs", repo="axum", path="examples/")
    assert input_data.owner == "tokio-rs"
    assert input_data.repo == "axum"
    assert input_data.path == "examples/"


def test_grep_search_input():
    input_data = GrepSearchInput(query="use axum", language="Rust", limit=100)
    assert input_data.query == "use axum"
    assert input_data.language == "Rust"
    assert input_data.limit == 100


def test_libsio_dependents_input():
    input_data = LibsIODependentsInput(package="axios", ecosystem="npm")
    assert input_data.package == "axios"
    assert input_data.ecosystem == "npm"


def test_so_accepted_input():
    input_data = SOAcceptedInput(q="fastapi", tags=["python", "fastapi"], limit=5)
    assert input_data.q == "fastapi"
    assert input_data.tags == ["python", "fastapi"]
    assert input_data.limit == 5