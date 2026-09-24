from __future__ import annotations

import math
from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from .models import PageviewPoint

TREND_DIRECTION_THRESHOLD_PCT = 10.0
ANOMALY_ROBUST_Z_THRESHOLD = 3.5
MIN_DIRECTIONAL_PERIODS = 12


def choose_granularity(start: date, end: date, requested: str) -> str:
    if requested in {"daily", "monthly"}:
        return requested
    if requested != "auto":
        raise ValueError("granularity must be auto, daily or monthly")
    return "monthly" if (end - start).days > 180 else "daily"


def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)


def expected_periods(start: date, end: date, granularity: str) -> pd.DatetimeIndex:
    if granularity == "monthly":
        return pd.date_range(_month_start(start), _month_start(end), freq="MS")
    return pd.date_range(start, end, freq="D")


def aggregate_points(points: list[PageviewPoint], start: date, end: date, granularity: str) -> tuple[pd.DataFrame, float]:
    """Align observations without turning missing periods into real zero views."""
    periods = expected_periods(start, end, granularity)
    frame = pd.DataFrame({"date": periods})
    if not points:
        frame["views"] = np.nan
        frame["observed"] = False
        return frame, 0.0
    raw = pd.DataFrame({"date": [p.timestamp for p in points], "views": [p.views for p in points]})
    raw["date"] = pd.to_datetime(raw["date"]).dt.normalize()
    raw["period"] = raw["date"].dt.to_period("M").dt.to_timestamp() if granularity == "monthly" else raw["date"]
    grouped = raw.groupby("period", as_index=True)["views"].sum()
    frame["views"] = frame["date"].map(grouped).astype(float)
    frame["observed"] = frame["date"].isin(grouped.index)
    return frame, float(frame["observed"].mean()) if len(frame) else 0.0


def _pct_change(old: float, new: float) -> float | None:
    if old <= 0:
        return None
    return round((new - old) / old * 100, 2)


def _robust_volatility(values: np.ndarray) -> float | None:
    median = float(np.median(values)) if len(values) else 0
    if median <= 0:
        return None
    return round(float(np.median(np.abs(values - median)) / median), 4)


def _regression(values: np.ndarray, periods_per_year: int, x: np.ndarray | None = None) -> tuple[float | None, float | None]:
    if len(values) < 3 or np.all(values <= 0):
        return None, None
    x = np.arange(len(values), dtype=float) if x is None else x.astype(float)
    y = np.log1p(np.maximum(values, 0))
    slope, intercept = np.polyfit(x, y, 1)
    prediction = slope * x + intercept
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - float(np.sum((y - prediction) ** 2)) / ss_tot if ss_tot > 1e-12 else 1.0
    annualized = (math.exp(float(slope) * periods_per_year) - 1) * 100
    return round(annualized, 2), round(max(0.0, min(1.0, r2)), 3)


def detect_anomalies(frame: pd.DataFrame) -> list[dict[str, Any]]:
    observed = frame[frame["observed"]].reset_index(drop=True)
    values = observed["views"].to_numpy(dtype=float)
    if len(values) < 5:
        return []
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = 1.4826 * mad
    if scale < 1e-9:
        q75, q25 = np.percentile(values, [75, 25])
        scale = float((q75 - q25) / 1.349) if q75 > q25 else float(np.std(values))
    if scale < 1e-9:
        return []
    robust_z = (values - median) / scale
    total = max(float(values.sum()), 1.0)
    anomalies: list[dict[str, Any]] = []
    for index in np.where(np.abs(robust_z) >= ANOMALY_ROBUST_Z_THRESHOLD)[0]:
        value = float(values[index])
        anomalies.append({
            "date": pd.Timestamp(observed.iloc[index]["date"]).date().isoformat(),
            "views": int(round(value)),
            "deviation": round(float(robust_z[index]), 2),
            "share_of_total_pct": round(value / total * 100, 2),
            "influence": "may materially distort the trend" if abs(robust_z[index]) >= 6 else "worth checking against an external event",
        })
    return anomalies


def _mean_if_enough(values: pd.Series, minimum: int) -> float | None:
    clean = values.dropna()
    return float(clean.mean()) if len(clean) >= minimum else None


