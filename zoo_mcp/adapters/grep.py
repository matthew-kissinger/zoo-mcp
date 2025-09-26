import logging
import re
from typing import Optional, List, Dict, Any
import requests

logger = logging.getLogger(__name__)


class GrepAdapter:
    TIMEOUT = 10

    def __init__(self, api_url: str, api_key: Optional[str] = None):
        self.api_url = api_url
        self.api_key = api_key
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})

    def search(
        self,
        query: str,
        language: Optional[str] = None,
        path: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        params = {"q": query, "limit": limit}

        if language:
            params["lang"] = language
        if path:
            params["path"] = path

        try:
            response = self.session.get(self.api_url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()

            hits = []
            for item in data.get("hits", {}).get("hits", [])[:limit]:
                repo = item.get("repo", "unknown/unknown")
                path = item.get("path", "")
                content = item.get("content", {})
                snippet_html = content.get("snippet", "")

                # Strip HTML tags from snippet
                snippet = re.sub(r'<[^>]+>', '', snippet_html)
                snippet = re.sub(r'\s+', ' ', snippet).strip()

                hits.append(
                    {
                        "repo": repo,
                        "ref": item.get("branch", "main"),
                        "path": path,
                        "snippet": snippet,
                        "line_start": 0,
                        "line_end": 0,
                        "url": f"https://github.com/{repo}/blob/{item.get('branch', 'main')}/{path}",
                    }
                )

            return {"hits": hits}

        except requests.RequestException as e:
            logger.error(f"Grep.app search failed: {e}")
            return {"hits": []}