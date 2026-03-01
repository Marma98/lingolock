"""LingoLock — main entry point.

Initialises the database, sets up KivyMD theme, registers all screens,
and starts the background monitor service (Android only).
"""

import os
import sys

# Ensure src/ is on the path when launched directly.
_SRC = os.path.dirname(os.path.abspath(__file__))
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, NoTransition
from kivy.clock import Clock

from database.db import init_db
from services.ipc import read_trigger, ack_trigger

# Screen imports
from ui.screens.home_screen      import HomeScreen
from ui.screens.challenge_screen import ChallengeScreen
from ui.screens.vocab_screen     import VocabScreen
from ui.screens.sessions_screen  import SessionsScreen
from ui.screens.settings_screen  import SettingsScreen

# KV file paths
_KV_DIR = os.path.join(_SRC, "ui", "kv")
_KV_FILES = ["home", "challenge", "vocab", "sessions", "settings"]


class LingoLockApp(MDApp):
    def build(self):
        # DB must be ready before any screen's on_enter() fires
        init_db()

        self.theme_cls.theme_style      = "Light"
        self.theme_cls.material_style   = "M3"
        self.theme_cls.primary_palette  = "DeepPurple"
        self.theme_cls.accent_palette   = "Amber"

        # Load KV files
        for name in _KV_FILES:
            kv_path = os.path.join(_KV_DIR, f"{name}.kv")
            Builder.load_file(kv_path)

        sm = ScreenManager(transition=NoTransition())
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(ChallengeScreen(name="challenge"))
        sm.add_widget(VocabScreen(name="vocab"))
        sm.add_widget(SessionsScreen(name="sessions"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm

    def on_start(self):
        self._start_monitor_service()
        # Poll IPC file every 2 seconds for desktop testing
        Clock.schedule_interval(self._poll_ipc, 2.0)

    def _start_monitor_service(self):
        try:
            from android import AndroidService  # type: ignore
            service = AndroidService("LingoLock Monitor", "Blocking active")
            service.start("Monitor started")
            self.service = service
        except ImportError:
            pass  # Not on Android; service runs separately or via debug trigger

    def _poll_ipc(self, *_):
        trigger = read_trigger()
        if trigger:
            ack_trigger()
            pkg = trigger.get("package", "")
            if pkg:
                challenge: ChallengeScreen = self.root.get_screen("challenge")
                challenge.trigger_package = pkg
                self.root.current = "challenge"

    def on_new_intent(self, intent):
        """Called by p4a when the activity receives a new Intent."""
        try:
            pkg = intent.getStringExtra("trigger_package")
            if pkg:
                challenge: ChallengeScreen = self.root.get_screen("challenge")
                challenge.trigger_package = pkg
                self.root.current = "challenge"
        except Exception:
            pass


if __name__ == "__main__":
    LingoLockApp().run()
