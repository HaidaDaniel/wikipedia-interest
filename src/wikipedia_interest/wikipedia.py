from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from .cache import FileCache
from .models import InterestError, PageviewPoint
from .titles import split_title_fragment


class WikimediaAPIError(InterestError):
    pass


USER_AGENT = "wikipedia-interest/0.1 (https://github.com/HaidaDaniel/wikipedia-interest)"
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 3


class WikimediaClient:
    """Small, polite client for MediaWiki and the Wikimedia Pageviews API."""

    def __init__(self, cache: FileCache | None = None, http_client: httpx.Client | None = None, use_cache: bool = True, sleeper: Any = time.sleep):
        self.cache = cache or FileCache()
        self.http = http_client or httpx.Client(timeout=httpx.Timeout(20.0, connect=10.0), headers={"User-Agent": USER_AGENT})
        self.use_cache = use_cache
        self.sleeper = sleeper

    def close(self) -> None:
        self.http.close()

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = self.http.get(url, params=params)
                if response.status_code in RETRYABLE_STATUS_CODES:
                    if attempt == MAX_ATTEMPTS - 1:
                        response.raise_for_status()
                    retry_after = response.headers.get("Retry-After")
                    try:
                        delay = min(float(retry_after), 20.0) if retry_after is not None else min(5.0 * (2**attempt), 20.0)
                    except ValueError:
                        delay = min(5.0 * (2**attempt), 20.0)
                    self.sleeper(delay)
                    continue
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if exc.response.status_code not in RETRYABLE_STATUS_CODES:
                    break
            except (httpx.RequestError, ValueError) as exc:
                last_error = exc
                # Transport errors can be transient; permanent HTTP 4xx are
                # raised immediately above and never enter this retry path.
                if attempt < MAX_ATTEMPTS - 1:
                    self.sleeper(min(5.0 * (2**attempt), 20.0))
        raise WikimediaAPIError("WIKIMEDIA_API_ERROR", f"Wikimedia request failed: {last_error}") from last_error

    def search(self, language: str, query: str, limit: int = 5) -> list[dict[str, Any]]:
        key = f"search|{language}|{query}|{limit}"
        payload = self.cache.get_or_set(
            "resolution",
            key,
            lambda: self._get(f"https://{language}.wikipedia.org/w/api.php", {"action": "query", "list": "search", "srsearch": query, "srlimit": limit, "format": "json", "utf8": 1}),
            self.use_cache,
        )
        return payload.get("query", {}).get("search", [])

    def langlinks(self, language: str, title: str) -> dict[str, str]:
        key = f"langlinks|{language}|{title}"

        def fetch() -> dict[str, str]:
            payload = self._get(f"https://{language}.wikipedia.org/w/api.php", {"action": "query", "prop": "langlinks", "titles": title, "redirects": 1, "lllimit": "max", "format": "json", "utf8": 1})
            pages = payload.get("query", {}).get("pages", {})
            links: dict[str, str] = {}
            for page in pages.values():
                for link in page.get("langlinks", []):
                    if "lang" in link and "*" in link:
                        links[link["lang"]] = link["*"]
            return links

        return self.cache.get_or_set("resolution", key, fetch, self.use_cache)

    def wikidata_id(self, language: str, title: str) -> str | None:
        title, _ = split_title_fragment(title)
        key = f"wikidata-id|{language}|{title}"

        def fetch() -> str | None:
            payload = self._get(f"https://{language}.wikipedia.org/w/api.php", {"action": "query", "prop": "pageprops", "titles": title, "redirects": 1, "format": "json", "utf8": 1})
            pages = payload.get("query", {}).get("pages", {})
            return next((page.get("pageprops", {}).get("wikibase_item") for page in pages.values()), None)

        return self.cache.get_or_set("resolution", key, fetch, self.use_cache)

    def is_disambiguation(self, language: str, title: str) -> bool:
        title, _ = split_title_fragment(title)
        key = f"disambiguation|{language}|{title}"

        def fetch() -> bool:
            payload = self._get(f"https://{language}.wikipedia.org/w/api.php", {"action": "query", "prop": "pageprops", "titles": title, "redirects": 1, "format": "json", "utf8": 1})
            pages = payload.get("query", {}).get("pages", {})
            return any("disambiguation" in page.get("pageprops", {}) for page in pages.values())

        return bool(self.cache.get_or_set("resolution", key, fetch, self.use_cache))

    def wikidata_sitelinks(self, qid: str) -> dict[str, str]:
        key = f"wikidata-sitelinks|{qid}"

        def fetch() -> dict[str, str]:
            payload = self._get("https://www.wikidata.org/w/api.php", {"action": "wbgetentities", "ids": qid, "props": "sitelinks", "format": "json", "utf8": 1})
            entity = payload.get("entities", {}).get(qid, {})
            return {key: value.get("title", "") for key, value in entity.get("sitelinks", {}).items() if value.get("title")}

        return self.cache.get_or_set("resolution", key, fetch, self.use_cache)

    def pageviews(self, project: str, article: str, start: datetime, end: datetime, granularity: str) -> list[PageviewPoint]:
        if granularity not in {"daily", "monthly"}:
            raise InterestError("INVALID_GRANULARITY", "granularity must be daily or monthly")
        article, _ = split_title_fragment(article)
        # Per-article pageviews uses YYYYMMDD boundaries and puts granularity
        # in the route (not in a query parameter).
        start_text = start.strftime("%Y%m%d")
        end_text = end.strftime("%Y%m%d")
        encoded_article = quote(article.replace(" ", "_"), safe="")
        key = f"pageviews|{project}|{article}|all-access|user|{granularity}|{start_text}|{end_text}"
        url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/user/{encoded_article}/{granularity}/{start_text}/{end_text}"

        payload = self.cache.get_or_set("pageviews", key, lambda: self._get(url), self.use_cache)
        points: list[PageviewPoint] = []
        for item in payload.get("items", []):
            raw_timestamp = str(item.get("timestamp", ""))
            try:
                timestamp = datetime.strptime(raw_timestamp[:10], "%Y%m%d%H")
                views = max(0, int(item.get("views", 0)))
            except (TypeError, ValueError):
                continue
            points.append(PageviewPoint(timestamp, views))
        return points
