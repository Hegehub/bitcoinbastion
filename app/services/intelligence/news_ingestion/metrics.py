from prometheus_client import Counter, Histogram

NEWS_FETCH_TOTAL = Counter("news_fetch_total", "Total news fetch attempts", ["source"])
NEWS_FETCH_FAILURES_TOTAL = Counter("news_fetch_failures_total", "Total news fetch failures", ["source"])
NEWS_FETCH_DURATION_SECONDS = Histogram("news_fetch_duration_seconds", "News fetch duration seconds", ["source"])
NEWS_ARTICLES_INGESTED_TOTAL = Counter("news_articles_ingested_total", "News articles ingested", ["source"])
NEWS_DUPLICATE_CANDIDATES_TOTAL = Counter("news_duplicate_candidates_total", "Duplicate candidates", ["source"])
NEWS_PAYLOAD_SIZE_BYTES = Histogram("news_payload_size_bytes", "Payload size bytes", ["source"])
NEWS_HTTP_304_TOTAL = Counter("news_http_304_total", "HTTP 304 responses", ["source"])
