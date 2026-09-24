from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(_json_safe(value), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def _json_safe(value: Any) -> Any:
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def make_run_dir(output_root: str | Path, request: dict[str, Any]) -> tuple[str, Path]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    short_hash = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()[:8]
    run_id = f"{stamp}-{short_hash}"
    path = Path(output_root) / run_id
    path.mkdir(parents=True, exist_ok=False)
    return run_id, path


def load_run(run_path: str | Path) -> dict[str, Any]:
    path = Path(run_path)
    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"run directory does not exist: {path}")
    result_path = path / "result.json"
    if not result_path.exists():
        raise FileNotFoundError(f"result.json is missing from {path}")
    return json.loads(result_path.read_text(encoding="utf-8"))


def inspect_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": result.get("status"),
        "run_id": result.get("run_id"),
        "request": result.get("request"),
        "series": [{"language": row.get("language"), "article": row.get("article"), "trend": row.get("metrics", {}).get("trend_label"), "trend_pct_per_year": row.get("metrics", {}).get("trend_pct_per_year"), "reliability": row.get("reliability")} for row in result.get("series", [])],
        "comparison": result.get("comparison"),
        "artifacts": result.get("artifacts"),
    }
