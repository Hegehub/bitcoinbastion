"""production historical similarity records and pattern library

Revision ID: 20260527_0036
Revises: 20260527_0035
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0036"
down_revision = "20260527_0035"
branch_labels = None
depends_on = None

PATTERNS = [
    ("ETF_INFLOW_SHOCK", "ETF inflow shock", "Spot Bitcoin ETF inflow surprise or acceleration.", "POSITIVE", ["15m", "1h", "4h"], "Strong"),
    ("ETF_OUTFLOW_SHOCK", "ETF outflow shock", "Spot Bitcoin ETF outflow surprise or acceleration.", "NEGATIVE", ["15m", "1h", "4h"], "Strong"),
    ("SEC_ENFORCEMENT", "SEC enforcement", "SEC enforcement action or legal pressure touching Bitcoin market structure.", "NEGATIVE", ["1h", "4h", "24h"], "Moderate"),
    ("REGULATORY_APPROVAL", "Regulatory approval", "Approval or constructive regulatory development.", "POSITIVE", ["1h", "4h", "24h"], "Moderate"),
    ("REGULATORY_DELAY", "Regulatory delay", "Delayed approval or unresolved regulatory process.", "NEGATIVE", ["1h", "4h", "24h"], "Moderate"),
    ("FED_LIQUIDITY_EASING", "Fed liquidity easing", "Liquidity easing or dovish macro signal.", "POSITIVE", ["1h", "4h", "24h"], "Moderate"),
    ("FED_TIGHTENING", "Fed tightening", "Tightening or hawkish macro signal.", "NEGATIVE", ["1h", "4h", "24h"], "Moderate"),
    ("EXCHANGE_HACK", "Exchange hack", "Exchange compromise or platform-security shock.", "NEGATIVE", ["15m", "1h", "4h"], "Strong"),
    ("CUSTODY_FAILURE", "Custody failure", "Custodian failure, insolvency, or custody confidence shock.", "NEGATIVE", ["1h", "4h", "24h"], "Strong"),
    ("MINER_CAPITULATION", "Miner capitulation", "Miner distress, forced selling, or capitulation narrative.", "NEGATIVE", ["4h", "24h"], "Moderate"),
    ("MINER_ACCUMULATION", "Miner accumulation", "Miner accumulation or reduced miner selling pressure.", "POSITIVE", ["4h", "24h"], "Moderate"),
    ("LARGE_LIQUIDATION_CASCADE", "Large liquidation cascade", "High-leverage liquidation cascade or derivatives stress.", "NEGATIVE", ["15m", "1h"], "Strong"),
    ("BITCOIN_CORE_RELEASE", "Bitcoin Core release", "Bitcoin Core software release or protocol maintenance event.", "NEUTRAL", ["4h", "24h"], "Weak"),
    ("LIGHTNING_ADOPTION", "Lightning adoption", "Lightning Network adoption or infrastructure news.", "POSITIVE", ["4h", "24h"], "Moderate"),
    ("TREASURY_ADOPTION", "Treasury adoption", "Corporate or sovereign Bitcoin treasury adoption.", "POSITIVE", ["1h", "4h", "24h"], "Strong"),
    ("INSTITUTIONAL_ACCUMULATION", "Institutional accumulation", "Institutional Bitcoin accumulation, custody, or allocation narrative.", "POSITIVE", ["1h", "4h", "24h"], "Strong"),
    ("MACRO_RISK_ON", "Macro risk-on", "Broad risk-on macro conditions supportive for BTC.", "POSITIVE", ["1h", "4h", "24h"], "Moderate"),
    ("MACRO_RISK_OFF", "Macro risk-off", "Broad risk-off macro conditions pressuring BTC.", "NEGATIVE", ["1h", "4h", "24h"], "Moderate"),
    ("SECURITY_INCIDENT", "Security incident", "Security incident, exploit, malware, or ecosystem risk disclosure.", "NEGATIVE", ["15m", "1h", "4h"], "Strong"),
    ("VOLATILITY_EXPANSION", "Volatility expansion", "Volatility breakout or market-structure expansion narrative.", "NEUTRAL", ["15m", "1h", "4h"], "Moderate"),
]


def upgrade() -> None:
    op.create_table(
        "market_pattern_library",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_code", sa.String(length=64), nullable=False),
        sa.Column("display_name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("description", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("expected_sentiment", sa.String(length=32), nullable=False, server_default="UNKNOWN"),
        sa.Column("expected_time_windows", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("default_confidence_band", sa.String(length=32), nullable=False, server_default="Moderate"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_market_pattern_library_pattern_code", "market_pattern_library", ["pattern_code"], unique=True)
    op.create_index("ix_market_pattern_library_created_at", "market_pattern_library", ["created_at"])
    market_pattern_library = sa.table(
        "market_pattern_library",
        sa.column("pattern_code", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.String),
        sa.column("expected_sentiment", sa.String),
        sa.column("expected_time_windows", sa.JSON),
        sa.column("default_confidence_band", sa.String),
    )
    op.bulk_insert(
        market_pattern_library,
        [
            {
                "pattern_code": code,
                "display_name": name,
                "description": description,
                "expected_sentiment": sentiment,
                "expected_time_windows": windows,
                "default_confidence_band": band,
            }
            for code, name, description, sentiment, windows, band in PATTERNS
        ],
    )

    op.create_table(
        "historical_similarity_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference_event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("reference_article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("candidate_event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("candidate_article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("event_type_match", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_match", sa.Float(), nullable=False, server_default="0"),
        sa.Column("impact_match", sa.Float(), nullable=False, server_default="0"),
        sa.Column("narrative_match", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reaction_match", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reaction_15m_pct", sa.Float(), nullable=True),
        sa.Column("reaction_1h_pct", sa.Float(), nullable=True),
        sa.Column("reaction_4h_pct", sa.Float(), nullable=True),
        sa.Column("reaction_24h_pct", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_historical_similarity_records_reference_event_id", "historical_similarity_records", ["reference_event_id"])
    op.create_index("ix_historical_similarity_records_candidate_event_id", "historical_similarity_records", ["candidate_event_id"])
    op.create_index("ix_historical_similarity_records_reference_article_id", "historical_similarity_records", ["reference_article_id"])
    op.create_index("ix_historical_similarity_records_candidate_article_id", "historical_similarity_records", ["candidate_article_id"])
    op.create_index("ix_historical_similarity_records_similarity_score", "historical_similarity_records", ["similarity_score"])


def downgrade() -> None:
    op.drop_index("ix_historical_similarity_records_similarity_score", table_name="historical_similarity_records")
    op.drop_index("ix_historical_similarity_records_candidate_article_id", table_name="historical_similarity_records")
    op.drop_index("ix_historical_similarity_records_reference_article_id", table_name="historical_similarity_records")
    op.drop_index("ix_historical_similarity_records_candidate_event_id", table_name="historical_similarity_records")
    op.drop_index("ix_historical_similarity_records_reference_event_id", table_name="historical_similarity_records")
    op.drop_table("historical_similarity_records")
    op.drop_index("ix_market_pattern_library_created_at", table_name="market_pattern_library")
    op.drop_index("ix_market_pattern_library_pattern_code", table_name="market_pattern_library")
    op.drop_table("market_pattern_library")
