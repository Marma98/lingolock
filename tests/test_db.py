"""Tests for database initialisation and CRUD operations."""

import os
import sys
import tempfile
import pytest

# Point at a temp DB for tests
_tmp = tempfile.mkdtemp()
os.environ["LINGOLOCK_DB"] = os.path.join(_tmp, "test.db")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database.db import init_db, get_connection
from database import queries as Q


@pytest.fixture(autouse=True)
def setup_db():
    init_db()
    yield
    # Clean state: wipe tables between tests
    conn = get_connection()
    conn.executescript("""
        DELETE FROM unlock_attempts;
        DELETE FROM words;
        DELETE FROM sessions;
        DELETE FROM blocked_apps;
        DELETE FROM app_settings;
    """)
    conn.commit()
    init_db()   # re-seed defaults


class TestWords:
    def test_add_and_get_word(self):
        wid = Q.add_word("gatto", "cat")
        words = Q.get_all_words()
        assert any(w.id == wid and w.italian == "gatto" for w in words)

    def test_delete_word(self):
        wid = Q.add_word("cane", "dog")
        Q.delete_word(wid)
        assert Q.get_word_by_id(wid) is None

    def test_words_for_challenge_order(self):
        # Give ALL existing words a perfect success rate first
        conn = get_connection()
        conn.execute("UPDATE words SET total_shown=10, total_correct=10")
        conn.commit()

        # Now add a word with a terrible success rate (shown but never correct)
        bad_id = Q.add_word("difficile", "difficult")
        conn.execute("UPDATE words SET total_shown=5, total_correct=0 WHERE id=?", (bad_id,))
        conn.commit()

        words = Q.get_words_for_challenge(1)
        assert words[0].id == bad_id

    def test_record_word_result(self):
        wid = Q.add_word("libro", "book")
        Q.record_word_result(wid, correct=True)
        w = Q.get_word_by_id(wid)
        assert w.total_shown   == 1
        assert w.total_correct == 1
        assert w.correct_streak == 1

    def test_record_wrong_resets_streak(self):
        wid = Q.add_word("penna", "pen")
        Q.record_word_result(wid, True)
        Q.record_word_result(wid, False)
        w = Q.get_word_by_id(wid)
        assert w.correct_streak == 0
        assert w.total_shown    == 2
        assert w.total_correct  == 1


class TestSessions:
    def test_add_and_get_session(self):
        sid = Q.add_session("Evening", "18:00", "22:00", "0,1,2")
        sessions = Q.get_all_sessions()
        assert any(s.id == sid and s.name == "Evening" for s in sessions)

    def test_delete_session(self):
        sid = Q.add_session("Night", "22:00", "23:59")
        Q.delete_session(sid)
        assert Q.get_session_by_id(sid) is None


class TestBlockedApps:
    def test_defaults_seeded(self):
        apps = Q.get_all_blocked_apps()
        assert any(a.package_name == "com.instagram.android" for a in apps)

    def test_toggle_enabled(self):
        Q.set_blocked_app_enabled("com.instagram.android", False)
        pkgs = Q.get_enabled_blocked_packages()
        assert "com.instagram.android" not in pkgs
        Q.set_blocked_app_enabled("com.instagram.android", True)
        pkgs = Q.get_enabled_blocked_packages()
        assert "com.instagram.android" in pkgs


class TestSettings:
    def test_get_default_setting(self):
        val = Q.get_setting("base_words")
        assert val == "3"

    def test_set_and_get(self):
        Q.set_setting("base_words", "5")
        assert Q.get_setting("base_words") == "5"


class TestUnlockAttempts:
    def test_add_attempt(self):
        sessions = Q.get_all_sessions()
        assert sessions
        sid = sessions[0].id
        Q.add_unlock_attempt(sid, "com.instagram.android", 3, 30, "passed", 1.0)
        stats = Q.get_stats_today()
        assert stats["total"] >= 1
        assert stats["passed"] >= 1

    def test_count_attempts_today(self):
        sessions = Q.get_all_sessions()
        sid = sessions[0].id
        for _ in range(3):
            Q.add_unlock_attempt(sid, "com.tiktok.android", 3, 30, "failed", 0.0)
        count = Q.count_attempts_today_in_session(sid)
        assert count >= 3
