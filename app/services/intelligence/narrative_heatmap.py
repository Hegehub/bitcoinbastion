from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Any, cast

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session


from app.db.models.intelligence_timeline import IntelligenceTimelineEvent
from app.db.models.market_narrative import MarketNarrative
from app.db.models.narrative_keyword import NarrativeKeyword
from app.db.models.narrative_observation import NarrativeObservation
from app.db.models.narrative_snapshot import NarrativeSnapshot
from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.time_utils import utcnow
from app.services.intelligence.narrative_heatmap_metrics import (
    CLASSIFICATION_FAILURES_TOTAL,
    NARRATIVE_CLASSIFICATIONS_TOTAL,
    NARRATIVE_CLASSIFIER_FAILURES_TOTAL,
    NARRATIVE_CONFIDENCE_AVG,
    NARRATIVE_DOMINANCE_UPDATES_TOTAL,
    NARRATIVE_GROWTH_RECALCULATIONS_TOTAL,
    NARRATIVE_HEAT_UPDATES_TOTAL,
    NARRATIVE_ROTATIONS_TOTAL,
    NARRATIVES_DETECTED_TOTAL,
    NARRATIVE_SNAPSHOTS_TOTAL,
)
from app.services.intelligence.narrative_types import NarrativeType
from app.services.market_intelligence.source_registry import yaml_any as yaml_loader

NARRATIVE_LIMITATION = "Narrative heatmap output is correlation-based and does not prove causation."
NARRATIVE_SAFETY = (
    "Narratives may be associated with market context, but they do not predict price movement."
)

