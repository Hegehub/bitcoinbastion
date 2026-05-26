# Intelligence Architecture

News ingestion runs via Celery tasks `news.fetch_source` and `news.fetch_all_sources` with retry/backoff and structured metrics.
