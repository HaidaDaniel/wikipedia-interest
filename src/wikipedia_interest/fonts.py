from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable
import warnings

import matplotlib
from matplotlib import font_manager
from matplotlib.ft2font import FT2Font


# These samples cover the scripts most likely to appear in article titles and
# language labels. The actual chart/report text is added by the caller too.
BASELINE_TEXT = "Wikipedia interest Астрономія 3Dプリント 3차원 인쇄 Přerušovaný půst"
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


def _select_font(text: str) -> tuple[str, bool]:
    required = {ord(char) for char in text if not char.isspace()}
    candidates: list[tuple[bool, int, int, str, str]] = []
    for name, path, charmap in _font_inventory():
        coverage = len(required & charmap)
        candidates.append((coverage == len(required), coverage, -_preference_rank(name), name, path))
    if not candidates:
        return "DejaVu Sans", False
    full, _, _, name, _ = max(candidates)
    return name, full


def configure_unicode_font(texts: Iterable[str] = ()) -> tuple[str, bool]:
    """Configure a broadly Unicode-capable installed font for an artifact.

    System fonts are deliberately selected at runtime so the package stays
    small and works across Linux/macOS/Windows environments. A best-effort
    fallback is still used when no one installed font covers every script.
    """

    text = BASELINE_TEXT + " " + " ".join(str(value) for value in texts if value)
    family, complete = _select_font(text)
    matplotlib.rcParams["font.family"] = [family]
    matplotlib.rcParams["axes.unicode_minus"] = False
    if not complete:
        warnings.warn(
            "No installed font covers all requested multilingual glyphs; "
            "install Noto Sans CJK, Source Han Sans, WenQuanYi or Unifont "
            "for complete chart/PDF rendering.",
            RuntimeWarning,
            stacklevel=2,
        )
    return family, complete
