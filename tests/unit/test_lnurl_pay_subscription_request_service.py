from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models.access import AccessAuditEvent
from app.domain.access.plans import PlanCode
from app.services.access.audit_chain import AccessAuditChain
from app.services.lnurl.pay.callback_urls import LNURLPayCallbackURLBuilder, LNURLPayCallbackURLConfig
from app.services.lnurl.pay.errors import (
    LNURLPayAnonymousCheckoutDeniedError,
    LNURLPayIdempotencyConflictError,
    LNURLPayInvalidAmountError,
    LNURLPayInvalidRangeError,
    LNURLPayMetadataError,
    LNURLPayPlanUnavailableError,
    LNURLPayPolicyDeniedError,
    LNURLPayPrincipalUnavailableError,
    LNURLPayUnsafeCallbackError,
    LNURLPayUnknownPlanError,
)
from app.services.lnurl.pay.metadata_provider import validate_lnurl_pay_metadata
from app.services.lnurl.pay.pricing import StaticSubscriptionPricingResolver
from app.services.lnurl.pay.subscription_request_service import (
    InMemoryLNURLPaySubscriptionRequestRepository,
    LNURLPayPolicyDecision,
    LNURLPaySubscriptionRequestConfig,
    LNURLPaySubscriptionRequestService,
)

FIXED = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)


class DenyPolicy:
    def evaluate_lnurl_pay_request(self, context: Mapping[str, object]) -> LNURLPayPolicyDecision:
        return LNURLPayPolicyDecision(decision="deny", allowed=False, reason_code="plan_unavailable", policy_hash="sha256:policy")


class StatusChecker:
    def __init__(self, status: str | None) -> None:
        self.status = status

    def get_principal_status(self, principal_hash: str) -> str | None:
        return self.status


class RevocationChecker:
    def __init__(self, revoked: set[tuple[str, str]]) -> None:
        self.revoked = revoked

    def is_revoked(self, target_type: str, target_hash: str) -> bool:
        return (target_type, target_hash) in self.revoked


@pytest.fixture()
def repository() -> InMemoryLNURLPaySubscriptionRequestRepository:
    return InMemoryLNURLPaySubscriptionRequestRepository()


def make_service(
    repository: InMemoryLNURLPaySubscriptionRequestRepository | None = None,
    *,
    config: LNURLPaySubscriptionRequestConfig | None = None,
    pricing_resolver: StaticSubscriptionPricingResolver | None = None,
    policy_hook: object | None = None,
    principal_status: str | None = "active",
    audit: bool = False,
) -> LNURLPaySubscriptionRequestService:
    audit_chain = None
    if audit:
        engine = create_engine("sqlite:///:memory:")
        AccessAuditEvent.__table__.create(bind=engine)
        audit_chain = AccessAuditChain(Session(engine))
    return LNURLPaySubscriptionRequestService(
        repository=repository or InMemoryLNURLPaySubscriptionRequestRepository(),
        config=config or LNURLPaySubscriptionRequestConfig(public_base_url="https://pay.example.com", request_ttl_seconds=300),
        pricing_resolver=pricing_resolver or StaticSubscriptionPricingResolver(clock=lambda: FIXED, quote_ttl_seconds=600),
        policy_hook=policy_hook,  # type: ignore[arg-type]
        principal_status_checker=StatusChecker(principal_status) if principal_status is not None else None,
        audit_chain=audit_chain,
        clock=lambda: FIXED,
    )


def create(service: LNURLPaySubscriptionRequestService, **overrides: object):
    params = {
        "plan_code": PlanCode.BASIC,
        "principal_hash": None,
        "actor_type": None,
        "product_code": "bastion_access",
        "requested_amount_msat": None,
        "origin": "https://app.example.com",
        "locale": "en-US",
        "idempotency_key": None,
        "payer_data_mode": None,
        "comment_allowed": None,
        "success_action_mode": None,
        "request_context": None,
    }
    params.update(overrides)
    return service.create_subscription_request(**params)  # type: ignore[arg-type]


def test_basic_lnurl_pay_response_contains_required_fields(repository: InMemoryLNURLPaySubscriptionRequestRepository) -> None:
    result = create(make_service(repository))
    response = result.to_lnurl_response()

    assert response["tag"] == "payRequest"
    assert response["callback"].startswith("https://pay.example.com/v1/lnurl/pay/callback/")
    assert isinstance(response["minSendable"], int)
    assert isinstance(response["maxSendable"], int)
    assert response["metadata"].startswith("[[\"text/plain\"")
    assert result.status == "pending_callback"
    assert list(repository.records.values())[0].status.value == "pending_callback"


