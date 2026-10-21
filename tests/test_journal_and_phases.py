from datetime import date, timedelta

import pytest

from app.models import DrinkLog, Goal
from app.services.cessation_phase_service import get_cessation_guidance, get_phase_key
from app.services.journal_service import is_empty_body, sanitize_html


class TestPhaseKey:
    def test_voorbereiding(self):
        assert get_phase_key(0) == "voorbereiding"

    def test_dag_1_3(self):
        assert get_phase_key(1) == "dag_1_3"
        assert get_phase_key(3) == "dag_1_3"

    def test_week_1(self):
        assert get_phase_key(7) == "week_1"

    def test_langdurig(self):
        assert get_phase_key(100) == "langdurig"


class TestCessationGuidance:
    def _log(self, log_date: date, units: float) -> DrinkLog:
        return DrinkLog(log_date=log_date, units=units, user_id=1)

    def test_abstain_goal_returns_phase_content(self):
        today = date.today()
        goal = Goal(goal_type="abstain", target_value=0, active=True)
        logs = [self._log(today - timedelta(days=i), 0) for i in range(5)]
        guidance = get_cessation_guidance([goal], logs, today - timedelta(days=30))
        assert guidance is not None
        assert guidance["mode"] == "abstain"
        assert guidance["phase_key"] == "week_1"
        assert guidance["days_since_last_drink"] == 5
        assert len(guidance["positive_effects"]) > 0
        assert len(guidance["negative_effects"]) > 0
        assert len(guidance["tips"]) > 0

    def test_gap_resets_phase_to_early_days(self):
        today = date.today()
        goal = Goal(goal_type="abstain", target_value=0, active=True)
        logs = [
            self._log(today, 0),
            self._log(today - timedelta(days=1), 0),
            # oude droge periode telt niet meer mee na de gap
            * [self._log(today - timedelta(days=40 + i), 0) for i in range(20)],
        ]
        guidance = get_cessation_guidance([goal], logs, today - timedelta(days=70))
        assert guidance["days_since_last_drink"] == 2
        assert guidance["phase_key"] == "dag_1_3"

    def test_reduction_goal(self):
        goal = Goal(goal_type="weekly_units", target_value=5, active=True)
        guidance = get_cessation_guidance([goal], [], date.today())
        assert guidance["mode"] == "reduction"
        assert guidance["label"] == "Minder drinken"

    def test_voorbereiding_without_goal(self):
        guidance = get_cessation_guidance([], [], date.today())
        assert guidance["mode"] == "voorbereiding"


class TestJournalService:
    def test_sanitize_strips_script(self):
        dirty = '<p>Hello</p><script>alert("x")</script>'
        assert "<script>" not in sanitize_html(dirty)
        assert "Hello" in sanitize_html(dirty)

    def test_is_empty_body(self):
        assert is_empty_body("<p><br></p>")
        assert is_empty_body("")
        assert not is_empty_body("<p>tekst</p>")
