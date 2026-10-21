from datetime import date, timedelta

import pytest

from app.models import DrinkLog
from app.services.gaps_service import detect_gaps, get_active_gap


def _log(log_date: date, units: float = 0) -> DrinkLog:
    return DrinkLog(log_date=log_date, units=units, user_id=1)


class TestDetectGaps:
    def test_no_gaps_when_daily_logs(self):
        today = date.today()
        since = today - timedelta(days=6)
        logs = [_log(today - timedelta(days=i)) for i in range(7)]
        assert detect_gaps(logs, since) == []

    def test_detects_gap_of_two_days(self):
        today = date.today()
        since = today - timedelta(days=10)
        logs = [
            _log(today - timedelta(days=5)),
            _log(today - timedelta(days=2)),
        ]
        gaps = detect_gaps(logs, since)
        assert len(gaps) == 1
        assert gaps[0]["days"] == 2
        assert gaps[0]["start"] == today - timedelta(days=4)
        assert gaps[0]["end"] == today - timedelta(days=3)

    def test_single_missing_day_is_not_a_gap(self):
        today = date.today()
        since = today - timedelta(days=5)
        logs = [_log(today), _log(today - timedelta(days=2))]
        assert detect_gaps(logs, since) == []

    def test_ongoing_gap_until_yesterday(self):
        today = date.today()
        since = today - timedelta(days=10)
        logs = [_log(today - timedelta(days=5))]
        gaps = detect_gaps(logs, since)
        assert len(gaps) == 1
        assert gaps[0]["end"] == today - timedelta(days=1)
        assert gaps[0]["days"] == 4

    def test_no_gaps_without_any_logs(self):
        since = date.today() - timedelta(days=10)
        assert detect_gaps([], since) == []

    def test_dismissed_gap_is_filtered(self):
        today = date.today()
        since = today - timedelta(days=10)
        logs = [_log(today - timedelta(days=5))]
        gap_end = today - timedelta(days=1)
        gaps = detect_gaps(logs, since, dismissed_until=gap_end)
        assert gaps == []

    def test_new_gap_after_dismissed_period(self):
        today = date.today()
        since = today - timedelta(days=20)
        logs = [
            _log(today - timedelta(days=15)),
            _log(today - timedelta(days=2)),
        ]
        gaps = detect_gaps(logs, since, dismissed_until=today - timedelta(days=10))
        assert len(gaps) == 1
        assert gaps[0]["end"] == today - timedelta(days=3)


class TestGetActiveGap:
    def test_returns_oldest_gap_first(self):
        today = date.today()
        since = today - timedelta(days=20)
        logs = [
            _log(today - timedelta(days=18)),
            _log(today - timedelta(days=10)),
            _log(today - timedelta(days=2)),
        ]
        gap = get_active_gap(logs, since)
        assert gap is not None
        assert gap["start"] == today - timedelta(days=17)
        assert gap["days_list"][0] == gap["start"]

    def test_none_when_no_gaps(self):
        today = date.today()
        logs = [_log(today - timedelta(days=i)) for i in range(3)]
        assert get_active_gap(logs, today - timedelta(days=10)) is None
