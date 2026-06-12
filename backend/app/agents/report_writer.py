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

REPORT_WRITER_PROMPT = """
You are writing a research report. Use ONLY the data provided below.

RULES:
- Do NOT use placeholders like [Title], [Topic], [Field], [Source 1]
- Do NOT describe the report format or your own process
- Do NOT reference "the verification findings section" or "the research process"
- Do NOT invent URLs, statistics, or claims not present in the findings
- Do NOT write "Research was conducted on..." as the executive summary
- Write in plain prose. Be specific. Use the actual findings below.

Query: {query}

Findings from research:
{findings_text}

Begin your response with ## Executive Summary immediately.
Do not write the report title. Do not add any text before ## Executive Summary.

You MUST include all four sections in this exact order:
## Executive Summary
3-5 sentences directly answering the query using the findings above.

## Key Findings
Numbered list. Each item is a factual statement about the topic — not a description
of where the information came from. No source names, no dates, no URLs here.

## Analysis
2-3 paragraphs expanding on the key findings. Discuss implications and connections.

## Sources
List every URL from the findings above as a markdown bullet. One URL per line.
You MUST end with ## Sources. Do not skip this section.
"""

FALLBACK_REPORT = """## No Sufficient Data

The research pipeline could not retrieve relevant sources for this query.

**Suggestions:**
- Try a more specific query
- Rephrase using academic terminology
- Check your internet connection
"""


class ReportWriterAgent:
    def __init__(self):
        self.llm = get_llm("report_writer")

    async def write(
        self,
        query: str,
        synthesis: dict,
        verified_findings: list,
        citations: list = None,
    ) -> str:
        synthesis = synthesis or {}
        insights = synthesis.get("insights", [])
        findings = verified_findings or []

        # Build findings text — use content, abstract, or title, in that order
        finding_lines = []
        seen_urls = set()
        for f in findings[:12]:
            url = f.get("url", "")
            if url in seen_urls:
                continue
            seen_urls.add(url)
            text = (
                f.get("content")
                or f.get("abstract")
                or f.get("title")
                or ""
            )
            text = _truncate_to_sentence(text.strip(), 400)
            if text and url.startswith("http"):
                finding_lines.append(f"- {text} (source: {url})")

        findings_text = "\n".join(finding_lines) if finding_lines else ""

        # Hard stop — nothing to write about
        if not findings_text:
            return FALLBACK_REPORT

        prompt = REPORT_WRITER_PROMPT.format(
            query=query,
            findings_text=findings_text or "No findings available.",
        )

        try:
            response = await asyncio.wait_for(
                self.llm.ainvoke(prompt), timeout=60
            )
            report = response.content.strip()

            # Sanity check — reject if LLM still output a template
            bad_signals = ["[Title]", "[Topic]", "[Field]", "[Source", "Research was conducted on"]
            if any(s in report for s in bad_signals) or len(report) < 100:
                return _build_fallback_from_findings(query, findings, insights)

            return report

        except asyncio.TimeoutError:
            return _build_fallback_from_findings(query, findings, insights)
        except Exception as e:
            return _build_fallback_from_findings(query, findings, insights)


def _build_fallback_from_findings(query: str, findings: list, insights: list) -> str:
    """Construct a minimal but real report from raw data when LLM fails."""
    lines = []

    exec_text = " ".join(insights[:3])[:500] if insights else ""
    if not exec_text and findings:
        snippet = (findings[0].get("content") or findings[0].get("abstract") or findings[0].get("title") or "")[:200]
        exec_text = f"Research on '{query}' produced {len(findings)} relevant sources. {snippet}"
    if exec_text:
        lines.append("## Executive Summary")
        lines.append(exec_text + "\n")

    if insights:
        lines.append("## Key Findings\n")
        for i, insight in enumerate(insights[:6], 1):
            if insight and len(insight) > 20:
                lines.append(f"{i}. {insight[:300]}\n")
    elif findings:
        lines.append("## Key Findings\n")
        for i, f in enumerate(findings[:6], 1):
            text = (f.get("content") or f.get("abstract") or f.get("title") or "")[:200]
            if text:
                lines.append(f"{i}. {text}\n")

    analysis_text = " ".join(insights[3:5])[:500] if insights and len(insights) > 3 else ""
    if not analysis_text and insights:
        analysis_text = " ".join(insights[:2])[:500]
    if not analysis_text and findings:
        texts = [(f.get("content") or f.get("abstract") or "")[:150] for f in findings[:3] if f.get("content") or f.get("abstract")]
        analysis_text = " ".join(texts)[:500]
    if analysis_text:
        lines.append("## Analysis")
        lines.append(analysis_text + "\n")

    seen_urls = set()
    source_lines = []
    for f in findings[:8]:
        url = f.get("url", "")
        if url.startswith("http") and url not in seen_urls:
            seen_urls.add(url)
            source_lines.append(f"* {url}")

    if source_lines:
        lines.append("## Sources\n")
        lines.extend(source_lines)

    return "\n".join(lines)
