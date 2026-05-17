import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models.mining import (
    MiningCensorshipRisk,
    MiningPool,
    MiningPoolEndpoint,
    MiningSignal,
    PoolSovereigntyScore,
    StratumV2Capability,
    TemplateControlAssessment,
)


class MiningRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_pools(self, *, limit: int = 50, offset: int = 0) -> list[MiningPool]:
        stmt = select(MiningPool).order_by(MiningPool.updated_at.desc(), MiningPool.id.desc()).limit(limit).offset(offset)
        try:
            return list(self.db.execute(stmt).scalars())
        except SQLAlchemyError:
            return []

    def get_pool(self, pool_id: int) -> MiningPool | None:
        stmt = select(MiningPool).where(MiningPool.id == pool_id).limit(1)
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def get_pool_by_name(self, name: str) -> MiningPool | None:
        stmt = select(MiningPool).where(MiningPool.display_name == name).order_by(MiningPool.id.desc()).limit(1)
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def upsert_pool(
        self,
        *,
        pool_key: str,
        display_name: str,
        provider_name: str = "unknown",
        source_type: str = "unknown",
        confidence_score: float = 0.0,
        freshness_seconds: int | None = None,
        is_verified: bool = False,
        is_fallback: bool = False,
        is_synthetic: bool = False,
        limitations: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        metadata: dict[str, object] | None = None,
        observed_at: datetime | None = None,
    ) -> MiningPool:
        row = self.db.execute(select(MiningPool).where(MiningPool.pool_key == pool_key)).scalar_one_or_none()
        if row is None:
            row = MiningPool(pool_key=pool_key, display_name=display_name)
            self.db.add(row)

        row.display_name = display_name
        row.provider_name = provider_name
        row.source_type = source_type
        row.confidence_score = confidence_score
        row.freshness_seconds = freshness_seconds
        row.is_verified = is_verified
        row.is_fallback = is_fallback
        row.is_synthetic = is_synthetic
        row.limitations_json = json.dumps(limitations or [])
        row.evidence_refs_json = json.dumps(evidence_refs or [])
        row.metadata_json = json.dumps(metadata or {})
        row.observed_at = observed_at

        self.db.commit()
        self.db.refresh(row)
        return row

    def list_pool_endpoints(self, pool_id: int) -> list[MiningPoolEndpoint]:
        stmt = (
            select(MiningPoolEndpoint)
            .where(MiningPoolEndpoint.pool_id == pool_id)
            .order_by(MiningPoolEndpoint.updated_at.desc(), MiningPoolEndpoint.id.desc())
        )
        try:
            return list(self.db.execute(stmt).scalars())
        except SQLAlchemyError:
            return []

    def attach_pool_endpoint(
        self,
        *,
        pool_id: int,
        endpoint_type: str = "api",
        endpoint_url: str,
        network: str = "unknown",
        source_type: str = "unknown",
        confidence_score: float = 0.0,
        freshness_seconds: int | None = None,
        is_verified: bool = False,
        limitations: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        observed_at: datetime | None = None,
    ) -> MiningPoolEndpoint:
        row = MiningPoolEndpoint(
            pool_id=pool_id,
            endpoint_type=endpoint_type,
            endpoint_url=endpoint_url,
            network=network,
            source_type=source_type,
            confidence_score=confidence_score,
            freshness_seconds=freshness_seconds,
            is_verified=is_verified,
            limitations_json=json.dumps(limitations or []),
            evidence_refs_json=json.dumps(evidence_refs or []),
            observed_at=observed_at,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_pool_endpoint(
        self,
        *,
        pool_id: int,
        endpoint_type: str,
        endpoint_url: str,
        network: str,
    ) -> MiningPoolEndpoint | None:
        stmt = (
            select(MiningPoolEndpoint)
            .where(MiningPoolEndpoint.pool_id == pool_id)
            .where(MiningPoolEndpoint.endpoint_type == endpoint_type)
            .where(MiningPoolEndpoint.endpoint_url == endpoint_url)
            .where(MiningPoolEndpoint.network == network)
            .order_by(MiningPoolEndpoint.id.desc())
            .limit(1)
        )
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def upsert_stratum_v2_capability(
        self,
        *,
        pool_id: int,
        capability_state: str = "unknown",
        job_declaration_state: str = "unknown",
        translator_proxy_state: str = "unknown",
        encrypted_channel_state: str = "unknown",
        source_type: str = "unknown",
        confidence_score: float = 0.0,
        freshness_seconds: int | None = None,
        limitations: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        observed_at: datetime | None = None,
    ) -> StratumV2Capability:
        stmt = (
            select(StratumV2Capability)
            .where(StratumV2Capability.pool_id == pool_id)
            .order_by(StratumV2Capability.created_at.desc(), StratumV2Capability.id.desc())
            .limit(1)
        )
        row = self.db.execute(stmt).scalar_one_or_none()
        if row is None:
            row = StratumV2Capability(pool_id=pool_id)
            self.db.add(row)

        row.capability_state = capability_state
        row.job_declaration_state = job_declaration_state
        row.translator_proxy_state = translator_proxy_state
        row.encrypted_channel_state = encrypted_channel_state
        row.source_type = source_type
        row.confidence_score = confidence_score
        row.freshness_seconds = freshness_seconds
        row.limitations_json = json.dumps(limitations or [])
        row.evidence_refs_json = json.dumps(evidence_refs or [])
        row.observed_at = observed_at

        self.db.commit()
        self.db.refresh(row)
        return row

    def save_stratum_v2_capability(
        self,
        *,
        pool_id: int,
        capability_state: str = "unknown",
        job_declaration_state: str = "unknown",
        translator_proxy_state: str = "unknown",
        encrypted_channel_state: str = "unknown",
        source_type: str = "unknown",
        confidence_score: float = 0.0,
        freshness_seconds: int | None = None,
        limitations: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        observed_at: datetime | None = None,
    ) -> StratumV2Capability:
        row = StratumV2Capability(
            pool_id=pool_id,
            capability_state=capability_state,
            job_declaration_state=job_declaration_state,
            translator_proxy_state=translator_proxy_state,
            encrypted_channel_state=encrypted_channel_state,
            source_type=source_type,
            confidence_score=confidence_score,
            freshness_seconds=freshness_seconds,
            limitations_json=json.dumps(limitations or []),
            evidence_refs_json=json.dumps(evidence_refs or []),
            observed_at=observed_at,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def latest_stratum_v2_capability(self, pool_id: int) -> StratumV2Capability | None:
        stmt = (
            select(StratumV2Capability)
            .where(StratumV2Capability.pool_id == pool_id)
            .order_by(StratumV2Capability.created_at.desc(), StratumV2Capability.id.desc())
            .limit(1)
        )
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def list_latest_stratum_v2_capabilities(self) -> list[StratumV2Capability]:
        pools = self.list_pools(limit=10000, offset=0)
        latest: list[StratumV2Capability] = []
        for pool in pools:
            item = self.latest_stratum_v2_capability(pool.id)
            if item is not None:
                latest.append(item)
        return latest

    def latest_pool_score(self, pool_id: int) -> PoolSovereigntyScore | None:
        stmt = (
            select(PoolSovereigntyScore)
            .where(PoolSovereigntyScore.pool_id == pool_id)
            .order_by(PoolSovereigntyScore.generated_at.desc(), PoolSovereigntyScore.id.desc())
            .limit(1)
        )
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def save_pool_score(
        self,
        *,
        pool_id: int,
        score_100: float,
        severity: str = "unknown",
        factor_breakdown: list[dict[str, object]] | None = None,
        explainability: dict[str, object] | None = None,
        source_type: str = "unknown",
        confidence_score: float = 0.0,
        freshness_seconds: int | None = None,
        is_verified: bool = False,
        is_fallback: bool = False,
        is_synthetic: bool = False,
        limitations: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> PoolSovereigntyScore:
        row = PoolSovereigntyScore(
            pool_id=pool_id,
            score_100=score_100,
            severity=severity,
            factor_breakdown_json=json.dumps(factor_breakdown or []),
            explainability_json=json.dumps(explainability or {}),
            source_type=source_type,
            confidence_score=confidence_score,
            freshness_seconds=freshness_seconds,
            is_verified=is_verified,
            is_fallback=is_fallback,
            is_synthetic=is_synthetic,
            limitations_json=json.dumps(limitations or []),
            evidence_refs_json=json.dumps(evidence_refs or []),
            window_start=window_start,
            window_end=window_end,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def latest_censorship_risk(self, pool_id: int) -> MiningCensorshipRisk | None:
        stmt = (
            select(MiningCensorshipRisk)
            .where(MiningCensorshipRisk.pool_id == pool_id)
            .order_by(MiningCensorshipRisk.generated_at.desc(), MiningCensorshipRisk.id.desc())
            .limit(1)
        )
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def save_censorship_risk(
        self,
        *,
        pool_id: int,
        risk_score_100: float,
        risk_level: str = "unknown",
        factor_breakdown: list[dict[str, object]] | None = None,
        explainability: dict[str, object] | None = None,
        source_type: str = "unknown",
        confidence_score: float = 0.0,
        freshness_seconds: int | None = None,
        is_verified: bool = False,
        is_fallback: bool = False,
        is_synthetic: bool = False,
        limitations: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        window_start: datetime | None = None,
        window_end: datetime | None = None,
    ) -> MiningCensorshipRisk:
        row = MiningCensorshipRisk(
            pool_id=pool_id,
            risk_score_100=risk_score_100,
            risk_level=risk_level,
            factor_breakdown_json=json.dumps(factor_breakdown or []),
            explainability_json=json.dumps(explainability or {}),
            source_type=source_type,
            confidence_score=confidence_score,
            freshness_seconds=freshness_seconds,
            is_verified=is_verified,
            is_fallback=is_fallback,
            is_synthetic=is_synthetic,
            limitations_json=json.dumps(limitations or []),
            evidence_refs_json=json.dumps(evidence_refs or []),
            window_start=window_start,
            window_end=window_end,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def latest_template_control_assessment(self, pool_id: int) -> TemplateControlAssessment | None:
        stmt = (
            select(TemplateControlAssessment)
            .where(TemplateControlAssessment.pool_id == pool_id)
            .order_by(TemplateControlAssessment.observed_at.desc(), TemplateControlAssessment.id.desc())
            .limit(1)
        )
        try:
            return self.db.execute(stmt).scalar_one_or_none()
        except SQLAlchemyError:
            return None

    def save_template_control_assessment(
        self,
        *,
        pool_id: int,
        template_control_state: str = "unknown",
        template_control_owner: str = "unknown",
        template_sovereignty_score_100: float = 0.0,
        template_interference_risk_score_100: float = 0.0,
        mitm_risk_level: str = "unknown",
        explainability: dict[str, object] | None = None,
        source_type: str = "unknown",
        confidence_score: float = 0.0,
        freshness_seconds: int | None = None,
        is_verified: bool = False,
        is_fallback: bool = False,
        is_synthetic: bool = False,
        limitations: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        observed_at: datetime | None = None,
    ) -> TemplateControlAssessment:
        row = TemplateControlAssessment(
            pool_id=pool_id,
            template_control_state=template_control_state,
            template_control_owner=template_control_owner,
            template_sovereignty_score_100=template_sovereignty_score_100,
            template_interference_risk_score_100=template_interference_risk_score_100,
            mitm_risk_level=mitm_risk_level,
            explainability_json=json.dumps(explainability or {}),
            source_type=source_type,
            confidence_score=confidence_score,
            freshness_seconds=freshness_seconds,
            is_verified=is_verified,
            is_fallback=is_fallback,
            is_synthetic=is_synthetic,
            limitations_json=json.dumps(limitations or []),
            evidence_refs_json=json.dumps(evidence_refs or []),
            observed_at=observed_at,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def save_mining_signal(
        self,
        *,
        signal_type: str,
        severity: str = "unknown",
        title: str = "",
        summary: str = "",
        pool_id: int | None = None,
        source_type: str = "unknown",
        provider_name: str = "unknown",
        confidence_score: float = 0.0,
        freshness_seconds: int | None = None,
        is_verified: bool = False,
        is_fallback: bool = False,
        is_synthetic: bool = False,
        explainability: dict[str, object] | None = None,
        limitations: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        observed_at: datetime | None = None,
    ) -> MiningSignal:
        row = MiningSignal(
            signal_type=signal_type,
            severity=severity,
            title=title,
            summary=summary,
            pool_id=pool_id,
            source_type=source_type,
            provider_name=provider_name,
            confidence_score=confidence_score,
            freshness_seconds=freshness_seconds,
            is_verified=is_verified,
            is_fallback=is_fallback,
            is_synthetic=is_synthetic,
            explainability_json=json.dumps(explainability or {}),
            limitations_json=json.dumps(limitations or []),
            evidence_refs_json=json.dumps(evidence_refs or []),
            observed_at=observed_at,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def list_mining_signals(
        self,
        *,
        pool_id: int | None = None,
        signal_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[MiningSignal]:
        stmt = select(MiningSignal)
        if pool_id is not None:
            stmt = stmt.where(MiningSignal.pool_id == pool_id)
        if signal_type is not None:
            stmt = stmt.where(MiningSignal.signal_type == signal_type)
        stmt = stmt.order_by(MiningSignal.observed_at.desc(), MiningSignal.id.desc()).limit(limit).offset(offset)
        try:
            return list(self.db.execute(stmt).scalars())
        except SQLAlchemyError:
            return []
