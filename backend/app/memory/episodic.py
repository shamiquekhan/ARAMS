from app.core.config import settings
from typing import List, Dict, Optional


class EpisodicMemory:
    def __init__(self, collection_name: str = "research_memory"):
        self._client = None
        self._embeddings_model = None
        self.collection = collection_name

    @property
    def client(self):
        if self._client is None:
            try:
                from qdrant_client import QdrantClient
                self._client = QdrantClient(url=settings.QDRANT_URL, timeout=5)
                self._ensure_collection()
            except Exception:
                self._client = None
        return self._client

    def _ensure_collection(self):
        if self._client is None:
            return
        try:
            self._client.get_collection(self.collection)
        except Exception:
            try:
                self._client.create_collection(
                    collection_name=self.collection,
                    vectors_config={"size": 384, "distance": "Cosine"}
                )
            except Exception:
                pass

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        try:
            if self._embeddings_model is None:
                from sentence_transformers import SentenceTransformer
                self._embeddings_model = SentenceTransformer(settings.EMBEDDING_MODEL)
            return self._embeddings_model.encode(text).tolist()
        except Exception:
            return None

    def store(self, memory_id: str, text: str, metadata: dict):
        c = self.client
        if c is None:
            return
        vector = self._get_embedding(text)
        if vector is None:
            return
        try:
            from qdrant_client.models import PointStruct
            c.upsert(
                collection_name=self.collection,
                points=[PointStruct(
                    id=hash(memory_id) % (2**63),
                    vector=vector,
                    payload={"text": text, **metadata}
                )]
            )
        except Exception:
            pass

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        c = self.client
        if c is None:
            return []
        vector = self._get_embedding(query)
        if vector is None:
            return []
        try:
            results = c.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=top_k
            )
            return [r.payload for r in results]
        except Exception:
            return []
