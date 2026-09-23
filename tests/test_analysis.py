from datetime import date, datetime

from wikipedia_interest.analysis import analyze_series, aggregate_points
from wikipedia_interest.models import PageviewPoint


def points(values):
    return [PageviewPoint(datetime(2024 + index // 12, index % 12 + 1, 1), value) for index, value in enumerate(values)]


def test_growth_uses_trend_not_only_endpoints():
    result = analyze_series(points([100, 110, 125, 140, 160, 180, 200, 220, 250, 280, 310, 350]), date(2024, 1, 1), date(2024, 12, 31), "monthly", "high")
    assert result["metrics"]["trend_label"] == "growing"
    assert result["metrics"]["trend_pct_per_year"] > 0
    assert result["metrics"]["first_window_vs_last_window_growth_pct"] > 100


def test_zero_and_missing_months_are_explicit():
    sparse = [PageviewPoint(datetime(2024, 1, 1), 0), PageviewPoint(datetime(2024, 3, 1), 100)]
    frame, completeness = aggregate_points(sparse, date(2024, 1, 1), date(2024, 4, 30), "monthly")
    assert frame["views"].tolist() == [0.0, 0.0, 100.0, 0.0]
    assert completeness == 0.5


def test_yoy_compares_recent_year_to_prior_year():
    values = [100] * 12 + [200] * 12
    result = analyze_series(points(values), date(2024, 1, 1), date(2025, 12, 31), "monthly", "high")
    assert result["metrics"]["recent_yoy_growth_pct"] == 100.0


def test_short_series_is_uncertain():
    result = analyze_series(points([10, 20, 30]), date(2024, 1, 1), date(2024, 3, 31), "monthly", "high")
    assert result["metrics"]["trend_label"] == "uncertain"
