from __future__ import annotations

from typing import Any

MIN_TREND_SIGNAL_PCT = 10.0
STRONG_TREND_SIGNAL_PCT = 15.0


def assess_reliability(metrics: dict[str, Any], anomalies: list[dict[str, Any]], resolution_confidence: str) -> dict[str, Any]:
    score = 0
    reasons: list[str] = []
    periods = int(metrics.get("periods", 0))
    completeness = float(metrics.get("data_completeness_pct", 0))
    trend = metrics.get("trend_pct_per_year")
    r2 = metrics.get("trend_fit_r2")
    volatility = metrics.get("volatility_mad_over_median")
    if periods >= 24:
        score += 20
        reasons.append(f"{periods} periods provide a long comparison window")
    elif periods >= 12:
        score += 10
        reasons.append(f"{periods} periods provide a usable but limited window")
    else:
        reasons.append("short time series makes direction uncertain")
    if completeness >= 95:
        score += 20
        reasons.append("at least 95% of expected periods are present")
    elif completeness >= 80:
        score += 10
        reasons.append("most expected periods are present")
    else:
        score -= 15
        reasons.append("missing periods reduce evidence quality")
    if trend is not None and abs(trend) >= STRONG_TREND_SIGNAL_PCT:
        score += 20
        reasons.append("directional trend is materially larger than the baseline threshold")
    elif trend is not None and abs(trend) >= MIN_TREND_SIGNAL_PCT:
        score += 10
        reasons.append("directional trend clears the minimum threshold")
    else:
        reasons.append("directional trend is small or unavailable")
    if r2 is not None and r2 >= 0.5:
        score += 15
        reasons.append("log-linear trend fit is consistent")
    elif r2 is not None and r2 >= 0.25:
        score += 8
        reasons.append("trend fit is moderately consistent")
    else:
        score -= 5
        reasons.append("trend fit is noisy")
    if volatility is None or volatility <= 0.5:
        score += 10
        reasons.append("period-to-period variation is moderate")
    elif volatility <= 1:
        score += 4
        reasons.append("period-to-period variation is noticeable")
    else:
        score -= 5
        reasons.append("high variation weakens a directional reading")
    if not anomalies:
        score += 5
        reasons.append("no robust spike detected")
    else:
        score -= min(10, 5 + len(anomalies))
        largest = max(anomalies, key=lambda row: row["share_of_total_pct"])
        reasons.append(f"{len(anomalies)} spike(s) detected; largest is {largest['share_of_total_pct']:.1f}% of total views")
    if resolution_confidence == "high":
        score += 10
        reasons.append("article resolution is high confidence")
    elif resolution_confidence == "medium":
        score += 5
        reasons.append("article resolution is plausible but should be checked")
    else:
        score -= 10
        reasons.append("article resolution is low confidence")
        score = min(score, 44)
        reasons.append("low-confidence candidate is capped at low evidence quality and excluded from comparison")
    if resolution_confidence == "medium":
        score = min(score, 69)
        reasons.append("medium-confidence article resolution caps evidence quality at medium")
    score = max(0, min(100, score))
    level = "high" if score >= 70 else "medium" if score >= 45 else "low"
    return {"level": level, "score": score, "reasons": reasons, "note": "Heuristic evidence quality, not a statistical confidence interval."}
