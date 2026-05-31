from sqlalchemy.orm import Session

from app.db.models.news_price_impact import NewsPriceImpact
from app.services.intelligence.news_impact_engine import NewsImpactEngine


class NewsPriceImpactService:
    """Backward-compatible facade for the production NewsImpactEngine."""

    def __init__(self) -> None:
        self.engine = NewsImpactEngine()

    def calculate_for_article(self, db: Session, article_id: int) -> NewsPriceImpact | None:
        return self.engine.calculate_article_impact(db, article_id)

    def calculate_for_event(self, db: Session, event_id: int) -> NewsPriceImpact | None:
        return self.engine.calculate_event_impact(db, event_id)

    def determine_impact_band(self, confidence: float) -> str:
        return self.engine._confidence_band(confidence)
