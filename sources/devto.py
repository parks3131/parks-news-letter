import requests

DEVTO_BASE = "https://dev.to/api/articles"

TAGS = {
    "ai": ["ai", "machinelearning", "llm", "openai", "artificialintelligence"],
    "startup_jobs": ["career", "startup", "webdev", "programming", "job"],
}


def fetch_devto_articles(category: str, limit: int = 15) -> list[dict]:
    if category not in TAGS:
        return []

    results = []
    for tag in TAGS[category]:
        if len(results) >= limit:
            break
        try:
            r = requests.get(
                DEVTO_BASE,
                params={"tag": tag, "per_page": 5, "top": 1},
                timeout=10,
            )
            r.raise_for_status()
            for article in r.json():
                results.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "source": "Dev.to",
                    "summary": article.get("description", "")[:300],
                    "score": article.get("positive_reactions_count", 0),
                    "published_at": article.get("published_at", ""),
                    "category": category,
                })
        except Exception:
            continue

    return results[:limit]
