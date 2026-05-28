from prometheus_client import Counter, Gauge

NEWS_DEDUP_EXACT_TOTAL = Counter("news_dedup_exact_total", "Exact duplicates detected")
NEWS_DEDUP_NEAR_TOTAL = Counter("news_dedup_near_total", "Near duplicates detected")
NEWS_CLUSTERS_CREATED_TOTAL = Counter("news_clusters_created_total", "Clusters created")
NEWS_CLUSTER_REASSIGNMENTS_TOTAL = Counter("news_cluster_reassignments_total", "Cluster reassignments")
NEWS_SIMILARITY_CALCULATIONS_TOTAL = Counter("news_similarity_calculations_total", "Similarity calculations")
NEWS_DUPLICATE_RATE = Gauge("news_duplicate_rate", "Duplicate article rate")
