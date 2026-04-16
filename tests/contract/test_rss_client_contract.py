from datetime import UTC

from app.integrations.rss.client import RSSClient


RSS_XML = """<?xml version='1.0' encoding='UTF-8'?>
<rss version='2.0'>
  <channel>
    <title>Bitcoin Bastion Feed</title>
    <item>
      <title>ETF inflows rise</title>
      <link>https://example.com/etf</link>
      <author>Desk</author>
      <description>Bitcoin ETF demand is accelerating.</description>
      <pubDate>Tue, 14 Apr 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Mempool cools down</title>
      <link>https://example.com/fees</link>
      <description>Fee pressure declined during Asia session.</description>
    </item>
  </channel>
</rss>
"""


def test_rss_client_contract_normalizes_required_fields() -> None:
    client = RSSClient()
    client._fetch_raw = lambda _: RSS_XML  # type: ignore[method-assign]

    items = client.fetch("https://feed.example.com/rss")

    assert len(items) == 2
    first = items[0]
    assert first.title == "ETF inflows rise"
    assert first.url == "https://example.com/etf"
    assert first.author == "Desk"
    assert "Bitcoin ETF" in first.content
    assert first.published_at is not None
    assert first.published_at.tzinfo == UTC

    second = items[1]
    assert second.title == "Mempool cools down"
    assert second.url == "https://example.com/fees"
    assert second.author == ""
    assert second.published_at is not None
    assert second.published_at.tzinfo == UTC
