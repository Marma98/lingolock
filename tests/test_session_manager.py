"""Tests for session_manager — is_blocking_active(), get_current_session()."""

import os
import sys
import tempfile
from datetime import datetime
from unittest.mock import patch
import pytest

_tmp = tempfile.mkdtemp()
os.environ["LINGOLOCK_DB"] = os.path.join(_tmp, "test_sm.db")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database.db import init_db
from database import queries as Q


@pytest.fixture(autouse=True)
def setup():
    init_db()
    conn = Q.get_connection()
    conn.execute("DELETE FROM sessions")
    conn.commit()
    yield
    conn.execute("DELETE FROM sessions")
    conn.commit()


def _fake_now(weekday: int, hour: int, minute: int):
    """Return a datetime with the given weekday (0=Mon) and time."""
    # 2025-01-06 was a Monday (weekday 0)
    from datetime import date
    base = date(2025, 1, 6)   # Monday
    delta = weekday
    from datetime import timedelta
    d = base + timedelta(days=delta)
    return datetime(d.year, d.month, d.day, hour, minute, 0)


class TestIsBlockingActive:
    def test_no_sessions_returns_false(self):
        from logic.session_manager import is_blocking_active
        assert is_blocking_active() is False

    def test_active_session_within_range(self):
        Q.add_session("Work", "08:00", "22:00", "0,1,2,3,4")
        from logic.session_manager import is_blocking_active
        with patch("logic.session_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _fake_now(0, 12, 0)  # Monday 12:00
            assert is_blocking_active() is True

    def test_inactive_before_start(self):
        Q.add_session("Work", "09:00", "22:00", "0")
        from logic.session_manager import is_blocking_active
        with patch("logic.session_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _fake_now(0, 7, 59)  # Monday 07:59
            assert is_blocking_active() is False

    def test_inactive_after_end(self):
        Q.add_session("Work", "09:00", "18:00", "0")
        from logic.session_manager import is_blocking_active
        with patch("logic.session_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _fake_now(0, 18, 1)  # Monday 18:01
            assert is_blocking_active() is False

    def test_inactive_wrong_day(self):
        Q.add_session("Weekdays", "09:00", "22:00", "0,1,2,3,4")
        from logic.session_manager import is_blocking_active
        with patch("logic.session_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _fake_now(5, 12, 0)  # Saturday
            assert is_blocking_active() is False

    def test_disabled_session_not_active(self):
        sid = Q.add_session("Work", "08:00", "22:00", "0,1,2,3,4")
        s   = Q.get_session_by_id(sid)
        s.is_enabled = 0
        Q.update_session(s)
        from logic.session_manager import is_blocking_active
        with patch("logic.session_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _fake_now(0, 12, 0)
            assert is_blocking_active() is False

    def test_overnight_session(self):
        Q.add_session("Night", "22:00", "06:00", "0,1,2,3,4,5,6")
        from logic.session_manager import is_blocking_active
        with patch("logic.session_manager.datetime") as mock_dt:
            mock_dt.now.return_value = _fake_now(0, 23, 0)
            assert is_blocking_active() is True
