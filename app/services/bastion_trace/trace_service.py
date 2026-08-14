import json
from datetime import UTC, datetime
import re
from typing import cast

from app.db.models.bastion_trace import (
    TraceBatch,
    TraceBatchItem,
    TraceBusinessEventModel,
    TraceBusinessPolicyProfileModel,
    TraceReport,
)
from app.db.repositories.bastion_trace_repository import BastionTraceRepository
from app.schemas.bastion_trace import (
    OriginPassport,
    PaymentContextRiskReport,
    TraceReasonCode,
    TraceReport as TraceReportSchema,
    TraceScoreBreakdown,
    TraceScoringInput,
)
from app.services.bastion_trace.evidence_independence import EvidenceIndependenceService
from app.services.bastion_trace.origin_passport import build_origin_passport
from app.services.bastion_trace.provider_disagreement import ProviderDisagreementService
from app.services.bastion_trace.reason_codes import BASELINE_REASONS
from app.services.bastion_trace.risk_source_registry import RiskSourceRegistryService
from app.services.bastion_trace.scoring import score_trace
from app.services.bastion_trace.lite_report import LiteTraceReportService
from app.services.bastion_trace.privacy_shield import PrivacyShieldService
from app.services.bastion_trace.counterparty_lens import build_counterparty_lens
from app.services.bastion_trace.payment_context_risk import evaluate_payment_context
from app.services.bastion_trace.payment_intent_preview import preview
from app.services.bastion_trace.destination_review import review

from app.services.bastion_trace.batch_screening import make_batch_result
from app.services.bastion_trace.business_policy_profiles import default_policy_profiles
from app.services.bastion_trace.business_tier import get_business_tier_profile
from app.schemas.bastion_trace import (
    BatchTraceItemResult,
    BatchTraceRequest,
    BusinessPolicyAction,
    BusinessTraceEventType,
    PaymentContextRiskRequest,
)

from app.schemas.bastion_trace import (
    BastionTraceRegisterAdvisoryRequest,
    BastionTraceTreasuryCheckRequest,
    EvidenceAccessRequest,
)
from app.services.bastion_trace.enterprise_tier import get_enterprise_tier_profile
from app.services.bastion_trace.enterprise_rbac import default_rbac_policy
from app.services.bastion_trace.sso_placeholder import default_sso_config
from app.services.bastion_trace.evidence_governance import decide_evidence_access
from app.services.bastion_trace.enterprise_proof_packet import build_enterprise_proof_packet
from app.services.bastion_trace.integrations.citadel_bridge import score_impact
from app.services.bastion_trace.integrations.policy_bridge import recommend
from app.services.bastion_trace.integrations.treasury_bridge import treasury_review_level
from app.services.bastion_trace.integrations.register_bridge import merchant_recommendation
from app.services.bastion_trace.integrations.evidence_bridge import build_refs
from app.services.bastion_trace.trace_metrics import (
    TRACE_BATCH,
    TRACE_CONF,
    TRACE_LITE,
    TRACE_PRIVACY,
    TRACE_REPORTS,
    TRACE_REQUESTS,
    TRACE_RUNTIME,
    TRACE_SCORE_BAND,
)
from app.services.bastion_trace.trace_runtime_events import create_event, get_event, list_events
from app.services.bastion_trace.trace_alerts import create_alert, list_alerts
from app.services.bastion_trace.trace_status import make_status
from app.services.events.domain_event_publisher import publish_domain_event

_LIMITATIONS = [
    "advisory_only",
    "not_legal_verdict",
    "not_consensus_proof",
    "source_coverage_baseline",
    "false_positives_possible",
    "false_negatives_possible",
]


