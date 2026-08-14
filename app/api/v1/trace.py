import hashlib
import json
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.api.access_dependencies import (
    require_any_plan,
    require_human_intent,
    require_metric_entitlement,
    require_plan,
    require_scope,
)
from app.api.dependencies import db_session
from app.domain.access.context import AccessContext
from app.domain.access.plans import PlanCode
from app.db.repositories.bastion_trace_repository import BastionTraceRepository
from app.schemas.base import ResponseEnvelope
from app.schemas.bastion_trace import (
    BastionTraceRegisterAdvisoryRequest,
    BastionTraceTreasuryCheckRequest,
    BatchTraceRequest,
    EvidenceAccessRequest,
    PaymentContextRiskRequest,
    TraceBand,
    TraceEvidence,
    TraceFreshness,
    TraceReport,
    TraceSourceQuality,
    TraceSourceStatus,
    TraceSubmitRequest,
    TraceSubmissionResult,
    TraceWatchlistCreate,
    TraceWatchlistEntry,
)
from app.services.bastion_trace.trace_service import TraceService

router = APIRouter(prefix="/trace", tags=["trace"])
_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{16,128}$")


@router.post("/submit", response_model=ResponseEnvelope[TraceSubmissionResult], status_code=201)
def submit_trace(
    payload: TraceSubmitRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    db: Session = Depends(db_session),
) -> ResponseEnvelope[TraceSubmissionResult]:
    """Synchronously create an advisory report with durable retry identity.

    Feature 21 is a public-address workflow, so current canonical policy requires
    neither PoP nor Human Intent. The mutation is nevertheless audited by the
    domain event and requires an idempotency key.
    """
    if not _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        raise HTTPException(status_code=400, detail="Invalid Idempotency-Key")
    key_hash = hashlib.sha256(idempotency_key.encode()).hexdigest()
    repo = BastionTraceRepository(db)
    existing = repo.get_report_by_idempotency_hash(key_hash)
    if existing is not None:
        if existing.address != payload.subject.strip():
            raise HTTPException(status_code=409, detail="Idempotency key conflicts with request")
        return ResponseEnvelope(
            data=TraceSubmissionResult(
                trace_id=existing.id,
                report_id=existing.id,
                normalized_subject=existing.address,
                idempotency_replayed=True,
            )
        )
    try:
        report = TraceService(repo).analyze_address(
            payload.subject, idempotency_key_hash=key_hash
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Unsupported public Bitcoin address") from exc
    assert report.id is not None
    return ResponseEnvelope(
        data=TraceSubmissionResult(
            trace_id=report.id,
            report_id=report.id,
            normalized_subject=report.address,
        )
    )


@router.get("/address/{address}", response_model=ResponseEnvelope[TraceReport])
def analyze_address(
    address: str, db: Session = Depends(db_session)
) -> ResponseEnvelope[TraceReport]:
    service = TraceService(BastionTraceRepository(db))
    try:
        return ResponseEnvelope(data=service.analyze_address(address))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/report/{report_id}", response_model=ResponseEnvelope[TraceReport])
def get_report(report_id: int, db: Session = Depends(db_session)) -> ResponseEnvelope[TraceReport]:
    repo = BastionTraceRepository(db)
    item = repo.get_report(report_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(
        data=TraceReport(
            id=item.id,
            address=item.address,
            summary=item.summary,
            chain=item.chain,
            trace_score=item.trace_score,
            trace_band=TraceBand(item.trace_band),
            confidence=item.confidence,
            source_quality=TraceSourceQuality(item.source_quality),
            freshness=TraceFreshness(item.freshness),
            reason_codes=json.loads(item.reason_codes_json),
            evidence_refs=json.loads(item.evidence_refs_json),
            limitations=json.loads(item.limitations_json),
            operator_guidance=json.loads(item.operator_guidance_json),
            trace_dna=None,
            factor_contributions=[],
            confidence_ledger=[],
            score_breakdown=None,
            advisory_not_legal_verdict=item.advisory_not_legal_verdict,
            not_consensus_proof=item.not_consensus_proof,
            no_custody=item.no_custody,
            created_at=item.created_at,
        )
    )


@router.get("/report/{report_id}/evidence", response_model=ResponseEnvelope[list[TraceEvidence]])
def list_evidence(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[list[TraceEvidence]]:
    repo = BastionTraceRepository(db)
    items = [
        TraceEvidence(
            id=i.id,
            report_id=i.report_id,
            evidence_type=i.evidence_type,
            source_name=i.source_name,
            source_type=i.source_type,
            confidence=i.confidence,
            freshness_days=i.freshness_days,
            description=i.description,
            limitations=json.loads(i.limitations_json),
            evidence_ref=i.evidence_ref,
            created_at=i.created_at,
        )
        for i in repo.list_evidence(report_id)
    ]
    return ResponseEnvelope(data=items)


@router.get("/report/{report_id}/proof-packet", response_model=ResponseEnvelope[dict[str, object]])
def get_proof_packet(
    report_id: int,
    access_context: AccessContext = Depends(require_scope("evidence:packet:create")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    repo = BastionTraceRepository(db)
    report = repo.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    report_refs = json.loads(report.evidence_refs_json or "[]")
    evidence_refs = [
        {
            "id": item.id,
            "evidence_ref": item.evidence_ref,
            "evidence_type": item.evidence_type,
            "source_name": item.source_name,
            "source_type": item.source_type,
            "confidence": item.confidence,
            "freshness_days": item.freshness_days,
            "description": item.description,
            "limitations": json.loads(item.limitations_json or "[]"),
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in repo.list_evidence(report_id)
    ]
    return ResponseEnvelope(
        data={
            "report_id": report_id,
            "address": report.address,
            "trace_band": report.trace_band,
            "trace_score": report.trace_score,
            "confidence": report.confidence,
            "advisory_only": True,
            "not_legal_verification": True,
            "not_bitcoin_consensus_proof": True,
            "no_custody": True,
            "signed": False,
            "signature_available": False,
            "signature_status": "unsigned",
            "packet_type": "application_level_evidence_summary",
            "evidence_refs": evidence_refs,
            "report_evidence_refs": report_refs,
            "limitations": [
                "Proof packet is an application-level evidence summary.",
                "This is not Bitcoin consensus proof.",
                "This is not legal verification.",
                "Cryptographic signing is not available unless explicitly configured.",
            ],
            "operator_guidance": [
                "Use this packet as advisory evidence context only.",
                "Verify counterparties and evidence independently before operational decisions.",
            ],
            "created_at": report.created_at.isoformat() if report.created_at else None,
        }
    )


@router.get("/sources", response_model=ResponseEnvelope[list[TraceSourceStatus]])
def list_sources(db: Session = Depends(db_session)) -> ResponseEnvelope[list[TraceSourceStatus]]:
    repo = BastionTraceRepository(db)
    return ResponseEnvelope(
        data=[
            TraceSourceStatus(
                id=s.id,
                source_name=s.source_name,
                source_type=s.source_type,
                trust_level=s.trust_level,
                enabled=s.enabled,
                limitations=json.loads(s.limitations_json),
            )
            for s in repo.list_sources()
        ]
    )


@router.get("/watchlist", response_model=ResponseEnvelope[list[TraceWatchlistEntry]])
def list_watchlist(
    access_context: AccessContext = Depends(require_scope("trace:standard:read")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[TraceWatchlistEntry]]:
    repo = BastionTraceRepository(db)
    return ResponseEnvelope(
        data=[
            TraceWatchlistEntry.model_validate(w, from_attributes=True)
            for w in repo.list_watchlist_entries()
        ]
    )


@router.post("/watchlist", response_model=ResponseEnvelope[TraceWatchlistEntry])
def add_watchlist(
    payload: TraceWatchlistCreate,
    access_context: AccessContext = Depends(require_scope("trace:standard:read")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[TraceWatchlistEntry]:
    service = TraceService(BastionTraceRepository(db))
    try:
        address = service._validate_public_address(payload.address)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    entry = BastionTraceRepository(db).add_watchlist_entry(
        address, payload.label, payload.reason, payload.risk_hint
    )
    return ResponseEnvelope(data=TraceWatchlistEntry.model_validate(entry, from_attributes=True))


@router.get("/sources/{source_name}", response_model=ResponseEnvelope[TraceSourceStatus])
def get_source(
    source_name: str, db: Session = Depends(db_session)
) -> ResponseEnvelope[TraceSourceStatus]:
    service = TraceService(BastionTraceRepository(db))
    src = service.source_registry.get_source(source_name)
    if src is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return ResponseEnvelope(data=src)


@router.get(
    "/report/{report_id}/origin-passport", response_model=ResponseEnvelope[dict[str, object]]
)
def get_origin_passport(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    data = service.get_origin_passport(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=data)


@router.get(
    "/report/{report_id}/source-summary", response_model=ResponseEnvelope[list[dict[str, object]]]
)
def get_source_summary(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[list[dict[str, object]]]:
    service = TraceService(BastionTraceRepository(db))
    return ResponseEnvelope(data=service.get_source_summary(report_id))


@router.get(
    "/report/{report_id}/provider-disagreement", response_model=ResponseEnvelope[dict[str, object]]
)
def get_provider_disagreement(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    data = service.get_provider_disagreement(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=data)


@router.get(
    "/report/{report_id}/privacy-shield", response_model=ResponseEnvelope[dict[str, object]]
)
def get_privacy_shield(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    data = service.get_privacy_shield(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=data)


@router.get("/report/{report_id}/utxo-hygiene", response_model=ResponseEnvelope[dict[str, object]])
def get_utxo_hygiene(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    data = service.get_utxo_hygiene(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=data)


@router.get("/report/{report_id}/dust-radar", response_model=ResponseEnvelope[dict[str, object]])
def get_dust_radar(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    data = service.get_dust_radar(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=data)


@router.get(
    "/report/{report_id}/counterparty-lens", response_model=ResponseEnvelope[dict[str, object]]
)
def get_counterparty_lens(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    data = service.get_counterparty_lens(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=data)


@router.post("/payment-context", response_model=ResponseEnvelope[dict[str, object]])
def payment_context(
    payload: PaymentContextRiskRequest,
    access_context: AccessContext = Depends(require_metric_entitlement("trace.standard")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    return ResponseEnvelope(data=service.evaluate_payment_context(payload))


@router.post("/payment-intent/preview", response_model=ResponseEnvelope[dict[str, object]])
def payment_intent_preview(
    payload: PaymentContextRiskRequest,
    access_context: AccessContext = Depends(require_metric_entitlement("trace.standard")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    return ResponseEnvelope(data=service.preview_payment_intent(payload))


@router.post("/destination-review", response_model=ResponseEnvelope[dict[str, object]])
def destination_review(
    payload: PaymentContextRiskRequest,
    access_context: AccessContext = Depends(require_metric_entitlement("trace.advanced")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    return ResponseEnvelope(data=service.destination_review(payload))


@router.get("/lite/{address}", response_model=ResponseEnvelope[dict[str, object]])
def lite_address_check(
    address: str, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    try:
        return ResponseEnvelope(data=service.build_lite_report(address))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/business/profile", response_model=ResponseEnvelope[dict[str, object]])
def business_profile(
    access_context: AccessContext = Depends(
        require_any_plan([PlanCode.BUSINESS, PlanCode.ENTERPRISE])
    ),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).get_business_tier_profile()
    )


@router.post("/business/batch", response_model=ResponseEnvelope[dict[str, object]])
def business_batch(
    payload: BatchTraceRequest,
    access_context: AccessContext = Depends(
        require_any_plan([PlanCode.BUSINESS, PlanCode.ENTERPRISE])
    ),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    service = TraceService(BastionTraceRepository(db))
    try:
        return ResponseEnvelope(data=service.screen_batch(payload))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/business/policy-profiles", response_model=ResponseEnvelope[list[dict[str, object]]])
def business_policy_profiles(
    access_context: AccessContext = Depends(
        require_any_plan([PlanCode.BUSINESS, PlanCode.ENTERPRISE])
    ),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[dict[str, object]]]:
    return ResponseEnvelope(data=TraceService(BastionTraceRepository(db)).list_policy_profiles())


@router.get("/business/events", response_model=ResponseEnvelope[list[dict[str, object]]])
def business_events(
    access_context: AccessContext = Depends(
        require_any_plan([PlanCode.BUSINESS, PlanCode.ENTERPRISE])
    ),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[dict[str, object]]]:
    items = BastionTraceRepository(db).list_business_events()
    return ResponseEnvelope(
        data=[
            {
                "id": i.id,
                "event_type": i.event_type,
                "payload": json.loads(i.payload_json),
                "delivered": i.delivered,
                "created_at": i.created_at,
            }
            for i in items
        ]
    )


@router.get("/enterprise/profile", response_model=ResponseEnvelope[dict[str, object]])
def enterprise_profile(
    access_context: AccessContext = Depends(require_plan(PlanCode.ENTERPRISE)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).get_enterprise_tier_profile()
    )


@router.get("/enterprise/rbac/roles", response_model=ResponseEnvelope[list[str]])
def enterprise_roles(
    access_context: AccessContext = Depends(require_plan(PlanCode.ENTERPRISE)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[str]]:
    return ResponseEnvelope(data=TraceService(BastionTraceRepository(db)).list_enterprise_roles())


@router.get("/enterprise/rbac/permissions", response_model=ResponseEnvelope[list[str]])
def enterprise_permissions(
    access_context: AccessContext = Depends(require_plan(PlanCode.ENTERPRISE)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[list[str]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).list_enterprise_permissions()
    )


@router.get("/enterprise/rbac/default-policy", response_model=ResponseEnvelope[dict[str, object]])
def enterprise_default_policy(
    access_context: AccessContext = Depends(require_plan(PlanCode.ENTERPRISE)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).get_enterprise_default_policy()
    )


@router.get("/enterprise/sso", response_model=ResponseEnvelope[dict[str, object]])
def enterprise_sso(
    access_context: AccessContext = Depends(require_plan(PlanCode.ENTERPRISE)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(data=TraceService(BastionTraceRepository(db)).get_sso_placeholder())


@router.post(
    "/enterprise/evidence-access/evaluate", response_model=ResponseEnvelope[dict[str, object]]
)
def enterprise_evidence_access(
    payload: EvidenceAccessRequest,
    access_context: AccessContext = Depends(require_plan(PlanCode.ENTERPRISE)),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).evaluate_evidence_access_enterprise(payload)
    )


@router.post("/enterprise/proof-packet", response_model=ResponseEnvelope[dict[str, object]])
def enterprise_proof_packet(
    report_id: int,
    access_context: AccessContext = Depends(require_human_intent("export_data")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).create_enterprise_proof_packet(report_id)
    )


@router.get(
    "/report/{report_id}/citadel-contribution", response_model=ResponseEnvelope[dict[str, object]]
)
def trace_citadel_contribution(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    data = TraceService(BastionTraceRepository(db)).get_citadel_contribution(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=data)


@router.get("/report/{report_id}/policy-facts", response_model=ResponseEnvelope[dict[str, object]])
def trace_policy_facts(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    data = TraceService(BastionTraceRepository(db)).get_policy_facts(report_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace report not found")
    return ResponseEnvelope(data=data)


@router.post("/treasury/destination-check", response_model=ResponseEnvelope[dict[str, object]])
def trace_treasury_check(
    payload: BastionTraceTreasuryCheckRequest,
    access_context: AccessContext = Depends(require_scope("treasury:read")),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).treasury_destination_check(payload)
    )


@router.post("/register/payment-advisory", response_model=ResponseEnvelope[dict[str, object]])
def trace_register_advisory(
    payload: BastionTraceRegisterAdvisoryRequest,
    access_context: AccessContext = Depends(
        require_any_plan([PlanCode.BUSINESS, PlanCode.ENTERPRISE])
    ),
    db: Session = Depends(db_session),
) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).register_payment_advisory(payload)
    )


@router.get(
    "/report/{report_id}/evidence-refs", response_model=ResponseEnvelope[list[dict[str, object]]]
)
def trace_evidence_refs(
    report_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[list[dict[str, object]]]:
    return ResponseEnvelope(
        data=TraceService(BastionTraceRepository(db)).get_evidence_refs(report_id)
    )


@router.get("/status", response_model=ResponseEnvelope[dict[str, object]])
def trace_status(db: Session = Depends(db_session)) -> ResponseEnvelope[dict[str, object]]:
    return ResponseEnvelope(data=TraceService(BastionTraceRepository(db)).get_trace_status())


@router.get("/events", response_model=ResponseEnvelope[list[dict[str, object]]])
def trace_events(db: Session = Depends(db_session)) -> ResponseEnvelope[list[dict[str, object]]]:
    return ResponseEnvelope(data=TraceService(BastionTraceRepository(db)).list_runtime_events())


@router.get("/events/{event_id}", response_model=ResponseEnvelope[dict[str, object]])
def trace_event(
    event_id: int, db: Session = Depends(db_session)
) -> ResponseEnvelope[dict[str, object]]:
    data = TraceService(BastionTraceRepository(db)).get_runtime_event(event_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Trace event not found")
    return ResponseEnvelope(data=data)


@router.get("/alerts", response_model=ResponseEnvelope[list[dict[str, object]]])
def trace_alerts(db: Session = Depends(db_session)) -> ResponseEnvelope[list[dict[str, object]]]:
    return ResponseEnvelope(data=TraceService(BastionTraceRepository(db)).list_trace_alerts())
