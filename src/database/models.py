from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Word:
    id: Optional[int]
    italian: str
    english: str
    direction: str = "both"          # "both" | "it_to_en" | "en_to_it"
    difficulty: int = 1              # 1-3
    correct_streak: int = 0
    total_shown: int = 0
    total_correct: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Session:
    id: Optional[int]
    name: str
    start_time: str                  # "HH:MM"
    end_time: str                    # "HH:MM"
    days_active: str = "0,1,2,3,4"  # CSV of weekday indices (0=Mon)
    is_enabled: int = 1


@dataclass
class UnlockAttempt:
    id: Optional[int]
    session_id: int
    target_app: str                  # package name
    attempt_time: str                # ISO datetime
    words_shown: int
    time_limit_sec: int
    outcome: str                     # "passed" | "failed" | "abandoned"
    score: float                     # 0.0 – 1.0
    session_date: str                # "YYYY-MM-DD"


@dataclass
class BlockedApp:
    id: Optional[int]
    package_name: str
    display_name: str
    is_enabled: int = 1


@dataclass
class AppSetting:
    key: str
    value: str
