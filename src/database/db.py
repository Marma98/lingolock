"""Thread-safe SQLite connection management and schema initialisation."""

import sqlite3
import threading
import os

_local = threading.local()

DB_PATH = os.environ.get(
    "LINGOLOCK_DB",
    os.path.join(os.path.expanduser("~"), ".lingolock", "lingolock.db"),
)

_SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS words (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    italian         TEXT    NOT NULL,
    english         TEXT    NOT NULL,
    direction       TEXT    NOT NULL DEFAULT 'both'
                            CHECK(direction IN ('both','it_to_en','en_to_it')),
    difficulty      INTEGER NOT NULL DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 3),
    correct_streak  INTEGER NOT NULL DEFAULT 0,
    total_shown     INTEGER NOT NULL DEFAULT 0,
    total_correct   INTEGER NOT NULL DEFAULT 0,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    start_time  TEXT    NOT NULL,
    end_time    TEXT    NOT NULL,
    days_active TEXT    NOT NULL DEFAULT '0,1,2,3,4',
    is_enabled  INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS unlock_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    target_app      TEXT    NOT NULL,
    attempt_time    TEXT    NOT NULL DEFAULT (datetime('now')),
    words_shown     INTEGER NOT NULL,
    time_limit_sec  INTEGER NOT NULL,
    outcome         TEXT    NOT NULL CHECK(outcome IN ('passed','failed','abandoned')),
    score           REAL    NOT NULL DEFAULT 0.0,
    session_date    TEXT    NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS blocked_apps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    package_name TEXT    NOT NULL UNIQUE,
    display_name TEXT    NOT NULL,
    is_enabled   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS app_settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

_DEFAULT_BLOCKED_APPS = [
    ("com.instagram.android",   "Instagram"),
    ("com.zhiliaoapp.musically", "TikTok"),
    ("com.facebook.katana",     "Facebook"),
    ("com.twitter.android",     "Twitter / X"),
    ("com.snapchat.android",    "Snapchat"),
    ("com.reddit.frontpage",    "Reddit"),
]

_DEFAULT_SETTINGS = {
    "base_words":  "3",
    "increment":   "2",
    "max_words":   "10",
    "base_time":   "30",
    "decrement":   "5",
    "min_time":    "10",
    "pass_score":  "0.6",
    "cooldown_sec": "10",
}

_DEFAULT_SESSION = {
    "name":        "Morning",
    "start_time":  "08:00",
    "end_time":    "22:00",
    "days_active": "0,1,2,3,4,5,6",
}

_DEFAULT_WORDS = [
    ("ciao",          "hello",       "both", 1),
    ("grazie",        "thank you",   "both", 1),
    ("prego",         "you're welcome","both",1),
    ("buongiorno",    "good morning","both", 1),
    ("buonanotte",    "good night",  "both", 1),
    ("per favore",    "please",      "both", 1),
    ("scusi",         "excuse me",   "both", 1),
    ("quanto costa",  "how much",    "both", 2),
    ("non capisco",   "I don't understand","both",2),
    ("mi chiamo",     "my name is",  "both", 2),
]


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Return a per-thread SQLite connection, creating it on first access."""
    if not hasattr(_local, "conn") or _local.conn is None:
        _ensure_dir()
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.row_factory = sqlite3.Row
    return _local.conn


def init_db():
    """Create schema and seed default data (idempotent)."""
    _ensure_dir()
    conn = get_connection()
    conn.executescript(_SCHEMA)

    # Seed blocked apps
    conn.executemany(
        "INSERT OR IGNORE INTO blocked_apps (package_name, display_name) VALUES (?, ?)",
        _DEFAULT_BLOCKED_APPS,
    )

    # Seed settings
    conn.executemany(
        "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
        _DEFAULT_SETTINGS.items(),
    )

    # Seed default session if none exist
    cur = conn.execute("SELECT COUNT(*) FROM sessions")
    if cur.fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO sessions (name, start_time, end_time, days_active) VALUES (?,?,?,?)",
            (
                _DEFAULT_SESSION["name"],
                _DEFAULT_SESSION["start_time"],
                _DEFAULT_SESSION["end_time"],
                _DEFAULT_SESSION["days_active"],
            ),
        )

    # Seed starter vocabulary if none exist
    cur = conn.execute("SELECT COUNT(*) FROM words")
    if cur.fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO words (italian, english, direction, difficulty) VALUES (?,?,?,?)",
            _DEFAULT_WORDS,
        )

    conn.commit()


def close_connection():
    """Close the per-thread connection (call on thread exit)."""
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None
