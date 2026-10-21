from datetime import date, timedelta

import pytest

from app.models import DrinkLog, Goal
from app.services.stats_service import count_logged_dry_days_this_week
from app.services.tips_service import get_personalized_tips


def _log(log_date: date, units: float) -> DrinkLog:
    return DrinkLog(log_date=log_date, units=units, user_id=1)


def _days_this_week():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    return week_start, today


class TestCountLoggedDryDays:
    def test_unlogged_days_not_counted(self):
        today = date.today()
        since = today
        logs = [_log(today, 2)]
        assert count_logged_dry_days_this_week(logs, since) == 0

    def test_only_explicit_zero_days(self):
        week_start, today = _days_this_week()
        since = week_start
        logs = [_log(week_start, 0)]
        if week_start < today:
            mid = week_start + timedelta(days=1)
            logs.extend([_log(mid, 0), _log(mid, 3)])
        # Een dag is alleen "droog" als er wél een 0-log is en géén >0-log.
        units_by_date = {}
        for log in logs:
            units_by_date.setdefault(log.log_date, []).append(log.units)
        expected = sum(
            1
            for day_units in units_by_date.values()
            if any(u == 0 for u in day_units) and not any(u > 0 for u in day_units)
        )
        assert count_logged_dry_days_this_week(logs, since) == expected

    def test_ignores_days_before_registration(self):
        today = date.today()
        since = today
        logs = [_log(today - timedelta(days=2), 0)]
        assert count_logged_dry_days_this_week(logs, since) == 0


class TestDryDaysTip:
    def test_no_false_seven_day_tip(self):
        today = date.today()
        since = today
        logs = [_log(today, 0)]
        tips = get_personalized_tips(None, None, [], logs, since)
        dry_tip = next((t for t in tips if "alcoholvrije dagen" in t["title"].lower()), None)
        assert dry_tip is None

    def test_shows_tip_when_three_logged_dry_days(self):
        week_start, today = _days_this_week()
        since = week_start
        logs = [
            _log(week_start + timedelta(days=i), 0)
            for i in range((today - week_start).days + 1)
        ]
        if len(logs) < 3:
            pytest.skip("Minder dan 3 dagen verstreken in de huidige week")

        tips = get_personalized_tips(None, None, [], logs, since)
        dry_tip = next((t for t in tips if "alcoholvrije dagen" in t["title"].lower()), None)
        assert dry_tip is not None
        assert "3 dag(en)" in dry_tip["text"]

    def test_goal_tip_for_weekly_units(self):
        today = date.today()
        goal = Goal(goal_type="weekly_units", target_value=5, active=True)
        logs = [_log(today, 1)]
        tips = get_personalized_tips(None, None, [goal], logs, today)
        goal_tip = next((t for t in tips if t["category"] == "doel"), None)
        assert goal_tip is not None
        assert "5" in goal_tip["text"]
