"""Vocabulary management screen."""

from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.boxlayout import BoxLayout
from database.queries import get_all_words, add_word, delete_word
from database.models import Word


class AddWordDialog(BoxLayout):
    pass


class VocabScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dialog: MDDialog | None = None

    def on_enter(self):
        self._refresh_list()

    def _refresh_list(self):
        self.ids.word_list.clear_widgets()
        for word in get_all_words():
            item = TwoLineListItem(
                text=word.italian,
                secondary_text=f"{word.english}  |  {word.direction}  |  diff {word.difficulty}",
            )
            item.word_id = word.id
            item.bind(on_release=lambda i, w=word: self._confirm_delete(w))
            self.ids.word_list.add_widget(item)

    def open_add_dialog(self):
        self._it_field = MDTextField(hint_text="Italian", mode="rectangle")
        self._en_field = MDTextField(hint_text="English",  mode="rectangle")

        content = BoxLayout(orientation="vertical", spacing="8dp", size_hint_y=None, height="120dp")
        content.add_widget(self._it_field)
        content.add_widget(self._en_field)

        self._dialog = MDDialog(
            title="Add word",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="Add",   on_release=self._do_add),
            ],
        )
        self._dialog.open()

    def _do_add(self, *_):
        italian = self._it_field.text.strip()
        english = self._en_field.text.strip()
        if italian and english:
            add_word(italian, english)
            self._dialog.dismiss()
            self._refresh_list()

    def _confirm_delete(self, word: Word):
        dlg = MDDialog(
            title=f"Delete '{word.italian}'?",
            text="This word will be permanently removed.",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda *_: dlg.dismiss()),
                MDRaisedButton(
                    text="Delete",
                    on_release=lambda *_: self._do_delete(word.id, dlg),
                ),
            ],
        )
        dlg.open()

    def _do_delete(self, word_id: int, dlg: MDDialog):
        delete_word(word_id)
        dlg.dismiss()
        self._refresh_list()
