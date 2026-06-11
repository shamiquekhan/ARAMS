import asyncio
from typing import List, Dict
from ddgs import DDGS


class DuckDuckGoSearchTool:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = DDGS()
        return self._client

    async def search(self, query: str, max_results: int = 10) -> List[Dict]:
        try:
            results = await asyncio.to_thread(
                lambda: list(self.client.text(query, max_results=max_results))
            )
            return [{
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "content": r.get("body", ""),
                "score": 0.5,
                "published_date": None,
                "source": "duckduckgo"
            } for r in results]
        except Exception:
            return []
