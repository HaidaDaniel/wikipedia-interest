from pathlib import Path

from wikipedia_interest.charts import create_chart
from wikipedia_interest.fonts import configure_unicode_font
from wikipedia_interest.report import create_report


def series(language: str, status: str = "ok"):
    if status != "ok":
        return {"language": language, "status": "error", "error_code": "ARTICLE_NOT_FOUND", "article": None}
    observations = [{"date": f"2024-{index:02d}-01", "views": 100 + index * 5, "observed": True} for index in range(1, 7)]
    return {
        "language": language,
        "status": "ok",
        "article": f"Article {language}",
        "observations": observations,
        "metrics": {"trend_label": "growing", "trend_pct_per_year": 20, "total_views": 700},
        "reliability": {"level": "medium", "score": 60},
        "anomalies": [],
    }


def result(series_list):
    return {
        "run_id": "test-run",
        "status": "ok",
        "request": {"topic": "test topic", "start": "2024-01-01", "end": "2024-06-30"},
        "series": series_list,
        "comparison": {"criterion": "balanced", "strongest_signal": None, "no_positive_growth_signal": False},
    }


def test_chart_supports_one_two_and_four_series(tmp_path):
    for count in (1, 2, 4):
        path = tmp_path / f"chart-{count}.png"
        create_chart(result([series(chr(97 + index)) for index in range(count)]), path)
        assert path.exists() and path.stat().st_size > 1000


def test_unicode_font_selection_handles_multilingual_titles():
    family, complete = configure_unicode_font(["3Dプリント", "3차원 인쇄", "Астрономія", "Přerušovaný půst"])
    assert family
    assert isinstance(complete, bool)


def test_partial_success_chart_and_pdf_are_generated(tmp_path):
    payload = result([series("pl", "error"), series("uk"), series("cs")])
    chart = tmp_path / "chart.png"
    create_chart(payload, chart)
    report = create_report(payload, tmp_path)
    assert chart.exists() and chart.stat().st_size > 1000
    assert report.exists() and report.stat().st_size > 1000
