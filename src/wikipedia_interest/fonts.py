from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable
import warnings

import matplotlib
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font


# Static labels used across charts and reports. Topic, article, and language
# text is added by the caller so unused scripts are not required.
BASELINE_TEXT = "Wikipedia Interest Brief Pageviews views period trend Question compare Key findings evidence language article total generated • — ·"
PREFERRED_FAMILIES = (
    "noto sans cjk",
    "source han",
    "noto sans",
    "wenquanyi",
    "unifont",
    "ipa gothic",
    "dejavu sans",
)


@lru_cache(maxsize=1)
def _font_inventory() -> tuple[tuple[str, str, frozenset[int]], ...]:
    paths = set(font_manager.findSystemFonts(fontext="ttf"))
    paths.update(font_manager.findSystemFonts(fontext="otf"))
    inventory: list[tuple[str, str, frozenset[int]]] = []
    for raw_path in sorted(paths):
        try:
            path = str(Path(raw_path))
            name = font_manager.FontProperties(fname=path).get_name()
            charmap = frozenset(FT2Font(path).get_charmap())
        except (OSError, RuntimeError, ValueError):
            continue
        if charmap:
            inventory.append((name, path, charmap))
    return tuple(inventory)


def _preference_rank(name: str) -> int:
    lowered = name.casefold()
    for rank, family in enumerate(PREFERRED_FAMILIES):
        if family in lowered:
            return rank
    return len(PREFERRED_FAMILIES)


def _select_font(text: str) -> tuple[list[str], bool]:
    required = {ord(char) for char in text if not char.isspace()}
    coverage_by_family: dict[str, set[int]] = {}
    display_name_by_family: dict[str, str] = {}
    for name, path, charmap in _font_inventory():
        family_key = name.casefold()
        coverage_by_family.setdefault(family_key, set()).update(charmap)
        display_name_by_family.setdefault(family_key, name)

    if not coverage_by_family:
        return ["DejaVu Sans"], False

    complete_families = [
        family_key
        for family_key, charmap in coverage_by_family.items()
        if required <= charmap
    ]
    if complete_families:
        best = min(
            complete_families,
            key=lambda key: (_preference_rank(display_name_by_family[key]), key),
        )
        return [display_name_by_family[best]], True

    # Greedily add the family that covers the most remaining characters.
    # DejaVu is kept as the final fallback, rather than winning on Latin
    # coverage before a more useful script-specific family is considered.
    fallback_key = next(
        (key for key, name in display_name_by_family.items() if "dejavu sans" in name.casefold()),
        None,
    )
    available = set(coverage_by_family) - ({fallback_key} if fallback_key else set())
    selected: list[str] = []
    covered: set[int] = set()
    while available:
        best = max(
            available,
            key=lambda key: (
                len((required - covered) & coverage_by_family[key]),
                -_preference_rank(display_name_by_family[key]),
                key,
            ),
        )
        added = (required - covered) & coverage_by_family[best]
        if not added:
            break
        selected.append(display_name_by_family[best])
        covered.update(added)
        available.remove(best)
        if required <= covered:
            return selected, True

    if fallback_key:
        selected.append(display_name_by_family[fallback_key])
        covered.update(coverage_by_family[fallback_key])
    elif "dejavu sans" not in {name.casefold() for name in selected}:
        selected.append("DejaVu Sans")
    return selected or ["DejaVu Sans"], required <= covered


def configure_unicode_font(texts: Iterable[str] = ()) -> tuple[list[str], bool]:
    """Configure an ordered font stack covering the artifact's actual text.

    System fonts are deliberately selected at runtime so the package stays
    small and works across Linux/macOS/Windows environments. A best-effort
    fallback is still used when no one installed font covers every script.
    """

    text = BASELINE_TEXT + " " + " ".join(str(value) for value in texts if value)
    families, complete = _select_font(text)
    matplotlib.rcParams["font.family"] = families
    matplotlib.rcParams["axes.unicode_minus"] = False
    if not complete:
        warnings.warn(
            "No installed font stack covers all requested glyphs; "
            "install Noto Sans CJK, Source Han Sans, WenQuanYi or Unifont "
            "for complete chart/PDF rendering.",
            RuntimeWarning,
            stacklevel=2,
        )
    return families, complete