NARRATIVE_SEEDS: tuple[tuple[str, str, str, str, tuple[tuple[str, float], ...]], ...] = (
    (
        "etf",
        "ETF",
        "ETF inflows, outflows, approvals, issuers, and fund-flow narratives.",
        "institutional",
        (
            ("etf", 2.0),
            ("spot bitcoin etf", 3.0),
            ("inflow", 1.4),
            ("outflow", 1.4),
            ("blackrock", 1.2),
            ("fidelity", 1.2),
        ),
    ),
    (
        "institutional-adoption",
        "Institutional Adoption",
        "Institutional Bitcoin adoption and allocation narratives.",
        "institutional",
        (("institutional", 2.0), ("asset manager", 1.5), ("allocation", 1.4), ("fund", 1.1)),
    ),
    (
        "treasury-adoption",
        "Treasury Adoption",
        "Corporate and treasury Bitcoin adoption narratives.",
        "treasury",
        (
            ("treasury", 2.0),
            ("corporate bitcoin", 2.2),
            ("balance sheet", 1.3),
            ("reserve asset", 1.4),
        ),
    ),
    (
        "mining",
        "Mining",
        "Mining, hash rate, difficulty, and miner balance-sheet narratives.",
        "mining",
        (
            ("miner", 2.0),
            ("mining", 2.0),
            ("hash rate", 1.7),
            ("difficulty", 1.4),
            ("capitulation", 1.3),
        ),
    ),
    (
        "bitcoin-core",
        "Bitcoin Core",
        "Bitcoin Core releases, maintenance, and protocol software narratives.",
        "bitcoin_core",
        (("bitcoin core", 3.0), ("core release", 2.0), ("protocol", 1.0), ("node", 1.0)),
    ),
    (
        "lightning",
        "Lightning",
        "Lightning Network adoption, infrastructure, and liquidity narratives.",
        "lightning",
        (("lightning", 2.5), ("ln", 1.0), ("channel", 1.0), ("payment", 0.8)),
    ),
    (
        "macro-liquidity",
        "Macro Liquidity",
        "Global liquidity and macro risk appetite narratives.",
        "macro",
        (("liquidity", 2.0), ("global liquidity", 2.5), ("risk-on", 1.4), ("risk off", 1.4)),
    ),
    (
        "fed",
        "Fed",
        "Federal Reserve policy, rates, and liquidity narratives.",
        "macro",
        (
            ("fed", 2.0),
            ("federal reserve", 2.0),
            ("rate cut", 1.5),
            ("rate hike", 1.5),
            ("powell", 1.2),
        ),
    ),
    (
        "inflation",
        "Inflation",
        "Inflation, CPI, real-rate, and purchasing-power narratives.",
        "macro",
        (("inflation", 2.0), ("cpi", 1.5), ("ppi", 1.2), ("real yield", 1.3)),
    ),
    (
        "dollar-strength",
        "Dollar Strength",
        "USD strength, DXY, and currency pressure narratives.",
        "macro",
        (("dollar", 1.8), ("dxy", 2.0), ("usd", 1.0), ("currency", 1.0)),
    ),
    (
        "regulation",
        "Regulation",
        "Regulatory policy and jurisdictional treatment narratives.",
        "regulatory",
        (
            ("regulation", 2.0),
            ("regulatory", 2.0),
            ("law", 1.0),
            ("policy", 1.0),
            ("approval", 1.2),
        ),
    ),
    (
        "sec",
        "SEC",
        "SEC enforcement, approval, delay, and litigation narratives.",
        "regulatory",
        (
            ("sec", 2.5),
            ("securities and exchange commission", 2.5),
            ("enforcement", 1.3),
            ("lawsuit", 1.2),
        ),
    ),
    (
        "self-custody",
        "Self Custody",
        "Self-custody, withdrawal, and key-sovereignty narratives.",
        "sovereignty",
        (("self custody", 2.5), ("self-custody", 2.5), ("withdrawal", 1.2), ("private keys", 1.7)),
    ),
    (
        "sovereignty",
        "Sovereignty",
        "Bitcoin sovereignty, censorship resistance, and self-determination narratives.",
        "sovereignty",
        (
            ("sovereignty", 2.0),
            ("censorship resistance", 2.0),
            ("permissionless", 1.4),
            ("freedom", 0.8),
        ),
    ),
    (
        "exchange-risk",
        "Exchange Risk",
        "Exchange solvency, hacks, reserves, and counterparty-risk narratives.",
        "security",
        (
            ("exchange", 1.6),
            ("proof of reserves", 2.0),
            ("solvency", 1.8),
            ("withdrawals halted", 2.0),
        ),
    ),
    (
        "security-incidents",
        "Security Incidents",
        "Security incidents, exploits, vulnerabilities, and custody failures.",
        "security",
        (
            ("hack", 2.0),
            ("exploit", 2.0),
            ("vulnerability", 2.0),
            ("custody failure", 2.0),
            ("breach", 1.5),
        ),
    ),
    (
        "liquidations",
        "Liquidations",
        "Liquidation cascades, leverage flushes, and forced-deleveraging narratives.",
        "market_structure",
        (("liquidation", 2.5), ("cascade", 1.8), ("leverage", 1.2), ("forced selling", 1.4)),
    ),
    (
        "stablecoin-liquidity",
        "Stablecoin Liquidity",
        "Stablecoin liquidity and dollar-rail narratives around Bitcoin markets.",
        "market_structure",
        (("stablecoin liquidity", 2.4), ("stablecoin", 2.0), ("usdt", 1.2), ("usdc", 1.2)),
    ),
    (
        "market-structure",
        "Market Structure",
        "Liquidity, order-book, volatility, basis, and market-structure narratives.",
        "market_structure",
        (
            ("market structure", 2.5),
            ("liquidity", 1.2),
            ("order book", 1.5),
            ("volatility", 1.3),
            ("basis", 1.2),
        ),
    ),
    (
        "hashrate",
        "Hashrate",
        "Hashrate and mining difficulty narratives.",
        "mining",
        (("hashrate", 2.0), ("hash rate", 2.0), ("difficulty", 1.5)),
    ),
    (
        "macro",
        "Macro",
        "Macro market narratives.",
        "macro",
        (("macro", 1.6), ("global market", 1.0), ("risk appetite", 1.2)),
    ),
    (
        "interest-rates",
        "Interest Rates",
        "Rate-cut, rate-hike, and yield narratives.",
        "macro",
        (("interest rates", 2.0), ("rate cut", 1.5), ("rate hike", 1.5), ("yields", 1.2)),
    ),
    (
        "liquidity",
        "Liquidity",
        "Global liquidity and market liquidity narratives.",
        "macro",
        (("liquidity", 2.0), ("global liquidity", 2.5), ("dollar liquidity", 1.8)),
    ),
    (
        "cftc",
        "CFTC",
        "CFTC policy and enforcement narratives.",
        "regulatory",
        (("cftc", 2.5), ("commodity futures", 1.5)),
    ),
    (
        "banking",
        "Banking",
        "Banking stress and fiat-rail narratives.",
        "macro",
        (("bank", 1.5), ("banking", 1.8), ("bank failure", 2.2), ("deposit", 1.0)),
    ),
    (
        "exchange-liquidity",
        "Exchange Liquidity",
        "Exchange liquidity and order-book narratives.",
        "market_structure",
        (("exchange liquidity", 2.4), ("order book", 1.5), ("market depth", 1.5)),
    ),
    (
        "exchange-failure",
        "Exchange Failure",
        "Exchange solvency, halt, and failure narratives.",
        "security",
        (("exchange failure", 2.5), ("withdrawals halted", 2.0), ("insolvency", 1.8)),
    ),
    (
        "security",
        "Security",
        "Security and exploit narratives.",
        "security",
        (("security", 1.6), ("exploit", 1.7), ("vulnerability", 1.7)),
    ),
    (
        "exchange-hack",
        "Exchange Hack",
        "Exchange hack and breach narratives.",
        "security",
        (("exchange hack", 2.5), ("hack", 1.5), ("breach", 1.4)),
    ),
    (
        "wallet-security",
        "Wallet Security",
        "Wallet and key-management security narratives.",
        "security",
        (("wallet security", 2.5), ("private keys", 1.7), ("seed phrase", 1.5)),
    ),
    (
        "privacy",
        "Privacy",
        "Bitcoin privacy narratives.",
        "sovereignty",
        (("privacy", 2.0), ("coinjoin", 1.6), ("surveillance", 1.2)),
    ),
    (
        "nation-state-adoption",
        "Nation State Adoption",
        "Nation-state adoption and reserve narratives.",
        "sovereignty",
        (("nation state", 2.2), ("sovereign", 1.4), ("strategic reserve", 1.8)),
    ),
    (
        "corporate-adoption",
        "Corporate Adoption",
        "Corporate Bitcoin adoption narratives.",
        "treasury",
        (("corporate", 1.6), ("company", 0.8), ("balance sheet", 1.3)),
    ),
    (
        "energy",
        "Energy",
        "Energy, grid, and mining power narratives.",
        "mining",
        (("energy", 1.8), ("grid", 1.2), ("power", 1.0)),
    ),
    (
        "layer2",
        "Layer2",
        "Bitcoin Layer 2 narratives.",
        "layer2",
        (("layer 2", 2.0), ("layer2", 2.0), ("lightning", 1.2)),
    ),
    (
        "stablecoins",
        "Stablecoins",
        "Stablecoin and dollar-rail narratives around Bitcoin markets.",
        "market_structure",
        (("stablecoin", 2.0), ("usdt", 1.2), ("usdc", 1.2)),
    ),
    (
        "liquidation-cascade",
        "Liquidation Cascade",
        "Liquidation cascade and forced-deleveraging narratives.",
        "market_structure",
        (("liquidation cascade", 2.7), ("liquidations", 2.0), ("forced deleveraging", 1.7)),
    ),
    (
        "risk-off",
        "Risk Off",
        "Risk-off macro narratives.",
        "macro",
        (("risk off", 2.0), ("risk-off", 2.0), ("panic", 1.2)),
    ),
    (
        "risk-on",
        "Risk On",
        "Risk-on macro narratives.",
        "macro",
        (("risk on", 2.0), ("risk-on", 2.0), ("recovery", 1.0)),
    ),
)

