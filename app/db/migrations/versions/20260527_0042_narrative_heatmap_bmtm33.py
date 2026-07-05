"""narrative heatmap BMTM-033 expansion

Revision ID: 20260527_0042
Revises: 20260527_0041
"""

from alembic import op
import sqlalchemy as sa

revision = "20260527_0042"
down_revision = "20260527_0041"
branch_labels = None
depends_on = None

TAXONOMY = [
    ("etf", "ETF", "ETF", "ETF flows, approvals, issuers, and fund-market attention."),
    (
        "institutional-adoption",
        "INSTITUTIONAL_ADOPTION",
        "Institutional Adoption",
        "Institutional allocation and adoption narratives.",
    ),
    (
        "treasury-adoption",
        "TREASURY_ADOPTION",
        "Treasury Adoption",
        "Treasury and reserve-asset adoption narratives.",
    ),
    ("self-custody", "SELF_CUSTODY", "Self Custody", "Self-custody and withdrawal narratives."),
    (
        "sovereignty",
        "SOVEREIGNTY",
        "Sovereignty",
        "Sovereignty and censorship-resistance narratives.",
    ),
    (
        "bitcoin-core",
        "BITCOIN_CORE",
        "Bitcoin Core",
        "Bitcoin Core software and protocol maintenance narratives.",
    ),
    ("lightning", "LIGHTNING", "Lightning", "Lightning Network narratives."),
    ("mining", "MINING", "Mining", "Mining economics and miner behavior narratives."),
    ("hashrate", "HASHRATE", "Hashrate", "Hashrate and mining difficulty narratives."),
    ("macro", "MACRO", "Macro", "Macro market narratives."),
    ("fed", "FED", "Fed", "Federal Reserve narratives."),
    ("inflation", "INFLATION", "Inflation", "Inflation and purchasing-power narratives."),
    (
        "interest-rates",
        "INTEREST_RATES",
        "Interest Rates",
        "Rate-cut, rate-hike, and yield narratives.",
    ),
    ("liquidity", "LIQUIDITY", "Liquidity", "Global liquidity and market liquidity narratives."),
    ("regulation", "REGULATION", "Regulation", "Regulatory policy narratives."),
    ("sec", "SEC", "SEC", "SEC approval, enforcement, and litigation narratives."),
    ("cftc", "CFTC", "CFTC", "CFTC policy and enforcement narratives."),
    ("banking", "BANKING", "Banking", "Banking stress and fiat-rail narratives."),
    (
        "exchange-liquidity",
        "EXCHANGE_LIQUIDITY",
        "Exchange Liquidity",
        "Exchange liquidity and order-book narratives.",
    ),
    (
        "exchange-failure",
        "EXCHANGE_FAILURE",
        "Exchange Failure",
        "Exchange solvency, halt, and failure narratives.",
    ),
    ("security", "SECURITY", "Security", "Security and exploit narratives."),
    ("exchange-hack", "EXCHANGE_HACK", "Exchange Hack", "Exchange hack and breach narratives."),
    (
        "wallet-security",
        "WALLET_SECURITY",
        "Wallet Security",
        "Wallet and key-management security narratives.",
    ),
    ("privacy", "PRIVACY", "Privacy", "Bitcoin privacy narratives."),
    (
        "nation-state-adoption",
        "NATION_STATE_ADOPTION",
        "Nation State Adoption",
        "Nation-state adoption and reserve narratives.",
    ),
    (
        "corporate-adoption",
        "CORPORATE_ADOPTION",
        "Corporate Adoption",
        "Corporate Bitcoin adoption narratives.",
    ),
    ("energy", "ENERGY", "Energy", "Energy, grid, and mining power narratives."),
    ("layer2", "LAYER2", "Layer2", "Bitcoin Layer 2 narratives."),
    (
        "stablecoins",
        "STABLECOINS",
        "Stablecoins",
        "Stablecoin and dollar-rail narratives around Bitcoin markets.",
    ),
    (
        "market-structure",
        "MARKET_STRUCTURE",
        "Market Structure",
        "Market structure, basis, volatility, and order-book narratives.",
    ),
    (
        "liquidation-cascade",
        "LIQUIDATION_CASCADE",
        "Liquidation Cascade",
        "Liquidation cascade and forced-deleveraging narratives.",
    ),
    ("risk-off", "RISK_OFF", "Risk Off", "Risk-off macro narratives."),
    ("risk-on", "RISK_ON", "Risk On", "Risk-on macro narratives."),
]

