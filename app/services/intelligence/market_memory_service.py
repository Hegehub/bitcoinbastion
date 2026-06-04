from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from statistics import mean, median

from sqlalchemy.orm import Session

from app.db.models.event_pattern_match import EventPatternMatch
from app.db.models.historical_event_similarity import HistoricalEventSimilarity
from app.db.models.market_pattern import MarketPattern
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.pattern_reaction_profile import PatternReactionProfile
from app.db.models.time_utils import utcnow
from app.services.intelligence.historical_confidence_calibrator import (
    HistoricalConfidenceCalibrator,
)
from app.services.intelligence.historical_similarity_metrics import (
    HISTORICAL_PROFILES_GENERATED_TOTAL,
)

MARKET_PATTERNS: list[dict[str, object]] = [
    {
        "slug": "ETF_INFLOW_SHOCK",
        "name": "ETF inflow shock",
        "category": "institutional",
        "description": "Spot Bitcoin ETF inflow acceleration.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "1h",
    },
    {
        "slug": "ETF_OUTFLOW_SHOCK",
        "name": "ETF outflow shock",
        "category": "institutional",
        "description": "Spot Bitcoin ETF outflow acceleration.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "1h",
    },
    {
        "slug": "FED_LIQUIDITY_EASING",
        "name": "Fed liquidity easing",
        "category": "macro",
        "description": "Dovish liquidity or funding conditions.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "4h",
    },
    {
        "slug": "FED_LIQUIDITY_TIGHTENING",
        "name": "Fed liquidity tightening",
        "category": "macro",
        "description": "Hawkish liquidity or funding conditions.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "4h",
    },

    {
        "slug": "FED_LIQUIDITY_SHOCK",
        "name": "Fed liquidity shock",
        "category": "macro",
        "description": "Federal Reserve liquidity or policy shock affecting BTC market context.",
        "expected_sentiment": "NEUTRAL",
        "expected_direction": "UNKNOWN",
        "typical_impact_window": "4h",
    },
    {
        "slug": "SEC_APPROVAL",
        "name": "Regulatory approval",
        "category": "regulatory",
        "description": "Regulatory, SEC, or ETF approval event.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "1h",
    },
    {
        "slug": "SEC_ENFORCEMENT",
        "name": "SEC enforcement",
        "category": "regulatory",
        "description": "SEC enforcement or litigation pressure.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "1h",
    },
    {
        "slug": "BITCOIN_CORE_RELEASE",
        "name": "Bitcoin Core release",
        "category": "protocol",
        "description": "Bitcoin Core release or maintenance milestone.",
        "expected_sentiment": "NEUTRAL",
        "expected_direction": "UNKNOWN",
        "typical_impact_window": "24h",
    },
    {
        "slug": "LIGHTNING_ADOPTION",
        "name": "Lightning adoption",
        "category": "protocol",
        "description": "Lightning Network adoption or infrastructure growth.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "24h",
    },
    {
        "slug": "MINER_CAPITULATION",
        "name": "Miner capitulation",
        "category": "mining",
        "description": "Miner distress or forced selling narrative.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "4h",
    },
    {
        "slug": "MINER_ACCUMULATION",
        "name": "Miner accumulation",
        "category": "mining",
        "description": "Reduced miner selling or miner accumulation.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "24h",
    },
    {
        "slug": "EXCHANGE_HACK",
        "name": "Exchange hack",
        "category": "security",
        "description": "Exchange compromise or exploit.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "15m",
    },
    {
        "slug": "CUSTODY_FAILURE",
        "name": "Custody failure",
        "category": "security",
        "description": "Custodian failure, insolvency, or key-management risk.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "1h",
    },
    {
        "slug": "SECURITY_EXPLOIT",
        "name": "Security exploit",
        "category": "security",
        "description": "Protocol, wallet, bridge, or ecosystem exploit.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "15m",
    },

    {
        "slug": "SECURITY_INCIDENT",
        "name": "Security incident",
        "category": "security",
        "description": "Security incident, exploit, custody issue, or ecosystem compromise.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "15m",
    },
    {
        "slug": "INSTITUTIONAL_ADOPTION",
        "name": "Institutional adoption",
        "category": "institutional",
        "description": "Institutional allocation or adoption news.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "4h",
    },
    {
        "slug": "TREASURY_ADOPTION",
        "name": "Treasury adoption",
        "category": "institutional",
        "description": "Corporate or sovereign treasury adoption.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "4h",
    },
    {
        "slug": "MACRO_RISK_ON",
        "name": "Macro risk-on",
        "category": "macro",
        "description": "Risk-on macro regime supportive for BTC.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "4h",
    },
    {
        "slug": "MACRO_RISK_OFF",
        "name": "Macro risk-off",
        "category": "macro",
        "description": "Risk-off macro regime pressuring BTC.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "4h",
    },
    {
        "slug": "LIQUIDATION_CASCADE_LONG",
        "name": "Long liquidation cascade",
        "category": "market_structure",
        "description": "Long liquidation cascade or forced deleveraging.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "15m",
    },
    {
        "slug": "LIQUIDATION_CASCADE_SHORT",
        "name": "Short liquidation cascade",
        "category": "market_structure",
        "description": "Short squeeze liquidation cascade.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "15m",
    },

    {
        "slug": "LARGE_LIQUIDATION_CASCADE",
        "name": "Large liquidation cascade",
        "category": "market_structure",
        "description": "Large liquidation cascade or forced deleveraging shock.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "UNKNOWN",
        "typical_impact_window": "15m",
    },
    {
        "slug": "HALVING_NARRATIVE",
        "name": "Halving narrative",
        "category": "supply",
        "description": "Halving-cycle supply issuance narrative.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "24h",
    },
    {
        "slug": "SELF_CUSTODY_WAVE",
        "name": "Self-custody wave",
        "category": "sovereignty",
        "description": "Self-custody adoption or withdrawal wave.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "24h",
    },

    {
        "slug": "RATE_CUT_SIGNAL",
        "name": "Rate cut signal",
        "category": "macro",
        "description": "Central-bank rate-cut or dovish policy signal.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "4h",
    },
    {
        "slug": "RATE_HIKE_SIGNAL",
        "name": "Rate hike signal",
        "category": "macro",
        "description": "Central-bank rate-hike or hawkish policy signal.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "4h",
    },
    {
        "slug": "PRIVATE_KEY_LEAK",
        "name": "Private key leak",
        "category": "security",
        "description": "Private-key leak, signer compromise, or key-material exposure.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "DOWN",
        "typical_impact_window": "15m",
    },
    {
        "slug": "INSTITUTIONAL_ACCUMULATION",
        "name": "Institutional accumulation",
        "category": "institutional",
        "description": "Institutional Bitcoin accumulation or allocation narrative.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "4h",
    },
    {
        "slug": "LIQUIDATION_CASCADE",
        "name": "Liquidation cascade",
        "category": "market_structure",
        "description": "Large forced-liquidation cascade or derivative deleveraging shock.",
        "expected_sentiment": "NEGATIVE",
        "expected_direction": "UNKNOWN",
        "typical_impact_window": "15m",
    },
    {
        "slug": "VOLATILITY_EXPANSION",
        "name": "Volatility expansion",
        "category": "market_structure",
        "description": "Rapid realized-volatility expansion or market-structure breakout.",
        "expected_sentiment": "NEUTRAL",
        "expected_direction": "UNKNOWN",
        "typical_impact_window": "15m",
    },
    {
        "slug": "SOVEREIGNTY_ADOPTION",
        "name": "Sovereignty adoption",
        "category": "sovereignty",
        "description": "Nation-state, human-rights, or sovereignty adoption narrative.",
        "expected_sentiment": "POSITIVE",
        "expected_direction": "UP",
        "typical_impact_window": "24h",
    },
]


