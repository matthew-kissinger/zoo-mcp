import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from zoo_mcp.adapters.github import GitHubAdapter
from zoo_mcp.adapters.grep import GrepAdapter
from zoo_mcp.adapters.librariesio import LibrariesIOAdapter
from zoo_mcp.adapters.stackexchange import StackExchangeAdapter
from zoo_mcp.adapters.exa import ExaAdapter


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

    @patch("zoo_mcp.adapters.stackexchange.requests.Session.get")
    def test_search_accepted_answers_success(self, mock_get):
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "items": [
                {
                    "title": "How to parse JSON in Python?",
                    "link": "https://stackoverflow.com/q/123",
                    "accepted_answer_id": 456,
                }
            ]
        }

        answer_response = Mock()
        answer_response.status_code = 200
        answer_response.json.return_value = {
            "items": [
                {
                    "body": "<pre><code>import json\ndata = json.loads(text)</code></pre>"
                }
            ]
        }

        mock_get.side_effect = [search_response, answer_response]

        adapter = StackExchangeAdapter()
        result = adapter.search_accepted_answers("parse JSON", limit=10)

        assert len(result["answers"]) == 1
        assert result["answers"][0]["question"] == "How to parse JSON in Python?"
        assert result["answers"][0]["answer_url"] == "https://stackoverflow.com/q/123"
        assert len(result["answers"][0]["code_blocks"]) == 1
        assert "import json" in result["answers"][0]["code_blocks"][0]["text"]
        assert result["answers"][0]["code_blocks"][0]["lang"] == "python"

    @patch("zoo_mcp.adapters.stackexchange.requests.Session.get")
    def test_search_accepted_answers_with_tags(self, mock_get):
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {"items": []}
        mock_get.return_value = search_response

        adapter = StackExchangeAdapter()
        adapter.search_accepted_answers("test query", tags=["python", "django"], limit=10)

        call_args = mock_get.call_args
        assert call_args[1]["params"]["tagged"] == "python;django"

    @patch("zoo_mcp.adapters.stackexchange.requests.Session.get")
    def test_search_accepted_answers_with_api_key(self, mock_get):
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {"items": []}
        mock_get.return_value = search_response

        adapter = StackExchangeAdapter(api_key="test_api_key")
        adapter.search_accepted_answers("test query", limit=10)

        call_args = mock_get.call_args
        assert call_args[1]["params"]["key"] == "test_api_key"

    @patch("zoo_mcp.adapters.stackexchange.requests.Session.get")
    def test_search_accepted_answers_no_accepted_answer(self, mock_get):
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {
            "items": [
                {
                    "title": "Question without accepted answer",
                    "link": "https://stackoverflow.com/q/789",
                },
                {
                    "title": "Question with accepted answer",
                    "link": "https://stackoverflow.com/q/123",
                    "accepted_answer_id": 456,
                },
            ]
        }

        answer_response = Mock()
        answer_response.status_code = 200
        answer_response.json.return_value = {
            "items": [
                {
                    "body": "<pre><code>function test() {}</code></pre>"
                }
            ]
        }

        mock_get.side_effect = [search_response, answer_response]

        adapter = StackExchangeAdapter()
        result = adapter.search_accepted_answers("test query", limit=10)

        assert len(result["answers"]) == 1
        assert result["answers"][0]["question"] == "Question with accepted answer"
        assert mock_get.call_count == 2

    @patch("zoo_mcp.adapters.stackexchange.requests.Session.get")
    def test_search_accepted_answers_request_exception(self, mock_get):
        mock_get.side_effect = requests.RequestException("Network error")

        adapter = StackExchangeAdapter()
        result = adapter.search_accepted_answers("test query", limit=10)

        assert result == {"answers": []}

    @patch("zoo_mcp.adapters.stackexchange.requests.Session.get")
    def test_search_accepted_answers_empty_results(self, mock_get):
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = {"items": []}
        mock_get.return_value = search_response

        adapter = StackExchangeAdapter()
        result = adapter.search_accepted_answers("test query", limit=10)

        assert result == {"answers": []}


