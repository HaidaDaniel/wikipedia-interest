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


class CoveredClient(FakeClient):
    def __init__(self):
        self.wikidata_calls = 0

    def langlinks(self, language, title):
        return {"pl": "Post przerywany", "cs": "Přerušovaný půst"}

    def wikidata_id(self, language, title):
        self.wikidata_calls += 1
        return "Q1"

    def wikidata_sitelinks(self, qid):
        self.wikidata_calls += 1
        return {}


def test_wikidata_is_not_called_when_langlinks_cover_targets():
    client = CoveredClient()
    result = resolve_topic("intermittent fasting", ["pl", "cs"], client)
    assert [item.title for item in result] == ["Post przerywany", "Přerušovaný půst"]
    assert client.wikidata_calls == 0


class FallbackClient(FakeClient):
    def search(self, language, query, limit=5):
        if language == "cs":
            return [{"title": "Přerušovaný půst"}, {"title": "Půst"}]
        return super().search(language, query, limit)


def test_target_search_top_match_is_explicitly_low_confidence():
    result = resolve_topic("intermittent fasting", ["cs"], FallbackClient())
    assert result[0].method == "target_language_search"
    assert result[0].confidence == "low"
    assert result[0].warnings


class WeakEnglishMatchClient(FakeClient):
    def search(self, language, query, limit=5):
        if language == "en":
            return [{"title": "Self-hosting (compilers)"}]
        return []


def test_weak_english_top_match_is_low_confidence():
    result = resolve_topic("self-hosted AI", ["en"], WeakEnglishMatchClient())
    assert result[0].title == "Self-hosting (compilers)"
    assert result[0].confidence == "low"
    assert any("weak lexical overlap" in warning for warning in result[0].warnings)
