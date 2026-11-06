"""
Pax Modernica - Authoritative Simulation Clock
Handles the Year-0 calendar progression, speed multipliers, pause states,
and converts between simulation ticks and human-readable historical dates.
"""

import time
from typing import Dict, Any, Optional

MONTH_NAMES_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember"
]

class GameClock:
    """
    Server-authoritative game clock.
    Scale: 1 real second = 2 game minutes (standard default).
    1 game day = 24 hours * 60 mins = 1440 game minutes = 720 real seconds (12 real minutes).
    1 game month = 30 game days = 43,200 game minutes = 21,600 real seconds (6 real hours).
    1 game year = 12 game months = 360 game days = 518,400 game minutes = 259,200 real seconds (72 real hours / 3 real days).
    """

    def __init__(
        self,
        year: int = 0,
        month: int = 1,
        day: int = 1,
        minute_of_day: int = 0,
        historical_base_year: int = 1700,
        speed_multiplier: float = 1.0,
        is_paused: bool = True
    ):
        self.year = year
        self.month = month  # 1-12
        self.day = day      # 1-30
        self.minute_of_day = minute_of_day  # 0-1439
        self.historical_base_year = historical_base_year
        self.speed_multiplier = speed_multiplier
        self.is_paused = is_paused
        self.tick_id = 0
        self.last_real_timestamp = time.time()
        self.offline_multiplier = 0.2

    @property
    def historical_year(self) -> int:
        return self.historical_base_year + self.year

    @property
    def month_name(self) -> str:
        return MONTH_NAMES_DE[self.month - 1]

    def formatted_date(self) -> str:
        """Returns standard UI formatted alternative date."""
        return f"Jahr {self.year}, {self.day}. {self.month_name}"

    def formatted_full(self) -> str:
        """Returns complete date string with historical reference."""
        return f"Jahr {self.year}, {self.day}. {self.month_name} (Ref: {self.historical_year})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tick_id": self.tick_id,
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "minute_of_day": self.minute_of_day,
            "month_name": self.month_name,
            "formatted_date": self.formatted_date(),
            "formatted_full": self.formatted_full(),
            "historical_year": self.historical_year,
            "speed_multiplier": self.speed_multiplier,
            "is_paused": self.is_paused
        }

    def set_speed(self, multiplier: float) -> None:
        """Sets game speed multiplier (e.g. 1.0, 2.0, 5.0)."""
        self.speed_multiplier = max(0.1, min(10.0, multiplier))

    def set_paused(self, paused: bool) -> None:
        self.is_paused = paused
        self.last_real_timestamp = time.time()

    def tick(self, delta_real_seconds: float) -> Dict[str, Any]:
        """
        Advances the clock by delta_real_seconds * speed_multiplier.
        Standard conversion: 1 real second = 2 game minutes.
        """
        if self.is_paused or delta_real_seconds <= 0:
            return {
                "advanced": False,
                "new_day": False,
                "new_month": False,
                "new_year": False,
                "clock": self.to_dict()
            }

        self.tick_id += 1
        
        # 1 real sec = 2 game mins * multiplier
        game_minutes_to_add = int(delta_real_seconds * 2.0 * self.speed_multiplier)
        if game_minutes_to_add < 1:
            game_minutes_to_add = 1

        new_day = False
        new_month = False
        new_year = False

        self.minute_of_day += game_minutes_to_add
        while self.minute_of_day >= 1440:
            self.minute_of_day -= 1440
            self.day += 1
            new_day = True

            if self.day > 30:
                self.day = 1
                self.month += 1
                new_month = True

                if self.month > 12:
                    self.month = 1
                    self.year += 1
                    new_year = True

        return {
            "advanced": True,
            "new_day": new_day,
            "new_month": new_month,
            "new_year": new_year,
            "clock": self.to_dict()
        }
