import json
import os
from sources.hackernews import fetch_hn_stories
from sources.newsapi import fetch_newsapi_articles
from sources.rss_feeds import fetch_rss_articles
from sources.devto import fetch_devto_articles
from sources.arxiv import fetch_arxiv_papers
from subscribers.db import get_all_subscribers
from mailer.sender import send_email

# ── Server-side state (articles live here, model never passes big payloads) ───
_state: dict = {
    "ai": [],
    "startup_jobs": [],
    "immigration": [],
    "composed": None,   # {"html": ..., "plain": ...}
}

# ── Tool schemas for OpenRouter ────────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_news",
            "description": (
                "Fetch and store the top N news articles for a category. "
                "Call once per category before compose_newsletter."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["ai", "startup_jobs", "immigration"],
                    },
                    "count": {
                        "type": "integer",
                        "description": "10 for ai/startup_jobs, 5 for immigration.",
                    },
                },
                "required": ["category", "count"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compose_newsletter",
            "description": (
                "Compose the newsletter using the articles already fetched via get_top_news. "
                "Call this AFTER all three get_top_news calls. No parameters needed."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_subscribers",
            "description": "Return the list of all active subscriber email addresses.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_newsletter",
            "description": (
                "Send the composed newsletter to the given recipients. "
                "Call compose_newsletter and get_subscribers first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "Email subject line."},
                    "recipients": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email addresses from get_subscribers.",
                    },
                },
                "required": ["subject", "recipients"],
            },
        },
    },
]

# ── Tool implementations ───────────────────────────────────────────────────────

def tool_get_top_news(category: str, count: int) -> dict:
    articles = []
    articles += fetch_hn_stories(category, limit=20)
    articles += fetch_rss_articles(category, limit=20)
    articles += fetch_devto_articles(category, limit=15)
    if category == "ai":
        articles += fetch_arxiv_papers(category, limit=10)
    articles += fetch_newsapi_articles(category, limit=20)  # only fires if key is set

    seen = set()
    deduped = []
    for a in articles:
        key = a["title"].lower()[:60]
        if key and key not in seen:
            seen.add(key)
            deduped.append(a)

    ranked = sorted(deduped, key=lambda x: x.get("score", 0), reverse=True)[:count]

    for a in ranked:
        if not a.get("summary"):
            a["summary"] = f"Trending {category.replace('_', '/')} story from {a.get('source', 'the web')}."

    _state[category] = ranked
    return {"fetched": len(ranked), "category": category, "titles": [a["title"] for a in ranked]}


def tool_compose_newsletter() -> dict:
    from mailer.templates import render_newsletter
    ai = _state["ai"]
    startup = _state["startup_jobs"]
    immigration = _state["immigration"]

    if not any([ai, startup, immigration]):
        return {"error": "No articles fetched yet. Call get_top_news for each category first."}

    html, plain = render_newsletter(ai, startup, immigration)
    _state["composed"] = {"html": html, "plain": plain}
    return {"status": "composed", "sections": {"ai": len(ai), "startup_jobs": len(startup), "immigration": len(immigration)}}


def tool_get_subscribers() -> list[str]:
    # In CI/CD, read from env var (comma-separated). Falls back to local SQLite.
    env_subscribers = os.getenv("SUBSCRIBERS", "")
    if env_subscribers:
        return [e.strip() for e in env_subscribers.split(",") if e.strip()]
    return get_all_subscribers()


def tool_send_newsletter(subject: str, recipients: list[str]) -> dict:
    if not _state.get("composed"):
        return {"error": "compose_newsletter must be called first."}
    if not recipients:
        return {"status": "skipped", "reason": "no recipients"}

    html = _state["composed"]["html"]
    plain = _state["composed"]["plain"]

    results = []
    for email_addr in recipients:
        ok = send_email(to=email_addr, subject=subject, html=html, plain=plain)
        results.append({"email": email_addr, "sent": ok})

    sent = sum(1 for r in results if r["sent"])
    return {"status": "done", "sent": sent, "total": len(recipients)}


# ── Dispatcher ────────────────────────────────────────────────────────────────

def dispatch_tool(name: str, arguments: str | dict) -> str:
    args = json.loads(arguments) if isinstance(arguments, str) else arguments

    if name == "get_top_news":
        result = tool_get_top_news(**args)
    elif name == "compose_newsletter":
        result = tool_compose_newsletter()
    elif name == "get_subscribers":
        result = tool_get_subscribers()
    elif name == "send_newsletter":
        result = tool_send_newsletter(**args)
    else:
        result = {"error": f"Unknown tool: {name}"}

    return json.dumps(result, default=str)
