from datetime import UTC, datetime, timedelta

from app.services.payregister.lnurl.payment_context import PayRegisterLNURLContextStatus, PayRegisterLNULEndpointMode
from app.services.payregister.lnurl.static_endpoint import InMemoryPayRegisterLNURLRepository, PayRegisterLNURLConfig, PayRegisterLNURLStaticEndpointService


def _service(clock=None):
    return PayRegisterLNURLStaticEndpointService(repository=InMemoryPayRegisterLNURLRepository(), config=PayRegisterLNURLConfig(context_ttl_seconds=60), clock=clock)


def _active_terminal(service):
    endpoint = service.create_static_endpoint(public_alias="terminal-1", endpoint_mode=PayRegisterLNULEndpointMode.TERMINAL_CHECKOUT, merchant_workspace_hash="hmac:workspace", store_hash="hmac:store", terminal_hash="hmac:terminal", min_sendable_msat=1_000, max_sendable_msat=200_000)
    return service.activate_static_endpoint(endpoint.endpoint_id)


def test_publish_checkout_freezes_amount_metadata_and_version():
    service = _service()
    endpoint = _active_terminal(service)
    context = service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=50_000, description="Latte", order_reference="A-100", context_version=7)
    assert context.status == PayRegisterLNURLContextStatus.ACTIVE
    assert context.min_sendable_msat == 50_000
    assert context.max_sendable_msat == 50_000
    assert context.context_version == 7
    assert context.metadata_hash.startswith("sha256:")


def test_replacing_checkout_marks_old_context_replaced():
    service = _service()
    endpoint = _active_terminal(service)
    first = service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=50_000, description="Latte")
    second = service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=60_000, description="Mocha")
    assert service.repository.get_context(first.payment_context_id).status == PayRegisterLNURLContextStatus.REPLACED
    assert service.repository.get_context(second.payment_context_id).status == PayRegisterLNURLContextStatus.ACTIVE


def test_open_amount_context_uses_endpoint_bounds():
    service = _service()
    endpoint = service.create_static_endpoint(public_alias="tips", endpoint_mode=PayRegisterLNULEndpointMode.STORE_OPEN_AMOUNT, merchant_workspace_hash="hmac:workspace", store_hash="hmac:store", min_sendable_msat=1_000, max_sendable_msat=1_000_000)
    service.activate_static_endpoint(endpoint.endpoint_id)
    result = service.resolve_lnurl_pay_request("tips")
    assert result.min_sendable_msat == 1_000
    assert result.max_sendable_msat == 1_000_000


def test_expired_context_fails_resolution():
    now = datetime(2026, 1, 1, tzinfo=UTC)
    service = _service(clock=lambda: now)
    endpoint = _active_terminal(service)
    service.publish_checkout_context(endpoint_id=endpoint.endpoint_id, amount_msat=50_000, description="Latte", ttl_seconds=1)
    service.clock = lambda: now + timedelta(seconds=2)
    try:
        service.resolve_lnurl_pay_request("terminal-1")
    except Exception as exc:
        assert getattr(exc, "reason_code", "") == "checkout_expired"
