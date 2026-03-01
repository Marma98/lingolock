"""Tests for challenge_engine — compute_difficulty, evaluate_answer, build_challenge."""

import os
import sys
import tempfile
from unittest.mock import patch
import pytest

_tmp = tempfile.mkdtemp()
os.environ["LINGOLOCK_DB"] = os.path.join(_tmp, "test_ce.db")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from database.db import init_db
from database import queries as Q


@pytest.fixture(autouse=True)
def setup():
    init_db()
    conn = Q.get_connection()
    conn.execute("DELETE FROM words")
    conn.execute("DELETE FROM unlock_attempts")
    conn.execute("DELETE FROM sessions")
    conn.commit()
    # Add a default session
    Q.add_session("Test", "00:00", "23:59", "0,1,2,3,4,5,6")
    # Add some words
    for it, en in [("gatto","cat"),("cane","dog"),("casa","house"),
                   ("libro","book"),("mela","apple")]:
        Q.add_word(it, en)
    yield


class TestEvaluateAnswer:
    def test_exact_match(self):
        from logic.challenge_engine import evaluate_answer
        assert evaluate_answer("cat", "cat") is True

    def test_case_insensitive(self):
        from logic.challenge_engine import evaluate_answer
        assert evaluate_answer("Cat", "cat") is True
        assert evaluate_answer("CAT", "cat") is True

    def test_strip_whitespace(self):
        from logic.challenge_engine import evaluate_answer
        assert evaluate_answer("  cat  ", "cat") is True

    def test_levenshtein_1_accepted(self):
        from logic.challenge_engine import evaluate_answer
        # "houes" → "house": one transposition (e↔s)
        assert evaluate_answer("houes", "house") is True
        # "cta" → "cat": one transposition
        assert evaluate_answer("cta", "cat") is True
        # "grazie" → "grazei": one transposition (i↔e)
        assert evaluate_answer("grazei", "grazie") is True

    def test_levenshtein_2_rejected(self):
        from logic.challenge_engine import evaluate_answer
        # clearly wrong answers
        assert evaluate_answer("xyz", "house") is False
        assert evaluate_answer("dog", "cat") is False
        # two edits away
        assert evaluate_answer("hse", "house") is False

    def test_wrong_answer(self):
        from logic.challenge_engine import evaluate_answer
        assert evaluate_answer("dog", "cat") is False


class TestComputeDifficulty:
    def test_first_attempt(self):
        from logic.challenge_engine import compute_difficulty
        sessions = Q.get_all_sessions()
        sid = sessions[0].id
        words, t = compute_difficulty(sid)
        assert words == 3   # base_words default
        assert t     == 30  # base_time default

    def test_difficulty_increases_with_attempts(self):
        from logic.challenge_engine import compute_difficulty
        sessions = Q.get_all_sessions()
        sid = sessions[0].id

        # Simulate 2 prior failed attempts today
        for _ in range(2):
            Q.add_unlock_attempt(sid, "com.instagram.android", 3, 30, "failed", 0.0)

        words, t = compute_difficulty(sid)
        # base_words=3, increment=2, n=2 → 3+4=7
        assert words == 7
        # base_time=30, decrement=5, n=2 → 30-10=20
        assert t == 20

    def test_word_count_capped_at_max(self):
        from logic.challenge_engine import compute_difficulty
        sessions = Q.get_all_sessions()
        sid = sessions[0].id
        # Simulate many attempts to push past max
        for _ in range(10):
            Q.add_unlock_attempt(sid, "com.instagram.android", 3, 30, "failed", 0.0)
        words, _ = compute_difficulty(sid)
        assert words <= 10

    def test_time_floored_at_min(self):
        from logic.challenge_engine import compute_difficulty
        sessions = Q.get_all_sessions()
        sid = sessions[0].id
        for _ in range(10):
            Q.add_unlock_attempt(sid, "com.instagram.android", 3, 30, "failed", 0.0)
        _, t = compute_difficulty(sid)
        assert t >= 10


class TestBuildChallenge:
    def test_returns_correct_count(self):
        from logic.challenge_engine import build_challenge
        items = build_challenge(3)
        assert len(items) == 3

    def test_items_have_required_fields(self):
        from logic.challenge_engine import build_challenge
        items = build_challenge(2)
        for item in items:
            assert "word"      in item
            assert "direction" in item
            assert "prompt"    in item
            assert "expected"  in item

    def test_direction_validity(self):
        from logic.challenge_engine import build_challenge
        items = build_challenge(5)
        for item in items:
            assert item["direction"] in ("it_to_en", "en_to_it")

    def test_it_to_en_direction(self):
        from logic.challenge_engine import build_challenge, _pick_direction
        items = build_challenge(5)
        for item in items:
            if item["direction"] == "it_to_en":
                assert item["prompt"]   == item["word"].italian
                assert item["expected"] == item["word"].english
            else:
                assert item["prompt"]   == item["word"].english
                assert item["expected"] == item["word"].italian


class TestCalculateScore:
    def test_all_correct(self):
        from logic.challenge_engine import calculate_score
        words = Q.get_words_for_challenge(3)
        results = [(w.id, True) for w in words]
        score = calculate_score(results)
        assert score == 1.0

    def test_all_wrong(self):
        from logic.challenge_engine import calculate_score
        words = Q.get_words_for_challenge(3)
        results = [(w.id, False) for w in words]
        score = calculate_score(results)
        assert score == 0.0

    def test_partial(self):
        from logic.challenge_engine import calculate_score
        words = Q.get_words_for_challenge(4)
        results = [(w.id, i < 2) for i, w in enumerate(words)]   # 2 correct / 4
        score = calculate_score(results)
        assert abs(score - 0.5) < 0.01