WINDOWS: dict[str, timedelta] = {
    "1h": timedelta(hours=1),
    "4h": timedelta(hours=4),
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}

NarrativeSeed = tuple[str, str, str, str, tuple[tuple[str, float], ...]]


def narrative_seed_rows(path: Path = Path("config/narratives.yaml")) -> tuple[NarrativeSeed, ...]:
    if not path.exists():
        return NARRATIVE_SEEDS
    rows = yaml_loader.safe_load(path.read_text()) or []
    seeds: list[NarrativeSeed] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        keywords = tuple(
            (str(keyword_row.get("keyword", "")).lower(), float(keyword_row.get("weight", 1.0)))
            for keyword_row in row.get("keywords", [])
            if isinstance(keyword_row, dict) and keyword_row.get("keyword")
        )
        seeds.append(
            (
                str(row.get("slug", "")).strip(),
                str(row.get("name", "")).strip(),
                str(row.get("description", "")).strip(),
                str(row.get("category", "unknown")).strip(),
                keywords,
            )
        )
    return tuple(seed for seed in seeds if seed[0] and seed[1]) or NARRATIVE_SEEDS


SLUG_TO_TYPE: dict[str, NarrativeType] = {
    "etf": NarrativeType.ETF,
    "institutional-adoption": NarrativeType.INSTITUTIONAL_ADOPTION,
    "treasury-adoption": NarrativeType.TREASURY_ADOPTION,
    "self-custody": NarrativeType.SELF_CUSTODY,
    "sovereignty": NarrativeType.SOVEREIGNTY,
    "bitcoin-core": NarrativeType.BITCOIN_CORE,
    "lightning": NarrativeType.LIGHTNING,
    "mining": NarrativeType.MINING,
    "hashrate": NarrativeType.HASHRATE,
    "macro": NarrativeType.MACRO,
    "macro-liquidity": NarrativeType.LIQUIDITY,
    "fed": NarrativeType.FED,
    "inflation": NarrativeType.INFLATION,
    "interest-rates": NarrativeType.INTEREST_RATES,
    "liquidity": NarrativeType.LIQUIDITY,
    "regulation": NarrativeType.REGULATION,
    "sec": NarrativeType.SEC,
    "cftc": NarrativeType.CFTC,
    "banking": NarrativeType.BANKING,
    "exchange-risk": NarrativeType.EXCHANGE_FAILURE,
    "exchange-liquidity": NarrativeType.EXCHANGE_LIQUIDITY,
    "exchange-failure": NarrativeType.EXCHANGE_FAILURE,
    "security": NarrativeType.SECURITY,
    "security-incidents": NarrativeType.SECURITY,
    "exchange-hack": NarrativeType.EXCHANGE_HACK,
    "wallet-security": NarrativeType.WALLET_SECURITY,
    "privacy": NarrativeType.PRIVACY,
    "nation-state-adoption": NarrativeType.NATION_STATE_ADOPTION,
    "corporate-adoption": NarrativeType.CORPORATE_ADOPTION,
    "energy": NarrativeType.ENERGY,
    "layer2": NarrativeType.LAYER2,
    "stablecoins": NarrativeType.STABLECOINS,
    "stablecoin-liquidity": NarrativeType.STABLECOINS,
    "market-structure": NarrativeType.MARKET_STRUCTURE,
    "liquidations": NarrativeType.LIQUIDATION_CASCADE,
    "liquidation-cascade": NarrativeType.LIQUIDATION_CASCADE,
    "risk-off": NarrativeType.RISK_OFF,
    "risk-on": NarrativeType.RISK_ON,
}


@dataclass(frozen=True)
class NarrativeMatch:
    narrative: MarketNarrative
    keyword_score: float
    matched_keywords: list[str]
    confidence: float


class NarrativeClassificationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_narratives(self) -> list[MarketNarrative]:
        for slug, name, description, category, keywords in narrative_seed_rows():
            narrative = self.db.query(MarketNarrative).filter(MarketNarrative.slug == slug).first()
            narrative_type = SLUG_TO_TYPE.get(slug, NarrativeType.MARKET_STRUCTURE).value
            if narrative is None:
                narrative = MarketNarrative(
                    slug=slug,
                    narrative_type=narrative_type,
                    name=name,
                    display_name=name,
                    description=description,
                    category=category,
                )
                self.db.add(narrative)
                self.db.flush()
            else:
                narrative.narrative_type = narrative_type
                narrative.name = name
                narrative.display_name = name
                narrative.description = description
                narrative.category = category
                narrative.is_active = True
            existing = {
                row.keyword: row
                for row in self.db.query(NarrativeKeyword).filter(
                    NarrativeKeyword.narrative_id == narrative.id
                )
            }
            for keyword, weight in keywords:
                row = existing.get(keyword)
                if row is None:
                    self.db.add(
                        NarrativeKeyword(narrative_id=narrative.id, keyword=keyword, weight=weight)
                    )
                else:
                    row.weight = weight
        self.db.flush()
        return (
            self.db.query(MarketNarrative)
            .filter(MarketNarrative.is_active.is_(True))
            .order_by(MarketNarrative.slug.asc())
            .all()
        )

    def classify_article(self, article: NewsArticle) -> list[NarrativeMatch]:
        text = (
            f"{article.title} {article.summary} {article.content_text} {article.category}".lower()
        )
        return self._classify_text(text)

    def classify_event(self, event: NewsEvent) -> list[NarrativeMatch]:
        text = f"{event.canonical_title} {event.canonical_summary} {event.event_type} {event.event_category}".lower()
        return self._classify_text(text)

    def observe_article(self, article: NewsArticle) -> list[NarrativeObservation]:
        return self._persist_observations(
            self.classify_article(article), article=article, event=None
        )

    def observe_event(self, event: NewsEvent) -> list[NarrativeObservation]:
        return self._persist_observations(self.classify_event(event), article=None, event=event)

    def _persist_observations(
        self,
        matches: list[NarrativeMatch],
        article: NewsArticle | None,
        event: NewsEvent | None,
    ) -> list[NarrativeObservation]:
        rows: list[NarrativeObservation] = []
        observed_at = (
            getattr(article, "published_at", None)
            or getattr(event, "first_seen_at", None)
            or utcnow()
        )
        source_confidence = float(
            getattr(article, "provider_confidence", getattr(event, "provider_confidence", 0.5))
            or 0.5
        )
        article_id = article.id if article is not None else None
        event_id = event.id if event is not None else None
        for match in matches:
            narrative_type = (
                match.narrative.narrative_type
                or SLUG_TO_TYPE.get(match.narrative.slug, NarrativeType.MARKET_STRUCTURE).value
            )
            existing = (
                self.db.query(NarrativeObservation)
                .filter(
                    NarrativeObservation.narrative_type == narrative_type,
                    NarrativeObservation.article_id == article_id,
                    NarrativeObservation.event_id == event_id,
                )
                .first()
            )
            row = existing or NarrativeObservation(
                narrative_id=match.narrative.id,
                narrative_type=narrative_type,
                article_id=article_id,
                event_id=event_id,
                observed_at=observed_at,
                observation_time=observed_at,
            )
            if existing is None:
                self.db.add(row)
            row.narrative_id = match.narrative.id
            row.observation_time = observed_at
            row.observation_score = match.keyword_score
            row.strength_score = match.keyword_score
            row.relevance_score = min(1.0, match.keyword_score / 8.0)
            row.confidence_score = match.confidence
            row.source_confidence = source_confidence
            rows.append(row)
        self.db.flush()
        return rows

    def _classify_text(self, text: str) -> list[NarrativeMatch]:
        try:
            self.ensure_narratives()
            matches: list[NarrativeMatch] = []
            narratives = (
                self.db.query(MarketNarrative).filter(MarketNarrative.is_active.is_(True)).all()
            )
            for narrative in narratives:
                keywords = (
                    self.db.query(NarrativeKeyword)
                    .filter(NarrativeKeyword.narrative_id == narrative.id)
                    .all()
                )
                matched = [keyword for keyword in keywords if keyword.keyword.lower() in text]
                if not matched:
                    continue
                keyword_score = sum(float(keyword.weight) for keyword in matched)
                confidence = min(1.0, 0.25 + (keyword_score / 6.0))
                matches.append(
                    NarrativeMatch(
                        narrative=narrative,
                        keyword_score=round(keyword_score, 6),
                        matched_keywords=[keyword.keyword for keyword in matched],
                        confidence=round(confidence, 6),
                    )
                )
            matches.sort(
                key=lambda match: (match.keyword_score, match.narrative.slug), reverse=True
            )
            NARRATIVE_CLASSIFICATIONS_TOTAL.inc(len(matches))
            NARRATIVES_DETECTED_TOTAL.inc(len({match.narrative.slug for match in matches}))
            return matches
        except Exception:
            CLASSIFICATION_FAILURES_TOTAL.inc()
            NARRATIVE_CLASSIFIER_FAILURES_TOTAL.inc()
            raise


class NarrativeScoringService:
    def score_match(
        self,
        match: NarrativeMatch,
        item: NewsArticle | NewsEvent,
        snapshot_time: datetime,
        window: timedelta,
    ) -> dict[str, float]:
        keyword_score = min(match.keyword_score / 8.0, 1.0)
        impact = self._float(
            getattr(item, "market_impact_score", getattr(item, "impact_score", 0.0))
        )
        btc_relevance = self._float(getattr(item, "btc_relevance_score", 0.0))
        confidence = self._float(
            getattr(item, "event_confidence", getattr(item, "confidence_score", 0.5))
        )
        source_credibility = self._float(getattr(item, "credibility_score", 0.7)) or 0.7
        source_count = min(self._float(getattr(item, "source_count", 1.0)) / 5.0, 1.0)
        freshness = self._freshness(item, snapshot_time, window)
        provider = self._float(getattr(item, "provider_confidence", 0.5)) or 0.5
        score = (
            keyword_score * 25.0
            + impact * 20.0
            + btc_relevance * 20.0
            + confidence * 10.0
            + source_credibility * 10.0
            + source_count * 5.0
            + freshness * 5.0
            + provider * 5.0
        )
        return {
            "weighted_score": round(score, 6),
            "impact_score": round(impact, 6),
            "btc_relevance_score": round(btc_relevance, 6),
            "event_confidence": round(confidence, 6),
            "source_credibility": round(source_credibility, 6),
            "freshness": round(freshness, 6),
            "provider_confidence": round(provider, 6),
        }

    def _freshness(
        self, item: NewsArticle | NewsEvent, snapshot_time: datetime, window: timedelta
    ) -> float:
        when = cast(
            datetime, getattr(item, "published_at", getattr(item, "first_seen_at", snapshot_time))
        )
        comparable_snapshot = (
            snapshot_time.replace(tzinfo=None)
            if snapshot_time.tzinfo and when.tzinfo is None
            else snapshot_time
        )
        comparable_when = (
            when.replace(tzinfo=None)
            if when.tzinfo and comparable_snapshot.tzinfo is None
            else when
        )
        age = max((comparable_snapshot - comparable_when).total_seconds(), 0.0)
        denominator = max(window.total_seconds(), 1.0)
        return round(max(0.0, 1.0 - min(age / denominator, 1.0)), 6)

    def _float(self, value: object) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float, str)):
            return float(value)
        return float(cast(float, value))


