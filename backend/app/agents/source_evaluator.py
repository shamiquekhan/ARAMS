import datetime
import re
from typing import List, Dict

STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
              "have", "has", "had", "do", "does", "did", "will", "would",
              "can", "could", "shall", "should", "may", "might", "must",
              "to", "of", "in", "for", "on", "with", "at", "by", "from",
              "as", "into", "through", "during", "before", "after",
              "above", "below", "between", "out", "off", "over", "under",
              "again", "further", "then", "once", "here", "there", "when",
              "where", "why", "how", "all", "each", "every", "both", "few",
              "more", "most", "other", "some", "such", "no", "nor", "not",
              "only", "own", "same", "so", "than", "too", "very", "just",
              "because", "but", "and", "or", "if", "while", "about"}

class SourceEvaluationAgent:
    def __init__(self):
        self.domain_trust = {
            "gov": 1.0,
            "edu": 0.9,
            "org": 0.8,
            "com": 0.5,
            "net": 0.4
        }
        self.academic_domains = [".edu", "arxiv.org", "nature.com", "science.org"]

    def score_source(self, url: str, domain: str, date_str: str = None) -> float:
        # Extract TLD or use domain directly
        ext = domain.split('.')[-1] if '.' in domain else domain
        base_score = self.domain_trust.get(ext, 0.5)
        
        recency_penalty = 0.0
        if date_str:
            try:
                date = datetime.datetime.fromisoformat(date_str)
                days_old = (datetime.datetime.now() - date).days
                recency_penalty = max(0, (days_old / 365) * 0.1)
            except:
                pass
                
        https_bonus = 0.1 if url.startswith("https") else 0
        academic_bonus = 0.2 if any(d in url for d in self.academic_domains) else 0
        
        score = base_score - recency_penalty + https_bonus + academic_bonus
        return min(1.0, max(0.0, score))

    def evaluate_batch(self, sources: List[Dict]) -> Dict[str, float]:
        scores = {}
        for source in sources:
            url = source.get("url", "")
            domain = source.get("domain", url.split('/')[2] if "//" in url else "")
            date = source.get("published_date")
            scores[url] = self.score_source(url, domain, date)
        return scores

    def filter_relevant(self, findings: List[Dict], query: str) -> List[Dict]:
        query_tokens = {w.lower() for w in query.split() if w.lower() not in STOP_WORDS and len(w) > 2}
        if not query_tokens:
            return findings

        relevant = []
        for f in findings:
            content = (
                f.get("abstract", "") or
                f.get("content", "") or
                f.get("title", "") or
                ""
            ).lower()
            word_overlap = sum(1 for w in query_tokens if re.search(r'\b' + re.escape(w) + r'\b', content))
            if word_overlap > 0:
                relevant.append(f)

        if len(relevant) >= 2:
            return relevant
        if len(relevant) == 1:
            return relevant
        return findings
