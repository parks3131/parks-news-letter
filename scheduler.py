#!/usr/bin/env python3
"""
Runs the newsletter every morning at 7:00 AM local time.

Usage:
  python scheduler.py          # Start the scheduler (keep running)
  python scheduler.py --now    # Run once immediately and exit
"""
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from agent.agent import run_newsletter_agent

SEND_HOUR = 7
SEND_MINUTE = 0


def job():
    print("[scheduler] Running newsletter agent...")
    result = run_newsletter_agent(dry_run=False)
    print(f"[scheduler] Done: {result['status']}")


if __name__ == "__main__":
    if "--now" in sys.argv:
        job()
        sys.exit(0)

    scheduler = BlockingScheduler()
    scheduler.add_job(job, CronTrigger(hour=SEND_HOUR, minute=SEND_MINUTE))
    print(f"[scheduler] Newsletter scheduled daily at {SEND_HOUR:02d}:{SEND_MINUTE:02d} local time. Ctrl+C to stop.")
    try:
        scheduler.start()
    except KeyboardInterrupt:
        print("\n[scheduler] Stopped.")
