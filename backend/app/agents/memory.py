from app.memory.short_term import ShortTermMemory
from app.memory.episodic import EpisodicMemory
from app.rag.retriever import ResearchRetriever
from typing import List, Dict

class MemoryAgent:
    def __init__(self):
        self.stm = ShortTermMemory()
        self.episodic = EpisodicMemory()
        self.retriever = ResearchRetriever()

    async def persist_findings(self, session_id: str, findings: List[Dict]):
        self.stm.save(session_id, "latest_findings", findings)
        for f in findings:
            content = f.get("content", "") or f.get("title", "") or str(f)
            self.episodic.store(
                memory_id=f"{session_id}:{f.get('url', hash(str(f)))}",
                text=content,
                metadata={"session_id": session_id, "source": f.get("source", "research")}
            )

    async def retrieve_context(self, query: str) -> List[Dict]:
        episodic_results = self.episodic.retrieve(query, top_k=5)
        rag_results = self.retriever.retrieve(query)
        combined = (episodic_results or []) + (rag_results or [])
        seen = set()
        unique = []
        for item in combined:
            key = item.get("text", "") or item.get("page_content", "") or str(item)
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique[:10]
