import warnings

import matplotlib

from wikipedia_interest import fonts


def _inventory(name: str, text: str):
    return ((name, "/synthetic/font.ttf", frozenset(map(ord, text))),)


def test_latin_request_does_not_require_unused_cjk_glyphs(monkeypatch):
    monkeypatch.setattr(fonts, "_font_inventory", lambda: _inventory("Latin Sans", fonts.BASELINE_TEXT + " heat pump en"))
    with matplotlib.rc_context(), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        families, complete = fonts.configure_unicode_font(["heat pump", "en"])

    assert families == ["Latin Sans"]
    assert complete is True
    assert not caught


def test_cjk_request_warns_when_inventory_cannot_cover_requested_text(monkeypatch):
    request = "3Dプリント 3차원 인쇄"
    monkeypatch.setattr(fonts, "_font_inventory", lambda: _inventory("Latin Sans", fonts.BASELINE_TEXT))
    with matplotlib.rc_context(), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        families, complete = fonts.configure_unicode_font([request])

    assert families == ["Latin Sans", "DejaVu Sans"]
    assert complete is False
    assert len(caught) == 1
    assert "No installed font stack covers all requested glyphs" in str(caught[0].message)


def test_cjk_request_uses_installed_family_when_it_covers_text(monkeypatch):
    request = "3Dプリント 3차원 인쇄"
    monkeypatch.setattr(fonts, "_font_inventory", lambda: _inventory("Synthetic CJK", fonts.BASELINE_TEXT + request))
    with matplotlib.rc_context(), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        families, complete = fonts.configure_unicode_font([request])

    assert families == ["Synthetic CJK"]
    assert complete is True
    assert not caught


def test_font_selection_builds_greedy_fallback_stack(monkeypatch):
    latin = frozenset(map(ord, fonts.BASELINE_TEXT + " topic"))
    cjk = frozenset(map(ord, "プリント"))
    monkeypatch.setattr(
        fonts,
        "_font_inventory",
        lambda: (
            ("Latin Sans", "/synthetic/latin.ttf", latin),
            ("Noto Sans CJK JP", "/synthetic/cjk.ttf", cjk),
        ),
    )

    families, complete = fonts._select_font(fonts.BASELINE_TEXT + " topic プリント")

    assert families == ["Latin Sans", "Noto Sans CJK JP"]
    assert complete is True
