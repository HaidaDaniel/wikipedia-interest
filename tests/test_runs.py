from wikipedia_interest.runs import inspect_summary, make_run_dir, write_json


def test_run_persistence_and_compact_summary(tmp_path):
    run_id, path = make_run_dir(tmp_path, {"topic": "astronomy"})
    result = {"status": "ok", "run_id": run_id, "request": {"topic": "astronomy"}, "series": [{"language": "uk", "article": "Astronomy", "metrics": {"trend_label": "flat", "trend_pct_per_year": 1}, "reliability": {"level": "high", "score": 75}}], "comparison": {}, "artifacts": {}}
    write_json(path / "result.json", result)
    summary = inspect_summary(result)
    assert summary["run_id"] == run_id
    assert summary["series"][0]["trend"] == "flat"

