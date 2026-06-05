"""final release candidate schema runtime parity

Revision ID: 20260605_0052
Revises: 20260605_0051
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa

revision = "20260605_0052"
down_revision = "20260605_0051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("btc_candles", sa.Column("price_source_mode", sa.String(length=32), nullable=False, server_default="median_multi_provider"))
    op.add_column("btc_candles", sa.Column("provider_disagreement_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("btc_candles", sa.Column("aggregation_method", sa.String(length=32), nullable=False, server_default="hierarchical_v1"))
    op.add_column("btc_candles", sa.Column("is_degraded", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("btc_candles", sa.Column("market_regime", sa.String(length=16), nullable=False, server_default="normal"))
    op.add_column("btc_candles", sa.Column("volatility_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("btc_candles", sa.Column("evidence_packet_id", sa.String(length=64), nullable=False, server_default=""))
    op.create_index("ix_btc_candles_open_time", "btc_candles", ["open_time"])
    op.create_index("ix_btc_candles_close_time", "btc_candles", ["close_time"])
    op.create_index("ix_btc_candles_timeframe", "btc_candles", ["timeframe"])

    with op.batch_alter_table("btc_price_points") as batch_op:
        batch_op.alter_column(
            "aggregation_round_id",
            existing_type=sa.String(length=64),
            nullable=False,
            server_default="",
        )
    op.create_index("ix_btc_price_points_aggregation_round_id", "btc_price_points", ["aggregation_round_id"])
    op.create_index("ix_btc_price_points_raw_payload_hash", "btc_price_points", ["raw_payload_hash"])

    with op.batch_alter_table("news_articles") as batch_op:
        batch_op.add_column(sa.Column("uuid", sa.String(length=36), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("external_id", sa.String(length=255), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("normalized_title", sa.String(length=500), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("canonical_url", sa.String(length=2048), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("url_hash", sa.String(length=64), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("canonical_url_hash", sa.String(length=64), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("title_hash", sa.String(length=64), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("content_text", sa.Text(), nullable=False, server_default=""))
        batch_op.add_column(sa.Column("article_type", sa.String(length=64), nullable=False, server_default="NEWS"))
        batch_op.add_column(sa.Column("category", sa.String(length=80), nullable=False, server_default="general"))
        batch_op.add_column(sa.Column("sentiment_label", sa.String(length=32), nullable=False, server_default="UNKNOWN"))
        batch_op.add_column(sa.Column("market_impact_score", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.alter_column("metadata_json", existing_type=sa.Text(), type_=sa.JSON(), nullable=False)
    op.execute("UPDATE news_articles SET uuid = 'legacy-article-' || id WHERE uuid = ''")
    op.execute("UPDATE news_articles SET normalized_title = lower(title) WHERE normalized_title = ''")
    op.execute("UPDATE news_articles SET canonical_url = url WHERE canonical_url = ''")
    op.execute("UPDATE news_articles SET url_hash = 'legacy-url-' || id WHERE url_hash = ''")
    op.execute("UPDATE news_articles SET canonical_url_hash = 'legacy-canonical-url-' || id WHERE canonical_url_hash = ''")
    op.execute("UPDATE news_articles SET title_hash = 'legacy-title-' || id WHERE title_hash = ''")
    op.execute("UPDATE news_articles SET content_text = content_clean WHERE content_text = ''")
    op.create_index("ix_news_articles_source_id", "news_articles", ["source_id"])
    op.create_index("ix_news_articles_published_at", "news_articles", ["published_at"])
    op.create_index("ix_news_articles_btc_relevance_score", "news_articles", ["btc_relevance_score"])
    op.create_index("ix_news_articles_canonical_url_hash", "news_articles", ["canonical_url_hash"])
    op.create_index("ix_news_articles_title_hash", "news_articles", ["title_hash"])
    op.create_index("ix_news_articles_is_duplicate", "news_articles", ["is_duplicate"])
    op.create_index("ix_news_articles_url_hash", "news_articles", ["url_hash"], unique=True)
    with op.batch_alter_table("news_articles") as batch_op:
        batch_op.create_foreign_key(
            "fk_news_articles_cluster_id_news_article_clusters",
            "news_article_clusters",
            ["cluster_id"],
            ["id"],
        )

    op.create_index("ix_news_events_first_seen_at", "news_events", ["first_seen_at"])
    op.create_index("ix_news_events_btc_relevance_score", "news_events", ["btc_relevance_score"])
    with op.batch_alter_table("news_events") as batch_op:
        batch_op.create_foreign_key(
            "fk_news_events_first_source_id_news_sources",
            "news_sources",
            ["first_source_id"],
            ["id"],
        )

    op.add_column("news_sources", sa.Column("uuid", sa.String(length=36), nullable=False, server_default=""))
    op.add_column("news_sources", sa.Column("slug", sa.String(length=120), nullable=True))
    op.add_column("news_sources", sa.Column("tier", sa.String(length=80), nullable=False, server_default="market_media"))
    op.add_column("news_sources", sa.Column("supports_etag", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("news_sources", sa.Column("supports_last_modified", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("news_sources", sa.Column("notes", sa.String(length=1000), nullable=False, server_default=""))
    op.add_column("news_sources", sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("news_sources", sa.Column("last_success_at", sa.DateTime(), nullable=True))
    op.add_column("news_sources", sa.Column("last_failure_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE news_sources SET uuid = 'legacy-source-' || id WHERE uuid = ''")
    op.create_index("ix_news_sources_slug", "news_sources", ["slug"], unique=True)
    op.create_index("ix_news_sources_category", "news_sources", ["category"])
    op.create_index("ix_news_sources_tier", "news_sources", ["tier"])
    op.create_index("ix_news_sources_is_active", "news_sources", ["is_active"])

    op.add_column("source_reputation_profiles", sa.Column("duplication_rate", sa.Float(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("false_positive_rate", sa.Float(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("first_mover_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("timeliness_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("market_relevance_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("security_relevance_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("macro_relevance_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("bitcoin_native_score", sa.Float(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("total_articles_seen", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("total_events_created", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("source_reputation_profiles", sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"))
    op.add_column("source_reputation_profiles", sa.Column("notes", sa.String(length=1000), nullable=False, server_default=""))
    op.add_column("source_reputation_profiles", sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"))
    op.add_column("source_reputation_profiles", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()))
    op.create_index("ix_source_reputation_profiles_reliability_score", "source_reputation_profiles", ["reliability_score"])
    op.create_index("ix_source_reputation_profiles_signal_quality_score", "source_reputation_profiles", ["signal_quality_score"])

    op.create_index("ix_candle_build_runs_window_start", "candle_build_runs", ["window_start"])
    op.create_index("ix_candle_build_runs_window_end", "candle_build_runs", ["window_end"])

    op.create_index("ix_intelligence_timeline_events_event_time", "intelligence_timeline_events", ["event_time"])
    op.create_index("ix_intelligence_timeline_events_event_type", "intelligence_timeline_events", ["event_type"])
    op.create_index("ix_intelligence_timeline_events_related_article_id", "intelligence_timeline_events", ["related_article_id"])
    op.create_index("ix_intelligence_timeline_events_related_event_id", "intelligence_timeline_events", ["related_event_id"])
    op.create_index("ix_intelligence_timeline_events_related_signal_id", "intelligence_timeline_events", ["related_signal_id"])
    op.create_index("ix_intelligence_timeline_events_related_candle_id", "intelligence_timeline_events", ["related_candle_id"])
    op.create_index("ix_intelligence_timeline_events_related_provider_id", "intelligence_timeline_events", ["related_provider_id"])


def downgrade() -> None:
    for index_name in [
        "ix_intelligence_timeline_events_related_provider_id",
        "ix_intelligence_timeline_events_related_candle_id",
        "ix_intelligence_timeline_events_related_signal_id",
        "ix_intelligence_timeline_events_related_event_id",
        "ix_intelligence_timeline_events_related_article_id",
        "ix_intelligence_timeline_events_event_type",
        "ix_intelligence_timeline_events_event_time",
    ]:
        op.drop_index(index_name, table_name="intelligence_timeline_events")
    op.drop_index("ix_candle_build_runs_window_end", table_name="candle_build_runs")
    op.drop_index("ix_candle_build_runs_window_start", table_name="candle_build_runs")
    op.drop_index("ix_source_reputation_profiles_signal_quality_score", table_name="source_reputation_profiles")
    op.drop_index("ix_source_reputation_profiles_reliability_score", table_name="source_reputation_profiles")
    with op.batch_alter_table("source_reputation_profiles") as batch_op:
        for column_name in [
            "created_at",
            "metadata_json",
            "notes",
            "provider_confidence",
            "total_events_created",
            "total_articles_seen",
            "bitcoin_native_score",
            "macro_relevance_score",
            "security_relevance_score",
            "market_relevance_score",
            "timeliness_score",
            "first_mover_score",
            "false_positive_rate",
            "duplication_rate",
        ]:
            batch_op.drop_column(column_name)

    for index_name in ["ix_news_sources_is_active", "ix_news_sources_tier", "ix_news_sources_category", "ix_news_sources_slug"]:
        op.drop_index(index_name, table_name="news_sources")
    with op.batch_alter_table("news_sources") as batch_op:
        for column_name in [
            "last_failure_at",
            "last_success_at",
            "metadata_json",
            "notes",
            "supports_last_modified",
            "supports_etag",
            "tier",
            "slug",
            "uuid",
        ]:
            batch_op.drop_column(column_name)

    with op.batch_alter_table("news_events") as batch_op:
        batch_op.drop_constraint("fk_news_events_first_source_id_news_sources", type_="foreignkey")
    op.drop_index("ix_news_events_btc_relevance_score", table_name="news_events")
    op.drop_index("ix_news_events_first_seen_at", table_name="news_events")

    with op.batch_alter_table("news_articles") as batch_op:
        batch_op.drop_constraint("fk_news_articles_cluster_id_news_article_clusters", type_="foreignkey")
    for index_name in [
        "ix_news_articles_url_hash",
        "ix_news_articles_is_duplicate",
        "ix_news_articles_title_hash",
        "ix_news_articles_canonical_url_hash",
        "ix_news_articles_btc_relevance_score",
        "ix_news_articles_published_at",
        "ix_news_articles_source_id",
    ]:
        op.drop_index(index_name, table_name="news_articles")
    with op.batch_alter_table("news_articles") as batch_op:
        batch_op.alter_column("metadata_json", existing_type=sa.JSON(), type_=sa.Text(), nullable=False)
        for column_name in [
            "is_duplicate",
            "market_impact_score",
            "sentiment_label",
            "article_type",
            "content_text",
            "title_hash",
            "canonical_url_hash",
            "url_hash",
            "canonical_url",
            "normalized_title",
            "external_id",
            "uuid",
        ]:
            batch_op.drop_column(column_name)

    op.drop_index("ix_btc_price_points_raw_payload_hash", table_name="btc_price_points")
    op.drop_index("ix_btc_price_points_aggregation_round_id", table_name="btc_price_points")
    with op.batch_alter_table("btc_price_points") as batch_op:
        batch_op.alter_column(
            "aggregation_round_id",
            existing_type=sa.String(length=64),
            nullable=False,
            server_default="",
        )
    op.drop_index("ix_btc_candles_timeframe", table_name="btc_candles")
    op.drop_index("ix_btc_candles_close_time", table_name="btc_candles")
    op.drop_index("ix_btc_candles_open_time", table_name="btc_candles")
    with op.batch_alter_table("btc_candles") as batch_op:
        for column_name in [
            "evidence_packet_id",
            "volatility_score",
            "market_regime",
            "is_degraded",
            "aggregation_method",
            "provider_disagreement_score",
            "price_source_mode",
        ]:
            batch_op.drop_column(column_name)
