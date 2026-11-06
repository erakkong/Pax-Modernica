"""
Unit tests for Pax Modernica Simulation Clock.
"""

import pytest
from server.simulation.clock import GameClock

def test_initial_clock_state():
    clock = GameClock(year=0, month=1, day=1, historical_base_year=1700)
    assert clock.year == 0
    assert clock.month == 1
    assert clock.day == 1
    assert clock.historical_year == 1700
    assert clock.formatted_date() == "Jahr 0, 1. Januar"
    assert "Ref: 1700" in clock.formatted_full()

def test_clock_tick_advancement():
    clock = GameClock(year=0, month=1, day=1, minute_of_day=0, speed_multiplier=1.0, is_paused=False)
    # 1 real second = 2 game minutes
    res = clock.tick(1.0)
    assert res["advanced"] is True
    assert clock.minute_of_day == 2

    # Advance 720 real seconds (1440 game minutes = 1 game day)
    # We do it by passing 720.0 to tick
    res = clock.tick(719.0)
    assert res["new_day"] is True
    assert clock.day == 2

def test_clock_month_and_year_rollover():
    # Day 30, minute 1438
    clock = GameClock(year=0, month=1, day=30, minute_of_day=1438, speed_multiplier=1.0, is_paused=False)
    res = clock.tick(1.0) # +2 game mins -> day rolls over, month rolls over to 2
    assert res["new_month"] is True
    assert clock.month == 2
    assert clock.day == 1

    # End of year test
    clock.month = 12
    clock.day = 30
    clock.minute_of_day = 1438
    res = clock.tick(1.0)
    assert res["new_year"] is True
    assert clock.year == 1
    assert clock.month == 1
    assert clock.day == 1
    assert clock.historical_year == 1701

def test_clock_pause():
    clock = GameClock(year=0, month=1, day=1, is_paused=True)
    res = clock.tick(10.0)
    assert res["advanced"] is False
    assert clock.day == 1
    assert clock.minute_of_day == 0
