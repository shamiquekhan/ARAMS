from app.core.config import settings
from typing import List, Dict, Optional


class ResearchRetriever:
    def __init__(self, collection_name: str = "research_docs"):
        self.collection_name = collection_name
        self._qdrant = None
        self._embeddings = None

    @property
    def qdrant(self):
        if self._qdrant is None:
            try:
                from qdrant_client import QdrantClient
                self._qdrant = QdrantClient(url=settings.QDRANT_URL, timeout=5)
                self._ensure_collection()
            except Exception:
                self._qdrant = None
        return self._qdrant

    @property
    def embeddings(self):
        if self._embeddings is None:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                self._embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
            except Exception:
                try:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                    self._embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL)
                except Exception:
                    self._embeddings = None
        return self._embeddings

    def _ensure_collection(self):
        if self._qdrant is None:
            return
        try:
            self._qdrant.get_collection(self.collection_name)
        except Exception:
            try:
                self._qdrant.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={"size": 384, "distance": "Cosine"}
                )
            except Exception:
                pass

    def store_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        q = self.qdrant
        e = self.embeddings
        if q is None or e is None:
            return
        try:
            embedding = e.embed_query(text)
            q.upsert(
                collection_name=self.collection_name,
                points=[{
                    "id": hash(doc_id) % (2**63),
                    "vector": embedding,
                    "payload": {"text": text, **(metadata or {})}
                }]
            )
        except Exception:
            pass

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        q = self.qdrant
        e = self.embeddings
        if q is None or e is None:
            return []
        try:
            embedding = e.embed_query(query)
            results = q.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=top_k
            )
            return [r.payload for r in results]
        except Exception:
            return []