class NarrativeHeatEngine:
    def compute_heat_score(
        self, volume_score: float, impact_score: float, confidence_score: float, growth_score: float
    ) -> float:
        normalized_growth = max(0.0, min(growth_score, 100.0))
        score = (
            (volume_score * 0.35)
            + (impact_score * 0.30)
            + (confidence_score * 100.0 * 0.20)
            + (normalized_growth * 0.15)
        )
        return round(max(0.0, min(score, 100.0)), 6)

    def band(self, heat_score: float) -> str:
        if heat_score < 20.0:
            return "Quiet"
        if heat_score < 40.0:
            return "Emerging"
        if heat_score < 60.0:
            return "Active"
        if heat_score < 80.0:
            return "Dominant"
        return "Major Narrative"


class NarrativeTrendService:
    def detect_trend(self, current_score: float, previous_score: float | None) -> str:
        if previous_score is None:
            return "STABLE" if current_score < 20.0 else "RISING"
        delta = current_score - previous_score
        pct = delta / max(abs(previous_score), 1.0)
        if delta >= 25.0 or pct >= 0.75:
            return "SPIKING"
        if delta >= 8.0 or pct >= 0.25:
            return "RISING"
        if delta <= -25.0 or pct <= -0.75:
            return "COOLING"
        if delta <= -8.0 or pct <= -0.25:
            return "FALLING"
        return "STABLE"


class NarrativeDominanceIndex:
    def calculate(self, snapshots: list[NarrativeSnapshot]) -> dict[str, float]:
        total = sum(max(snapshot.weighted_score, 0.0) for snapshot in snapshots)
        if total <= 0:
            return {
                str(snapshot.metadata_json.get("slug", snapshot.narrative_id)): 0.0
                for snapshot in snapshots
            }
        return {
            str(snapshot.metadata_json.get("slug", snapshot.narrative_id)): round(
                (max(snapshot.weighted_score, 0.0) / total) * 100.0, 6
            )
            for snapshot in snapshots
        }


class NarrativeRotationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def detect_rotations(self, window: str = "24h") -> list[dict[str, object]]:
        latest_time = (
            self.db.query(NarrativeSnapshot.snapshot_time)
            .order_by(NarrativeSnapshot.snapshot_time.desc())
            .limit(1)
            .scalar()
        )
        if latest_time is None:
            return []
        previous_time = (
            self.db.query(NarrativeSnapshot.snapshot_time)
            .filter(NarrativeSnapshot.snapshot_time < latest_time)
            .order_by(NarrativeSnapshot.snapshot_time.desc())
            .limit(1)
            .scalar()
        )
        if previous_time is None:
            return []
        current = self._snapshots_at(latest_time)
        previous = self._snapshots_at(previous_time)
        current_dominance = NarrativeDominanceIndex().calculate(current)
        previous_dominance = NarrativeDominanceIndex().calculate(previous)
        rising = self._largest_delta(current_dominance, previous_dominance, positive=True)
        falling = self._largest_delta(current_dominance, previous_dominance, positive=False)
        if rising is None or falling is None:
            return []
        rising_slug, rising_delta = rising
        falling_slug, falling_delta = falling
        if rising_delta < 5.0 or abs(falling_delta) < 5.0:
            return []
        NARRATIVE_ROTATIONS_TOTAL.inc()
        return [
            {
                "from_narrative": falling_slug,
                "to_narrative": rising_slug,
                "from_delta_pct": round(falling_delta, 6),
                "to_delta_pct": round(rising_delta, 6),
                "window": window,
                "summary": f"Attention may be rotating from {falling_slug} toward {rising_slug}.",
                "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
                "detected_at": utcnow(),
            }
        ]

    def _snapshots_at(self, snapshot_time: datetime) -> list[NarrativeSnapshot]:
        return (
            self.db.query(NarrativeSnapshot)
            .filter(NarrativeSnapshot.snapshot_time == snapshot_time)
            .all()
        )

    def _largest_delta(
        self, current: dict[str, float], previous: dict[str, float], positive: bool
    ) -> tuple[str, float] | None:
        deltas = [
            (slug, current.get(slug, 0.0) - previous.get(slug, 0.0))
            for slug in set(current) | set(previous)
        ]
        filtered = (
            [item for item in deltas if item[1] > 0]
            if positive
            else [item for item in deltas if item[1] < 0]
        )
        if not filtered:
            return None
        return max(filtered, key=lambda item: abs(item[1]))


