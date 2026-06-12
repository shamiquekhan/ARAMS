import json
import asyncio
import re
from app.core.llm import get_llm


def _truncate_to_sentence(text: str, max_chars: int = 400) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    for punct in ['. ', '! ', '? ']:
        idx = truncated.rfind(punct)
        if idx > max_chars * 0.2:
            return truncated[:idx + 1]
    return truncated

SYNTHESIS_PROMPT = """
You are a Synthesis Agent. Analyze the research findings below and extract key insights.

Query: {query}

Research findings:
{all_findings}

RULES:
- Each insight must be a factual statement about the TOPIC itself
- Never mention source names, URLs, dates, or where the finding came from
- Cover different aspects — do not repeat the same point in different words
- If findings are from unrelated topics, only use the ones relevant to the query

Output ONLY valid JSON. No explanation, no markdown, no backticks. Exactly this structure:
{{"insights": ["insight1", "insight2", "insight3"], "conclusion": "2-3 sentence conclusion", "evidence_map": {{"theme1": ["finding1", "finding2"]}}}}

Minimum 3 insights, maximum 7.
"""


class SynthesisAgent:
    def __init__(self):
        self.llm = get_llm("synthesis")

    async def synthesize(self, query: str, findings: list) -> dict:
        if not findings:
            return _empty_synthesis(query)

        # Build findings text using content/abstract/title
        finding_lines = []
        seen_urls = set()
        for f in findings[:15]:
            url = f.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            text = _truncate_to_sentence((
                f.get("content")
                or f.get("abstract")
                or f.get("title")
                or ""
            ).strip(), 500)
            if text:
                finding_lines.append(f"- {text}")

        all_findings_text = "\n".join(finding_lines)

        if not all_findings_text:
            return _fallback_from_findings(query, findings)

        prompt = SYNTHESIS_PROMPT.format(
            query=query,
            all_findings=all_findings_text
        )

        try:
            response = await asyncio.wait_for(
                self.llm.ainvoke(prompt), timeout=45
            )
            content = response.content.strip()

            # Strip markdown fences if present
            content = re.sub(r"^```(?:json)?\s*", "", content)
            content = re.sub(r"\s*```$", "", content)
            content = content.strip()

            # Extract JSON object
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                content = match.group()

            parsed = json.loads(content)

            # Validate structure
            if (
                isinstance(parsed, dict)
                and isinstance(parsed.get("insights"), list)
                and len(parsed["insights"]) >= 1
                and any(len(str(i)) > 20 for i in parsed["insights"])
            ):
                # Filter out empty or trivially short insights
                parsed["insights"] = [
                    i for i in parsed["insights"] if len(str(i).strip()) > 20
                ]
                if parsed["insights"]:
                    return parsed

        except (json.JSONDecodeError, asyncio.TimeoutError, Exception):
            pass

        # LLM failed or returned bad JSON — build from raw findings
        return _fallback_from_findings(query, findings)


def _clean_snippet(text: str) -> str:
    text = re.sub(r'^(January|February|March|April|May|June|July|August|'
                  r'September|October|November|December)\s+\d+,\s+\d{4}\s*[-–]\s*', '', text)
    text = re.sub(r'^\d+\s+days?\s+ago\s*[-–]\s*', '', text)
    text = re.sub(r'^\d{4}-\d{2}-\d{2}\s*[-–]\s*', '', text)
    return text.strip()


def _fallback_from_findings(query: str, findings: list) -> dict:
    """Build a real synthesis from raw findings when LLM fails."""
    insights = []
    seen = set()
    for f in findings[:8]:
        text = (
            f.get("content")
            or f.get("abstract")
            or f.get("title")
            or ""
        ).strip()
        # Take first 2 sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        raw = " ".join(sentences[:2])[:250]
        snippet = _clean_snippet(_truncate_to_sentence(raw, 250))
        if snippet and snippet not in seen and len(snippet) > 30:
            seen.add(snippet)
            insights.append(snippet)

    return {
        "insights": insights or ["Research completed — see sources for details."],
        "conclusion": f"Research on '{query}' completed with {len(findings)} sources retrieved.",
        "evidence_map": {
            "sources": [f.get("url", "") for f in findings[:5] if f.get("url")]
        }
    }


def _empty_synthesis(query: str) -> dict:
    return {
        "insights": [],
        "conclusion": f"No data was retrieved for: {query}",
        "evidence_map": {}
    }
