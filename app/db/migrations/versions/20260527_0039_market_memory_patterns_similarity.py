"""market memory patterns and event similarities

Revision ID: 20260527_0039
Revises: 20260527_0038
"""

import json

from alembic import op
import sqlalchemy as sa

revision = "20260527_0039"
down_revision = "20260527_0038"
branch_labels = None
depends_on = None

PATTERNS = [
    (
        "ETF_INFLOW_SHOCK",
        "ETF inflow shock",
        "institutional",
        "Spot Bitcoin ETF inflow acceleration.",
        "POSITIVE",
        "UP",
        "1h",
    ),
    (
        "ETF_OUTFLOW_SHOCK",
        "ETF outflow shock",
        "institutional",
        "Spot Bitcoin ETF outflow acceleration.",
        "NEGATIVE",
        "DOWN",
        "1h",
    ),
    (
        "FED_LIQUIDITY_EASING",
        "Fed liquidity easing",
        "macro",
        "Dovish liquidity or funding conditions.",
        "POSITIVE",
        "UP",
        "4h",
    ),
    (
        "FED_LIQUIDITY_TIGHTENING",
        "Fed liquidity tightening",
        "macro",
        "Hawkish liquidity or funding conditions.",
        "NEGATIVE",
        "DOWN",
        "4h",
    ),
    (
        "SEC_APPROVAL",
        "SEC approval",
        "regulatory",
        "Constructive SEC or ETF approval event.",
        "POSITIVE",
        "UP",
        "1h",
    ),
    (
        "SEC_ENFORCEMENT",
        "SEC enforcement",
        "regulatory",
        "SEC enforcement or litigation pressure.",
        "NEGATIVE",
        "DOWN",
        "1h",
    ),
    (
        "BITCOIN_CORE_RELEASE",
        "Bitcoin Core release",
        "protocol",
        "Bitcoin Core release or maintenance milestone.",
        "NEUTRAL",
        "UNKNOWN",
        "24h",
    ),
    (
        "LIGHTNING_ADOPTION",
        "Lightning adoption",
        "protocol",
        "Lightning Network adoption or infrastructure growth.",
        "POSITIVE",
        "UP",
        "24h",
    ),
    (
        "MINER_CAPITULATION",
        "Miner capitulation",
        "mining",
        "Miner distress or forced selling narrative.",
        "NEGATIVE",
        "DOWN",
        "4h",
    ),
    (
        "MINER_ACCUMULATION",
        "Miner accumulation",
        "mining",
        "Reduced miner selling or miner accumulation.",
        "POSITIVE",
        "UP",
        "24h",
    ),
    (
        "EXCHANGE_HACK",
        "Exchange hack",
        "security",
        "Exchange compromise or exploit.",
        "NEGATIVE",
        "DOWN",
        "15m",
    ),
    (
        "CUSTODY_FAILURE",
        "Custody failure",
        "security",
        "Custodian failure, insolvency, or key-management risk.",
        "NEGATIVE",
        "DOWN",
        "1h",
    ),
    (
        "SECURITY_EXPLOIT",
        "Security exploit",
        "security",
        "Protocol, wallet, bridge, or ecosystem exploit.",
        "NEGATIVE",
        "DOWN",
        "15m",
    ),
    (
        "INSTITUTIONAL_ADOPTION",
        "Institutional adoption",
        "institutional",
        "Institutional allocation or adoption news.",
        "POSITIVE",
        "UP",
        "4h",
    ),
    (
        "TREASURY_ADOPTION",
        "Treasury adoption",
        "institutional",
        "Corporate or sovereign treasury adoption.",
        "POSITIVE",
        "UP",
        "4h",
    ),
    (
        "MACRO_RISK_ON",
        "Macro risk-on",
        "macro",
        "Risk-on macro regime supportive for BTC.",
        "POSITIVE",
        "UP",
        "4h",
    ),
    (
        "MACRO_RISK_OFF",
        "Macro risk-off",
        "macro",
        "Risk-off macro regime pressuring BTC.",
        "NEGATIVE",
        "DOWN",
        "4h",
    ),
    (
        "LIQUIDATION_CASCADE_LONG",
        "Long liquidation cascade",
        "market_structure",
        "Long liquidation cascade or forced deleveraging.",
        "NEGATIVE",
        "DOWN",
        "15m",
    ),
    (
        "LIQUIDATION_CASCADE_SHORT",
        "Short liquidation cascade",
        "market_structure",
        "Short squeeze liquidation cascade.",
        "POSITIVE",
        "UP",
        "15m",
    ),
    (
        "HALVING_NARRATIVE",
        "Halving narrative",
        "supply",
        "Halving-cycle supply issuance narrative.",
        "POSITIVE",
        "UP",
        "24h",
    ),
    (
        "SELF_CUSTODY_WAVE",
        "Self-custody wave",
        "sovereignty",
        "Self-custody adoption or withdrawal wave.",
        "POSITIVE",
        "UP",
        "24h",
    ),
    (
        "SOVEREIGNTY_ADOPTION",
        "Sovereignty adoption",
        "sovereignty",
        "Nation-state, human-rights, or sovereignty adoption narrative.",
        "POSITIVE",
        "UP",
        "24h",
    ),
]


