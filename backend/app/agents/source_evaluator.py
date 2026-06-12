import asyncio
import logging
import re
from app.core.llm import get_llm

logger = logging.getLogger("amars.source_eval")


class SourceEvaluatorAgent:
    def __init__(self):
        self.llm = get_llm("source_eval")

    async def evaluate(self, query: str, findings: list[dict]) -> list[dict]:
        if not findings:
            return []

        scored = await asyncio.gather(
            *[self._score_finding(query, f) for f in findings],
            return_exceptions=True
        )

        results = []
        for finding, score in zip(findings, scored):
            if isinstance(score, Exception):
                results.append({**finding, "relevance_score": 0.5})
            else:
                results.append({**finding, "relevance_score": score})

        relevant = [r for r in results if r["relevance_score"] >= 0.3]

        if not relevant:
            logger.warning(f"[source_eval] all sources filtered for query='{query[:60]}' — returning top 3")
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            return results[:3]

        relevant.sort(key=lambda x: x["relevance_score"], reverse=True)
        logger.info(
            f"[source_eval] {len(relevant)}/{len(findings)} sources passed "
            f"relevance filter for query='{query[:60]}'"
        )
        return relevant

    async def _score_finding(self, query: str, finding: dict) -> float:
        text = (
            finding.get("content")
            or finding.get("abstract")
            or finding.get("title")
            or ""
        ).lower()[:600]

        title = (finding.get("title") or "").lower()

        keyword_score = _keyword_overlap_score(query, text, title)

        if keyword_score >= 0.7:
            return keyword_score
        if keyword_score <= 0.15:
            return keyword_score

        return await self._llm_relevance_score(query, text, title)

    async def _llm_relevance_score(self, query: str, text: str, title: str) -> float:
        prompt = f"""Query: {query}

Source title: {title}
Source content (first 400 chars): {text[:400]}

Is this source PRIMARILY about the query topic, or only SECONDARILY related (uses it as a tool), or NOT relevant?
Answer with exactly one word: PRIMARY or SECONDARY or NO"""

        try:
            response = await asyncio.wait_for(
                self.llm.ainvoke(prompt), timeout=8
            )
            answer = response.content.strip().upper()
            if "PRIMARY" in answer:
                return 0.85
            elif "SECONDARY" in answer:
                return 0.15
            elif "NO" in answer:
                return 0.1
            return 0.4
        except Exception:
            return 0.4


def _keyword_overlap_score(query: str, text: str, title: str) -> float:
    query_words = set(
        w for w in re.findall(r'\b\w+\b', query.lower())
        if len(w) >= 2
    )

    stopwords = {
        "what", "is", "the", "of", "in", "how", "does", "do", "a", "an",
        "are", "use", "uses", "used", "for", "and", "or", "to", "with",
        "that", "this", "it", "its", "be", "was", "were", "has", "have",
        "can", "could", "would", "will", "on", "at", "by", "from", "as"
    }
    query_words -= stopwords

    if not query_words:
        return 0.5

    combined = text + " " + title

    hits = sum(1 for w in query_words if re.search(r'\b' + re.escape(w) + r'\b', combined))
    base_score = hits / len(query_words)

    title_hits = sum(1 for w in query_words if re.search(r'\b' + re.escape(w) + r'\b', title))
    title_bonus = min(0.2, title_hits * 0.1)

    return min(1.0, base_score + title_bonus)
