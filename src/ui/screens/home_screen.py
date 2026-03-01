"""Home / dashboard screen."""

from kivymd.uix.screen import MDScreen
from kivy.clock import Clock
from database.queries import get_stats_today, get_attempts_today
from logic.session_manager import is_blocking_active, get_current_session


class HomeScreen(MDScreen):
    def on_enter(self):
        self._refresh_event = Clock.schedule_interval(self._refresh, 5)
        self._refresh()

    def on_leave(self):
        if hasattr(self, "_refresh_event"):
            self._refresh_event.cancel()

    def _refresh(self, *_):
        stats   = get_stats_today()
        session = get_current_session()

        # Status chip
        if session:
            status = f"[color=44bb44]ACTIVE[/color]  –  session: {session.name}"
        else:
            status = "[color=aaaaaa]Inactive[/color]"
        self.ids.status_label.text = status

        # Stats
        total    = stats.get("total")    or 0
        passed   = stats.get("passed")   or 0
        failed   = stats.get("failed")   or 0
        avg      = stats.get("avg_score") or 0.0
        self.ids.stats_label.text = (
            f"Today:  {total} attempts  |  {passed} passed  |  {failed} failed\n"
            f"Average score: {avg:.0%}"
        )

        # Recent attempts
        attempts = get_attempts_today()[:5]
        lines = []
        for a in attempts:
            icon = "" if a["outcome"] == "passed" else ""
            lines.append(f"{icon}  {a['target_app'].split('.')[-1]}  –  {a['outcome']}  ({a['score']:.0%})")
        self.ids.recent_label.text = "\n".join(lines) if lines else "No attempts yet today."