def upgrade() -> None:
    op.create_table(
        "market_patterns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("description", sa.String(length=600), nullable=False, server_default=""),
        sa.Column(
            "expected_sentiment", sa.String(length=32), nullable=False, server_default="UNKNOWN"
        ),
        sa.Column(
            "expected_direction", sa.String(length=16), nullable=False, server_default="UNKNOWN"
        ),
        sa.Column(
            "typical_impact_window", sa.String(length=32), nullable=False, server_default="1h"
        ),
        sa.Column(
            "historical_reaction_profile_json", sa.JSON(), nullable=False, server_default="{}"
        ),
        sa.Column("confidence_rules_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_market_patterns_slug", "market_patterns", ["slug"], unique=True)
    op.create_index("ix_market_patterns_category", "market_patterns", ["category"])
    op.create_index("ix_market_patterns_is_active", "market_patterns", ["is_active"])

    op.create_table(
        "event_pattern_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id"), nullable=False),
        sa.Column("classification_confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("reasons_json", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_event_pattern_matches_event_id", "event_pattern_matches", ["event_id"])
    op.create_index("ix_event_pattern_matches_pattern_id", "event_pattern_matches", ["pattern_id"])
    op.create_index(
        "ix_event_pattern_matches_classification_confidence",
        "event_pattern_matches",
        ["classification_confidence"],
    )

    op.create_table(
        "historical_event_similarities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False),
        sa.Column(
            "similar_event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=False
        ),
        sa.Column("similarity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("pattern_match", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sentiment_match", sa.Float(), nullable=False, server_default="0"),
        sa.Column("impact_match", sa.Float(), nullable=False, server_default="0"),
        sa.Column("volatility_match", sa.Float(), nullable=False, server_default="0"),
        sa.Column("explanation_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_historical_event_similarities_event_id", "historical_event_similarities", ["event_id"]
    )
    op.create_index(
        "ix_historical_event_similarities_similar_event_id",
        "historical_event_similarities",
        ["similar_event_id"],
    )
    op.create_index(
        "ix_historical_event_similarities_similarity_score",
        "historical_event_similarities",
        ["similarity_score"],
    )

    op.create_table(
        "pattern_reaction_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_id", sa.Integer(), sa.ForeignKey("market_patterns.id"), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("median_change_15m", sa.Float(), nullable=True),
        sa.Column("median_change_1h", sa.Float(), nullable=True),
        sa.Column("median_change_4h", sa.Float(), nullable=True),
        sa.Column("median_change_24h", sa.Float(), nullable=True),
        sa.Column("average_change_15m", sa.Float(), nullable=True),
        sa.Column("average_change_1h", sa.Float(), nullable=True),
        sa.Column("average_change_4h", sa.Float(), nullable=True),
        sa.Column("average_change_24h", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_pattern_reaction_profiles_pattern_id", "pattern_reaction_profiles", ["pattern_id"]
    )

    rows = [
        {
            "slug": slug,
            "name": name,
            "category": category,
            "description": description,
            "expected_sentiment": sentiment,
            "expected_direction": direction,
            "typical_impact_window": window,
            "historical_reaction_profile_json": json.dumps({}),
            "confidence_rules_json": json.dumps(
                {"small_sample_penalty": True, "provider_disagreement_penalty": True}
            ),
            "is_active": True,
        }
        for slug, name, category, description, sentiment, direction, window in PATTERNS
    ]
    op.bulk_insert(sa.table("market_patterns", *[sa.column(key) for key in rows[0].keys()]), rows)


def downgrade() -> None:
    op.drop_index("ix_pattern_reaction_profiles_pattern_id", table_name="pattern_reaction_profiles")
    op.drop_table("pattern_reaction_profiles")
    op.drop_index(
        "ix_historical_event_similarities_similarity_score",
        table_name="historical_event_similarities",
    )
    op.drop_index(
        "ix_historical_event_similarities_similar_event_id",
        table_name="historical_event_similarities",
    )
    op.drop_index(
        "ix_historical_event_similarities_event_id", table_name="historical_event_similarities"
    )
    op.drop_table("historical_event_similarities")
    op.drop_index(
        "ix_event_pattern_matches_classification_confidence", table_name="event_pattern_matches"
    )
    op.drop_index("ix_event_pattern_matches_pattern_id", table_name="event_pattern_matches")
    op.drop_index("ix_event_pattern_matches_event_id", table_name="event_pattern_matches")
    op.drop_table("event_pattern_matches")
    op.drop_index("ix_market_patterns_is_active", table_name="market_patterns")
    op.drop_index("ix_market_patterns_category", table_name="market_patterns")
    op.drop_index("ix_market_patterns_slug", table_name="market_patterns")
    op.drop_table("market_patterns")
