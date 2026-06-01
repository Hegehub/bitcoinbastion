from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from statistics import mean, median
from time import perf_counter

from sqlalchemy.orm import Session

from app.db.models.historical_pattern import HistoricalPattern
from app.db.models.historical_reaction_profile import HistoricalReactionProfile
from app.db.models.historical_similarity_match import HistoricalSimilarityMatch
from app.db.models.news_event import NewsEvent
from app.db.models.news_price_impact import NewsPriceImpact
from app.db.models.time_utils import utcnow
from app.services.intelligence.historical_similarity_metrics import (
    SIMILARITY_FAILURES_TOTAL,
    SIMILARITY_GENERATION_DURATION_SECONDS,
    SIMILARITY_MATCHES_FOUND,
    SIMILARITY_REQUESTS_TOTAL,
)

DISCLAIMER = "Historical similarity does not imply future performance. Correlation is not proof of causation."

PATTERN_SEEDS: tuple[tuple[str, str, str, str], ...] = (
    ("ETF_INFLOW_SHOCK", "ETF inflow shock", "institutional", "Spot Bitcoin ETF inflow shock."),
    ("ETF_OUTFLOW_SHOCK", "ETF outflow shock", "institutional", "Spot Bitcoin ETF outflow shock."),
    ("SEC_ENFORCEMENT", "SEC enforcement", "regulatory", "SEC enforcement or litigation pressure."),
    ("REGULATORY_APPROVAL", "Regulatory approval", "regulatory", "Constructive regulatory approval event."),
    ("FED_LIQUIDITY_EASING", "Fed liquidity easing", "macro", "Dovish liquidity or easing regime."),
    ("FED_LIQUIDITY_TIGHTENING", "Fed liquidity tightening", "macro", "Hawkish liquidity or tightening regime."),
    ("EXCHANGE_HACK", "Exchange hack", "security", "Exchange compromise or loss event."),
    ("CUSTODY_FAILURE", "Custody failure", "security", "Custody, key-management, or custodian failure."),
    ("MINER_CAPITULATION", "Miner capitulation", "mining", "Miner distress or forced selling pattern."),
    ("MINER_ACCUMULATION", "Miner accumulation", "mining", "Miner accumulation or reduced miner selling."),
    ("BITCOIN_CORE_RELEASE", "Bitcoin Core release", "bitcoin_core", "Bitcoin Core release or protocol maintenance event."),
    ("LIGHTNING_ADOPTION", "Lightning adoption", "lightning", "Lightning Network adoption pattern."),
    ("TREASURY_ADOPTION", "Treasury adoption", "treasury", "Corporate or treasury Bitcoin adoption."),
    ("INSTITUTIONAL_ACCUMULATION", "Institutional accumulation", "institutional", "Institutional Bitcoin accumulation pattern."),
    ("LARGE_LIQUIDATION_CASCADE", "Large liquidation cascade", "market_structure", "Large liquidation cascade or forced deleveraging."),
    ("MACRO_RISK_ON", "Macro risk-on", "macro", "Risk-on macro backdrop."),
    ("MACRO_RISK_OFF", "Macro risk-off", "macro", "Risk-off macro backdrop."),
    ("SECURITY_VULNERABILITY", "Security vulnerability", "security", "Security vulnerability or exploit disclosure."),
)

