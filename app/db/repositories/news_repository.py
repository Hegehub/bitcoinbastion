from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.news import NewsArticle, NewsSource, SourceReputationProfile


class NewsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_hash(self, content_hash: str) -> NewsArticle | None:
        stmt = select(NewsArticle).where(NewsArticle.content_hash == content_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def add(self, article: NewsArticle) -> NewsArticle:
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        return article

    def latest(self, limit: int = 20, offset: int = 0) -> list[NewsArticle]:
        stmt = select(NewsArticle).order_by(NewsArticle.published_at.desc()).limit(limit).offset(offset)
        return list(self.db.execute(stmt).scalars())

    def count(self) -> int:
        stmt = select(func.count()).select_from(NewsArticle)
        return int(self.db.execute(stmt).scalar_one())

    def aggregate_source_scores(self) -> list[tuple[int, int, float, float]]:
        stmt = (
            select(
                NewsArticle.source_id,
                func.count(NewsArticle.id),
                func.avg(NewsArticle.credibility_score),
                func.avg(NewsArticle.impact_score),
            )
            .group_by(NewsArticle.source_id)
            .order_by(func.count(NewsArticle.id).desc())
        )
        return [
            (
                int(source_id),
                int(sample_size),
                float(avg_credibility or 0.0),
                float(avg_impact or 0.0),
            )
            for source_id, sample_size, avg_credibility, avg_impact in self.db.execute(stmt).all()
        ]

    def get_profile(self, source_id: int) -> SourceReputationProfile | None:
        stmt = select(SourceReputationProfile).where(SourceReputationProfile.source_id == source_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert_profile(
        self,
        *,
        source_id: int,
        reliability_score: float,
        consistency_score: float,
        signal_quality_score: float,
        sample_size: int,
    ) -> SourceReputationProfile:
        profile = self.get_profile(source_id)
        if profile is None:
            profile = SourceReputationProfile(source_id=source_id)
            self.db.add(profile)

        profile.reliability_score = reliability_score
        profile.consistency_score = consistency_score
        profile.signal_quality_score = signal_quality_score
        profile.sample_size = sample_size

        self.db.commit()
        self.db.refresh(profile)
        return profile

    def list_profiles(self, limit: int, offset: int) -> list[SourceReputationProfile]:
        stmt = (
            select(SourceReputationProfile)
            .order_by(SourceReputationProfile.signal_quality_score.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars())

    def active_sources_count(self) -> int:
        stmt = select(func.count()).select_from(NewsSource).where(NewsSource.is_active.is_(True))
        return int(self.db.execute(stmt).scalar_one())
