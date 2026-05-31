from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.services.market_intelligence.source_registry import SourceCategory, SourceRegistryService, SourceTier

router = APIRouter(prefix="/news", tags=["market-intelligence"])
service = SourceRegistryService()


@router.get("/sources")
def list_sources(db: Session = Depends(db_session)) -> dict[str, object]:
    items = service.list_sources(db)
    return {"data": [
        {
            "id": x.id,
            "name": x.name,
            "slug": x.slug,
            "category": x.category,
            "tier": x.tier,
            "kind": x.kind,
            "credibility_weight": x.credibility_weight,
            "signal_quality_weight": x.signal_quality_weight,
            "sovereignty_weight": x.sovereignty_weight,
            "default_confidence": x.default_confidence,
            "is_active": x.is_active,
            "fetch_interval_minutes": x.fetch_interval_minutes,
        }
        for x in items
    ]}


@router.get("/sources/{source_id}")
def get_source(source_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    source = service.get_source(db, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="source not found")
    return {"data": {"id": source.id, "name": source.name, "slug": source.slug, "category": source.category, "tier": source.tier, "kind": source.kind, "credibility_weight": source.credibility_weight, "signal_quality_weight": source.signal_quality_weight, "sovereignty_weight": source.sovereignty_weight, "default_confidence": source.default_confidence, "is_active": source.is_active, "fetch_interval_minutes": source.fetch_interval_minutes}}


@router.get("/sources/categories")
def categories() -> dict[str, object]:
    return {"data": [x.value for x in SourceCategory]}


@router.get("/sources/tiers")
def tiers() -> dict[str, object]:
    return {"data": [x.value for x in SourceTier]}


@router.get("/sources/health")
def sources_health(db: Session = Depends(db_session)) -> dict[str, object]:
    items = service.list_sources(db)
    return {"data": [{"source_id": x.id, "provider_confidence": x.provider_confidence, "health_band": x.health_band, "degraded_state": x.is_degraded, "last_success_at": x.last_success_at, "last_failure_at": x.last_failure_at, "avg_latency_ms": x.avg_latency_ms, "failure_count": x.failure_count, "consecutive_failures": x.consecutive_failures, "backoff_until": x.backoff_until} for x in items]}


@router.get("/sources/{source_id}/health")
def source_health(source_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    x = service.get_source(db, source_id)
    if x is None:
        raise HTTPException(status_code=404, detail="source not found")
    return {"data": {"source_id": x.id, "provider_confidence": x.provider_confidence, "health_band": x.health_band, "degraded_state": x.is_degraded, "last_success_at": x.last_success_at, "last_failure_at": x.last_failure_at, "avg_latency_ms": x.avg_latency_ms, "failure_count": x.failure_count, "consecutive_failures": x.consecutive_failures, "backoff_until": x.backoff_until}}


@router.get("/sources/{source_id}/snapshots")
def source_snapshots(source_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.source_health_snapshot import SourceHealthSnapshot
    rows = list(db.execute(select(SourceHealthSnapshot).where(SourceHealthSnapshot.source_id == source_id).order_by(SourceHealthSnapshot.id.desc()).limit(100)).scalars())
    return {"data": [{"snapshot_window": r.snapshot_window, "provider_confidence": r.provider_confidence, "health_band": r.health_band, "degraded_state": r.degraded_state, "created_at": r.created_at} for r in rows]}


@router.get("/sources/{source_id}/confidence-events")
def source_confidence_events(source_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.provider_confidence_event import ProviderConfidenceEvent
    rows = list(db.execute(select(ProviderConfidenceEvent).where(ProviderConfidenceEvent.source_id == source_id).order_by(ProviderConfidenceEvent.id.desc()).limit(100)).scalars())
    return {"data": [{"event_type": r.event_type, "old_confidence": r.old_confidence, "new_confidence": r.new_confidence, "delta": r.delta, "reason_code": r.reason_code, "created_at": r.created_at} for r in rows]}


@router.get("/clusters")
def list_clusters(db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.news_article_cluster import NewsArticleCluster
    rows = list(db.execute(select(NewsArticleCluster).order_by(NewsArticleCluster.id.desc()).limit(100)).scalars())
    return {"data": [{"cluster_id": r.id, "canonical_article_id": r.canonical_article_id, "article_count": r.article_count, "cluster_confidence": r.cluster_confidence} for r in rows]}


@router.get("/clusters/{cluster_id}")
def get_cluster(cluster_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.news_article import NewsArticle
    from app.db.models.news_article_cluster import NewsArticleCluster
    cl = db.get(NewsArticleCluster, cluster_id)
    if cl is None:
        raise HTTPException(status_code=404, detail="cluster not found")
    arts = list(db.execute(select(NewsArticle).where(NewsArticle.cluster_id == cluster_id)).scalars())
    return {"data": {"cluster_id": cl.id, "canonical_article_id": cl.canonical_article_id, "article_count": cl.article_count, "cluster_confidence": cl.cluster_confidence, "articles": [{"id": a.id, "title": a.title, "is_canonical": a.is_canonical} for a in arts]}}


@router.get("/articles/{article_id}/duplicates")
def article_duplicates(article_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import or_, select
    from app.db.models.news_article import NewsArticle
    a = db.get(NewsArticle, article_id)
    if a is None:
        raise HTTPException(status_code=404, detail="article not found")
    rows = list(db.execute(select(NewsArticle).where(or_(NewsArticle.duplicate_of_id == article_id, NewsArticle.id == a.duplicate_of_id))).scalars())
    return {"data": [{"id": x.id, "title": x.title, "deduplication_status": x.deduplication_status, "similarity_score": x.similarity_score} for x in rows]}


@router.get("/events")
def list_events(db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.news_event import NewsEvent
    rows = list(db.execute(select(NewsEvent).where(NewsEvent.is_active.is_(True)).order_by(NewsEvent.first_seen_at.desc()).limit(100)).scalars())
    return {"data": [{"id": e.id, "canonical_title": e.canonical_title, "event_type": e.event_type, "event_category": e.event_category, "source_count": e.source_count, "article_count": e.article_count, "event_confidence": e.event_confidence, "is_high_impact": e.is_high_impact} for e in rows]}


@router.get("/events/{event_id}")
def get_event(event_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    from app.db.models.news_event import NewsEvent
    e = db.get(NewsEvent, event_id)
    if e is None:
        raise HTTPException(status_code=404, detail="event not found")
    return {"data": {"id": e.id, "canonical_title": e.canonical_title, "canonical_summary": e.canonical_summary, "event_type": e.event_type, "event_category": e.event_category, "first_seen_at": e.first_seen_at, "last_seen_at": e.last_seen_at, "source_count": e.source_count, "article_count": e.article_count, "event_confidence": e.event_confidence}}


@router.get("/events/{event_id}/articles")
def get_event_articles(event_id: int, db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.news_article import NewsArticle
    from app.db.models.news_event_article import NewsEventArticle
    rows = list(db.execute(select(NewsArticle, NewsEventArticle).join(NewsEventArticle, NewsEventArticle.article_id == NewsArticle.id).where(NewsEventArticle.event_id == event_id)).all())
    return {"data": [{"article_id": a.id, "title": a.title, "published_at": a.published_at, "relationship_type": link.relationship_type, "similarity_score": link.similarity_score, "is_primary_source": link.is_primary_source} for a, link in rows]}


@router.get("/events/high-impact")
def high_impact_events(db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.news_event import NewsEvent
    rows = list(db.execute(select(NewsEvent).where(NewsEvent.is_high_impact.is_(True), NewsEvent.is_active.is_(True)).order_by(NewsEvent.first_seen_at.desc()).limit(100)).scalars())
    return {"data": [{"id": e.id, "canonical_title": e.canonical_title, "event_confidence": e.event_confidence} for e in rows]}


@router.get("/events/security")
def security_events(db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.news_event import NewsEvent
    rows = list(db.execute(select(NewsEvent).where(NewsEvent.is_security_related.is_(True), NewsEvent.is_active.is_(True)).order_by(NewsEvent.first_seen_at.desc()).limit(100)).scalars())
    return {"data": [{"id": e.id, "canonical_title": e.canonical_title, "event_type": e.event_type} for e in rows]}


@router.get("/events/regulatory")
def regulatory_events(db: Session = Depends(db_session)) -> dict[str, object]:
    from sqlalchemy import select
    from app.db.models.news_event import NewsEvent
    rows = list(db.execute(select(NewsEvent).where(NewsEvent.is_regulatory_related.is_(True), NewsEvent.is_active.is_(True)).order_by(NewsEvent.first_seen_at.desc()).limit(100)).scalars())
    return {"data": [{"id": e.id, "canonical_title": e.canonical_title, "event_type": e.event_type} for e in rows]}
