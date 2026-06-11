import asyncio
from typing import List, Dict
from firecrawl import FirecrawlApp
from app.core.config import settings

class FirecrawlTool:
    def __init__(self):
        self.app = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)

    async def scrape(self, url: str) -> Dict:
        result = await asyncio.to_thread(
            lambda: self.app.scrape_url(url, params={"formats": ["markdown", "html"]})
        )
        return {
            "url": url,
            "content": result.get("markdown", ""),
            "metadata": result.get("metadata", {})
        }

    async def crawl(self, url: str, max_pages: int = 5) -> List[Dict]:
        result = await asyncio.to_thread(
            lambda: self.app.crawl_url(url, params={"limit": max_pages})
        )
        return result.get("data", [])
