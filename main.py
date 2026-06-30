#!/usr/bin/env python3
"""
Parks Daily Brief — Newsletter Runner

Usage:
  python main.py            # Run full pipeline (fetch + send)
  python main.py --dry-run  # Fetch + compose only, don't send
"""
import sys
from agent.agent import run_newsletter_agent


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("[main] DRY RUN — newsletter will not be sent")

    result = run_newsletter_agent(dry_run=dry_run)
    print(f"\n[main] Result: {result['status']}")
    if result.get("summary"):
        print(f"[main] {result['summary']}")


if __name__ == "__main__":
    main()
