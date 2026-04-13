from datetime import UTC, datetime

from app.db.models.news import NewsArticle, NewsSource
from app.services.scoring.news_scoring import NewsScoringService


def test_keyword_scoring_increases_relevance() -> None:
    source = NewsSource(name="Test", rss_url="http://example.com/rss", credibility_weight=0.9)
    article = NewsArticle(
        source_id=1,
        title="Bitcoin ETF sees surge",
        url="https://example.com/a",
        content_hash="x",
        published_at=datetime.now(UTC),
        content_clean="bitcoin etf adoption surge",
    )

    result = NewsScoringService().score(article, source)
    assert result.relevance > 0.3
    assert result.urgency >= 0.0
    assert result.confidence > 0.5
