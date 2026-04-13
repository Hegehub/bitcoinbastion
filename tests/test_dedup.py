from app.services.ingestion.news_ingestion import NewsIngestionService


def test_hash_dedup_is_deterministic() -> None:
    h1 = NewsIngestionService.content_hash("Hello Bitcoin", "https://x.com")
    h2 = NewsIngestionService.content_hash("Hello Bitcoin", "https://x.com")
    assert h1 == h2
