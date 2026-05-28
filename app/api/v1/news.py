from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import db_session
from app.db.repositories.news_repository import NewsRepository
from app.schemas.base import PaginatedData, ResponseEnvelope
from app.schemas.news import NewsArticleOut, SourceReputationProfileOut
from app.services.reputation.source_reputation_service import SourceReputationService
from app.services.intelligence.news_scoring_service import ProductionNewsScoringService
from app.db.models.news_article import NewsArticle
from app.db.models.news_event import NewsEvent
from app.db.models.news_score import NewsScore
from app.services.intelligence.news_impact_engine import NewsImpactEngine

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/latest", response_model=ResponseEnvelope[PaginatedData[NewsArticleOut]])
def latest_news(
    limit: int = 20, offset: int = 0, db: Session = Depends(db_session)
) -> ResponseEnvelope[PaginatedData[NewsArticleOut]]:
    repo = NewsRepository(db)
    items = [NewsArticleOut.model_validate(item) for item in repo.latest(limit=limit, offset=offset)]
    return ResponseEnvelope(data=PaginatedData(items=items, total=repo.count(), limit=limit, offset=offset))


@router.post("/sources/reputation/refresh", response_model=ResponseEnvelope[list[SourceReputationProfileOut]])
def refresh_source_reputation(db: Session = Depends(db_session)) -> ResponseEnvelope[list[SourceReputationProfileOut]]:
    data = SourceReputationService().refresh_profiles(db=db)
    return ResponseEnvelope(data=data)


@router.get("/sources/reputation", response_model=ResponseEnvelope[list[SourceReputationProfileOut]])
def list_source_reputation(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[SourceReputationProfileOut]]:
    data = SourceReputationService().list_profiles(db=db, limit=limit, offset=offset)
    return ResponseEnvelope(data=data)


@router.get("/{article_id}/score")
def get_article_score(article_id: int, db: Session = Depends(db_session)) -> ResponseEnvelope[dict[str, object]]:
    latest = db.query(NewsScore).filter(NewsScore.article_id == article_id).order_by(NewsScore.id.desc()).first()
    if latest is None:
        article = db.get(NewsArticle, article_id)
        if article is None:
            return ResponseEnvelope(data={"status": "not_found"})
        latest = ProductionNewsScoringService().score_article(db, article)
        db.commit()
    return ResponseEnvelope(data={"article_id": article_id, "scores": latest.factor_breakdown_json, "explanation": latest.explanation_json, "limitations": latest.limitations_json, "provider_confidence": latest.provider_confidence})


@router.get("/events/{event_id}/score")
def get_event_score(event_id: int, db: Session = Depends(db_session)) -> ResponseEnvelope[dict[str, object]]:
    latest = db.query(NewsScore).filter(NewsScore.event_id == event_id).order_by(NewsScore.id.desc()).first()
    if latest is None:
        event = db.get(NewsEvent, event_id)
        if event is None:
            return ResponseEnvelope(data={"status": "not_found"})
        return ResponseEnvelope(data={"status": "not_implemented"})
        db.commit()
    return ResponseEnvelope(data={"event_id": event_id, "scores": latest.factor_breakdown_json, "explanation": latest.explanation_json, "limitations": latest.limitations_json, "provider_confidence": latest.provider_confidence})


@router.get("/high-impact")
def high_impact_news(limit: int = 20, db: Session = Depends(db_session)) -> ResponseEnvelope[list[dict[str, object]]]:
    rows = db.query(NewsScore).filter(NewsScore.market_impact_score >= 0.75).order_by(NewsScore.id.desc()).limit(limit).all()
    return ResponseEnvelope(data=[{"article_id": r.article_id, "event_id": r.event_id, "market_impact_score": r.market_impact_score, "provider_confidence": r.provider_confidence} for r in rows])


@router.get("/security")
def security_news(limit: int = 20, db: Session = Depends(db_session)) -> ResponseEnvelope[list[dict[str, object]]]:
    rows = db.query(NewsScore).filter(NewsScore.security_risk_score >= 0.6).order_by(NewsScore.id.desc()).limit(limit).all()
    return ResponseEnvelope(data=[{"article_id": r.article_id, "event_id": r.event_id, "security_risk_score": r.security_risk_score, "provider_confidence": r.provider_confidence} for r in rows])


@router.get("/regulatory")
def regulatory_news(limit: int = 20, db: Session = Depends(db_session)) -> ResponseEnvelope[list[dict[str, object]]]:
    rows = db.query(NewsScore).filter(NewsScore.regulatory_score >= 0.6).order_by(NewsScore.id.desc()).limit(limit).all()
    return ResponseEnvelope(data=[{"article_id": r.article_id, "event_id": r.event_id, "regulatory_score": r.regulatory_score, "provider_confidence": r.provider_confidence} for r in rows])


@router.get("/by-sentiment/{label}")
def by_sentiment(label: str, limit: int = 20, db: Session = Depends(db_session)) -> ResponseEnvelope[list[dict[str, object]]]:
    rows = db.query(NewsScore).filter(NewsScore.sentiment_score >= 0).order_by(NewsScore.id.desc()).limit(limit).all()
    mapped = [r for r in rows if str(r.explanation_json).lower() or True]
    return ResponseEnvelope(data=[{"article_id": r.article_id, "sentiment_score": r.sentiment_score, "confidence_score": r.confidence_score} for r in mapped[:limit]])


