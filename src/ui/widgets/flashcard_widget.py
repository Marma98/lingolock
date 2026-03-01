"""Animated flashcard MDCard widget used in ChallengeScreen."""

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.animation import Animation
from kivy.properties import StringProperty, BooleanProperty


class FlashcardWidget(MDCard):
    """A card that displays a word prompt and an answer input area."""

    prompt_text   = StringProperty("")
    result_text   = StringProperty("")
    show_result   = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding     = "16dp"
        self.spacing     = "8dp"
        self.radius      = [12,]
        self.elevation   = 4

    def flash_correct(self):
        """Briefly turn the card green."""
        anim = (
            Animation(md_bg_color=[0.2, 0.8, 0.2, 1], duration=0.15) +
            Animation(md_bg_color=[1, 1, 1, 1], duration=0.3)
        )
        anim.start(self)

    def flash_wrong(self):
        """Briefly turn the card red."""
        anim = (
            Animation(md_bg_color=[0.9, 0.2, 0.2, 1], duration=0.15) +
            Animation(md_bg_color=[1, 1, 1, 1], duration=0.3)
        )
        anim.start(self)

    def shake(self):
        """Horizontal shake animation for wrong answer."""
        ox = self.x
        anim = (
            Animation(x=ox - 10, duration=0.05) +
            Animation(x=ox + 10, duration=0.05) +
            Animation(x=ox - 8,  duration=0.05) +
            Animation(x=ox + 8,  duration=0.05) +
            Animation(x=ox,      duration=0.05)
        )
        anim.start(self)
