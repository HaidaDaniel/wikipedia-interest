from wikipedia_interest.reliability import assess_reliability


def test_reliability_penalizes_spikes_and_low_resolution():
    metrics = {"periods": 24, "data_completeness_pct": 100, "trend_pct_per_year": 40, "trend_fit_r2": 0.8, "volatility_mad_over_median": 0.2}
    clean = assess_reliability(metrics, [], "high")
    spiky = assess_reliability(metrics, [{"share_of_total_pct": 35}], "low")
    assert clean["level"] == "high"
    assert spiky["score"] < clean["score"]
    assert "spike" in " ".join(spiky["reasons"])


def test_stable_flat_series_can_have_high_evidence_quality():
    metrics = {"periods": 24, "data_completeness_pct": 100, "trend_pct_per_year": 0, "trend_fit_r2": 1.0, "volatility_mad_over_median": 0.0}
    result = assess_reliability(metrics, [], "high")
    assert result["level"] == "high"
