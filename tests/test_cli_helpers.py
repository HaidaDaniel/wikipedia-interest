import csv
import json
from datetime import date, datetime

from wikipedia_interest import cli
from wikipedia_interest.cli import _complete_data_through, compact_result
from wikipedia_interest.models import PageviewPoint, ResolvedArticle


def test_complete_data_cutoff_excludes_current_period():
    assert _complete_data_through(date(2026, 9, 24), "monthly") == date(2026, 8, 31)
    assert _complete_data_through(date(2026, 9, 24), "daily") == date(2026, 9, 23)


def test_compact_result_drops_observations():
    full = {"status": "ok", "series": [{"language": "uk", "observations": [{"date": "2024-01-01", "views": 1}], "metrics": {}}]}
    compact = compact_result(full)
    assert "observations" not in compact["series"][0]


def test_analysis_persists_section_target_and_parent_page_source(tmp_path, monkeypatch, capsys):
    requested_articles = []
    resolution = ResolvedArticle(
        "de",
        "de.wikipedia.org",
        "Netbook#Nettop",
        "https://de.wikipedia.org/wiki/Netbook#Nettop",
        "interlanguage_link",
        "low",
        ["section proxy; Pageviews cover the parent page"],
        "Netbook",
        True,
    )

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def pageviews(self, _project, article, *_args):
            requested_articles.append(article)
            return [PageviewPoint(datetime(2024, month, 1), 100 + month) for month in range(1, 7)]

        def close(self):
            pass

    monkeypatch.setattr(cli, "resolve_topic", lambda *_args: [resolution])
    monkeypatch.setattr(cli, "WikimediaClient", FakeClient)
    output_dir = tmp_path / "output"
    cache_dir = tmp_path / "cache"

    exit_code = cli.main([
        "analyze", "--topic", "mini PC", "--languages", "de",
        "--start", "2024-01", "--end", "2024-06", "--granularity", "monthly",
        "--output", str(output_dir), "--cache-dir", str(cache_dir), "--no-cache",
    ])
    payload = json.loads(capsys.readouterr().out)
    persisted = json.loads((output_dir / payload["run_id"] / "result.json").read_text(encoding="utf-8"))
    with (output_dir / payload["run_id"] / "data.csv").open(encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))

    assert exit_code == 0
    assert requested_articles == ["Netbook"]
    assert payload["partial"] is False
    assert payload["comparison"]["no_eligible_series"] is True
    assert payload["comparison"]["excluded_low_confidence"][0]["language"] == "de"
    section = persisted["series"][0]
    assert section["status"] == "ok"
    assert section["article"] == "Netbook#Nettop"
    assert section["pageview_article"] == "Netbook"
    assert section["resolution"]["has_fragment"] is True
    assert section["resolution"]["pageview_title"] == "Netbook"
    assert section["metrics"]
    assert csv_rows[0]["article"] == "Netbook#Nettop"
    assert csv_rows[0]["pageview_article"] == "Netbook"
