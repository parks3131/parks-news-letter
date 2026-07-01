#!/usr/bin/env python3
"""
Parks Daily Brief — Newsletter Runner

Usage:
  python main.py            # Run full pipeline (fetch + send)
  python main.py --dry-run  # Fetch + compose only, don't send
"""
import sys
from datetime import datetime
from agent.tools import (
    tool_get_top_news,
    tool_compose_newsletter,
    tool_get_subscribers,
    tool_send_newsletter,
)


def run_pipeline(dry_run: bool = False):
    date_str = datetime.now().strftime("%A, %B %d, %Y")
    subject = f"Parks Tech USA Daily Brief — {date_str}"

    print("[pipeline] Step 1/5 — Fetching AI news...")
    tool_get_top_news("ai", 10)

    print("[pipeline] Step 2/5 — Fetching Startup/Jobs news...")
    tool_get_top_news("startup_jobs", 10)

    print("[pipeline] Step 3/5 — Fetching Immigration news...")
    tool_get_top_news("immigration", 5)

    print("[pipeline] Step 4/5 — Composing newsletter...")
    result = tool_compose_newsletter()
    print(f"[pipeline] Composed: {result}")

    if dry_run:
        print("[pipeline] DRY RUN — skipping send.")
        return {"status": "dry_run_complete"}

    print("[pipeline] Step 5/5 — Sending...")
    recipients = tool_get_subscribers()
    print(f"[pipeline] Recipients: {recipients}")
    result = tool_send_newsletter(subject=subject, recipients=recipients)
    print(f"[pipeline] Send result: {result}")
    return result


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("[main] DRY RUN — newsletter will not be sent")
    result = run_pipeline(dry_run=dry_run)
    print(f"\n[main] Done: {result}")


if __name__ == "__main__":
    main()
