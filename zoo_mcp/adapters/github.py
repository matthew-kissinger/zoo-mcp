import time
import re
import base64
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import requests

from zoo_mcp.limits import (
    RateLimitError,
    handle_rate_limit_headers,
    parse_rate_limit,
    page_cache,
)
from zoo_mcp.guards import safe_path_join, SecurityError

logger = logging.getLogger(__name__)


class GitHubAdapter:
    BASE_URL = "https://api.github.com"
    TIMEOUT = 10

    def __init__(self, token: Optional[str] = None, workspace: Path = Path("./workspace")):
        self.token = token
        self.workspace = workspace
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
        self.session.headers.update({"Accept": "application/vnd.github+json"})

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.TIMEOUT)
        response = self.session.request(method, url, **kwargs)

        wait_time = handle_rate_limit_headers(response)
        if wait_time is not None:
            logger.warning(f"Rate limit hit, waiting {wait_time}s")
            time.sleep(wait_time)
            raise RateLimitError(f"Rate limit exceeded, retry after {wait_time}s")

        response.raise_for_status()
        return response

    def search_repos(
        self,
        query: str,
        sort: str = "best-match",
        order: str = "desc",
        per_page: int = 50,
        page: int = 1,
        time_windows: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        items = []
        rate_info = {"remaining": 0, "reset": 0}

        queries = [query]
        if time_windows:
            queries = [f"{query} pushed:{window}" for window in time_windows]

        for q in queries:
            params = {"q": q, "sort": sort, "order": order, "per_page": per_page, "page": page}
            cache_key = f"search_repos:{q}:{page}"

            cached = page_cache.get(cache_key)
            if cached:
                items.extend(cached["items"])
                continue

            response = self._request("GET", f"{self.BASE_URL}/search/repositories", params=params)
            data = response.json()

            rate_info = parse_rate_limit(response)

            repo_items = [
                {
                    "full_name": item["full_name"],
                    "html_url": item["html_url"],
                    "default_branch": item.get("default_branch", "main"),
                    "license": item.get("license", {}).get("spdx_id") if item.get("license") else None,
                    "stargazers_count": item["stargazers_count"],
                    "pushed_at": item["pushed_at"],
                }
                for item in data.get("items", [])
            ]

            page_cache.set(cache_key, {"items": repo_items})
            items.extend(repo_items)

        return {"items": items, "rate": rate_info}

    def search_code(self, query: str, per_page: int = 50, page: int = 1) -> Dict[str, Any]:
        params = {"q": query, "per_page": per_page, "page": page}
        cache_key = f"search_code:{query}:{page}"

        cached = page_cache.get(cache_key)
        if cached:
            return cached

        response = self._request("GET", f"{self.BASE_URL}/search/code", params=params)
        data = response.json()

        items = [
            {
                "repository": item["repository"]["full_name"],
                "path": item["path"],
                "html_url": item["html_url"],
            }
            for item in data.get("items", [])
        ]

        result = {"items": items, "rate": parse_rate_limit(response)}
        page_cache.set(cache_key, result)
        return result

    def get_contents(
        self, owner: str, repo: str, path: str, ref: Optional[str] = None, save_to: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {}
        if ref:
            params["ref"] = ref

        url = f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        response = self._request("GET", url, params=params)
        data = response.json()

        base_dir = Path(save_to).resolve() if save_to else self.workspace
        repo_folder = safe_path_join(base_dir, f"{owner}_{repo}")
        repo_folder.mkdir(parents=True, exist_ok=True)

        if isinstance(data, list):
            items = [
                {
                    "name": item["name"],
                    "path": item["path"],
                    "download_url": item.get("download_url"),
                    "size": item.get("size"),
                }
                for item in data
            ]
            return {"type": "dir", "items": items, "rate": parse_rate_limit(response)}
        else:
            content = None
            saved_path = None
            if data.get("encoding") == "base64" and data.get("content"):
                try:
                    content = base64.b64decode(data["content"]).decode("utf-8")
                    file_path = safe_path_join(repo_folder, data["path"])
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content, encoding="utf-8")
                    saved_path = str(file_path)
                except Exception as e:
                    logger.warning(f"Failed to decode or save content: {e}")

            items = [
                {
                    "name": data["name"],
                    "path": data["path"],
                    "download_url": data.get("download_url"),
                    "size": data.get("size"),
                    "content": content,
                    "saved_path": saved_path,
                }
            ]
            return {"type": "file", "items": items, "rate": parse_rate_limit(response)}

    def get_archive(
        self, owner: str, repo: str, ref: Optional[str] = None, format: str = "zipball", save_to: Optional[str] = None
    ) -> Dict[str, Any]:
        if ref is None:
            repo_url = f"{self.BASE_URL}/repos/{owner}/{repo}"
            repo_response = self._request("GET", repo_url)
            ref = repo_response.json().get("default_branch", "main")

        url = f"{self.BASE_URL}/repos/{owner}/{repo}/{format}/{ref}"
        response = self._request("GET", url, allow_redirects=True, stream=True)

        archive_name = f"{owner}_{repo}_{ref}.{'zip' if format == 'zipball' else 'tar.gz'}"
        base_dir = Path(save_to).resolve() if save_to else self.workspace
        archive_path = safe_path_join(base_dir, archive_name)

        total_bytes = 0
        with open(archive_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                total_bytes += len(chunk)

        return {"archive_path": str(archive_path), "bytes": total_bytes}

    def get_releases(self, owner: str, repo: str, limit: int = 5) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/releases"
        params = {"per_page": limit}
        response = self._request("GET", url, params=params)
        data = response.json()

        releases = [
            {
                "tag": item["tag_name"],
                "name": item.get("name", ""),
                "body": item.get("body", ""),
                "html_url": item["html_url"],
            }
            for item in data[:limit]
        ]

        return {"releases": releases, "rate": parse_rate_limit(response)}

    def search_issues_with_code(
        self, owner: str, repo: str, query: str, limit: int = 20
    ) -> Dict[str, Any]:
        search_query = f"repo:{owner}/{repo} {query}"
        params = {"q": search_query, "per_page": limit, "sort": "created", "order": "desc"}

        response = self._request("GET", f"{self.BASE_URL}/search/issues", params=params)
        data = response.json()

        items = []
        for item in data.get("items", [])[:limit]:
            code_blocks = self._extract_code_blocks(item.get("body", ""))
            if code_blocks:
                items.append(
                    {
                        "number": item["number"],
                        "title": item["title"],
                        "html_url": item["html_url"],
                        "code_blocks": code_blocks,
                    }
                )

        return {"items": items, "rate": parse_rate_limit(response)}

    def _extract_code_blocks(self, markdown: str) -> List[Dict[str, Any]]:
        pattern = r"```(\w+)?\n(.*?)```"
        matches = re.findall(pattern, markdown, re.DOTALL)
        return [{"lang": lang or None, "text": code.strip()} for lang, code in matches]