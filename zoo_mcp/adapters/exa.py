import logging
from typing import Optional, List, Dict, Any
from exa_py import Exa

logger = logging.getLogger(__name__)


class ExaAdapter:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Exa API key is required")
        self.client = Exa(api_key=api_key)
        self.api_key = api_key

    def search(
        self,
        query: str,
        search_type: str = "auto",
        num_results: int = 10,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        start_published_date: Optional[str] = None,
        end_published_date: Optional[str] = None,
        use_autoprompt: bool = True,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Search the web using Exa's neural/keyword search.

        Args:
            query: Search query
            search_type: "neural", "keyword", "auto" (default)
            num_results: Number of results (1-100)
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude
            start_published_date: ISO date string (e.g., "2024-01-01")
            end_published_date: ISO date string
            use_autoprompt: Whether to use Exa's autoprompt optimization
            category: Content category filter
        """
        try:
            logger.info(f"Exa search: query='{query}', type={search_type}, num_results={num_results}")

            result = self.client.search_and_contents(
                query,
                type=search_type,
                num_results=num_results,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                start_published_date=start_published_date,
                end_published_date=end_published_date,
                use_autoprompt=use_autoprompt,
                category=category,
                text=True,
            )

            items = []
            for r in result.results:
                items.append({
                    "title": r.title,
                    "url": r.url,
                    "published_date": r.published_date,
                    "author": r.author,
                    "text": r.text if hasattr(r, 'text') and r.text else None,
                    "score": r.score if hasattr(r, 'score') else None,
                })

            return {
                "items": items,
                "autoprompt_string": result.autoprompt_string if hasattr(result, 'autoprompt_string') else None,
            }

        except Exception as e:
            logger.error(f"Exa search failed: {e}")
            return {"items": [], "error": str(e)}

    def find_similar(
        self,
        url: str,
        num_results: int = 10,
        exclude_source_domain: bool = False,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        start_published_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find pages similar to a given URL.

        Args:
            url: URL to find similar pages to
            num_results: Number of results (1-100)
            exclude_source_domain: Whether to exclude the source domain
            include_domains: List of domains to include
            exclude_domains: List of domains to exclude
            start_published_date: ISO date string
        """
        try:
            logger.info(f"Exa find_similar: url='{url}', num_results={num_results}")

            result = self.client.find_similar_and_contents(
                url,
                num_results=num_results,
                exclude_source_domain=exclude_source_domain,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                start_published_date=start_published_date,
                text=True,
            )

            items = []
            for r in result.results:
                items.append({
                    "title": r.title,
                    "url": r.url,
                    "published_date": r.published_date,
                    "author": r.author,
                    "text": r.text if hasattr(r, 'text') and r.text else None,
                    "score": r.score if hasattr(r, 'score') else None,
                })

            return {"items": items}

        except Exception as e:
            logger.error(f"Exa find_similar failed: {e}")
            return {"items": [], "error": str(e)}

    def search_code(
        self,
        query: str,
        num_results: int = 10,
        include_domains: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search for code examples using Exa's neural search optimized for code.
        This focuses on GitHub, Stack Overflow, and documentation sites.

        Args:
            query: Code search query (e.g., "fastapi dependency injection")
            num_results: Number of results (1-100)
            include_domains: Optional list of domains to focus on
        """
        code_domains = [
            "github.com",
            "stackoverflow.com",
            "docs.python.org",
            "readthedocs.io",
            "readthedocs.org",
        ]

        if include_domains:
            code_domains = list(set(code_domains + include_domains))

        try:
            logger.info(f"Exa code search: query='{query}', num_results={num_results}")

            result = self.client.search_and_contents(
                query,
                type="neural",
                num_results=num_results,
                include_domains=code_domains,
                text=True,
                use_autoprompt=True,
            )

            items = []
            for r in result.results:
                item = {
                    "title": r.title,
                    "url": r.url,
                    "published_date": r.published_date,
                    "author": r.author,
                    "text": r.text if hasattr(r, 'text') and r.text else None,
                    "score": r.score if hasattr(r, 'score') else None,
                }

                if "github.com" in r.url:
                    parts = r.url.replace("https://github.com/", "").split("/")
                    if len(parts) >= 2:
                        item["repo"] = f"{parts[0]}/{parts[1]}"
                        if len(parts) >= 4 and parts[2] == "blob":
                            item["path"] = "/".join(parts[4:])
                            item["ref"] = parts[3]

                items.append(item)

            return {
                "items": items,
                "autoprompt_string": result.autoprompt_string if hasattr(result, 'autoprompt_string') else None,
            }

        except Exception as e:
            logger.error(f"Exa code search failed: {e}")
            return {"items": [], "error": str(e)}