import json

from app.services.drinks_service import (
    calculate_units_from_items,
    format_drink_summary,
    parse_drink_items,
    parse_drink_summary,
    serialize_drink_items,
)


class TestParseDrinkItems:
    def test_valid_items(self):
        raw = json.dumps([{"id": "tripel", "count": 2}, {"id": "bier", "count": 1}])
        assert parse_drink_items(raw) == [
            {"id": "tripel", "count": 2},
            {"id": "bier", "count": 1},
        ]

    def test_ignores_unknown_drinks(self):
        raw = json.dumps([{"id": "onbekend", "count": 1}, {"id": "wijn", "count": 1}])
        assert parse_drink_items(raw) == [{"id": "wijn", "count": 1}]

    def test_invalid_json(self):
        assert parse_drink_items("not-json") == []


class TestCalculateUnits:
    def test_tripel_units(self):
        items = [{"id": "tripel", "count": 1}]
        assert calculate_units_from_items(items) == 1.6

    def test_multiple_drinks(self):
        items = [{"id": "tripel", "count": 2}, {"id": "radler", "count": 1}]
        assert calculate_units_from_items(items) == 3.7

    def test_zero_items(self):
        assert calculate_units_from_items([]) == 0.0


class TestFormatSummary:
    def test_single_drink(self):
        items = [{"id": "wijn", "count": 1}]
        assert format_drink_summary(items) == "Wijnglas"

    def test_multiple_counts(self):
        items = [{"id": "tripel", "count": 2}]
        assert format_drink_summary(items) == "2× Tripel"

    def test_sterk_drink(self):
        items = [{"id": "sterk", "count": 2}]
        assert calculate_units_from_items(items) == 2.0
        assert format_drink_summary(items) == "2× Sterke drank"


class TestParseDrinkSummary:
    def test_single_drink(self):
        assert parse_drink_summary("Wijnglas") == [{"id": "wijn", "count": 1}]

    def test_multiple_counts(self):
        assert parse_drink_summary("2× Tripel") == [{"id": "tripel", "count": 2}]

    def test_mixed_summary(self):
        summary = "Tripel, 2× Standaard bier"
        assert parse_drink_summary(summary) == [
            {"id": "tripel", "count": 1},
            {"id": "bier", "count": 2},
        ]

    def test_empty_summary(self):
        assert parse_drink_summary("") == []


class TestSerializeDrinkItems:
    def test_empty_items(self):
        assert serialize_drink_items([]) is None

    def test_serializes_items(self):
        items = [{"id": "bier", "count": 2}]
        assert serialize_drink_items(items) == json.dumps(items)
