from datetime import date, timedelta

from app.models import DrinkLog
from app.services.badges_service import (
    compute_badges,
    compute_consecutive_alcohol_free_days,
    compute_dry_streak,
    compute_dry_week_streak,
    days_since_last_drink,
)


def _log(log_date: date, units: float) -> DrinkLog:
    return DrinkLog(log_date=log_date, units=units, user_id=1)


class TestDryStreak:
    def test_no_logs_is_zero(self):
        since = date.today()
        assert compute_dry_streak([], since) == 0

    def test_unlogged_days_do_not_count(self):
        since = date.today() - timedelta(days=5)
        logs = [_log(date.today() - timedelta(days=1), 0)]
        assert compute_dry_streak(logs, since) == 1

    def test_consecutive_logged_dry_days(self):
        since = date.today() - timedelta(days=5)
        today = date.today()
        logs = [_log(today - timedelta(days=i), 0) for i in range(3)]
        assert compute_dry_streak(logs, since) == 3

    def test_includes_today_when_logged_dry(self):
        since = date.today() - timedelta(days=2)
        today = date.today()
        logs = [_log(today, 0), _log(today - timedelta(days=1), 0)]
        assert compute_dry_streak(logs, since) == 2

    def test_skips_today_when_unlogged(self):
        since = date.today() - timedelta(days=2)
        today = date.today()
        logs = [_log(today - timedelta(days=1), 0)]
        assert compute_dry_streak(logs, since) == 1

    def test_stops_at_drink_day(self):
        since = date.today() - timedelta(days=5)
        today = date.today()
        logs = [
            _log(today - timedelta(days=1), 0),
            _log(today - timedelta(days=2), 2),
        ]
        assert compute_dry_streak(logs, since) == 1

    def test_does_not_count_before_registration(self):
        since = date.today()
        logs = [_log(date.today() - timedelta(days=1), 0), _log(date.today(), 0)]
        assert compute_dry_streak(logs, since) == 1

    def test_gap_breaks_streak_even_after_old_dry_period(self):
        """Maand niet registreren mag geen mijlpalen opleveren."""
        since = date.today() - timedelta(days=40)
        today = date.today()
        logs = [
            _log(today, 0),
            _log(today - timedelta(days=1), 0),
            # gap van ~30 dagen
            *[_log(today - timedelta(days=35 + i), 0) for i in range(5)],
        ]
        assert compute_dry_streak(logs, since) == 2


class TestDaysSinceLastDrink:
    def test_no_logs_is_zero(self):
        assert days_since_last_drink([], date.today()) == 0

    def test_equals_registered_streak(self):
        since = date.today() - timedelta(days=10)
        today = date.today()
        logs = [_log(today - timedelta(days=i), 0) for i in range(3)]
        assert days_since_last_drink(logs, since) == 3
        assert days_since_last_drink(logs, since) == compute_dry_streak(logs, since)

    def test_gap_does_not_inflate_count(self):
        since = date.today() - timedelta(days=40)
        today = date.today()
        logs = [
            _log(today, 0),
            _log(today - timedelta(days=30), 3),
        ]
        assert days_since_last_drink(logs, since) == 1


class TestBadges:
    def test_new_user_no_earned_badges(self):
        result = compute_badges([], date.today())
        assert result["dry_streak"] == 0
        assert result["days_since_last_drink"] == 0
        assert len(result["days"]["earned"]) == 0

    def test_first_day_badge(self):
        logs = [_log(date.today(), 0)]
        result = compute_badges(logs, date.today() - timedelta(days=1))
        assert any(b["threshold"] == 1 for b in result["days"]["earned"])

    def test_day_milestones_ignore_unlogged_gap(self):
        since = date.today() - timedelta(days=40)
        today = date.today()
        # 2 recente droge dagen + oude droge maand ver weg
        logs = [
            _log(today, 0),
            _log(today - timedelta(days=1), 0),
            *[_log(today - timedelta(days=35 + i), 0) for i in range(10)],
        ]
        result = compute_badges(logs, since)
        assert result["consecutive_alcohol_free_days"] == 2
        earned_thresholds = {b["threshold"] for b in result["days"]["earned"]}
        assert earned_thresholds == {1}
        assert 3 not in earned_thresholds
        assert 30 not in earned_thresholds

    def test_week_badge_requires_seven_consecutive_days(self):
        since = date.today() - timedelta(days=7)
        today = date.today()
        logs = [_log(today - timedelta(days=i), 0) for i in range(7)]
        assert compute_consecutive_alcohol_free_days(logs, since) == 7
        assert compute_dry_week_streak(logs, since) == 1
        result = compute_badges(logs, since)
        assert any(b["threshold"] == 1 for b in result["weeks"]["earned"])

    def test_one_dry_day_is_not_a_week(self):
        """Geregistreerd vandaag, alleen vandaag 0 — geen week."""
        since = date.today()
        today = date.today()
        logs = [
            _log(today, 0),
            _log(today - timedelta(days=1), 3),
            _log(today - timedelta(days=2), 2),
        ]
        assert compute_dry_week_streak(logs, since) == 0
        assert compute_consecutive_alcohol_free_days(logs, since) == 1

    def test_alcohol_breaks_week_count(self):
        since = date.today() - timedelta(days=14)
        today = date.today()
        logs = [_log(today - timedelta(days=i), 0) for i in range(3)]
        logs.append(_log(today - timedelta(days=3), 2))
        assert compute_dry_week_streak(logs, since) == 0

    def test_unlogged_days_break_week_streak(self):
        since = date.today() - timedelta(days=6)
        today = date.today()
        logs = [_log(today - timedelta(days=1), 0), _log(today - timedelta(days=7), 0)]
        assert compute_consecutive_alcohol_free_days(logs, since) == 1
        assert compute_dry_week_streak(logs, since) == 0
