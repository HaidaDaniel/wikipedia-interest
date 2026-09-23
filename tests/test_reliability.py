from wikipedia_interest.reliability import assess_reliability


def test_reliability_penalizes_spikes_and_low_resolution():
    metrics = {"periods": 24, "data_completeness_pct": 100, "trend_pct_per_year": 40, "trend_fit_r2": 0.8, "volatility_mad_over_median": 0.2}
    clean = assess_reliability(metrics, [], "high")
    spiky = assess_reliability(metrics, [{"share_of_total_pct": 35}], "low")
    assert clean["level"] == "high"
    assert spiky["score"] < clean["score"]
    assert "spike" in " ".join(spiky["reasons"])

