"""narrative heatmap engine

Revision ID: 20260527_0041
Revises: 20260527_0040
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0041"
down_revision = "20260527_0040"
branch_labels = None
depends_on = None

NARRATIVES = [
    ("etf", "ETF", "ETF inflows, outflows, approvals, issuers, and fund-flow narratives.", "institutional"),
    ("institutional-adoption", "Institutional Adoption", "Institutional Bitcoin adoption and allocation narratives.", "institutional"),
    ("treasury-adoption", "Treasury Adoption", "Corporate and treasury Bitcoin adoption narratives.", "treasury"),
    ("mining", "Mining", "Mining, hash rate, difficulty, and miner balance-sheet narratives.", "mining"),
    ("bitcoin-core", "Bitcoin Core", "Bitcoin Core releases, maintenance, and protocol software narratives.", "bitcoin_core"),
    ("lightning", "Lightning", "Lightning Network adoption, infrastructure, and liquidity narratives.", "lightning"),
    ("macro-liquidity", "Macro Liquidity", "Global liquidity and macro risk appetite narratives.", "macro"),
    ("fed", "Fed", "Federal Reserve policy, rates, and liquidity narratives.", "macro"),
    ("inflation", "Inflation", "Inflation, CPI, real-rate, and purchasing-power narratives.", "macro"),
    ("dollar-strength", "Dollar Strength", "USD strength, DXY, and currency pressure narratives.", "macro"),
    ("regulation", "Regulation", "Regulatory policy and jurisdictional treatment narratives.", "regulatory"),
    ("sec", "SEC", "SEC enforcement, approval, delay, and litigation narratives.", "regulatory"),
    ("self-custody", "Self Custody", "Self-custody, withdrawal, and key-sovereignty narratives.", "sovereignty"),
    ("sovereignty", "Sovereignty", "Bitcoin sovereignty, censorship resistance, and self-determination narratives.", "sovereignty"),
    ("exchange-risk", "Exchange Risk", "Exchange solvency, hacks, reserves, and counterparty-risk narratives.", "security"),
    ("security-incidents", "Security Incidents", "Security incidents, exploits, vulnerabilities, and custody failures.", "security"),
    ("liquidations", "Liquidations", "Liquidation cascades, leverage flushes, and forced-deleveraging narratives.", "market_structure"),
    ("market-structure", "Market Structure", "Liquidity, order-book, volatility, basis, and market-structure narratives.", "market_structure"),
]

KEYWORDS = {
    "etf": [("etf", 2.0), ("spot bitcoin etf", 3.0), ("inflow", 1.4), ("outflow", 1.4), ("blackrock", 1.2), ("fidelity", 1.2)],
    "institutional-adoption": [("institutional", 2.0), ("fund", 1.1), ("asset manager", 1.5), ("allocation", 1.4), ("wall street", 1.0)],
    "treasury-adoption": [("treasury", 2.0), ("corporate bitcoin", 2.2), ("balance sheet", 1.3), ("reserve asset", 1.4)],
    "mining": [("miner", 2.0), ("mining", 2.0), ("hash rate", 1.7), ("difficulty", 1.4), ("capitulation", 1.3)],
    "bitcoin-core": [("bitcoin core", 3.0), ("core release", 2.0), ("protocol", 1.0), ("node", 1.0)],
    "lightning": [("lightning", 2.5), ("ln", 1.0), ("channel", 1.0), ("payment", 0.8)],
    "macro-liquidity": [("liquidity", 2.0), ("risk-on", 1.4), ("risk off", 1.4), ("global liquidity", 2.5)],
    "fed": [("fed", 2.0), ("federal reserve", 2.0), ("rate cut", 1.5), ("rate hike", 1.5), ("powell", 1.2)],
    "inflation": [("inflation", 2.0), ("cpi", 1.5), ("ppi", 1.2), ("real yield", 1.3)],
    "dollar-strength": [("dollar", 1.8), ("dxy", 2.0), ("usd", 1.0), ("currency", 1.0)],
    "regulation": [("regulation", 2.0), ("regulatory", 2.0), ("law", 1.0), ("policy", 1.0), ("approval", 1.2)],
    "sec": [("sec", 2.5), ("securities and exchange commission", 2.5), ("enforcement", 1.3), ("lawsuit", 1.2)],
    "self-custody": [("self custody", 2.5), ("self-custody", 2.5), ("withdrawal", 1.2), ("private keys", 1.7)],
    "sovereignty": [("sovereignty", 2.0), ("censorship resistance", 2.0), ("permissionless", 1.4), ("freedom", 0.8)],
    "exchange-risk": [("exchange", 1.6), ("proof of reserves", 2.0), ("solvency", 1.8), ("withdrawals halted", 2.0)],
    "security-incidents": [("hack", 2.0), ("exploit", 2.0), ("vulnerability", 2.0), ("custody failure", 2.0), ("breach", 1.5)],
    "liquidations": [("liquidation", 2.5), ("cascade", 1.8), ("leverage", 1.2), ("forced selling", 1.4)],
    "market-structure": [("market structure", 2.5), ("liquidity", 1.2), ("order book", 1.5), ("volatility", 1.3), ("basis", 1.2)],
}


def upgrade() -> None:
    op.create_table(
        "market_narratives",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=96), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=600), nullable=False, server_default=""),
        sa.Column("category", sa.String(length=64), nullable=False, server_default="unknown"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_market_narratives_slug", "market_narratives", ["slug"], unique=True)
    op.create_index("ix_market_narratives_category", "market_narratives", ["category"])
    op.create_index("ix_market_narratives_is_active", "market_narratives", ["is_active"])

    op.create_table(
        "narrative_keywords",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("narrative_id", sa.Integer(), sa.ForeignKey("market_narratives.id"), nullable=False),
        sa.Column("keyword", sa.String(length=160), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_narrative_keywords_narrative_id", "narrative_keywords", ["narrative_id"])
    op.create_index("ix_narrative_keywords_keyword", "narrative_keywords", ["keyword"])

    op.create_table(
        "narrative_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_time", sa.DateTime(), nullable=False),
        sa.Column("narrative_id", sa.Integer(), sa.ForeignKey("market_narratives.id"), nullable=False),
        sa.Column("mention_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("weighted_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sentiment_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("impact_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("trend_direction", sa.String(length=16), nullable=False, server_default="STABLE"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("metadata_json", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_narrative_snapshots_snapshot_time", "narrative_snapshots", ["snapshot_time"])
    op.create_index("ix_narrative_snapshots_narrative_id", "narrative_snapshots", ["narrative_id"])
    op.create_index("ix_narrative_snapshots_weighted_score", "narrative_snapshots", ["weighted_score"])
    op.create_index("ix_narrative_snapshots_trend_direction", "narrative_snapshots", ["trend_direction"])

    narrative_table = sa.table(
        "market_narratives",
        sa.column("slug"),
        sa.column("name"),
        sa.column("description"),
        sa.column("category"),
    )
    op.bulk_insert(
        narrative_table,
        [
            {"slug": slug, "name": name, "description": description, "category": category}
            for slug, name, description, category in NARRATIVES
        ],
    )
    conn = op.get_bind()
    ids: dict[str, int] = {str(row[0]): int(row[1]) for row in conn.execute(sa.text("select slug, id from market_narratives"))}
    keyword_table = sa.table("narrative_keywords", sa.column("narrative_id"), sa.column("keyword"), sa.column("weight"))
    rows = [
        {"narrative_id": ids[slug], "keyword": keyword, "weight": weight}
        for slug, words in KEYWORDS.items()
        for keyword, weight in words
    ]
    op.bulk_insert(keyword_table, rows)


def downgrade() -> None:
    op.drop_index("ix_narrative_snapshots_trend_direction", table_name="narrative_snapshots")
    op.drop_index("ix_narrative_snapshots_weighted_score", table_name="narrative_snapshots")
    op.drop_index("ix_narrative_snapshots_narrative_id", table_name="narrative_snapshots")
    op.drop_index("ix_narrative_snapshots_snapshot_time", table_name="narrative_snapshots")
    op.drop_table("narrative_snapshots")
    op.drop_index("ix_narrative_keywords_keyword", table_name="narrative_keywords")
    op.drop_index("ix_narrative_keywords_narrative_id", table_name="narrative_keywords")
    op.drop_table("narrative_keywords")
    op.drop_index("ix_market_narratives_is_active", table_name="market_narratives")
    op.drop_index("ix_market_narratives_category", table_name="market_narratives")
    op.drop_index("ix_market_narratives_slug", table_name="market_narratives")
    op.drop_table("market_narratives")