@dataclass(frozen=True)
class PatternCandidate:
    pattern: MarketPattern
    confidence: float
    reasons: list[str]


class MarketMemoryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_patterns(self) -> list[MarketPattern]:
        rows: list[MarketPattern] = []
        for payload in MARKET_PATTERNS:
            slug = str(payload["slug"])
            payload = dict(payload)
            payload.setdefault("pattern_code", slug)
            payload.setdefault("default_sentiment", payload.get("expected_sentiment", "UNKNOWN"))
            payload.setdefault("default_impact_window", payload.get("typical_impact_window", "1h"))
            payload.setdefault("risk_profile", "elevated" if "SHOCK" in slug or "HACK" in slug or "CASCADE" in slug else "standard")
            row = self.db.query(MarketPattern).filter(MarketPattern.slug == slug).first()
            if row is None:
                row = MarketPattern(
                    **payload,
                    historical_reaction_profile_json={},
                    confidence_rules_json={
                        "small_sample_penalty": True,
                        "provider_disagreement_penalty": True,
                    },
                )
                self.db.add(row)
            else:
                for key, value in payload.items():
                    setattr(row, key, value)
            rows.append(row)
        self.db.flush()
        return (
            self.db.query(MarketPattern)
            .filter(MarketPattern.is_active.is_(True))
            .order_by(MarketPattern.slug.asc())
            .all()
        )

    def get_pattern(self, pattern_id_or_slug: str | int) -> MarketPattern | None:
        self.ensure_patterns()
        if isinstance(pattern_id_or_slug, int) or str(pattern_id_or_slug).isdigit():
            return self.db.get(MarketPattern, int(pattern_id_or_slug))
        return (
            self.db.query(MarketPattern)
            .filter(MarketPattern.slug == str(pattern_id_or_slug).upper())
            .first()
        )

    def classify_event(self, event: NewsEvent, persist: bool = True) -> list[PatternCandidate]:
        patterns = self.ensure_patterns()
        candidates: list[PatternCandidate] = []
        text = f"{event.canonical_title} {event.canonical_summary} {event.event_type} {event.event_category}".lower()
        for pattern in patterns:
            score, reasons = self._pattern_score(pattern, event, text)
            if score >= 0.35:
                candidates.append(
                    PatternCandidate(pattern=pattern, confidence=score, reasons=reasons)
                )
        if not candidates:
            fallback = next(
                (pattern for pattern in patterns if pattern.slug == "MACRO_RISK_ON"), None
            )
            if fallback is not None:
                candidates.append(
                    PatternCandidate(fallback, 0.35, ["fallback low-confidence macro pattern"])
                )
        ranked = sorted(candidates, key=lambda item: (-item.confidence, item.pattern.slug))[:4]
        if persist:
            self._persist_matches(event, ranked)
        return ranked

    def retrieve_similar_events(
        self, event_id: int, limit: int = 10
    ) -> list[HistoricalEventSimilarity]:
        return (
            self.db.query(HistoricalEventSimilarity)
            .filter(HistoricalEventSimilarity.event_id == event_id)
            .order_by(
                HistoricalEventSimilarity.similarity_score.desc(),
                HistoricalEventSimilarity.id.asc(),
            )
            .limit(limit)
            .all()
        )

    def retrieve_pattern_history(self, pattern_id_or_slug: str | int) -> list[dict[str, object]]:
        pattern = self.get_pattern(pattern_id_or_slug)
        if pattern is None:
            return []
        matches = (
            self.db.query(EventPatternMatch)
            .filter(EventPatternMatch.pattern_id == pattern.id)
            .order_by(
                EventPatternMatch.classification_confidence.desc(), EventPatternMatch.id.asc()
            )
            .all()
        )
        events = {
            event.id: event
            for event in self.db.query(NewsEvent)
            .filter(NewsEvent.id.in_([row.event_id for row in matches] or [0]))
            .all()
        }
        return [
            {
                "event_id": row.event_id,
                "title": events[row.event_id].canonical_title if row.event_id in events else "",
                "classification_confidence": row.classification_confidence,
                "reasons": row.reasons_json,
                "created_at": row.created_at,
            }
            for row in matches
        ]

    def retrieve_reaction_profile(
        self, pattern_id_or_slug: str | int
    ) -> PatternReactionProfile | None:
        pattern = self.get_pattern(pattern_id_or_slug)
        if pattern is None:
            return None
        profile = (
            self.db.query(PatternReactionProfile)
            .filter(PatternReactionProfile.pattern_id == pattern.id)
            .first()
        )
        if profile is None:
            profile = self.generate_reaction_profile(pattern)
        return profile

    def retrieve_confidence_history(self, event_id: int) -> dict[str, object]:
        similarities = self.retrieve_similar_events(event_id)
        return {
            "event_id": event_id,
            "sample_size": len(similarities),
            "average_similarity": (
                mean([row.similarity_score for row in similarities]) if similarities else 0.0
            ),
            "limitations": ["Historical similarity does not guarantee future market behavior."],
        }

    def event_memory(self, event_id: int) -> dict[str, object]:
        event = self.db.get(NewsEvent, event_id)
        if event is None:
            return {"event_id": event_id, "similar_events": [], "limitations": ["event_not_found"]}
        matches = self.classify_event(event)
        return {
            "event": {
                "id": event.id,
                "title": event.canonical_title,
                "event_type": event.event_type,
            },
            "pattern_matches": [self._candidate_payload(item) for item in matches],
            "similar_events": [
                self._similarity_payload(row) for row in self.retrieve_similar_events(event_id)
            ],
            "confidence_history": self.retrieve_confidence_history(event_id),
            "limitations": [
                "Historical similarity does not guarantee future market behavior.",
                "Correlation is not proof of causation.",
            ],
        }

    def generate_reaction_profile(self, pattern: MarketPattern) -> PatternReactionProfile:
        event_ids = [
            row.event_id
            for row in self.db.query(EventPatternMatch)
            .filter(EventPatternMatch.pattern_id == pattern.id)
            .all()
        ]
        impacts = (
            self.db.query(NewsPriceImpact)
            .filter(NewsPriceImpact.event_id.in_(event_ids or [0]))
            .all()
        )
        profile = (
            self.db.query(PatternReactionProfile)
            .filter(PatternReactionProfile.pattern_id == pattern.id)
            .first()
        )
        if profile is None:
            profile = PatternReactionProfile(pattern_id=pattern.id)
            self.db.add(profile)
        values = {
            "15m": [
                impact.change_15m_pct for impact in impacts if impact.change_15m_pct is not None
            ],
            "1h": [impact.change_1h_pct for impact in impacts if impact.change_1h_pct is not None],
            "4h": [impact.change_4h_pct for impact in impacts if impact.change_4h_pct is not None],
            "24h": [
                impact.change_24h_pct for impact in impacts if impact.change_24h_pct is not None
            ],
        }
        profile.sample_size = len(impacts)
        profile.median_change_15m = self._median(values["15m"])
        profile.median_change_1h = self._median(values["1h"])
        profile.median_change_4h = self._median(values["4h"])
        profile.median_change_24h = self._median(values["24h"])
        profile.average_change_15m = self._average(values["15m"])
        profile.average_change_1h = self._average(values["1h"])
        profile.average_change_4h = self._average(values["4h"])
        profile.average_change_24h = self._average(values["24h"])
        consistency = self._consistency(values["4h"] or values["1h"] or values["15m"])
        profile.confidence_score = (
            HistoricalConfidenceCalibrator().calibrate(0.55, len(impacts), consistency).confidence
        )
        profile.updated_at = utcnow()
        HISTORICAL_PROFILES_GENERATED_TOTAL.inc()
        self.db.flush()
        return profile

    def pattern_payload(self, pattern: MarketPattern) -> dict[str, object]:
        return {
            "id": pattern.id,
            "slug": pattern.slug,
            "name": pattern.name,
            "category": pattern.category,
            "description": pattern.description,
            "expected_sentiment": pattern.expected_sentiment,
            "expected_direction": pattern.expected_direction,
            "typical_impact_window": pattern.typical_impact_window,
            "historical_reaction_profile": pattern.historical_reaction_profile_json,
            "confidence_rules": pattern.confidence_rules_json,
            "is_active": pattern.is_active,
        }

    def reaction_profile_payload(
        self, profile: PatternReactionProfile | None
    ) -> dict[str, object] | None:
        if profile is None:
            return None
        return {
            "pattern_id": profile.pattern_id,
            "sample_size": profile.sample_size,
            "median_change_15m": profile.median_change_15m,
            "median_change_1h": profile.median_change_1h,
            "median_change_4h": profile.median_change_4h,
            "median_change_24h": profile.median_change_24h,
            "average_change_15m": profile.average_change_15m,
            "average_change_1h": profile.average_change_1h,
            "average_change_4h": profile.average_change_4h,
            "average_change_24h": profile.average_change_24h,
            "confidence_score": profile.confidence_score,
            "updated_at": profile.updated_at,
        }

    def _persist_matches(self, event: NewsEvent, candidates: list[PatternCandidate]) -> None:
        existing = {
            (row.event_id, row.pattern_id)
            for row in self.db.query(EventPatternMatch)
            .filter(EventPatternMatch.event_id == event.id)
            .all()
        }
        for candidate in candidates:
            key = (event.id, candidate.pattern.id)
            if key in existing:
                continue
            self.db.add(
                EventPatternMatch(
                    event_id=event.id,
                    pattern_id=candidate.pattern.id,
                    classification_confidence=candidate.confidence,
                    reasons_json=candidate.reasons,
                )
            )
        self.db.flush()

    def _pattern_score(
        self, pattern: MarketPattern, event: NewsEvent, text: str
    ) -> tuple[float, list[str]]:
        reasons: list[str] = []
        score = 0.0
        keywords = self._keywords(pattern.slug)
        matched = [keyword for keyword in keywords if keyword in text]
        if matched:
            score += min(0.55, 0.22 * len(matched))
            reasons.append(f"matched keywords: {', '.join(matched)}")
        if pattern.expected_sentiment == str(event.event_sentiment or "UNKNOWN").upper():
            score += 0.15
            reasons.append("sentiment aligned with pattern")
        category = str(event.event_category or event.event_type or "").lower()
        if pattern.category.lower() in category or pattern.category.lower() in text:
            score += 0.20
            reasons.append("event category aligned with pattern")
        if pattern.slug.startswith("ETF") and "etf" in text:
            score += 0.25
            reasons.append("ETF-specific pattern evidence")
        if pattern.slug.startswith("SEC") and ("sec" in text or "regulatory" in text):
            score += 0.20
            reasons.append("SEC/regulatory evidence")
        return max(0.0, min(score, 1.0)), reasons or ["low-confidence contextual match"]

    def _keywords(self, slug: str) -> list[str]:
        return {
            "ETF_INFLOW_SHOCK": ["etf", "inflow", "flow"],
            "ETF_OUTFLOW_SHOCK": ["etf", "outflow"],
            "FED_LIQUIDITY_EASING": ["fed", "liquidity", "easing", "dovish"],
            "FED_LIQUIDITY_TIGHTENING": ["fed", "tightening", "hawkish", "rate"],
            "FED_LIQUIDITY_SHOCK": ["fed", "liquidity", "shock", "rate", "fomc"],
            "SEC_APPROVAL": ["sec", "approval", "approved", "regulatory"],
            "SEC_ENFORCEMENT": ["sec", "enforcement", "lawsuit", "charges"],
            "BITCOIN_CORE_RELEASE": ["bitcoin core", "core release"],
            "LIGHTNING_ADOPTION": ["lightning"],
            "MINER_CAPITULATION": ["miner", "capitulation"],
            "MINER_ACCUMULATION": ["miner", "accumulation"],
            "EXCHANGE_HACK": ["exchange", "hack"],
            "CUSTODY_FAILURE": ["custody", "custodian", "failure"],
            "SECURITY_EXPLOIT": ["exploit", "security", "malware"],
            "SECURITY_INCIDENT": ["security", "incident", "exploit", "hack", "custody"],
            "INSTITUTIONAL_ADOPTION": ["institutional", "blackrock", "fidelity"],
            "TREASURY_ADOPTION": ["treasury", "corporate"],
            "MACRO_RISK_ON": ["risk-on", "recovery"],
            "MACRO_RISK_OFF": ["risk-off", "panic"],
            "LIQUIDATION_CASCADE_LONG": ["long", "liquidation", "cascade"],
            "LIQUIDATION_CASCADE_SHORT": ["short", "squeeze", "liquidation"],
            "LARGE_LIQUIDATION_CASCADE": ["large liquidation", "liquidation", "cascade", "deleveraging"],
            "HALVING_NARRATIVE": ["halving"],
            "SELF_CUSTODY_WAVE": ["self-custody", "withdrawal"],
            "SOVEREIGNTY_ADOPTION": ["sovereignty", "nation", "state"],
        }.get(slug, [])

    def _candidate_payload(self, candidate: PatternCandidate) -> dict[str, object]:
        return {
            "pattern_id": candidate.pattern.id,
            "slug": candidate.pattern.slug,
            "confidence": candidate.confidence,
            "reasons": candidate.reasons,
        }

    def _similarity_payload(self, row: HistoricalEventSimilarity) -> dict[str, object]:
        event = self.db.get(NewsEvent, row.similar_event_id)
        return {
            "event_id": row.similar_event_id,
            "title": event.canonical_title if event else "",
            "similarity_score": row.similarity_score,
            "pattern_match": row.pattern_match,
            "explanation": row.explanation_json,
        }

    def _median(self, values: Sequence[float | None]) -> float | None:
        clean = [float(value) for value in values if value is not None]
        return float(median(clean)) if clean else None

    def _average(self, values: Sequence[float | None]) -> float | None:
        clean = [float(value) for value in values if value is not None]
        return float(mean(clean)) if clean else None

    def _consistency(self, values: Sequence[float | None]) -> float:
        clean = [float(value) for value in values if value is not None]
        if len(clean) < 2:
            return 0.35 if clean else 0.0
        positive = sum(1 for value in clean if value >= 0) / len(clean)
        return max(positive, 1.0 - positive)
