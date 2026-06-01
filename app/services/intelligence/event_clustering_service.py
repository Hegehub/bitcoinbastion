from __future__ import annotations

from datetime import datetime, timedelta
from difflib import SequenceMatcher

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.news_event_article import NewsEventArticle
from app.db.models.news_event_cluster import NewsEventCluster


class CanonicalNewsEventService:
    def cluster_article(self, db: Session, article_id: int) -> NewsEvent | None:
        article = db.get(NewsArticle, article_id)
        if article is None:
            return None
        candidates = self.find_candidate_events(db, article)
        best, score = None, 0.0
        for event in candidates:
            s = self.calculate_event_similarity(article, event)
            if s > score:
                best, score = event, s
        threshold = 0.82 if self._is_security(article) else 0.55
        if best is None or score < threshold:
            return self.create_event_from_article(db, article)
        return self.attach_article_to_event(db, article, best, score)

    def cluster_recent_articles(self, db: Session, hours: int = 24) -> int:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        rows = db.execute(select(NewsArticle.id).where(NewsArticle.created_at >= cutoff).order_by(NewsArticle.id.asc())).all()
        for (aid,) in rows:
            self.cluster_article(db, aid)
        db.commit()
        return len(rows)

    def find_candidate_events(self, db: Session, article: NewsArticle) -> list[NewsEvent]:
        cutoff = article.published_at - timedelta(hours=24)
        return list(db.execute(select(NewsEvent).where(NewsEvent.last_seen_at >= cutoff, NewsEvent.is_active.is_(True)).limit(100)).scalars())

    def create_event_from_article(self, db: Session, article: NewsArticle) -> NewsEvent:
        event = NewsEvent(
            event_key=f"{article.source_id}:{article.id}",
            canonical_title=self._canonical_title(article),
            canonical_summary=self._summary(article),
            event_type=self._event_type(article),
            event_category=self._event_category(article),
            primary_article_id=article.id,
            first_seen_at=article.published_at,
            last_seen_at=article.published_at,
            first_source_id=article.source_id,
            first_source_name=article.metadata_json.get("source_name", ""),
            first_source_published_at=article.published_at,
            source_count=1,
            article_count=1,
            cluster_confidence=0.8,
            event_confidence=0.7,
            provider_confidence=article.provider_confidence,
            dominant_language=article.language,
            metadata_json={"lineage": [article.id]},
            limitations_json={"notes": ["initial_cluster_single_source"]},
        )
        db.add(event)
        db.flush()
        self._link_article(db, event.id, article.id, 1.0, True)
        db.add(NewsEventCluster(event_id=event.id, cluster_hash=event.event_key, cluster_reason="seed_from_article", confidence_score=event.cluster_confidence, candidate_count=1, accepted_count=1))
        return event

    def attach_article_to_event(self, db: Session, article: NewsArticle, event: NewsEvent, similarity: float) -> NewsEvent:
        exists = db.execute(select(NewsEventArticle).where(NewsEventArticle.event_id == event.id, NewsEventArticle.article_id == article.id)).scalar_one_or_none()
        if exists is None:
            self._link_article(db, event.id, article.id, similarity, False)
            event.article_count += 1
        event.last_seen_at = max(event.last_seen_at, article.published_at)
        event.cluster_confidence = self.calculate_cluster_confidence(db, event)
        event.event_confidence = self.calculate_event_confidence(db, event)
        event.provider_confidence = max(event.provider_confidence, article.provider_confidence)
        self.determine_first_mover(db, event)
        return event

    def calculate_event_similarity(self, article: NewsArticle, event: NewsEvent) -> float:
        title_ratio = SequenceMatcher(None, (article.normalized_title or ""), (event.canonical_title or "").lower()).ratio()
        keyword = self._keyword_overlap(article.normalized_title, event.canonical_title)
        time_gap = abs((article.published_at - event.last_seen_at).total_seconds())
        time_score = 1.0 if time_gap <= 6 * 3600 else 0.5 if time_gap <= 24 * 3600 else 0.0
        base=(0.6 * title_ratio) + (0.25 * keyword) + (0.15 * time_score)
        if self._event_type(article) == event.event_type and event.event_type != "unknown":
            base += 0.35
        return round(min(1.0, base), 4)

    def calculate_cluster_confidence(self, db: Session, event: NewsEvent) -> float:
        avg_similarity = db.execute(select(func.avg(NewsEventArticle.similarity_score)).where(NewsEventArticle.event_id == event.id)).scalar() or 0.0
        return float(max(0.2, min(0.99, 0.5 + (avg_similarity * 0.5))))

    def calculate_event_confidence(self, db: Session, event: NewsEvent) -> float:
        source_factor = min(1.0, event.source_count / 5)
        cluster_factor = event.cluster_confidence
        provider_factor = event.provider_confidence
        return round(max(0.0, min(1.0, (0.35 * source_factor) + (0.4 * cluster_factor) + (0.25 * provider_factor))), 4)

    def rebuild_event(self, db: Session, event_id: int) -> NewsEvent | None:
        event = db.get(NewsEvent, event_id)
        if event is None:
            return None
        event.cluster_confidence = self.calculate_cluster_confidence(db, event)
        event.event_confidence = self.calculate_event_confidence(db, event)
        self.determine_first_mover(db, event)
        return event

    def merge_events(self, db: Session, primary_event_id: int, secondary_event_id: int) -> NewsEvent | None:
        primary, secondary = db.get(NewsEvent, primary_event_id), db.get(NewsEvent, secondary_event_id)
        if primary is None or secondary is None:
            return None
        links = list(db.execute(select(NewsEventArticle).where(NewsEventArticle.event_id == secondary.id)).scalars())
        for link in links:
            link.event_id = primary.id
        primary.article_count += secondary.article_count
        primary.source_count = max(primary.source_count, secondary.source_count)
        primary.last_seen_at = max(primary.last_seen_at, secondary.last_seen_at)
        secondary.is_active = False
        self.rebuild_event(db, primary.id)
        return primary

    def determine_first_mover(self, db: Session, event: NewsEvent) -> None:
        rows = list(db.execute(select(NewsArticle).join(NewsEventArticle, NewsEventArticle.article_id == NewsArticle.id).where(NewsEventArticle.event_id == event.id).order_by(NewsArticle.published_at.asc())).scalars())
        if rows:
            first = rows[0]
            event.first_source_id = first.source_id
            event.first_source_published_at = first.published_at

    def _link_article(self, db: Session, event_id: int, article_id: int, similarity: float, is_primary: bool) -> None:
        db.add(NewsEventArticle(event_id=event_id, article_id=article_id, similarity_score=similarity, is_primary_source=is_primary, relationship_type="primary" if is_primary else "supporting"))

    def _keyword_overlap(self, a: str, b: str) -> float:
        sa, sb = set((a or "").split()), set((b or "").split())
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)

    def _event_type(self, article: NewsArticle) -> str:
        t = (article.normalized_title or "").lower()
        if "etf" in t and "inflow" in t:
            return "institutional_etf_inflow"
        if "fed" in t:
            return "fed_liquidity"
        if any(x in t for x in ("hack", "exploit", "breach", "custody")):
            return "security_exploit"
        return "unknown"

    def _event_category(self, article: NewsArticle) -> str:
        et = self._event_type(article)
        return "institutional" if "institutional" in et else "macro" if "fed" in et else "security" if "security" in et else "unknown"

    def _canonical_title(self, article: NewsArticle) -> str:
        et = self._event_type(article)
        mapping = {
            "institutional_etf_inflow": "Bitcoin ETF inflow shock",
            "fed_liquidity": "Fed liquidity easing narrative",
            "security_exploit": "Exchange security incident",
            "unknown": article.title[:160],
        }
        return mapping[et]

    def _summary(self, article: NewsArticle) -> str:
        return f"This event groups reports related to: {article.title[:120]}"

    def _is_security(self, article: NewsArticle) -> bool:
        return self._event_type(article) in {"security_exploit", "custody_failure", "exchange_hack"}