class TestExaAdapter:
    def test_init_no_api_key(self):
        with pytest.raises(ValueError, match="Exa API key is required"):
            ExaAdapter(api_key="")

    def test_init_with_api_key(self):
        with patch("zoo_mcp.adapters.exa.Exa") as mock_exa:
            adapter = ExaAdapter(api_key="test_key")
            assert adapter.api_key == "test_key"
            mock_exa.assert_called_once_with(api_key="test_key")

    @patch("zoo_mcp.adapters.exa.Exa")
    def test_search(self, mock_exa_class):
        mock_client = Mock()
        mock_exa_class.return_value = mock_client

        mock_result = Mock()
        mock_result.autoprompt_string = "optimized query"
        mock_result.results = [
            Mock(
                title="Test Result",
                url="https://example.com",
                published_date="2024-01-01",
                author="Test Author",
                text="Test content",
                score=0.95,
            )
        ]
        mock_client.search_and_contents.return_value = mock_result

        adapter = ExaAdapter(api_key="test_key")
        result = adapter.search("test query", num_results=5)

        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Test Result"
        assert result["items"][0]["url"] == "https://example.com"
        assert result["items"][0]["text"] == "Test content"
        assert result["items"][0]["score"] == 0.95
        assert result["autoprompt_string"] == "optimized query"

        mock_client.search_and_contents.assert_called_once_with(
            "test query",
            type="auto",
            num_results=5,
            include_domains=None,
            exclude_domains=None,
            start_published_date=None,
            end_published_date=None,
            use_autoprompt=True,
            category=None,
            text=True,
        )

    @patch("zoo_mcp.adapters.exa.Exa")
    def test_search_code(self, mock_exa_class):
        mock_client = Mock()
        mock_exa_class.return_value = mock_client

        mock_result = Mock()
        mock_result.autoprompt_string = "code query"
        mock_result.results = [
            Mock(
                title="GitHub Result",
                url="https://github.com/user/repo/blob/main/src/file.py",
                published_date="2024-01-01",
                author="user",
                text="def example(): pass",
                score=0.9,
            )
        ]
        mock_client.search_and_contents.return_value = mock_result

        adapter = ExaAdapter(api_key="test_key")
        result = adapter.search_code("fastapi example", num_results=10)

        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "GitHub Result"
        assert result["items"][0]["repo"] == "user/repo"
        assert result["items"][0]["path"] == "src/file.py"
        assert result["items"][0]["ref"] == "main"
        assert result["autoprompt_string"] == "code query"

        mock_client.search_and_contents.assert_called_once()
        call_args = mock_client.search_and_contents.call_args
        assert call_args[0][0] == "fastapi example"
        assert call_args[1]["type"] == "neural"
        assert call_args[1]["num_results"] == 10
        assert "github.com" in call_args[1]["include_domains"]
        assert "stackoverflow.com" in call_args[1]["include_domains"]

    @patch("zoo_mcp.adapters.exa.Exa")
    def test_find_similar(self, mock_exa_class):
        mock_client = Mock()
        mock_exa_class.return_value = mock_client

        mock_result = Mock()
        mock_result.results = [
            Mock(
                title="Similar Page",
                url="https://example.org",
                published_date="2024-01-15",
                author="Author",
                text="Similar content",
                score=0.88,
            )
        ]
        mock_client.find_similar_and_contents.return_value = mock_result

        adapter = ExaAdapter(api_key="test_key")
        result = adapter.find_similar("https://example.com", num_results=5)

        assert len(result["items"]) == 1
        assert result["items"][0]["title"] == "Similar Page"
        assert result["items"][0]["url"] == "https://example.org"
        assert result["items"][0]["score"] == 0.88

        mock_client.find_similar_and_contents.assert_called_once_with(
            "https://example.com",
            num_results=5,
            exclude_source_domain=False,
            include_domains=None,
            exclude_domains=None,
            start_published_date=None,
            text=True,
        )

    @patch("zoo_mcp.adapters.exa.Exa")
    def test_search_error_handling(self, mock_exa_class):
        mock_client = Mock()
        mock_exa_class.return_value = mock_client
        mock_client.search_and_contents.side_effect = Exception("API Error")

        adapter = ExaAdapter(api_key="test_key")
        result = adapter.search("test query")

        assert result["items"] == []
        assert "error" in result
        assert "API Error" in result["error"]