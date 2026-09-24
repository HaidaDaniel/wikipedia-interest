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


def test_low_confidence_candidates_are_excluded_from_comparison():
    result = compare_series([
        {"status": "ok", "language": "pl", "article": "Unverified", "resolution": {"confidence": "low"}, "metrics": {"trend_label": "growing", "trend_pct_per_year": 80}, "reliability": {"level": "low", "score": 40}},
        {"status": "ok", "language": "de", "article": "Verified", "resolution": {"confidence": "high"}, "metrics": {"trend_label": "flat", "trend_pct_per_year": 0}, "reliability": {"level": "high", "score": 80}},
    ])
    assert [row["language"] for row in result["ranking"]] == ["de"]
    assert result["strongest_signal"] is None
    assert result["excluded_low_confidence"][0]["language"] == "pl"
