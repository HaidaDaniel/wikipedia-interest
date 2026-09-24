from __future__ import annotations

import re
from urllib.parse import quote

from .models import InterestError, ResolvedArticle
from .wikipedia import WikimediaClient


LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]+)?$")


def _norm(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").split())


def validate_languages(languages: list[str]) -> list[str]:
    cleaned = [value.strip().lower() for value in languages if value.strip()]
    if not cleaned or any(not LANGUAGE_RE.match(value) for value in cleaned):
        raise InterestError("INVALID_LANGUAGES", "languages must be comma-separated Wikipedia language codes")
    return list(dict.fromkeys(cleaned))


def resolve_topic(topic: str, languages: list[str], client: WikimediaClient) -> list[ResolvedArticle]:
    topic = topic.strip()
    if not topic:
        raise InterestError("INVALID_TOPIC", "topic must not be empty")
    languages = validate_languages(languages)
    english_results = client.search("en", topic)
    canonical: str | None = None
    method = "unresolved"
    confidence = "low"
    warnings: list[str] = []
    if english_results:
        exact = next((row["title"] for row in english_results if _norm(row.get("title", "")) == _norm(topic)), None)
        canonical = exact or english_results[0].get("title")
        if exact:
            method, confidence = "english_exact_plus_interlanguage", "high"
        else:
            method, confidence = "english_search_plus_interlanguage", "medium"
            warnings.append(f"English search selected '{canonical}' for requested topic '{topic}'.")

    links = client.langlinks("en", canonical) if canonical else {}
    # Interlanguage links are usually enough. Only use Wikidata when a
    # requested edition is still missing, reducing calls and rate-limit risk.
    missing_languages = [language for language in languages if language != "en" and language not in links]
    if canonical and missing_languages and hasattr(client, "wikidata_id") and hasattr(client, "wikidata_sitelinks"):
        try:
            wikidata_id = client.wikidata_id("en", canonical)
            if wikidata_id:
                for site, title in client.wikidata_sitelinks(wikidata_id).items():
                    if site.endswith("wiki") and site != "commonswiki":
                        links.setdefault(site[:-4], title)
        except InterestError:
            # Pageviews analysis must remain usable when Wikidata is rate-limited;
            # the already fetched langlinks are still valid evidence.
            warnings.append("Wikidata sitelinks were unavailable; used Wikipedia interlanguage links only.")
    resolved: list[ResolvedArticle] = []
    for language in languages:
        if language == "en" and canonical:
            title = canonical
            item_method, item_confidence, item_warnings = method, confidence, list(warnings)
        elif language in links:
            title = links[language]
            item_method, item_confidence, item_warnings = "interlanguage_link", confidence, list(warnings)
        else:
            try:
                results = client.search(language, topic)
            except InterestError:
                results = []
                search_unavailable = True
            else:
                search_unavailable = False
            exact = next((row["title"] for row in results if _norm(row.get("title", "")) == _norm(topic)), None)
            top = results[0].get("title") if results else None
            title = exact or top
            if title:
                item_method = "target_language_exact_search" if exact else "target_language_search"
                item_confidence = "medium" if exact else "low"
                item_warnings = [f"No English interlanguage link for {language}; target-language search was used."]
                if not exact:
                    item_warnings.append(f"Search selected '{title}'; verify that it represents the requested concept.")
            else:
                reason = "target-language search was unavailable" if search_unavailable else "no confident article match found"
                item_method, item_confidence, item_warnings = "unresolved", "low", [f"{reason} for language '{language}'."]
        resolved.append(ResolvedArticle(language, f"{language}.wikipedia.org", title, f"https://{language}.wikipedia.org/wiki/{quote(title.replace(' ', '_'), safe='') }" if title else None, item_method, item_confidence, item_warnings))
    return resolved
