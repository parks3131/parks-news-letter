import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

ARXIV_BASE = "http://export.arxiv.org/api/query"
NS = {"atom": "http://www.w3.org/2005/Atom"}

QUERIES = {
    "ai": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
}


def fetch_arxiv_papers(category: str = "ai", limit: int = 10) -> list[dict]:
    if category not in QUERIES:
        return []

    try:
        r = requests.get(
            ARXIV_BASE,
            params={
                "search_query": QUERIES[category],
                "sortBy": "submittedDate",
                "sortOrder": "descending",
                "max_results": limit,
            },
            timeout=15,
        )
        r.raise_for_status()
        root = ET.fromstring(r.text)
    except Exception:
        return []

    results = []
    for entry in root.findall("atom:entry", NS):
        title_el = entry.find("atom:title", NS)
        summary_el = entry.find("atom:summary", NS)
        link_el = entry.find("atom:id", NS)
        published_el = entry.find("atom:published", NS)

        if title_el is None or link_el is None:
            continue

        title = title_el.text.strip().replace("\n", " ")
        url = link_el.text.strip()
        summary = (summary_el.text or "").strip().replace("\n", " ")[:300]
        published = published_el.text.strip() if published_el is not None else ""

        results.append({
            "title": title,
            "url": url,
            "source": "arXiv",
            "summary": summary,
            "published_at": published,
            "category": category,
        })

    return results
