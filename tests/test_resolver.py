from wikipedia_interest.resolver import resolve_topic, validate_languages


class FakeClient:
    def search(self, language, query, limit=5):
        if language == "en":
            return [{"title": "Intermittent fasting"}]
        if language == "pl":
            return [{"title": "Post przerywany"}]
        return []

    def langlinks(self, language, title):
        return {"pl": "Post przerywany"}


def test_interlanguage_resolution_and_fallback():
    result = resolve_topic("intermittent fasting", ["pl", "cs"], FakeClient())
    assert result[0].title == "Post przerywany"
    assert result[0].method == "interlanguage_link"
    assert result[1].title is None
    assert result[1].method == "unresolved"


def test_language_validation_deduplicates():
    assert validate_languages(["PL", "pl", "uk"]) == ["pl", "uk"]

