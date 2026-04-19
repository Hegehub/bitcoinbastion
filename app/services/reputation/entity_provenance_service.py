import json

from sqlalchemy.orm import Session

from app.db.repositories.entity_repository import EntityRepository
from app.schemas.entities import ProvenanceEntityDeltaOut, ProvenanceRefreshOut


class EntityProvenanceService:
    def refresh(self, db: Session, limit: int = 200) -> ProvenanceRefreshOut:
        repo = EntityRepository(db)
        entities = repo.list_entities(limit=limit, offset=0)

        updated = 0
        drifted = 0
        deltas: list[ProvenanceEntityDeltaOut] = []
        for entity in entities:
            old_conf = float(entity.confidence)
            derived = self._derived_confidence(entity.source_refs_json)
            target = round((old_conf * 0.5) + (derived * 0.5), 3)

            drift = abs(target - old_conf)
            if drift >= 0.05:
                drifted += 1
                entity.confidence = target
                db.add(entity)
                updated += 1
                deltas.append(
                    ProvenanceEntityDeltaOut(
                        entity_id=entity.id,
                        name=entity.name,
                        old_confidence=round(old_conf, 3),
                        new_confidence=target,
                        drift=round(drift, 3),
                    )
                )

        if updated > 0:
            db.commit()

        return ProvenanceRefreshOut(scanned=len(entities), updated=updated, drifted=drifted, deltas=deltas[:20])

    @staticmethod
    def _derived_confidence(source_refs_json: str) -> float:
        try:
            parsed = json.loads(source_refs_json or "[]")
        except json.JSONDecodeError:
            parsed = []

        refs = len(parsed) if isinstance(parsed, list) else 0
        return min(1.0, 0.3 + (min(refs, 8) / 8) * 0.7)
