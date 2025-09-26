import logging
from typing import Optional, Dict, Any
import requests

logger = logging.getLogger(__name__)


class LibrariesIOAdapter:
    BASE_URL = "https://libraries.io/api"
    TIMEOUT = 10

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()

    def get_dependents(self, package: str, ecosystem: str, limit: int = 50) -> Dict[str, Any]:
        if not self.api_key:
            logger.warning("Libraries.io API key not set, returning empty results")
            return {"dependents": []}

        url = f"{self.BASE_URL}/{ecosystem}/{package}/dependents"
        params = {"api_key": self.api_key, "per_page": min(limit, 100), "page": 1}

        try:
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            data = response.json()

            dependents = []
            items = data if isinstance(data, list) else []
            for item in items[:limit]:
                repo_url = item.get("repository_url")
                if repo_url and "github.com" in repo_url:
                    parts = repo_url.rstrip("/").split("/")
                    if len(parts) >= 2:
                        repo = f"{parts[-2]}/{parts[-1]}"
                        dependents.append({"repo": repo, "url": repo_url})

            return {"dependents": dependents}

        except requests.RequestException as e:
            logger.error(f"Libraries.io request failed: {e}")
            return {"dependents": []}