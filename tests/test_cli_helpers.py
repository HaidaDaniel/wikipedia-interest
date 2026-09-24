from datetime import date

from wikipedia_interest.cli import _complete_data_through, compact_result


def test_complete_data_cutoff_excludes_current_period():
    assert _complete_data_through(date(2026, 9, 24), "monthly") == date(2026, 8, 31)
    assert _complete_data_through(date(2026, 9, 24), "daily") == date(2026, 9, 23)


def test_compact_result_drops_observations():
    full = {"status": "ok", "series": [{"language": "uk", "observations": [{"date": "2024-01-01", "views": 1}], "metrics": {}}]}
    compact = compact_result(full)
    assert "observations" not in compact["series"][0]
