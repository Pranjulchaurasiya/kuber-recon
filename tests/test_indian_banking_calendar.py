"""Tests for IndianBankingCalendar & Dynamic Settlement Window Expansion.

Verifies:
1. RBI Rule: All Sundays and 2nd/4th Saturdays are bank holidays.
2. 1st and 3rd Saturdays are active banking days.
3. Statutory holidays (Republic Day, Diwali, Gandhi Jayanti) are respected.
4. Dynamic lookback expansion from T+4 to T+6/T+7 across holiday clusters.
"""

from datetime import date, timedelta
import pytest

from kuber_recon.calendar import IndianBankingCalendar, get_effective_settlement_dates


def test_sundays_and_saturdays():
    cal = IndianBankingCalendar()

    # August 2026 calendar inspection:
    # Aug 1: 1st Saturday -> Working banking day
    # Aug 2: Sunday -> Bank holiday
    # Aug 8: 2nd Saturday -> Bank holiday
    # Aug 9: Sunday -> Bank holiday
    # Aug 15: 3rd Saturday + Independence Day -> Holiday
    # Aug 22: 4th Saturday -> Bank holiday
    # Aug 29: 5th Saturday -> Working banking day
    
    assert cal.is_second_or_fourth_saturday(date(2026, 8, 1)) is False
    assert cal.is_second_or_fourth_saturday(date(2026, 8, 8)) is True
    assert cal.is_second_or_fourth_saturday(date(2026, 8, 15)) is False
    assert cal.is_second_or_fourth_saturday(date(2026, 8, 22)) is True
    assert cal.is_second_or_fourth_saturday(date(2026, 8, 29)) is False

    # Sundays
    assert cal.is_sunday(date(2026, 8, 2)) is True
    assert cal.is_sunday(date(2026, 8, 3)) is False


def test_statutory_rbi_holidays():
    cal = IndianBankingCalendar()

    # Republic Day 2026-01-26 (Monday)
    assert cal.is_banking_day(date(2026, 1, 26)) is False
    # Regular Tuesday 2026-01-27
    assert cal.is_banking_day(date(2026, 1, 27)) is True
    # Gandhi Jayanti 2026-10-02 (Friday)
    assert cal.is_banking_day(date(2026, 10, 2)) is False


def test_custom_holiday_injection():
    cal = IndianBankingCalendar()
    custom_diwali = {date(2026, 11, 10)}
    
    # Without custom holiday
    assert cal.is_banking_day(date(2026, 11, 10)) is True
    # With custom holiday injected
    assert cal.is_banking_day(date(2026, 11, 10), custom_holidays=custom_diwali) is False


def test_dynamic_settlement_window_expansion():
    cal = IndianBankingCalendar()

    # Normal Tuesday capture without intervening holidays: 2026-08-04
    # Aug 4 (Tue), Aug 5 (Wed), Aug 6 (Thu), Aug 7 (Fri) are all banking days
    window_normal = cal.effective_settlement_window(date(2026, 8, 4), base_banking_days=4)
    assert len(window_normal) == 5  # T+0, T+1, T+2, T+3, T+4
    assert window_normal[-1] == date(2026, 8, 8)

    # Capture on Friday before 2nd Saturday + Sunday: 2026-08-07
    # Aug 7 (Fri) - Day 1
    # Aug 8 (2nd Sat) - Holiday
    # Aug 9 (Sun) - Holiday
    # Aug 10 (Mon) - Day 2
    # Aug 11 (Tue) - Day 3
    # Aug 12 (Wed) - Day 4
    # The calendar must automatically expand the window across the weekend!
    window_weekend = cal.effective_settlement_window(date(2026, 8, 7), base_banking_days=4)
    assert date(2026, 8, 12) in window_weekend
    assert len(window_weekend) >= 6  # Expanded window
