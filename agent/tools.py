import json
import os
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from sources.hackernews import fetch_hn_stories
from sources.newsapi import fetch_newsapi_articles
from sources.rss_feeds import fetch_rss_articles
from sources.devto import fetch_devto_articles
from sources.arxiv import fetch_arxiv_papers
from subscribers.db import get_all_subscribers
from mailer.sender import send_email

CANDIDATES_PER_CATEGORY = 15

# ── Server-side state ──────────────────────────────────────────────────────────
_state: dict = {
    "ai": [],
    "startup_jobs": [],
    "immigration": [],
    "composed": None,
}

# ── Tool schemas ───────────────────────────────────────────────────────────────

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_top_news",
            "description": (
                "Fetch the 30 most recent articles for a category, have the AI summarize "
                "and editorially select the best N, then store them. "
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
                "Compose the newsletter using articles fetched via get_top_news. "
                "Call AFTER all three get_top_news calls. No parameters needed."
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
            "description": "Send the composed newsletter. Call compose_newsletter and get_subscribers first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "recipients": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["subject", "recipients"],
            },
        },
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str[:19], fmt[:len(fmt)])
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        except ValueError:
            continue
    return datetime.min.replace(tzinfo=timezone.utc)


def _is_recent(article: dict, hours: int = 48) -> bool:
    """Returns True if article is within the last `hours`, or has no date (can't tell)."""
    date_str = article.get("published_at", "")
    if not date_str:
        return True  # no date = keep it, don't throw away potentially fresh content
    dt = _parse_date(date_str)
    if dt == datetime.min.replace(tzinfo=timezone.utc):
        return True  # unparseable = keep
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt >= cutoff


def _llm_summarize_and_select(articles: list[dict], category: str, count: int) -> list[dict]:
    """
    Single LLM call that:
    1. Reads all candidate articles (title + existing summary + source)
    2. Writes a clean 2-sentence summary for each
    3. Picks the best `count` by relevance and newsworthiness
    4. Returns them as a JSON list
    """
    from openai import OpenAI
    from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL

    category_label = {
        "ai": "Artificial Intelligence & Machine Learning",
        "startup_jobs": "Startups, Tech Jobs & New Skills",
        "immigration": "US Immigration & Visa Policy",
    }[category]

    # Build compact article list for the prompt
    articles_text = ""
    for i, a in enumerate(articles, 1):
        existing = (a.get("summary") or "").strip()[:150]
        articles_text += f"{i}. TITLE: {a['title']}\n   SOURCE: {a.get('source','')}\n"
        if existing:
            articles_text += f"   CONTEXT: {existing}\n"
        articles_text += "\n"

    prompt = f"""You are an editor for "Parks Tech USA Daily Brief", a morning newsletter.

Category: {category_label}
Task: From the {len(articles)} articles below, select the {count} most newsworthy and relevant ones for today's newsletter. Avoid duplicates on the same topic.

For your selected articles, write a punchy 2-sentence summary that:
- States what happened and why it matters
- Is factual, not clickbait
- Is under 50 words

Return ONLY a valid JSON array. Each object must have these exact keys:
- "index": the original article number (1-based)
- "summary": your 2-sentence summary

Example format:
[{{"index": 3, "summary": "OpenAI released GPT-5 today with 10x improved reasoning. The model outperforms all existing benchmarks and will be available via API next week."}}, ...]

Articles:
{articles_text}

Return JSON only, no other text."""

    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL, timeout=60.0)

    try:
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        raw = resp.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        selected = json.loads(raw.strip())

        result = []
        for item in selected:
            idx = int(item["index"]) - 1
            if 0 <= idx < len(articles):
                article = dict(articles[idx])
                article["summary"] = item["summary"]
                result.append(article)

        if result:
            return result[:count]

    except Exception as e:
        print(f"[tools] LLM select/summarize failed: {e} — falling back to recency order")

    # Fallback: just take top N by recency with whatever summaries exist
    return articles[:count]


# ── Tool implementations ───────────────────────────────────────────────────────

def tool_get_top_news(category: str, count: int | str) -> dict:
    count = int(count)

    # Fetch all sources in parallel
    def _hn():  return fetch_hn_stories(category, limit=20)
    def _rss(): return fetch_rss_articles(category, limit=25)
    def _dev(): return fetch_devto_articles(category, limit=20)
    def _nws(): return fetch_newsapi_articles(category, limit=25)
    def _arx(): return fetch_arxiv_papers(category, limit=15) if category == "ai" else []

    with ThreadPoolExecutor(max_workers=5) as ex:
        futures = [ex.submit(f) for f in (_hn, _rss, _dev, _nws, _arx)]
        raw = []
        for f in futures:
            try:
                raw += f.result(timeout=45)
            except Exception:
                pass

    # Deduplicate by title
    seen = set()
    deduped = []
    for a in raw:
        key = a["title"].lower()[:60]
        if key and key not in seen:
            seen.add(key)
            deduped.append(a)

    # Keep only last 48 hours (articles with no date are kept)
    recent = [a for a in deduped if _is_recent(a, hours=48)]

    # Sort by most recent first
    recent.sort(key=lambda a: _parse_date(a.get("published_at", "")), reverse=True)

    # Take top 30 candidates
    candidates = recent[:CANDIDATES_PER_CATEGORY]
    print(f"[tools] {category}: {len(deduped)} total → {len(recent)} recent (48h) → {len(candidates)} candidates → LLM selects {count}")

    # LLM summarizes all candidates and picks the best `count`
    selected = _llm_summarize_and_select(candidates, category, count)

    _state[category] = selected
    return {
        "fetched": len(selected),
        "category": category,
        "titles": [a["title"] for a in selected],
    }


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
    env_subscribers = os.getenv("SUBSCRIBERS", "")
    if env_subscribers:
        emails = [e.strip() for e in env_subscribers.split(",") if e.strip()]
        print(f"[tools] Subscribers from env: {emails}")
        return emails

    db_subscribers = get_all_subscribers()
    if db_subscribers:
        print(f"[tools] Subscribers from DB: {db_subscribers}")
        return db_subscribers

    # Fallback: send to FROM_EMAIL so CI runs are never silently swallowed
    from config import FROM_EMAIL
    if FROM_EMAIL and "@" in FROM_EMAIL:
        print(f"[tools] WARNING: No SUBSCRIBERS env or DB — falling back to FROM_EMAIL: {FROM_EMAIL}")
        return [FROM_EMAIL]

    print("[tools] WARNING: No recipients found — email will be skipped")
    return []


def tool_send_newsletter(subject: str, recipients: list[str] | str) -> dict:
    if isinstance(recipients, str):
        try:
            recipients = json.loads(recipients)
        except Exception:
            recipients = [r.strip() for r in recipients.split(",") if r.strip()]

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


# ── Dispatcher ─────────────────────────────────────────────────────────────────

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
