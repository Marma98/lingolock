"""Settings screen — blocked apps, difficulty, permissions, debug."""

from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineAvatarIconListItem, IconLeftWidget
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.boxlayout import BoxLayout
from database.queries import (
    get_all_blocked_apps, set_blocked_app_enabled,
    get_all_settings, set_setting,
)
from logic.permissions import (
    is_android, check_all_permissions,
    request_usage_stats_permission, request_overlay_permission,
    request_accessibility_settings,
)


class SettingsScreen(MDScreen):
    def on_enter(self):
        self._load_blocked_apps()
        self._load_permissions()
        self._load_difficulty()

    # ── Blocked apps ──────────────────────────────────────────────────────────

    def _load_blocked_apps(self):
        self.ids.app_list.clear_widgets()
        for app in get_all_blocked_apps():
            item = TwoLineAvatarIconListItem(
                text=app.display_name,
                secondary_text=app.package_name,
            )
            chk = MDCheckbox(
                active=bool(app.is_enabled),
                size_hint=(None, None), size=("48dp", "48dp"),
            )
            pkg = app.package_name
            chk.bind(active=lambda cb, val, p=pkg: set_blocked_app_enabled(p, val))
            item.add_widget(chk)
            self.ids.app_list.add_widget(item)

    # ── Difficulty settings ───────────────────────────────────────────────────

    def _load_difficulty(self):
        s = get_all_settings()
        self.ids.base_words_field.text  = s.get("base_words",  "3")
        self.ids.increment_field.text   = s.get("increment",   "2")
        self.ids.base_time_field.text   = s.get("base_time",   "30")
        self.ids.decrement_field.text   = s.get("decrement",   "5")

    def save_difficulty(self):
        set_setting("base_words", self.ids.base_words_field.text)
        set_setting("increment",  self.ids.increment_field.text)
        set_setting("base_time",  self.ids.base_time_field.text)
        set_setting("decrement",  self.ids.decrement_field.text)
        self.ids.diff_saved_label.text = "Saved!"

    # ── Permissions ───────────────────────────────────────────────────────────

    def _load_permissions(self):
        perms = check_all_permissions()
        ok = "[color=44bb44]OK[/color]"
        no = "[color=cc4444]MISSING[/color]"
        self.ids.perm_usage_label.text      = f"Usage Stats:   {ok if perms['usage_stats'] else no}"
        self.ids.perm_overlay_label.text    = f"Overlay:       {ok if perms['overlay'] else no}"
        self.ids.android_label.text         = "Android" if is_android() else "Desktop (no Android perms needed)"

    def req_usage(self):
        request_usage_stats_permission()

    def req_overlay(self):
        request_overlay_permission()

    def req_accessibility(self):
        request_accessibility_settings()

    # ── Debug ─────────────────────────────────────────────────────────────────

    def debug_trigger_challenge(self):
        challenge = self.manager.get_screen("challenge")
        challenge.debug_trigger("com.instagram.android")
