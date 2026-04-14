from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.repositories.news_repository import NewsRepository
from app.schemas.news import SourceReputationProfileOut


class SourceReputationService:
    def refresh_profiles(self, db: Session) -> list[SourceReputationProfileOut]:
        repo = NewsRepository(db)
        try:
            aggregates = repo.aggregate_source_scores()
            profiles: list[SourceReputationProfileOut] = []
            for source_id, sample_size, avg_credibility, avg_impact in aggregates:
                reliability_score = min(100.0, max(0.0, avg_credibility * 100))
                consistency_score = min(100.0, sample_size * 2.0)
                signal_quality_score = round((reliability_score * 0.7) + (avg_impact * 30.0), 2)

                profile = repo.upsert_profile(
                    source_id=source_id,
                    reliability_score=round(reliability_score, 2),
                    consistency_score=round(consistency_score, 2),
                    signal_quality_score=min(100.0, signal_quality_score),
                    sample_size=sample_size,
                )
                profiles.append(SourceReputationProfileOut.model_validate(profile))
            return profiles
        except OperationalError:
            db.rollback()
            return []

    def list_profiles(self, db: Session, limit: int, offset: int) -> list[SourceReputationProfileOut]:
        repo = NewsRepository(db)
        try:
            return [
                SourceReputationProfileOut.model_validate(item)
                for item in repo.list_profiles(limit=limit, offset=offset)
            ]
        except OperationalError:
            db.rollback()
            return []