KEYWORDS: dict[str, tuple[str, ...]] = {
    "ETF_INFLOW_SHOCK": ("etf", "inflow", "flows", "demand"),
    "ETF_OUTFLOW_SHOCK": ("etf", "outflow"),
    "SEC_ENFORCEMENT": ("sec", "enforcement", "lawsuit", "charges"),
    "REGULATORY_APPROVAL": ("approval", "approved", "regulatory approval"),
    "FED_LIQUIDITY_EASING": ("fed", "liquidity", "easing", "dovish"),
    "FED_LIQUIDITY_TIGHTENING": ("fed", "tightening", "hawkish", "rates"),
    "EXCHANGE_HACK": ("exchange", "hack"),
    "CUSTODY_FAILURE": ("custody", "custodian", "failure"),
    "MINER_CAPITULATION": ("miner", "capitulation"),
    "MINER_ACCUMULATION": ("miner", "accumulation"),
    "BITCOIN_CORE_RELEASE": ("bitcoin core", "core release"),
    "LIGHTNING_ADOPTION": ("lightning",),
    "TREASURY_ADOPTION": ("treasury", "corporate"),
    "INSTITUTIONAL_ACCUMULATION": ("institutional", "accumulation", "blackrock", "fidelity"),
    "LARGE_LIQUIDATION_CASCADE": ("liquidation", "cascade"),
    "MACRO_RISK_ON": ("risk-on", "recovery"),
    "MACRO_RISK_OFF": ("risk-off", "panic"),
    "SECURITY_VULNERABILITY": ("vulnerability", "exploit", "security"),
}


@dataclass(frozen=True)
class SimilarityScore:
    score: float
    pattern_match_score: float
    sentiment_match_score: float
    market_context_match_score: float
    reaction_similarity_score: float
    confidence_score: float
    explanation: dict[str, object]