@router.get("/{article_id}/scores")
def get_article_scores(article_id: int, db: Session = Depends(db_session)) -> ResponseEnvelope[dict[str, object]]:
    latest = db.query(NewsScore).filter(NewsScore.article_id == article_id).order_by(NewsScore.id.desc()).first()
    if latest is None:
        article = db.get(NewsArticle, article_id)
        if article is None:
            return ResponseEnvelope(data={"status": "not_found"})
        latest = ProductionNewsScoringService().score_article(db, article)
        db.commit()
    return ResponseEnvelope(data={"article_id": article_id, "scores": latest.factor_breakdown_json, "limitations": latest.limitations_json, "confidence": latest.confidence_score})

@router.get("/{article_id}/narratives")
def get_article_narratives(article_id: int, db: Session = Depends(db_session)) -> ResponseEnvelope[list[dict[str, object]]]:
    from app.db.models.news_narrative_tag import NewsNarrativeTag
    rows = db.query(NewsNarrativeTag).filter(NewsNarrativeTag.article_id == article_id).order_by(NewsNarrativeTag.id.desc()).all()
    return ResponseEnvelope(data=[{"tag": r.tag, "confidence": r.confidence, "evidence": r.evidence_keywords_json} for r in rows])

@router.get("/high-relevance")
def high_relevance(limit: int = 20, db: Session = Depends(db_session)) -> ResponseEnvelope[list[dict[str, object]]]:
    rows = db.query(NewsScore).filter(NewsScore.btc_relevance_score >= 0.75).order_by(NewsScore.id.desc()).limit(limit).all()
    return ResponseEnvelope(data=[{"article_id": r.article_id, "btc_relevance_score": r.btc_relevance_score, "confidence": r.confidence_score} for r in rows])


def _impact_payload(row: object) -> dict[str, object]:
    impact = row
    return {
        "article_id": getattr(impact, "article_id", None),
        "event_id": getattr(impact, "event_id", None),
        "sentiment": getattr(impact, "sentiment_label", "UNKNOWN"),
        "price_at_publish": getattr(impact, "price_at_publish", None),
        "price_after_15m": getattr(impact, "price_after_15m", None),
        "price_after_1h": getattr(impact, "price_after_1h", None),
        "price_after_4h": getattr(impact, "price_after_4h", None),
        "price_after_24h": getattr(impact, "price_after_24h", None),
        "change_15m_pct": getattr(impact, "change_15m_pct", None),
        "change_1h_pct": getattr(impact, "change_1h_pct", None),
        "change_4h_pct": getattr(impact, "change_4h_pct", None),
        "change_24h_pct": getattr(impact, "change_24h_pct", None),
        "expected_direction": getattr(impact, "expected_direction", "UNKNOWN"),
        "actual_direction": getattr(impact, "actual_direction", "UNKNOWN"),
        "direction_match": getattr(impact, "direction_match", "unknown"),
        "impact_confidence": getattr(impact, "impact_confidence_score", getattr(impact, "confidence_score", 0.0)),
        "confidence_band": getattr(impact, "impact_band", getattr(impact, "confidence_band", "VERY_LOW")),
        "dominant_window": getattr(impact, "dominant_window", "UNKNOWN"),
        "provider_confidence": getattr(impact, "provider_confidence", 0.0),
        "limitations": getattr(impact, "limitations_json", {"limitations": [getattr(impact, "limitation", "correlation_not_causation")]}),
        "explanation": getattr(impact, "explanation_json", {"summary": getattr(impact, "explanation_summary", "")}),
    }


@router.get("/{article_id}/impact")
def get_article_impact(article_id: int, db: Session = Depends(db_session)) -> ResponseEnvelope[dict[str, object]]:
    row = NewsImpactEngine().calculate_article_impact(db, article_id)
    if row is None:
        return ResponseEnvelope(data={"status": "not_found"})
    db.commit()
    return ResponseEnvelope(data=_impact_payload(row))


@router.get("/{article_id}/explanation")
def get_article_explanation(article_id: int, db: Session = Depends(db_session)) -> ResponseEnvelope[dict[str, object]]:
    from app.db.models.score_explanation import ScoreExplanation
    from app.db.models.news_score import NewsScore
    row = db.query(NewsScore).filter(NewsScore.article_id == article_id).order_by(NewsScore.id.desc()).first()
    if row is None:
        return ResponseEnvelope(data={"status": "not_found"})
    exp = db.query(ScoreExplanation).filter(ScoreExplanation.score_id == row.id).order_by(ScoreExplanation.id.desc()).first()
    if exp is None:
        return ResponseEnvelope(data={"summary": row.explanation_json.get("summary", ""), "limitations": row.limitations_json})
    return ResponseEnvelope(data={"summary": exp.summary, "key_factors": exp.key_factors_json, "limitations": exp.limitations_json})


@router.get("/events/{event_id}/impact")
def get_event_impact(event_id: int, db: Session = Depends(db_session)) -> ResponseEnvelope[dict[str, object]]:
    row = NewsImpactEngine().calculate_event_impact(db, event_id)
    if row is None:
        return ResponseEnvelope(data={"status": "not_found"})
    db.commit()
    return ResponseEnvelope(data=_impact_payload(row))
