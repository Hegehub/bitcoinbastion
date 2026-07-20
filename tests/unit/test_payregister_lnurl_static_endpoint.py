from app.services.payregister.lnurl.payment_context import PayRegisterLNULEndpointMode
from app.services.payregister.lnurl.static_endpoint import InMemoryPayRegisterLNURLRepository, PayRegisterLNURLStaticEndpointService, PayRegisterLNURLEndpointStatus


def _service():
    return PayRegisterLNURLStaticEndpointService(repository=InMemoryPayRegisterLNURLRepository())


def test_create_activate_static_endpoint_and_payloads_contain_no_secrets():
    service = _service()
    endpoint = service.create_static_endpoint(
        public_alias="counter-east",
        endpoint_mode=PayRegisterLNULEndpointMode.TERMINAL_CHECKOUT,
        merchant_workspace_hash="hmac:workspace",
        store_hash="hmac:store",
        terminal_hash="hmac:terminal",
        min_sendable_msat=1_000,
        max_sendable_msat=100_000,
        display_label="Coffee Shop",
    )
    endpoint = service.activate_static_endpoint(endpoint.endpoint_id)

    assert endpoint.status == PayRegisterLNURLEndpointStatus.ACTIVE
    qr = service.build_qr_payload(endpoint.endpoint_id)
    nfc = service.build_nfc_payload(endpoint.endpoint_id)
    assert "/.well-known/lnurlp/counter-east" in qr.raw_discovery_url
    assert qr.lnurl.startswith("lnurl1")
    assert nfc.https_url == qr.raw_discovery_url
    payload_text = f"{qr.raw_discovery_url} {qr.lnurl} {nfc.lnurl_text}".lower()
    assert "bolt11" not in payload_text
    assert "session_token" not in payload_text
    assert "access_pass" not in payload_text


def test_alias_is_unique_and_reserved_alias_is_rejected():
    service = _service()
    kwargs = dict(endpoint_mode=PayRegisterLNULEndpointMode.STORE_OPEN_AMOUNT, merchant_workspace_hash="hmac:workspace", store_hash="hmac:store")
    endpoint = service.create_static_endpoint(public_alias="tip-jar", **kwargs)
    assert service.create_static_endpoint(public_alias="tip-jar", **kwargs).endpoint_id == endpoint.endpoint_id
    try:
        service.create_static_endpoint(public_alias="admin", **kwargs)
    except Exception as exc:  # public error must be generic
        assert getattr(exc, "reason_code", "") in {"endpoint_not_found", "policy_denied"}
    else:  # pragma: no cover
        raise AssertionError("reserved alias accepted")


def test_suspend_and_revoke_stop_resolution():
    service = _service()
    endpoint = service.create_static_endpoint(public_alias="front", endpoint_mode=PayRegisterLNULEndpointMode.STORE_OPEN_AMOUNT, merchant_workspace_hash="hmac:workspace", store_hash="hmac:store")
    service.activate_static_endpoint(endpoint.endpoint_id)
    assert service.resolve_static_endpoint("front").public_alias == "front"
    service.suspend_static_endpoint(endpoint.endpoint_id)
    try:
        service.resolve_static_endpoint("front")
    except Exception as exc:
        assert getattr(exc, "reason_code", "") == "endpoint_disabled"
    endpoint = service.activate_static_endpoint(endpoint.endpoint_id)
    service.revoke_static_endpoint(endpoint.endpoint_id)
    try:
        service.resolve_static_endpoint("front")
    except Exception as exc:
        assert getattr(exc, "reason_code", "") == "endpoint_revoked"