class HistoricalReactionService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def build_reaction_profile(self, event_id: int) -> HistoricalReactionProfile | None:
        event = self.db.get(NewsEvent, event_id)
        if event is None:
            return None
        impact = self.db.query(NewsPriceImpact).filter(NewsPriceImpact.event_id == event_id).first()
        existing = (
            self.db.query(HistoricalReactionProfile)
            .filter(HistoricalReactionProfile.event_id == event_id)
            .first()
        )
        profile = existing or HistoricalReactionProfile(event_id=event_id)
        if existing is None:
            self.db.add(profile)
        changes = [
            impact.change_15m_pct if impact else None,
            impact.change_1h_pct if impact else None,
            impact.change_4h_pct if impact else None,
            impact.change_24h_pct if impact else None,
        ]
        clean = [value for value in changes if value is not None]
        profile.reaction_15m_pct = changes[0]
        profile.reaction_1h_pct = changes[1]
        profile.reaction_4h_pct = changes[2]
        profile.reaction_24h_pct = changes[3]
        profile.max_positive_move_pct = max(clean) if clean else None
        profile.max_negative_move_pct = min(clean) if clean else None
        profile.volatility_score = self._volatility(clean)
        profile.confidence_score = self._confidence(impact, clean)
        self.db.flush()
        return profile

    def payload(self, profile: HistoricalReactionProfile | None) -> dict[str, object] | None:
        if profile is None:
            return None
        return {
            "event_id": profile.event_id,
            "reaction_15m_pct": profile.reaction_15m_pct,
            "reaction_1h_pct": profile.reaction_1h_pct,
            "reaction_4h_pct": profile.reaction_4h_pct,
            "reaction_24h_pct": profile.reaction_24h_pct,
            "max_positive_move_pct": profile.max_positive_move_pct,
            "max_negative_move_pct": profile.max_negative_move_pct,
            "volatility_score": profile.volatility_score,
            "confidence_score": profile.confidence_score,
            "created_at": profile.created_at,
        }

    def _volatility(self, values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        return round(max(values) - min(values), 6)

    def _confidence(self, impact: NewsPriceImpact | None, values: list[float]) -> float:
        if impact is None or not values:
            return 0.25
        base = float(impact.impact_confidence_score or impact.confidence_score or 0.5)
        provider = float(impact.provider_confidence or 0.5)
        return round(max(0.0, min(1.0, (base * 0.7) + (provider * 0.3))), 6)


class HistoricalSimilarityService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.reactions = HistoricalReactionService(db)

    def ensure_patterns(self) -> list[HistoricalPattern]:
        for slug, name, category, description in PATTERN_SEEDS:
            row = self.db.query(HistoricalPattern).filter(HistoricalPattern.slug == slug).first()
            if row is None:
                self.db.add(
                    HistoricalPattern(
                        slug=slug, name=name, category=category, description=description
                    )
                )
            else:
                row.name = name
                row.category = category
                row.description = description
        self.db.flush()
        return self.db.query(HistoricalPattern).order_by(HistoricalPattern.slug.asc()).all()

    def find_similar_events(self, event_id: int, limit: int = 10) -> dict[str, object]:
        SIMILARITY_REQUESTS_TOTAL.inc()
        started = perf_counter()
        try:
            event = self.db.get(NewsEvent, event_id)
            if event is None:
                return self._empty(event_id, "event_not_found")
            self.ensure_patterns()
            reference_profile = self.build_similarity_profile(event_id)
            candidates = (
                self.db.query(NewsEvent)
                .filter(NewsEvent.id != event_id)
                .order_by(NewsEvent.first_seen_at.desc(), NewsEvent.id.desc())
                .all()
            )
            scored: list[tuple[NewsEvent, SimilarityScore]] = []
            for candidate in candidates:
                candidate_profile = self.build_similarity_profile(candidate.id)
                score = self.calculate_similarity_score(reference_profile, candidate_profile)
                if score.score > 0.0:
                    scored.append((candidate, score))
            scored.sort(key=lambda item: (item[1].score, item[0].first_seen_at), reverse=True)
            top = scored[:limit]
            self._persist_matches(event, top)
            SIMILARITY_MATCHES_FOUND.inc(len(top))
            reaction_profiles: list[dict[str, object]] = []
            for row, _ in top:
                profile = self.reactions.payload(self.reactions.build_reaction_profile(row.id))
                if profile is not None:
                    reaction_profiles.append(profile)
            median_reaction = self._median_reaction(reaction_profiles)
            confidence = self._report_confidence([score for _, score in top], len(top))
            limitations = self._limitations(len(top), confidence)
            pattern = reference_profile.get("pattern")
            return {
                "current_event": self._event_payload(event),
                "pattern": pattern,
                "similar_events": [self._match_payload(row, score) for row, score in top],
                "reaction_profiles": reaction_profiles,
                "median_reaction": median_reaction,
                "similarity_summary": self.generate_similarity_explanation(
                    event, pattern, median_reaction, confidence, len(top)
                ),
                "confidence": confidence,
                "limitations": limitations,
                "evidence": {
                    "attachable_to": [
                        "Evidence Packet",
                        "Evidence Replay",
                        "Candle Attribution",
                        "Reverse Explanation",
                        "News Impact Reports",
                    ],
                    "disclaimer": DISCLAIMER,
                },
                "generated_at": utcnow(),
            }
        except Exception:
            SIMILARITY_FAILURES_TOTAL.inc()
            raise
        finally:
            SIMILARITY_GENERATION_DURATION_SECONDS.observe(perf_counter() - started)

    def build_similarity_profile(self, event_id: int) -> dict[str, object]:
        event = self.db.get(NewsEvent, event_id)
        if event is None:
            return {"event_id": event_id, "pattern": None}
        reaction = self.reactions.build_reaction_profile(event_id)
        return {
            "event_id": event.id,
            "pattern": self._detect_pattern(event),
            "sentiment": str(event.event_sentiment or "UNKNOWN").upper(),
            "btc_relevance": float(event.btc_relevance_score or 0.0),
            "impact_window": self._dominant_window(event_id),
            "reaction_4h": reaction.reaction_4h_pct if reaction else None,
            "source_category": str(event.event_category or event.event_type or "unknown").lower(),
            "first_seen_at": event.first_seen_at,
        }

    def calculate_similarity_score(
        self, reference: dict[str, object], candidate: dict[str, object]
    ) -> SimilarityScore:
        pattern_score = 1.0 if reference.get("pattern") == candidate.get("pattern") else 0.0
        sentiment_score = self._sentiment_score(reference.get("sentiment"), candidate.get("sentiment"))
        btc_score = self._numeric_score(reference.get("btc_relevance"), candidate.get("btc_relevance"))
        impact_window_score = 1.0 if reference.get("impact_window") == candidate.get("impact_window") else 0.35
        reaction_score = self._reaction_score(reference.get("reaction_4h"), candidate.get("reaction_4h"))
        source_score = 1.0 if reference.get("source_category") == candidate.get("source_category") else 0.35
        total = (
            pattern_score * 0.30
            + sentiment_score * 0.20
            + btc_score * 0.15
            + impact_window_score * 0.15
            + reaction_score * 0.10
            + source_score * 0.10
        )
        confidence = round(max(0.0, min(1.0, (total * 0.85) + 0.10)), 6)
        explanation: dict[str, object] = {
            "factors": {
                "pattern_match": pattern_score,
                "sentiment_match": sentiment_score,
                "btc_relevance_proximity": btc_score,
                "impact_window_similarity": impact_window_score,
                "market_reaction_similarity": reaction_score,
                "source_category_similarity": source_score,
            },
            "weights": {
                "pattern_match": 0.30,
                "sentiment_match": 0.20,
                "btc_relevance_proximity": 0.15,
                "impact_window_similarity": 0.15,
                "market_reaction_similarity": 0.10,
                "source_category_similarity": 0.10,
            },
            "limitations": [DISCLAIMER, "Similarity is based on observable features."],
        }
        return SimilarityScore(
            score=round(max(0.0, min(1.0, total)), 6),
            pattern_match_score=pattern_score,
            sentiment_match_score=sentiment_score,
            market_context_match_score=round((impact_window_score + source_score) / 2.0, 6),
            reaction_similarity_score=reaction_score,
            confidence_score=confidence,
            explanation=explanation,
        )

    def generate_similarity_explanation(
        self,
        event: NewsEvent,
        pattern: object,
        median_reaction: dict[str, float | None],
        confidence: float,
        sample_size: int,
    ) -> str:
        pattern_text = str(pattern or "unknown historical pattern")
        reaction = median_reaction.get("reaction_4h_pct")
        reaction_text = "unknown" if reaction is None else f"{reaction:+.2f}% within 4 hours"
        confidence_text = "Medium-High" if confidence >= 0.70 else "Medium" if confidence >= 0.45 else "Low"
        return (
            f"This event resembles prior {pattern_text} events observed in Bitcoin market history. "
            f"Median historical reaction: {reaction_text}. Confidence: {confidence_text}. "
            f"Sample size: {sample_size}. {DISCLAIMER}"
        )

    def _persist_matches(
        self, event: NewsEvent, rows: list[tuple[NewsEvent, SimilarityScore]]
    ) -> None:
        self.db.query(HistoricalSimilarityMatch).filter(
            HistoricalSimilarityMatch.event_id == event.id
        ).delete()
        for candidate, score in rows:
            time_distance = abs((event.first_seen_at - candidate.first_seen_at).total_seconds()) / 86400
            self.db.add(
                HistoricalSimilarityMatch(
                    event_id=event.id,
                    similar_event_id=candidate.id,
                    similarity_score=score.score,
                    pattern_match_score=score.pattern_match_score,
                    sentiment_match_score=score.sentiment_match_score,
                    market_context_match_score=score.market_context_match_score,
                    time_distance_days=round(time_distance, 6),
                    reaction_similarity_score=score.reaction_similarity_score,
                    confidence_score=score.confidence_score,
                    explanation_json=score.explanation,
                )
            )
        self.db.flush()

    def _detect_pattern(self, event: NewsEvent) -> str | None:
        text = f"{event.canonical_title} {event.canonical_summary} {event.event_type} {event.event_category}".lower()
        best_slug: str | None = None
        best_hits = 0
        for slug, keywords in KEYWORDS.items():
            hits = sum(1 for keyword in keywords if keyword in text)
            if hits > best_hits:
                best_slug = slug
                best_hits = hits
        return best_slug

    def _dominant_window(self, event_id: int) -> str:
        impact = self.db.query(NewsPriceImpact).filter(NewsPriceImpact.event_id == event_id).first()
        return str(impact.dominant_window if impact else "UNKNOWN")

    def _sentiment_score(self, left: object, right: object) -> float:
        if left == right:
            return 1.0
        if "UNKNOWN" in {str(left), str(right)} or "NEUTRAL" in {str(left), str(right)}:
            return 0.45
        return 0.1

    def _numeric_score(self, left: object, right: object) -> float:
        left_value = self._to_float(left)
        right_value = self._to_float(right)
        return round(max(0.0, 1.0 - min(abs(left_value - right_value), 1.0)), 6)

    def _reaction_score(self, left: object, right: object) -> float:
        if left is None or right is None:
            return 0.5
        left_value = self._to_float(left)
        right_value = self._to_float(right)
        return round(max(0.0, 1.0 - min(abs(left_value - right_value) / 10.0, 1.0)), 6)

    def _to_float(self, value: object) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float, str)):
            return float(value)
        return float(cast(float, value))

    def _median_reaction(self, profiles: list[dict[str, object]]) -> dict[str, float | None]:
        return {
            "reaction_15m_pct": self._median([p.get("reaction_15m_pct") for p in profiles]),
            "reaction_1h_pct": self._median([p.get("reaction_1h_pct") for p in profiles]),
            "reaction_4h_pct": self._median([p.get("reaction_4h_pct") for p in profiles]),
            "reaction_24h_pct": self._median([p.get("reaction_24h_pct") for p in profiles]),
        }

    def _median(self, values: list[object]) -> float | None:
        clean = [self._to_float(value) for value in values if value is not None]
        return round(float(median(clean)), 6) if clean else None

    def _report_confidence(self, scores: list[SimilarityScore], sample_size: int) -> float:
        if not scores:
            return 0.0
        sample_factor = min(sample_size / 5.0, 1.0)
        return round(max(0.0, min(1.0, (mean([score.confidence_score for score in scores]) * 0.75) + (sample_factor * 0.25))), 6)

    def _limitations(self, sample_size: int, confidence: float) -> list[str]:
        limitations = [DISCLAIMER, "Similarity is based on observable features."]
        if sample_size == 0:
            limitations.append("Limited historical sample.")
        elif sample_size < 3:
            limitations.append("Limited historical sample.")
        if confidence < 0.55:
            limitations.append("Pattern confidence is moderate.")
        limitations.append("Market structure may have changed since comparison events.")
        return limitations

    def _event_payload(self, event: NewsEvent) -> dict[str, object]:
        return {
            "event_id": event.id,
            "title": event.canonical_title,
            "event_type": event.event_type,
            "category": event.event_category,
            "sentiment": event.event_sentiment,
            "btc_relevance_score": event.btc_relevance_score,
            "market_impact_score": event.market_impact_score,
            "first_seen_at": event.first_seen_at,
        }

    def _match_payload(self, event: NewsEvent, score: SimilarityScore) -> dict[str, object]:
        profile = self.reactions.payload(self.reactions.build_reaction_profile(event.id))
        return {
            "event_id": event.id,
            "title": event.canonical_title,
            "date": event.first_seen_at,
            "similarity_score": score.score,
            "confidence": score.confidence_score,
            "reaction_profile": profile,
            "explanation": score.explanation,
        }

    def _empty(self, event_id: int, reason: str) -> dict[str, object]:
        return {
            "current_event": {"event_id": event_id},
            "pattern": None,
            "similar_events": [],
            "reaction_profiles": [],
            "median_reaction": self._median_reaction([]),
            "confidence": 0.0,
            "limitations": [DISCLAIMER, reason, "Limited historical sample."],
            "generated_at": utcnow(),
        }
