#!/usr/bin/env python3
"""
Subscriber management CLI.

Usage:
  python manage.py subscribe email@example.com [--name "John Doe"]
  python manage.py unsubscribe email@example.com
  python manage.py list
"""
import sys
from subscribers.db import subscribe, unsubscribe, list_subscribers


def cmd_subscribe(args):
    if not args:
        print("Usage: python manage.py subscribe <email> [--name <name>]")
        sys.exit(1)
    email = args[0]
    name = ""
    if "--name" in args:
        idx = args.index("--name")
        name = args[idx + 1] if idx + 1 < len(args) else ""
    ok = subscribe(email, name)
    if ok:
        print(f"✓ Subscribed: {email}" + (f" ({name})" if name else ""))
    else:
        print(f"✗ Failed to subscribe {email}")


def cmd_unsubscribe(args):
    if not args:
        print("Usage: python manage.py unsubscribe <email>")
        sys.exit(1)
    email = args[0]
    ok = unsubscribe(email)
    if ok:
        print(f"✓ Unsubscribed: {email}")
    else:
        print(f"✗ {email} not found or already unsubscribed")


def cmd_list(_):
    subs = list_subscribers()
    if not subs:
        print("No subscribers yet.")
        return
    print(f"\n{'EMAIL':<35} {'NAME':<20} {'STATUS':<12} {'SINCE'}")
    print("-" * 85)
    for s in subs:
        status = "active" if s["active"] else "unsubscribed"
        print(f"{s['email']:<35} {s['name']:<20} {status:<12} {s['subscribed_at']}")
    active = sum(1 for s in subs if s["active"])
    print(f"\nTotal: {len(subs)} ({active} active)")


COMMANDS = {
    "subscribe": cmd_subscribe,
    "unsubscribe": cmd_unsubscribe,
    "list": cmd_list,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("Commands: subscribe | unsubscribe | list")
        sys.exit(1)
    COMMANDS[sys.argv[1]](sys.argv[2:])
