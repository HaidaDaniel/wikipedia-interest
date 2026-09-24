from __future__ import annotations

import re

from .models import InterestError, ResolvedArticle
from .titles import split_title_fragment, wikipedia_article_url
from .wikipedia import WikimediaClient


LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]+)?$")
TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def _norm(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").split())


def _lexical_overlap(topic: str, title: str) -> float:
    topic_tokens = set(TOKEN_RE.findall(_norm(topic)))
    title_tokens = set(TOKEN_RE.findall(_norm(title)))
    if not topic_tokens:
        return 0.0
    return len(topic_tokens & title_tokens) / len(topic_tokens)


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
            method = "english_search_plus_interlanguage"
            confidence = "medium" if _lexical_overlap(topic, canonical or "") >= 0.5 else "low"
            warnings.append(f"English search selected '{canonical}' for requested topic '{topic}'.")
            if confidence == "low":
                warnings.append("English search result has weak lexical overlap; treat the resolution as a low-confidence candidate.")

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
                    item_warnings.append(f"Search selected '{title}'; review whether it represents the requested concept.")
            else:
                reason = "target-language search was unavailable" if search_unavailable else "no confident article match found"
                item_method, item_confidence, item_warnings = "unresolved", "low", [f"{reason} for language '{language}'."]
        pageview_title, fragment = split_title_fragment(title) if title else (None, None)
        has_fragment = fragment is not None
        if has_fragment:
            item_confidence = "low"
            item_warnings.append(
                f"Resolved concept maps to a section of the broader '{pageview_title}' article. "
                "Pageviews cover the parent page, so this is a low-confidence proxy and is excluded from comparison."
            )
        if title and hasattr(client, "is_disambiguation"):
            try:
                if client.is_disambiguation(language, title):
                    item_confidence = "low"
                    item_warnings.append("Resolved title is a Wikipedia disambiguation page; treat it as a low-confidence candidate and review its concept match.")
            except InterestError:
                item_warnings.append("Disambiguation status could not be checked; review the article match before using its metrics.")
        resolved.append(ResolvedArticle(
            language,
            f"{language}.wikipedia.org",
            title,
            wikipedia_article_url(language, title) if title else None,
            item_method,
            item_confidence,
            item_warnings,
            pageview_title,
            has_fragment,
        ))
    return resolved
