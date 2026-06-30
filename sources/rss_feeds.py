import feedparser
from datetime import datetime, timezone

RSS_FEEDS = {
    "ai": [
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
        "https://www.wired.com/feed/category/artificial-intelligence/latest/rss",
        "https://feeds.arstechnica.com/arstechnica/index",
        "https://www.technologyreview.com/feed/",
        "https://huggingface.co/blog/feed.xml",
        "https://openai.com/news/rss/",
        "https://feeds.feedburner.com/oreilly/radar",
        "https://machinelearningmastery.com/feed/",
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
    ],
}


def fetch_rss_articles(category: str, limit: int = 20) -> list[dict]:
    results = []
    for feed_url in RSS_FEEDS.get(category, []):
        if len(results) >= limit:
            break
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:4]:
                title = entry.get("title", "").strip()
                url = entry.get("link", "").strip()
                if not title or not url:
                    continue

                published = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()

                summary = entry.get("summary", "") or entry.get("description", "")
                # Strip HTML tags from summary
                import re
                summary = re.sub(r"<[^>]+>", "", summary)[:400].strip()

                results.append({
                    "title": title,
                    "url": url,
                    "source": feed.feed.get("title", feed_url),
                    "summary": summary,
                    "published_at": published,
                    "category": category,
                })
        except Exception:
            continue

    return results[:limit]