def test_fixed_price_basic_plan_uses_integer_msats_and_no_base_pass() -> None:
    result = create(make_service(), plan_code="basic_pass")

    assert result.min_sendable_msat == result.max_sendable_msat == 50_000_000
    assert result.plan_code == "basic_pass"
    with pytest.raises(LNURLPayUnknownPlanError):
        create(make_service(), plan_code="base_pass")


def test_variable_amount_requires_config_and_bounds() -> None:
    disabled = StaticSubscriptionPricingResolver(variable_ranges_msat={PlanCode.PLUS: (100, 200)}, variable_amount_enabled=False, clock=lambda: FIXED)
    with pytest.raises(LNURLPayPlanUnavailableError):
        create(make_service(pricing_resolver=disabled), plan_code=PlanCode.PLUS, requested_amount_msat=150)

    enabled = StaticSubscriptionPricingResolver(variable_ranges_msat={PlanCode.PLUS: (100, 200)}, variable_amount_enabled=True, clock=lambda: FIXED)
    result = create(make_service(pricing_resolver=enabled), plan_code=PlanCode.PLUS, requested_amount_msat=150)
    assert result.min_sendable_msat == 100
    assert result.max_sendable_msat == 200
    with pytest.raises(LNURLPayInvalidAmountError):
        create(make_service(pricing_resolver=enabled), plan_code=PlanCode.PLUS, requested_amount_msat=99)
    with pytest.raises(LNURLPayInvalidAmountError):
        create(make_service(pricing_resolver=enabled), plan_code=PlanCode.PLUS, requested_amount_msat=201)


def test_invalid_amounts_and_ranges_fail() -> None:
    with pytest.raises(LNURLPayInvalidAmountError):
        create(make_service(), requested_amount_msat=0)
    with pytest.raises(LNURLPayInvalidAmountError):
        create(make_service(), requested_amount_msat=1.5)
    bad_range = StaticSubscriptionPricingResolver(variable_ranges_msat={PlanCode.PLUS: (200, 100)}, variable_amount_enabled=True, clock=lambda: FIXED)
    with pytest.raises(LNURLPayInvalidRangeError):
        create(make_service(pricing_resolver=bad_range), plan_code=PlanCode.PLUS, requested_amount_msat=150)


def test_plan_validation_disabled_enterprise_and_sovereign() -> None:
    disabled = StaticSubscriptionPricingResolver(disabled_plans={PlanCode.ENTERPRISE}, clock=lambda: FIXED)
    with pytest.raises(LNURLPayPlanUnavailableError):
        create(make_service(pricing_resolver=disabled), plan_code=PlanCode.ENTERPRISE)
    with pytest.raises(LNURLPayPlanUnavailableError):
        create(make_service(), plan_code="lite_pass", product_code="sovereign_mode")


def test_callback_url_safety_uses_trusted_host_and_opaque_reference() -> None:
    result = create(make_service(), principal_hash="hmac-sha256:principal", origin="https://evil.example")
    parsed = urlparse(result.callback)

    assert parsed.netloc == "pay.example.com"
    assert "hmac-sha256:principal" not in result.callback
    assert "basic_pass" not in result.callback
    assert parsed.path.startswith("/v1/lnurl/pay/callback/")
    assert parsed.path.rsplit("/", 1)[-1] != "1"


def test_callback_url_builder_rejects_unsafe_base_and_reference() -> None:
    with pytest.raises(LNURLPayUnsafeCallbackError):
        LNURLPayCallbackURLBuilder(LNURLPayCallbackURLConfig(public_base_url="http://pay.example.com"))
    with pytest.raises(LNURLPayUnsafeCallbackError):
        LNURLPayCallbackURLBuilder(LNURLPayCallbackURLConfig(public_base_url="https://user:pass@pay.example.com"))
    with pytest.raises(LNURLPayUnsafeCallbackError):
        LNURLPayCallbackURLBuilder(LNURLPayCallbackURLConfig(public_base_url="https://pay.example.com#frag"))
    builder = LNURLPayCallbackURLBuilder(LNURLPayCallbackURLConfig(public_base_url="https://pay.example.com"))
    with pytest.raises(LNURLPayUnsafeCallbackError):
        builder.build_callback_url("../escape")


def test_metadata_validation_and_hash_are_stable_and_safe() -> None:
    first = validate_lnurl_pay_metadata('[["text/plain","Bastion Basic"]]')
    second = validate_lnurl_pay_metadata('[["text/plain","Bastion Basic"]]')

    assert first.metadata_hash == second.metadata_hash
    with pytest.raises(LNURLPayMetadataError):
        validate_lnurl_pay_metadata('[["text/long-desc","missing plain"]]')
    with pytest.raises(LNURLPayMetadataError):
        validate_lnurl_pay_metadata('[["text/plain","principal_hash hmac-sha256:p"]]')


