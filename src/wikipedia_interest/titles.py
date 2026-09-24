from __future__ import annotations

from urllib.parse import quote


def split_title_fragment(title: str) -> tuple[str, str | None]:
    """Return a page title and optional MediaWiki section fragment.

    Only a literal ``#`` is a separator. Percent-encoded text remains part of
    the title and is encoded normally when constructing a URL.
    """
    page, separator, fragment = title.partition("#")
    if not separator or not page:
        return title, None
    return page, fragment or None


def wikipedia_article_url(language: str, title: str) -> str:
    page, fragment = split_title_fragment(title)
    url = f"https://{language}.wikipedia.org/wiki/{quote(page.replace(' ', '_'), safe='')}"
    if fragment is not None:
        url += f"#{quote(fragment.replace(' ', '_'), safe='')}"
    return url
