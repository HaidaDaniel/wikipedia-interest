from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from .analysis import analyze_series, choose_granularity, compare_series
from .cache import FileCache
from .charts import create_chart
from .models import AnalysisRequest, InterestError
from .reliability import assess_reliability
from .report import create_report
from .resolver import resolve_topic, validate_languages
from .runs import inspect_summary, load_run, make_run_dir, write_json
from .wikipedia import WikimediaAPIError, WikimediaClient


LIMITATIONS = [
    "Pageviews measure attention, not people, willingness to pay, conversion or product-market fit.",
    "Absolute views across language editions are not directly comparable as market size.",
    "A single Wikipedia article may not represent the complete concept; review resolution warnings.",
]


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise InterestError("INVALID_REQUEST", message)


def parse_date(value: str, is_end: bool = False) -> date:
    try:
        if len(value) == 7:
            year, month = (int(part) for part in value.split("-"))
            if not 1 <= month <= 12:
                raise ValueError
            next_month = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
            return next_month - timedelta(days=1) if is_end else date(year, month, 1)
        parsed = date.fromisoformat(value)
        return parsed
    except (ValueError, TypeError) as exc:
        raise InterestError("INVALID_DATE", f"invalid date '{value}'; use YYYY-MM or YYYY-MM-DD") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = JsonArgumentParser(prog="wikipedia-interest", description="Deterministic Wikipedia Pageviews interest analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="resolve articles, fetch data, analyse and create a chart")
    analyze.add_argument("--topic")
    analyze.add_argument("--languages", help="comma-separated Wikipedia language codes")
    analyze.add_argument("--start")
    analyze.add_argument("--end")
    analyze.add_argument("--granularity", choices=["auto", "daily", "monthly"], default=None)
    analyze.add_argument("--criterion", choices=["balanced", "growth", "stability"], default=None)
    analyze.add_argument("--output", default="output")
    analyze.add_argument("--cache-dir", default=".cache")
    analyze.add_argument("--no-cache", action="store_true")
    analyze.add_argument("--from-run", help="reuse request fields from a previous run")
    analyze.add_argument("--verbose-json", action="store_true", help="include full observations in stdout; default is compact")
    report = sub.add_parser("report", help="create a one-page PDF from a saved run")
    report.add_argument("--run", required=True)
    inspect = sub.add_parser("inspect-run", help="print a compact summary of a saved run")
    inspect.add_argument("run")
    return parser


def _request_from_args(args: argparse.Namespace, prior: dict[str, Any] | None = None) -> AnalysisRequest:
    prior_request = (prior or {}).get("request", {})
    topic = args.topic or prior_request.get("topic")
    languages_text = args.languages or ",".join(prior_request.get("languages", []))
    start_text = args.start or prior_request.get("start")
    end_text = args.end or prior_request.get("end")
    if not topic or not languages_text or not start_text or not end_text:
        raise InterestError("INVALID_REQUEST", "analyze requires --topic, --languages, --start and --end (or --from-run)")
    start = parse_date(start_text)
    end = parse_date(end_text, is_end=True)
    if start > end:
        raise InterestError("INVALID_DATE_RANGE", "start must not be after end")
    languages = validate_languages(languages_text.split(","))
    granularity = args.granularity or prior_request.get("granularity") or "auto"
    criterion = args.criterion or prior_request.get("criterion") or "balanced"
    return AnalysisRequest(topic.strip(), languages, start, end, granularity, criterion)


def _complete_data_through(today: date, granularity: str) -> date:
    if granularity == "monthly":
        return date(today.year, today.month, 1) - timedelta(days=1)
    return today - timedelta(days=1)


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    compact = {key: value for key, value in result.items() if key != "series"}
    compact["series"] = []
    for series in result.get("series", []):
        compact["series"].append({key: value for key, value in series.items() if key != "observations"})
    return compact


def _analyze(args: argparse.Namespace) -> dict[str, Any]:
    prior = load_run(args.from_run) if args.from_run else None
    request = _request_from_args(args, prior)
    actual_granularity = choose_granularity(request.start, request.end, request.granularity)
    complete_through = _complete_data_through(datetime.now(timezone.utc).date(), actual_granularity)
    available_end = min(request.end, complete_through)
    if request.start > available_end:
        raise InterestError("NO_DATA", "requested range is after the latest complete Wikimedia period", {"data_through": complete_through.isoformat()})
    partial_period_excluded = request.end > available_end
    persisted_request = {
        **request.to_dict(),
        "effective_granularity": actual_granularity,
        "requested_end": request.end.isoformat(),
        "data_through": available_end.isoformat(),
        "partial_period_excluded": partial_period_excluded,
    }
    run_id, run_dir = make_run_dir(args.output, persisted_request)
    write_json(run_dir / "request.json", persisted_request)
    client = WikimediaClient(FileCache(args.cache_dir), use_cache=not args.no_cache)
    pageview_rows: list[dict[str, Any]] = []
    series: list[dict[str, Any]] = []
    try:
        resolutions = resolve_topic(request.topic, request.languages, client)
        for resolution in resolutions:
            common = {
                "language": resolution.language,
                "project": resolution.project,
                "article": resolution.title,
                "pageview_article": resolution.pageview_title,
                "resolution": resolution.to_dict(),
            }
            if not resolution.title:
                series.append({**common, "status": "error", "error_code": "ARTICLE_NOT_FOUND", "error": "No matching article found."})
                continue
            try:
                points = client.pageviews(resolution.project, resolution.pageview_title or resolution.title, datetime.combine(request.start, time.min), datetime.combine(available_end, time(23, 59)), actual_granularity)
            except WikimediaAPIError as exc:
                series.append({**common, "status": "error", "error_code": exc.code, "error": exc.message})
                continue
            pageview_rows.extend({"language": resolution.language, "article": resolution.title, "pageview_article": resolution.pageview_title or resolution.title, **point.to_dict()} for point in points)
            if not points:
                series.append({**common, "status": "error", "error_code": "NO_DATA", "error": "Wikimedia returned no pageview observations."})
                continue
            analysis = analyze_series(points, request.start, available_end, actual_granularity, resolution.confidence)
            reliability = assess_reliability(analysis["metrics"], analysis["anomalies"], resolution.confidence)
            series.append({**common, "status": "ok", "metrics": analysis["metrics"], "reliability": reliability, "anomalies": analysis["anomalies"], "observations": analysis["observations"]})
    finally:
        client.close()
    if not any(row.get("status") == "ok" for row in series):
        raise InterestError("NO_DATA", "no requested language produced usable pageview data", {"run_id": run_id})
    comparison = compare_series(series, request.criterion)
    limitations = list(LIMITATIONS)
    if partial_period_excluded:
        limitations.append(f"Requested end extends beyond available data; observations were fetched through {available_end.isoformat()}.")
    if comparison.get("excluded_low_confidence"):
        languages = ", ".join(item["language"] for item in comparison["excluded_low_confidence"])
        limitations.append(f"Low-confidence article candidates ({languages}) were retained for inspection but excluded from comparison. Refine the topic and rerun if a resolved title does not represent the intended concept.")
    if any(row.get("resolution", {}).get("has_fragment") for row in series):
        limitations.append("Section-level concept matches use Pageviews for the parent article; treat these as low-confidence proxies.")
    succeeded = sum(row.get("status") == "ok" for row in series)
    result = {
        "status": "ok",
        "run_id": run_id,
        "request": persisted_request,
        "series": series,
        "comparison": comparison,
        "limitations": limitations,
        "partial": succeeded < len(request.languages),
        "languages_requested": len(request.languages),
        "languages_succeeded": succeeded,
        "languages_failed": len(request.languages) - succeeded,
        "artifacts": {"chart": str(run_dir / "chart.png"), "data": str(run_dir / "data.csv"), "pageviews": str(run_dir / "pageviews.json"), "report": None},
        "analysis_version": "0.1",
    }
    # A flat JSON/CSV pair is convenient for human review. It is normalized
    # pageview data, not an unmodified Wikimedia response.
    write_json(run_dir / "pageviews.json", pageview_rows)
    import csv
    with (run_dir / "data.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["language", "article", "pageview_article", "timestamp", "views"])
        writer.writeheader()
        writer.writerows(pageview_rows)
    create_chart(result, run_dir / "chart.png")
    write_json(run_dir / "result.json", result)
    write_json(run_dir / "metadata.json", {"run_id": run_id, "created_at": datetime.now(timezone.utc).isoformat(), "analysis_version": "0.1", "effective_granularity": actual_granularity, "cache_enabled": not args.no_cache, "data_through": available_end.isoformat()})
    return result if args.verbose_json else compact_result(result)


def _handle(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "analyze":
        return _analyze(args)
    if args.command == "report":
        result = load_run(args.run)
        report_path = create_report(result, args.run)
        result["artifacts"]["report"] = str(report_path)
        write_json(Path(args.run) / "result.json", result)
        return {"status": "ok", "run_id": result["run_id"], "report": str(report_path)}
    if args.command == "inspect-run":
        return inspect_summary(load_run(args.run))
    raise InterestError("INVALID_COMMAND", "unknown command")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        payload = _handle(args)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except InterestError as exc:
        print(json.dumps({"status": "error", "error": {"code": exc.code, "message": exc.message, "details": exc.details}}, ensure_ascii=False, indent=2))
        print(f"{exc.code}: {exc.message}", file=sys.stderr)
        return 2
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(json.dumps({"status": "error", "error": {"code": "LOCAL_ERROR", "message": str(exc), "details": {}}}, ensure_ascii=False, indent=2))
        print(f"LOCAL_ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
