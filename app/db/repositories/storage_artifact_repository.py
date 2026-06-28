from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.storage_artifact import StorageArtifact, StorageArtifactStatus
from app.db.models.time_utils import utcnow


class StorageArtifactRepositoryError(RuntimeError):
    pass


class StorageArtifactRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, artifact: StorageArtifact) -> StorageArtifact:
        self.db.add(artifact)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise StorageArtifactRepositoryError("artifact_id already exists") from exc
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise StorageArtifactRepositoryError("could not create storage artifact") from exc
        self.db.refresh(artifact)
        return artifact

    def get_by_id(self, artifact_pk: int) -> StorageArtifact | None:
        return self.db.get(StorageArtifact, artifact_pk)

    def get_by_artifact_id(self, artifact_id: str) -> StorageArtifact | None:
        stmt = select(StorageArtifact).where(StorageArtifact.artifact_id == artifact_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_sha256_hash(self, sha256_hash: str, limit: int = 100) -> list[StorageArtifact]:
        stmt = (
            select(StorageArtifact)
            .where(StorageArtifact.sha256_hash == sha256_hash.lower())
            .order_by(StorageArtifact.created_at.desc(), StorageArtifact.id.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())

    def get_by_bucket_key(self, bucket: str, object_key: str) -> StorageArtifact | None:
        stmt = (
            select(StorageArtifact)
            .where(StorageArtifact.bucket == bucket)
            .where(StorageArtifact.object_key == object_key)
            .order_by(StorageArtifact.created_at.desc(), StorageArtifact.id.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def list_by_domain(
        self, domain: str, limit: int = 100, offset: int = 0
    ) -> list[StorageArtifact]:
        stmt = (
            select(StorageArtifact)
            .where(StorageArtifact.domain == domain)
            .order_by(StorageArtifact.created_at.desc(), StorageArtifact.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())

    def list_by_type(
        self, artifact_type: str, limit: int = 100, offset: int = 0
    ) -> list[StorageArtifact]:
        stmt = (
            select(StorageArtifact)
            .where(StorageArtifact.artifact_type == artifact_type)
            .order_by(StorageArtifact.created_at.desc(), StorageArtifact.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())

    def list_artifacts(
        self,
        *,
        domain: str | None = None,
        artifact_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[StorageArtifact]:
        stmt = select(StorageArtifact)
        if domain:
            stmt = stmt.where(StorageArtifact.domain == domain)
        if artifact_type:
            stmt = stmt.where(StorageArtifact.artifact_type == artifact_type)
        if status:
            stmt = stmt.where(StorageArtifact.status == status)
        stmt = (
            stmt.order_by(StorageArtifact.created_at.desc(), StorageArtifact.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars())

    def mark_deleted(self, artifact_id: str) -> StorageArtifact:
        artifact = self._require_artifact(artifact_id)
        artifact.status = StorageArtifactStatus.DELETED.value
        artifact.deleted_at = utcnow()
        artifact.updated_at = utcnow()
        return self._save(artifact)

    def mark_quarantined(self, artifact_id: str) -> StorageArtifact:
        artifact = self._require_artifact(artifact_id)
        artifact.status = StorageArtifactStatus.QUARANTINED.value
        artifact.updated_at = utcnow()
        return self._save(artifact)

    def update_status(self, artifact_id: str, status: str) -> StorageArtifact:
        artifact = self._require_artifact(artifact_id)
        artifact.status = status
        artifact.updated_at = utcnow()
        return self._save(artifact)

    def _require_artifact(self, artifact_id: str) -> StorageArtifact:
        artifact = self.get_by_artifact_id(artifact_id)
        if artifact is None:
            raise StorageArtifactRepositoryError("storage artifact not found")
        return artifact

    def _save(self, artifact: StorageArtifact) -> StorageArtifact:
        try:
            self.db.add(artifact)
            self.db.commit()
        except SQLAlchemyError as exc:
            self.db.rollback()
            raise StorageArtifactRepositoryError("could not update storage artifact") from exc
        self.db.refresh(artifact)
        return artifact
