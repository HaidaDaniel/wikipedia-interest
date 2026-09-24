from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .models import InterestError
from .fonts import configure_unicode_font


def _successful_series(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [series for series in result.get("series", []) if series.get("status") == "ok" and series.get("observations")]


def create_chart(result: dict[str, Any], path: str | Path) -> Path:
    renderable = _successful_series(result)
    if not renderable:
        raise InterestError("NO_DATA", "cannot create a chart without a successful series")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = len(renderable)
    request = result.get("request", {})
    configure_unicode_font([
        str(request.get("topic", "")),
        *(str(series.get("article", "")) for series in renderable),
        *(str(series.get("language", "")) for series in renderable),
    ])
    height = min(4.8 + 1.45 * (count - 1), 15.5)
    fig, axes = plt.subplots(count, 1, figsize=(10, height), sharex=True, squeeze=False)
    axes_flat = axes[:, 0]
    for index, series in enumerate(renderable):
        ax = axes_flat[index]
        observations = series["observations"]
        dates = pd.to_datetime([row["date"] for row in observations])
        values = [row["views"] for row in observations]
        plot_values = pd.Series(values, dtype="float64")
        ax.plot(dates, plot_values, color="#2563eb", linewidth=1.8, marker="o" if len(values) <= 24 else None, markersize=3, label="views")
        if plot_values.notna().sum() >= 3:
            smooth = plot_values.rolling(3, center=True, min_periods=1).mean()
            ax.plot(dates, smooth, color="#f97316", linewidth=1.6, linestyle="--", label="3-period smooth")
        for anomaly in series.get("anomalies", []):
            ax.axvline(pd.to_datetime(anomaly["date"]), color="#dc2626", alpha=0.18, linewidth=1)
        metrics = series.get("metrics", {})
        candidate = " · low-confidence candidate, excluded from comparison" if series.get("resolution", {}).get("confidence") == "low" else ""
        ax.set_title(f"{series['language']} — {series.get('article', '')} · {metrics.get('trend_label', 'uncertain')}{candidate}", loc="left", fontsize=10, fontweight="normal")
        ax.set_ylabel("pageviews")
        ax.grid(axis="y", alpha=0.2)
        ax.legend(frameon=False, fontsize=8, loc="upper left")
    failed = [series for series in result.get("series", []) if series.get("status") != "ok"]
    suffix = f" · excluded: {', '.join(row.get('language', '?') for row in failed)}" if failed else ""
    fig.suptitle(f"Wikipedia interest: {request.get('topic', 'topic')}\n{request.get('start')} to {request.get('end')}{suffix}", fontsize=13, fontweight="normal")
    axes_flat[-1].set_xlabel("period")
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path
