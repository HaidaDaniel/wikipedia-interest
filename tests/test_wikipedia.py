import httpx

from wikipedia_interest.cache import FileCache
from wikipedia_interest.wikipedia import WikimediaClient


def test_pageviews_client_parses_items(tmp_path):
    def handler(request):
        return httpx.Response(200, json={"items": [{"timestamp": "2024010100", "views": 12}, {"timestamp": "2024020100", "views": 0}]})

    client = WikimediaClient(FileCache(tmp_path), http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    points = client.pageviews("pl.wikipedia", "Test page", __import__("datetime").datetime(2024, 1, 1), __import__("datetime").datetime(2024, 2, 28), "monthly")
    client.close()
    assert [point.views for point in points] == [12, 0]
    assert list((tmp_path / "pageviews").glob("*.json"))

