"""historical similarity foundation models

Revision ID: 20260527_0040
Revises: 20260527_0039
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0040"
down_revision = "20260527_0039"
branch_labels = None
depends_on = None

PATTERNS = [
    ("ETF_INFLOW_SHOCK", "ETF inflow shock", "institutional", "Spot Bitcoin ETF inflow shock."),
    ("ETF_OUTFLOW_SHOCK", "ETF outflow shock", "institutional", "Spot Bitcoin ETF outflow shock."),
    ("SEC_ENFORCEMENT", "SEC enforcement", "regulatory", "SEC enforcement, litigation, or settlement pressure."),
    ("REGULATORY_APPROVAL", "Regulatory approval", "regulatory", "Constructive regulatory approval event."),
    ("FED_LIQUIDITY_EASING", "Fed liquidity easing", "macro", "Dovish liquidity or easing regime."),
    ("FED_LIQUIDITY_TIGHTENING", "Fed liquidity tightening", "macro", "Hawkish liquidity or tightening regime."),
    ("EXCHANGE_HACK", "Exchange hack", "security", "Exchange compromise or loss event."),
    ("CUSTODY_FAILURE", "Custody failure", "security", "Custody, key-management, or custodian failure."),
    ("MINER_CAPITULATION", "Miner capitulation", "mining", "Miner distress or forced selling pattern."),
    ("MINER_ACCUMULATION", "Miner accumulation", "mining", "Miner accumulation or reduced miner selling."),
    ("BITCOIN_CORE_RELEASE", "Bitcoin Core release", "bitcoin_core", "Bitcoin Core release or protocol maintenance event."),
    ("LIGHTNING_ADOPTION", "Lightning adoption", "lightning", "Lightning Network adoption or infrastructure pattern."),
    ("TREASURY_ADOPTION", "Treasury adoption", "treasury", "Corporate or treasury Bitcoin adoption."),
    ("INSTITUTIONAL_ACCUMULATION", "Institutional accumulation", "institutional", "Institutional Bitcoin accumulation pattern."),
    ("LARGE_LIQUIDATION_CASCADE", "Large liquidation cascade", "market_structure", "Large liquidation cascade or forced deleveraging."),
    ("MACRO_RISK_ON", "Macro risk-on", "macro", "Risk-on macro backdrop."),
    ("MACRO_RISK_OFF", "Macro risk-off", "macro", "Risk-off macro backdrop."),
    ("SECURITY_VULNERABILITY", "Security vulnerability", "security", "Security vulnerability or exploit disclosure."),
]


def upgrade() -> None:
    op.create_table(
        "historical_patterns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("description", sa.String(length=600), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_historical_patterns_slug", "historical_patterns", ["slug"], unique=True)
    op.create_index("ix_historical_patterns_category", "historical_patterns", ["category"])

    op.create_table(
        "historical_similarity_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("similar_event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pattern_match_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_match_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("market_context_match_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("time_distance_days", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reaction_similarity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_historical_similarity_matches_event_id", "historical_similarity_matches", ["event_id"])
    op.create_index("ix_historical_similarity_matches_similar_event_id", "historical_similarity_matches", ["similar_event_id"])
    op.create_index("ix_historical_similarity_matches_similarity_score", "historical_similarity_matches", ["similarity_score"])

    op.create_table(
        "historical_reaction_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("reaction_15m_pct", sa.Float(), nullable=True),
        sa.Column("reaction_1h_pct", sa.Float(), nullable=True),
        sa.Column("reaction_4h_pct", sa.Float(), nullable=True),
        sa.Column("reaction_24h_pct", sa.Float(), nullable=True),
        sa.Column("max_positive_move_pct", sa.Float(), nullable=True),
        sa.Column("max_negative_move_pct", sa.Float(), nullable=True),
        sa.Column("volatility_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_historical_reaction_profiles_event_id", "historical_reaction_profiles", ["event_id"])

    rows = [
        {"slug": slug, "name": name, "category": category, "description": description}
        for slug, name, category, description in PATTERNS
    ]
    op.bulk_insert(sa.table("historical_patterns", *[sa.column(key) for key in rows[0].keys()]), rows)


def downgrade() -> None:
    op.drop_index("ix_historical_reaction_profiles_event_id", table_name="historical_reaction_profiles")
    op.drop_table("historical_reaction_profiles")
    op.drop_index("ix_historical_similarity_matches_similarity_score", table_name="historical_similarity_matches")
    op.drop_index("ix_historical_similarity_matches_similar_event_id", table_name="historical_similarity_matches")
    op.drop_index("ix_historical_similarity_matches_event_id", table_name="historical_similarity_matches")
    op.drop_table("historical_similarity_matches")
    op.drop_index("ix_historical_patterns_category", table_name="historical_patterns")
    op.drop_index("ix_historical_patterns_slug", table_name="historical_patterns")
    op.drop_table("historical_patterns")
