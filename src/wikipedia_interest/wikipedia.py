from __future__ import annotations

import time
from datetime import datetime
from typing import Any
from urllib.parse import quote

import httpx

from .cache import FileCache
from .models import InterestError, PageviewPoint


class WikimediaAPIError(InterestError):
    pass


class WikimediaClient:
    """Small, polite client for MediaWiki and the Wikimedia Pageviews API."""

    def __init__(self, cache: FileCache | None = None, http_client: httpx.Client | None = None, use_cache: bool = True):
        self.cache = cache or FileCache()
        self.http = http_client or httpx.Client(timeout=httpx.Timeout(20.0, connect=10.0), headers={"User-Agent": "wikipedia-interest/0.1 (research skill)"})
        self.use_cache = use_cache

    def close(self) -> None:
        self.http.close()

    def _get(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.http.get(url, params=params)
                if response.status_code in (429, 500, 502, 503, 504):
                    response.raise_for_status()
                response.raise_for_status()
                return response.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(0.35 * (2**attempt))
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
        key = f"wikidata-id|{language}|{title}"

        def fetch() -> str | None:
            payload = self._get(f"https://{language}.wikipedia.org/w/api.php", {"action": "query", "prop": "pageprops", "titles": title, "redirects": 1, "format": "json", "utf8": 1})
            pages = payload.get("query", {}).get("pages", {})
            return next((page.get("pageprops", {}).get("wikibase_item") for page in pages.values()), None)

        return self.cache.get_or_set("resolution", key, fetch, self.use_cache)

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
