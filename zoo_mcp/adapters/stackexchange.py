import re
import html
import logging
from typing import Optional, List, Dict, Any
import requests

logger = logging.getLogger(__name__)


class StackExchangeAdapter:
    BASE_URL = "https://api.stackexchange.com/2.3"
    TIMEOUT = 10

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()

    def search_accepted_answers(
        self, query: str, tags: Optional[List[str]] = None, limit: int = 10
    ) -> Dict[str, Any]:
        params = {
            "order": "desc",
            "sort": "votes",
            "intitle": query,
            "site": "stackoverflow",
            "filter": "withbody",
            "pagesize": limit,
            "accepted": "True",
        }

        if tags:
            params["tagged"] = ";".join(tags)

        if self.api_key:
            params["key"] = self.api_key

        try:
            response = self.session.get(
                f"{self.BASE_URL}/search/advanced", params=params, timeout=self.TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            answers = []
            for item in data.get("items", [])[:limit]:
                answer_id = item.get("accepted_answer_id")
                if not answer_id:
                    continue

                answer_response = self.session.get(
                    f"{self.BASE_URL}/answers/{answer_id}",
                    params={
                        "site": "stackoverflow",
                        "filter": "withbody",
                        "key": self.api_key if self.api_key else None,
                    },
                    timeout=self.TIMEOUT,
                )

                if answer_response.status_code == 200:
                    answer_data = answer_response.json().get("items", [])
                    if answer_data:
                        answer_body = html.unescape(answer_data[0].get("body", ""))
                        code_blocks = self._extract_code_blocks(answer_body)

                        if code_blocks:
                            answers.append(
                                {
                                    "question": item.get("title", ""),
                                    "answer_url": item.get("link", ""),
                                    "code_blocks": code_blocks,
                                }
                            )

            return {"answers": answers}

        except requests.RequestException as e:
            logger.error(f"Stack Exchange request failed: {e}")
            return {"answers": []}

    def _extract_code_blocks(self, html_body: str) -> List[Dict[str, Any]]:
        code_pattern = r"<pre><code>(.*?)</code></pre>"
        matches = re.findall(code_pattern, html_body, re.DOTALL)

        code_blocks = []
        for code in matches:
            clean_code = html.unescape(code.strip())
            if clean_code:
                lang = self._detect_language(clean_code)
                code_blocks.append({"lang": lang, "text": clean_code})

        return code_blocks

    def _detect_language(self, code: str) -> Optional[str]:
        if "public class" in code or "private class" in code:
            return "java"
        elif "import " in code or "def " in code:
            return "python"
        elif "function " in code or "const " in code or "let " in code or "var " in code:
            return "javascript"
        return None