from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.db.models.evidence_packet import EvidenceReplayLog
from app.db.models.time_utils import utcnow
from app.repositories.evidence_repository import EvidenceRepository
from app.services.events.domain_event_publisher import publish_domain_event
from app.services.intelligence.evidence_metrics import (
    EVIDENCE_INTEGRITY_CHECKS_TOTAL,
    EVIDENCE_INTEGRITY_MISMATCHES_TOTAL,
    EVIDENCE_REPLAY_FAILURES_TOTAL,
    EVIDENCE_REPLAY_REQUESTS_TOTAL,
)
from app.services.intelligence.evidence_packet_builder import EvidencePacketBuilder


class EvidenceReplayService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = EvidenceRepository(db)
        self.builder = EvidencePacketBuilder(db)

    def replay_article(self, entity_id: int) -> dict[str, Any]:
        return self.replay("article", entity_id)

    def replay_event(self, entity_id: int) -> dict[str, Any]:
        return self.replay("event", entity_id)

    def replay_impact(self, entity_id: int) -> dict[str, Any]:
        return self.replay("impact", entity_id)

    def replay_attribution(self, entity_id: int) -> dict[str, Any]:
        return self.replay("attribution", entity_id)

    def replay_signal(self, entity_id: int) -> dict[str, Any]:
        return self.replay("signal", entity_id)

    def replay_publication(self, entity_id: int) -> dict[str, Any]:
        return self.replay("publication", entity_id)

    def replay(self, entity_type: str, entity_id: int) -> dict[str, Any]:
        normalized = self.builder.normalize_entity_type(entity_type)
        EVIDENCE_REPLAY_REQUESTS_TOTAL.labels(entity_type=self._bounded_entity(normalized)).inc()
        input_hash = ""
        log = EvidenceReplayLog(
            entity_type=normalized,
            entity_id=entity_id,
            step_name=f"replay_{normalized}",
            input_hash="",
        )
        self.repo.add_replay_log(log)
        try:
            input_hash = self.builder.entity_hash(normalized, entity_id)
            log.input_hash = input_hash
            packet = self.builder.build(normalized, entity_id)
            payload = self.builder.packet_payload(packet)
            output = {
                "entity_type": normalized,
                "entity_id": entity_id,
                "input_entities": self._input_entities(payload),
                "derived_entities": self._derived_entities(payload),
                "hashes": {"input_hash": input_hash, "output_hash": self._payload_hash(payload)},
                "scores": self._scores(payload),
                "confidence": payload["confidence_breakdown"],
                "policies_applied": self._policies(payload),
                "review_decisions": self._reviews(payload),
                "limitations": payload["limitations"],
                "timeline": payload["timeline"],
                "evidence_chain": payload["evidence_chain"],
                "integrity_status": payload["integrity_status"],
                "operator_review_status": payload["operator_review_status"],
                "publication_status": payload["publication_status"],
                "correlation_not_causation": True,
                "evidence_based": True,
                "replayable": True,
                "operator_reviewed": payload["operator_review_status"] != "none",
                "failures": [],
            }
            log.output_hash = output["hashes"]["output_hash"]
            log.success = True
            log.finished_at = utcnow()
            log.metadata_json = {"packet_id": packet.id, "timeline_steps": len(output["timeline"])}
            self.db.flush()
            publish_domain_event(
                self.db,
                "evidence.replay.completed",
                {
                    "packet_id": packet.id,
                    "source_entity_type": normalized,
                    "source_entity_id": entity_id,
                    "integrity_hash": output["hashes"]["output_hash"],
                    "replay_status": "completed",
                    "confidence": output.get("scores", {}).get("confidence_score"),
                    "limitations": output.get("limitations", []),
                    "operator_reviewed": bool(output.get("operator_reviewed")),
                    "publication_status": output.get("publication_status", "unknown"),
                },
                aggregate_type="evidence_replay",
                aggregate_id=log.id,
                source="evidence_replay_service",
                idempotency_key=f"evidence.replay.completed:{normalized}:{entity_id}:{output['hashes']['output_hash']}",
            )
            return output
        except Exception as exc:
            reason = self._bounded_reason(str(exc))
            log.input_hash = input_hash
            log.success = False
            log.error_code = reason
            log.finished_at = utcnow()
            log.metadata_json = {"error": reason, "failure_visible": True}
            self.db.flush()
            failure_output = {
                "entity_type": normalized,
                "entity_id": entity_id,
                "success": False,
                "failures": [
                    {"error_code": reason, "message": "Replay failed and the failure is exposed."}
                ],
                "correlation_not_causation": True,
                "evidence_based": False,
                "replayable": False,
                "operator_reviewed": False,
                "limitations": {"replay_failure_visible": True, "correlation_not_causation": True},
            }
            publish_domain_event(
                self.db,
                "evidence.replay.failed",
                {
                    "source_entity_type": normalized,
                    "source_entity_id": entity_id,
                    "replay_status": "failed",
                    "failure_reason": reason,
                    "limitations": failure_output["limitations"],
                    "operator_reviewed": False,
                    "evidence_based": False,
                    "replayable": False,
                },
                aggregate_type="evidence_replay",
                aggregate_id=log.id,
                source="evidence_replay_service",
                idempotency_key=f"evidence.replay.failed:{normalized}:{entity_id}:{log.id}",
            )
            EVIDENCE_REPLAY_FAILURES_TOTAL.labels(
                entity_type=self._bounded_entity(normalized), reason_code=reason
            ).inc()
            return failure_output

    def replay_timeline(self, entity_type: str, entity_id: int) -> list[dict[str, Any]]:
        return self.builder.timeline_for(entity_type, entity_id)

    def integrity(self, entity_type: str, entity_id: int) -> dict[str, Any]:
        normalized = self.builder.normalize_entity_type(entity_type)
        current_hash = self.builder.entity_hash(normalized, entity_id)
        snapshot = self.repo.latest_integrity_snapshot(normalized, entity_id)
        if snapshot is None:
            snapshot = self.builder.create_integrity_snapshot(normalized, entity_id)
            status = "created"
            matches = True
        else:
            matches = snapshot.content_hash == current_hash
            status = "match" if matches else "mismatch"
        EVIDENCE_INTEGRITY_CHECKS_TOTAL.labels(
            entity_type=self._bounded_entity(normalized), status=status
        ).inc()
        if not matches:
            EVIDENCE_INTEGRITY_MISMATCHES_TOTAL.labels(
                entity_type=self._bounded_entity(normalized)
            ).inc()
        return {
            "entity_type": normalized,
            "entity_id": entity_id,
            "hash_algorithm": "sha256",
            "latest_snapshot_hash": snapshot.content_hash,
            "current_hash": current_hash,
            "matches": matches,
            "status": status,
            "correlation_not_causation": True,
            "evidence_based": True,
            "replayable": True,
        }

    def export_replay(
        self, entity_type: str, entity_id: int, *, fmt: str = "json"
    ) -> dict[str, Any] | str:
        payload = self.replay(entity_type, entity_id)
        if fmt == "json":
            return payload
        if fmt != "markdown":
            raise ValueError("unsupported_export_format")
        limitations = payload.get("limitations", {})
        return (
            f"# Evidence Replay {payload.get('entity_type')}:{payload.get('entity_id')}\n\n"
            f"## Hashes\n{json.dumps(payload.get('hashes', {}), sort_keys=True)}\n\n"
            f"## Timeline steps\n{len(payload.get('timeline', []))}\n\n"
            f"## Limitations\n{json.dumps(limitations, sort_keys=True)}\n\n"
            "Correlation-based attribution is not proof of causation. Not financial advice."
        )

    def _payload_hash(self, payload: dict[str, Any]) -> str:
        import hashlib

        encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode(
            "utf-8"
        )
        return hashlib.sha256(encoded).hexdigest()

    def _input_entities(self, payload: dict[str, Any]) -> dict[str, Any]:
        return dict(payload.get("evidence_sources", {}))

    def _derived_entities(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        return list(payload.get("evidence_chain", []))

    def _scores(self, payload: dict[str, Any]) -> dict[str, Any]:
        summary = payload.get("evidence_summary", {})
        return {"confidence_score": summary.get("confidence_score")}

    def _policies(self, payload: dict[str, Any]) -> dict[str, Any]:
        breakdown = payload.get("confidence_breakdown", {})
        return {"policy_adjustments": breakdown.get("policy_adjustments")}

    def _reviews(self, payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "operator_review_status": payload.get("operator_review_status"),
            "operator_overrides": payload.get("confidence_breakdown", {}).get(
                "operator_overrides", []
            ),
        }

    def _bounded_entity(self, value: str) -> str:
        return (
            value
            if value in {"article", "event", "impact", "attribution", "signal", "publication"}
            else "other"
        )

    def _bounded_reason(self, value: str) -> str:
        return (
            value
            if value
            in {
                "evidence_entity_not_found",
                "unsupported_evidence_entity_type",
                "unsupported_export_format",
            }
            else "other"
        )
