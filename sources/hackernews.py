import requests
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

HN_BASE = "https://hacker-news.firebaseio.com/v0"

AI_KEYWORDS = {"ai", "llm", "gpt", "claude", "gemini", "openai", "anthropic", "machine learning",
               "deep learning", "neural", "transformer", "agent", "diffusion", "mistral", "llama"}

STARTUP_JOB_KEYWORDS = {"startup", "job", "hiring", "funding", "series a", "series b", "vc",
                         "venture", "yc", "y combinator", "launch", "founder", "raises", "seed",
                         "acquisition", "ipo", "layoff", "remote", "engineer", "developer"}


def _fetch_story(story_id: int) -> dict | None:
    try:
        r = requests.get(f"{HN_BASE}/item/{story_id}.json", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def _matches_keywords(text: str, keywords: set) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def fetch_hn_stories(category: str, limit: int = 30) -> list[dict]:
    if category == "immigration":
        return []  # HN rarely has immigration news

    keywords = AI_KEYWORDS if category == "ai" else STARTUP_JOB_KEYWORDS

    try:
        top_ids = requests.get(f"{HN_BASE}/topstories.json", timeout=10).json()
    except Exception:
        return []

    # Fetch top 50 stories in parallel (not 100 sequentially)
    candidates = top_ids[:50]
    with ThreadPoolExecutor(max_workers=15) as ex:
        stories = list(ex.map(_fetch_story, candidates, timeout=20))

    results = []
    for story in stories:
        if not story or story.get("type") != "story":
            continue
        title = story.get("title", "")
        url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id')}")
        if _matches_keywords(title, keywords):
            results.append({
                "title": title,
                "url": url,
                "source": "Hacker News",
                "score": story.get("score", 0),
                "published_at": datetime.fromtimestamp(
                    story.get("time", 0), tz=timezone.utc
                ).isoformat(),
                "category": category,
            })
        if len(results) >= limit:
            break

    return results
