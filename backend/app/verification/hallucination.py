from typing import List, Dict
from app.search.duckduckgo import DuckDuckGoSearchTool
from app.core.llm import get_llm
import json

class FactVerificationSystem:
    def __init__(self):
        self.search = DuckDuckGoSearchTool()
        self.llm = get_llm(format_json=True)

    async def verify_claim(self, claim: str, original_source: str) -> Dict:
        search_results = await self.search.search(f'verify: "{claim}"')

        supporting = []
        contradicting = []

        for result in search_results[:5]:
            if result["url"] == original_source:
                continue

            verdict = await self._check_alignment(claim, result["content"])
            if verdict.get("supports"):
                supporting.append(result)
            elif verdict.get("contradicts"):
                contradicting.append(result)

        confidence = self._calculate_confidence(supporting, contradicting)

        return {
            "claim": claim,
            "verified": confidence > 0.6,
            "confidence": confidence,
            "supporting_sources": supporting,
            "contradicting_sources": contradicting,
            "hallucination_flag": len(supporting) == 0 and len(contradicting) > 2
        }

    async def _check_alignment(self, claim: str, context: str) -> Dict:
        prompt = f"""
        Does the following context support or contradict the claim?
        Claim: {claim}
        Context: {context[:2000]}

        Output only JSON: {{"supports": bool, "contradicts": bool, "explanation": "string"}}
        """
        response = await self.llm.ainvoke(prompt)
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        return json.loads(content)

    def _calculate_confidence(self, supporting: List, contradicting: List) -> float:
        if not supporting and not contradicting:
            return 0.5
        total = len(supporting) + len(contradicting)
        base = len(supporting) / total
        weighted = sum(s.get("score", 0.5) for s in supporting)
        return min(1.0, (base + weighted / (total * 2)) / 1.5)

    async def detect_hallucination(self, claim: str, context: str) -> bool:
        prompt = f"""
        Does this claim appear to be supported by the context?
        Claim: {claim}
        Context: {context[:1000]}

        Answer only: SUPPORTED or HALLUCINATION
        """
        response = await self.llm.ainvoke(prompt)
        return "HALLUCINATION" in response.content.upper()
