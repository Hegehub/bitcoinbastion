from prometheus_client import Counter, Gauge

NEWS_SOURCES_TOTAL = Gauge("news_sources_total", "Total configured news sources")
NEWS_SOURCES_ACTIVE_TOTAL = Gauge("news_sources_active_total", "Active configured news sources")
NEWS_SOURCES_BY_CATEGORY = Counter("news_sources_by_category", "News sources seen by category", ["category"])
NEWS_SOURCES_BY_TIER = Counter("news_sources_by_tier", "News sources seen by tier", ["tier"])
