from wikipedia_interest.analysis import compare_series


def test_comparison_contract_is_compact_and_stable():
    series = [{"status": "ok", "language": "uk", "article": "Астрономія", "metrics": {"trend_label": "growing", "trend_pct_per_year": 20}, "reliability": {"level": "medium", "score": 60}}]
    result = compare_series(series, "growth")
    assert result["no_positive_growth_signal"] is False
    assert result["strongest_signal"]["language"] == "uk"


def test_balanced_does_not_select_decline_as_positive_signal():
    series = [
        {"status": "ok", "language": "a", "article": "A", "metrics": {"trend_label": "growing", "trend_pct_per_year": 20}, "reliability": {"level": "medium", "score": 70}},
        {"status": "ok", "language": "b", "article": "B", "metrics": {"trend_label": "declining", "trend_pct_per_year": -80}, "reliability": {"level": "high", "score": 85}},
    ]
    result = compare_series(series, "balanced")
    assert result["strongest_signal"]["language"] == "a"


def test_all_declining_has_no_positive_signal():
    series = [{"status": "ok", "language": "uk", "article": "A", "metrics": {"trend_label": "declining", "trend_pct_per_year": -80}, "reliability": {"level": "high", "score": 85}}]
    result = compare_series(series, "balanced")
    assert result["strongest_signal"] is None
    assert result["no_positive_growth_signal"] is True
