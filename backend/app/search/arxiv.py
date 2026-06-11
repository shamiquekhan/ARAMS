import asyncio
import arxiv
from typing import List, Dict

class ArXivTool:
    def __init__(self):
        self._client = arxiv.Client()
        self._nlp_keywords = [
            "nlp", "natural language", "transformer", "bert", "gpt",
            "language model", "large language model", "text generation",
            "sentiment", "translation", "text classification", "token",
            "embedding", "attention mechanism", "self-attention",
            "encoder", "decoder", "sequence", "semantic", "parsing",
            "named entity", "question answering", "summarization",
            "prompt", "fine-tuning", "llm", "neural machine translation",
        ]
        self._ml_keywords = [
            "machine learning", "neural network", "deep learning",
            "classification", "regression", "clustering",
            "reinforcement learning", "supervised", "unsupervised",
            "gradient descent", "backpropagation", "convolutional",
            "generative", "adversarial", "autoencoder", "gan",
            "dimensionality reduction", "feature extraction",
            "cross-validation", "overfitting", "underfitting",
        ]

    @property
    def client(self):
        return self._client

    def _build_arxiv_query(self, user_query: str) -> str:
        q = user_query.lower()
        if any(kw in q for kw in self._nlp_keywords):
            return f"(cat:cs.CL OR cat:cs.AI) AND ({user_query})"
        if any(kw in q for kw in self._ml_keywords):
            return f"(cat:cs.LG OR cat:cs.AI) AND ({user_query})"
        return user_query

    async def search(self, query: str, max_results: int = 5) -> List[Dict]:
        arxiv_query = self._build_arxiv_query(query)
        search = arxiv.Search(
            query=arxiv_query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        results = await asyncio.to_thread(
            lambda: [
                {
                    "title": paper.title,
                    "authors": [a.name for a in paper.authors],
                    "abstract": paper.summary,
                    "content": paper.summary,
                    "url": paper.entry_id,
                    "published": str(paper.published.date()),
                    "source": "arxiv",
                }
                for paper in self.client.results(search)
            ]
        )
        return results
