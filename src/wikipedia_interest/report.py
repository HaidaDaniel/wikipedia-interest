from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .charts import create_chart
from .fonts import configure_unicode_font


def _finding(series: dict[str, Any]) -> str:
    metrics = series.get("metrics", {})
    growth = metrics.get("trend_pct_per_year")
    growth_text = "trend unavailable" if growth is None else f"{growth:+.1f}% annualized trend"
    reliability = series.get("reliability", {})
    resolution = series.get("resolution", {})
    confidence = resolution.get("confidence")
    resolution_text = "; low-confidence candidate — excluded from comparison" if confidence == "low" else ""
    if resolution.get("has_fragment"):
        source = series.get("pageview_article") or resolution.get("pageview_title", "parent page")
        resolution_text += f"; section proxy — Pageviews cover parent page {source}"
    return f"{series.get('language', '?')}: {metrics.get('trend_label', 'uncertain')}; {growth_text}; evidence {reliability.get('level', 'unknown')} ({reliability.get('score', 'n/a')}/100){resolution_text}."


def create_report(result: dict[str, Any], run_dir: str | Path) -> Path:
    run_dir = Path(run_dir)
    chart_path = run_dir / "chart.png"
    if not chart_path.exists():
        create_chart(result, chart_path)
    report_path = run_dir / "report.pdf"
    successful = [series for series in result.get("series", []) if series.get("status") == "ok" and "metrics" in series]
    failed = [series for series in result.get("series", []) if series.get("status") != "ok"]
    if not successful:
        raise ValueError("cannot create a report without a successful series")

    request = result.get("request", {})
    configure_unicode_font([
        str(request.get("topic", "")),
        *(str(series.get("article", "")) for series in successful),
        *(str(series.get("language", "")) for series in successful),
    ])
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    fig.text(0.07, 0.965, "Wikipedia Interest Brief", fontsize=19, weight="normal", color="#111827")
    fig.text(0.07, 0.942, request.get("topic", "topic"), fontsize=12, color="#374151")
    fig.text(0.07, 0.912, f"Question: compare pageview interest from {request.get('start')} to {request.get('end')}", fontsize=8.5, color="#4b5563")
    chart = plt.imread(chart_path)
    ax_chart = fig.add_axes([0.07, 0.55, 0.86, 0.31])
    ax_chart.imshow(chart)
    ax_chart.axis("off")
    fig.text(0.07, 0.525, "Key findings", fontsize=11, weight="normal", color="#111827")
    y = 0.498
    for series in successful[:4]:
        fig.text(0.085, y, "• " + _finding(series), fontsize=8.5, color="#1f2937", wrap=True)
        y -= 0.031
    for series in failed[:4]:
        fig.text(0.085, y, f"• {series.get('language', '?')}: unresolved/excluded ({series.get('error_code', 'error')}).", fontsize=8.2, color="#b45309", wrap=True)
        y -= 0.027

    comparison = result.get("comparison", {})
    strongest = comparison.get("strongest_signal")
    if comparison.get("no_eligible_series") is True:
        recommendation = "No verified article matches are eligible for comparison; review or refine the low-confidence candidates."
    elif comparison.get("criterion") == "stability" and strongest:
        recommendation = f"Most reliable evidence: {strongest['language']} (stability criterion)."
    elif strongest:
        recommendation = f"Strongest positive signal for further validation: {strongest['language']}."
    else:
        recommendation = "No clear positive growth signal was found in this comparison."
    fig.text(0.07, y - 0.005, recommendation, fontsize=8.5, color="#1d4ed8")

    table_y = y - 0.055
    fig.text(0.07, table_y + 0.035, "Compact comparison", fontsize=10, weight="normal", color="#111827")
    columns = ["Language", "Article/status", "Total", "Trend", "Evidence"]
    rows = []
    for series in successful:
        metrics = series["metrics"]
        confidence = series.get("resolution", {}).get("confidence")
        article = series.get("article", "")[:22]
        if confidence == "low":
            article = f"{article}*"
        rows.append([series["language"], article, f"{metrics.get('total_views', 0):,}", metrics.get("trend_label", "uncertain"), series.get("reliability", {}).get("level", "n/a")])
    for series in failed:
        rows.append([series.get("language", "?"), "unresolved / excluded", "—", "—", "—"])
    if rows:
        ax_table = fig.add_axes([0.07, table_y - 0.11, 0.86, 0.105])
        ax_table.axis("off")
        table = ax_table.table(cellText=rows, colLabels=columns, loc="center", cellLoc="left", colLoc="left")
        table.auto_set_font_size(False)
        table.set_fontsize(7.0 if len(rows) > 4 else 7.5)
        table.scale(1, 1.45)
        for (row, col), cell in table.get_celld().items():
            cell.set_edgecolor("#d1d5db")
            if row == 0:
                cell.set_facecolor("#eff6ff")
                cell.set_text_props(weight="normal")

    fig.text(0.07, 0.19, "Caveats", fontsize=10, weight="normal", color="#111827")
    caveat = "Wikipedia pageviews are attention, not market size, willingness to pay, conversion, or product-market fit. Cross-language totals are not directly comparable; inspect article coverage and validate with external research."
    fig.text(0.07, 0.165, caveat, fontsize=8, color="#4b5563", wrap=True, linespacing=1.35)
    if any(series.get("resolution", {}).get("confidence") == "low" for series in successful):
        fig.text(0.07, 0.14, "* Low-confidence candidate; excluded from comparison. Refine the topic and rerun if the title does not represent the intended concept.", fontsize=7.5, color="#b45309")
    source_y = 0.105 if not any(series.get("resolution", {}).get("confidence") == "low" for series in successful) else 0.09
    fig.text(0.07, source_y, "Source: Wikimedia Pageviews API · monthly/daily deterministic analysis · reliability is evidence quality, not a confidence interval.", fontsize=7.5, color="#6b7280")
    fig.text(0.07, source_y - 0.03, f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · run {result['run_id']}", fontsize=7.5, color="#9ca3af")
    with PdfPages(report_path) as pdf:
        pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)
    return report_path
