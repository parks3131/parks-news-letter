import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "subscribers.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            subscribed_at TEXT DEFAULT (datetime('now')),
            unsubscribed_at TEXT
        )
    """)
    conn.commit()
    return conn


def subscribe(email: str, name: str = "") -> bool:
    email = email.strip().lower()
    with _connect() as conn:
        try:
            conn.execute(
                "INSERT INTO subscribers (email, name) VALUES (?, ?) "
                "ON CONFLICT(email) DO UPDATE SET active=1, unsubscribed_at=NULL",
                (email, name),
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[db] subscribe error: {e}")
            return False


def unsubscribe(email: str) -> bool:
    email = email.strip().lower()
    with _connect() as conn:
        conn.execute(
            "UPDATE subscribers SET active=0, unsubscribed_at=datetime('now') WHERE email=?",
            (email,),
        )
        conn.commit()
        return conn.execute("SELECT changes()").fetchone()[0] > 0


def get_all_subscribers() -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT email FROM subscribers WHERE active=1 ORDER BY subscribed_at"
        ).fetchall()
        return [r[0] for r in rows]


def list_subscribers() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT email, name, active, subscribed_at FROM subscribers ORDER BY subscribed_at"
        ).fetchall()
        return [
            {"email": r[0], "name": r[1], "active": bool(r[2]), "subscribed_at": r[3]}
            for r in rows
        ]
