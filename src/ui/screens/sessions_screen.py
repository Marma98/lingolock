"""Time-block / session management screen."""

from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineIconListItem, IconLeftWidget
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.boxlayout import BoxLayout
from database.queries import get_all_sessions, add_session, delete_session, update_session
from database.models import Session
from logic.session_manager import _session_is_active_now


_DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


class SessionsScreen(MDScreen):
    def on_enter(self):
        self._refresh_list()

    def _refresh_list(self):
        self.ids.session_list.clear_widgets()
        for session in get_all_sessions():
            active = _session_is_active_now(session)
            days   = ", ".join(
                _DAY_LABELS[int(d)] for d in session.days_active.split(",") if d.strip()
            )
            icon = IconLeftWidget(
                icon="clock-check" if active else "clock-outline",
            )
            item = TwoLineIconListItem(
                text=session.name,
                secondary_text=f"{session.start_time} – {session.end_time}  |  {days}",
            )
            item.add_widget(icon)
            item.session = session
            item.bind(on_release=lambda i: self._confirm_delete(i.session))
            self.ids.session_list.add_widget(item)

    def open_add_dialog(self):
        self._name_field  = MDTextField(hint_text="Name",       mode="rectangle")
        self._start_field = MDTextField(hint_text="Start HH:MM", mode="rectangle", text="08:00")
        self._end_field   = MDTextField(hint_text="End HH:MM",   mode="rectangle", text="22:00")
        self._days_field  = MDTextField(hint_text="Days (0=Mon,…,6=Sun)", mode="rectangle", text="0,1,2,3,4")

        content = BoxLayout(orientation="vertical", spacing="8dp",
                            size_hint_y=None, height="240dp")
        for field in (self._name_field, self._start_field, self._end_field, self._days_field):
            content.add_widget(field)

        self._dialog = MDDialog(
            title="Add session",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="Save",  on_release=self._do_add),
            ],
        )
        self._dialog.open()

    def _do_add(self, *_):
        name  = self._name_field.text.strip()
        start = self._start_field.text.strip()
        end   = self._end_field.text.strip()
        days  = self._days_field.text.strip()
        if name and start and end:
            add_session(name, start, end, days)
            self._dialog.dismiss()
            self._refresh_list()

    def _confirm_delete(self, session: Session):
        dlg = MDDialog(
            title=f"Delete '{session.name}'?",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda *_: dlg.dismiss()),
                MDRaisedButton(
                    text="Delete",
                    on_release=lambda *_: self._do_delete(session.id, dlg),
                ),
            ],
        )
        dlg.open()

    def _do_delete(self, session_id: int, dlg: MDDialog):
        delete_session(session_id)
        dlg.dismiss()
        self._refresh_list()
