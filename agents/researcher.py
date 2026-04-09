"""
Researcher Agent — Clinical Researcher (Tool User)

Uses Tavily to search trusted medical domains and Firecrawl to scrape
full clinical guidelines for deep-context analysis.
"""

import os
from dotenv import load_dotenv

load_dotenv()


def run_researcher(symptoms: str, differential: list[dict]) -> list[dict]:
    """
    Search medical literature for the given symptoms and differential diagnoses.
    Returns a list of research result dicts with title, url, snippet, and full_content.
    """
    results = []

    # Build a smart search query from the top diagnoses
    top_conditions = [d.get("condition", "") for d in differential[:3] if d.get("condition")]
    query_parts = [symptoms[:200]]
    if top_conditions:
        query_parts.append(" OR ".join(top_conditions))
    query = " ".join(query_parts)[:400]

    # ---------- Tavily Search ----------
    tavily_results = _tavily_search(query)
    results.extend(tavily_results)

    # ---------- Firecrawl Deep-Scrape ----------
    # Scrape the top 2 Tavily results for full-content analysis
    for item in tavily_results[:2]:
        url = item.get("url", "")
        if url:
            scraped = _firecrawl_scrape(url)
            if scraped:
                item["full_content"] = scraped[:3000]  # Limit to first 3k chars

    return results


# ─────────────────────────────────────────────────────────
# Tool helpers
# ─────────────────────────────────────────────────────────

TRUSTED_DOMAINS = [
    "mayoclinic.org",
    "nih.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "webmd.com",
    "medlineplus.gov",
    "uptodate.com",
    "cdc.gov",
    "who.int",
]


def _tavily_search(query: str) -> list[dict]:
    """Search Tavily and return structured results."""
    try:
        from tavily import TavilyClient

        api_key = os.getenv("tavilysearchapi") or os.getenv("TAVILY_API_KEY")
        if not api_key:
            return []

        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=6,
            include_domains=TRUSTED_DOMAINS,
        )

        out = []
        for r in response.get("results", []):
            out.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:500],
                    "score": r.get("score", 0),
                    "full_content": "",
                }
            )
        return out

    except Exception as e:
        print(f"[Researcher] Tavily error: {e}")
        return []


def _firecrawl_scrape(url: str) -> str:
    """Scrape a URL via Firecrawl and return clean markdown text."""
    try:
        from firecrawl import FirecrawlApp

        api_key = os.getenv("firecrawlapi") or os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return ""

        app = FirecrawlApp(api_key=api_key)
        result = app.scrape_url(url, params={"formats": ["markdown"]})

        if isinstance(result, dict):
            return result.get("markdown", "") or result.get("content", "")
        return ""

    except Exception as e:
        print(f"[Researcher] Firecrawl error scraping {url}: {e}")
        return ""