KEYWORDS = {
    "hashrate": [("hashrate", 2.0), ("hash rate", 2.0), ("difficulty", 1.5)],
    "macro": [("macro", 1.6), ("global market", 1.0), ("risk appetite", 1.2)],
    "interest-rates": [
        ("interest rates", 2.0),
        ("rate cut", 1.5),
        ("rate hike", 1.5),
        ("yields", 1.2),
    ],
    "liquidity": [("liquidity", 2.0), ("global liquidity", 2.5), ("dollar liquidity", 1.8)],
    "cftc": [("cftc", 2.5), ("commodity futures", 1.5)],
    "banking": [("bank", 1.5), ("banking", 1.8), ("bank failure", 2.2), ("deposit", 1.0)],
    "exchange-liquidity": [("exchange liquidity", 2.4), ("order book", 1.5), ("market depth", 1.5)],
    "exchange-failure": [
        ("exchange failure", 2.5),
        ("withdrawals halted", 2.0),
        ("insolvency", 1.8),
    ],
    "security": [("security", 1.6), ("exploit", 1.7), ("vulnerability", 1.7)],
    "exchange-hack": [("exchange hack", 2.5), ("hack", 1.5), ("breach", 1.4)],
    "wallet-security": [("wallet security", 2.5), ("private keys", 1.7), ("seed phrase", 1.5)],
    "privacy": [("privacy", 2.0), ("coinjoin", 1.6), ("surveillance", 1.2)],
    "nation-state-adoption": [
        ("nation state", 2.2),
        ("sovereign", 1.4),
        ("strategic reserve", 1.8),
    ],
    "corporate-adoption": [("corporate", 1.6), ("company", 0.8), ("balance sheet", 1.3)],
    "energy": [("energy", 1.8), ("grid", 1.2), ("power", 1.0)],
    "layer2": [("layer 2", 2.0), ("layer2", 2.0), ("lightning", 1.2)],
    "stablecoins": [("stablecoin", 2.0), ("usdt", 1.2), ("usdc", 1.2)],
    "liquidation-cascade": [
        ("liquidation cascade", 2.7),
        ("liquidations", 2.0),
        ("forced deleveraging", 1.7),
    ],
    "risk-off": [("risk off", 2.0), ("risk-off", 2.0), ("panic", 1.2)],
    "risk-on": [("risk on", 2.0), ("risk-on", 2.0), ("recovery", 1.0)],
}


def upgrade() -> None:
    op.add_column(
        "market_narratives",
        sa.Column("narrative_type", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "market_narratives",
        sa.Column("display_name", sa.String(length=160), nullable=False, server_default=""),
    )
    op.create_index("ix_market_narratives_narrative_type", "market_narratives", ["narrative_type"])

    op.add_column(
        "narrative_snapshots",
        sa.Column("narrative_type", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "narrative_snapshots",
        sa.Column("heat_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "narrative_snapshots",
        sa.Column("volume_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.add_column(
        "narrative_snapshots",
        sa.Column("growth_score", sa.Float(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_narrative_snapshots_narrative_type", "narrative_snapshots", ["narrative_type"]
    )
    op.create_index("ix_narrative_snapshots_heat_score", "narrative_snapshots", ["heat_score"])

    op.create_table(
        "narrative_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("narrative_type", sa.String(length=64), nullable=False),
        sa.Column("article_id", sa.Integer(), sa.ForeignKey("news_articles.id"), nullable=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("news_events.id"), nullable=True),
        sa.Column("observation_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("observed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_narrative_observations_narrative_type", "narrative_observations", ["narrative_type"]
    )
    op.create_index(
        "ix_narrative_observations_article_id", "narrative_observations", ["article_id"]
    )
    op.create_index("ix_narrative_observations_event_id", "narrative_observations", ["event_id"])
    op.create_index(
        "ix_narrative_observations_observed_at", "narrative_observations", ["observed_at"]
    )

    conn = op.get_bind()
    for slug, narrative_type, display_name, description in TAXONOMY:
        row = conn.execute(
            sa.text("select id from market_narratives where slug = :slug"), {"slug": slug}
        ).first()
        if row is None:
            conn.execute(
                sa.text(
                    "insert into market_narratives (slug, narrative_type, name, display_name, description, category, is_active) values (:slug, :type, :name, :display, :description, :category, 1)"
                ),
                {
                    "slug": slug,
                    "type": narrative_type,
                    "name": display_name,
                    "display": display_name,
                    "description": description,
                    "category": narrative_type.lower(),
                },
            )
        else:
            conn.execute(
                sa.text(
                    "update market_narratives set narrative_type = :type, display_name = :display where slug = :slug"
                ),
                {"slug": slug, "type": narrative_type, "display": display_name},
            )
    conn.execute(
        sa.text(
            "update market_narratives set narrative_type = upper(replace(slug, '-', '_')) where narrative_type = ''"
        )
    )
    conn.execute(
        sa.text("update market_narratives set display_name = name where display_name = ''")
    )
    ids: dict[str, int] = {
        str(row[0]): int(row[1])
        for row in conn.execute(sa.text("select slug, id from market_narratives"))
    }
    keyword_table = sa.table(
        "narrative_keywords", sa.column("narrative_id"), sa.column("keyword"), sa.column("weight")
    )
    rows = [
        {"narrative_id": ids[slug], "keyword": keyword, "weight": weight}
        for slug, words in KEYWORDS.items()
        for keyword, weight in words
        if slug in ids
    ]
    if rows:
        op.bulk_insert(keyword_table, rows)


def downgrade() -> None:
    op.drop_index("ix_narrative_observations_observed_at", table_name="narrative_observations")
    op.drop_index("ix_narrative_observations_event_id", table_name="narrative_observations")
    op.drop_index("ix_narrative_observations_article_id", table_name="narrative_observations")
    op.drop_index("ix_narrative_observations_narrative_type", table_name="narrative_observations")
    op.drop_table("narrative_observations")
    op.drop_index("ix_narrative_snapshots_heat_score", table_name="narrative_snapshots")
    op.drop_index("ix_narrative_snapshots_narrative_type", table_name="narrative_snapshots")
    op.drop_column("narrative_snapshots", "growth_score")
    op.drop_column("narrative_snapshots", "volume_score")
    op.drop_column("narrative_snapshots", "heat_score")
    op.drop_column("narrative_snapshots", "narrative_type")
    op.drop_index("ix_market_narratives_narrative_type", table_name="market_narratives")
    op.drop_column("market_narratives", "display_name")
    op.drop_column("market_narratives", "narrative_type")
