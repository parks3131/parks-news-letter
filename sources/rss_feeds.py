import re
import requests
import feedparser
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

RSS_FEEDS = {
    "ai": [
        # Major tech news
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "https://www.wired.com/feed/category/artificial-intelligence/latest/rss",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.technologyreview.com/feed/",
        # AI company blogs
        "https://openai.com/news/rss/",
        "https://www.anthropic.com/rss.xml",
        "https://deepmind.google/blog/rss.xml",
        "https://ai.meta.com/blog/rss/",
        "https://mistral.ai/news/rss/",
        "https://huggingface.co/blog/feed.xml",
        "https://blog.google/technology/ai/rss/",
        # Newsletters / researchers
        "https://www.deeplearning.ai/the-batch/feed/",
        "https://importai.substack.com/feed",
        "https://www.interconnects.ai/feed",
    ],
    "startup_jobs": [
        "https://techcrunch.com/category/startups/feed/",
        "https://techcrunch.com/category/venture/feed/",
        "https://www.theverge.com/tech/rss/index.xml",
        "https://news.crunchbase.com/feed/",
        "https://www.businessinsider.com/rss",
        "https://feeds.feedburner.com/entrepreneur/latest",
        "https://www.producthunt.com/feed",
        "https://remotive.com/remote-jobs/feed/category/software-dev",
        "https://www.levels.fyi/blog/feed",
        "https://techcrunch.com/category/apps/feed/",
    ],
    "immigration": [
        "https://www.uscis.gov/feeds/news",
        "https://thehill.com/policy/national-security/feed/",
        "https://feeds.npr.org/1015/rss.xml",
        "https://rss.politico.com/congress.xml",
        "https://www.reuters.com/rssFeed/us-usa-immigration",
        "https://abcnews.go.com/abcnews/usheadlines",
        "https://feeds.foxnews.com/foxnews/politics",
        "https://www.nbcnews.com/id/3032524/device/rss/rss.xml",
        "https://www.washingtonpost.com/immigration/rss/",
        "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/topic/subject/immigration-and-emigration/rss.xml",
    ],
}


def _fetch_one_feed(feed_url: str, category: str) -> list[dict]:
    try:
        resp = requests.get(feed_url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        feed = feedparser.parse(resp.content)
        articles = []
        for entry in feed.entries[:4]:
            title = entry.get("title", "").strip()
            url = entry.get("link", "").strip()
            if not title or not url:
                continue

            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()

            summary = entry.get("summary", "") or entry.get("description", "")
            summary = re.sub(r"<[^>]+>", "", summary)[:400].strip()

            articles.append({
                "title": title,
                "url": url,
                "source": feed.feed.get("title", feed_url),
                "summary": summary,
                "published_at": published,
                "category": category,
            })
        return articles
    except Exception:
        return []


def fetch_rss_articles(category: str, limit: int = 20) -> list[dict]:
    feed_urls = RSS_FEEDS.get(category, [])
    results = []

    # Fetch all feeds in parallel with a hard cap of 25s total
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_fetch_one_feed, url, category): url for url in feed_urls}
        try:
            for future in as_completed(futures, timeout=25):
                try:
                    results.extend(future.result())
                except Exception:
                    pass
        except TimeoutError:
            pass  # keep whatever arrived before the deadline

    return results[:limit]
