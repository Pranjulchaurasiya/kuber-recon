"""Indian Banking Calendar & Settlement Window Expansion Engine.

In accordance with Reserve Bank of India (RBI) RTGS/NEFT settlement rules:
1. Banks are closed on all Sundays.
2. Banks are closed on 2nd and 4th Saturdays of every Gregorian month.
3. Banks observe statutory holidays under the Negotiable Instruments Act, 1881.
4. When settlement capture occurs prior to long holiday clusters (e.g., Diwali, Durga Puja),
   nodal bank clearing credits may clear on T+5 or T+6 instead of standard T+2/T+4.
"""

from datetime import date, timedelta
from typing import List, Optional, Set


# Standard national statutory banking holidays across major Indian nodal hubs (2025-2027 samples)
DEFAULT_RBI_STATUTORY_HOLIDAYS: Set[date] = {
    # 2025
    date(2025, 1, 26),   # Republic Day
    date(2025, 4, 1),    # Annual Bank Closing
    date(2025, 8, 15),   # Independence Day
    date(2025, 10, 2),   # Mahatma Gandhi Jayanti
    date(2025, 10, 20),  # Diwali (Deepavali)
    date(2025, 10, 21),  # Diwali Balipratipada
    date(2025, 12, 25),  # Christmas
    # 2026
    date(2026, 1, 26),   # Republic Day
    date(2026, 4, 1),    # Annual Bank Closing
    date(2026, 8, 15),   # Independence Day
    date(2026, 10, 2),   # Mahatma Gandhi Jayanti
    date(2026, 11, 8),   # Diwali Laxmi Pujan
    date(2026, 11, 9),   # Diwali Balipratipada
    date(2026, 12, 25),  # Christmas
    # 2027
    date(2027, 1, 26),   # Republic Day
    date(2027, 4, 1),    # Annual Bank Closing
    date(2027, 8, 15),   # Independence Day
    date(2027, 10, 2),   # Mahatma Gandhi Jayanti
    date(2027, 10, 29),  # Diwali
    date(2027, 12, 25),  # Christmas
}


class IndianBankingCalendar:
    """Deterministic Indian Banking Holiday & Settlement Window Resolver."""

    def __init__(self, additional_holidays: Optional[Set[date]] = None):
        self.statutory_holidays: Set[date] = set(DEFAULT_RBI_STATUTORY_HOLIDAYS)
        if additional_holidays:
            self.statutory_holidays.update(additional_holidays)

    @staticmethod
    def is_second_or_fourth_saturday(d: date) -> bool:
        """RBI Rule: 2nd and 4th Saturdays of every month are mandatory bank holidays."""
        if d.weekday() != 5:  # Saturday is 5 in Python (Monday=0)
            return False
        # Calculate which Saturday of the month this is
        # The first Saturday occurs in days 1..7, second in 8..14, third in 15..21, fourth in 22..28
        saturday_index = (d.day - 1) // 7 + 1
        return saturday_index in (2, 4)

    @staticmethod
    def is_sunday(d: date) -> bool:
        """Sunday is day 6."""
        return d.weekday() == 6

    def is_banking_day(self, d: date, custom_holidays: Optional[Set[date]] = None) -> bool:
        """Determines whether a given date is an active RBI clearing/settlement day."""
        if self.is_sunday(d):
            return False
        if self.is_second_or_fourth_saturday(d):
            return False
        if d in self.statutory_holidays:
            return False
        if custom_holidays and d in custom_holidays:
            return False
        return True

    def effective_settlement_window(
        self,
        cap_date: date,
        holidays: Optional[Set[date]] = None,
        base_banking_days: int = 4,
        max_calendar_days: int = 7,
    ) -> List[date]:
        """
        Dynamically computes the list of eligible settlement dates starting from `cap_date`.
        
        Ensures that at least `base_banking_days` active banking clearing days are covered,
        automatically expanding the search window across weekend/holiday clusters up to
        `max_calendar_days` (e.g., from T+4 to T+6 or T+7).
        """
        eligible_dates: List[date] = []
        banking_days_counted = 0
        
        curr_offset = 0
        while curr_offset <= max_calendar_days:
            curr_date = cap_date + timedelta(days=curr_offset)
            eligible_dates.append(curr_date)
            
            if self.is_banking_day(curr_date, custom_holidays=holidays):
                banking_days_counted += 1
                
            # If we have captured the capture date plus the required banking days, stop
            if curr_offset >= base_banking_days and banking_days_counted >= base_banking_days:
                break
                
            curr_offset += 1
            
        return eligible_dates


# Singleton instance for quick module access
_default_calendar = IndianBankingCalendar()


def get_effective_settlement_dates(
    cap_date: date,
    holidays: Optional[Set[date]] = None,
    base_banking_days: int = 4,
    max_calendar_days: int = 7,
) -> List[date]:
    """Helper wrapper for dynamic settlement window expansion."""
    return _default_calendar.effective_settlement_window(
        cap_date=cap_date,
        holidays=holidays,
        base_banking_days=base_banking_days,
        max_calendar_days=max_calendar_days,
    )
