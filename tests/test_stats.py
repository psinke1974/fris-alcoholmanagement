from datetime import date, timedelta

from app.models import DrinkLog
from app.services.stats_service import compute_trends, trend_start_date


def _log(log_date: date, units: float) -> DrinkLog:
    return DrinkLog(log_date=log_date, units=units, user_id=1)


class TestComputeTrends:
    def test_starts_from_registration_week(self):
        since = date.today() - timedelta(days=2)
        today = date.today()
        logs = [_log(today, 0), _log(today - timedelta(days=1), 2)]
        trends = compute_trends(logs, since)

        assert trends["week_count"] >= 1
        assert "(nu)" in trends["labels"][-1]
        assert sum(trends["units"]) == 2.0

    def test_shows_all_weeks_since_registration(self):
        since = date.today() - timedelta(days=20)
        trends = compute_trends([], since)
        assert trends["week_count"] >= 3

    def test_unknown_days_not_counted_as_dry(self):
        since = date.today() - timedelta(days=6)
        today = date.today()
        logs = [_log(today, 0)]
        trends = compute_trends(logs, since)
        incomplete = [i for i, complete in enumerate(trends["is_complete"]) if not complete]
        assert incomplete
        idx = incomplete[-1]
        assert trends["dry_days"][idx] <= trends["days_logged"][idx]
        assert trends["days_logged"][idx] < trends["days_in_period"][idx]

    def test_partial_week_days_in_period(self):
        since = date.today()
        trends = compute_trends([], since)
        assert trends["days_in_period"][-1] == 1

    def test_includes_weeks_before_registration_when_backfilled(self):
        today = date.today()
        since = today  # geregistreerd vandaag
        two_weeks_ago = today - timedelta(days=14)
        last_week = today - timedelta(days=3)
        logs = [
            _log(two_weeks_ago, 4),
            _log(last_week, 2),
            _log(today, 0),
        ]
        trends = compute_trends(logs, since)

        assert trends["week_count"] >= 3
        assert sum(trends["units"]) == 6.0
        assert trends["has_backfill"] is True

    def test_pre_registration_week_only_counts_logged_days(self):
        today = date.today()
        since = today
        drinking_day = today - timedelta(days=10)
        logs = [_log(drinking_day, 3)]
        trends = compute_trends(logs, since)

        week_with_log = next(i for i, u in enumerate(trends["units"]) if u == 3.0)
        assert trends["dry_days"][week_with_log] == 0
        assert trends["days_in_period"][week_with_log] == 1


class TestTrendStartDate:
    def test_without_logs_uses_registration(self):
        since = date.today()
        assert trend_start_date(since, []) == since

    def test_with_older_logs_uses_earliest(self):
        today = date.today()
        since = today
        logs = [_log(today - timedelta(days=21), 1)]
        assert trend_start_date(since, logs) == today - timedelta(days=21)
