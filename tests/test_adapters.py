import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from zoo_mcp.adapters.github import GitHubAdapter
from zoo_mcp.adapters.grep import GrepAdapter
from zoo_mcp.adapters.librariesio import LibrariesIOAdapter
from zoo_mcp.adapters.stackexchange import StackExchangeAdapter


@pytest.fixture
def tmp_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


class TestGitHubAdapter:
    def test_init(self, tmp_workspace):
        adapter = GitHubAdapter(token="test_token", workspace=tmp_workspace)
        assert adapter.token == "test_token"
        assert "Authorization" in adapter.session.headers

    @patch("zoo_mcp.adapters.github.requests.Session.request")
    def test_search_repos(self, mock_request, tmp_workspace):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"X-RateLimit-Remaining": "100", "X-RateLimit-Reset": "123"}
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "owner/repo",
                    "html_url": "https://github.com/owner/repo",
                    "default_branch": "main",
                    "license": {"spdx_id": "MIT"},
                    "stargazers_count": 100,
                    "pushed_at": "2024-01-01T00:00:00Z",
                }
            ]
        }
        mock_request.return_value = mock_response

        adapter = GitHubAdapter(workspace=tmp_workspace)
        result = adapter.search_repos("test query")

        assert len(result["items"]) == 1
        assert result["items"][0]["full_name"] == "owner/repo"
        assert "rate" in result

    def test_extract_code_blocks(self, tmp_workspace):
        adapter = GitHubAdapter(workspace=tmp_workspace)
        markdown = """
        Some text
        ```python
        def hello():
            print("world")
        ```
        More text
        ```js
        console.log("hi");
        ```
        """
        blocks = adapter._extract_code_blocks(markdown)
        assert len(blocks) == 2
        assert blocks[0]["lang"] == "python"
        assert "def hello" in blocks[0]["text"]


class TestGrepAdapter:
    @patch("zoo_mcp.adapters.grep.requests.Session.get")
    def test_search(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "content": {
                                "repo": {"raw": "owner/repo"},
                                "branch": {"raw": "main"},
                                "path": {"raw": "src/main.rs"},
                                "snippet": {"text": "use axum::Router;"},
                                "line_start": 10,
                                "line_end": 10,
                            }
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        adapter = GrepAdapter(api_url="https://test.com/search")
        result = adapter.search("use axum", language="Rust")

        assert len(result["hits"]) == 1
        assert result["hits"][0]["repo"] == "owner/repo"
        assert result["hits"][0]["path"] == "src/main.rs"


class TestLibrariesIOAdapter:
    @patch("zoo_mcp.adapters.librariesio.requests.Session.get")
    def test_get_dependents(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"repository_url": "https://github.com/owner/repo1"},
            {"repository_url": "https://github.com/owner/repo2"},
        ]
        mock_get.return_value = mock_response

        adapter = LibrariesIOAdapter(api_key="test_key")
        result = adapter.get_dependents("axios", "npm")

        assert len(result["dependents"]) == 2
        assert result["dependents"][0]["repo"] == "owner/repo1"

    def test_no_api_key(self):
        adapter = LibrariesIOAdapter()
        result = adapter.get_dependents("axios", "npm")
        assert result["dependents"] == []


class TestStackExchangeAdapter:
    def test_extract_code_blocks(self):
        adapter = StackExchangeAdapter()
        html = "<pre><code>def hello():\n    pass</code></pre>"
        blocks = adapter._extract_code_blocks(html)

        assert len(blocks) == 1
        assert "def hello" in blocks[0]["text"]

    def test_detect_language(self):
        adapter = StackExchangeAdapter()
        assert adapter._detect_language("def foo(): pass") == "python"
        assert adapter._detect_language("function foo() {}") == "javascript"
        assert adapter._detect_language("public class Foo {}") == "java"