class TraceService:
    def __init__(self, repo: BastionTraceRepository) -> None:
        self.repo = repo
        self.source_registry = RiskSourceRegistryService(repo)

    def _publish_trace_report_created(
        self,
        saved: TraceReport,
        breakdown: TraceScoreBreakdown,
        scoring: object,
    ) -> None:
        publish_domain_event(
            self.repo.db,
            "trace.report.created",
            {
                "report_id": saved.id,
                "address_hash_or_public_address": saved.address,
                "trace_band": saved.trace_band,
                "confidence": saved.confidence,
                "source_quality": saved.source_quality,
                "freshness": saved.freshness,
                "manual_review_recommended": saved.trace_band in {"HIGH", "CRITICAL"},
                "reason_codes": json.loads(saved.reason_codes_json or "[]"),
                "evidence_refs": json.loads(saved.evidence_refs_json or "[]"),
                "limitations": breakdown.limitations,
                "advisory_not_legal_verdict": True,
                "not_consensus_proof": True,
                "no_custody": True,
            },
            aggregate_type="trace_report",
            aggregate_id=saved.id,
            source="bastion_trace",
            idempotency_key=f"trace.report.created:trace_report:{saved.id}:created",
        )

    def analyze_address(
        self, address: str, *, idempotency_key_hash: str | None = None
    ) -> TraceReportSchema:
        TRACE_REQUESTS.labels(tier="core", operation="analyze_address", status="attempt").inc()
        normalized = self._validate_public_address(address)
        scoring = score_trace(
            TraceScoringInput(
                evidence_count=0,
                independent_source_count=0,
                evidence_freshness_days=[],
                baseline_mode=True,
                reason_codes=[TraceReasonCode.NO_MEANINGFUL_EVIDENCE.value],
            )
        )
        sources = self.source_registry.list_sources()
        source_names = [s.source_name for s in sources]
        independence = EvidenceIndependenceService().calculate(source_names)
        disagreement = ProviderDisagreementService().detect_disagreement(
            ["unknown"], [scoring.band.value]
        )
        passport: OriginPassport = build_origin_passport(normalized, [], disagreement, independence)
        privacy = PrivacyShieldService().build_privacy_shield(normalized, None, None)

        guidance = [
            self._guidance(scoring.band.value),
            "Do not provide seed phrases, private keys or wallet files.",
        ]
        breakdown = TraceScoreBreakdown(
            base_score=0.0,
            final_score=scoring.final_score,
            band=scoring.band,
            confidence=max(
                0.0, scoring.confidence - disagreement.confidence_impact + independence.score * 0.1
            ),
            source_quality=scoring.source_quality,
            freshness=scoring.freshness,
            trace_dna=scoring.trace_dna,
            factor_contributions=scoring.factor_contributions,
            confidence_ledger=scoring.confidence_ledger,
            reason_codes=sorted(
                set(
                    scoring.reason_codes
                    + BASELINE_REASONS
                    + disagreement.reason_codes
                    + independence.reason_codes
                    + passport.reason_codes
                )
            ),
            limitations=sorted(set(_LIMITATIONS + passport.limitations)),
            operator_guidance=guidance,
        )
        report = TraceReport(
            idempotency_key_hash=idempotency_key_hash,
            address=normalized,
            chain="bitcoin",
            trace_score=scoring.final_score,
            trace_band=scoring.band.value,
            confidence=breakdown.confidence,
            source_quality=scoring.source_quality.value,
            freshness=scoring.freshness.value,
            summary="Baseline deterministic scoring report.",
            limitations_json=json.dumps(breakdown.limitations),
            operator_guidance_json=json.dumps(guidance),
            reason_codes_json=json.dumps(breakdown.reason_codes),
            evidence_refs_json=json.dumps([]),
        )
        saved = self.repo.save_report(report)
        TRACE_REPORTS.labels(tier="core", status="created").inc()
        TRACE_SCORE_BAND.labels(tier="core", band=scoring.band.value).inc()
        TRACE_CONF.labels(tier="core").set(float(breakdown.confidence))
        TRACE_PRIVACY.labels(tier="core").set(0.0)
        create_event(
            "TRACE_REPORT_CREATED", "INFO", "analyze_address", "success", "trace report created"
        )
        TRACE_RUNTIME.labels(
            event_type="TRACE_REPORT_CREATED", severity="INFO", status="success"
        ).inc()
        self.repo.save_origin_metadata(
            saved.id,
            passport.model_dump(mode="json"),
            disagreement.model_dump(mode="json"),
            independence.model_dump(mode="json"),
            [item.model_dump(mode="json") for item in sources],
        )
        self.repo.save_privacy_metadata(saved.id, privacy.model_dump(mode="json"))
        lens = build_counterparty_lens(
            normalized,
            scoring.band.value,
            privacy.privacy_band.value,
            passport.origin_category,
            disagreement.severity.value,
            independence.score,
        )
        self.repo.save_counterparty_lens(saved.id, lens.model_dump(mode="json"))
        self._publish_trace_report_created(saved, breakdown, scoring)

        return TraceReportSchema(
            id=saved.id,
            address=normalized,
            trace_score=scoring.final_score,
            trace_band=scoring.band,
            confidence=breakdown.confidence,
            source_quality=scoring.source_quality,
            freshness=scoring.freshness,
            trace_dna=scoring.trace_dna,
            factor_contributions=scoring.factor_contributions,
            confidence_ledger=scoring.confidence_ledger,
            score_breakdown=breakdown,
            reason_codes=breakdown.reason_codes,
            evidence_refs=[],
            limitations=breakdown.limitations,
            operator_guidance=guidance,
            advisory_not_legal_verdict=True,
            not_consensus_proof=True,
            no_custody=True,
            created_at=saved.created_at,
        )

    def get_origin_passport(self, report_id: int) -> dict[str, object] | None:
        report = self.repo.get_report(report_id)
        if report is None:
            return None
        return cast(dict[str, object], json.loads(report.origin_passport_json or "{}"))

    def get_source_summary(self, report_id: int) -> list[dict[str, object]]:
        report = self.repo.get_report(report_id)
        if report is None:
            return []
        return cast(list[dict[str, object]], json.loads(report.source_status_summary_json or "[]"))

    def get_provider_disagreement(self, report_id: int) -> dict[str, object] | None:
        report = self.repo.get_report(report_id)
        if report is None:
            return None
        return cast(dict[str, object], json.loads(report.provider_disagreement_json or "{}"))

    def get_privacy_shield(self, report_id: int) -> dict[str, object] | None:
        report = self.repo.get_report(report_id)
        if report is None:
            return None
        return cast(dict[str, object], json.loads(report.privacy_shield_json or "{}"))

    def get_utxo_hygiene(self, report_id: int) -> dict[str, object] | None:
        report = self.repo.get_report(report_id)
        if report is None:
            return None
        return cast(dict[str, object], json.loads(report.utxo_hygiene_json or "{}"))

    def get_dust_radar(self, report_id: int) -> dict[str, object] | None:
        report = self.repo.get_report(report_id)
        if report is None:
            return None
        return cast(dict[str, object], json.loads(report.dust_radar_json or "{}"))

    def get_counterparty_lens(self, report_id: int) -> dict[str, object] | None:
        report = self.repo.get_report(report_id)
        if report is None:
            return None
        privacy = self.get_privacy_shield(report_id) or {}
        origin = self.get_origin_passport(report_id) or {}
        disag = self.get_provider_disagreement(report_id) or {}
        indep = json.loads(report.evidence_independence_json or "{}").get("score", 0.0)
        lens = build_counterparty_lens(
            report.address,
            report.trace_band,
            str(privacy.get("privacy_band", "UNKNOWN")),
            str(origin.get("origin_category", "unknown")),
            str(disag.get("severity", "NONE")),
            float(indep),
        )
        return cast(dict[str, object], lens.model_dump(mode="json"))

    def evaluate_payment_context(self, payload: PaymentContextRiskRequest) -> dict[str, object]:
        report = self.analyze_address(payload.address)
        lens = build_counterparty_lens(
            payload.address, report.trace_band.value, "UNKNOWN", "unknown", "NONE", 0.0
        ).model_dump(mode="json")
        ctx = evaluate_payment_context(
            payload.address,
            report.trace_band.value,
            report.confidence,
            "NONE",
            payload.amount_sats,
            payload.direction,
            payload.payment_purpose,
            payload.business_context == "treasury",
            payload.urgency == "urgent",
            lens,
        )
        return cast(dict[str, object], ctx.model_dump(mode="json"))

    def preview_payment_intent(self, payload: PaymentContextRiskRequest) -> dict[str, object]:
        ctx = PaymentContextRiskReport.model_validate(self.evaluate_payment_context(payload))
        return cast(dict[str, object], preview(ctx).model_dump(mode="json"))

    def destination_review(self, payload: PaymentContextRiskRequest) -> dict[str, object]:
        ctx = self.evaluate_payment_context(payload)
        advisory = ctx.get("safe_to_send_advisory", "INSUFFICIENT_INFORMATION")
        res = review(advisory) if isinstance(advisory, str) else review(str(advisory))
        return cast(dict[str, object], res.model_dump(mode="json"))

    def build_lite_report(self, address: str) -> dict[str, object]:
        TRACE_LITE.labels(status="attempt").inc()
        trace = self.analyze_address(address)
        privacy = self.get_privacy_shield(trace.id or 0) or {}
        lite = LiteTraceReportService().from_trace_report(
            trace, str(privacy.get("privacy_band", "UNKNOWN"))
        )
        TRACE_LITE.labels(status="success").inc()
        create_event(
            "TRACE_LITE_CHECK_CREATED", "INFO", "lite_check", "success", "lite check created"
        )
        TRACE_RUNTIME.labels(
            event_type="TRACE_LITE_CHECK_CREATED", severity="INFO", status="success"
        ).inc()
        return cast(dict[str, object], lite.model_dump(mode="json"))

    def get_business_tier_profile(self) -> dict[str, object]:
        return cast(dict[str, object], get_business_tier_profile().model_dump(mode="json"))

    def ensure_default_policy_profiles(self) -> None:
        existing = {p.id for p in self.repo.list_policy_profiles()}
        for profile in default_policy_profiles():
            if profile.id in existing:
                continue
            self.repo.save_policy_profile(
                TraceBusinessPolicyProfileModel(
                    id=profile.id,
                    name=profile.name,
                    description=profile.description,
                    context_type=profile.context_type.value,
                    low_action=profile.low_action.value,
                    medium_action=profile.medium_action.value,
                    high_action=profile.high_action.value,
                    critical_action=profile.critical_action.value,
                    unknown_action=profile.unknown_action.value,
                    manual_review_threshold=profile.manual_review_threshold,
                    high_value_threshold_sats=profile.high_value_threshold_sats,
                    require_review_on_provider_disagreement=profile.require_review_on_provider_disagreement,
                    require_review_on_low_confidence=profile.require_review_on_low_confidence,
                    require_review_on_privacy_high=profile.require_review_on_privacy_high,
                    limitations_json=json.dumps(profile.limitations),
                )
            )

    def list_policy_profiles(self) -> list[dict[str, object]]:
        self.ensure_default_policy_profiles()
        out: list[dict[str, object]] = []
        for p in self.repo.list_policy_profiles():
            out.append(
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "context_type": p.context_type,
                    "low_action": p.low_action,
                    "medium_action": p.medium_action,
                    "high_action": p.high_action,
                    "critical_action": p.critical_action,
                    "unknown_action": p.unknown_action,
                    "manual_review_threshold": p.manual_review_threshold,
                    "high_value_threshold_sats": p.high_value_threshold_sats,
                    "require_review_on_provider_disagreement": p.require_review_on_provider_disagreement,
                    "require_review_on_low_confidence": p.require_review_on_low_confidence,
                    "require_review_on_privacy_high": p.require_review_on_privacy_high,
                    "limitations": json.loads(p.limitations_json),
                }
            )
        return out

    def screen_batch(self, payload: BatchTraceRequest) -> dict[str, object]:
        if len(payload.addresses) > 1000:
            raise ValueError("Batch exceeds max_addresses_per_batch=1000")
        batch = self.repo.create_batch(
            TraceBatch(
                batch_label=payload.batch_label or "",
                business_context=payload.business_context.value,
                policy_profile_id=payload.policy_profile_id,
                total_addresses=len(payload.addresses),
                limitations_json=json.dumps(["baseline_batch_screening"]),
            )
        )
        items: list[BatchTraceItemResult] = []
        for addr in payload.addresses:
            try:
                report = self.analyze_address(addr)
                policy = self.apply_policy_action(report.trace_band.value)
                manual = policy in {
                    BusinessPolicyAction.HOLD_FOR_REVIEW,
                    BusinessPolicyAction.REJECT_BY_POLICY,
                    BusinessPolicyAction.INSUFFICIENT_INFORMATION,
                }
                self.repo.add_batch_item(
                    TraceBatchItem(
                        batch_id=batch.id,
                        address=report.address,
                        report_id=report.id,
                        status="processed",
                        trace_band=report.trace_band.value,
                        trace_score=report.trace_score,
                        confidence=report.confidence,
                        policy_action=policy.value,
                        manual_review_recommended=manual,
                    )
                )
                items.append(
                    BatchTraceItemResult(
                        address=report.address,
                        status="processed",
                        report_id=report.id,
                        trace_band=report.trace_band.value,
                        trace_score=report.trace_score,
                        confidence=report.confidence,
                        policy_action=policy,
                        manual_review_recommended=manual,
                    )
                )
            except ValueError as exc:
                reason = (
                    "sensitive_wallet_material_not_accepted"
                    if "Sensitive wallet material" in str(exc)
                    else "invalid_public_bitcoin_address"
                )
                safe_address = "redacted"
                self.repo.add_batch_item(
                    TraceBatchItem(
                        batch_id=batch.id,
                        address=safe_address,
                        status="rejected",
                        rejection_reason=reason,
                        manual_review_recommended=False,
                    )
                )
                items.append(
                    BatchTraceItemResult(
                        address=safe_address,
                        status="rejected",
                        rejection_reason=reason,
                        limitations=["BATCH_ADDRESS_REJECTED_INVALID"],
                    )
                )
        TRACE_BATCH.labels(status="attempt").inc()
        result = make_batch_result(
            batch.id,
            payload.batch_label,
            payload.business_context,
            items,
            ["max_addresses_per_batch=1000"],
        )
        batch.processed_count = result.processed_count
        batch.rejected_count = result.rejected_count
        batch.low_count = result.low_count
        batch.medium_count = result.medium_count
        batch.high_count = result.high_count
        batch.critical_count = result.critical_count
        batch.unknown_count = result.unknown_count
        batch.manual_review_count = result.manual_review_count
        batch.updated_at = datetime.now(UTC)
        self.repo.create_batch(batch)
        self.repo.save_business_event(
            TraceBusinessEventModel(
                event_type=BusinessTraceEventType.TRACE_BATCH_COMPLETED.value,
                payload_json=json.dumps({"batch_id": batch.id}),
                delivered=False,
            )
        )
        publish_domain_event(
            self.repo.db,
            "trace.batch.completed",
            {
                "batch_id": batch.id,
                "processed_count": result.processed_count,
                "rejected_count": result.rejected_count,
                "manual_review_count": result.manual_review_count,
                "limitations": ["baseline_batch_screening", "advisory_only", "not_consensus_proof"],
                "advisory_not_legal_verdict": True,
                "not_consensus_proof": True,
                "no_custody": True,
            },
            aggregate_type="trace_batch",
            aggregate_id=batch.id,
            source="bastion_trace_batch",
            idempotency_key=f"trace.batch.completed:trace_batch:{batch.id}:completed",
        )
        TRACE_BATCH.labels(status="success").inc()
        create_event(
            "TRACE_BATCH_COMPLETED",
            "INFO",
            "batch",
            "success",
            "batch completed",
            {"batch_id": batch.id},
        )
        TRACE_RUNTIME.labels(
            event_type="TRACE_BATCH_COMPLETED", severity="INFO", status="success"
        ).inc()
        return cast(dict[str, object], result.model_dump(mode="json"))

    def apply_policy_action(self, trace_band: str) -> BusinessPolicyAction:
        if trace_band == "LOW":
            return BusinessPolicyAction.ACCEPT_WITH_NOTE
        if trace_band == "MEDIUM":
            return BusinessPolicyAction.HOLD_FOR_REVIEW
        if trace_band == "HIGH":
            return BusinessPolicyAction.HOLD_FOR_REVIEW
        if trace_band == "CRITICAL":
            return BusinessPolicyAction.REJECT_BY_POLICY
        return BusinessPolicyAction.INSUFFICIENT_INFORMATION

    def get_enterprise_tier_profile(self) -> dict[str, object]:
        return cast(dict[str, object], get_enterprise_tier_profile().model_dump(mode="json"))

    def list_enterprise_roles(self) -> list[str]:
        return [r.value for r in default_rbac_policy().role_permissions.keys()]

    def list_enterprise_permissions(self) -> list[str]:
        perms: set[str] = set()
        for vals in default_rbac_policy().role_permissions.values():
            perms.update(p.value for p in vals)
        return sorted(perms)

    def get_enterprise_default_policy(self) -> dict[str, object]:
        return cast(dict[str, object], default_rbac_policy().model_dump(mode="json"))

    def get_sso_placeholder(self) -> dict[str, object]:
        return cast(dict[str, object], default_sso_config().model_dump(mode="json"))

    def evaluate_evidence_access_enterprise(
        self, payload: EvidenceAccessRequest
    ) -> dict[str, object]:
        decision = decide_evidence_access(payload.requester_role.value)
        return {
            "evidence_ref": payload.evidence_ref,
            "requester_role": payload.requester_role.value,
            "purpose": payload.purpose,
            "decision": decision.value,
        }

    def create_enterprise_proof_packet(self, report_id: int) -> dict[str, object]:
        return cast(
            dict[str, object],
            build_enterprise_proof_packet(
                {
                    "base_proof_packet": {"report_id": report_id},
                    "legal_hold_status": "UNKNOWN",
                    "rbac_context": {"production_enforced": False},
                    "sso_context": default_sso_config().model_dump(mode="json"),
                    "limitations": ["enterprise_baseline_placeholder"],
                }
            ).model_dump(mode="json"),
        )

    def get_citadel_contribution(self, report_id: int) -> dict[str, object] | None:
        report = self.repo.get_report(report_id)
        if report is None:
            return None
        impact = score_impact(report.trace_band)
        return {
            "trace_report_id": report.id,
            "trace_band": report.trace_band,
            "trace_score": report.trace_score,
            "confidence": report.confidence,
            "privacy_band": "UNKNOWN",
            "origin_category": "unknown",
            "provider_disagreement_severity": "NONE",
            "evidence_independence_score": 0.0,
            "manual_review_recommended": report.trace_band in {"HIGH", "CRITICAL"},
            "highest_exposure_band": report.trace_band,
            "citadel_score_impact": impact,
            "reason_codes": json.loads(report.reason_codes_json),
            "evidence_refs": json.loads(report.evidence_refs_json),
            "limitations": json.loads(report.limitations_json),
            "operator_guidance": json.loads(report.operator_guidance_json),
        }

    def get_policy_facts(self, report_id: int) -> dict[str, object] | None:
        report = self.repo.get_report(report_id)
        if report is None:
            return None
        rec = recommend(report.trace_band, report.confidence)
        return {
            "trace_band": report.trace_band,
            "trace_score": report.trace_score,
            "confidence": report.confidence,
            "privacy_band": "UNKNOWN",
            "provider_disagreement_severity": "NONE",
            "safe_to_send_advisory": (
                "MANUAL_REVIEW_RECOMMENDED"
                if report.trace_band in {"HIGH", "CRITICAL", "MEDIUM"}
                else "PROCEED_WITH_CAUTION"
            ),
            "manual_review_recommended": rec in {"REQUIRE_MANUAL_REVIEW", "REQUIRE_SENIOR_REVIEW"},
            "business_policy_action": self.apply_policy_action(report.trace_band).value,
            "enterprise_legal_hold_active": False,
            "evidence_independence_score": 0.0,
            "policy_recommendation": rec,
        }

    def treasury_destination_check(
        self, payload: BastionTraceTreasuryCheckRequest
    ) -> dict[str, object]:
        report = self.analyze_address(payload.destination_address)
        result: dict[str, object] = {
            "destination_address": payload.destination_address,
            "trace_report_id": report.id,
            "trace_band": report.trace_band.value,
            "safe_to_send_advisory": (
                "MANUAL_REVIEW_RECOMMENDED"
                if report.trace_band.value in {"HIGH", "CRITICAL", "MEDIUM"}
                else "PROCEED_WITH_CAUTION"
            ),
            "manual_review_recommended": report.trace_band.value in {"HIGH", "CRITICAL", "MEDIUM"},
            "treasury_review_level": treasury_review_level(report.trace_band.value),
            "approval_packet_hint": "attach_trace_receipt",
            "limitations": ["advisory_only", "no_transaction_signing"],
            "operator_guidance": ["Treasury Bridge does not sign or broadcast transactions."],
        }
        publish_domain_event(
            self.repo.db,
            "trace.treasury_destination_check.created",
            {
                "report_id": report.id,
                "address_hash_or_public_address": payload.destination_address,
                "trace_band": report.trace_band.value,
                "confidence": report.confidence,
                "manual_review_recommended": result["manual_review_recommended"],
                "reason_codes": report.reason_codes,
                "evidence_refs": report.evidence_refs,
                "limitations": result["limitations"],
                "advisory_not_legal_verdict": True,
                "not_consensus_proof": True,
                "no_custody": True,
            },
            aggregate_type="trace_report",
            aggregate_id=report.id,
            source="bastion_trace_treasury_bridge",
            idempotency_key=f"trace.treasury_destination_check.created:trace_report:{report.id}:created",
        )
        return result

    def register_payment_advisory(
        self, payload: BastionTraceRegisterAdvisoryRequest
    ) -> dict[str, object]:
        report = self.analyze_address(payload.payer_address)
        return {
            "incoming_payment_id": payload.incoming_payment_id,
            "payer_address": payload.payer_address,
            "trace_report_id": report.id,
            "merchant_recommendation": merchant_recommendation(report.trace_band.value),
            "risk_receipt_hint": f"trace-receipt-{report.id}",
            "manual_review_recommended": report.trace_band.value in {"HIGH", "CRITICAL", "MEDIUM"},
            "limitations": ["advisory_only", "register_placeholder"],
            "operator_guidance": ["Register Bridge is advisory and does not auto-reject payments."],
        }

    def get_evidence_refs(self, report_id: int) -> list[dict[str, object]]:
        if self.repo.get_report(report_id) is None:
            return []
        return build_refs(report_id)

    def list_runtime_events(self) -> list[dict[str, object]]:
        return list_events()

    def get_runtime_event(self, event_id: int) -> dict[str, object] | None:
        return get_event(event_id)

    def list_trace_alerts(self) -> list[dict[str, object]]:
        return list_alerts()

    def create_trace_alert_placeholder(
        self, alert_type: str, severity: str, message: str
    ) -> dict[str, object]:
        return create_alert(alert_type, severity, message)

    def get_trace_status(self) -> dict[str, object]:
        reports = 0
        latest = self.repo.get_report(1)
        while latest is not None:
            reports += 1
            latest = self.repo.get_report(reports + 1)
        last_report = self.repo.get_report(reports)
        last = (
            last_report.created_at.isoformat() if last_report and last_report.created_at else None
        )
        return make_status(
            reports_count=reports,
            lite_checks_count=0,
            batches_count=0,
            source_count=len(self.repo.list_sources()),
            last_report_at=last,
        )

    def _guidance(self, band: str) -> str:
        return {
            "UNKNOWN": "Insufficient evidence. Treat this as advisory-only and repeat analysis when more sources are available.",
            "LOW": "No strong risk signal was found in the available evidence. This is not a guarantee.",
            "MEDIUM": "Some risk signals require caution. Consider manual review before high-value activity.",
            "HIGH": "Strong risk signals are present. Manual review is recommended before proceeding.",
            "CRITICAL": "Critical risk signals are present. Do not proceed without senior/manual review.",
        }.get(band, "Use this report as advisory information only.")

    def _validate_public_address(self, address: str) -> str:
        value = address.strip()
        lowered = value.lower()
        if not value:
            raise ValueError("Invalid Bitcoin address")
        if (
            any(t in lowered for t in ["xprv", "xpriv", ".dat", "seed phrase", "mnemonic"])
            or len(value.split()) >= 12
        ):
            raise ValueError(
                "Sensitive wallet material is not accepted. Use only a public Bitcoin address."
            )
        if re.match(r"^(0x)[0-9a-fA-F]{40}$", value):
            raise ValueError("Invalid Bitcoin address")
        if re.match(r"^[KL5][1-9A-HJ-NP-Za-km-z]{50,51}$", value):
            raise ValueError(
                "Sensitive wallet material is not accepted. Use only a public Bitcoin address."
            )
        if re.match(r"^(1|3)[1-9A-HJ-NP-Za-km-z]{25,62}$", value) or re.match(
            r"^bc1[ac-hj-np-z02-9]{11,71}$", lowered
        ):
            return value
        raise ValueError("Invalid Bitcoin address")
