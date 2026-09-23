from wikipedia_interest.analysis import compare_series


def test_comparison_contract_is_compact_and_stable():
    series = [{"status": "ok", "language": "uk", "article": "Астрономія", "metrics": {"trend_label": "growing", "trend_pct_per_year": 20}, "reliability": {"level": "medium", "score": 60}}]
    result = compare_series(series, "growth")
    assert set(result) == {"criterion", "ranking", "strongest_signal", "fastest_growth", "most_reliable", "rationale", "interpretation"}
    assert result["strongest_signal"]["language"] == "uk"

