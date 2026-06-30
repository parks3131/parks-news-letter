import requests
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT

SUBREDDITS = {
    "ai": ["artificial", "MachineLearning", "LocalLLaMA", "ChatGPT", "singularity"],
    "startup_jobs": ["startups", "cscareerquestions", "ExperiencedDevs", "jobs", "remotework"],
    "immigration": ["immigration", "USCIS", "h1b", "greencard", "ImmigrationLaw"],
}


def _get_token() -> str | None:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        return None
    try:
        r = requests.post(
            "https://www.reddit.com/api/v1/access_token",
            auth=(REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET),
            data={"grant_type": "client_credentials"},
            headers={"User-Agent": REDDIT_USER_AGENT},
            timeout=10,
        )
        r.raise_for_status()
        return r.json().get("access_token")
    except Exception:
        return None


def fetch_reddit_posts(category: str, limit: int = 20) -> list[dict]:
    token = _get_token()
    if not token:
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": REDDIT_USER_AGENT,
    }

    results = []
    for sub in SUBREDDITS.get(category, []):
        if len(results) >= limit:
            break
        try:
            r = requests.get(
                f"https://oauth.reddit.com/r/{sub}/hot",
                headers=headers,
                params={"limit": 5},
                timeout=10,
            )
            r.raise_for_status()
            posts = r.json().get("data", {}).get("children", [])
            for post in posts:
                d = post.get("data", {})
                if d.get("is_self") and not d.get("selftext"):
                    continue
                results.append({
                    "title": d.get("title", ""),
                    "url": d.get("url", f"https://reddit.com{d.get('permalink', '')}"),
                    "source": f"r/{sub}",
                    "summary": d.get("selftext", "")[:300],
                    "score": d.get("score", 0),
                    "published_at": "",
                    "category": category,
                })
        except Exception:
            continue

    return results[:limit]
