from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def create_chart(result: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2 if len(result.get("series", [])) > 1 else 1, 1, figsize=(10, 6.2 if len(result.get("series", [])) > 1 else 4.8), sharex=True, squeeze=False)
    axes_flat = axes[:, 0]
    for index, series in enumerate(result.get("series", [])):
        ax = axes_flat[index]
        observations = series.get("observations", [])
        dates = pd.to_datetime([row["date"] for row in observations])
        values = [row["views"] for row in observations]
        ax.plot(dates, values, color="#2563eb", linewidth=1.8, marker="o" if len(values) <= 24 else None, markersize=3, label="views")
        if len(values) >= 3:
            smooth = pd.Series(values).rolling(3, center=True, min_periods=1).mean()
            ax.plot(dates, smooth, color="#f97316", linewidth=1.6, linestyle="--", label="3-period smooth")
        for anomaly in series.get("anomalies", []):
            anomaly_date = pd.to_datetime(anomaly["date"])
            ax.axvline(anomaly_date, color="#dc2626", alpha=0.18, linewidth=1)
        metrics = series.get("metrics", {})
        ax.set_title(f"{series['language']} — {series.get('article', '')} · {metrics.get('trend_label', 'uncertain')}", loc="left", fontsize=10, fontweight="bold")
        ax.set_ylabel("pageviews")
        ax.grid(axis="y", alpha=0.2)
        ax.legend(frameon=False, fontsize=8, loc="upper left")
    fig.suptitle(f"Wikipedia interest: {result['request']['topic']}\n{result['request']['start']} to {result['request']['end']}", fontsize=13, fontweight="bold")
    axes_flat[-1].set_xlabel("period")
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return path

