"""Determine whether blocking is currently active."""

from __future__ import annotations
from datetime import datetime, time
from typing import Optional
from database.queries import get_all_sessions
from database.models import Session


def _parse_time(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


def _session_is_active_now(session: Session) -> bool:
    """Return True if *session* is enabled and covers the current moment."""
    if not session.is_enabled:
        return False

    now = datetime.now()
    weekday = now.weekday()  # 0=Monday … 6=Sunday

    active_days = {int(d.strip()) for d in session.days_active.split(",") if d.strip()}
    if weekday not in active_days:
        return False

    current = now.time().replace(second=0, microsecond=0)
    start = _parse_time(session.start_time)
    end = _parse_time(session.end_time)

    if start <= end:
        return start <= current < end
    else:
        # overnight session: e.g. 22:00 – 06:00
        return current >= start or current < end


def is_blocking_active() -> bool:
    """Return True if any session is currently active."""
    return get_current_session() is not None


def get_current_session() -> Optional[Session]:
    """Return the first active session, or None."""
    for session in get_all_sessions():
        if _session_is_active_now(session):
            return session
    return None