class NarrativeHeatmapService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.classifier = NarrativeClassificationService(db)
        self.scoring = NarrativeScoringService()
        self.trends = NarrativeTrendService()
        self.heat = NarrativeHeatEngine()

    def build_heatmap(
        self, window: str = "24h", snapshot_time: datetime | None = None
    ) -> dict[str, object]:
        snapshot_at = snapshot_time or utcnow()
        delta = WINDOWS.get(window, WINDOWS["24h"])
        self.classifier.ensure_narratives()
        articles = self._articles(snapshot_at - delta, snapshot_at)
        events = self._events(snapshot_at - delta, snapshot_at)
        aggregates = self._aggregate(articles, events, snapshot_at, delta)
        snapshots = self._store_snapshots(aggregates, snapshot_at)
        NARRATIVE_HEAT_UPDATES_TOTAL.inc(len(snapshots))
        dominance = NarrativeDominanceIndex().calculate(snapshots)
        for snapshot in snapshots:
            snapshot.dominance_score = dominance.get(
                str(snapshot.metadata_json.get("slug", snapshot.narrative_id)), 0.0
            )
        self.db.flush()
        NARRATIVE_DOMINANCE_UPDATES_TOTAL.inc()
        confidence_values = [snapshot.confidence_score for snapshot in snapshots]
        if confidence_values:
            NARRATIVE_CONFIDENCE_AVG.set(mean(confidence_values))
        self._store_timeline_events(snapshots)
        return {
            "window": window,
            "snapshot_time": snapshot_at,
            "top_narratives": [
                self.snapshot_payload(snapshot, dominance)
                for snapshot in sorted(snapshots, key=lambda row: row.weighted_score, reverse=True)
            ],
            "top_rising_narratives": [
                self.snapshot_payload(snapshot, dominance)
                for snapshot in snapshots
                if snapshot.trend_direction in {"RISING", "SPIKING"}
            ],
            "top_falling_narratives": [
                self.snapshot_payload(snapshot, dominance)
                for snapshot in snapshots
                if snapshot.trend_direction in {"FALLING", "COOLING"}
            ],
            "highest_impact_narratives": [
                self.snapshot_payload(snapshot, dominance)
                for snapshot in sorted(snapshots, key=lambda row: row.impact_score, reverse=True)
            ],
            "dominance_index": dominance,
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
            "generated_at": utcnow(),
        }

    def list_narratives(self) -> list[dict[str, object]]:
        return [self.narrative_payload(row) for row in self.classifier.ensure_narratives()]

    def get_narrative(self, slug: str) -> dict[str, object] | None:
        self.classifier.ensure_narratives()
        row = (
            self.db.query(MarketNarrative)
            .filter(
                or_(
                    MarketNarrative.slug == slug,
                    MarketNarrative.narrative_type == slug.upper().replace("-", "_"),
                    MarketNarrative.id == self._int_or_zero(slug),
                )
            )
            .first()
        )
        if row is None:
            return None
        keywords = (
            self.db.query(NarrativeKeyword)
            .filter(NarrativeKeyword.narrative_id == row.id)
            .order_by(NarrativeKeyword.weight.desc())
            .all()
        )
        latest = self._latest_snapshot(row.id)
        return {
            **self.narrative_payload(row),
            "keywords": [
                {"keyword": keyword.keyword, "weight": keyword.weight} for keyword in keywords
            ],
            "latest_snapshot": self.snapshot_payload(latest, {}) if latest else None,
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }

    def latest_snapshots(self) -> list[NarrativeSnapshot]:
        latest_time = (
            self.db.query(NarrativeSnapshot.snapshot_time)
            .order_by(NarrativeSnapshot.snapshot_time.desc())
            .limit(1)
            .scalar()
        )
        if latest_time is None:
            return []
        return (
            self.db.query(NarrativeSnapshot)
            .filter(NarrativeSnapshot.snapshot_time == latest_time)
            .all()
        )

    def top(self) -> dict[str, object]:
        snapshots = self.latest_snapshots()
        dominance = NarrativeDominanceIndex().calculate(snapshots)
        return {
            "data": [
                self.snapshot_payload(row, dominance)
                for row in sorted(snapshots, key=lambda row: row.weighted_score, reverse=True)
            ],
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }

    def rising(self) -> dict[str, object]:
        snapshots = [
            row for row in self.latest_snapshots() if row.trend_direction in {"RISING", "SPIKING"}
        ]
        dominance = NarrativeDominanceIndex().calculate(snapshots)
        return {
            "data": [self.snapshot_payload(row, dominance) for row in snapshots],
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }

    def falling(self) -> dict[str, object]:
        snapshots = [
            row for row in self.latest_snapshots() if row.trend_direction in {"FALLING", "COOLING"}
        ]
        dominance = NarrativeDominanceIndex().calculate(snapshots)
        return {
            "data": [self.snapshot_payload(row, dominance) for row in snapshots],
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }

    def emerging(self) -> dict[str, object]:
        snapshots = [
            row
            for row in self.latest_snapshots()
            if row.trend_direction in {"RISING", "SPIKING"} or row.velocity_score >= 10.0
        ]
        dominance = NarrativeDominanceIndex().calculate(snapshots)
        return {
            "data": [
                self.snapshot_payload(row, dominance)
                for row in sorted(snapshots, key=lambda row: row.velocity_score, reverse=True)
            ],
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }

    def dominant(self) -> dict[str, object]:
        snapshots = [
            row
            for row in self.latest_snapshots()
            if row.dominance_score >= 20.0 or row.heat_score >= 60.0
        ]
        dominance = NarrativeDominanceIndex().calculate(snapshots)
        return {
            "data": [
                self.snapshot_payload(row, dominance)
                for row in sorted(snapshots, key=lambda row: row.dominance_score, reverse=True)
            ],
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }

    def narrative_payload(self, row: MarketNarrative) -> dict[str, object]:
        return {
            "id": row.id,
            "slug": row.slug,
            "narrative_type": row.narrative_type,
            "name": row.name,
            "display_name": row.display_name or row.name,
            "description": row.description,
            "category": row.category,
            "is_active": row.is_active,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def snapshot_payload(
        self, row: NarrativeSnapshot | None, dominance: dict[str, float]
    ) -> dict[str, object] | None:
        if row is None:
            return None
        slug = str(row.metadata_json.get("slug", row.narrative_id))
        evidence = cast(dict[str, object], row.metadata_json.get("evidence", {}))
        supporting_articles = cast(list[dict[str, object]], evidence.get("top_articles", []))
        supporting_events = cast(list[dict[str, object]], evidence.get("top_events", []))
        return {
            "snapshot_id": row.id,
            "snapshot_time": row.snapshot_time,
            "narrative_id": row.narrative_id,
            "slug": slug,
            "narrative_type": row.narrative_type,
            "name": row.metadata_json.get("name", slug),
            "category": row.metadata_json.get("category", "unknown"),
            "mention_count": row.mention_count,
            "weighted_score": row.weighted_score,
            "heat_score": row.heat_score,
            "heat_band": self.heat.band(row.heat_score),
            "velocity_score": row.velocity_score,
            "dominance_score": row.dominance_score,
            "volume_score": row.volume_score,
            "growth_score": row.growth_score,
            "dominance_pct": dominance.get(slug, row.dominance_score),
            "sentiment_score": row.sentiment_score,
            "impact_score": row.impact_score,
            "source_count": row.source_count,
            "event_count": row.event_count,
            "supporting_events_count": row.supporting_events_count,
            "supporting_articles": supporting_articles,
            "supporting_events": supporting_events,
            "provider_confidence": row.provider_confidence,
            "trend_direction": row.trend_direction,
            "confidence_score": row.confidence_score,
            "evidence": evidence,
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }

    def dominance(self) -> dict[str, object]:
        snapshots = self.latest_snapshots()
        dominance = NarrativeDominanceIndex().calculate(snapshots)
        return {
            "data": dominance,
            "items": [
                self.snapshot_payload(row, dominance)
                for row in sorted(snapshots, key=lambda row: row.heat_score, reverse=True)
            ],
            "limitations": [NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
        }

    def history(self, period: str = "month", limit: int = 20) -> dict[str, object]:
        snapshots = (
            self.db.query(NarrativeSnapshot)
            .order_by(NarrativeSnapshot.snapshot_time.desc(), NarrativeSnapshot.heat_score.desc())
            .limit(limit)
            .all()
        )
        return {
            "period": period,
            "top_narratives": [self.snapshot_payload(row, {}) for row in snapshots],
            "most_impactful_narratives": [
                self.snapshot_payload(row, {})
                for row in sorted(snapshots, key=lambda row: row.impact_score, reverse=True)[:limit]
            ],
            "growth_leaders": [
                self.snapshot_payload(row, {})
                for row in sorted(snapshots, key=lambda row: row.growth_score, reverse=True)[:limit]
            ],
            "declining_narratives": [
                self.snapshot_payload(row, {})
                for row in sorted(snapshots, key=lambda row: row.growth_score)[:limit]
            ],
            "before_major_btc_moves": [],
            "limitations": [
                NARRATIVE_LIMITATION,
                NARRATIVE_SAFETY,
                "Major BTC move correlation requires candle attribution backfill.",
            ],
        }

    def _aggregate(
        self,
        articles: list[NewsArticle],
        events: list[NewsEvent],
        snapshot_time: datetime,
        window: timedelta,
    ) -> dict[int, dict[str, Any]]:
        aggregates: dict[int, dict[str, Any]] = {}
        for article in articles:
            matches = self.classifier.classify_article(article)
            self.classifier._persist_observations(matches, article=article, event=None)
            self._add_item(aggregates, article, matches, snapshot_time, window)
        for event in events:
            matches = self.classifier.classify_event(event)
            self.classifier._persist_observations(matches, article=None, event=event)
            self._add_item(aggregates, event, matches, snapshot_time, window)
        return aggregates

    def _add_item(
        self,
        aggregates: dict[int, dict[str, Any]],
        item: NewsArticle | NewsEvent,
        matches: list[NarrativeMatch],
        snapshot_time: datetime,
        window: timedelta,
    ) -> None:
        for match in matches:
            scoring = self.scoring.score_match(match, item, snapshot_time, window)
            aggregate = aggregates.setdefault(
                match.narrative.id,
                {
                    "narrative": match.narrative,
                    "mention_count": 0,
                    "weighted_score": 0.0,
                    "sentiments": [],
                    "impacts": [],
                    "sources": set(),
                    "event_ids": set(),
                    "article_ids": set(),
                    "provider_confidences": [],
                    "keywords": {},
                    "top_titles": [],
                },
            )
            aggregate["mention_count"] += 1
            aggregate["weighted_score"] += scoring["weighted_score"]
            aggregate["sentiments"].append(self._sentiment_value(item))
            aggregate["impacts"].append(scoring["impact_score"])
            aggregate["provider_confidences"].append(scoring["provider_confidence"])
            source_id = getattr(item, "source_id", getattr(item, "first_source_id", None))
            if source_id is not None:
                aggregate["sources"].add(source_id)
            if isinstance(item, NewsEvent):
                aggregate["event_ids"].add(item.id)
                aggregate["sources"].add(item.first_source_name or item.first_source_id or item.id)
                aggregate["top_titles"].append({"event_id": item.id, "title": item.canonical_title})
            else:
                aggregate["article_ids"].add(item.id)
                aggregate["top_titles"].append({"article_id": item.id, "title": item.title})
            for keyword in match.matched_keywords:
                aggregate["keywords"][keyword] = aggregate["keywords"].get(keyword, 0) + 1

    def _store_snapshots(
        self, aggregates: dict[int, dict[str, Any]], snapshot_time: datetime
    ) -> list[NarrativeSnapshot]:
        snapshots: list[NarrativeSnapshot] = []
        for narrative_id, aggregate in aggregates.items():
            narrative = aggregate["narrative"]
            previous = self._latest_snapshot(narrative_id)
            score = round(float(aggregate["weighted_score"]), 6)
            volume_score = round(min(float(aggregate["mention_count"]) * 20.0, 100.0), 6)
            impact_score = round(self._average(aggregate["impacts"], 0.0) * 100.0, 6)
            previous_heat = previous.heat_score if previous else 0.0
            growth_score = round(max(-100.0, min(100.0, score - previous_heat)), 6)
            velocity_score = round(max(0.0, min(100.0, growth_score)), 6)
            trend = self.trends.detect_trend(score, previous_heat if previous else None)
            NARRATIVE_GROWTH_RECALCULATIONS_TOTAL.inc()
            provider_confidence = self._average(aggregate["provider_confidences"], 0.5)
            confidence = round(
                min(
                    1.0,
                    (provider_confidence * 0.45)
                    + (min(aggregate["mention_count"] / 5.0, 1.0) * 0.35)
                    + (min(score / 100.0, 1.0) * 0.20),
                ),
                6,
            )
            heat_score = self.heat.compute_heat_score(
                volume_score, impact_score, confidence, growth_score
            )
            narrative_type = (
                narrative.narrative_type
                or SLUG_TO_TYPE.get(narrative.slug, NarrativeType.MARKET_STRUCTURE).value
            )
            snapshot = NarrativeSnapshot(
                snapshot_time=snapshot_time,
                narrative_id=narrative_id,
                narrative_type=narrative_type,
                mention_count=int(aggregate["mention_count"]),
                weighted_score=score,
                heat_score=heat_score,
                velocity_score=velocity_score,
                dominance_score=0.0,
                volume_score=volume_score,
                sentiment_score=round(self._average(aggregate["sentiments"], 0.0), 6),
                impact_score=impact_score,
                growth_score=growth_score,
                source_count=len(aggregate["sources"]),
                event_count=len(aggregate["event_ids"]),
                supporting_events_count=len(aggregate["event_ids"]),
                provider_confidence=round(provider_confidence, 6),
                trend_direction=trend,
                confidence_score=confidence,
                metadata_json={
                    "slug": narrative.slug,
                    "narrative_type": narrative_type,
                    "name": narrative.name,
                    "category": narrative.category,
                    "evidence": {
                        "top_articles": [
                            item for item in aggregate["top_titles"] if "article_id" in item
                        ][:5],
                        "top_events": [
                            item for item in aggregate["top_titles"] if "event_id" in item
                        ][:5],
                        "top_keywords": sorted(
                            aggregate["keywords"].items(), key=lambda item: item[1], reverse=True
                        )[:8],
                        "provider_state": "HEALTHY" if provider_confidence >= 0.7 else "DEGRADED",
                        "confidence_reasoning": "Confidence combines provider confidence, sample size, and weighted narrative score.",
                        "scoring_factors": {
                            "article_count": len(aggregate["article_ids"]),
                            "event_count": len(aggregate["event_ids"]),
                            "source_count": len(aggregate["sources"]),
                            "source_quality": round(provider_confidence, 6),
                            "btc_relevance": "included per item when available",
                            "market_impact": impact_score,
                            "freshness": "weighted inside item scoring",
                        },
                    },
                },
            )
            self.db.add(snapshot)
            snapshots.append(snapshot)
        self.db.flush()
        NARRATIVE_SNAPSHOTS_TOTAL.inc(len(snapshots))
        return snapshots

    def _articles(self, start: datetime, end: datetime) -> list[NewsArticle]:
        return (
            self.db.query(NewsArticle)
            .filter(
                and_(
                    NewsArticle.published_at >= start,
                    NewsArticle.published_at <= end,
                    NewsArticle.is_duplicate.is_(False),
                )
            )
            .all()
        )

    def _events(self, start: datetime, end: datetime) -> list[NewsEvent]:
        return (
            self.db.query(NewsEvent)
            .filter(
                and_(
                    NewsEvent.first_seen_at >= start,
                    NewsEvent.first_seen_at <= end,
                    NewsEvent.is_active.is_(True),
                )
            )
            .all()
        )

    def _latest_snapshot(self, narrative_id: int) -> NarrativeSnapshot | None:
        return (
            self.db.query(NarrativeSnapshot)
            .filter(NarrativeSnapshot.narrative_id == narrative_id)
            .order_by(NarrativeSnapshot.snapshot_time.desc(), NarrativeSnapshot.id.desc())
            .first()
        )

    def _store_timeline_events(self, snapshots: list[NarrativeSnapshot]) -> None:
        for snapshot in snapshots:
            if snapshot.trend_direction not in {"SPIKING", "RISING"}:
                continue
            slug = str(snapshot.metadata_json.get("slug", snapshot.narrative_id))
            title = f"{slug} narrative entered {snapshot.trend_direction} state"
            exists = (
                self.db.query(IntelligenceTimelineEvent)
                .filter(
                    IntelligenceTimelineEvent.event_time == snapshot.snapshot_time,
                    IntelligenceTimelineEvent.title == title,
                )
                .first()
            )
            if exists is not None:
                continue
            self.db.add(
                IntelligenceTimelineEvent(
                    event_type="NARRATIVE_HEATMAP",
                    importance="HIGH" if snapshot.trend_direction == "SPIKING" else "MEDIUM",
                    visibility="INTERNAL",
                    source_kind="INTERNAL",
                    title=title,
                    summary=f"Narrative score {snapshot.weighted_score:.2f}; correlation-based attention signal only.",
                    event_time=snapshot.snapshot_time,
                    confidence_score=snapshot.confidence_score,
                    provider_confidence=snapshot.provider_confidence,
                    timeline_rank=snapshot.weighted_score,
                    tags_json=["narrative", slug, snapshot.trend_direction.lower()],
                    metadata_json={
                        "narrative_id": snapshot.narrative_id,
                        "snapshot_id": snapshot.id,
                    },
                    limitations_json=[NARRATIVE_LIMITATION, NARRATIVE_SAFETY],
                )
            )

    def _sentiment_value(self, item: NewsArticle | NewsEvent) -> float:
        sentiment = str(
            getattr(item, "sentiment_label", getattr(item, "event_sentiment", "UNKNOWN"))
        ).upper()
        if sentiment == "POSITIVE":
            return 1.0
        if sentiment == "NEGATIVE":
            return -1.0
        return 0.0

    def _average(self, values: list[float], default: float) -> float:
        return float(mean(values)) if values else default

    def _int_or_zero(self, value: str) -> int:
        return int(value) if value.isdigit() else 0


class NarrativeHistoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def history(self, period: str = "month", limit: int = 20) -> dict[str, object]:
        return NarrativeHeatmapService(self.db).history(period=period, limit=limit)


NarrativeClassifierService = NarrativeClassificationService