def test_idempotency_replays_same_request_without_storing_raw_key(repository: InMemoryLNURLPaySubscriptionRequestRepository) -> None:
    service = make_service(repository)
    first = create(service, idempotency_key="client-secret-idempotency")
    second = create(service, idempotency_key="client-secret-idempotency")
    record = next(iter(repository.records.values()))

    assert second.idempotency_replayed is True
    assert second.request_id == first.request_id
    assert second.callback == first.callback
    assert len(repository.records) == 1
    assert record.idempotency_hash is not None
    assert "client-secret-idempotency" not in str(record)


def test_idempotency_conflict_and_revoked_prior_request_fail(repository: InMemoryLNURLPaySubscriptionRequestRepository) -> None:
    service = make_service(repository)
    create(service, idempotency_key="same-key")
    with pytest.raises(LNURLPayIdempotencyConflictError):
        create(service, idempotency_key="same-key", plan_code=PlanCode.PLUS)


def test_anonymous_and_principal_bound_checkout_policies() -> None:
    with pytest.raises(LNURLPayAnonymousCheckoutDeniedError):
        create(make_service(config=LNURLPaySubscriptionRequestConfig(public_base_url="https://pay.example.com", allow_anonymous_checkout=False)))
    principal = create(make_service(), principal_hash="hmac-sha256:principal", actor_type="lightning_wallet_principal")
    assert principal.payment_context_hash is not None
    with pytest.raises(LNURLPayPrincipalUnavailableError):
        create(make_service(principal_status="revoked"), principal_hash="hmac-sha256:principal")


def test_payer_data_privacy_defaults_and_auth_mode() -> None:
    result = create(make_service())
    assert result.payer_data is None
    assert "email" not in result.to_lnurl_response()
    with pytest.raises(LNURLPayPolicyDeniedError):
        create(make_service(), payer_data_mode="auth_mandatory")
    enabled = make_service(config=LNURLPaySubscriptionRequestConfig(public_base_url="https://pay.example.com", payerdata_auth_enabled=True))
    auth = create(enabled, payer_data_mode="auth_mandatory")
    assert auth.payer_data == {"auth": {"mandatory": True}}


def test_comment_allowed_is_bounded_and_untrusted() -> None:
    assert "commentAllowed" not in create(make_service()).to_lnurl_response()
    service = make_service(config=LNURLPaySubscriptionRequestConfig(public_base_url="https://pay.example.com", max_comment_length=80))
    assert create(service, comment_allowed=40).to_lnurl_response()["commentAllowed"] == 40
    with pytest.raises(LNURLPayInvalidRangeError):
        create(service, comment_allowed=81)


def test_success_action_mode_is_recorded_but_not_returned() -> None:
    repository = InMemoryLNURLPaySubscriptionRequestRepository()
    result = create(make_service(repository), success_action_mode="message")

    assert "successAction" not in result.to_lnurl_response()
    assert next(iter(repository.records.values())).success_action_mode == "message"
    with pytest.raises(ValueError):
        create(make_service(), success_action_mode="token")


def test_policy_denial_creates_no_usable_request(repository: InMemoryLNURLPaySubscriptionRequestRepository) -> None:
    with pytest.raises(LNURLPayPolicyDeniedError):
        create(make_service(repository, policy_hook=DenyPolicy()))

    assert repository.records == {}


def test_success_audit_event_contains_hashes_only() -> None:
    repository = InMemoryLNURLPaySubscriptionRequestRepository()
    service = make_service(repository, audit=True)
    result = create(service, principal_hash="hmac-sha256:principal")
    record = next(iter(repository.records.values()))

    assert result.audit_event_hash is not None
    assert record.audit_event_hash is not None
    assert record.callback_hash.startswith("sha256:")
    assert record.request_reference_hash.startswith("hmac-sha256:")


def test_no_premature_invoice_proof_entitlement_or_access_side_effects(repository: InMemoryLNURLPaySubscriptionRequestRepository) -> None:
    create(make_service(repository))

    assert repository.count_invoices() == 0
    assert repository.count_payment_proofs() == 0
    assert repository.count_entitlements() == 0


def test_secret_material_rejected_from_context() -> None:
    with pytest.raises(Exception):
        create(make_service(), request_context={"wallet_seed": "abandon abandon"})
