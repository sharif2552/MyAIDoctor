"""
Researcher Agent — Clinical Researcher (Tool User)

Uses Tavily to search trusted medical domains and Firecrawl to scrape
full clinical guidelines for deep-context analysis.
"""

import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from langsmith import traceable

from backend.utils.logging import get_logger

load_dotenv()
logger = get_logger("myaidoc.researcher")


@traceable(name="run_researcher", run_type="chain")
def run_researcher(
    symptoms: str,
    differential: list[dict],
    research_query: str = "",
    medical_only: bool = True,
) -> list[dict]:
    if not isinstance(symptoms, str):
        symptoms = str(symptoms)
    if not isinstance(differential, list):
        differential = []
    if not isinstance(research_query, str):
        research_query = str(research_query)

    results = []

    top_conditions = [d.get("condition", "") for d in differential[:3] if d.get("condition")]
    query_parts = [research_query[:220] if research_query else symptoms[:200]]
    if top_conditions:
        query_parts.append(" OR ".join(top_conditions))
    query = " ".join(query_parts)[:400]

    realtime_query = _is_realtime_query(query)
    if realtime_query:
        query = _augment_realtime_query(query)
    include_domains = _choose_include_domains(realtime_query=realtime_query)
    tavily_results = _tavily_search(
        query,
        include_domains=include_domains,
        realtime_query=realtime_query,
    )
    results.extend(tavily_results)

    scrape_n = 3 if "pharmacotherapy" in (research_query or "").lower() else 2
    for item in tavily_results[:scrape_n]:
        url = item.get("url", "")
        if _is_valid_http_url(url):
            scraped = _firecrawl_scrape(url)
            if scraped:
                item["full_content"] = scraped[:3000]

    return results


def tavily_search_results(query: str, medical_only: bool = True) -> list[dict]:
    realtime_query = _is_realtime_query(str(query))
    effective_query = _augment_realtime_query(str(query)) if realtime_query else str(query)
    include_domains = _choose_include_domains(realtime_query=realtime_query)
    return _tavily_search(
        effective_query,
        include_domains=include_domains,
        realtime_query=realtime_query,
    )


def firecrawl_scrape_content(url: str) -> str:
    if not _is_valid_http_url(str(url)):
        return ""
    return _firecrawl_scrape(str(url))


NEWS_OUTBREAK_DOMAINS = [
    "who.int",
    "unicef.org",
    "reliefweb.int",
    "bbc.com",
    "theguardian.com",
    "reuters.com",
    "apnews.com",
    "aljazeera.com",
    "thedailystar.net",
    "dhakatribune.com",
]

# Sites that add no clinical value and pollute results
EXCLUDE_DOMAINS = [
    "pinterest.com",
    "reddit.com",
    "quora.com",
    "youtube.com",
    "tiktok.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
]


@traceable(name="tavily_search", run_type="tool")
def _tavily_search(
    query: str,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    realtime_query: bool = False,
) -> list[dict]:
    try:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return []

        client = TavilyClient(api_key=api_key)
        search_kwargs: dict = {
            "query": query,
            "search_depth": "advanced",
            "max_results": 8,
        }
        if realtime_query:
            search_kwargs["topic"] = "news"
            search_kwargs["days"] = 7
        if include_domains:
            search_kwargs["include_domains"] = include_domains
        # Always exclude low-signal social/video sites
        search_kwargs["exclude_domains"] = exclude_domains or EXCLUDE_DOMAINS

        try:
            response = client.search(**search_kwargs)
        except TypeError:
            # Older tavily-python versions don't accept exclude_domains — fall back gracefully
            fallback_kwargs: dict = {
                "query": query,
                "search_depth": "advanced",
                "max_results": 8,
            }
            if include_domains:
                fallback_kwargs["include_domains"] = include_domains
            response = client.search(**fallback_kwargs)

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

    except Exception:
        logger.exception("run_researcher: tavily search failed")
        return []


@traceable(name="firecrawl_scrape", run_type="tool")
def _firecrawl_scrape(url: str) -> str:
    try:
        from firecrawl import FirecrawlApp

        api_key = os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            return ""

        app = FirecrawlApp(api_key=api_key)
        result = app.scrape(url, formats=["markdown"])

        if isinstance(result, dict):
            return result.get("markdown", "") or result.get("content", "")

        markdown = getattr(result, "markdown", "")
        content = getattr(result, "content", "")
        return markdown or content or ""

    except Exception:
        logger.exception("run_researcher: firecrawl scrape failed for %s", url)
        return ""


def _is_valid_http_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def _is_realtime_query(query: str) -> bool:
    q = query.lower()
    signals = {
        "today",
        "latest",
        "current",
        "right now",
        "news",
        "update",
        "how many",
        "deaths",
        "died",
        "cases",
        "outbreak",
        "this week",
        "this month",
    }
    return any(signal in q for signal in signals)


def _augment_realtime_query(query: str) -> str:
    q = query.strip()
    if "bangladesh" in q.lower():
        return f"{q} latest update today 2026 outbreak official report"
    return f"{q} latest update today 2026 official report"


def _choose_include_domains(realtime_query: bool) -> list[str] | None:
    # Only restrict domains for news/outbreak queries where source credibility is critical.
    # For regular medical searches we let Tavily rank freely — whitelisting a small set of
    # sites was blocking relevant results from the wider medical web.
    if realtime_query:
        return NEWS_OUTBREAK_DOMAINS
    return None
