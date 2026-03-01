"""Named query functions — all DB access goes through here."""

from __future__ import annotations
from typing import List, Optional, Tuple
from .db import get_connection
from .models import Word, Session, UnlockAttempt, BlockedApp, AppSetting


# ── Words ─────────────────────────────────────────────────────────────────────

def get_all_words() -> List[Word]:
    rows = get_connection().execute("SELECT * FROM words ORDER BY id").fetchall()
    return [_row_to_word(r) for r in rows]


def get_word_by_id(word_id: int) -> Optional[Word]:
    row = get_connection().execute("SELECT * FROM words WHERE id=?", (word_id,)).fetchone()
    return _row_to_word(row) if row else None


def add_word(italian: str, english: str, direction: str = "both", difficulty: int = 1) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO words (italian, english, direction, difficulty) VALUES (?,?,?,?)",
        (italian.strip(), english.strip(), direction, difficulty),
    )
    conn.commit()
    return cur.lastrowid


def update_word(word: Word):
    conn = get_connection()
    conn.execute(
        """UPDATE words SET italian=?, english=?, direction=?, difficulty=?,
           correct_streak=?, total_shown=?, total_correct=? WHERE id=?""",
        (word.italian, word.english, word.direction, word.difficulty,
         word.correct_streak, word.total_shown, word.total_correct, word.id),
    )
    conn.commit()


def delete_word(word_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM words WHERE id=?", (word_id,))
    conn.commit()


def get_words_for_challenge(limit: int) -> List[Word]:
    """Return words sorted by success rate ascending (worst first)."""
    rows = get_connection().execute(
        """SELECT * FROM words
           ORDER BY (total_correct * 1.0 / MAX(total_shown, 1)) ASC, RANDOM()
           LIMIT ?""",
        (limit,),
    ).fetchall()
    return [_row_to_word(r) for r in rows]


def record_word_result(word_id: int, correct: bool):
    conn = get_connection()
    if correct:
        conn.execute(
            """UPDATE words SET total_shown=total_shown+1, total_correct=total_correct+1,
               correct_streak=correct_streak+1 WHERE id=?""",
            (word_id,),
        )
    else:
        conn.execute(
            """UPDATE words SET total_shown=total_shown+1, correct_streak=0 WHERE id=?""",
            (word_id,),
        )
    conn.commit()


def _row_to_word(r) -> Word:
    return Word(
        id=r["id"], italian=r["italian"], english=r["english"],
        direction=r["direction"], difficulty=r["difficulty"],
        correct_streak=r["correct_streak"], total_shown=r["total_shown"],
        total_correct=r["total_correct"], created_at=r["created_at"],
    )


# ── Sessions ──────────────────────────────────────────────────────────────────

def get_all_sessions() -> List[Session]:
    rows = get_connection().execute("SELECT * FROM sessions ORDER BY start_time").fetchall()
    return [_row_to_session(r) for r in rows]


def get_session_by_id(session_id: int) -> Optional[Session]:
    row = get_connection().execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    return _row_to_session(row) if row else None


def add_session(name: str, start_time: str, end_time: str, days_active: str = "0,1,2,3,4") -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO sessions (name, start_time, end_time, days_active) VALUES (?,?,?,?)",
        (name, start_time, end_time, days_active),
    )
    conn.commit()
    return cur.lastrowid


def update_session(session: Session):
    conn = get_connection()
    conn.execute(
        """UPDATE sessions SET name=?, start_time=?, end_time=?, days_active=?, is_enabled=?
           WHERE id=?""",
        (session.name, session.start_time, session.end_time,
         session.days_active, session.is_enabled, session.id),
    )
    conn.commit()


def delete_session(session_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()


def _row_to_session(r) -> Session:
    return Session(
        id=r["id"], name=r["name"], start_time=r["start_time"],
        end_time=r["end_time"], days_active=r["days_active"], is_enabled=r["is_enabled"],
    )


# ── Unlock Attempts ───────────────────────────────────────────────────────────

def count_attempts_today_in_session(session_id: int) -> int:
    row = get_connection().execute(
        """SELECT COUNT(*) FROM unlock_attempts
           WHERE session_id=? AND session_date=date('now')""",
        (session_id,),
    ).fetchone()
    return row[0]


def add_unlock_attempt(
    session_id: int, target_app: str, words_shown: int,
    time_limit_sec: int, outcome: str, score: float,
) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO unlock_attempts
           (session_id, target_app, words_shown, time_limit_sec, outcome, score)
           VALUES (?,?,?,?,?,?)""",
        (session_id, target_app, words_shown, time_limit_sec, outcome, score),
    )
    conn.commit()
    return cur.lastrowid


def get_attempts_today() -> List[dict]:
    rows = get_connection().execute(
        """SELECT ua.*, s.name AS session_name FROM unlock_attempts ua
           JOIN sessions s ON s.id = ua.session_id
           WHERE ua.session_date = date('now')
           ORDER BY ua.attempt_time DESC""",
    ).fetchall()
    return [dict(r) for r in rows]


def get_stats_today() -> dict:
    row = get_connection().execute(
        """SELECT
               COUNT(*) AS total,
               SUM(CASE WHEN outcome='passed'   THEN 1 ELSE 0 END) AS passed,
               SUM(CASE WHEN outcome='failed'   THEN 1 ELSE 0 END) AS failed,
               SUM(CASE WHEN outcome='abandoned'THEN 1 ELSE 0 END) AS abandoned,
               ROUND(AVG(score),2) AS avg_score
           FROM unlock_attempts WHERE session_date=date('now')""",
    ).fetchone()
    return dict(row) if row else {}


# ── Blocked Apps ──────────────────────────────────────────────────────────────

def get_all_blocked_apps() -> List[BlockedApp]:
    rows = get_connection().execute(
        "SELECT * FROM blocked_apps ORDER BY display_name"
    ).fetchall()
    return [_row_to_blocked(r) for r in rows]


def get_enabled_blocked_packages() -> List[str]:
    rows = get_connection().execute(
        "SELECT package_name FROM blocked_apps WHERE is_enabled=1"
    ).fetchall()
    return [r["package_name"] for r in rows]


def set_blocked_app_enabled(package_name: str, enabled: bool):
    conn = get_connection()
    conn.execute(
        "UPDATE blocked_apps SET is_enabled=? WHERE package_name=?",
        (1 if enabled else 0, package_name),
    )
    conn.commit()


def add_blocked_app(package_name: str, display_name: str) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT OR IGNORE INTO blocked_apps (package_name, display_name) VALUES (?,?)",
        (package_name, display_name),
    )
    conn.commit()
    return cur.lastrowid


def _row_to_blocked(r) -> BlockedApp:
    return BlockedApp(
        id=r["id"], package_name=r["package_name"],
        display_name=r["display_name"], is_enabled=r["is_enabled"],
    )


# ── Settings ──────────────────────────────────────────────────────────────────

def get_setting(key: str, default: str = "") -> str:
    row = get_connection().execute(
        "SELECT value FROM app_settings WHERE key=?", (key,)
    ).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO app_settings (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    conn.commit()


def get_all_settings() -> dict:
    rows = get_connection().execute("SELECT key, value FROM app_settings").fetchall()
    return {r["key"]: r["value"] for r in rows}