def analyze_series(points: list[PageviewPoint], start: date, end: date, granularity: str, resolution_confidence: str) -> dict[str, Any]:
    frame, completeness = aggregate_points(points, start, end, granularity)
    observed = frame[frame["observed"]].copy()
    values = observed["views"].to_numpy(dtype=float)
    n_expected = len(frame)
    n_observed = len(observed)
    periods_per_year = 12 if granularity == "monthly" else 365
    period_positions = frame.index[frame["observed"]].to_numpy(dtype=float)
    window = max(1, min(3 if granularity == "monthly" else 7, n_observed // 4 if n_observed >= 4 else 1))
    first_mean = float(np.mean(values[:window])) if n_observed else 0
    last_mean = float(np.mean(values[-window:])) if n_observed else 0
    trend_pct, r2 = _regression(values, periods_per_year, period_positions)
    smooth = pd.Series(values).rolling(window=min(3 if granularity == "monthly" else 7, max(1, n_observed)), center=True, min_periods=1).mean().to_numpy()
    smoothed_trend_pct, _ = _regression(smooth, periods_per_year, period_positions)
    anomalies = detect_anomalies(frame)
    if trend_pct is None or n_observed < (MIN_DIRECTIONAL_PERIODS if granularity == "monthly" else 30):
        trend_label = "uncertain"
    elif abs(trend_pct) < TREND_DIRECTION_THRESHOLD_PCT:
        trend_label = "flat" if (r2 is None or r2 >= 0.25) else "uncertain"
    elif r2 is not None and r2 < 0.15:
        trend_label = "uncertain"
    else:
        trend_label = "growing" if trend_pct > 0 else "declining"

    yoy = None
    if n_expected >= periods_per_year * 2:
        minimum = max(1, periods_per_year * 3 // 4)
        prior = _mean_if_enough(frame.iloc[-periods_per_year * 2:-periods_per_year]["views"], minimum)
        recent = _mean_if_enough(frame.iloc[-periods_per_year:]["views"], minimum)
        if prior is not None and recent is not None:
            yoy = _pct_change(prior, recent)

    nonzero = values[values > 0]
    total_views = float(values.sum()) if n_observed else 0
    peak_index = int(np.argmax(values)) if n_observed else None
    metrics = {
        "periods": n_expected,
        "observed_periods": n_observed,
        "data_completeness_pct": round(completeness * 100, 2),
        "total_views": int(round(total_views)),
        "mean_period_views": round(float(np.mean(values)), 2) if n_observed else None,
        "median_period_views": round(float(np.median(values)), 2) if n_observed else None,
        "first_window_vs_last_window_growth_pct": _pct_change(first_mean, last_mean) if n_observed else None,
        "recent_yoy_growth_pct": yoy,
        "trend_pct_per_year": trend_pct,
        "smoothed_trend_pct_per_year": smoothed_trend_pct,
        "trend_fit_r2": r2,
        "trend_label": trend_label,
        "volatility_mad_over_median": _robust_volatility(nonzero if len(nonzero) else values),
        "peak_views": int(round(float(values[peak_index]))) if peak_index is not None else None,
        "peak_date": observed.iloc[peak_index]["date"].date().isoformat() if peak_index is not None else None,
        "largest_peak_share_pct": round(float(np.max(values)) / max(total_views, 1) * 100, 2) if n_observed else None,
    }
    observations = []
    for row in frame.itertuples():
        observations.append({"date": row.date.date().isoformat(), "views": int(round(row.views)) if row.observed else None, "observed": bool(row.observed)})
    return {"metrics": metrics, "anomalies": anomalies, "observations": observations}


def compare_series(series: list[dict[str, Any]], criterion: str = "balanced") -> dict[str, Any]:
    usable = [item for item in series if item.get("status") == "ok" and "metrics" in item]
    rankings = []
    for item in usable:
        metrics = item["metrics"]
        rankings.append({"language": item["language"], "article": item["article"], "trend_label": metrics["trend_label"], "trend_pct_per_year": metrics["trend_pct_per_year"], "reliability": item["reliability"]["level"], "reliability_score": item["reliability"]["score"]})
    positive = [row for row in rankings if row["trend_label"] == "growing" and (row["trend_pct_per_year"] or 0) > 0]
    fastest = max(positive, key=lambda row: row["trend_pct_per_year"], default=None)
    stable = max(rankings, key=lambda row: row["reliability_score"], default=None)
    if criterion == "stability":
        primary = stable
        rationale = "ranked by evidence quality"
    elif criterion == "growth":
        primary = fastest
        rationale = "ranked by positive deterministic annualized trend"
    else:
        # Declining trends receive no growth bonus and cannot become an
        # opportunity signal merely because their magnitude is large.
        primary = max(positive, key=lambda row: min(row["trend_pct_per_year"], 100) / 2 + row["reliability_score"], default=None)
        rationale = "balanced positive growth signal and evidence quality"
    return {
        "criterion": criterion,
        "ranking": rankings,
        "strongest_signal": primary,
        "strongest_positive_signal": primary if criterion != "stability" else fastest,
        "fastest_growth": fastest,
        "most_reliable": stable,
        "no_positive_growth_signal": not bool(positive),
        "rationale": rationale,
        "interpretation": "Absolute views indicate article attention, not comparable language-market size.",
    }
