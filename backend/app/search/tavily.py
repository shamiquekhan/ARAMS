import asyncio
from typing import List, Dict, Optional
from app.core.config import settings

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

class TavilySearchTool:
    def __init__(self):
        self._client = None
        if TAVILY_AVAILABLE and settings.TAVILY_API_KEY:
            self._client = TavilyClient(api_key=settings.TAVILY_API_KEY)

    @property
    def client(self):
        return self._client

    async def search(self, query: str, depth: str = "advanced") -> List[Dict]:
        if not self.client:
            return []
        try:
            response = await asyncio.to_thread(
                lambda: self.client.search(
                    query=query,
                    search_depth=depth,
                    max_results=10,
                    include_answer=True,
                    include_raw_content=True
                )
            )
            return self._parse_results(response)
        except Exception:
            return []

    def _parse_results(self, response) -> List[Dict]:
        return [{
            "title": r["title"],
            "url": r["url"],
            "content": r["content"],
            "score": r.get("score", 0.5),
            "published_date": r.get("published_date")
        } for r in response.get("results", [])]
