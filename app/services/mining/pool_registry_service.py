from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.db.models.mining import MiningPool, MiningPoolEndpoint
from app.db.repositories.mining_repository import MiningRepository
from app.schemas.mining import MiningPoolEndpointCreate, MiningPoolRegistryMetadata


class MiningPoolRegistryService:
    """Service for managing mining pool registry records."""

    def __init__(self, repository: MiningRepository) -> None:
        self.repository = repository

    def list_pools(self, *, limit: int = 50, offset: int = 0) -> list[MiningPool]:
        return self.repository.list_pools(limit=limit, offset=offset)

    def get_pool_by_id(self, pool_id: int) -> MiningPool | None:
        return self.repository.get_pool(pool_id)

    def get_pool_by_name(self, pool_name: str) -> MiningPool | None:
        return self.repository.get_pool_by_name(pool_name)

    def upsert_pool_capability_metadata(self, metadata_record: dict[str, Any]) -> dict[str, Any]:
        pool_name = str(metadata_record.get("pool_name", "")).strip()
        if not pool_name:
            raise ValueError("pool_name is required")

        pool = self._resolve_or_create_pool(pool_name, metadata_record)
        endpoints_created = self._upsert_endpoints_from_metadata(pool.id, metadata_record)
        capability = self._persist_capability_from_metadata(pool.id, metadata_record)
        return {
            "pool_id": pool.id,
            "pool_key": pool.pool_key,
            "endpoint_count": len(endpoints_created),
            "capability_id": capability.id,
        }

    def register_pool(self, metadata: MiningPoolRegistryMetadata) -> MiningPool:
        as_dict = metadata.model_dump()
        pool_name = as_dict["pool_name"]
        pool_key = self._pool_key_from_name(pool_name)
        return self.repository.upsert_pool(
            pool_key=pool_key,
            display_name=pool_name,
            provider_name="pool_registry_service",
            source_type=as_dict.get("source_quality", "unknown"),
            confidence_score=float(as_dict.get("confidence", 0.0)),
            freshness_seconds=as_dict.get("freshness"),
            is_verified=False,
            is_fallback=False,
            is_synthetic=False,
            metadata=as_dict,
            observed_at=datetime.now(UTC),
        )

    def update_pool_metadata(self, pool_id: int, metadata: MiningPoolRegistryMetadata) -> MiningPool | None:
        current = self.repository.get_pool(pool_id)
        if current is None:
            return None

        as_dict = metadata.model_dump()
        return self.repository.upsert_pool(
            pool_key=current.pool_key,
            display_name=as_dict["pool_name"],
            provider_name=current.provider_name,
            source_type=as_dict.get("source_quality", current.source_type),
            confidence_score=float(as_dict.get("confidence", current.confidence_score)),
            freshness_seconds=as_dict.get("freshness", current.freshness_seconds),
            is_verified=current.is_verified,
            is_fallback=current.is_fallback,
            is_synthetic=current.is_synthetic,
            limitations=self._decode_json_list(current.limitations_json),
            evidence_refs=self._decode_json_list(current.evidence_refs_json),
            metadata=as_dict,
            observed_at=datetime.now(UTC),
        )

    def set_pool_active(self, pool_id: int, *, is_active: bool) -> MiningPool | None:
        current = self.repository.get_pool(pool_id)
        if current is None:
            return None

        current_metadata = self._decode_json_object(current.metadata_json)
        current_metadata["is_active"] = is_active
        return self.repository.upsert_pool(
            pool_key=current.pool_key,
            display_name=current.display_name,
            provider_name=current.provider_name,
            source_type=current.source_type,
            confidence_score=current.confidence_score,
            freshness_seconds=current.freshness_seconds,
            is_verified=current.is_verified,
            is_fallback=current.is_fallback,
            is_synthetic=current.is_synthetic,
            limitations=self._decode_json_list(current.limitations_json),
            evidence_refs=self._decode_json_list(current.evidence_refs_json),
            metadata=current_metadata,
            observed_at=datetime.now(UTC),
        )

    def attach_endpoints(self, pool_id: int, endpoints: list[MiningPoolEndpointCreate]) -> list[MiningPoolEndpoint]:
        attached: list[MiningPoolEndpoint] = []
        for endpoint in endpoints:
            created = self.repository.attach_pool_endpoint(
                pool_id=pool_id,
                endpoint_type=endpoint.endpoint_type,
                endpoint_url=endpoint.endpoint_url,
                network=endpoint.network,
                source_type=endpoint.source_type,
                confidence_score=endpoint.confidence,
                freshness_seconds=endpoint.freshness,
                is_verified=endpoint.is_verified,
                limitations=endpoint.limitations,
                evidence_refs=endpoint.evidence_refs,
                observed_at=datetime.now(UTC),
            )
            attached.append(created)
        return attached

    @staticmethod
    def _pool_key_from_name(name: str) -> str:
        normalized = "".join(ch.lower() if ch.isalnum() else "-" for ch in name).strip("-")
        while "--" in normalized:
            normalized = normalized.replace("--", "-")
        return normalized or "unknown-pool"

    @staticmethod
    def _decode_json_list(payload: Any) -> list[str]:
        if isinstance(payload, str):
            import json

            loaded = json.loads(payload)
            if isinstance(loaded, list):
                return [str(item) for item in loaded]
        return []

    @staticmethod
    def _decode_json_object(payload: Any) -> dict[str, Any]:
        if isinstance(payload, str):
            import json

            loaded = json.loads(payload)
            if isinstance(loaded, dict):
                return dict(loaded)
        if isinstance(payload, dict):
            return dict(payload)
        return {}

    def _resolve_or_create_pool(self, pool_name: str, metadata_record: dict[str, Any]) -> MiningPool:
        normalized = self._pool_key_from_name(pool_name)
        existing = self.repository.upsert_pool(
            pool_key=normalized,
            display_name=pool_name,
            provider_name=str(metadata_record.get("provider_name", "pool_registry_service")),
            source_type=str(metadata_record.get("source_type", "unknown")),
            confidence_score=float(metadata_record.get("confidence", 0.0)),
            freshness_seconds=metadata_record.get("freshness"),
            is_verified=bool(metadata_record.get("is_verified", False)),
            is_fallback=bool(metadata_record.get("is_fallback", False)),
            is_synthetic=bool(metadata_record.get("is_synthetic", False)),
            limitations=list(metadata_record.get("limitations", [])),
            evidence_refs=list(metadata_record.get("evidence_refs", [])),
            metadata=metadata_record,
            observed_at=datetime.now(UTC),
        )
        return existing

    def _upsert_endpoints_from_metadata(self, pool_id: int, metadata_record: dict[str, Any]) -> list[MiningPoolEndpoint]:
        created: list[MiningPoolEndpoint] = []
        endpoints = metadata_record.get("endpoints", [])
        if not isinstance(endpoints, list):
            return created
        for endpoint in endpoints:
            if not isinstance(endpoint, dict):
                continue
            endpoint_type = str(endpoint.get("endpoint_type", "api"))
            endpoint_url = str(endpoint.get("endpoint_url", "")).strip()
            if not endpoint_url:
                continue
            network = str(endpoint.get("network", "unknown"))
            duplicate = self.repository.get_pool_endpoint(
                pool_id=pool_id,
                endpoint_type=endpoint_type,
                endpoint_url=endpoint_url,
                network=network,
            )
            if duplicate is not None:
                continue
            created.append(
                self.repository.attach_pool_endpoint(
                    pool_id=pool_id,
                    endpoint_type=endpoint_type,
                    endpoint_url=endpoint_url,
                    network=network,
                    source_type=str(endpoint.get("source_type", metadata_record.get("source_type", "unknown"))),
                    confidence_score=float(endpoint.get("confidence", metadata_record.get("confidence", 0.0))),
                    freshness_seconds=endpoint.get("freshness", metadata_record.get("freshness")),
                    is_verified=bool(endpoint.get("is_verified", metadata_record.get("is_verified", False))),
                    limitations=list(endpoint.get("limitations", metadata_record.get("limitations", []))),
                    evidence_refs=list(endpoint.get("evidence_refs", metadata_record.get("evidence_refs", []))),
                    observed_at=datetime.now(UTC),
                )
            )
        return created

    def _persist_capability_from_metadata(self, pool_id: int, metadata_record: dict[str, Any]) -> Any:
        capability_claims = metadata_record.get("capability_claims", {})
        if not isinstance(capability_claims, dict):
            capability_claims = {}
        capability_state = str(capability_claims.get("supports_stratum_v2", "unknown"))
        job_declaration_state = str(capability_claims.get("supports_job_declaration", "unknown"))
        translator_proxy_state = str(capability_claims.get("supports_translator_proxy", "unknown"))
        encrypted_channel_state = str(capability_claims.get("supports_encrypted_channel", "unknown"))
        source_type = str(metadata_record.get("source_type", "unknown"))
        confidence_score = float(metadata_record.get("confidence", 0.0))
        freshness_seconds = metadata_record.get("freshness")
        limitations = list(metadata_record.get("limitations", []))
        evidence_refs = list(metadata_record.get("evidence_refs", []))

        latest = self.repository.latest_stratum_v2_capability(pool_id)
        if (
            latest is not None
            and latest.capability_state == capability_state
            and latest.job_declaration_state == job_declaration_state
            and latest.translator_proxy_state == translator_proxy_state
            and latest.encrypted_channel_state == encrypted_channel_state
            and latest.source_type == source_type
            and latest.confidence_score == confidence_score
            and latest.freshness_seconds == freshness_seconds
            and self._decode_json_list(latest.limitations_json) == limitations
            and self._decode_json_list(latest.evidence_refs_json) == evidence_refs
        ):
            return latest

        return self.repository.save_stratum_v2_capability(
            pool_id=pool_id,
            capability_state=capability_state,
            job_declaration_state=job_declaration_state,
            translator_proxy_state=translator_proxy_state,
            encrypted_channel_state=encrypted_channel_state,
            source_type=source_type,
            confidence_score=confidence_score,
            freshness_seconds=freshness_seconds,
            limitations=limitations,
            evidence_refs=evidence_refs,
            observed_at=datetime.now(UTC),
        )
