import asyncio
import logging
from app.search.tools import SearchOrchestrator

logger = logging.getLogger("amars.research")


class ResearchAgent:
    def __init__(self):
        self.orchestrator = SearchOrchestrator()

    async def execute(self, subtask: str, query: str = "") -> list[dict]:
        search_term = query if query else subtask

        logger.info(f"[research] subtask='{subtask[:80]}' search_term='{search_term[:80]}'")

        try:
            results = await asyncio.wait_for(
                self.orchestrator.search_all(search_term),
                timeout=45
            )
        except asyncio.TimeoutError:
            logger.warning(f"[research] search timed out for: {search_term[:80]}")
            results = []
        except Exception as e:
            logger.error(f"[research] search error: {e}")
            results = []

        logger.info(
            f"[research] done — {len(results)} results "
            f"(ddg/arxiv/wiki breakdown logged in SearchOrchestrator)"
        )

        return results


async def run_subtasks(subtasks: list[dict], original_query: str) -> list[dict]:
    agent = ResearchAgent()
    all_findings = []
    seen_urls = set()

    for i, subtask in enumerate(subtasks):
        if i > 0:
            await asyncio.sleep(1.5)

        description = (
            subtask.get("description")
            or subtask.get("query")
            or subtask.get("task")
            or str(subtask)
        )
        try:
            results = await agent.execute(subtask=description, query=original_query)
            for item in results:
                url = item.get("url", "").rstrip("/")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_findings.append(item)
        except Exception as e:
            logger.error(f"[research] subtask {i} failed: {e}")

    logger.info(f"[research] total unique findings: {len(all_findings)}")
    return all_findings
