"""Challenge / gatekeeper screen.

On Android: launched from monitor service via Intent extra "trigger_package".
On desktop: triggered by the debug button in SettingsScreen.
"""

from __future__ import annotations
import time
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ListProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from logic.challenge_engine import (
    build_challenge, compute_difficulty, evaluate_answer,
    calculate_score, passed as challenge_passed,
)
from logic.session_manager import get_current_session
from database.queries import add_unlock_attempt

try:
    from jnius import autoclass  # type: ignore
    PackageManager = autoclass("android.content.pm.PackageManager")
    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    _ON_ANDROID = True
except Exception:
    _ON_ANDROID = False


class ChallengeScreen(MDScreen):
    trigger_package  = StringProperty("")
    time_remaining   = NumericProperty(30)
    current_index    = NumericProperty(0)
    total_words      = NumericProperty(0)
    prompt_text      = StringProperty("")
    feedback_text    = StringProperty("")
    result_color     = ListProperty([1, 1, 1, 1])
    on_android       = BooleanProperty(_ON_ANDROID)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._items:    list  = []
        self._results:  list  = []
        self._timer:    object = None
        self._time_limit: int  = 30
        self._start_time: float = 0.0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_enter(self):
        # Read trigger package from Intent on Android
        if _ON_ANDROID:
            try:
                activity = PythonActivity.mActivity
                intent   = activity.getIntent()
                pkg      = intent.getStringExtra("trigger_package")
                if pkg:
                    self.trigger_package = pkg
            except Exception:
                pass

        session = get_current_session()
        session_id = session.id if session else 1

        word_count, self._time_limit = compute_difficulty(session_id)
        self._items   = build_challenge(word_count)
        self._results = []
        self.total_words    = len(self._items)
        self.time_remaining = self._time_limit
        self._start_time    = time.time()

        if not self._items:
            self._finish(abandoned=True)
            return

        self._load_item(0)
        self._timer = Clock.schedule_interval(self._tick, 1)

    def on_leave(self):
        self._cancel_timer()

    # ── Back button override ──────────────────────────────────────────────────

    def on_back_pressed(self) -> bool:
        """Block the hardware back button."""
        return True

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _tick(self, dt):
        self.time_remaining -= 1
        if self.time_remaining <= 0:
            self._cancel_timer()
            self._finish(abandoned=False)

    def _cancel_timer(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    # ── Word navigation ───────────────────────────────────────────────────────

    def _load_item(self, index: int):
        self.current_index = index
        item = self._items[index]
        direction_label = "IT → EN" if item["direction"] == "it_to_en" else "EN → IT"
        self.prompt_text = f"[{direction_label}]  {item['prompt']}"
        self.feedback_text = ""
        if hasattr(self, "ids") and "answer_field" in self.ids:
            self.ids.answer_field.text = ""
            self.ids.answer_field.focus = True

    def submit_answer(self):
        if self.current_index >= len(self._items):
            return

        given    = self.ids.answer_field.text if hasattr(self, "ids") else ""
        item     = self._items[self.current_index]
        correct  = evaluate_answer(given, item["expected"])
        self._results.append((item["word"].id, correct))

        if correct:
            self.feedback_text = f"Correct!  ({item['expected']})"
            self.result_color  = [0.27, 0.73, 0.27, 1]
        else:
            self.feedback_text = f"Wrong.  Answer: {item['expected']}"
            self.result_color  = [0.8, 0.27, 0.27, 1]

        Clock.schedule_once(self._next_item, 0.9)

    def _next_item(self, *_):
        next_idx = self.current_index + 1
        if next_idx < len(self._items):
            self._load_item(next_idx)
        else:
            self._cancel_timer()
            self._finish(abandoned=False)

    # ── Finish ────────────────────────────────────────────────────────────────

    def _finish(self, abandoned: bool):
        session  = get_current_session()
        session_id = session.id if session else 1

        if abandoned or not self._results:
            outcome = "abandoned"
            score   = 0.0
        else:
            score   = calculate_score(self._results)
            outcome = "passed" if challenge_passed(score) else "failed"

        add_unlock_attempt(
            session_id    = session_id,
            target_app    = self.trigger_package or "unknown",
            words_shown   = len(self._results),
            time_limit_sec= self._time_limit,
            outcome       = outcome,
            score         = score,
        )

        if outcome == "passed":
            self._open_target_app()
            self.manager.current = "home"
        else:
            self.ids.prompt_card.opacity    = 0
            self.feedback_text = (
                f"{'Time up!' if not self._results else 'Challenge failed.'}\n"
                f"Score: {score:.0%}  –  Try again later."
            )
            self.result_color = [0.8, 0.27, 0.27, 1]
            Clock.schedule_once(lambda *_: setattr(self.manager, "current", "home"), 3)

    def _open_target_app(self):
        if not _ON_ANDROID or not self.trigger_package:
            return
        try:
            activity = PythonActivity.mActivity
            pm       = activity.getPackageManager()
            intent   = pm.getLaunchIntentForPackage(self.trigger_package)
            if intent:
                activity.startActivity(intent)
        except Exception as exc:
            print(f"[challenge] failed to open target app: {exc}")

    def exit_desktop(self):
        self._cancel_timer()
        self.manager.current = "home"

    # ── Desktop debug trigger ─────────────────────────────────────────────────

    def debug_trigger(self, package: str = "com.instagram.android"):
        self.trigger_package = package
        self.manager.current = "challenge"
