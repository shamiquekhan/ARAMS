import asyncio
import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
import arxiv
import wikipedia

# Domains that only syndicate other sites — no original content
SPAM_DOMAINS = {
    "customeranalytics.com.au",
    "deeplearningdaily.com",
    "feedproxy.google.com",
    "feeds.feedburner.com",
}

# ArXiv category routing — maps topic keywords to correct arxiv categories
ARXIV_CATEGORY_MAP = [
    (
        ["nlp", "natural language", "transformer", "bert", "gpt", "language model",
         "text classification", "sentiment", "named entity", "machine translation",
         "question answering", "summarization", "tokenization"],
        "cat:cs.CL OR cat:cs.AI"
    ),
    (
        ["machine learning", "neural network", "deep learning", "classification",
         "regression", "clustering", "reinforcement learning", "gradient descent",
         "backpropagation", "convolutional", "recurrent", "lstm"],
        "cat:cs.LG OR cat:cs.AI"
    ),
    (
        ["computer vision", "image recognition", "object detection", "segmentation",
         "generative adversarial", "diffusion model", "stable diffusion"],
        "cat:cs.CV OR cat:cs.LG"
    ),
    (
        ["battery", "solid-state", "electrolyte", "cathode", "anode", "lithium",
         "photovoltaic", "solar cell", "perovskite", "semiconductor", "thin film",
         "materials science", "crystal", "alloy", "polymer"],
        "cat:cond-mat.mtrl-sci OR cat:cond-mat.mes-hall"
    ),
    (
        ["healthcare", "medical", "clinical", "drug", "disease", "patient",
         "diagnosis", "hospital", "treatment", "radiology", "pathology",
         "symptom", "therapy", "surgery", "epidemiology", "biomedical"],
        "cat:cs.LG OR cat:cs.AI OR cat:q-bio OR cat:stat.ML"
    ),
    (
        ["drug discovery", "protein folding", "genomics", "bioinformatics",
         "clinical trial", "cancer", "biomarker", "molecular"],
        "cat:q-bio OR cat:cs.LG"
    ),
    (
        ["quantum computing", "qubit", "quantum circuit", "quantum algorithm",
         "quantum entanglement", "quantum error correction"],
        "cat:quant-ph OR cat:cs.ET"
    ),
    (
        ["robotics", "autonomous", "control system", "path planning",
         "simultaneous localization", "slam"],
        "cat:cs.RO OR cat:cs.AI"
    ),
]


def _build_arxiv_query(user_query: str) -> str:
    q = user_query.lower()
    for keywords, category_filter in ARXIV_CATEGORY_MAP:
        if any(kw in q for kw in keywords):
            return f"({category_filter}) AND ({user_query})"
    return user_query  # no category filter for general queries


class DuckDuckGoSearch:
    async def search(self, query: str, max_results: int = 6) -> list[dict]:
        loop = asyncio.get_event_loop()
        try:
            results = await loop.run_in_executor(
                None,
                lambda: list(DDGS().text(query, max_results=max_results))
            )
        except Exception:
            return []

        output = []
        for r in results:
            url = r.get("href", "")
            domain = url.split("/")[2] if "/" in url else ""
            if domain in SPAM_DOMAINS:
                continue
            output.append({
                "title": r.get("title", ""),
                "url": url,
                "content": r.get("body", ""),
                "source": "duckduckgo",
            })
        return output


class ArXivSearch:
    async def search(self, query: str, max_results: int = 6) -> list[dict]:
        loop = asyncio.get_event_loop()
        arxiv_query = _build_arxiv_query(query)

        def _search():
            client = arxiv.Client()
            search = arxiv.Search(
                query=arxiv_query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            return list(client.results(search))

        try:
            papers = await asyncio.wait_for(
                loop.run_in_executor(None, _search), timeout=15
            )
        except Exception:
            return []

        return [{
            "title": p.title,
            "url": p.entry_id,
            "content": p.summary,
            "abstract": p.summary,
            "authors": [a.name for a in p.authors],
            "published": str(p.published.date()),
            "source": "arxiv",
        } for p in papers]


class WikipediaSearch:
    async def search(self, query: str, max_results: int = 2) -> list[dict]:
        loop = asyncio.get_event_loop()

        def _search():
            titles = wikipedia.search(query, results=max_results)
            docs = []
            for title in titles:
                try:
                    page = wikipedia.page(title, auto_suggest=False)
                    docs.append({
                        "title": page.title,
                        "url": page.url,
                        "content": page.summary,
                        "source": "wikipedia",
                    })
                except Exception:
                    continue
            return docs

        try:
            return await asyncio.wait_for(
                loop.run_in_executor(None, _search), timeout=10
            )
        except Exception:
            return []


class WebScraper:
    async def scrape(self, url: str) -> dict:
        # Block private/internal addresses
        blocked_prefixes = ("http://localhost", "http://127.", "http://10.",
                            "http://192.168.", "http://169.254.", "https://169.254.")
        if any(url.startswith(p) for p in blocked_prefixes):
            return {"url": url, "content": "", "error": "Blocked internal URL"}

        try:
            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(
                    url, headers={"User-Agent": "Mozilla/5.0"}
                )
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["nav", "footer", "script", "style", "aside", "header"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                return {"url": url, "content": text[:3000]}
        except Exception as e:
            return {"url": url, "content": "", "error": str(e)}


class SearchOrchestrator:
    def __init__(self):
        self.ddg = DuckDuckGoSearch()
        self.arxiv = ArXivSearch()
        self.wiki = WikipediaSearch()
        self.scraper = WebScraper()

    async def search_all(self, query: str) -> list[dict]:
        # Run all three in parallel
        ddg_task = self.ddg.search(query)
        arxiv_task = self.arxiv.search(query)
        wiki_task = self.wiki.search(query)

        ddg_r, arxiv_r, wiki_r = await asyncio.gather(
            ddg_task, arxiv_task, wiki_task,
            return_exceptions=True
        )
        print(f"[search] DDG:{len(ddg_r) if isinstance(ddg_r,list) else 'ERR'} "
              f"ArXiv:{len(arxiv_r) if isinstance(arxiv_r,list) else 'ERR'} "
              f"Wiki:{len(wiki_r) if isinstance(wiki_r,list) else 'ERR'}")

        # ArXiv first — highest quality sources
        all_results = []
        for source in [arxiv_r, ddg_r, wiki_r]:
            if isinstance(source, list):
                all_results.extend(source)

        return self._deduplicate(all_results)

    def _deduplicate(self, results: list[dict]) -> list[dict]:
        seen_urls = set()
        unique = []
        for r in results:
            url = r.get("url", "").rstrip("/")
            if not url:
                continue
            domain = url.split("/")[2] if "/" in url else ""
            if domain in SPAM_DOMAINS:
                continue
            if url not in seen_urls:
                seen_urls.add(url)
                unique.append(r)
        return unique
