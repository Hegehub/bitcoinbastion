"""expand historical similarity results for production engine

Revision ID: 20260527_0037
Revises: 20260527_0036
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0037"
down_revision = "20260527_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("historical_similarity_results") as batch_op:
        batch_op.add_column(sa.Column("reference_signal_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reference_article_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("reference_candle_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("matched_event_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("matched_signal_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("matched_article_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("pattern_type", sa.String(length=64), nullable=False, server_default="UNKNOWN"))
        batch_op.add_column(sa.Column("reaction_15m_pct", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("reaction_1h_pct", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("reaction_4h_pct", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("reaction_24h_pct", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("reaction_direction", sa.String(length=16), nullable=False, server_default="UNKNOWN"))
        batch_op.add_column(sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("limitations_json", sa.JSON(), nullable=False, server_default="{}"))
        batch_op.create_foreign_key(
            "fk_historical_similarity_results_reference_article_id_news_articles",
            "news_articles",
            ["reference_article_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_historical_similarity_results_reference_candle_id_btc_candles",
            "btc_candles",
            ["reference_candle_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_historical_similarity_results_matched_event_id_news_events",
            "news_events",
            ["matched_event_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_historical_similarity_results_matched_article_id_news_articles",
            "news_articles",
            ["matched_article_id"],
            ["id"],
        )
    op.create_index("ix_historical_similarity_results_reference_signal_id", "historical_similarity_results", ["reference_signal_id"])
    op.create_index("ix_historical_similarity_results_reference_article_id", "historical_similarity_results", ["reference_article_id"])
    op.create_index("ix_historical_similarity_results_reference_candle_id", "historical_similarity_results", ["reference_candle_id"])
    op.create_index("ix_historical_similarity_results_matched_event_id", "historical_similarity_results", ["matched_event_id"])
    op.create_index("ix_historical_similarity_results_matched_signal_id", "historical_similarity_results", ["matched_signal_id"])
    op.create_index("ix_historical_similarity_results_matched_article_id", "historical_similarity_results", ["matched_article_id"])
    op.create_index("ix_historical_similarity_results_pattern_type", "historical_similarity_results", ["pattern_type"])


def downgrade() -> None:
    op.drop_index("ix_historical_similarity_results_pattern_type", table_name="historical_similarity_results")
    op.drop_index("ix_historical_similarity_results_matched_article_id", table_name="historical_similarity_results")
    op.drop_index("ix_historical_similarity_results_matched_signal_id", table_name="historical_similarity_results")
    op.drop_index("ix_historical_similarity_results_matched_event_id", table_name="historical_similarity_results")
    op.drop_index("ix_historical_similarity_results_reference_candle_id", table_name="historical_similarity_results")
    op.drop_index("ix_historical_similarity_results_reference_article_id", table_name="historical_similarity_results")
    op.drop_index("ix_historical_similarity_results_reference_signal_id", table_name="historical_similarity_results")
    with op.batch_alter_table("historical_similarity_results") as batch_op:
        batch_op.drop_constraint(
            "fk_historical_similarity_results_matched_article_id_news_articles",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_historical_similarity_results_matched_event_id_news_events",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_historical_similarity_results_reference_candle_id_btc_candles",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_historical_similarity_results_reference_article_id_news_articles",
            type_="foreignkey",
        )
        batch_op.drop_column("limitations_json")
        batch_op.drop_column("confidence_score")
        batch_op.drop_column("reaction_direction")
        batch_op.drop_column("reaction_24h_pct")
        batch_op.drop_column("reaction_4h_pct")
        batch_op.drop_column("reaction_1h_pct")
        batch_op.drop_column("reaction_15m_pct")
        batch_op.drop_column("pattern_type")
        batch_op.drop_column("matched_article_id")
        batch_op.drop_column("matched_signal_id")
        batch_op.drop_column("matched_event_id")
        batch_op.drop_column("reference_candle_id")
        batch_op.drop_column("reference_article_id")
        batch_op.drop_column("reference_signal_id")
