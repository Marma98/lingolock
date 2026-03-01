"""Challenge building, difficulty computation, and answer evaluation."""

from __future__ import annotations
import random
from typing import List, Tuple, Optional
from database.queries import (
    count_attempts_today_in_session,
    get_words_for_challenge,
    get_setting,
    record_word_result,
)
from database.models import Word


# ── Difficulty ────────────────────────────────────────────────────────────────

def compute_difficulty(session_id: int) -> Tuple[int, int]:
    """
    Return (word_count, time_limit_sec) based on how many attempts
    were made today in this session (adaptive difficulty).
    """
    n = count_attempts_today_in_session(session_id)

    base_words = int(get_setting("base_words", "3"))
    increment  = int(get_setting("increment",  "2"))
    max_words  = int(get_setting("max_words",  "10"))
    base_time  = int(get_setting("base_time",  "30"))
    decrement  = int(get_setting("decrement",  "5"))
    min_time   = int(get_setting("min_time",   "10"))

    word_count = min(base_words + increment * n, max_words)
    time_limit = max(base_time - decrement * n, min_time)

    return word_count, time_limit


# ── Challenge Building ────────────────────────────────────────────────────────

def build_challenge(word_count: int) -> List[dict]:
    """
    Select *word_count* words (worst success-rate first) and assign
    a direction for each item.

    Returns a list of dicts:
        { "word": Word, "direction": "it_to_en"|"en_to_it",
          "prompt": str, "expected": str }
    """
    words = get_words_for_challenge(word_count)
    if not words:
        return []

    items = []
    for w in words:
        direction = _pick_direction(w)
        if direction == "it_to_en":
            prompt   = w.italian
            expected = w.english
        else:
            prompt   = w.english
            expected = w.italian
        items.append({
            "word":      w,
            "direction": direction,
            "prompt":    prompt,
            "expected":  expected,
        })

    random.shuffle(items)
    return items


def _pick_direction(word: Word) -> str:
    if word.direction == "it_to_en":
        return "it_to_en"
    if word.direction == "en_to_it":
        return "en_to_it"
    # "both" → random
    return random.choice(["it_to_en", "en_to_it"])


# ── Answer Evaluation ─────────────────────────────────────────────────────────

def evaluate_answer(given: str, expected: str) -> bool:
    """
    Case-insensitive, whitespace-stripped comparison.
    Accepts Levenshtein distance ≤ 1 (single typo tolerance).
    """
    g = given.strip().lower()
    e = expected.strip().lower()
    if g == e:
        return True
    return _levenshtein(g, e) <= 1


def _levenshtein(a: str, b: str) -> int:
    """Optimal string alignment distance (supports transpositions)."""
    la, lb = len(a), len(b)
    # dp[i][j] = OSA distance between a[:i] and b[:j]
    dp = [[0] * (lb + 1) for _ in range(la + 1)]
    for i in range(la + 1):
        dp[i][0] = i
    for j in range(lb + 1):
        dp[0][j] = j
    for i in range(1, la + 1):
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,          # deletion
                dp[i][j - 1] + 1,          # insertion
                dp[i - 1][j - 1] + cost,   # substitution
            )
            # transposition
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)
    return dp[la][lb]


# ── Score Calculation ─────────────────────────────────────────────────────────

def calculate_score(results: List[Tuple[int, bool]]) -> float:
    """
    *results*: list of (word_id, correct).
    Returns score 0.0–1.0 and records each result in the DB.
    """
    if not results:
        return 0.0
    for word_id, correct in results:
        record_word_result(word_id, correct)
    correct_count = sum(1 for _, c in results if c)
    return correct_count / len(results)


def passed(score: float) -> bool:
    threshold = float(get_setting("pass_score", "0.6"))
    return score >= threshold
