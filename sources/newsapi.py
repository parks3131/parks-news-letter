import requests
from datetime import datetime, timedelta, timezone
from config import NEWSAPI_KEY

NEWSAPI_BASE = "https://newsapi.org/v2/everything"

QUERIES = {
    "ai": "artificial intelligence OR machine learning OR LLM OR OpenAI OR Claude OR Gemini",
    "startup_jobs": "startup funding OR tech layoffs OR job market OR new skills hiring OR venture capital",
    "immigration": "US immigration OR USCIS OR visa OR green card OR H1B OR immigration policy",
}


def fetch_newsapi_articles(category: str, limit: int = 20) -> list[dict]:
    if not NEWSAPI_KEY:
        return []

    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    params = {
        "q": QUERIES[category],
        "from": yesterday,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": limit,
        "apiKey": NEWSAPI_KEY,
    }

    try:
        r = requests.get(NEWSAPI_BASE, params=params, timeout=10)
        r.raise_for_status()
        articles = r.json().get("articles", [])
    except Exception:
        return []

    return [
        {
            "title": a.get("title", ""),
            "url": a.get("url", ""),
            "source": a.get("source", {}).get("name", "NewsAPI"),
            "summary": a.get("description", ""),
            "published_at": a.get("publishedAt", ""),
            "category": category,
        }
        for a in articles
        if a.get("title") and a.get("url")
    ]
