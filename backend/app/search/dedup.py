from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class Deduplicator:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=500, stop_words="english")

    def deduplicate_sources(self, sources: List[Dict], threshold: float = 0.92) -> List[Dict]:
        if not sources:
            return []

        contents = [s.get("content", "")[:500] for s in sources]
        if not any(contents):
            return sources

        try:
            tfidf = self.vectorizer.fit_transform(contents)
            keep = [0]
            for i in range(1, len(sources)):
                sims = cosine_similarity(tfidf[i], tfidf[keep])[0]
                if max(sims) < threshold:
                    keep.append(i)
            return [sources[i] for i in keep]
        except Exception:
            return sources
