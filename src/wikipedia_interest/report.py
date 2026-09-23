from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .charts import create_chart


def _finding(series: dict[str, Any]) -> str:
    m = series["metrics"]
    growth = m.get("trend_pct_per_year")
    growth_text = "trend unavailable" if growth is None else f"{growth:+.1f}% annualized trend"
    return f"{series['language']}: {m['trend_label']}; {growth_text}; evidence {series['reliability']['level']} ({series['reliability']['score']}/100)."


def create_report(result: dict[str, Any], run_dir: str | Path) -> Path:
    run_dir = Path(run_dir)
    chart_path = run_dir / "chart.png"
    if not chart_path.exists():
        create_chart(result, chart_path)
    report_path = run_dir / "report.pdf"
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    fig.text(0.07, 0.965, "Wikipedia Interest Brief", fontsize=19, weight="bold", color="#111827")
    fig.text(0.07, 0.942, result["request"]["topic"], fontsize=12, color="#374151")
    fig.text(0.07, 0.912, f"Question: compare pageview interest from {result['request']['start']} to {result['request']['end']}", fontsize=8.5, color="#4b5563")
    chart = plt.imread(chart_path)
    ax_chart = fig.add_axes([0.07, 0.55, 0.86, 0.31])
    ax_chart.imshow(chart)
    ax_chart.axis("off")
    fig.text(0.07, 0.525, "Key findings", fontsize=11, weight="bold", color="#111827")
    y = 0.498
    for series in result.get("series", [])[:4]:
        fig.text(0.085, y, "• " + _finding(series), fontsize=8.5, color="#1f2937", wrap=True)
        y -= 0.031
    comparison = result.get("comparison", {})
    strongest = comparison.get("strongest_signal")
    if strongest:
        fig.text(0.07, y - 0.005, f"Suggested next signal: {strongest['language']} ({comparison.get('rationale', 'balanced comparison')}).", fontsize=8.5, color="#1d4ed8")
    table_y = y - 0.055
    fig.text(0.07, table_y + 0.035, "Compact comparison", fontsize=10, weight="bold", color="#111827")
    columns = ["Language", "Article", "Total", "Trend", "Evidence"]
    rows = []
    for series in result.get("series", []):
        m = series["metrics"]
        rows.append([series["language"], series.get("article", "")[:22], f"{m['total_views']:,}", m["trend_label"], series["reliability"]["level"]])
    if rows:
        ax_table = fig.add_axes([0.07, table_y - 0.11, 0.86, 0.105])
        ax_table.axis("off")
        table = ax_table.table(cellText=rows, colLabels=columns, loc="center", cellLoc="left", colLoc="left")
        table.auto_set_font_size(False)
        table.set_fontsize(7.5)
        table.scale(1, 1.55)
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#d1d5db")
            if row == 0:
                cell.set_facecolor("#eff6ff")
                cell.set_text_props(weight="bold")
    fig.text(0.07, 0.19, "Caveats", fontsize=10, weight="bold", color="#111827")
    caveat = "Wikipedia pageviews are attention, not market size, willingness to pay, conversion, or product-market fit. Cross-language totals are not directly comparable; inspect article coverage and validate with external research."
    fig.text(0.07, 0.165, caveat, fontsize=8, color="#4b5563", wrap=True, linespacing=1.35)
    fig.text(0.07, 0.105, "Source: Wikimedia Pageviews API · monthly/daily deterministic analysis · reliability is evidence quality, not a confidence interval.", fontsize=7.5, color="#6b7280")
    fig.text(0.07, 0.075, f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · run {result['run_id']}", fontsize=7.5, color="#9ca3af")
    with PdfPages(report_path) as pdf:
        pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
    return report_path

