from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class AnalysisRequest:
    topic: str
    languages: list[str]
    start: date
    end: date
    granularity: str = "auto"
    criterion: str = "balanced"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["start"] = self.start.isoformat()
        value["end"] = self.end.isoformat()
        return value


@dataclass(frozen=True)
class ResolvedArticle:
    language: str
    project: str
    title: str | None
    url: str | None
    method: str
    confidence: str
    warnings: list[str] = field(default_factory=list)
    pageview_title: str | None = None
    has_fragment: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PageviewPoint:
    timestamp: datetime
    views: int

    def to_dict(self) -> dict[str, Any]:
        return {"timestamp": self.timestamp.isoformat(), "views": self.views}


class InterestError(Exception):
    """An expected, machine-readable application error."""

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


@dataclass
class RunResult:
    status: str
    run_id: str
    request: dict[str, Any]
    series: list[dict[str, Any]]
    comparison: dict[str, Any]
    limitations: list[str]
    artifacts: dict[str, str | None]
    analysis_version: str = "0.1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
