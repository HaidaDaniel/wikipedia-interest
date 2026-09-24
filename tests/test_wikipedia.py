import httpx
from datetime import datetime

from wikipedia_interest.cache import FileCache
from wikipedia_interest.wikipedia import WikimediaClient


def test_pageviews_client_parses_items(tmp_path):
    def handler(request):
        return httpx.Response(200, json={"items": [{"timestamp": "2024010100", "views": 12}, {"timestamp": "2024020100", "views": 0}]})

    client = WikimediaClient(FileCache(tmp_path), http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    points = client.pageviews("pl.wikipedia", "Test page", datetime(2024, 1, 1), datetime(2024, 2, 28), "monthly")
    client.close()
    assert [point.views for point in points] == [12, 0]
    assert list((tmp_path / "pageviews").glob("*.json"))


def test_retry_after_and_transient_500(tmp_path):
    responses = [
        httpx.Response(429, headers={"Retry-After": "7"}),
        httpx.Response(500),
        httpx.Response(200, json={"items": []}),
    ]
    sleeps = []

    def handler(request):
        return responses.pop(0)

    client = WikimediaClient(FileCache(tmp_path), http_client=httpx.Client(transport=httpx.MockTransport(handler)), sleeper=sleeps.append)
    payload = client._get("https://example.test/data")
    client.close()
    assert payload == {"items": []}
    assert sleeps == [7.0, 10.0]


def test_permanent_404_is_not_retried(tmp_path):
    calls = []

    def handler(request):
        calls.append(1)
        return httpx.Response(404)

    client = WikimediaClient(FileCache(tmp_path), http_client=httpx.Client(transport=httpx.MockTransport(handler)), sleeper=lambda delay: (_ for _ in ()).throw(AssertionError("should not sleep")))
    try:
        client._get("https://example.test/missing")
    except Exception as exc:
        assert getattr(exc, "code", None) == "WIKIMEDIA_API_ERROR"
    else:
        raise AssertionError("expected API error")
    finally:
        client.close()
    assert len(calls) == 1
